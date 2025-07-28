from dotenv import load_dotenv
from fastapi import FastAPI

# load environment variable
load_dotenv()

# 1. initialize fastapi
app = FastAPI(
    title="LLMs.txt Generator API",
    description="An API to crawl a website and generate an llms.txt file.",
    version="1.0.0"
)

