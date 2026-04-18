import logging
import threading
from collections import deque
from typing import List, Set


logger = logging.getLogger(__name__)


class URLQueue:
    """Thread-safe queue for URLs with batch operations."""

    def __init__(self):
        self._queue: deque = deque()
        self._visited: Set[str] = set()
        self._lock = threading.RLock()

    def add_batch(self, urls: List[str]) -> int:
        """Add multiple URLs. Returns count of newly added URLs."""
        added = 0
        with self._lock:
            for url in urls:
                if url not in self._visited and url not in self._queue:
                    self._queue.append(url)
                    added += 1
        return added

    def get_batch(self, size: int) -> List[str]:
        """Get up to `size` URLs from the queue."""
        batch = []
        with self._lock:
            for _ in range(min(size, len(self._queue))):
                if self._queue:
                    url = self._queue.popleft()
                    if url not in self._visited:
                        batch.append(url)
                        self._visited.add(url)
        return batch

    def mark_visited(self, urls: List[str]):
        """Mark URLs as visited without adding to queue."""
        with self._lock:
            self._visited.update(urls)

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._queue) == 0

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def visited_count(self) -> int:
        with self._lock:
            return len(self._visited)

    def has_seen(self, url: str) -> bool:
        with self._lock:
            return url in self._visited or url in self._queue
