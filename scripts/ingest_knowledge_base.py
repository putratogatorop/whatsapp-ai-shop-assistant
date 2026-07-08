"""Embed and upsert the FAQ/policy knowledge base into Qdrant.

Usage:
  python -m scripts.ingest_knowledge_base                 # seed docs only
  python -m scripts.ingest_knowledge_base --scrape URL...  # also scrape extra pages first
"""
import argparse
from pathlib import Path

from app.rag.ingest import ingest_directory, ingest_documents
from app.rag.scrape import scrape_urls

SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "faq_seed"
SCRAPED_DIR = Path(__file__).resolve().parent.parent / "data" / "scraped"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scrape", nargs="*", default=[], help="Extra URLs to scrape and ingest")
    args = parser.parse_args()

    count = ingest_directory(SEED_DIR)
    print(f"Ingested {count} chunks from {SEED_DIR}")

    if args.scrape:
        scraped = scrape_urls(args.scrape)
        for url, text in scraped:
            filename = SCRAPED_DIR / (url.replace("https://", "").replace("/", "_") + ".md")
            filename.write_text(text, encoding="utf-8")
        scraped_count = ingest_documents(scraped)
        print(f"Scraped + ingested {scraped_count} chunks from {len(args.scrape)} URL(s)")


if __name__ == "__main__":
    main()
