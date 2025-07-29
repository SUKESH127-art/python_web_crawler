import os
from typing import Literal
from urllib.parse import urlparse

from fastapi import HTTPException
from firecrawl.firecrawl import LocationConfig, ScrapeOptions


def validate_url_scheme(url: str) -> bool:
    """Validate that the URL uses a supported scheme and has a netloc."""
    supported_schemes = {"http", "https"}
    parsed = urlparse(url)
    return parsed.scheme in supported_schemes and bool(parsed.netloc)


def build_scrape_options(
    max_age: int = 604800000,
    proxy: Literal["basic", "stealth", "auto"] = "stealth",
    country: str = "US",
) -> ScrapeOptions:
    return ScrapeOptions(
        maxAge=max_age, proxy=proxy, location=LocationConfig(country=country)
    )


def handle_crawl_exception(e, target_url):
    print(f"Error during Firecrawl API call for {target_url}: {e}")
    if "timeout" in str(e).lower():
        raise HTTPException(
            status_code=408,
            detail="Request timed out. The website may be too large or slow to respond.",
        )
    elif "rate limit" in str(e).lower() or "quota" in str(e).lower():
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please try again later."
        )
    elif "not found" in str(e).lower() or "404" in str(e):
        raise HTTPException(
            status_code=404, detail="Website not found or inaccessible."
        )
    else:
        raise HTTPException(
            status_code=502,
            detail=f"An error occurred with the crawling service: {str(e)}",
        )


def write_output_to_file(
    content: str, filename: str = "output_llm.txt", mode: str = "w"
) -> bool:
    """
    Writes the given content to a local file. Returns True if successful, False otherwise.
    """
    try:
        (
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            if os.path.dirname(filename)
            else None
        )
        with open(filename, mode, encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully wrote output to {filename}")
        return True
    except IOError as e:
        print(f"Error writing to file {filename}: {e}")
        return False
