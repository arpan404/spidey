import psutil
import requests
import validators
from file import File
from webpage import Webpage
from typing import Set, List
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading


class Spidey:
    def __init__(self, initial_urls: List[str]):
        self.__urls: Set[str] = set(initial_urls)
        available_threads = psutil.cpu_count(logical=True)
        self.__visted_urls: Set[str] = set()
        self.executors = ThreadPoolExecutor(max_workers=available_threads)
        self.lock = threading.Lock()

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
            futures.append(self.executors.submit(self.__process_pages))

        for future in futures:
            future.result()

    def __process_pages(self):
        try:
            with self.lock:
                for url in self.__urls:
                    if url in self.__visted_urls:
                        continue

                    page_data = requests.get(url)

                    if (page_data.status_code != 200):
                        continue

                    page_data = BeautifulSoup(page_data.content, "html.parser")

                    File.write(Webpage(url).set_data(page_data))

                    urls_in_page = set([link.get("href")
                                        for link in page_data.find_all("a")])

                    if not urls_in_page:
                        continue
                    processed_urls = self.__process_urls(url, urls_in_page)
                    # self.__urls.update(processed_urls)
                    self.__visted_urls.add(url)

        except Exception as e:
            print(e)

        finally:
            self.executors.submit

    def __is_url(self, url: str) -> bool:
        return validators.url(url)

    def __process_urls(self, current_url: str, urls: Set[str]) -> Set[str]:
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
                    url_components.append(url)
                    new_url = "/".join(url_components)
                    processed_urls.add(new_url)

        return processed_urls
