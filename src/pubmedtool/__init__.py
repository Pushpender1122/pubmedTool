import argparse
import requests

class PubMedFetcher:
    def __init__(self, query: str):
        self.query = query
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        self.db="pubmed"
        self.retmax=5
        self.retmode="xml"
    def fetch_paper_ids(self):
        requests.packages.urllib3.util.connection.HAS_IPV6 = False # This line is added to fix the error
        response=requests.get(self.base_url, params={
            "db": self.db,
            "term": self.query,
            "retmax": self.retmax,
            "retmode": self.retmode
        })
def main():
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed.")
    parser.add_argument('query', type=str, help="Search query for PubMed.")
    parser.add_argument('-f', '--file', type=str, help="File to save the results.")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug output.")
    args = parser.parse_args()
    fetcher = PubMedFetcher(args.query)
    fetcher.fetch_paper_ids()
if __name__ == "__main__":
    main()