import asyncio
import logging
from typing import Optional, Dict, Any

import aiohttp
from aiohttp import ClientTimeout

from .exceptions import FetchError, RateLimitError
from .config import Config


logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate: float, burst: int = 1):
        self._rate = rate
        self._burst = burst
        self._tokens = burst
        self._last_update = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            while self._tokens < 1:
                await self._refill()
                await asyncio.sleep(0.1)
            self._tokens -= 1

    async def _refill(self):
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_update
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last_update = now


class Fetcher:
    """Handles HTTP requests with retry logic and rate limiting."""

    def __init__(self, config: Config):
        self._config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = RateLimiter(
            rate=config.max_concurrent_requests / 10,
            burst=config.max_concurrent_requests
        )
        self._stats: Dict[str, int] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retries": 0
        }

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=self._config.max_concurrent_requests,
            limit_per_host=self._config.num_workers
        )
        timeout = ClientTimeout(total=self._config.request_timeout)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "Spidey/1.0"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def fetch(self, url: str, referrer: Optional[str] = None) -> Optional[str]:
        """Fetch URL with retry logic and rate limiting."""
        await self._rate_limiter.acquire()

        headers = {}
        if referrer:
            headers["Referer"] = referrer

        for attempt in range(self._config.max_retries):
            try:
                self._stats["total_requests"] += 1
                async with self._session.get(url, headers=headers) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 5))
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    response.raise_for_status()
                    content = await response.text()
                    self._stats["successful_requests"] += 1
                    return content

            except aiohttp.ClientError as e:
                logger.debug(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self._config.max_retries - 1:
                    delay = self._config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    self._stats["retries"] += 1
                else:
                    self._stats["failed_requests"] += 1
                    logger.error(f"Failed to fetch {url} after {self._config.max_retries} attempts")

            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                self._stats["failed_requests"] += 1
                break

        return None

    async def fetch_bytes(self, url: str, referrer: Optional[str] = None) -> Optional[bytes]:
        """Fetch URL and return raw bytes."""
        await self._rate_limiter.acquire()

        headers = {}
        if referrer:
            headers["Referer"] = referrer

        for attempt in range(self._config.max_retries):
            try:
                self._stats["total_requests"] += 1
                async with self._session.get(url, headers=headers) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 5))
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    response.raise_for_status()
                    content = await response.read()
                    self._stats["successful_requests"] += 1
                    return content

            except aiohttp.ClientError as e:
                logger.debug(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self._config.max_retries - 1:
                    delay = self._config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    self._stats["retries"] += 1
                else:
                    self._stats["failed_requests"] += 1
                    logger.error(f"Failed to fetch {url} after {self._config.max_retries} attempts")

            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                self._stats["failed_requests"] += 1
                break

        return None

    def get_stats(self) -> Dict[str, int]:
        return self._stats.copy()