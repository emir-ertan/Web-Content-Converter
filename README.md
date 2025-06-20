# Web Content Converter

This project contains a set of Python scripts to extract links from a webpage and convert the content of those links into Markdown format.

## Scripts

### [`get_links.py`](get_links.py)

This script fetches a given URL and extracts links that match a specific CSS selector (`.post-grid.bb-grid .ratio-wrap a`). The extracted links are saved to `linkler.txt`.

**Usage:**

```bash
python get_links.py <URL>
```

### [`web_to_markdown.py`](web_to_markdown.py)

This script takes a single URL, fetches its content, attempts to clean and extract the main article content, converts tables to Markdown, and converts the remaining HTML to Markdown. The output is saved to a Markdown file named after the URL.

**Usage:**

```bash
python web_to_markdown.py <URL>
```

### [`txt_link_to_md.py`](txt_link_to_md.py)

This script reads a list of URLs from a specified text file (e.g., `linkler.txt`) and converts each URL's content into a separate Markdown file. It uses a similar conversion logic to `web_to_markdown.py` but is designed to process multiple links from a file.
*Usage:**

```bash
python txt_link_to_md.py <links_file.txt>
```

## Project Flow

1.  Use [`get_links.py`](get_links.py) to extract links from an index page and save them to `linkler.txt`.
2.  Use [`txt_link_to_md.py`](txt_link_to_md.py) with `linkler.txt` as input to convert each link into a separate Markdown file.
