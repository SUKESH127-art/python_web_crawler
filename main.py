from collections import defaultdict
from typing import Optional
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from firecrawl import FirecrawlApp
from pydantic import BaseModel, HttpUrl, field_validator

from helpers import (
    build_scrape_options,
    handle_crawl_exception,
    load_environment_config,
    validate_url_scheme,
)

app = FastAPI(
    title="LLMs.txt Generator API",
    description="An API to crawl a website and generate an llms.txt file.",
    version="1.0.0",
)

# Initialize Firecrawl with API key from environment
firecrawl_api_key = load_environment_config()
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
        print(f"Crawling URL: {target_url} with limit: {limit}")
        crawl_job = firecrawl_app.async_crawl_url(
            url=target_url,
            limit=limit,
            max_concurrency=20,
            scrape_options=build_scrape_options(),
        )
        if not crawl_job or not crawl_job.id:
            raise HTTPException(
                status_code=500, detail="Failed to start crawl job with Firecrawl."
            )
        # bc async_crawl_url, return job_id + status_url to poll when needed
        return {
            "message": "Crawl job started successfully",
            "job_id": crawl_job.id,
            "status_url": f"/crawl-status/{crawl_job.id}",
        }
    except Exception as e:
        handle_crawl_exception(e, target_url)


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


@app.post("/generate-llms-txt")
async def generate_llms_txt(request: CrawlRequest):
    """
    Accepts a URL, crawls the site using Firecrawl, and returns the crawled data.
    """
    target_url = str(request.url)  # Convert HttpUrl to string
    limit = request.limit or 20

    print(f"Starting crawl for: {target_url} with limit: {limit}")

    try:
        return perform_crawl(target_url, limit)
    except HTTPException as e:
        raise e
    except Exception as e:
        handle_crawl_exception(e, target_url)


@app.get("/crawl-status/{job_id}", response_class=PlainTextResponse)
async def get_crawl_status(job_id: str):
    """
    Checks the status of a crawl job. If complete, formats and returns the llms.txt.
    """
    try:
        print(f"Checking status for job_id: {job_id}")
        status_response = firecrawl_app.check_crawl_status(job_id)

        if status_response.status == "completed":
            if not status_response.data:
                raise HTTPException(
                    status_code=404, detail="Crawl completed but no data was found."
                )

            grouped_pages = group_crawled_pages(status_response.data)
            final_output = format_groups_to_llmstxt(grouped_pages)

            return PlainTextResponse(content=final_output)

        elif status_response.status in ["failed", "cancelled"]:
            return PlainTextResponse(
                content=f"Job {job_id} failed or was cancelled.", status_code=400
            )
        else:
            return PlainTextResponse(
                content=f"Job is still running. Status: {status_response.status}. "
                f"Completed {status_response.completed}/{status_response.total} pages.",
                status_code=202,
            )
    except Exception as e:
        handle_crawl_exception(e, f"job_id: {job_id}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


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
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


@app.get("/test-connection")
async def test_connection():
    """
    Tests the Firecrawl API connection using a lightweight scrape call.
    """
    try:
        print("Testing Firecrawl API connection...")
        simple_url = "https://www.scrapethissite.com/pages/simple/"
        firecrawl_app.scrape_url(simple_url)
        return {"status": "success", "message": "Firecrawl API connection is valid."}
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Firecrawl API connection failed: {str(e)}"
        )
