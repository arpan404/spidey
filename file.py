import os
import time
import json
import secrets
import tldextract
from pathlib import Path
from webpage import Webpage
from datetime import datetime


class File:
    @staticmethod
    def write(data: "Webpage"):
        try:
            root_folder: str = os.getcwd()
            folder: str = tldextract.extract(data.get_values()[0]).domain
            if (not os.path.exists(folder)):
                os.mkdir(folder)
            while True:
                filename: str = File().generate_filename()
                filepath = Path(root_folder).joinpath(
                    "data", datetime.now().date, folder, filename)
                if (not filepath.exists()):
                    break
            json_data = {
                "url": f"{data.get_values()[0]}",
                "data": f"{data.get_values()[1]}"
            }
            with open(filepath, "w") as file:
                json.dump(json_data, file, indent=4)
        except Exception as e:
            print(e)

    def generate_filename() -> str:
        timestamp = int(time.time())
        random_string = secrets.token_hex(10)
        return f"{timestamp}_{random_string}.json"
