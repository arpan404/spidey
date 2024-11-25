import psutil
import requests
import validators
from file import File
from webpage import Webpage
from typing import Set, List
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
import asyncio
import aiohttp
from collections import deque


class Spidey:
    def __init__(self, initial_urls: List[str]):
        self.__urls: Set[str] = deque(initial_urls)
        self.__visted_urls: Set[str] = set()
        self.__total_urls: int = len(initial_urls)

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
                await File.write(Webpage(url).set_data(page_data))

                urls_in_page = set(
                    link.get("href") for link in page_data.find_all("a") if link.get("href"))

                if urls_in_page:
                    processed_urls = self.__process_urls(url, urls_in_page)
                    print(f"\nFound {len(processed_urls)} URLs on {url}")
                    self.__total_urls += len(processed_urls)
                    self.__urls.extend(processed_urls)

                self.__visted_urls.add(url)
                print(f"\nCompleted crawling {len(
                    self.__visted_urls)} / {len(self.__urls) + len(self.__visted_urls)} webpages")
        except Exception as e:
            print(f"An error occurred: {e}")

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
