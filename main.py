import os
import time
from socket import timeout

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from firecrawl import FirecrawlApp
from pydantic import BaseModel, HttpUrl

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


# Define request model
class CrawlRequest(BaseModel):
    url: HttpUrl


# Crawling logic
@app.post("/generate-llms-txt")
async def generate_llms_txt(request: CrawlRequest):
    """
    Accepts a URL, crawls the site using Firecrawl, and returns the crawled data.
    """
    target_url = str(request.url)  # Convert HttpUrl to string
    print(f"Starting crawl for: {target_url}")
    try:
        crawl_response = firecrawl_app.crawl_url(url=target_url, limit=20)
        if not crawl_response or not crawl_response.data:
            err = "No Response Found!" if not crawl_response else "No Data Found!"
            raise HTTPException(status_code=404, detail=err)

        # llms.txt formatting logic
        llms_txt_content = []
        for page in crawl_response.data:
            print("Page metadata:", page.metadata)
            # ensure metadata exists and has required url
            if not page.metadata or not page.metadata.get("sourceURL"):
                continue
            entry = [f"url: {page.metadata['sourceURL']}"]
            # safely get title and description
            title = page.metadata.get("title")
            if title:
                entry.append(f"title: {title}")
            description = page.metadata.get("description")
            if description:
                entry.append(f"description: {description}")
            llms_txt_content.append("\n".join(entry))
        # Join all entries with a double newline
        final_output = "\n\n".join(llms_txt_content)
        print("Crawl response data:", crawl_response.data)
        return PlainTextResponse(content=final_output)

    except Exception as e:
        print(f"Error while crawling {target_url}: {e}")
        # Return error as plain text for consistency
        return PlainTextResponse(
            content=f"An error occurred: {str(e)}", status_code=502
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
        firecrawl_app.crawl_url(simple_url)
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
