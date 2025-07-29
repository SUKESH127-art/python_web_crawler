import os
import time
from socket import timeout

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
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


# Define pydantic request model
class CrawlRequest(BaseModel):
    url: HttpUrl


# Crawling logic
@app.post("/generate-llms-txt")
async def generate_llms_txt(request: CrawlRequest):
    """
    Accepts a URL, crawls the site using Firecrawl, and returns the crawled data.
    """

    # Stream the llmstxt content to both the client and write to output_llm.txt
    def llmstxt_streamer(llmstxt):
        # Ensure output_llm.txt is cleared before writing new content
        with open("output_llm.txt", "w", encoding="utf-8") as f:
            pass  # This will truncate the file to zero length
        # Write to file as we stream
        with open("output_llm.txt", "a", encoding="utf-8") as f:
            for chunk in llmstxt.splitlines(keepends=True):
                f.write(chunk)
                yield chunk

    target_url = str(request.url)  # Convert HttpUrl to string
    print(f"Starting crawl for: {target_url}")

    try:
        llm_text_response = firecrawl_app.generate_llms_text(
            url=target_url, cache=True, max_urls=100
        )
        if (
            not llm_text_response
            or not llm_text_response.success
            or not llm_text_response.data
            or not llm_text_response.data.llmstxt
        ):
            err = "No Response Found!" if not llm_text_response else "No Data Found!"
            raise HTTPException(status_code=404, detail=err)

        return StreamingResponse(
            llmstxt_streamer(llm_text_response.data.llmstxt), media_type="text/plain"
        )

    except Exception as e:
        print(f"Error while crawling {target_url}: {e}")
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
