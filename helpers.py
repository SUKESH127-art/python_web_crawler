import os
import warnings
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlparse

import requests
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from firecrawl.firecrawl import LocationConfig, ScrapeOptions
from rich.console import Console
from rich.panel import Panel

# Suppress Pydantic field shadowing warnings from Firecrawl
warnings.filterwarnings(
    "ignore", message="Field name.*shadows an attribute in parent.*"
)

# Global console instance for UI components
console = Console()

# API Key Authentication
API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(key: str = Security(api_key_header)):
    """Dependency function to validate the API key from the Authorization header."""
    expected_api_key = os.getenv("INTERNAL_API_KEY")
    if not expected_api_key:
        raise HTTPException(status_code=500, detail="Internal server error: API key not configured on the server.")

    if key and key == f"Bearer {expected_api_key}":
        return key
    else:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing API Key")


def load_environment_config() -> str:
    """Load and validate environment configuration."""
    from dotenv import load_dotenv

    load_dotenv()

    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    if not firecrawl_api_key:
        raise RuntimeError("Firecrawl's API key isn't found in .env file!")
    return firecrawl_api_key


def get_base_url() -> str:
    """Get the base URL for API requests."""
    return os.getenv("BASE_URL", "http://127.0.0.1:8000")


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


def create_error_panel(message: str, title: str = "Error") -> Panel:
    """Create a standardized error panel."""
    return Panel(
        f"[bold red]{message}[/bold red]",
        title=f"[bold red]{title}[/bold red]",
        border_style="red",
    )


def create_success_panel(message: str, title: str = "Success") -> Panel:
    """Create a standardized success panel."""
    return Panel(
        f"[bold green]{message}[/bold green]",
        title=f"[bold green]{title}[/bold green]",
        border_style="green",
    )


def create_info_panel(message: str, title: str = "Info") -> Panel:
    """Create a standardized info panel."""
    return Panel(
        f"[bold cyan]{message}[/bold cyan]",
        title=f"[bold yellow]{title}[/bold yellow]",
        border_style="yellow",
    )


def handle_request_exception(
    e: requests.exceptions.RequestException, context: str = "API"
) -> None:
    """Handle request exceptions with standardized error display."""
    if hasattr(e, "response") and e.response is not None:
        try:
            error_detail = e.response.json().get("detail", str(e))
            error_message = f"Error during {context.lower()}: {error_detail}"
        except:
            error_message = f"Error during {context.lower()}: {e}"
    else:
        error_message = f"Error during {context.lower()}: {e}"

    console.print(create_error_panel(error_message, f"{context} Error"))


def extract_job_data(response: requests.Response) -> Optional[Dict[str, Any]]:
    """Extract and validate job data from API response."""
    try:
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get("job_id")

        if not job_id:
            console.print(create_error_panel("No job_id returned from API."))
            return None

        return job_data
    except requests.exceptions.RequestException as e:
        handle_request_exception(e, "Job Creation")
        return None
    except ValueError as e:
        console.print(create_error_panel(f"Invalid JSON response: {e}"))
        return None


def build_status_url(base_url: str, job_data: Dict[str, Any]) -> str:
    """Build the status URL for job polling."""
    status_url = job_data.get("status_url", "")
    if status_url.startswith("/"):
        return f"{base_url}{status_url}"
    return f"{base_url}/{status_url}"
