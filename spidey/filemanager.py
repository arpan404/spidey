import os
import time
import json
import secrets
import aiofiles
import tldextract
from spidey.webpage import Webpage
from datetime import datetime
from typing import List
import aiohttp
from urllib.parse import urlsplit


class File:
    def __init__(self, data: 'Webpage', folder: str):
        self.__data = data
        self.__folder = folder

    async def save(self, unique_file_name=True, extensions=[]):
        try:
            folder = os.path.join(self.__folder, datetime.now(
            ).date().isoformat(), tldextract.extract(self.data.current_url).domain)

            if not os.path.exists(folder):
                os.makedirs(folder)

            while True:
                filename: str = self.__generate_filename(".html")
                filepath = os.path.join(folder, filename)
                if not os.path.exists(filepath):
                    break

            async with aiofiles.open(filepath) as file:
                await file.write(self.__data.page_html_data)
            if extensions:
                for file in self.__data.files_url:
                    await self.__fetch_and_save_file(file, extensions, unique_file_name,)
        except Exception as e:
            print(e)

    async def __fetch_and_save_file(self,  url: str, extensions, unique_file_name=True):
        try:
            filename = os.path.basename(urlsplit(url).path)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content_disposition = response.headers.get(
                            'Content-Disposition', None)
                        if content_disposition:
                            filename = content_disposition.split('filename=')[
                                1].strip('"')
                            _, file_extension = os.path.splitext(filename)
                            if unique_file_name:
                                filename = self.__generate_filename(
                                    file_extension)
                            if file_extension in extensions:
                                filepath = os.path.join(
                                    self.folder, "files", filename)
                                async with aiofiles.open(filepath, 'wb') as file:
                                    async for chunk in response.content.iter_any(1024):
                                        if chunk:
                                            await file.write(chunk)
        except Exception as e:
            print("Exception occured while fetching and saving the files.")
            raise e

    def __generate_filename(self, extension) -> str:
        timestamp = int(time.time())
        random_string = secrets.token_hex(10)
        return f"{timestamp}_{random_string}.{extension}"
