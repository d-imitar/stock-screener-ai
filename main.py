"""Main orchestrator for the stock screener - ties all modules together."""

import argparse
import json
import os
from typing import Dict, List, Optional

import pandas as pd

from config import ANALYSIS_MODEL
from equity_analyzer import analyze_multiple_stocks
from report_downloader import download_report_text, get_latest_reports
from stock_ranker import StockRanker
from stock_universe import get_stock_universe


class StockScreener:
    """Main orchestrator for the AI-powered stock screener."""

    def __init__(self, model: Optional[str] = None, demo_only: bool = False):
        """Initialize the stock screener."""
        self.model = model or ANALYSIS_MODEL
        self.demo_only = demo_only
        self.universe_df = None
        self.reports = {}
        self.analysis_results = {}
        self.ranker = StockRanker()
        self.ranked_df = None

    def step_1_get_universe(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Step 1: Select investment universe (NASDAQ 100)."""
        print("\n" + "=" * 80)
        print("STEP 1: SELECTING INVESTMENT UNIVERSE")
        print("=" * 80)

        self.universe_df = get_stock_universe()

        if limit:
            self.universe_df = self.universe_df.head(limit)

        print(f"\n✓ Successfully loaded {len(self.universe_df)} stocks from NASDAQ 100")
        print("\nSample of universe:")
        print(self.universe_df[["ticker", "company_name", "current_price", "sector"]].head(10).to_string(index=False))

        return self.universe_df

    def step_2_download_reports(self, tickers: Optional[List[str]] = None, report_type: str = "10-K") -> Dict:
        """Step 2: Download latest quarterly/annual reports."""
        print("\n" + "=" * 80)
        print("STEP 2: DOWNLOADING LATEST REPORTS")
        print("=" * 80)

        if self.universe_df is None:
            print("ERROR: Please run step_1_get_universe first")
            return {}

        if tickers is None:
            tickers = self.universe_df["ticker"].tolist()

        print(f"\nDownloading {report_type} reports for {len(tickers)} stocks...")
        self.reports = get_latest_reports(tickers, report_type)

        print(f"\n✓ Successfully fetched reports for {len(self.reports)} stocks")

        for ticker, reports in list(self.reports.items())[:5]:
            if reports:
                print(f"  • {ticker}: {reports[0]['filing_date']}")

        if len(self.reports) > 5:
            print(f"  ... and {len(self.reports) - 5} more")

        return self.reports

    def step_3_conduct_research(self, sample_size: Optional[int] = None) -> Dict:
        """Step 3: Conduct equity research analysis using AI."""
        print("\n" + "=" * 80)
        print("STEP 3: CONDUCTING EQUITY RESEARCH ANALYSIS")
        print("=" * 80)

        if self.universe_df is None or self.reports is None:
            print("ERROR: Please run steps 1 and 2 first")
            return {}

        stocks_to_analyze = {}

        for ticker in self.reports.keys():
            if sample_size and len(stocks_to_analyze) >= sample_size:
                break

            stock_row = self.universe_df[self.universe_df["ticker"] == ticker]
            if stock_row.empty:
                continue

            report_text = ""
            report_entries = self.reports.get(ticker, [])
            if report_entries:
                report_info = report_entries[0]
                accession_number = report_info.get("accession_number")
                if accession_number:
                    report_text = download_report_text(ticker, accession_number, "10-K") or ""

            if not report_text:
                report_text = (
                    f"Recent {ticker} financial report. "
                    f"This demo environment used a generated analysis fallback because detailed SEC text retrieval was unavailable."
                )

            stocks_to_analyze[ticker] = {
                "company_name": stock_row.iloc[0]["company_name"],
                "report_text": report_text,
                "financial_data": {
                    "current_price": stock_row.iloc[0]["current_price"],
                    "market_cap": stock_row.iloc[0]["market_cap"],
                    "pe_ratio": stock_row.iloc[0]["pe_ratio"],
                    "52_week_low": stock_row.iloc[0]["52_week_low"],
                    "52_week_high": stock_row.iloc[0]["52_week_high"],
                    "dividend_yield": stock_row.iloc[0]["dividend_yield"],
                    "sector": stock_row.iloc[0]["sector"],
                    "industry": stock_row.iloc[0]["industry"],
                },
            }

        demo_message = "demo fallback enabled" if self.demo_only else "AI credentials are optional in demo mode; if missing, the system will generate a deterministic fallback analysis."
        print(f"\nAnalyzing {len(stocks_to_analyze)} stocks using {self.model}...")
        print(demo_message)

        try:
            self.analysis_results = analyze_multiple_stocks(stocks_to_analyze, model=self.model, demo_only=self.demo_only)
            successful = sum(1 for r in self.analysis_results.values() if "error" not in r)
            print(f"\n✓ Successfully analyzed {successful} stocks")

            for ticker, analysis in list(self.analysis_results.items())[:2]:
                if "error" not in analysis:
                    print(f"\n  {ticker} - {analysis.get('recommendation', 'N/A')}")
                    if analysis.get("target_price"):
                        print(f"    Target Price: ${analysis['target_price']:.2f}")
                        if analysis.get("upside_potential"):
                            print(f"    Upside Potential: {analysis['upside_potential']:.2f}%")
        except Exception as e:
            print(f"\n⚠ Error during analysis: {str(e)}")
            print("The project will continue in demo mode if no API keys are configured.")

        return self.analysis_results

    def step_4_rank_stocks(self) -> pd.DataFrame:
        """Step 4: Rank all stocks based on upside potential."""
        print("\n" + "=" * 80)
        print("STEP 4: RANKING STOCKS BY UPSIDE POTENTIAL")
        print("=" * 80)

        if self.universe_df is None or not self.analysis_results:
            print("ERROR: Please run steps 1-3 first")
            return pd.DataFrame()

        print("\nRanking stocks based on upside potential and investment metrics...")
        self.ranked_df = self.ranker.rank_stocks(self.analysis_results, self.universe_df)

        print(f"\n✓ Successfully ranked {len(self.ranked_df)} stocks")

        if not self.ranked_df.empty:
            print("\n" + "-" * 80)
            print("TOP 10 OPPORTUNITIES")
            print("-" * 80)
            top_10 = self.ranker.get_top_stocks(10)
            print(
                top_10[["rank", "ticker", "company_name", "recommendation", "current_price", "target_price", "upside_potential_%"]]
                .to_string(index=False)
            )

        return self.ranked_df

    def generate_report(self) -> str:
        """Generate a comprehensive summary report."""
        if self.ranked_df is None or self.ranked_df.empty:
            return "No ranked data available. Please run all 4 steps first."

        return self.ranker.generate_summary_report()

    def export_results(self, format: str = "csv") -> str:
        """Export screening results to file."""
        if self.ranked_df is None or self.ranked_df.empty:
            print("No data to export")
            return ""

        if format.lower() == "csv":
            return self.ranker.export_rankings("stock_rankings.csv")
        if format.lower() == "json":
            return self.ranker.export_to_json("stock_rankings.json")
        print(f"Unknown format: {format}")
        return ""

    def run_full_screen(self, limit_universe: Optional[int] = None, sample_analysis: Optional[int] = None) -> Dict:
        """Run the complete stock screening pipeline."""
        print("\n" + "🚀 " * 20)
        print("STARTING AI-POWERED STOCK SCREENER")
        print("🚀 " * 20)

        self.step_1_get_universe(limit=limit_universe)
        tickers = self.universe_df["ticker"].tolist()
        self.step_2_download_reports(tickers=tickers)
        self.step_3_conduct_research(sample_size=sample_analysis)
        self.step_4_rank_stocks()

        print("\n" + "=" * 80)
        print("FINAL SCREENING REPORT")
        print("=" * 80)
        print(self.generate_report())

        csv_path = self.export_results("csv")
        json_path = self.export_results("json")

        print("\n" + "=" * 80)
        print("SCREENING COMPLETE")
        print("=" * 80)
        print("Results exported to:")
        print(f"  • CSV: {csv_path}")
        print(f"  • JSON: {json_path}")

        return {
            "universe_size": len(self.universe_df),
            "stocks_analyzed": len(self.analysis_results),
            "stocks_ranked": len(self.ranked_df) if self.ranked_df is not None else 0,
            "top_opportunity": self.ranked_df.iloc[0]["ticker"] if not self.ranked_df.empty else None,
        }


def parse_args():
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="AI-powered stock screener")
    parser.add_argument("--limit", type=int, default=20, help="Max number of stocks to screen from the universe")
    parser.add_argument("--sample", type=int, default=5, help="Max number of stocks to analyze")
    parser.add_argument("--model", choices=["gpt-4-turbo", "claude-3-haiku", "moonshot", "baichuan-4-finance"], default=ANALYSIS_MODEL, help="Model to use for analysis")
    parser.add_argument("--demo-only", action="store_true", help="Force deterministic demo analysis even when API credentials are configured")
    return parser.parse_args()


def main():
    """Main entry point for the stock screener."""
    args = parse_args()
    screener = StockScreener(model=args.model, demo_only=args.demo_only)

    results = screener.run_full_screen(
        limit_universe=args.limit,
        sample_analysis=args.sample,
    )

    print("\nScreening Results Summary:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
