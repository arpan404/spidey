import psutil
import requests
import validators
from file import File
from webpage import Webpage
from typing import Set, List
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
import asyncio

class Spidey:
    