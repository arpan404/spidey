from typing import List


class Webpage:
    def __init__(self, current_url: str) -> None:
        self.__current_url = current_url
        self.__page_data = None

    def set_data(self, page_data: str) -> 'Webpage':
        self.__page_data = page_data
        return self

    def get_values(self) -> List[str]:
        return self.__current_url, self.__page_data
