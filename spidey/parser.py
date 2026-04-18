import logging
from typing import List, Set, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import validators

from .exceptions import ValidationError


logger = logging.getLogger(__name__)


class Parser:
    """Parses HTML content and extracts URLs and file links."""

    @staticmethod
    def extract_page_urls(html: str, base_url: str) -> Set[str]:
        """Extract all anchor links from HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            urls = set()

            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href and not href.startswith("#"):
                    absolute_url = urljoin(base_url, href)
                    if validators.url(absolute_url):
                        urls.add(absolute_url)

            return urls
        except Exception as e:
            logger.error(f"Failed to extract page URLs: {e}")
            return set()

    @staticmethod
    def extract_file_urls(html: str, base_url: str) -> Set[str]:
        """Extract file URLs from img, link, script, video, source tags."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            urls = set()
            selectors = ["img", "link", "script", "video", "source"]
            attributes = ["href", "src"]

            for tag in soup.find_all(selectors):
                for attr in attributes:
                    if tag.has_attr(attr):
                        href = tag[attr]
                        if href:
                            absolute_url = urljoin(base_url, href)
                            urls.add(absolute_url)

            return urls
        except Exception as e:
            logger.error(f"Failed to extract file URLs: {e}")
            return set()

    @staticmethod
    def get_content_type(html: str) -> Optional[str]:
        """Detect content type from HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            meta = soup.find("meta", {"http-equiv": lambda x: x and x.lower() == "content-type"})
            if meta:
                return meta.get("content", "")

            content_type_tag = soup.find("meta", {"name": "generator"})
            if content_type_tag:
                return content_type_tag.get("content", "")

            return "text/html"
        except Exception:
            return "text/html"

    @staticmethod
    def extract_title(html: str) -> Optional[str]:
        """Extract page title."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.find("title")
            return title.text.strip() if title else None
        except Exception:
            return None