import tldextract
import validators
from spidey.filemanager import File
from spidey.webpage import Webpage
from typing import Set, List
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from collections import deque
from time import sleep


class Spidey:

    def __init__(self, urls: List[str], extensions: List[str], limited_to_domains: bool = False, max_pages: int = 1000, sleep_time: int = 0, restricted_domains: List[str] = [], folder=""):
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

    def crawl(self):
        asyncio.run(self.__spider())

    async def __spider(self):
        try:
            for url in self.__urls:
                self.__initial_domains.add(self.get_url_domain(url))

            while self.__urls:

                url = self.__urls.popleft()

                if url in self.__visted_urls:
                    continue

                if self.get_url_domain(url) in self.__restricted_domains:
                    continue

                if self.__limited_to_domains:
                    if self.get_url_domain(url) not in self.__initial_domains:
                        continue

                response = await self.__fetch_data(url)
                if response is None:
                    continue
                webpage = Webpage(url, self.__folder)

                page_data = BeautifulSoup(response, "html.parser")
                webpage.page_html_data = page_data

                pages_urls = set(
                    link.get("href") for link in page_data.find_all("a") if link.get("href"))

                if pages_urls:
                    processed_urls = self.__process_urls(url, pages_urls)
                    print(f"\nFound {len(processed_urls)} URLs on {url}")
                    self.__total_urls += len(processed_urls)
                    self.__urls.extend(processed_urls)

                self.__visited_urls.add(url)

                files_urls = set(link.get(attr) for link in page_data.find_all(
                    ["img", "link", "script", "video", "source"]) for attr in ["href", "src"] if link.get(attr))

                if files_urls:
                    processed_urls = self.__process_urls(url, pages_urls)
                    webpage.files_url = processed_urls
                webpage.save(unique_file_names=True)
                if len(self.__visited_urls) == self.__max_pages:
                    break
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_url_domain(self, url):
        extracted = tldextract.extract(url)
        return f"{extracted.domain}.{extracted.suffix}"

    async def __fetch_data(self, url: str):
        try:
            if not isinstance(url, str):
                raise ValueError(f"The URL must be a string, but got {
                                 type(url).__name__}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
        except:
            return None

    def __is_url(self, url: str) -> bool:
        try:
            return validators.url(url)
        except Exception as e:
            raise e

    def __process_urls(self, current_url: str, urls: Set[str]) -> Set[str]:
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

                        if (url.startswith("../")):
                            total_dashes = url.count("../")
                            for i in range(total_dashes):
                                url_components.pop()
                                url.replace("../", "", 1)
                                if (not url.startswith("../")):
                                    break

                        if url[0] == "/":
                            url = url[1:]
                        url_components.append(url)
                        new_url = "/".join(url_components)
                        processed_urls.add(new_url)
        except Exception as e:
            print(e.with_traceback)

        return processed_urls
