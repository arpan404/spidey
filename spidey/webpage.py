from typing import Set


class Webpage:
    def __init__(self, current_url: str) -> None:
        """
        Initialize a Webpage object.

        Args:
            current_url: URL of the webpage to process
        """
        self.current_url = current_url  # Store the URL being processed
        self.page_html_data = None      # Will store the HTML content of the page
        self.files_url = set()          # Set to store URLs of files found on the page
