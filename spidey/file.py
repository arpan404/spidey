import os
import time
import json
import secrets
import aiofiles
import tldextract
from .webpage import Webpage
from datetime import datetime


class File:
    @staticmethod
    async def write(data: "Webpage"):
        try:
            root_folder: str = os.getcwd()
            folder: str = os.path.join(root_folder, "data", datetime.now(
            ).date().isoformat(), tldextract.extract(data.get_values()[0]).domain)
            if not os.path.exists(folder):
                os.makedirs(folder)
            while True:
                filename: str = File().__generate_filename()
                filepath = os.path.join(folder, filename)
                if not os.path.exists(filepath):
                    break
            json_data = {
                "url": f"{data.get_values()[0]}",
                "data": f"{data.get_values()[1]}"
            }
            async with aiofiles.open(filepath, "w") as file:
                await file.write(json.dumps(json_data, indent=4))
        except Exception as e:
            print(e)

    def __generate_filename(self) -> str:
        timestamp = int(time.time())
        random_string = secrets.token_hex(10)
        return f"{timestamp}_{random_string}.json"
