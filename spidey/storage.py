import hashlib
import logging
import os
from pathlib import Path
from typing import Optional, Set
from urllib.parse import urlsplit

import aiofiles


logger = logging.getLogger(__name__)


class Storage:
    """Handles file storage with deduplication via SHA256 checksums."""

    def __init__(self, folder: str):
        self._folder = Path(folder)
        self._processed_checksums: Set[str] = set()
        self._stats = {"files_saved": 0, "files_skipped": 0, "bytes_written": 0}

    def _compute_checksum(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _get_extension(
        self,
        url: str,
        content: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> str:
        """Determine file extension from URL, content, or content-type."""
        parsed = urlsplit(url)
        ext = os.path.splitext(parsed.path)[1].lower()

        if not ext and content_type:
            ext_map = {
                "image/svg+xml": ".svg",
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/gif": ".gif",
                "image/webp": ".webp",
                "text/html": ".html",
                "text/css": ".css",
                "application/javascript": ".js",
                "application/json": ".json",
                "application/xml": ".xml",
                "application/pdf": ".pdf",
            }
            ext = ext_map.get(content_type, "")

        if not ext:
            ext = ".bin"

        return ext

    def is_duplicate(self, checksum: str) -> bool:
        """Check if checksum was already processed (in-memory only)."""
        return checksum in self._processed_checksums

    async def save_file(
        self, url: str, content: bytes, content_type: Optional[str] = None
    ) -> Optional[str]:
        """Save file with checksum filename. Returns path if saved, None if duplicate/skipped."""
        checksum = self._compute_checksum(content)

        if checksum in self._processed_checksums:
            self._stats["files_skipped"] += 1
            logger.debug(f"Skipping duplicate: {checksum[:16]}...")
            return None

        ext = self._get_extension(url, content, content_type)
        filename = f"{checksum}{ext}"
        ext_folder = ext.lstrip(".")

        save_dir = self._folder / ext_folder
        save_dir.mkdir(parents=True, exist_ok=True)

        filepath = save_dir / filename

        try:
            async with aiofiles.open(filepath, "wb") as f:
                await f.write(content)

            self._processed_checksums.add(checksum)
            self._stats["files_saved"] += 1
            self._stats["bytes_written"] += len(content)

            logger.info(f"Saved: {filename} ({len(content)} bytes)")
            return str(filepath)

        except FileExistsError:
            self._processed_checksums.add(checksum)
            self._stats["files_skipped"] += 1
            logger.debug(f"File already exists: {filename}")
            return None

        except Exception as e:
            logger.warning(f"Failed to save {filename}: {e}")
            return None

    async def save_html(self, url: str, html: str, checksum: str) -> Optional[str]:
        """Save HTML file with checksum filename."""
        filename = f"{checksum}.html"
        ext_folder = "html"

        save_dir = self._folder / ext_folder
        save_dir.mkdir(parents=True, exist_ok=True)

        filepath = save_dir / filename

        try:
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(html)

            logger.debug(f"Saved HTML: {filename}")
            return str(filepath)

        except FileExistsError:
            logger.debug(f"HTML already exists: {filename}")
            return None

        except Exception as e:
            logger.warning(f"Failed to save HTML {filename}: {e}")
            return None

    def get_stats(self) -> dict:
        return self._stats.copy()
