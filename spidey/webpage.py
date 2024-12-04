from typing import List, Dict, Tuple


class Webpage:
    def __init__(self, current_url: str) -> None:
        self.__current_url = current_url
        self.__page_html_data = None
        self.__files_url = []

    def set_data(self, data: Dict) -> 'Webpage':
        self.__page_html_data = data.get('page_html')
        self.__files_url = data.get('files_url', [])
        return self

    def get_values(self) -> Tuple[str, str, List[str]]:
        return self.__current_url, self.__page_html_data, self.__files_url

