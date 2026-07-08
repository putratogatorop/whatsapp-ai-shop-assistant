"""Optional: pull extra knowledge-base source pages from the web.

Not required for the demo to work (data/faq_seed already ships enough content to
answer common questions offline) but shows the "web scraping for knowledge base"
requirement end-to-end. Point SCRAPE_URLS at your own store/docs site.
"""
import httpx
from bs4 import BeautifulSoup


def scrape_url(url: str, timeout: float = 15.0) -> str:
    resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def scrape_urls(urls: list[str]) -> list[tuple[str, str]]:
    return [(url, scrape_url(url)) for url in urls]
