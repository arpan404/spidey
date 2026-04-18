from dataclasses import dataclass, field
from typing import List, Optional
import random


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]


def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)


@dataclass
class Config:
    """Configuration for the Spidey crawler."""

    urls: List[str]
    extensions: List[str]
    limited_to_domains: bool = False
    max_pages: int = 1000
    sleep_time: float = 1.0
    restricted_domains: List[str] = field(default_factory=list)
    folder: str = ""
    unique_file_name: bool = True
    num_workers: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0
    request_timeout: float = 30.0
    max_concurrent_requests: int = 50
    respect_robots_txt: bool = True
    user_agent: Optional[str] = None
    min_delay_between_requests: float = 1.0

    def __post_init__(self):
        self.extensions = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in self.extensions
        ]

    @property
    def allowed_extensions(self) -> set:
        return set(self.extensions)
