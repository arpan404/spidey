import requests
from bs4 import BeautifulSoup
from typing import Set, List
import re
from concurrent.futures import ThreadPoolExecutor

from page_data import Pagedata


class Spidey:
    def __init__(self, initial_url: str):
        self.root = Pagedata(initial_url)
        self.visted_url: Set[str] = set()
        self.executor = ThreadPoolExecutor(max_workers=8) 
    def start_crawl(self):
        self.__crawl(self.root)
        self.executor.shutdown(wait=True)


    def __crawl(self, pagedata: Pagedata):
        try:
            response_data = requests.get(pagedata.current_url)
            status_code = response_data.status_code
            if (status_code != 200):
                return
            response_content = BeautifulSoup(
                response_data.content, "html.parser")
            urls_found = [link.get("href")
                          for link in response_content.find_all("a")]
            if len(urls_found) == 0:
                return

            formatted_urls = self.__formatURL(pagedata.current_url, urls_found)
            if len(formatted_urls) == 0:
                return
            for url in formatted_urls:
                if url not in self.visted_url:
                    self.visted_url.add(url)
                    child_page = Pagedata(url)
                    pagedata.children_pages.append(child_page)
                    self.__crawl(child_page)

                    self.executor.submit(self.__crawl, child_page)
        except Exception as e:
            print(e)

    def __formatURL(self, current_url: str, urls: List[str]) -> Set[str]:
        url_pattern = re.compile(
            r'^(https?:\/\/)'
            r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            r'(\/[^\s]*)?$'
        )
        formatted_urls = set()
        for url in urls:
            if url is None:
                continue
            if url_pattern.match(url):
                formatted_urls.add(url)
            else:
                if url[0] != "#":
                    url_components = current_url.strip().split("/")
                    url_components.pop()
                    url_components.append(url)
                    new_url = "/".join(url_components)
                    formatted_urls.add(new_url)

        return formatted_urls
