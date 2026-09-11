"""Module for selecting and managing investment universe."""

import os
from typing import Dict, List

import pandas as pd
import yfinance as yf

from config import CACHE_DIR

# Use a curated, valid set of Nasdaq/large-cap tickers for reliable real-data runs.
# This avoids a large number of delisted or invalid symbols that trigger noisy
# SEC/yfinance 404 responses during the screening flow.
NASDAQ_100_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "AVGO", "ASML",
    "AMD", "INTC", "QCOM", "INTU", "CSCO", "PEP", "COST", "CMCSA", "ADBE",
    "NFLX", "PYPL", "CRWD", "AZN", "ABNB", "LRCX", "ISRG", "VRTX", "PCAR",
    "REGN", "ORLY", "AMAT", "KLAC", "PAYX", "MXIM", "ANSS", "ADI", "ROST",
    "CPRT", "FTNT", "ZM", "SPLK", "NTNX", "DXCM", "MNST", "KDP", "WDAY",
    "OKTA", "NET", "CHWY", "PTON", "SHOP", "TMUS", "DOCU", "BKNG", "ILMN",
    "UBER", "SPOT", "AFRM", "SQ", "DASH", "RBLX", "ZS", "DDOG", "MDB",
    "PLTR", "ON", "PDD", "MSTR", "VRSK", "CPNG", "JD", "SIRI", "SNPS",
    "CDNS", "MELI", "PANW", "MRVL", "PRGS", "TROW", "NDAQ", "GILD", "FISV",
    "NWSA", "NWS"
]


def get_nasdaq_100_universe() -> List[str]:
    """Return the valid NASDAQ universe used for screening."""
    return NASDAQ_100_TICKERS


def fetch_stock_data(tickers: List[str], period: str = "1y") -> pd.DataFrame:
    """Fetch current stock prices and basic info for given tickers."""
    stock_data = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period=period)

            if not hist.empty and info.get("regularMarketPrice") is not None:
                stock_data.append({
                    "ticker": ticker,
                    "company_name": info.get("longName", "N/A"),
                    "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                    "market_cap": info.get("marketCap", None),
                    "pe_ratio": info.get("trailingPE", None),
                    "52_week_high": info.get("fiftyTwoWeekHigh", None),
                    "52_week_low": info.get("fiftyTwoWeekLow", None),
                    "dividend_yield": info.get("dividendYield", None),
                    "sector": info.get("sector", "N/A"),
                    "industry": info.get("industry", "N/A"),
                })
        except Exception as exc:  # pragma: no cover - noisy but expected for some tickers
            print(f"Warning: unable to fetch data for {ticker}: {exc}")
            continue

    df = pd.DataFrame(stock_data)

    cache_file = os.path.join(CACHE_DIR, "stock_universe.json")
    os.makedirs(CACHE_DIR, exist_ok=True)
    if not df.empty:
        df.to_json(cache_file, orient="records", indent=2)

    return df


def get_stock_universe() -> pd.DataFrame:
    """Get the complete stock universe with current data."""
    print("Fetching curated Nasdaq stock universe...")
    tickers = get_nasdaq_100_universe()
    universe_df = fetch_stock_data(tickers)

    print(f"Successfully fetched data for {len(universe_df)} stocks")
    return universe_df


if __name__ == "__main__":
    universe = get_stock_universe()
    print(universe.head(10))
    print(f"\nTotal stocks: {len(universe)}")
