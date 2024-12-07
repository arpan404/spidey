import validators
from .file import File
from .aaa import Webpage
from typing import Set, List
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from collections import deque
from time import sleep


class Spidey:
    def __init__(self, initial_urls: List[str], download_files: bool = False, download_images: bool = False, restrict_to_domain: bool = False, max_depth: int = 10, chunk_size: int = 100, sleep_time: float = 0):
        self.__urls: Set[str] = deque(initial_urls)
        self.__visted_urls: Set[str] = set()
        self.__total_urls: int = len(initial_urls)
        self.__download_files = download_files
        self.__download_images = download_images
        self.__restrict_to_domain = restrict_to_domain
        self.__max_depth = max_depth
        self.__chunk_size = chunk_size
        self.__sleep_time = sleep_time

    def crawl(self):
        asyncio.run(self.__spider())

    async def __spider(self):
        try:
            while self.__urls:
                url = self.__urls.popleft()
                if url in self.__visted_urls:
                    continue

                response = await self.__fetch_data(url)
                if response is None:
                    continue

                page_data = BeautifulSoup(response, "html.parser")

                urls_in_page = set(
                    link.get("href") for link in page_data.find_all("a") if link.get("href"))

        except Exception as e:
            print(f"An error occurred: {e}")
