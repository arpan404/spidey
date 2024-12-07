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

- Automatically downloads files matching specified extensions
- Supports various file types (images, documents, etc.)
- Maintains original file structure with metadata

### Domain Control

- Option to limit crawling to initial domains
- Domain restriction list for excluding specific sites
- Automatic domain extraction and validation

### Asynchronous Operation

- Fast, non-blocking network operations
- Efficient resource utilization
- Built with aiohttp for optimal performance

## Dependencies

- aiohttp
- beautifulsoup4
- tldextract
- validators
- aiofiles

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

We welcome and encourage contributions to Spidey! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Guidelines

- Ensure your code follows the existing style and conventions
- Add/update documentation for any new features
- Write clear commit messages
- Include tests for new functionality
- Update the README if needed

### Development Setup

1. Clone your fork of the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a new branch for your changes
4. Make your changes and test thoroughly
5. Submit a pull request with a description of your changes

For major changes, please open an issue first to discuss what you would like to change. This helps ensure your time is well spent and your contribution will be accepted.
