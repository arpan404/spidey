# Spidey Web Crawler

A robust, modular asynchronous web crawler built in Python that crawls websites and downloads files with specified extensions.

## Features

- **Parallel crawling** - Multiple async workers for URL fetching and file downloads
- **SHA256 deduplication** - Files saved as `{checksum}.{ext}`, no duplicates
- **Full control** - Pause, resume, stop, and monitor crawl progress in real-time
- **Events system** - Subscribe to progress, page crawled, file saved events
- **Rate limiting** - Token bucket rate limiter to avoid overwhelming servers
- **Retry with backoff** - Exponential backoff for failed requests
- **Modular architecture** - Separate components for fetch, parse, storage, queue
- **Thread-safe queues** - Safe concurrent access for URL and file queues

## Installation

```bash
uv pip install spidey
```

Or from source:

```bash
cd spidey
uv sync
```

## Quick Start

```python
from spidey import Spidey

crawler = Spidey.from_args(
    urls=["https://example.com"],
    extensions=[".svg", ".png", ".jpg"],
    max_pages=100,
    folder="data"
)

crawler.crawl()
```

## Full Control Example

```python
from spidey import Spidey
import threading
import time

# Create crawler
crawler = Spidey.from_args(
    urls=["https://example.com"],
    extensions=[".svg", ".png", ".jpg"],
    num_workers=5,
    max_pages=50,
    folder="data"
)

# Subscribe to events
crawler.on("progress", lambda e: print(f"Progress: {e.data}"))
crawler.on("file_saved", lambda e: print(f"Saved: {e.data['checksum'][:16]}..."))
crawler.on("crawl_complete", lambda e: print(f"Done! {e.data}"))

# Run in background thread for external control
t = threading.Thread(target=crawler.crawl)
t.start()

# Control while running
time.sleep(5)
crawler.pause()
print("Paused...")

time.sleep(2)
crawler.resume()
print("Resumed...")

# Or just run to completion
# crawler.crawl()

t.join()
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `urls` | List[str] | Required | Starting URLs to crawl |
| `extensions` | List[str] | Required | File extensions to download (e.g., `.svg`, `.png`) |
| `limited_to_domains` | bool | False | Limit crawling to initial domains only |
| `max_pages` | int | 1000 | Maximum number of pages to crawl |
| `sleep_time` | float | 0.0 | Delay between requests in seconds |
| `restricted_domains` | List[str] | [] | Domains to exclude from crawling |
| `folder` | str | "" | Output folder for downloaded files |
| `unique_file_name` | bool | True | Generate unique filenames |
| `num_workers` | int | 10 | Number of concurrent workers |
| `max_retries` | int | 3 | Maximum retry attempts for failed requests |
| `retry_delay` | float | 1.0 | Initial retry delay in seconds |
| `request_timeout` | float | 30.0 | HTTP request timeout in seconds |
| `max_concurrent_requests` | int | 50 | Maximum concurrent HTTP requests |

## Output Structure

Files are organized by extension and named with their SHA256 checksum:

```
data/
├── svg/
│   ├── a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.svg
│   └── f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2.svg
├── png/
│   ├── l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7.png
│   └── a1b2c3d4e5e6f7g8h9i0j1k2l3m4n5o6.png
├── jpg/
├── html/
└── css/
```

This approach ensures:
- No duplicate files are saved
- Easy deduplication across runs
- Quick file identification by checksum

## Events

Subscribe to events for real-time monitoring:

```python
crawler.on("state_changed", lambda e: print(f"State: {e.data['new']}"))
crawler.on("progress", lambda e: print(f"Pages: {e.data['pages_visited']}"))
crawler.on("page_crawled", lambda e: print(f"URL: {e.data['url']}"))
crawler.on("file_saved", lambda e: print(f"File: {e.data['checksum'][:16]}..."))
crawler.on("crawl_complete", lambda e: print(f"Complete: {e.data}"))
```

| Event | Data |
|-------|------|
| `state_changed` | `{old: str, new: str}` |
| `progress` | `{pages_visited, urls_queued, files_saved, files_skipped}` |
| `page_crawled` | `{url, new_urls, files}` |
| `file_saved` | `{url, checksum, size}` |
| `crawl_complete` | `{stats: {...}}` |

## Crawler States

```python
from spidey import CrawlerState

# Check current state
print(crawler.state)  # CrawlerState.RUNNING

# States: IDLE, RUNNING, PAUSED, STOPPED, COMPLETED
```

## Architecture

```
Spidey (Main Orchestrator)
    │
    ├── Controller (State, Stats, Events, Pause/Resume/Stop)
    │
    ├── URLQueue (Thread-safe URL batching)
    │       │
    │       └── URL Workers (async)
    │               │
    │               └── Fetcher (HTTP + retry + rate limit)
    │               └── Parser (extract URLs and files)
    │
    ├── FileQueue (Thread-safe file download queue)
    │       │
    │       └── File Workers (async)
    │               │
    │               └── Fetcher (download bytes)
    │               └── Storage (SHA256 dedup + write)
    │
    └── Storage (SHA256 deduplication)
```

### Components

| Component | Responsibility |
|-----------|---------------|
| `Config` | All settings with validation |
| `Controller` | State management, stats, events |
| `URLQueue` | Thread-safe URL batching |
| `FileQueue` | Thread-safe file download queue |
| `Fetcher` | HTTP client with retry & rate limiting |
| `Parser` | Extract links and files from HTML |
| `Storage` | SHA256 deduplication & file writes |

## License

MIT License - See LICENSE file