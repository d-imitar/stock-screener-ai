"""Module for selecting and managing investment universe."""

import os
from typing import List

import pandas as pd
import yfinance as yf

from config import CACHE_DIR

# Use a small, valid, well-known list of U.S. large-cap tickers.
# This avoids the noisy delisted/invalid symbols that trigger 404s.
NASDAQ_VALID_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "AVGO",
    "ASML", "AMD", "INTC", "QCOM", "INTU", "CSCO", "PEP", "COST",
    "CMCSA", "ADBE", "NFLX", "PYPL", "CRWD", "AZN", "LRCX", "ORLY",
    "AMAT", "KLAC", "PAYX"
]


def get_nasdaq_100_universe() -> List[str]:
    """Return the valid stock universe used for testing and screening."""
    return NASDAQ_VALID_TICKERS


def fetch_stock_data(tickers: List[str], period: str = "1y") -> pd.DataFrame:
    """Fetch current stock prices and basic info for given tickers."""
    stock_data = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period=period)

            if hist.empty:
                continue

            market_price = info.get("currentPrice") or info.get("regularMarketPrice")
            if market_price is None:
                continue

            stock_data.append({
                "ticker": ticker,
                "company_name": info.get("longName", "N/A"),
                "current_price": market_price,
                "market_cap": info.get("marketCap", None),
                "pe_ratio": info.get("trailingPE", None),
                "52_week_high": info.get("fiftyTwoWeekHigh", None),
                "52_week_low": info.get("fiftyTwoWeekLow", None),
                "dividend_yield": info.get("dividendYield", None),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
            })

        except Exception as exc:
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
    universe_df = fetch_stock_data(get_nasdaq_100_universe())
    print(f"Successfully fetched data for {len(universe_df)} stocks")
    return universe_df


if __name__ == "__main__":
    universe = get_stock_universe()
    print(universe.head(10))
    print(f"\nTotal stocks: {len(universe)}")