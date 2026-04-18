from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    """Configuration for the Spidey crawler."""

    urls: List[str]
    extensions: List[str]
    limited_to_domains: bool = False
    max_pages: int = 1000
    sleep_time: float = 0.0
    restricted_domains: List[str] = field(default_factory=list)
    folder: str = ""
    unique_file_name: bool = True
    num_workers: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0
    request_timeout: float = 30.0
    max_concurrent_requests: int = 50

    def __post_init__(self):
        self.extensions = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in self.extensions
        ]

    @property
    def allowed_extensions(self) -> set:
        return set(self.extensions)
