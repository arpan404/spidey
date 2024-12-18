# Standard library imports
import asyncio
from collections import deque
from time import sleep
from typing import List, Set

# Third party imports
import aiohttp
from bs4 import BeautifulSoup
import tldextract
import validators

# Local imports
from spidey.file import File
from spidey.webpage import Webpage


class Spidey:
    """
    A web crawler class that crawls web pages and downloads files with specified extensions.
    """

    def __init__(
        self,
        urls: List[str],
        extensions: List[str],
        limited_to_domains: bool = False,
        max_pages: int = 1000,
        sleep_time: int = 0,
        restricted_domains: List[str] = [],
        folder="",
        unique_file_name=True,
    ):
        """
        Initialize the Spidey crawler.

        Args:
            urls: List of starting URLs to crawl
            extensions: List of file extensions to download
            limited_to_domains: Whether to limit crawling to initial domains only
            max_pages: Maximum number of pages to crawl
            sleep_time: Time to sleep between requests in seconds
            restricted_domains: List of domains to exclude from crawling
            folder: Output folder for downloaded files
            unique_file_name: Whether to generate unique filenames
        """
        self.__urls = deque(urls)
        self.__visited_urls: Set[str] = set()
        self.__total_urls: int = len(urls)
        self.__limited_to_domains = limited_to_domains
        self.__extensions = extensions
        self.__sleep_time = sleep_time
        self.__restricted_domains = restricted_domains
        self.__initial_domains = set()
        self.__max_pages: int = max_pages
        self.__folder = folder
        self.__unique_file_name = unique_file_name

    def crawl(self):
        """Start the crawling process by running the spider."""
        asyncio.run(self.__spider())

    async def __spider(self):
        """
        Main crawling logic that processes URLs and downloads content.
        Extracts links and files from pages while respecting domain restrictions.
        """
        try:
            # Get initial domains from starting URLs
            for url in self.__urls:
                self.__initial_domains.add(self.get_url_domain(url))

            while self.__urls:
                url = self.__urls.popleft()

                # Skip if URL was already visited
                if url in self.__visited_urls:
                    continue

                # Skip if domain is restricted
                if self.get_url_domain(url) in self.__restricted_domains:
                    continue

                # Skip if outside initial domains when limited
                if self.__limited_to_domains:
                    if self.get_url_domain(url) not in self.__initial_domains:
                        continue

                # Fetch and parse page content
                response = await self.__fetch_data(url)
                if response is None:
                    continue
                webpage = Webpage(url)

                page_data = BeautifulSoup(response, "html.parser")
                webpage.page_html_data = page_data

                # Extract and process links from page
                pages_urls = set(
                    link.get("href")
                    for link in page_data.find_all("a")
                    if link.get("href")
                )

                if pages_urls:
                    processed_urls = self.__process_urls(url, pages_urls)
                    print(f"\nFound {len(processed_urls)} URLs on {url}")
                    self.__total_urls += len(processed_urls)
                    self.__urls.extend(processed_urls)

                self.__visited_urls.add(url)

                # Extract URLs of embedded files (images, scripts, etc)
                files_urls = set(
                    link.get(attr)
                    for link in page_data.find_all(
                        ["img", "link", "script", "video", "source"]
                    )
                    for attr in ["href", "src"]
                    if link.get(attr)
                )

                if files_urls:
                    processed_urls = self.__process_urls(url, files_urls)
                    validated_urls = processed_urls.copy()
                    for url in processed_urls:
                        if url in self.__visited_urls:
                            validated_urls.remove(url)

                    webpage.files_url = validated_urls

                # Save webpage and associated files
                file = File(webpage, self.__folder)
                await file.save(self.__unique_file_name, self.__extensions)

                # Stop if max pages reached
                if len(self.__visited_urls) == self.__max_pages:
                    break

                sleep(self.__sleep_time)
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_url_domain(self, url):
        """
        Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain name with TLD (e.g. 'example.com')
        """
        extracted = tldextract.extract(url)
        return f"{extracted.domain}.{extracted.suffix}"

    async def __fetch_data(self, url: str):
        """
        Fetch webpage content from URL.

        Args:
            url: URL to fetch

        Returns:
            Page content as text, or None if fetch fails
        """
        try:
            if not isinstance(url, str):
                raise ValueError(
                    f"The URL must be a string, but got {
                                 type(url).__name__}"
                )
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
        except:
            return None

    def __is_url(self, url: str) -> bool:
        """
        Validate if string is a valid URL.

        Args:
            url: String to validate

        Returns:
            True if valid URL, False otherwise
        """
        try:
            return validators.url(url)
        except Exception as e:
            raise e

    def __process_urls(self, current_url: str, urls: Set[str]) -> Set[str]:
        """
        Process and normalize relative URLs to absolute URLs.

        Args:
            current_url: Base URL for resolving relative URLs
            urls: Set of URLs to process

        Returns:
            Set of processed absolute URLs
        """
        try:
            processed_urls: Set[str] = set()
            for url in urls:
                if url is None:
                    continue

                if self.__is_url(url):
                    processed_urls.add(url)
                else:
                    if url[0] != "#":
                        url_components = current_url.strip().split("/")
                        url_components.pop()

                        if url.startswith("../"):
                            total_dashes = url.count("../")
                            for i in range(total_dashes):
                                url_components.pop()
                                url.replace("../", "", 1)
                                if not url.startswith("../"):
                                    break

                        if url[0] == "/":
                            url = url[1:]
                        url_components.append(url)
                        new_url = "/".join(url_components)
                        processed_urls.add(new_url)
        except Exception as e:
            print(e)

        return processed_urls
