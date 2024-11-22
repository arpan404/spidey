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

        urls_to_process = list(self.__urls)
        for url in urls_to_process:
            futures.append(self.executors.submit(self.__process_pages))

        for future in futures:
            future.result()

    def __process_pages(self):
        try:
            with self.lock:
                while True:
                    if self.__urls:
                        url = list(self.__urls)[0]
                        self.__urls.remove(url)
                    if url in self.__visted_urls:
                        continue
                    try:
                        page_data = requests.get(url)
                    except Exception as e:
                        raise e
                    if (page_data.status_code != 200):
                        continue

                    page_data = BeautifulSoup(page_data.content, "html.parser")

                    File.write(Webpage(url).set_data(page_data))

                    urls_in_page = set([link.get("href")
                                        for link in page_data.find_all("a")])

                    if not urls_in_page:
                        continue
                    processed_urls = self.__process_urls(url, urls_in_page)
                    print(f"\nFounded {len(processed_urls)} urls in {url}")
                    self.__urls.update(processed_urls)
                    self.__visted_urls.add(url)
                    print(f"\nCompleted crawling {
                          len(self.__visted_urls)} / {len(self.__urls)+len(self.__visted_urls)} webpages")

        except Exception as e:
            print(e.with_traceback)

        finally:
            self.executors.submit

    def __is_url(self, url: str) -> bool:
        return validators.url(url)

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
                        if (url.startswith("../../")):
                            url_components.pop()
                            url_components.pop()
                            url.replace("../../", "", 1)
                        if url.startswith("../"):
                            url_components.pop()
                            url.replace("../", "", 1)
                        if url[0] == "/":
                            url = url[1:]
                        url_components.append(url)
                        new_url = "/".join(url_components)
                        processed_urls.add(new_url)
        except Exception as e:
            print(e.with_traceback)

        return processed_urls
