import asyncio
import logging
import random
from typing import Optional, Dict

import aiohttp
from aiohttp import ClientTimeout


from .config import Config, get_random_user_agent
from .robots import RobotsManager


logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate: float, burst: int = 1):
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last_update = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        while True:
            async with self._lock:
                if self._last_update == 0.0:
                    self._last_update = asyncio.get_running_loop().time()

                now = asyncio.get_running_loop().time()
                elapsed = now - self._last_update
                self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
                self._last_update = now

                if self._tokens >= 1:
                    self._tokens -= 1
                    return

            await asyncio.sleep(0.05)


class DomainRateLimiter:
    """Rate limiter per domain."""

    def __init__(self, delay: float = 1.0):
        self._delay = delay
        self._last_request: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, domain: str):
        async with self._lock:
            last = self._last_request.get(domain, 0)
            now = asyncio.get_running_loop().time()
            wait_time = self._delay - (now - last)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_request[domain] = asyncio.get_running_loop().time()


class Fetcher:
    """Handles HTTP requests with retry logic and rate limiting."""

    def __init__(self, config: Config):
        self._config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = RateLimiter(
            rate=config.max_concurrent_requests / 10,
            burst=config.max_concurrent_requests // 5,
        )
        self._domain_limiter = DomainRateLimiter(
            delay=config.min_delay_between_requests
        )
        self._robots_manager = RobotsManager()
        self._robots_fetched: set = set()
        self._in_robots_fetch = False
        self._stats: Dict[str, int] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retries": 0,
            "robots_blocked": 0,
        }
        self._user_agent = config.user_agent or get_random_user_agent()

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=self._config.max_concurrent_requests,
            limit_per_host=min(5, self._config.num_workers),
        )
        timeout = ClientTimeout(total=self._config.request_timeout)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": self._user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def _ensure_robots_loaded(self, url: str):
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain in self._robots_fetched:
            return

        if self._config.respect_robots_txt:
            self._in_robots_fetch = True
            robots = self._robots_manager.get_robots(domain)
            await robots.fetch(domain, self.fetch)
            self._in_robots_fetch = False
            self._robots_fetched.add(domain)

    def _is_allowed_by_robots(self, url: str) -> bool:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if not self._config.respect_robots_txt:
            return True

        robots = self._robots_manager.get_robots(domain)
        return robots.is_allowed(url, self._user_agent)

    async def fetch(self, url: str, referrer: Optional[str] = None) -> Optional[str]:
        """Fetch URL with retry logic and rate limiting."""
        if not self._in_robots_fetch:
            await self._ensure_robots_loaded(url)

            if not self._is_allowed_by_robots(url):
                logger.info(f"Blocked by robots.txt: {url}")
                self._stats["robots_blocked"] += 1
                return None

        from urllib.parse import urlparse

        domain = urlparse(url).netloc
        await self._domain_limiter.acquire(domain)
        await self._rate_limiter.acquire()

        headers = {}
        if referrer:
            headers["Referer"] = referrer

        session = self._session
        assert session is not None, (
            "Session not initialized. Use async with Fetcher(config):"
        )

        for attempt in range(self._config.max_retries):
            try:
                self._stats["total_requests"] += 1
                async with session.get(url, headers=headers) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 5))
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status == 403:
                        logger.warning(f"Access forbidden (403) for {url}")
                        self._stats["failed_requests"] += 1
                        return None

                    response.raise_for_status()
                    content = await response.text()
                    self._stats["successful_requests"] += 1
                    return content

            except aiohttp.ClientError as e:
                logger.debug(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self._config.max_retries - 1:
                    delay = self._config.retry_delay * (2**attempt)
                    await asyncio.sleep(delay)
                    self._stats["retries"] += 1
                else:
                    self._stats["failed_requests"] += 1
                    logger.error(
                        f"Failed to fetch {url} after {self._config.max_retries} attempts"
                    )

            except Exception as e:
                logger.debug(f"Non-retryable error fetching {url}: {e}")
                self._stats["failed_requests"] += 1
                break

        return None

    async def fetch_bytes(
        self, url: str, referrer: Optional[str] = None
    ) -> Optional[bytes]:
        """Fetch URL and return raw bytes."""
        if not self._in_robots_fetch:
            await self._ensure_robots_loaded(url)

            if not self._is_allowed_by_robots(url):
                logger.info(f"Blocked by robots.txt: {url}")
                self._stats["robots_blocked"] += 1
                return None

        from urllib.parse import urlparse

        domain = urlparse(url).netloc
        await self._domain_limiter.acquire(domain)
        await self._rate_limiter.acquire()

        headers = {}
        if referrer:
            headers["Referer"] = referrer

        session = self._session
        assert session is not None, (
            "Session not initialized. Use async with Fetcher(config):"
        )

        for attempt in range(self._config.max_retries):
            try:
                self._stats["total_requests"] += 1
                async with session.get(url, headers=headers) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 5))
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status == 403:
                        logger.warning(f"Access forbidden (403) for {url}")
                        self._stats["failed_requests"] += 1
                        return None

                    response.raise_for_status()
                    content = await response.read()
                    self._stats["successful_requests"] += 1
                    return content

            except aiohttp.ClientError as e:
                logger.debug(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self._config.max_retries - 1:
                    delay = self._config.retry_delay * (2**attempt)
                    await asyncio.sleep(delay)
                    self._stats["retries"] += 1
                else:
                    self._stats["failed_requests"] += 1
                    logger.error(
                        f"Failed to fetch {url} after {self._config.max_retries} attempts"
                    )

            except Exception as e:
                logger.debug(f"Non-retryable error fetching {url}: {e}")
                self._stats["failed_requests"] += 1
                break

        return None

    def get_stats(self) -> Dict[str, int]:
        return self._stats.copy()
