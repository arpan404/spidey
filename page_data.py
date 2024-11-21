from typing import List

class Pagedata:
    def __init__(self, current_url:str)->None:
        self.current_url = current_url
        self.data : str=None
        self.children_pages: List[Pagedata] = []
    
    def add_child_url(self, child_url:'Pagedata'):
        self.children_pages.append(child_url)
        