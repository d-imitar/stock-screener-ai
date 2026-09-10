"""Main orchestrator for the stock screener - ties all modules together."""

import json
import sys
from typing import Dict, List, Optional
import pandas as pd

from stock_universe import get_stock_universe
from report_downloader import get_latest_reports, download_report_text
from equity_analyzer import analyze_multiple_stocks
from stock_ranker import StockRanker
from config import CACHE_DIR


class StockScreener:
    """Main orchestrator for the AI-powered stock screener."""
    
    def __init__(self):
        """Initialize the stock screener."""
        self.universe_df = None
        self.reports = {}
        self.analysis_results = {}
        self.ranker = StockRanker()
        self.ranked_df = None
    
    def step_1_get_universe(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Step 1: Select investment universe (NASDAQ 100).
        
        Args:
            limit: Optional limit on number of stocks
            
        Returns:
            DataFrame with stock universe
        """
        print("\n" + "="*80)
        print("STEP 1: SELECTING INVESTMENT UNIVERSE")
        print("="*80)
        
        self.universe_df = get_stock_universe()
        
        if limit:
            self.universe_df = self.universe_df.head(limit)
        
        print(f"\n✓ Successfully loaded {len(self.universe_df)} stocks from NASDAQ 100")
        print("\nSample of universe:")
        print(self.universe_df[['ticker', 'company_name', 'current_price', 'sector']].head(10).to_string(index=False))
        
        return self.universe_df
    
    def step_2_download_reports(self, tickers: Optional[List[str]] = None, report_type: str = "10-K") -> Dict:
        """Step 2: Download latest quarterly/annual reports.
        
        Args:
            tickers: Optional list of specific tickers to process
            report_type: Type of report ("10-K" or "10-Q")
            
        Returns:
            Dictionary of reports metadata
        """
        print("\n" + "="*80)
        print("STEP 2: DOWNLOADING LATEST REPORTS")
        print("="*80)
        
        if self.universe_df is None:
            print("ERROR: Please run step_1_get_universe first")
            return {}
        
        # Use provided tickers or all from universe
        if tickers is None:
            tickers = self.universe_df['ticker'].tolist()
        
        print(f"\nDownloading {report_type} reports for {len(tickers)} stocks...")
        
        self.reports = get_latest_reports(tickers, report_type)
        
        print(f"\n✓ Successfully fetched reports for {len(self.reports)} stocks")
        
        # Show summary
        for ticker, reports in list(self.reports.items())[:5]:
            if reports:
                print(f"  • {ticker}: {reports[0]['filing_date']}")
        
        if len(self.reports) > 5:
            print(f"  ... and {len(self.reports) - 5} more")
        
        return self.reports
    
    def step_3_conduct_research(self, sample_size: Optional[int] = None) -> Dict:
        """Step 3: Conduct equity research analysis using AI.
        
        Args:
            sample_size: Optional limit on number of stocks to analyze
            
        Returns:
            Dictionary of analysis results
        """
        print("\n" + "="*80)
        print("STEP 3: CONDUCTING EQUITY RESEARCH ANALYSIS")
        print("="*80)
        
        if self.universe_df is None or self.reports is None:
            print("ERROR: Please run steps 1 and 2 first")
            return {}
        
        # Prepare analysis data
        stocks_to_analyze = {}
        
        for ticker in self.reports.keys():
            if sample_size and len(stocks_to_analyze) >= sample_size:
                break
            
            # Get stock data
            stock_row = self.universe_df[self.universe_df['ticker'] == ticker]
            if stock_row.empty:
                continue
            
            # Get report text (simplified - in production would download actual report)
            report_text = f"Recent {ticker} financial report. [Report text would be downloaded from SEC EDGAR]"
            
            stocks_to_analyze[ticker] = {
                "company_name": stock_row.iloc[0]['company_name'],
                "report_text": report_text,
                "financial_data": {
                    "current_price": stock_row.iloc[0]['current_price'],
                    "market_cap": stock_row.iloc[0]['market_cap'],
                    "pe_ratio": stock_row.iloc[0]['pe_ratio'],
                    "52_week_low": stock_row.iloc[0]['52_week_low'],
                    "52_week_high": stock_row.iloc[0]['52_week_high'],
                    "dividend_yield": stock_row.iloc[0]['dividend_yield'],
                    "sector": stock_row.iloc[0]['sector'],
                    "industry": stock_row.iloc[0]['industry'],
                }
            }
        
        print(f"\nAnalyzing {len(stocks_to_analyze)} stocks using OpenAI API...")
        print("Note: This requires a valid OPENAI_API_KEY in your .env file")
        
        try:
            self.analysis_results = analyze_multiple_stocks(stocks_to_analyze)
            
            # Count successful analyses
            successful = sum(1 for r in self.analysis_results.values() if "error" not in r)
            print(f"\n✓ Successfully analyzed {successful} stocks")
            
            # Show sample analysis
            for ticker, analysis in list(self.analysis_results.items())[:2]:
                if "error" not in analysis:
                    print(f"\n  {ticker} - {analysis.get('recommendation', 'N/A')}")
                    if analysis.get('target_price'):
                        print(f"    Target Price: ${analysis['target_price']:.2f}")
                        if analysis.get('upside_potential'):
                            print(f"    Upside Potential: {analysis['upside_potential']:.2f}%")
        
        except Exception as e:
            print(f"\n⚠ Error during analysis: {str(e)}")
            print("Make sure OPENAI_API_KEY is set in your .env file")
        
        return self.analysis_results
    
    def step_4_rank_stocks(self) -> pd.DataFrame:
        """Step 4: Rank all stocks based on upside potential.
        
        Returns:
            DataFrame with ranked stocks
        """
        print("\n" + "="*80)
        print("STEP 4: RANKING STOCKS BY UPSIDE POTENTIAL")
        print("="*80)
        
        if self.universe_df is None or not self.analysis_results:
            print("ERROR: Please run steps 1-3 first")
            return pd.DataFrame()
        
        print("\nRanking stocks based on upside potential and investment metrics...")
        
        self.ranked_df = self.ranker.rank_stocks(self.analysis_results, self.universe_df)
        
        print(f"\n✓ Successfully ranked {len(self.ranked_df)} stocks")
        
        # Show top opportunities
        if not self.ranked_df.empty:
            print("\n" + "-"*80)
            print("TOP 10 OPPORTUNITIES")
            print("-"*80)
            
            top_10 = self.ranker.get_top_stocks(10)
            print(top_10[['rank', 'ticker', 'company_name', 'recommendation', 
                         'current_price', 'target_price', 'upside_potential_%']].to_string(index=False))
        
        return self.ranked_df
    
    def generate_report(self) -> str:
        """Generate a comprehensive summary report.
        
        Returns:
            Report text
        """
        if self.ranked_df is None or self.ranked_df.empty:
            return "No ranked data available. Please run all 4 steps first."
        
        report = self.ranker.generate_summary_report()
        return report
    
    def export_results(self, format: str = "csv") -> str:
        """Export screening results to file.
        
        Args:
            format: Export format ("csv" or "json")
            
        Returns:
            Path to exported file
        """
        if self.ranked_df is None or self.ranked_df.empty:
            print("No data to export")
            return ""
        
        if format.lower() == "csv":
            return self.ranker.export_rankings("stock_rankings.csv")
        elif format.lower() == "json":
            return self.ranker.export_to_json("stock_rankings.json")
        else:
            print(f"Unknown format: {format}")
            return ""
    
    def run_full_screen(self, limit_universe: Optional[int] = None, 
                       sample_analysis: Optional[int] = None) -> Dict:
        """Run the complete stock screening pipeline.
        
        Args:
            limit_universe: Optional limit on universe size
            sample_analysis: Optional sample size for analysis
            
        Returns:
            Dictionary with results
        """
        print("\n" + "🚀 "*20)
        print("STARTING AI-POWERED STOCK SCREENER")
        print("🚀 "*20)
        
        # Step 1: Get universe
        self.step_1_get_universe(limit=limit_universe)
        
        # Step 2: Download reports
        tickers = self.universe_df['ticker'].tolist()
        self.step_2_download_reports(tickers=tickers)
        
        # Step 3: Conduct research
        self.step_3_conduct_research(sample_size=sample_analysis)
        
        # Step 4: Rank stocks
        self.step_4_rank_stocks()
        
        # Generate and print report
        print("\n" + "="*80)
        print("FINAL SCREENING REPORT")
        print("="*80)
        print(self.generate_report())
        
        # Export results
        csv_path = self.export_results("csv")
        json_path = self.export_results("json")
        
        print("\n" + "="*80)
        print("SCREENING COMPLETE")
        print("="*80)
        print(f"Results exported to:")
        print(f"  • CSV: {csv_path}")
        print(f"  • JSON: {json_path}")
        
        return {
            "universe_size": len(self.universe_df),
            "stocks_analyzed": len(self.analysis_results),
            "stocks_ranked": len(self.ranked_df) if self.ranked_df is not None else 0,
            "top_opportunity": self.ranked_df.iloc[0]['ticker'] if not self.ranked_df.empty else None,
        }


def main():
    """Main entry point for the stock screener."""
    screener = StockScreener()
    
    # Run screening with limits for demo
    # In production, remove these limits
    results = screener.run_full_screen(
        limit_universe=20,      # Limit to 20 stocks for demo
        sample_analysis=5       # Analyze only 5 stocks due to API costs
    )
    
    print("\nScreening Results Summary:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
