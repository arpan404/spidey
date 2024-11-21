import requests
from bs4 import BeautifulSoup
from typing import Set

from page_data import Pagedata


class Spidey:
    def __init__(self, initial_url: str):
        self.root = Pagedata(initial_url)
        self.visted_url: Set[str] = set()

    def crawl(self):
        try:
            response_data = requests.get(self.root.current_url)
            status_code = response_data.status_code
            if (status_code != 200):
                return
            response_content = BeautifulSoup(
                response_data.content, "html.parser")
            print([link.get("href") for link in response_content.find_all("a")])
        except Exception as e:
            print(e)
