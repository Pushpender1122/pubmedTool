import argparse
import logging
from pubmedtool.pubmed_fetcher import PubMedFetcher

def main():
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed and extract non-academic authors.")
    parser.add_argument('-q', '--query', type=str, required=True, help="Search query for PubMed.")
    parser.add_argument('-f', '--file', type=str, help="File to save the results (CSV).")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug logging.")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    fetcher = PubMedFetcher()
    
    paper_ids = fetcher.fetch_paper_ids(args.query)
    if not paper_ids:
        print("No paper IDs fetched.")
        return

    paper_details = fetcher.fetch_papers_details(paper_ids)
    if not paper_details:
        print("No paper details fetched.")
        return

    extracted_data = fetcher.extract_non_academic_authors(paper_details)
    if not extracted_data:
        print("No non-academic authors found.")
        return

    if args.file:
        fetcher.write_to_csv(extracted_data, args.file)
        print(f"Data saved to {args.file}")
    else:
        for paper in extracted_data:
            print(paper)

if __name__ == "__main__":
    main()
