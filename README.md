# PubMed Tool

This tool fetches research papers from PubMed based on a search query, extracts non-academic authors, and saves the results to a CSV file.

## Features

- Fetch paper IDs from PubMed using a search query.
- Retrieve detailed information about the papers.
- Extract non-academic authors from the papers.
- Save the results to a CSV file.

## Requirements

- Python 3.x
- `requests` library
- `argparse` library
- `xml.etree.ElementTree` library
- `re` library
- `logging` library
- `csv` library
- `poetry` for dependency management

## Usage

First, install the dependencies using Poetry:

```sh
poetry install
```

Then, run the tool with the desired search query:

```sh
poetry run python get-papers-list --query "your search query"
```
