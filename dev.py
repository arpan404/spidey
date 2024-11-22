import requests
from file import File
from webpage import Webpage
from typing import Set, List
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import psutil


class Spidey:
    def __init__(self, initial_urls: List[str]):
        self.__urls: List[str] = initial_urls
        available_threads = psutil.cpu_count(logical=True)
        self.executors = ThreadPoolExecutor(max_workers=available_threads)

    def crawl(self):
        try:
            self.__spider()
        except Exception as e:
            print(f"Error during crawling: {e}")
        finally:
            self.executors.shutdown(wait=True)

    def __spider(self):
        futures = []

        for url in self.__urls:
            futures.append(self.executors.submit(self.__process_page, url))

        for future in futures:
            future.result()

    def __process_pages(self):
        try:
            for url in self.__urls:
                page_data = requests.get(url)

                if (page_data.status_code != 200):
                    continue

                page_data = BeautifulSoup(page_data.content, "html.parser")

                urls_in_page = [link.get("href")
                                for link in page_data.find_all("a")]

                # self.__urls = list(set(self.__urls.extend(urls_in_page)))

        except Exception as e:
            print(e)
