import requests
import base64
import datetime
from typing import List, Dict, Tuple
import os
import fitz  # PyMuPDF
import subprocess
from bs4 import BeautifulSoup  # For HTML parsing

# Import the ZyteCrawler class from your previous code file
from zyte_crawler_class import ZyteCrawler  # Adjust the filename if needed


def is_pdf_recent(pdf_url: str, days: int = 30) -> bool:
    """Checks if a PDF file was uploaded within the last 'days' days."""
    try:
        response = requests.head(pdf_url)  # Use HEAD request for efficiency
        response.raise_for_status()
        last_modified = response.headers.get('Last-Modified')
        if last_modified:
            modified_date = datetime.datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
            return (datetime.datetime.now() - modified_date).days <= days
        else:
            return False  # Assume not recent if Last-Modified header is missing
    except requests.exceptions.RequestException as e:
        print(f"Error checking date for {pdf_url}: {e}")
        return False


def main():
    api_key = "YOUR_ZYTE_API_KEY"  # Replace with your actual Zyte API key
    crawler = ZyteCrawler(api_key)
    crawler.set_size_criteria({"51-100": (51, 100), "100-150": (100, 150),
                               "150-800": (150, 800), "800+": (800, float('inf'))})

    cia_urls = [
        "https://www.cia.gov/readingroom/historical-collections",
        # Add more CIA.gov URLs to crawl
    ]

    for url in cia_urls:
        pdf_urls = crawler.get_pdf_urls(url)
        for pdf_url in pdf_urls:
            if is_pdf_recent(pdf_url, 30) and crawler.get_pdf_page_count(pdf_url) > 50:
                print(f"Found recent PDF: {pdf_url}")
                # ... Rest of the download and processing logic ...


if __name__ == "__main__":
    main()
