import os
import time

import requests
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
console = Console()


def run_job(url: str):
    """Starts a crawl job and polls for the result."""
    console.print(
        Panel(
            f"[bold cyan]🚀 Starting crawl for:[/bold cyan] {url}",
            title="[bold green]Step 1: Initiate Crawl[/bold green]",
            border_style="green",
        )
    )

    # --- Start the Crawl Job ---
    try:
        response = requests.post(
            f"{BASE_URL}/generate-llms-txt",
            json={"url": url},
            timeout=10,  # Timeout for the initial request
        )
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        job_data = response.json()
        job_id = job_data.get("job_id")

        if not job_id:
            console.print("[bold red]Error: No job_id returned from API.[/bold red]")
            return

        console.print(
            f"[green]✔[/green] Job started successfully! [bold]job_id:[/bold] {job_id}"
        )
    except requests.exceptions.RequestException as e:
        console.print(
            Panel(
                f"[bold red]Error starting job:[/bold red] {e}",
                title="[bold red]API Error[/bold red]",
                border_style="red",
            )
        )
        return

    # --- Poll for the Result ---
    status_url = f"{BASE_URL}{job_data['status_url']}"
    console.print(
        Panel(
            f"Polling status at: {status_url}",
            title="[bold yellow]Step 2: Check Status[/bold yellow]",
            border_style="yellow",
        )
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
                    Panel(
                        poll_response.text,
                        title=f"[bold green]Final llms.txt for {url}[/bold green]",
                        border_style="green",
                        expand=True,
                    )
                )
                break

            except requests.exceptions.RequestException as e:
                console.print(
                    Panel(
                        f"[bold red]Error polling for status:[/bold red] {e}",
                        title="[bold red]API Error[/bold red]",
                        border_style="red",
                    )
                )
                break


if __name__ == "__main__":
    target_site = "https://www.scrapethissite.com/"
    run_job(target_site)
