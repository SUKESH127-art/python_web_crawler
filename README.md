<!-- @format -->

# LLMs.txt Generation Microservice

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-blue)](https://fastapi.tiangolo.com/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A production-ready microservice for generating structured `llms.txt` files from any website. This service uses a non-blocking, asynchronous architecture to handle long-running crawls efficiently, providing a robust backend engine for AI and RAG (Retrieval-Augmented Generation) applications.

---

## Core Features ✨

- **Stateless Architecture**: Designed as a stateless microservice with no persistent storage or database dependencies. Each request is independent and can be handled by any instance, enabling horizontal scaling and high availability.

- **Asynchronous Job Processing**: Initiate crawls instantly and poll for results via a `job_id`. This non-blocking design ensures a fast UI/client experience, even when crawling large websites.

- **Intelligent Structuring**: Automatically groups discovered pages by URL path (e.g., `/blog`, `/docs`) and applies language filtering to produce a clean, semantically organized `llms.txt` file, a significant improvement over simple link lists.

- **Production-Ready Security**: API key authentication, input validation, and secure error handling. All endpoints are protected except for health checks and documentation.

- **Modular & Maintainable**: Cleanly organized into a core application (`main.py`) and helper modules (`helpers.py`), following modern Python best practices for maintainability and testing.

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
    Create a file named `.env` in the project root and add your API keys:

    ```env
    FIRECRAWL_API_KEY="fc-YOUR_API_KEY_HERE"
    INTERNAL_API_KEY="your-secret-api-key-here"
    ```

    **Note**: Generate a secure `INTERNAL_API_KEY` using:

    ```bash
    python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
    ```

### Running the Service

1.  **Start the FastAPI Server:**

    ```bash
    uvicorn main:app --reload
    ```

    The API will be available at `http://127.0.0.1:8000`.

2.  **Use the Python Client for Testing:**
    In a new terminal, run the provided client script to start a job and see the results. If you don't provide a url, it will use a default url.

    ```bash
    python client.py https://docs.firecrawl.dev/
    ```

3.  **Test API Security:**
    Verify that the API authentication is working correctly:

    ```bash
    # Test without API key (should fail)
    curl -X POST "http://127.0.0.1:8000/generate-llms-txt" \
      -H "Content-Type: application/json" \
      -d '{"url": "https://example.com"}'

    # Test with correct API key (should succeed)
    curl -X POST "http://127.0.0.1:8000/generate-llms-txt" \
      -H "Authorization: Bearer YOUR_INTERNAL_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"url": "https://example.com"}'
    ```

## 🐳 Docker Deployment

### Local Docker Usage

1. **Build the Docker image:**

   ```bash
   docker build -t llms-txt-generator .
   ```

2. **Run the container:**

   ```bash
   docker run -p 8000:8000 -e FIRECRAWL_API_KEY=your_api_key_here -e INTERNAL_API_KEY=your_secret_key_here llms-txt-generator
   ```

3. **Or use an environment file:**
   ```bash
   docker run -p 8000:8000 --env-file .env llms-txt-generator
   ```

### Docker Hub

The latest image is available on Docker Hub:

```bash
docker pull sukeshram/llms-txt-generator
```

## 🚀 Production Deployment

### Stateless Microservice Architecture

This is a **stateless microservice** designed for horizontal scaling and high availability. The service:
- **No persistent storage**: All data is processed in-memory and returned to clients
- **No database dependencies**: Eliminates database bottlenecks and maintenance overhead
- **Stateless design**: Each request is independent and can be handled by any instance
- **Horizontal scaling**: Can be easily scaled across multiple instances for high traffic

### Render Deployment

The service is currently deployed on **Render** using the following configuration:

#### **Deployment Settings:**
- **Platform**: Render Web Services
- **Build Command**: `docker pull sukeshram/llms-txt-generator`
- **Start Command**: `docker run -p $PORT:8000 sukeshram/llms-txt-generator`
- **Environment**: Docker container with Python 3.11
- **Auto-deploy**: Enabled (deploys on every push to main branch)

#### **Environment Variables on Render:**
```env
FIRECRAWL_API_KEY=fc-d98c413660f346e6bb1f78134eae13b4
INTERNAL_API_KEY=BopGY8MgN6SXkG7uLZLlrljMrLhtbkHEWv8sdGVINuk
PORT=8000
```

#### **Deployment Process:**
1. **CI/CD Pipeline**: CircleCI builds and tests the Docker image
2. **Docker Hub**: Image is pushed to `sukeshram/llms-txt-generator`
3. **Render**: Automatically pulls the latest image from Docker Hub
4. **Health Checks**: Render monitors the service at `/test-connection`
5. **Auto-scaling**: Render can scale instances based on traffic

### Alternative Deployment Platforms

The stateless design makes this service compatible with any container platform:

- **Railway**: Direct GitHub integration with automatic deployments
- **Heroku**: Container deployment with the Docker image
- **AWS ECS**: Container orchestration with auto-scaling
- **Google Cloud Run**: Serverless container platform
- **Azure Container Instances**: Managed container service

## 🔄 CI/CD with CircleCI

This project includes automated CI/CD using CircleCI with **"build once, deploy same"** optimization. The pipeline:

1. **Builds** the Docker image once
2. **Tests** the container functionality thoroughly
3. **Deploys** the exact same tested image to Docker Hub

### Key Features

- **Build Once, Deploy Same**: Ensures the exact same image that passed tests is deployed
- **Docker Hub Authentication**: Prevents rate limiting issues
- **Comprehensive Testing**: Container health checks, API endpoint validation, and import tests
- **Efficient Workflow**: Eliminates redundant builds, saving time and ensuring consistency

### Setting up CircleCI

1. **Connect your repository** to CircleCI
2. **Add environment variables** in CircleCI project settings:

   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub access token (not login password)

3. **Push to main branch** to trigger the pipeline

The pipeline will automatically:

- Build and test the Docker image
- Save the tested image to workspace
- Load and tag the exact same image for deployment
- Push to Docker Hub with tags: `latest` and commit SHA
- Only run on the `main` branch

---

## 🌐 Live API

The service is now **live and ready for production use**!

### Production Endpoint

- **API URL**: https://llms-txt-crawler-api.onrender.com
- **Status**: ✅ Live and operational
- **Documentation**: https://llms-txt-crawler-api.onrender.com/docs

### Using the Production API

1. **With the Python Client:**

   ```bash
   python client.py https://example.com
   ```

   The client automatically connects to the production API.

2. **Direct API Calls:**
   ```bash
   # Start a crawl job
   curl -X POST "https://llms-txt-crawler-api.onrender.com/generate-llms-txt" \
     -H "Authorization: Bearer YOUR_INTERNAL_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
   ```

---

## 🔐 Security Features

- **API Key Authentication**: All endpoints require a valid `Authorization: Bearer <INTERNAL_API_KEY>` header
- **Environment Variable Management**: Secure handling of API keys and secrets
- **Input Validation**: Comprehensive URL and parameter validation using Pydantic
- **Error Handling**: Secure error responses that don't leak sensitive information

## Technology Stack

- **Backend Framework**: FastAPI
- **Web Crawling Service**: Firecrawl API
- **Data Validation**: Pydantic
- **HTTP Client (for testing)**: Requests
- **Containerization**: Docker
- **CI/CD**: CircleCI with Docker Hub integration
