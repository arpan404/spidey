from typing import List, Set, Tuple


class Webpage:
    def __init__(self, current_url: str) -> None:
        self.__current_url = current_url
        self.__page_html_data = None
        self.__files_url = set()

    def set_data(self, page_html_data: str, files_url: Set[str] = set()) -> 'Webpage':
        self.__page_html_data = page_html_data
        self.__files_url = files_url
        return self

    def get_values(self) -> Tuple[str, str, List[str]]:
        return self.__current_url, self.__page_html_data, self.__files_url
