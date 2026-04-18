import asyncio
import time
from typing import Dict, Set, Optional
import aiohttp
import logging

logger = logging.getLogger(__name__)


class RobotsTxt:
    def __init__(self):
        self._crawl_delays: Dict[str, float] = {}
        self._disallowed_paths: Dict[str, Set[str]] = {}
        self._cache: Dict[str, tuple[float, Dict]] = {}
        self._lock = asyncio.Lock()

    async def fetch(self, base_url: str, fetch_func) -> bool:
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        async with self._lock:
            if domain in self._cache:
                cached_time, _ = self._cache[domain]
                if time.time() - cached_time < 3600:
                    return True

        try:
            html = await fetch_func(domain)
            if not html:
                return True

            lines = html.split("\n")
            current_user_agent = "*"
            disallowed_paths: Set[str] = set()
            crawl_delay: Optional[float] = None

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.lower().startswith("user-agent:"):
                    if current_user_agent != "*":
                        if current_user_agent not in self._disallowed_paths:
                            self._disallowed_paths[current_user_agent] = (
                                disallowed_paths.copy()
                            )
                        if crawl_delay and current_user_agent not in self._crawl_delays:
                            self._crawl_delays[current_user_agent] = crawl_delay
                    current_user_agent = line.split(":", 1)[1].strip()
                    disallowed_paths = set()
                    crawl_delay = None
                elif line.lower().startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if path:
                        disallowed_paths.add(path)
                elif line.lower().startswith("crawl-delay:"):
                    try:
                        crawl_delay = float(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass

            if current_user_agent not in self._disallowed_paths:
                self._disallowed_paths[current_user_agent] = disallowed_paths.copy()
            if crawl_delay and current_user_agent not in self._crawl_delays:
                self._crawl_delays[current_user_agent] = crawl_delay

            async with self._lock:
                self._cache[domain] = (time.time(), {})

            return True

        except Exception as e:
            logger.debug(f"Failed to fetch robots.txt for {domain}: {e}")
            return True

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = parsed.path or "/"

        for ua in [user_agent, "*"]:
            if ua in self._disallowed_paths:
                for disallowed in self._disallowed_paths[ua]:
                    if path.startswith(disallowed):
                        return False

        return True

    def get_crawl_delay(self, user_agent: str = "*") -> Optional[float]:
        for ua in [user_agent, "*"]:
            if ua in self._crawl_delays:
                return self._crawl_delays[ua]
        return None


class RobotsManager:
    def __init__(self):
        self._robots: Dict[str, RobotsTxt] = {}

    def get_robots(self, base_url: str) -> RobotsTxt:
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain not in self._robots:
            self._robots[domain] = RobotsTxt()

        return self._robots[domain]
