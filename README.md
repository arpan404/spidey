# A web crawler

## Usage:

```python
from spidey import Spidey
crawler = Spidey(["https://stackoverflow.com/","https://bun.sh/"])
crawler.crawl()
