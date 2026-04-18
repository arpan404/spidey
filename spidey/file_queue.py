import logging
import threading
from queue import Queue
from typing import List, Optional, Tuple, Set


logger = logging.getLogger(__name__)


class FileQueue:
    """Thread-safe queue for files to download."""

    def __init__(self):
        self._queue: Queue = Queue()
        self._lock = threading.Lock()
        self._processed: Set[str] = set()

    def put(self, url: str, referrer: str):
        """Add a file to the download queue."""
        self._queue.put((url, referrer))

    def put_batch(self, items: List[Tuple[str, str]]):
        """Add multiple files to the download queue."""
        for url, referrer in items:
            self._queue.put((url, referrer))

    def get(self) -> Optional[Tuple[str, str]]:
        """Get next file task. Returns (url, referrer) or None."""
        if self._queue.empty():
            return None
        return self._queue.get()

    def get_batch(self, size: int) -> List[Tuple[str, str]]:
        """Get up to `size` file tasks."""
        batch = []
        for _ in range(min(size, self._queue.qsize())):
            if not self._queue.empty():
                batch.append(self._queue.get())
        return batch

    def mark_processed(self, checksum: str):
        """Mark a file as processed by its checksum."""
        with self._lock:
            self._processed.add(checksum)

    def is_processed(self, checksum: str) -> bool:
        """Check if file with this checksum was already processed."""
        with self._lock:
            return checksum in self._processed

    def is_empty(self) -> bool:
        return self._queue.empty()

    def size(self) -> int:
        return self._queue.qsize()