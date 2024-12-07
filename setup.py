from setuptools import setup, find_packages
import os

# Read version from __init__.py
with open(os.path.join("spidey", "__init__.py"), "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

# Read README.md for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements.txt for dependencies
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

setup(
    name="spidey",
    version=version,
    author="Arpan Bhandari",
    author_email="arpan@socioy.com",
    description="An asynchronous web crawler that downloads files with specified extensions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arpan404/spidey",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    package_data={
        "spidey": ["py.typed"],
    },
    keywords="web crawler spider async download files",
    project_urls={
        "Bug Reports": "https://github.com/arpan404/spidey/issues",
        "Source": "https://github.com/arpan404/spidey",
    },
)
