from typing import List, Set, Tuple


class Webpage:
    def __init__(self, current_url: str) -> None:
        self.current_url = current_url
        self.page_html_data = None
        self.files_url = set()