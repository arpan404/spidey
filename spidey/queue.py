import logging
import threading
from collections import deque
from typing import Dict, List, Set
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return ""


class URLQueue:
    """Thread-safe queue for URLs with batch operations and domain rotation."""

    def __init__(self):
        self._queues: Dict[str, deque] = {}
        self._domain_order: List[str] = []
        self._visited: Set[str] = set()
        self._lock = threading.RLock()

    def add_batch(self, urls: List[str]) -> int:
        """Add multiple URLs grouped by domain. Returns count of newly added URLs."""
        added = 0
        with self._lock:
            for url in urls:
                if url in self._visited:
                    continue

                domain = get_domain(url)
                if not domain:
                    continue

                if domain not in self._queues:
                    self._queues[domain] = deque()
                    self._domain_order.append(domain)

                if url not in self._queues[domain]:
                    self._queues[domain].append(url)
                    added += 1
        return added

    def get_batch(self, size: int) -> List[str]:
        """Get up to `size` URLs from the queue, rotating across domains."""
        batch = []
        with self._lock:
            if not self._domain_order:
                return batch

            domains_checked = 0
            max_domains = len(self._domain_order)

            while len(batch) < size and domains_checked < max_domains:
                domains_checked += 1

                domain = self._domain_order.pop(0)
                self._domain_order.append(domain)

                domain_queue = self._queues.get(domain)
                if not domain_queue or not domain_queue:
                    continue

                url = domain_queue.popleft()
                if url in self._visited:
                    continue

                self._visited.add(url)
                batch.append(url)

        return batch

    def mark_visited(self, urls: List[str]):
        """Mark URLs as visited without adding to queue."""
        with self._lock:
            self._visited.update(urls)

    def is_empty(self) -> bool:
        with self._lock:
            return sum(len(q) for q in self._queues.values()) == 0

    def size(self) -> int:
        with self._lock:
            return sum(len(q) for q in self._queues.values())

    def visited_count(self) -> int:
        with self._lock:
            return len(self._visited)

    def has_seen(self, url: str) -> bool:
        with self._lock:
            if url in self._visited:
                return True
            domain = get_domain(url)
            if domain in self._queues and url in self._queues[domain]:
                return True
            return False
