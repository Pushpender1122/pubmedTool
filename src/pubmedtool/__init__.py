import argparse
import requests
import xml.etree.ElementTree as ET
import re
import logging
import csv
from pprint import pprint
from typing import List, Dict, Any, Union

class PubMedFetcher:
    def __init__(self, query: str):
        self.query = query
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        self.db = "pubmed"
        self.retmax = 5
        self.retmode = "xml"
        requests.packages.urllib3.util.connection.HAS_IPV6 = False
        logging.debug(f"Initialized PubMedFetcher with query: {query}")

    def fetch_paper_ids(self) -> List[str]:
        params = {
            "db": self.db,
            "term": self.query,
            "retmax": self.retmax,
            "retmode": self.retmode
        }
        logging.debug(f"Fetching paper IDs with params: {params}")
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            ids = self.__parse_ids(response.text)
            logging.debug(f"Fetched paper IDs: {ids}")
            return ids
        except requests.RequestException as e:
            logging.error(f"Error fetching paper IDs: {e}")
            return []

    def fetch_papers_details(self, ids: List[str]) -> str:
        logging.debug(f"Fetching paper details for IDs: {ids}")
        try:
            response = requests.get(self.fetch_url, params={
                "db": self.db,
                "id": ",".join(ids),
                "retmode": self.retmode
            })
            response.raise_for_status()
            logging.debug(f"Fetched paper details")
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error fetching paper details: {e}")
            return ""

    def extract_non_academic_authors(self, papers: str) -> List[Dict[str, Any]]:
        logging.debug("Extracting non-academic authors")
        root = ET.fromstring(papers)
        filtered_papers = []
        for article in root.findall("PubmedArticle"):
            details = {}
            logging.debug(f"Processing article: {article}")
            medline_citation = article.find("MedlineCitation")
            id = medline_citation.find("PMID").text
            date_element = medline_citation.find("DateRevised")
            year = date_element.find("Year").text
            month = date_element.find("Month").text
            day = date_element.find("Day").text
            date = f"{year}-{month}-{day}"
            article_title = medline_citation.find("Article").find("ArticleTitle").text
            author_data = self.__find_non_academic_authors(medline_citation.find("Article").find("AuthorList"))
            if author_data:
                details["id"] = id
                details["date"] = date
                details["title"] = article_title
                details["authors"] = author_data
                filtered_papers.append(details)
        logging.debug(f"Extracted non-academic authors: {filtered_papers}")
        return filtered_papers

    def __find_non_academic_authors(self, authors: ET.Element) -> Dict[str, Union[str, List[str]]]:
        logging.debug(f"Finding non-academic authors from: {authors}")
        author_data = {}
        for author in authors.findall("Author"):
            logging.debug(f"Processing author: {author}")
            affiliation = author.find("AffiliationInfo")
            if affiliation is not None:
                affiliation_text = affiliation.find("Affiliation").text
                if all(keyword not in affiliation_text for keyword in ["University", "labs", "Institute", "College", "School"]):
                    author_data["name"] = f"{author.find('ForeName').text} {author.find('LastName').text}"
                    author_data["affiliation"] = affiliation_text
                    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", affiliation_text)
                    author_data["email"] = emails if emails else ["n/a"]
                    logging.debug(f"Non-academic author found: {author_data}")
        return author_data

    def write_to_csv(self, papers: List[Dict[str, Any]], file: str) -> None:
        logging.debug(f"Writing papers to file: {file}")
        logging.debug(f"Fetched papers: {papers}")
        try:
            with open(file, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow(["ID", "Date", "Title", "Non-academic Author(s)", "Company Affiliation(s)", "Author Email"])
                for paper in papers:
                    writer.writerow([
                        paper['id'],
                        paper['date'],
                        paper['title'],
                        paper['authors']['name'],
                        paper['authors']['affiliation'],
                        ", ".join(paper['authors']['email']) if paper['authors']['email'] else ""
                    ])
        except IOError as e:
            logging.error(f"Error writing to file: {e}")

    def __parse_ids(self, response: str) -> List[str]:
        logging.debug("Parsing IDs from response")
        ids = []
        for line in response.split("\n"):
            if "<Id>" in line:
                ids.append(line.replace("<Id>", "").replace("</Id>", ""))
        logging.debug(f"Parsed IDs: {ids}")
        return ids

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed.")
    parser.add_argument('-q', type=str, required=True, help="Search query for PubMed.")
    parser.add_argument('-f', '--file', type=str, help="File to save the results.")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug output.")
    args = parser.parse_args()

    if args.debug:
        log_level = logging.DEBUG 
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s', filename='pubmedtool.log', filemode='w')

    if not args.q:
        logging.error("No query provided. Exiting.")
        return
    fetcher = PubMedFetcher(args.q)
    paper_ids = fetcher.fetch_paper_ids()
    if not paper_ids:
        logging.error("No paper IDs fetched. Exiting.")
        return

    papers = fetcher.fetch_papers_details(paper_ids)
    if not papers:
        logging.error("No paper details fetched. Exiting.")
        return

    filtered_papers = fetcher.extract_non_academic_authors(papers)
    logging.debug(f"Filtered papers: {filtered_papers}")

    if args.file:
        fetcher.write_to_csv(filtered_papers, args.file)
    else:
        pprint(filtered_papers)

if __name__ == "__main__":
    main()