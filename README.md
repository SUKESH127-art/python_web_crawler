<!-- @format -->

# LLMs.txt Generation Microservice

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-blue)](https://fastapi.tiangolo.com/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A production-ready microservice for generating structured `llms.txt` files from any website. This service uses a non-blocking, asynchronous architecture to handle long-running crawls efficiently, providing a robust backend engine for AI and RAG (Retrieval-Augmented Generation) applications.

---

## Core Features ✨

- **Asynchronous Job Processing**: Initiate crawls instantly and poll for results via a `job_id`. This non-blocking design ensures a fast UI/client experience, even when crawling large websites.

- **Intelligent Structuring**: Automatically groups discovered pages by URL path (e.g., `/blog`, `/docs`) and applies language filtering to produce a clean, semantically organized `llms.txt` file, a significant improvement over simple link lists.

- **Data Persistence & Refresh Logic**: Caches completed crawl results to a local data store and provides an endpoint to trigger re-crawls for stale data (defaulting to 7 days), ensuring content can be kept fresh.

- **Modular & Production-Ready**: Cleanly organized into a core application (`main.py`) and helper modules (`helpers.py`), following modern Python best practices for maintainability and testing.

---

## Architecture Overview 🏛️

The service is built as a standalone component for a decoupled web stack. The asynchronous workflow is key to its performance and scalability.

**Request Lifecycle:**

1.  Client `POSTS` a URL to `/generate-llms-txt`.
2.  The server immediately initiates the background job via Firecrawl and responds with a `job_id`.
3.  The client polls the `GET /crawl-status/{job_id}` endpoint.
4.  Once the job is complete, the server processes, formats, and returns the final `llms.txt`, caching the result on the filesystem.

[Image of an asynchronous job processing diagram]

---

## API Endpoints

| Method | Path                      | Description                                                                            |
| :----- | :------------------------ | :------------------------------------------------------------------------------------- |
| `POST` | `/generate-llms-txt`      | Kicks off a new crawl job. Responds immediately with a `job_id`.                       |
| `GET`  | `/crawl-status/{job_id}`  | Checks the status of a job. Returns progress or the final `llms.txt` if complete.      |
| `POST` | `/refresh-crawl/{job_id}` | Checks if a completed job's data is older than 7 days and starts a new crawl if it is. |
| `GET`  | `/`                       | Root endpoint providing basic API information.                                         |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- An API key from [Firecrawl](https://www.firecrawl.dev/)

### Installation & Setup

1.  **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    Create a file named `.env` in the project root and add your Firecrawl API key:
    ```env
    FIRECRAWL_API_KEY="fc-YOUR_API_KEY_HERE"
    ```

### Running the Service

1.  **Start the FastAPI Server:**

    ```bash
    uvicorn main:app --reload
    ```

    The API will be available at `http://127.0.0.1:8000`.

2.  **Use the Python Client for Testing:**
    In a new terminal, run the provided client script to start a job and see the results.
    ```bash
    python client.py
    ```

---

## 🛣️ Project Roadmap

This microservice is the foundational component of a larger web application. The next steps are:

- [ ] **Dockerize the Application**: Containerize the service for consistent, isolated deployments.
- [ ] **Deploy to Production**: Deploy to a cloud platform like Render or Railway.
- [ ] **Integrate with Frontend**: Connect this API to a Next.js and Supabase frontend.

---

## Technology Stack

- **Backend Framework**: FastAPI
- **Web Crawling Service**: Firecrawl API
- **Data Validation**: Pydantic
- **HTTP Client (for testing)**: Requests
