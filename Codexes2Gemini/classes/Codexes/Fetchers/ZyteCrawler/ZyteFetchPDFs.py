import requests
import base64
import datetime
from typing import List, Dict, Tuple
import os
import fitz  # PyMuPDF
import subprocess


class ZyteCrawler:

    def __init__(self, api_key: str, base_url: str = "https://api.zyte.com/v1/extract"):
        self.api_key = api_key
        self.base_url = base_url
        self.last_crawl_data: Dict[str, List[str]] = {}  # {URI: [PDF_URLs]}
        self.keyword_phrases: List[str] = []
        self.size_criteria: Dict[str, Tuple[int, int]] = {}  # {"category": (min_pages, max_pages)}

    def set_keyword_phrases(self, keyword_phrases: List[str]):
        self.keyword_phrases = keyword_phrases

    def set_size_criteria(self, size_criteria: Dict[str, Tuple[int, int]]):
        self.size_criteria = size_criteria

    def get_pdf_urls(self, url: str) -> List[str]:
        """Extracts all PDF URLs from a given webpage."""
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.api_key}:'.encode()).decode()}",
            "Content-Type": "application/json"
        }
        data = {
            "url": url,
            "browserHtml": True
        }
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 200:
                html = response.json().get('browserHtml', '')
                # Extract PDF URLs from HTML (implementation depends on HTML structure)
                # Example using BeautifulSoup:
                # from bs4 import BeautifulSoup
                # soup = BeautifulSoup(html, 'html.parser')
                # pdf_urls = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.pdf')]
                # return pdf_urls
            else:
                print(f"Error fetching {url}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
        return []

    def get_pdf_page_count(self, pdf_url: str) -> int:
        """Returns the number of pages in a PDF file."""
        try:
            response = requests.get(pdf_url)
            response.raise_for_status()

            with fitz.open(stream=response.content) as doc:  # Use PyMuPDF
                return doc.page_count
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {pdf_url}: {e}")
        except fitz.fitz.PyMuPDFError as e:
            print(f"Error parsing PDF {pdf_url}: {e}")
        return 0

    def categorize_pdf(self, page_count: int) -> str:
        """Categorizes a PDF by page count."""
        if 0 <= page_count <= 18:
            return "0-18"
        elif 20 <= page_count <= 50:
            return "20-50"
        elif 51 <= page_count <= 100:
            return "51-100"
        elif 100 <= page_count <= 150:
            return "100-150"
        elif 150 <= page_count <= 800:
            return "150-800"
        else:
            return "800+"

    def download_pdf(self, pdf_url: str, filename: str):
        """Downloads a PDF file."""
        try:
            response = requests.get(pdf_url)
            response.raise_for_status()

            with open(filename, "wb") as f:
                f.write(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {pdf_url}: {e}")

    def call_codexes2gemini(self, pdf_path: str, parameters: List[str]):
        """Calls the Codexes2Gemini function with given parameters."""
        try:
            # Assuming Codexes2Gemini is a command-line tool
            command = ["Codexes2Gemini"] + parameters + [pdf_path]
            subprocess.run(command, check=True)  # Check for subprocess errors
        except subprocess.CalledProcessError as e:
            print(f"Error executing Codexes2Gemini: {e}")

    def crawl_and_process(self, urls: List[str]):
        """Crawls given URLs, finds new PDFs, categorizes, downloads and processes them."""
        today = datetime.date.today().strftime("%Y-%m-%d")
        for url in urls:
            new_pdfs = []
            pdf_urls = self.get_pdf_urls(url)
            for pdf_url in pdf_urls:
                if pdf_url not in self.last_crawl_data.get(url, []):
                    new_pdfs.append(pdf_url)
            self.last_crawl_data[url] = pdf_urls

            for pdf_url in new_pdfs:
                page_count = self.get_pdf_page_count(pdf_url)
                category = self.categorize_pdf(page_count)

                # Check if PDF fits size criteria
                if (category in self.size_criteria and
                        self.size_criteria[category][0] <= page_count <= self.size_criteria[category][1]):
                    filename = f"{today}_{category}_{os.path.basename(pdf_url)}"
                    self.download_pdf(pdf_url, filename)

                    # Call Codexes2Gemini with parameters
                    self.call_codexes2gemini(filename, ["parameter1", "parameter2"])
