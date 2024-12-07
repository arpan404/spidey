import os
import time
import secrets
import aiofiles
import tldextract
from spidey.webpage import Webpage
from datetime import datetime
from typing import List
import aiohttp
from urllib.parse import urlsplit
import json


class File:
    def __init__(self, data: 'Webpage', folder: str):
        self.__data = data
        self.__folder = folder
        self.__data_written = {}

    async def save(self, unique_file_name=True, extensions=[]):
        try:
            self.__domain_folder = os.path.join(self.__folder, datetime.now(
            ).date().isoformat(), tldextract.extract(self.__data.current_url).domain)

            if not os.path.exists(self.__domain_folder):
                os.makedirs(self.__domain_folder)

            while True:
                filename: str = self.__generate_filename("html")
                filepath = os.path.join(self.__domain_folder, filename)
                if not os.path.exists(filepath):
                    files_folder_path = os.path.join(
                        self.__domain_folder, "files")
                    if not os.path.exists(files_folder_path):
                        os.makedirs(files_folder_path)
                    break

            async with aiofiles.open(filepath, "w") as file:
                await file.write(str(self.__data.page_html_data))
                self.__data_written["url"] = self.__data.current_url
                self.__data_written["file_name"] = filename

            if extensions:
                self.__data_written["files"] = []
                if self.__data.files_url:
                    for file in list(self.__data.files_url):
                        await self.__fetch_and_save_file(file, extensions, unique_file_name)
            if len(filename.split(".")) == 1:
                details_filepath = os.path.join(
                    self.__domain_folder, f"{filename}.json")
            else:
                details_filepath = os.path.join(self.__domain_folder, f"{
                                                filename.split(".")[0]}.json")
            async with aiofiles.open(details_filepath, "w") as file:
                await file.write(json.dumps(self.__data_written, indent=4))

        except Exception as e:
            print(e)

    async def __fetch_and_save_file(self,  url: str, extensions, unique_file_name=True):
        try:
            filename = os.path.basename(urlsplit(url).path)
            org_filename = filename
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content_disposition = response.headers.get(
                            'Content-Disposition', None)
                        if content_disposition:
                            filename = content_disposition.split('filename=')[
                                1].strip('"')
                            _, file_extension = os.path.splitext(filename)
                            org_filename = filename
                        else:
                            filename = os.path.basename(urlsplit(url).path)
                            _, file_extension = os.path.splitext(filename)
                        if unique_file_name:
                            filename = self.__generate_filename(
                                file_extension.strip("."))
                        if file_extension in extensions:
                            filepath = os.path.join(
                                self.__domain_folder, "files", filename)
                            self.__data_written["files"].append(
                                {
                                    "url": url,
                                    "original_name": org_filename,
                                    "saved_as": filename
                                }
                            )

                            async with aiofiles.open(filepath, 'wb') as file:
                                async for chunk in response.content.iter_any():
                                    if chunk:
                                        await file.write(chunk)
        except Exception as e:
            print("Exception occured while fetching and saving the files.")
            print(e)

    def __generate_filename(self, extension) -> str:
        timestamp = int(time.time())
        random_string = secrets.token_hex(10)
        return f"{timestamp}_{random_string}.{extension}"
