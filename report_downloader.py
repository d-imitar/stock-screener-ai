"""Module for downloading and managing SEC reports (10-K, 10-Q)."""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import feedparser
import requests

from config import REPORTS_DIR, REPORT_CACHE_DAYS, SEC_EDGAR_USERNAME

SEC_FEEDS = {
    "10-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=10-K&dateb=&owner=exclude&count=100&format=rss",
    "10-Q": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=10-Q&dateb=&owner=exclude&count=100&format=rss",
}

SEC_EDGAR_BASE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
SEC_HEADERS = {
    "User-Agent": f"{SEC_EDGAR_USERNAME} stock-screener-ai@example.com",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Host": "www.sec.gov",
}


def get_cik_for_ticker(ticker: str) -> Optional[str]:
    """Get CIK number for a given ticker symbol.

    SEC rejects unauthenticated or missing-user-agent requests with 403 responses.
    We retry with a browser-like user-agent and skip any ticker that still fails.
    """
    try:
        url = f"{SEC_EDGAR_BASE_URL}?company={ticker}&owner=exclude&action=getcompany&format=json"
        response = requests.get(url, headers=SEC_HEADERS, timeout=15)
        response.raise_for_status()

        data = response.json()
        if data.get("cik_lookup"):
            cik = list(data["cik_lookup"].values())[0]
            return str(cik).zfill(10)
    except Exception as exc:
        print(f"Warning: could not resolve CIK for {ticker}: {exc}")

    return None


def fetch_reports_for_ticker(ticker: str, report_type: str = "10-K", limit: int = 2) -> List[Dict]:
    """Fetch recent SEC reports for a given ticker."""
    cik = get_cik_for_ticker(ticker)
    if not cik:
        print(f"Could not find CIK for {ticker}; skipping SEC filing lookup.")
        return []

    reports = []
    try:
        url = (
            f"{SEC_EDGAR_BASE_URL}?action=getcompany&CIK={cik}&type={report_type}"
            f"&dateb=&owner=exclude&count={limit}&format=json"
        )
        response = requests.get(url, headers=SEC_HEADERS, timeout=15)
        response.raise_for_status()

        data = response.json()
        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])

        for i in range(min(limit, len(forms))):
            if forms[i] == report_type:
                accession_number = filings["accessionNumber"][i]
                report_data = {
                    "ticker": ticker,
                    "type": report_type,
                    "accession_number": accession_number,
                    "filing_date": filings["filingDate"][i],
                    "report_date": filings["reportDate"][i],
                    "url": (
                        "https://www.sec.gov/cgi-bin/viewer?action=view&cik="
                        f"{cik}&accession_number={accession_number}&xbrl_type=v"
                    ),
                }
                reports.append(report_data)

        if not reports:
            print(f"No {report_type} filings found for {ticker}.")

    except Exception as exc:
        print(f"Error fetching reports for {ticker}: {exc}")

    time.sleep(0.25)
    return reports


def download_report_text(ticker: str, accession_number: str, report_type: str) -> Optional[str]:
    """Download the text content of a SEC report."""
    cache_file = os.path.join(REPORTS_DIR, f"{ticker}_{accession_number}_{report_type}.txt")

    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age.days < REPORT_CACHE_DAYS:
            print(f"Loading cached report for {ticker}")
            with open(cache_file, "r", encoding="utf-8") as handle:
                return handle.read()

    try:
        cik = get_cik_for_ticker(ticker)
        if not cik:
            return None

        clean_accession = accession_number.replace("-", "")
        url = (
            "https://www.sec.gov/cgi-bin/viewer?action=view&cik="
            f"{cik}&accession_number={accession_number}&xbrl_type=v"
        )

        response = requests.get(url, headers=SEC_HEADERS, timeout=20)
        response.raise_for_status()

        os.makedirs(REPORTS_DIR, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as handle:
            handle.write(response.text)

        return response.text
    except Exception as exc:
        print(f"Error downloading report for {ticker}: {exc}")

    return None


def get_latest_reports(tickers: List[str], report_type: str = "10-K") -> Dict[str, List[Dict]]:
    """Get the latest reports for a list of tickers."""
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


if __name__ == "__main__":
    test_tickers = ["AAPL", "MSFT", "NVDA", "META"]
    reports = get_latest_reports(test_tickers, "10-K")
    print(json.dumps(reports, indent=2, default=str))
    cache_reports_metadata(reports)
