"""Module for downloading and managing SEC reports (10-K, 10-Q)."""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser
from config import REPORTS_DIR, REPORT_CACHE_DAYS

# SEC EDGAR RSS Feed URLs
SEC_FEEDS = {
    "10-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=10-K&dateb=&owner=exclude&count=100&format=rss",
    "10-Q": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=10-Q&dateb=&owner=exclude&count=100&format=rss",
}

SEC_EDGAR_BASE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"


def get_cik_for_ticker(ticker: str) -> Optional[str]:
    """Get CIK number for a given ticker symbol.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        CIK number or None if not found
    """
    try:
        # Query SEC EDGAR lookup API
        url = f"{SEC_EDGAR_BASE_URL}?company={ticker}&owner=exclude&action=getcompany&format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get("cik_lookup"):
            cik = list(data["cik_lookup"].values())[0]
            return str(cik).zfill(10)  # CIK should be 10 digits
    except Exception as e:
        print(f"Error fetching CIK for {ticker}: {str(e)}")
    
    return None


def fetch_reports_for_ticker(ticker: str, report_type: str = "10-K", limit: int = 2) -> List[Dict]:
    """Fetch recent SEC reports for a given ticker.
    
    Args:
        ticker: Stock ticker symbol
        report_type: Type of report ("10-K" or "10-Q")
        limit: Maximum number of reports to fetch
        
    Returns:
        List of report metadata
    """
    cik = get_cik_for_ticker(ticker)
    if not cik:
        print(f"Could not find CIK for {ticker}")
        return []
    
    reports = []
    try:
        # Query SEC EDGAR for filings
        url = f"{SEC_EDGAR_BASE_URL}?action=getcompany&CIK={cik}&type={report_type}&dateb=&owner=exclude&count={limit}&format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        filings = data.get("filings", {}).get("recent", {})
        
        for i in range(min(limit, len(filings.get("form", [])))):
            if filings["form"][i] == report_type:
                report_data = {
                    "ticker": ticker,
                    "type": report_type,
                    "accession_number": filings["accessionNumber"][i],
                    "filing_date": filings["filingDate"][i],
                    "report_date": filings["reportDate"][i],
                    "url": f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={filings['accessionNumber'][i]}&xbrl_type=v",
                }
                reports.append(report_data)
    except Exception as e:
        print(f"Error fetching reports for {ticker}: {str(e)}")
    
    return reports


def download_report_text(ticker: str, accession_number: str, report_type: str) -> Optional[str]:
    """Download the text content of a SEC report.
    
    Args:
        ticker: Stock ticker symbol
        accession_number: SEC accession number
        report_type: Type of report
        
    Returns:
        Report text content or None if download failed
    """
    cache_file = os.path.join(REPORTS_DIR, f"{ticker}_{accession_number}_{report_type}.txt")
    
    # Check cache
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age.days < REPORT_CACHE_DAYS:
            print(f"Loading cached report for {ticker}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
    
    try:
        # Construct SEC filing URL
        clean_accession = accession_number.replace("-", "")
        url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={get_cik_for_ticker(ticker)}&accession_number={accession_number}&xbrl_type=v"
        
        # Alternative: download from EDGAR directly
        base_url = f"https://www.sec.gov/Archives/edgar/0000{get_cik_for_ticker(ticker)[-7:]}/{clean_accession}/"
        
        print(f"Downloading {report_type} for {ticker}...")
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        
        # Save to cache
        os.makedirs(REPORTS_DIR, exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return response.text
    except Exception as e:
        print(f"Error downloading report for {ticker}: {str(e)}")
    
    return None


def get_latest_reports(tickers: List[str], report_type: str = "10-K") -> Dict[str, List[Dict]]:
    """Get the latest reports for a list of tickers.
    
    Args:
        tickers: List of stock ticker symbols
        report_type: Type of report ("10-K" or "10-Q")
        
    Returns:
        Dictionary mapping ticker to list of report metadata
    """
    all_reports = {}
    
    for ticker in tickers:
        print(f"Fetching reports for {ticker}...")
        reports = fetch_reports_for_ticker(ticker, report_type, limit=1)
        if reports:
            all_reports[ticker] = reports
    
    return all_reports


def cache_reports_metadata(reports: Dict[str, List[Dict]]) -> None:
    """Cache reports metadata to JSON file.
    
    Args:
        reports: Dictionary of reports metadata
    """
    cache_file = os.path.join(REPORTS_DIR, "reports_metadata.json")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    with open(cache_file, 'w') as f:
        json.dump(reports, f, indent=2, default=str)


def load_reports_metadata() -> Dict[str, List[Dict]]:
    """Load cached reports metadata.
    
    Returns:
        Dictionary of reports metadata or empty dict if not found
    """
    cache_file = os.path.join(REPORTS_DIR, "reports_metadata.json")
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    return {}


if __name__ == "__main__":
    # Example usage
    test_tickers = ["AAPL", "MSFT", "GOOGL"]
    reports = get_latest_reports(test_tickers, "10-K")
    print(json.dumps(reports, indent=2, default=str))
    cache_reports_metadata(reports)
