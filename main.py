import os
import time
from collections import defaultdict
from typing import Optional
from urllib.parse import urlparse

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from firecrawl import FirecrawlApp
from pydantic import BaseModel, HttpUrl, field_validator

# load environment variable
load_dotenv()

# Initialize fastapi
app = FastAPI(
    title="LLMs.txt Generator API",
    description="An API to crawl a website and generate an llms.txt file.",
    version="1.0.0",
)

# Retrieve API key from environment variable
firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
if not firecrawl_api_key:
    raise RuntimeError("Firecrawl's API key isn't found in .env file!")

# Initialize the FirecrawlApp client once
# This object will be reused for all incoming API requests.
firecrawl_app = FirecrawlApp(api_key=firecrawl_api_key)


# Define pydantic request model with validation
class CrawlRequest(BaseModel):
    url: HttpUrl
    limit: Optional[int] = 20

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 500):
            raise ValueError("Limit must be between 1 and 500")
        return v


def validate_url_scheme(url: str) -> bool:
    """Validate that the URL uses a supported scheme."""
    supported_schemes = {"http", "https"}
    parsed = urlparse(url)
    return parsed.scheme in supported_schemes


def perform_crawl(target_url: str, limit: int = 20):
    """
    Calls the Firecrawl API to crawl the site and returns the response.
    Handles initial validation and API-level errors.
    """
    # Input validation
    if not validate_url_scheme(target_url):
        raise HTTPException(
            status_code=400, detail="Only HTTP and HTTPS URLs are supported"
        )

    try:
        crawl_response = firecrawl_app.crawl_url(
            url=target_url,
            limit=limit,
            max_concurrency=20,
            crawl_options={
                "maxAge": 604800000,  # 1 week cache
                "proxy": "stealth",
                "location": {"country": "US"},
            },
        )
        if not crawl_response or not crawl_response.data:
            err = "No Response Found!" if not crawl_response else "No Data Found!"
            raise HTTPException(status_code=404, detail=err)
        return crawl_response.data
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Error during Firecrawl API call for {target_url}: {e}")

        # Provide more specific error messages based on exception type
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


def group_crawled_pages(pages: list):
    """
    Takes a list of crawled page objects and groups them by their primary URL path.
    """
    if not pages:
        raise HTTPException(status_code=404, detail="No pages were found to process")

    url_groups = defaultdict(list)
    processed_count = 0
    filtered_count = 0

    for page in pages:
        if not page.metadata or not page.metadata.get("sourceURL"):
            filtered_count += 1
            continue
        try:
            path = urlparse(page.metadata["sourceURL"]).path
            path_segments = [segment for segment in path.split("/") if segment]

            group_key = (
                "Homepage"
                if not path_segments
                else path_segments[0].replace("-", " ").title()
            )
            url_groups[group_key].append(page)
            processed_count += 1
        except Exception as e:
            print(
                f"Could not parse or group URL {page.metadata.get('sourceURL', 'N/A')}: {e}"
            )
            filtered_count += 1
            continue

    if processed_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No valid pages found after filtering. Processed: {processed_count}, Filtered: {filtered_count}",
        )

    print(
        f"Successfully processed {processed_count} pages, filtered {filtered_count} pages"
    )
    return url_groups


def format_groups_to_llmstxt(url_groups: dict):
    """
    Takes a dictionary of grouped pages and formats it into a structured llms.txt string.
    """
    if not url_groups:
        raise HTTPException(status_code=404, detail="No content to format")

    final_output_parts = []
    for group_name, pages in sorted(url_groups.items()):
        final_output_parts.append(f"## {group_name}")
        group_entries = []
        for page in pages:
            title = page.metadata.get("title", "No Title")
            if not title:
                title = group_name
            url = page.metadata.get("sourceURL")
            description = page.metadata.get("description")

            entry = f"- [{title}]({url})"
            if description:
                entry += f": {description}"
            group_entries.append(entry)

        final_output_parts.append("\n".join(group_entries))

    result = "\n\n".join(final_output_parts)
    if not result.strip():
        raise HTTPException(status_code=404, detail="Generated content is empty")

    return result


def write_output_to_file(content: str, filename: str = "output_llm.txt"):
    """
    Writes the given content to a local file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully wrote output to {filename}")
    except IOError as e:
        # Log the error but don't crash the request. The primary goal is to
        # return the data to the user.
        print(f"Error writing to file {filename}: {e}")


# Crawling logic
@app.post("/generate-llms-txt")
async def generate_llms_txt(request: CrawlRequest):
    """
    Accepts a URL, crawls the site using Firecrawl, and returns the crawled data.
    """
    target_url = str(request.url)  # Convert HttpUrl to string
    limit = request.limit or 20

    print(f"Starting crawl for: {target_url} with limit: {limit}")

    try:
        # Step 1: Perform the crawl to get page data
        crawled_pages = perform_crawl(target_url, limit)

        # Step 2: Group the results by URL path
        grouped_pages = group_crawled_pages(crawled_pages)

        # Step 3: Format the groups into the final llms.txt string
        final_output = format_groups_to_llmstxt(grouped_pages)

        # Step 4: Write the output to a file
        write_output_to_file(final_output)

        return PlainTextResponse(content=final_output)

    except HTTPException as e:
        # If an HTTPException was raised in the helpers, re-raise it
        raise e

    except Exception as e:
        print(f"Unexpected error while crawling {target_url}: {e}")
        return PlainTextResponse(
            content=f"An unexpected error occurred: {str(e)}", status_code=500
        )


@app.get("/")
async def root():
    """
    Root endpoint that provides API information.
    """
    return {
        "message": "LLMs.txt Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate_llms_txt": "/generate-llms-txt (POST)",
            "test_connection": "/test-connection (GET)",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


@app.get("/test-connection")
async def test_connection():
    """
    Test the Firecrawl API connection.
    """
    try:
        # Try a simple API call to test the connection
        print("Testing Firecrawl API connection...")
        simple_url = "https://www.scrapethissite.com/pages/simple/"
        firecrawl_app.scrape_url(simple_url)
        # You might need to check what methods are available for testing
        return {
            "status": "success",
            "message": "Firecrawl API connection test completed",
            "api_key_configured": bool(firecrawl_api_key),
            "api_key_length": len(firecrawl_api_key) if firecrawl_api_key else 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Firecrawl API connection failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
