"""Module for downloading and managing SEC reports (10-K, 10-Q)."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from config import REPORT_CACHE_DAYS, REPORTS_DIR

# Local fallback mode: no live SEC fetches.
# This avoids the constant 403 / non-JSON SEC issue during local testing.
# The app can still run and reach Gemini using synthetic report metadata.


def get_cik_for_ticker(ticker: str) -> Optional[str]:
    """Return a static fallback CIK for local testing."""
    fallback = {
        "AAPL": "0000320193",
        "MSFT": "0000789019",
        "NVDA": "0001045810",
        "AMZN": "0001018284",
        "META": "0001326801",
        "GOOGL": "0001652044",
        "GOOG": "0001652044",
        "AVGO": "0001730168",
        "ASML": "0001015780",
        "AMD": "0000002488",
        "INTC": "0000050863",
        "QCOM": "0000804328",
        "INTU": "0001651907",
        "CSCO": "0000858877",
        "PEP": "0000068525",
        "COST": "0000906304",
        "CMCSA": "0001166691",
        "ADBE": "0000796343",
        "NFLX": "0001065280",
        "PYPL": "0001633917",
        "CRWD": "0001535527",
        "AZN": "0001018294",
        "LRCX": "0000707549",
        "ORLY": "0000899689",
        "AMAT": "0001014683",
        "KLAC": "0000315293",
        "PAYX": "0000723531",
    }
    return fallback.get(ticker.upper())


def fetch_reports_for_ticker(ticker: str, report_type: str = "10-K", limit: int = 2) -> List[Dict]:
    """Return synthetic report metadata so the app can continue without SEC access."""
    cik = get_cik_for_ticker(ticker)

    report = {
        "ticker": ticker,
        "type": report_type,
        "accession_number": f"LOCAL-{ticker}-{report_type}",
        "filing_date": datetime.now().strftime("%Y-%m-%d"),
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "url": f"https://example.local/{ticker}/{report_type}",
        "cik": cik,
    }

    return [report]


def download_report_text(ticker: str, accession_number: str, report_type: str) -> Optional[str]:
    """Return a synthetic report summary instead of trying to fetch real SEC text."""
    return (
        f"{ticker} is a large-cap technology company with stable revenue, operating leverage, "
        f"and competitive market position. This local fallback report is used for prototype testing "
        f"and AI analysis while SEC live access is unavailable."
    )


def get_latest_reports(tickers: List[str], report_type: str = "10-K") -> Dict[str, List[Dict]]:
    """Return local report metadata for all requested tickers."""
    all_reports = {}

    for ticker in tickers:
        print(f"Fetching reports for {ticker}...")
        reports = fetch_reports_for_ticker(ticker, report_type, limit=1)
        if reports:
            all_reports[ticker] = reports

    return all_reports


def cache_reports_metadata(reports: Dict[str, List[Dict]]) -> None:
    """Cache reports metadata to JSON file."""
    cache_file = os.path.join(REPORTS_DIR, "reports_metadata.json")
    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(cache_file, "w", encoding="utf-8") as handle:
        json.dump(reports, handle, indent=2, default=str)


def load_reports_metadata() -> Dict[str, List[Dict]]:
    """Load cached reports metadata."""
    cache_file = os.path.join(REPORTS_DIR, "reports_metadata.json")

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as handle:
            return json.load(handle)

    return {}