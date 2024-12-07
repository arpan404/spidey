# Standard library imports
import json
import os
import secrets
import time
from datetime import datetime
from typing import List
from urllib.parse import urlsplit

# Third party imports
import aiofiles
import aiohttp
import tldextract

# Local imports
from spidey.webpage import Webpage


class File:
    """
    A class to handle saving webpage data and associated files to disk.
    """

    def __init__(self, data: "Webpage", folder: str):
        """
        Initialize File object with webpage data and output folder.

        Args:
            data: Webpage object containing the page data
            folder: Base folder path where files will be saved
        """
        self.__data = data
        self.__folder = folder
        self.__data_written = {}

    async def save(self, unique_file_name=True, extensions=[]):
        """
        Save webpage HTML and optionally download linked files with specified extensions.

        Args:
            unique_file_name: Whether to generate unique filenames (default True)
            extensions: List of file extensions to download (e.g. ['.pdf', '.doc'])
        """
        try:
            # Create folder structure: base_folder/date/domain
            self.__domain_folder = os.path.join(
                self.__folder,
                datetime.now().date().isoformat(),
                tldextract.extract(self.__data.current_url).domain,
            )

            if not os.path.exists(self.__domain_folder):
                os.makedirs(self.__domain_folder)

            # Generate unique filename for the HTML file
            while True:
                filename: str = self.__generate_filename("html")
                filepath = os.path.join(self.__domain_folder, filename)
                if not os.path.exists(filepath):
                    files_folder_path = os.path.join(self.__domain_folder, "files")
                    if not os.path.exists(files_folder_path):
                        os.makedirs(files_folder_path)
                    break

            # Save the HTML content
            async with aiofiles.open(filepath, "w") as file:
                await file.write(str(self.__data.page_html_data))
                self.__data_written["url"] = self.__data.current_url
                self.__data_written["file_name"] = filename

            # Download and save associated files if extensions are specified
            if extensions:
                self.__data_written["files"] = []
                if self.__data.files_url:
                    for file in list(self.__data.files_url):
                        await self.__fetch_and_save_file(
                            file, extensions, unique_file_name
                        )

            # Save metadata to JSON file
            if len(filename.split(".")) == 1:
                details_filepath = os.path.join(
                    self.__domain_folder, f"{filename}.json"
                )
            else:
                details_filepath = os.path.join(
                    self.__domain_folder,
                    f"{
                                                filename.split(".")[0]}.json",
                )
            async with aiofiles.open(details_filepath, "w") as file:
                await file.write(json.dumps(self.__data_written, indent=4))

        except Exception as e:
            print(e)

    async def __fetch_and_save_file(self, url: str, extensions, unique_file_name=True):
        """
        Download and save a file from a given URL.

        Args:
            url: URL of the file to download
            extensions: List of allowed file extensions
            unique_file_name: Whether to generate unique filename (default True)
        """
        try:
            filename = os.path.basename(urlsplit(url).path)
            org_filename = filename
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Try to get filename from Content-Disposition header
                        content_disposition = response.headers.get(
                            "Content-Disposition", None
                        )
                        if content_disposition:
                            filename = content_disposition.split("filename=")[1].strip(
                                '"'
                            )
                            _, file_extension = os.path.splitext(filename)
                            org_filename = filename
                        else:
                            filename = os.path.basename(urlsplit(url).path)
                            _, file_extension = os.path.splitext(filename)

                        # Generate unique filename if requested
                        if unique_file_name:
                            filename = self.__generate_filename(
                                file_extension.strip(".")
                            )

                        # Save file if extension matches allowed list
                        if file_extension in extensions:
                            filepath = os.path.join(
                                self.__domain_folder, "files", filename
                            )
                            self.__data_written["files"].append(
                                {
                                    "url": url,
                                    "original_name": org_filename,
                                    "saved_as": filename,
                                }
                            )

                            # Save file contents in chunks
                            async with aiofiles.open(filepath, "wb") as file:
                                async for chunk in response.content.iter_any():
                                    if chunk:
                                        await file.write(chunk)
        except Exception as e:
            print("Exception occured while fetching and saving the files.")
            print(e)

    def __generate_filename(self, extension) -> str:
        """
        Generate a unique filename using timestamp and random string.

        Args:
            extension: File extension to append

        Returns:
            String containing unique filename with extension
        """
        timestamp = int(time.time())
        random_string = secrets.token_hex(10)
        return f"{timestamp}_{random_string}.{extension}"
