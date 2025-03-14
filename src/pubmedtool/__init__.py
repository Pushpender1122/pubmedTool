import argparse
import requests
import xml.etree.ElementTree as ET
import re
import logging
import csv
class PubMedFetcher:
    def __init__(self, query: str):
        self.query = query
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        self.db = "pubmed"
        self.retmax = 5
        self.retmode = "xml"
        requests.packages.urllib3.util.connection.HAS_IPV6 = False # This line is added to fix the error
        logging.info(f"Initialized PubMedFetcher with query: {query}")

    def fetch_paper_ids(self):
        params = {
            "db": self.db,
            "term": self.query,
            "retmax": self.retmax,
            "retmode": self.retmode
        }
        logging.info(f"Fetching paper IDs with params: {params}")
        response = requests.get(self.base_url, params=params)
        ids = self.__parseIds(response.text)
        logging.info(f"Fetched paper IDs: {ids}")
        return ids

    def fetch_papers_details(self, ids: list):
        logging.info(f"Fetching paper details for IDs: {ids}")
        response = requests.get(self.fetch_url, params={
            "db": self.db,
            "id": ",".join(ids),
            "retmode": self.retmode
        })
        logging.info(f"Fetched paper details")
        return response.text

    def extract_non_academic_authors(self, papers: str):
        logging.info("Extracting non-academic authors")
        root = ET.fromstring(papers)
        filtered_papers = []
        for article in root.findall("PubmedArticle"):
            details = {}
            logging.info(f"Processing article: {article}")
            medline_citation = article.find("MedlineCitation")
            id= medline_citation.find("PMID").text
            date_element = medline_citation.find("DateRevised")
            year = date_element.find("Year").text
            month = date_element.find("Month").text
            day = date_element.find("Day").text
            date = f"{year}-{month}-{day}"
            article_title = medline_citation.find("Article").find("ArticleTitle").text
            auther_data=self.__findNonAcademicAuthors(medline_citation.find("Article").find("AuthorList"))
            if len(auther_data)>0:
                details["id"]=id
                details["date"]=date
                details["title"]=article_title
                details["authors"]=auther_data
                filtered_papers.append(details)
        logging.info(f"Extracted non-academic authors: {filtered_papers}")
        return filtered_papers
    def __findNonAcademicAuthors(self, authors):
        logging.info(f"Finding non-academic authors from: {authors}")    
        autherData={}
        for author in authors.findall("Author"):
            logging.info(f"Processing author: {author}")
            affiliation = author.find("AffiliationInfo")
            if affiliation is not None:
                affiliation_text = affiliation.find("Affiliation").text
                if "University" not in affiliation_text and "labs" not in affiliation_text and "Institute" not in affiliation_text and "College" not in affiliation_text and "School" not in affiliation_text:
                    autherData["name"] = f"{author.find('ForeName').text} {author.find('LastName').text}"
                    autherData["affiliation"]=affiliation_text
                    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", affiliation_text)
                    autherData["email"] = emails if emails else "n/a"
                    logging.info(f"Non-academic author found: {autherData}")
        return autherData
    
    def write_to_csv(self, papers: list, file: str):
        logging.info(f"Writing papers to file: {file}")
        logging.info(f"Fetched papers: {papers}")
    
        with open(file, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)  
            
            # Writing header
            writer.writerow(["ID", "Date", "Title", "Author Name", "Author Affiliation", "Author Email"])
            
            for paper in papers:
                writer.writerow([
                    paper['id'],
                    paper['date'],
                    paper['title'],
                    paper['authors']['name'],
                    paper['authors']['affiliation'],
                    ", ".join(paper['authors']['email']) if paper['authors']['email'] else ""  # Handling empty email list
                ])
        
        logging.info(f"Written papers to file: {file}")
    def __parseIds(self, response):
        logging.info("Parsing IDs from response")
        ids = []
        for line in response.split("\n"):
            if "<Id>" in line:
                ids.append(line.replace("<Id>", "").replace("</Id>", ""))
        logging.info(f"Parsed IDs: {ids}")
        return ids

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',filename='pubmedtool.log',filemode='w')
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed.")
    parser.add_argument('-q', type=str, help="Search query for PubMed.")
    parser.add_argument('-f', '--file', type=str, help="File to save the results.")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug output.")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    fetcher = PubMedFetcher(args.q)
    paper_ids = fetcher.fetch_paper_ids()
    papers = fetcher.fetch_papers_details(paper_ids)
    # logging.info(f"Fetched papers: {papers}")
    filtered_papers = fetcher.extract_non_academic_authors(papers)
    logging.info(f"Filtered papers: {filtered_papers}")
    # logging.info(f"All authors: {fetcher.findAllAuthors(papers)}")
    if args.file:
        fetcher.write_to_csv(filtered_papers, args.file)
    else:
        print(filtered_papers)

if __name__ == "__main__":
    main()