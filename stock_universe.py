"""Module for selecting and managing investment universe."""

import yfinance as yf
import pandas as pd
from typing import List, Dict
import json
import os
from config import CACHE_DIR

# NASDAQ 100 tickers (top companies)
NASDAQ_100_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "GOOGL", "GOOG", "META", "AVGO", "ASML",
    "NFLX", "AMD", "QCOM", "INTC", "INTU", "CSCO", "PEP", "COST", "CMCSA", "ADBE",
    "SNPS", "CDNS", "VRTX", "TSCO", "MELI", "PYPL", "MRNA", "CRWD", "AZN", "ABNB",
    "LRCX", "ISRG", "AMD", "PCAR", "REGN", "ORLY", "AMAT", "KLAC", "PAYX", "MXIM",
    "ANSS", "JD", "ADI", "ROST", "ULVR", "CPRT", "FTNT", "ZM", "SPLK", "NTNX",
    "DXCM", "SIRI", "TCOM", "MNST", "KDP", "WDAY", "OKTA", "NET", "CHWY", "PTON",
    "RUSH", "SHOP", "SNPS", "TMUS", "DOCU", "BKNG", "ILMN", "SUMO", "ESTC", "GFS",
    "NFLX", "LCID", "RIVN", "PLTR", "ROKU", "FVRR", "UBER", "SPOT", "AFRM", "SQ",
    "DASH", "ABNB", "RBLX", "ZS", "DDOG", "NEON", "MDB", "ENVX", "TPG", "BLDR",
    "KNSL", "DHI", "LEN", "MSTR", "AVGO", "QCOM", "ADSK", "VRSK", "JBHT", "CPNG"
][:100]  # Limit to 100


def get_nasdaq_100_universe() -> List[str]:
    """Get list of NASDAQ 100 ticker symbols.
    
    Returns:
        List of ticker symbols
    """
    return NASDAQ_100_TICKERS


def fetch_stock_data(tickers: List[str], period: str = "1y") -> pd.DataFrame:
    """Fetch current stock prices and basic info for given tickers.
    
    Args:
        tickers: List of ticker symbols
        period: Time period for historical data
        
    Returns:
        DataFrame with stock data including current price, market cap, etc.
    """
    stock_data = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period=period)
            
            if not hist.empty and "currentPrice" in info:
                stock_data.append({
                    "ticker": ticker,
                    "company_name": info.get("longName", "N/A"),
                    "current_price": info.get("currentPrice", None),
                    "market_cap": info.get("marketCap", None),
                    "pe_ratio": info.get("trailingPE", None),
                    "52_week_high": info.get("fiftyTwoWeekHigh", None),
                    "52_week_low": info.get("fiftyTwoWeekLow", None),
                    "dividend_yield": info.get("dividendYield", None),
                    "sector": info.get("sector", "N/A"),
                    "industry": info.get("industry", "N/A"),
                })
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            continue
    
    df = pd.DataFrame(stock_data)
    
    # Cache the data
    cache_file = os.path.join(CACHE_DIR, "stock_universe.json")
    df.to_json(cache_file, orient="records", indent=2)
    
    return df


def get_stock_universe() -> pd.DataFrame:
    """Get the complete stock universe with current data.
    
    Returns:
        DataFrame with all stocks in the investment universe
    """
    print("Fetching NASDAQ 100 stock universe...")
    tickers = get_nasdaq_100_universe()
    universe_df = fetch_stock_data(tickers)
    
    print(f"Successfully fetched data for {len(universe_df)} stocks")
    return universe_df


if __name__ == "__main__":
    universe = get_stock_universe()
    print(universe.head(10))
    print(f"\nTotal stocks: {len(universe)}")
