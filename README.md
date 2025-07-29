<!-- @format -->

# LLMs.txt Generator API

A FastAPI-based API to crawl a website and generate an llms.txt file, using the Firecrawl API.

## Features

- Modular codebase with helper functions in `helpers.py`
- Fast, region-specific crawling using US-based stealth proxies
- Caching of crawl results for up to 1 week to minimize API usage and speed up repeated requests
- Robust error handling and input validation
- Outputs results to both API response and a local file (`output_llm.txt`)

## Setup

1. **Clone the repository**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up your `.env` file**
   - Add your Firecrawl API key:
     ```
     FIRECRAWL_API_KEY=your_api_key_here
     ```
4. **Run the server**
   ```bash
   uvicorn main:app --reload
   ```

## Usage

### Generate llms.txt

Send a POST request to `/generate-llms-txt` with a JSON body:

```json
{
	"url": "https://www.scrapethissite.com/pages/simple/",
	"limit": 20
}
```

- `url`: The website to crawl (required)
- `limit`: Max number of pages to crawl (optional, default: 20, max: 500)

Example with `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/generate-llms-txt" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.scrapethissite.com/pages/simple/", "limit": 10}'
```

### Output

- The API returns the llms.txt content as plain text.
- The same content is written to `output_llm.txt` in your project directory.

## Configuration & Customization

- **Proxy & Location:**
  - Uses US-based stealth proxies by default for region-specific crawling and to minimize credit usage.
- **Caching:**
  - Results are cached for 1 week (`maxAge=604800000` ms) to speed up repeated crawls.
- **File Output:**
  - Output file and mode can be customized in `write_output_to_file` in `helpers.py`.
- **Error Handling:**
  - All errors are handled gracefully and returned as HTTP error responses.

## Code Structure

- `main.py` — FastAPI app, endpoint logic, and grouping/formatting
- `helpers.py` — All helper functions (validation, options, error handling, file writing)
- `requirements.txt` — Python dependencies
- `output_llm.txt` — Output file (generated)

## Extending

- Add more helper functions to `helpers.py` as needed
- Adjust crawl options in `build_scrape_options` for different regions, proxies, or cache durations
- Customize grouping/formatting logic in `main.py`

## License

MIT
