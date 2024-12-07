# Spidey Web Crawler

Spidey is a powerful asynchronous web crawler built in Python that can crawl websites and download files with specified extensions. It's designed to be efficient, configurable, and easy to use.

## Features

- ⚡ Asynchronous web crawling using aiohttp
- 📂 Download files with specific extensions
- 🔒 Domain restrictions and filtering
- ⚙️ Configurable crawl limits and delays
- 📁 Organized file storage by date and domain
- 🔄 Unique file naming system
- 🕸️ Support for relative and absolute URLs
- 🗃️ Automatic metadata generation

## Example Usage

```python
import spidey
import os

folder = os.path.join(os.getcwd(), "data")
urls_to_crawl = ["https://example.com"]
crawler = spidey.Spidey(urls=urls_to_crawl, extensions=[".png", ".js", ".css"], limited_to_domains=False, max_pages=100, sleep_time=0, folder=folder)

crawler.crawl()
```

## Configuration Options

| Parameter            | Type      | Description                        | Default  |
| -------------------- | --------- | ---------------------------------- | -------- |
| `urls`               | List[str] | Starting URLs to crawl             | Required |
| `extensions`         | List[str] | File extensions to download        | Required |
| `limited_to_domains` | bool      | Limit crawling to initial domains  | False    |
| `max_pages`          | int       | Maximum number of pages to crawl   | 1000     |
| `sleep_time`         | int       | Delay between requests (seconds)   | 0        |
| `restricted_domains` | List[str] | Domains to exclude from crawling   | []       |
| `folder`             | str       | Output folder for downloaded files | ""       |
| `unique_file_name`   | bool      | Generate unique filenames          | True     |

## Output Structure

Files are saved in the following structure:

```
data/
    example/
        files/
            filename.ext
        filename.html
        filename.json
```

## Features in Detail

### File Downloads
- Automatically downloads files with specified extensions (.pdf, .jpg, .png, etc.)
- Preserves original filenames with optional unique ID generation
- Organizes downloads by date and domain for easy management
- Stores metadata including source URL and timestamp
- Handles both direct file links and embedded resources (images, scripts, stylesheets)

### Domain Control
- Flexible domain scoping with multiple options:
  - Crawl any linked domain
  - Restrict to initial domain list only
  - Exclude specific domains via blocklist
- Smart domain extraction using tldextract
- Proper handling of subdomains and TLDs
- Validation of domain names and URLs

### Asynchronous Operation
- High-performance concurrent crawling with aiohttp
- Non-blocking I/O for optimal resource usage
- Configurable delays between requests to control load
- Graceful error handling and recovery
- Progress tracking and status reporting
- Memory-efficient processing of large sites


## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contributing

We welcome and appreciate contributions to Spidey! Whether you're fixing bugs, adding features, or improving documentation, here's how you can contribute:

1. Fork the repository to your GitHub account
2. Create a descriptive feature branch (`git checkout -b feature/add-retry-logic`)
3. Make focused, well-tested changes
4. Commit with clear messages (`git commit -m 'Add request retry logic with exponential backoff'`) 
5. Push changes to your fork (`git push origin feature/add-retry-logic`)
6. Open a detailed Pull Request describing your changes

### Guidelines

- Follow PEP 8 style guide and match existing code conventions
- Add comprehensive docstrings and type hints to new code
- Write descriptive commit messages explaining the why, not just what
- Include unit tests with good coverage for new functionality
- Update documentation including docstrings, README, and comments
- Keep pull requests focused on a single feature or fix
- Run the full test suite before submitting

### Development Setup

1. Clone your fork: `git clone https://github.com/YOUR_USERNAME/spidey.git`
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Install dev dependencies: `pip install pytest black mypy`
5. Create a branch: `git checkout -b your-feature-name`
6. Make changes and run tests: `pytest`
7. Format code: `black .`

For significant changes, please open an issue first to discuss your proposed changes. This ensures alignment with project goals and helps avoid duplicate work. We aim to review all pull requests within a week.
