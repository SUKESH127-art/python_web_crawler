import sys
import time

import requests
from rich.spinner import Spinner
from rich.text import Text

from helpers import (
    build_status_url,
    console,
    create_error_panel,
    create_info_panel,
    create_success_panel,
    extract_job_data,
    get_base_url,
    handle_request_exception,
)


def run_job(url: str):
    """Starts a crawl job and polls for the result."""
    base_url = get_base_url()

    console.print(
        create_info_panel(f"🚀 Starting crawl for: {url}", "Step 1: Initiate Crawl")
    )

    # --- Start the Crawl Job ---
    try:
        response = requests.post(
            f"{base_url}/generate-llms-txt",
            json={"url": url},
            timeout=10,  # Timeout for the initial request
        )

        job_data = extract_job_data(response)
        if not job_data:
            return

        job_id = job_data.get("job_id")
        console.print(
            f"[green]✔[/green] Job started successfully! [bold]job_id:[/bold] {job_id}"
        )
    except requests.exceptions.RequestException as e:
        handle_request_exception(e, "Job Creation")
        return

    # --- Poll for the Result ---
    status_url = build_status_url(base_url, job_data)
    console.print(
        create_info_panel(f"Polling status at: {status_url}", "Step 2: Check Status")
    )

    spinner = Spinner(
        "dots", text=Text("Waiting for crawl to complete...", style="yellow")
    )
    with console.status(spinner) as status:
        while True:
            try:
                poll_response = requests.get(status_url, timeout=30)

                # If the status is 202, the job is still processing
                if poll_response.status_code == 202:
                    status.update(Text(poll_response.text, style="yellow"))
                    time.sleep(5)  # Wait 5 seconds before polling again
                    continue

                # If the status is not 200, something went wrong with the completed job
                poll_response.raise_for_status()

                # If we reach here, the job is done (status 200)
                console.print("[green]✔[/green] Crawl completed!")
                console.print(
                    create_success_panel(
                        poll_response.text, f"Final llms.txt for {url}"
                    )
                )
                break

            except requests.exceptions.RequestException as e:
                handle_request_exception(e, "Status Polling")
                break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use the URL provided from the command line
        target_site = sys.argv[1]
    else:
        # Use the default URL and provide instructions
        target_site = "https://www.scrapethissite.com/"
        console.print(
            create_info_panel(
                f"No URL provided. Using default: {target_site}\n\n"
                f"To crawl a different site, run:\n"
                f"[bold]python client.py https://example.com[/bold]",
                "Usage Information",
            )
        )
