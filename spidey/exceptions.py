class SpideyError(Exception):
    """Base exception for Spidey."""
    pass


class FetchError(SpideyError):
    """Raised when fetching a URL fails."""
    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch {url}: {reason}")


class ParseError(SpideyError):
    """Raised when parsing HTML fails."""
    pass


class StorageError(SpideyError):
    """Raised when saving files fails."""
    pass


class ValidationError(SpideyError):
    """Raised when URL validation fails."""
    pass


class RateLimitError(SpideyError):
    """Raised when rate limit is exceeded."""
    pass