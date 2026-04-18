import asyncio
import hashlib
import logging
import threading
from typing import List, Optional, Set

import tldextract
import validators

from .config import Config
from .fetcher import Fetcher
from .parser import Parser
from .queue import URLQueue
from .file_queue import FileQueue
from .storage import Storage
from .controller import Controller, CrawlerState, CrawlStats


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Spidey:
    """
    A robust, modular asynchronous web crawler with full control.

    Features:
    - Pause/Resume/Stop control
    - Real-time stats and events
    - Thread-safe queues
    - SHA256 deduplication
    """

    def __init__(self, config: Config):
        self._config = config
        self._url_queue = URLQueue()
        self._file_queue = FileQueue()
        self._storage = Storage(config.folder)
        self._visited_pages: Set[str] = set()
        self._visited_pages_lock = threading.Lock()
        self._initial_domains: Set[str] = set()
        self._controller = Controller()

    @classmethod
    def from_args(
        cls,
        urls: List[str],
        extensions: List[str],
        limited_to_domains: bool = False,
        max_pages: int = 1000,
        sleep_time: float = 1.0,
        restricted_domains: Optional[List[str]] = None,
        folder: str = "",
        unique_file_name: bool = True,
        num_workers: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        request_timeout: float = 30.0,
        max_concurrent_requests: int = 50,
        respect_robots_txt: bool = True,
        user_agent: Optional[str] = None,
        min_delay_between_requests: float = 1.0,
    ):
        """Create Spidey instance from constructor arguments."""
        config = Config(
            urls=urls,
            extensions=extensions,
            limited_to_domains=limited_to_domains,
            max_pages=max_pages,
            sleep_time=sleep_time,
            restricted_domains=restricted_domains or [],
            folder=folder,
            unique_file_name=unique_file_name,
            num_workers=num_workers,
            max_retries=max_retries,
            retry_delay=retry_delay,
            request_timeout=request_timeout,
            max_concurrent_requests=max_concurrent_requests,
            respect_robots_txt=respect_robots_txt,
            user_agent=user_agent,
            min_delay_between_requests=min_delay_between_requests,
        )
        return cls(config)

    @property
    def state(self) -> CrawlerState:
        """Current crawler state."""
        return self._controller.state

    @property
    def stats(self) -> CrawlStats:
        """Current crawl statistics."""
        return self._controller.get_stats()

    def on(self, event_type: str, callback):
        """Register event listener."""
        self._controller.on(event_type, callback)

    def off(self, event_type: str, callback):
        """Unregister event listener."""
        self._controller.off(event_type, callback)

    def pause(self):
        """Pause the crawler."""
        self._controller.pause()
        logger.info("Crawler paused")

    def resume(self):
        """Resume the crawler."""
        self._controller.resume()
        logger.info("Crawler resumed")

    def stop(self):
        """Stop the crawler."""
        self._controller.stop()
        logger.info("Crawler stopped")

    def crawl(self):
        """Start the crawling process."""
        self._controller.start()
        asyncio.run(self._spider())
        self._controller.complete()
        logger.info("Crawl completed")

    async def _spider(self):
        """Main crawling orchestrator."""
        async with Fetcher(self._config) as fetcher:
            await self._init_domains()

            url_workers = [
                asyncio.create_task(self._url_worker(i, fetcher))
                for i in range(self._config.num_workers)
            ]

            file_workers = [
                asyncio.create_task(self._file_worker(i, fetcher))
                for i in range(self._config.num_workers)
            ]

            monitor_task = asyncio.create_task(self._monitor_progress())

            await asyncio.gather(*url_workers, return_exceptions=True)

            self._controller.set_state(CrawlerState.STOPPED)

            await asyncio.gather(*file_workers, return_exceptions=True)
            monitor_task.cancel()

            self._print_stats(fetcher)

    async def _init_domains(self):
        """Extract initial domains from starting URLs."""
        self._url_queue.add_batch(self._config.urls)
        for url in self._config.urls:
            domain = self._get_url_domain(url)
            self._initial_domains.add(domain)

    async def _monitor_progress(self):
        """Monitor and report progress."""
        while self._controller.state != CrawlerState.STOPPED:
            await self._controller.wait_if_paused()
            await asyncio.sleep(5)

            if self._controller.is_stopped():
                break

            url_count = self._url_queue.size()
            storage_stats = self._storage.get_stats()

            stats = {
                "urls_queued": url_count,
                "files_saved": storage_stats["files_saved"],
                "files_skipped": storage_stats["files_skipped"],
            }
            self._controller.update_stats(**stats)

            page_count = self._controller.get_stats().pages_visited

            logger.info(
                f"Progress: Pages={page_count}/{self._config.max_pages}, "
                f"URLs queued={url_count}, Files saved={storage_stats['files_saved']}, "
                f"Skipped={storage_stats['files_skipped']}"
            )

            self._controller.emit_event("progress", stats)

            if url_count == 0 and page_count >= self._config.max_pages // 2:
                self._controller.stop()
                break

    async def _url_worker(self, worker_id: int, fetcher: Fetcher):
        """Worker that fetches URLs and extracts new URLs/files."""
        while self._controller.state != CrawlerState.STOPPED:
            await self._controller.wait_if_paused()

            batch = self._url_queue.get_batch(5)
            if not batch:
                await asyncio.sleep(0.5)
                continue

            tasks = [self._process_url(url, fetcher) for url in batch]
            await asyncio.gather(*tasks, return_exceptions=True)

            if self._config.sleep_time > 0:
                await asyncio.sleep(self._config.sleep_time)

    async def _process_url(self, url: str, fetcher: Fetcher):
        """Fetch and process a single URL."""
        try:
            if self._controller.is_stopped():
                return

            with self._visited_pages_lock:
                if url in self._visited_pages:
                    return
                self._visited_pages.add(url)

            html = await fetcher.fetch(url)
            if not html:
                return

            new_page_urls = Parser.extract_page_urls(html, url)
            filtered_urls = [u for u in new_page_urls if self._is_allowed(u)]
            self._url_queue.add_batch(filtered_urls)

            self._controller.increment_stats(
                urls_discovered=len(filtered_urls), pages_visited=1
            )

            file_urls = Parser.extract_file_urls(html, url)
            for file_url in file_urls:
                if self._is_allowed_file(file_url):
                    self._file_queue.put(file_url, url)

            self._controller.emit_event(
                "page_crawled",
                {"url": url, "new_urls": len(filtered_urls), "files": len(file_urls)},
            )

            logger.debug(
                f"Processed {url}: {len(filtered_urls)} new URLs, {len(file_urls)} files"
            )

        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            self._controller.increment_stats(requests_failed=1)

    async def _file_worker(self, worker_id: int, fetcher: Fetcher):
        """Worker that downloads files."""
        while self._controller.state != CrawlerState.STOPPED:
            await self._controller.wait_if_paused()

            task = self._file_queue.get()
            if task is None:
                await asyncio.sleep(0.5)
                continue

            url, referrer = task
            await self._download_file(url, referrer, fetcher)

    async def _download_file(self, url: str, referrer: str, fetcher: Fetcher):
        """Download a file and save it."""
        try:
            if self._controller.is_stopped():
                return

            content = await fetcher.fetch_bytes(url, referrer)
            if not content:
                return

            checksum = hashlib.sha256(content).hexdigest()

            if self._file_queue.is_processed(checksum):
                return

            saved_path = await self._storage.save_file(url, content)

            if saved_path:
                self._controller.increment_stats(
                    files_saved=1, bytes_downloaded=len(content)
                )
                self._controller.emit_event(
                    "file_saved",
                    {"url": url, "checksum": checksum, "size": len(content)},
                )
            else:
                self._controller.increment_stats(files_skipped=1)

            self._file_queue.mark_processed(checksum)

        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")

    def _is_allowed(self, url: str) -> bool:
        """Check if URL is allowed based on domain restrictions."""
        if not validators.url(url):
            return False

        domain = self._get_url_domain(url)

        if domain in self._config.restricted_domains:
            return False

        if self._config.limited_to_domains:
            if domain not in self._initial_domains:
                return False

        return True

    def _is_allowed_file(self, url: str) -> bool:
        """Check if file extension is in allowed list."""
        if not validators.url(url):
            return False

        ext = self._get_file_extension(url)
        return ext in self._config.allowed_extensions

    def _get_url_domain(self, url: str) -> str:
        """Extract domain from URL."""
        extracted = tldextract.extract(url)
        return f"{extracted.domain}.{extracted.suffix}"

    def _get_file_extension(self, url: str) -> str:
        """Extract file extension from URL."""
        from urllib.parse import urlsplit

        path = urlsplit(url).path
        ext = path.rsplit(".", 1)[-1] if "." in path else ""
        return f".{ext.lower()}" if ext else ""

    def _print_stats(self, fetcher: Fetcher):
        """Print final statistics."""
        fetcher_stats = fetcher.get_stats()
        final_stats = self._controller.get_stats()

        logger.info("=" * 50)
        logger.info("Crawl Statistics")
        logger.info("=" * 50)
        logger.info(f"Pages visited: {final_stats.pages_visited}")
        logger.info(f"URLs discovered: {final_stats.urls_discovered}")
        logger.info(f"URLs in queue: {self._url_queue.size()}")
        logger.info(f"Files saved: {final_stats.files_saved}")
        logger.info(f"Files skipped (duplicates): {final_stats.files_skipped}")
        logger.info(f"Total requests: {fetcher_stats['total_requests']}")
        logger.info(f"Successful requests: {fetcher_stats['successful_requests']}")
        logger.info(f"Failed requests: {fetcher_stats['failed_requests']}")
        logger.info(f"Retries: {fetcher_stats['retries']}")
        logger.info(f"Duration: {final_stats.duration:.2f}s")
        logger.info("=" * 50)

        self._controller.emit_event(
            "crawl_complete",
            {
                "stats": {
                    "pages_visited": final_stats.pages_visited,
                    "files_saved": final_stats.files_saved,
                    "duration": final_stats.duration,
                }
            },
        )
