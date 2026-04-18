import asyncio
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class CrawlerState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


@dataclass
class CrawlStats:
    """Statistics for the crawl session."""

    pages_visited: int = 0
    urls_discovered: int = 0
    urls_queued: int = 0
    files_saved: int = 0
    files_skipped: int = 0
    bytes_downloaded: int = 0
    requests_total: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        if self.requests_total > 0:
            return self.requests_successful / self.requests_total * 100
        return 0.0


@dataclass
class CrawlEvent:
    """Event emitted during crawling."""

    type: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)


class EventEmitter:
    """Simple event emitter for crawl events."""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def on(self, event_type: str, callback: Callable[[CrawlEvent], None]):
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(callback)

    def off(self, event_type: str, callback: Callable[[CrawlEvent], None]):
        with self._lock:
            if event_type in self._listeners:
                self._listeners[event_type] = [
                    cb for cb in self._listeners[event_type] if cb != callback
                ]

    def emit(self, event: CrawlEvent):
        with self._lock:
            listeners = self._listeners.get(event.type, [])
        for callback in listeners:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event listener for {event.type}: {e}")


class Controller:
    """Controls and monitors the crawler."""

    def __init__(self):
        self._state = CrawlerState.IDLE
        self._state_lock = threading.RLock()
        self._stats = CrawlStats()
        self._stats_lock = threading.RLock()
        self._events = EventEmitter()
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop_event = asyncio.Event()
        self._stop_event.clear()

    @property
    def state(self) -> CrawlerState:
        with self._state_lock:
            return self._state

    def set_state(self, new_state: CrawlerState):
        with self._state_lock:
            old_state = self._state
            self._state = new_state
            logger.info(f"State changed: {old_state.value} -> {new_state.value}")
            self._events.emit(
                CrawlEvent(
                    type="state_changed",
                    data={"old": old_state.value, "new": new_state.value},
                )
            )

    def start(self):
        """Mark crawler as started."""
        self._stats.start_time = datetime.now()
        self.set_state(CrawlerState.RUNNING)
        self._pause_event.set()
        self._stop_event.clear()

    def pause(self):
        """Pause the crawler."""
        with self._state_lock:
            if self._state == CrawlerState.RUNNING:
                self._pause_event.clear()
                self.set_state(CrawlerState.PAUSED)
                logger.info("Crawler paused")

    def resume(self):
        """Resume the crawler."""
        with self._state_lock:
            if self._state == CrawlerState.PAUSED:
                self._pause_event.set()
                self.set_state(CrawlerState.RUNNING)
                logger.info("Crawler resumed")

    def stop(self):
        """Stop the crawler."""
        self._stop_event.set()
        self._pause_event.set()
        with self._state_lock:
            if self._state in (CrawlerState.RUNNING, CrawlerState.PAUSED):
                self.set_state(CrawlerState.STOPPED)
                self._stats.end_time = datetime.now()

    def complete(self):
        """Mark crawl as completed."""
        self._stats.end_time = datetime.now()
        self.set_state(CrawlerState.COMPLETED)

    async def wait_if_paused(self):
        """Wait if crawler is paused."""
        await self._pause_event.wait()

    def is_stopped(self) -> bool:
        return self._stop_event.is_set()

    def get_stats(self) -> CrawlStats:
        with self._stats_lock:
            return CrawlStats(
                pages_visited=self._stats.pages_visited,
                urls_discovered=self._stats.urls_discovered,
                urls_queued=self._stats.urls_queued,
                files_saved=self._stats.files_saved,
                files_skipped=self._stats.files_skipped,
                bytes_downloaded=self._stats.bytes_downloaded,
                requests_total=self._stats.requests_total,
                requests_successful=self._stats.requests_successful,
                requests_failed=self._stats.requests_failed,
                start_time=self._stats.start_time,
                end_time=self._stats.end_time,
            )

    def update_stats(self, **kwargs):
        with self._stats_lock:
            for key, value in kwargs.items():
                if hasattr(self._stats, key):
                    setattr(self._stats, key, value)

    def increment_stats(self, **kwargs):
        with self._stats_lock:
            for key, value in kwargs.items():
                if hasattr(self._stats, key):
                    current = getattr(self._stats, key)
                    setattr(self._stats, key, current + value)

    def on(self, event_type: str, callback: Callable[[CrawlEvent], None]):
        self._events.on(event_type, callback)

    def off(self, event_type: str, callback: Callable[[CrawlEvent], None]):
        self._events.off(event_type, callback)

    def emit_event(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        self._events.emit(CrawlEvent(type=event_type, data=data or {}))
