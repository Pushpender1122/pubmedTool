import requests
import xml.etree.ElementTree as ET
import re
import csv
import logging
from typing import List, Dict, Any, Union


class PubMedFetcher:
    def __init__(self, retmax: int = 5):
        self.search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        self.db = "pubmed"
        self.retmax = retmax
        self.retmode = "xml"

    def fetch_paper_ids(self,query: str) -> List[str]:
        """Fetches paper IDs from PubMed."""
        logging.debug(f"Initialized PubMedFetcher with query: {query}")
        params = {"db": self.db, "term": query, "retmax": self.retmax, "retmode": self.retmode}
        logging.debug(f"Fetching paper IDs from PubMed...", params)
        response = self.__make_request(self.search_url, params)
        return self.__parse_ids(response)
    def __make_request(self, url: str, params:any) -> str:
        """Makes a request to the given URL with the provided parameters."""
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error fetching data: {e}")
            return ""
    def fetch_papers_details(self, ids: List[str]) -> str:
        """Fetches full details of papers from PubMed."""
        logging.debug(f"Fetching details for paper IDs: {', '.join(ids)}")
        params = {"db": self.db, "id": ",".join(ids), "retmode": self.retmode}
        response = self.__make_request(self.fetch_url, params)
        return response

    def extract_non_academic_authors(self, papers: str) -> List[Dict[str, Any]]:
        """Extracts papers with non-academic authors and their details."""
        try:
            logging.debug("Extracting non-academic authors from paper data...")
            root = ET.fromstring(papers)
            extracted_data = []

            for article in root.findall("PubmedArticle"):
                medline_citation = article.find("MedlineCitation")
                id = medline_citation.find("PMID").text
                title = medline_citation.find("Article").find("ArticleTitle").text
                date = self.__extract_date(medline_citation)

                authors_data = self.__find_non_academic_authors(medline_citation.find("Article").find("AuthorList"))
                for author in authors_data:
                    extracted_data.append({
                        "PubmedID": id,
                        "Title": title,
                        "Publication Date": date,
                        "Non-academic Author(s)": author["name"],
                        "Company Affiliation(s)": author["affiliation"],
                        "Author Email": ", ".join(author["email"])
                    })
            logging.debug("Extraction completed.")
            return extracted_data
        except ET.ParseError as e:
            logging.error(f"Error parsing XML: {e}")
            return []

    def write_to_csv(self, papers: List[Dict[str, Any]], file: str) -> None:
        """Writes extracted paper data to a CSV file."""
        try:
            logging.debug(f"Writing extracted data to {file}...")
            with open(file, "w", newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "PubmedID", "Title", "Publication Date",
                    "Non-academic Author(s)", "Company Affiliation(s)", "Author Email"
                ])
                writer.writeheader()
                writer.writerows(papers)
            logging.debug("CSV writing completed.")
        except IOError as e:
            logging.error(f"Error writing to CSV file: {e}")

    def __parse_ids(self, response: str) -> List[str]:
        """Parses PubMed IDs from API response."""
        if not response or "No items found" in response:
            return []
        try:
            return [line.replace("<Id>", "").replace("</Id>", "") for line in response.split("\n") if "<Id>" in line]
        except Exception as e:
            logging.error(f"Error parsing paper IDs: {e}")
            return []

    def __extract_date(self, medline_citation: ET.Element) -> str:
        """Extracts publication date from MedlineCitation."""
        try:
            date_element = medline_citation.find("DateRevised")
            if date_element:
                return f"{date_element.find('Year').text}-{date_element.find('Month').text}-{date_element.find('Day').text}"
            return "Unknown"
        except AttributeError as e:
            logging.error(f"Error extracting date: {e}")
            return "Unknown"

    def __find_non_academic_authors(self, authors: ET.Element) -> List[Dict[str, str]]:
        """Finds non-academic authors based on their affiliation."""
        try:
            author_data = []
            for author in authors.findall("Author"):
                affiliation = author.find("AffiliationInfo")
                if affiliation is not None:
                    affiliation_text = affiliation.find("Affiliation").text
                    if affiliation_text and not any(keyword in affiliation_text for keyword in ["University", "Institute", "College", "School"]):
                        name = f"{author.find('ForeName').text} {author.find('LastName').text}"
                        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", affiliation_text) or ["n/a"]
                        author_data.append({"name": name, "affiliation": affiliation_text, "email": emails})
            return author_data
        except AttributeError as e:
            logging.error(f"Error extracting authors: {e}")
            return []