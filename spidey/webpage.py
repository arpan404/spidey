from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Webpage:
    """Represents a webpage with its content and discovered file URLs."""

    url: str
    html_data: Optional[str] = None
    files_url: list = field(default_factory=list)
    referrer: Optional[str] = None
    status_code: Optional[int] = None
    error: Optional[str] = None

    @property
    def current_url(self) -> str:
        return self.url

    @property
    def page_html_data(self):
        return self.html_data

    @page_html_data.setter
    def page_html_data(self, value):
        self.html_data = value