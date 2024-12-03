from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="spidey",
    version="1.0.0",
    author="Arpan Bhandari",
    author_email="arpan@socioy.com",
    description="Spidey crawls the web and save the crawled data in json format locally.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arpan404/spidey",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",

    install_requires=[
        'aiofiles>=22.1.0',
        'aiohttp>=3.11.7',
        'beautifulsoup4>=4.12.3',
        'psutil>=5.9.0',
        'pybind11>=2.13.6',
        'requests>=2.32.3',
        'tldextract>=5.1.2',
        'validators>=0.18.2',
        # Dependencies that might be important
        'urllib3>=2.2.3',
        'charset-normalizer>=3.3.2',
        'idna>=3.7',
        'certifi>=2024.8.30',
    ],
)
