"""Configuration settings for the stock screener."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEC_EDGAR_USERNAME = os.getenv("SEC_EDGAR_USERNAME", "research@stockscreener.com")

# Stock Universe
NASDAQ_100_LIMIT = int(os.getenv("NASDAQ_100_LIMIT", 100))

# Report Settings
REPORT_CACHE_DAYS = int(os.getenv("REPORT_CACHE_DAYS", 30))
REPORTS_DIR = "data/reports"
CACHE_DIR = "data/cache"

# Analysis Settings
ANALYSIS_MODEL = "gpt-4"
ANALYSIS_TEMPERATURE = 0.7

# Ensure directories exist
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
