"""Module for ranking stocks based on upside potential and investment metrics."""

import pandas as pd
from typing import Dict, List, Optional
import json
import os
from config import CACHE_DIR
from datetime import datetime


class StockRanker:
    """Ranks stocks based on upside potential and other investment metrics."""
    
    def __init__(self):
        """Initialize the stock ranker."""
        self.ranked_stocks = []
        self.ranking_timestamp = None
    
    def calculate_upside_potential(self, target_price: float, current_price: float) -> float:
        """Calculate upside potential percentage.
        
        Args:
            target_price: Target price from analysis
            current_price: Current stock price
            
        Returns:
            Upside potential as percentage
        """
        if current_price <= 0:
            return 0.0
        return ((target_price - current_price) / current_price) * 100
    
    def rank_stocks(self, analysis_results: Dict, stock_universe: pd.DataFrame) -> pd.DataFrame:
        """Rank all stocks based on upside potential and other metrics.
        
        Args:
            analysis_results: Dictionary of analysis results from equity_analyzer
            stock_universe: DataFrame with stock universe data
            
        Returns:
            DataFrame with ranked stocks
        """
        ranked_data = []
        
        for ticker, analysis in analysis_results.items():
            if "error" in analysis:
                continue
            
            # Get stock data from universe
            stock_info = stock_universe[stock_universe['ticker'] == ticker]
            if stock_info.empty:
                continue
            
            current_price = stock_info.iloc[0]['current_price']
            target_price = analysis.get('target_price')
            recommendation = analysis.get('recommendation', 'HOLD')
            
            # Calculate metrics
            upside_potential = 0.0
            if target_price and current_price:
                upside_potential = self.calculate_upside_potential(target_price, current_price)
            
            # Risk score based on recommendation
            risk_score = self._get_risk_score(recommendation)
            
            # Composite score for ranking
            composite_score = self._calculate_composite_score(
                upside_potential=upside_potential,
                recommendation=recommendation,
                pe_ratio=stock_info.iloc[0]['pe_ratio']
            )
            
            ranked_data.append({
                'ticker': ticker,
                'company_name': analysis.get('company_name'),
                'current_price': current_price,
                'target_price': target_price,
                'upside_potential_%': round(upside_potential, 2),
                'recommendation': recommendation,
                'risk_score': risk_score,
                'composite_score': composite_score,
                'pe_ratio': stock_info.iloc[0]['pe_ratio'],
                'market_cap': stock_info.iloc[0]['market_cap'],
                'sector': stock_info.iloc[0]['sector'],
                'industry': stock_info.iloc[0]['industry'],
                '52_week_high': stock_info.iloc[0]['52_week_high'],
                '52_week_low': stock_info.iloc[0]['52_week_low'],
                'dividend_yield': stock_info.iloc[0]['dividend_yield'],
            })
        
        # Create DataFrame and sort by upside potential
        df = pd.DataFrame(ranked_data)
        
        if not df.empty:
            df = df.sort_values('upside_potential_%', ascending=False).reset_index(drop=True)
            df['rank'] = range(1, len(df) + 1)
            
            # Reorder columns
            cols = ['rank', 'ticker', 'company_name', 'recommendation', 'current_price', 
                   'target_price', 'upside_potential_%', 'composite_score', 'risk_score',
                   'pe_ratio', 'sector', 'industry', 'market_cap', '52_week_high', 
                   '52_week_low', 'dividend_yield']
            df = df[[col for col in cols if col in df.columns]]
        
        self.ranked_stocks = df
        self.ranking_timestamp = datetime.now()
        
        return df
    
    def _get_risk_score(self, recommendation: str) -> float:
        """Get risk score based on recommendation.
        
        Args:
            recommendation: Investment recommendation (BUY, HOLD, SELL)
            
        Returns:
            Risk score (0-10, lower is better)
        """
        risk_map = {
            'BUY': 2.0,
            'HOLD': 5.0,
            'SELL': 8.0,
        }
        return risk_map.get(recommendation, 5.0)
    
    def _calculate_composite_score(self, upside_potential: float, 
                                   recommendation: str, pe_ratio: Optional[float]) -> float:
        """Calculate a composite score for ranking.
        
        Args:
            upside_potential: Upside potential percentage
            recommendation: Investment recommendation
            pe_ratio: Current P/E ratio
            
        Returns:
            Composite score (higher is better)
        """
        # Normalize upside potential (0-100)
        upside_score = min(max(upside_potential / 2, 0), 100)  # Scale down upside
        
        # Recommendation score
        recommendation_score = {
            'BUY': 100,
            'HOLD': 50,
            'SELL': 0,
        }.get(recommendation, 50)
        
        # Valuation score (lower P/E is better, but we need reasonable bounds)
        valuation_score = 50
        if pe_ratio and pe_ratio > 0:
            # Target P/E around 20, score drops as we move away
            pe_target = 20
            valuation_score = max(0, 100 - (abs(pe_ratio - pe_target) / pe_target) * 50)
        
        # Weighted average: 50% upside, 30% recommendation, 20% valuation
        composite = (upside_score * 0.5) + (recommendation_score * 0.3) + (valuation_score * 0.2)
        
        return round(composite, 2)
    
    def get_top_stocks(self, n: int = 10) -> pd.DataFrame:
        """Get top N stocks by upside potential.
        
        Args:
            n: Number of top stocks to return
            
        Returns:
            DataFrame with top N stocks
        """
        if self.ranked_stocks.empty:
            return pd.DataFrame()
        
        return self.ranked_stocks.head(n)
    
    def get_stocks_by_recommendation(self, recommendation: str) -> pd.DataFrame:
        """Get all stocks with a specific recommendation.
        
        Args:
            recommendation: Recommendation to filter by (BUY, HOLD, SELL)
            
        Returns:
            DataFrame with filtered stocks
        """
        if self.ranked_stocks.empty:
            return pd.DataFrame()
        
        return self.ranked_stocks[self.ranked_stocks['recommendation'] == recommendation]
    
    def get_best_buy_opportunities(self, n: int = 10, min_upside: float = 20.0) -> pd.DataFrame:
        """Get best BUY opportunities with minimum upside potential.
        
        Args:
            n: Number of stocks to return
            min_upside: Minimum upside potential %
            
        Returns:
            DataFrame with best buy opportunities
        """
        if self.ranked_stocks.empty:
            return pd.DataFrame()
        
        buys = self.ranked_stocks[
            (self.ranked_stocks['recommendation'] == 'BUY') & 
            (self.ranked_stocks['upside_potential_%'] >= min_upside)
        ]
        
        return buys.head(n)
    
    def export_rankings(self, filename: str = "stock_rankings.csv") -> str:
        """Export rankings to CSV file.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if self.ranked_stocks.empty:
            print("No stocks to export")
            return ""
        
        output_path = os.path.join(CACHE_DIR, filename)
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        self.ranked_stocks.to_csv(output_path, index=False)
        print(f"Rankings exported to {output_path}")
        
        return output_path
    
    def export_to_json(self, filename: str = "stock_rankings.json") -> str:
        """Export rankings to JSON file.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if self.ranked_stocks.empty:
            print("No stocks to export")
            return ""
        
        output_path = os.path.join(CACHE_DIR, filename)
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        export_data = {
            "timestamp": self.ranking_timestamp.isoformat() if self.ranking_timestamp else None,
            "total_stocks": len(self.ranked_stocks),
            "stocks": json.loads(self.ranked_stocks.to_json(orient='records'))
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Rankings exported to {output_path}")
        
        return output_path
    
    def generate_summary_report(self) -> str:
        """Generate a text summary report of the rankings.
        
        Returns:
            Summary report as string
        """
        if self.ranked_stocks.empty:
            return "No stocks to report"
        
        report = []
        report.append("=" * 80)
        report.append("STOCK SCREENER RANKING REPORT")
        report.append(f"Generated: {self.ranking_timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.ranking_timestamp else 'N/A'}")
        report.append("=" * 80)
        report.append("")
        
        # Top opportunities
        report.append("TOP 10 OPPORTUNITIES (By Upside Potential)")
        report.append("-" * 80)
        top_10 = self.get_top_stocks(10)
        for _, row in top_10.iterrows():
            report.append(
                f"{int(row['rank']):2}. {row['ticker']:6} | {row['recommendation']:5} | "
                f"${row['current_price']:8.2f} → ${row['target_price']:8.2f} | "
                f"+{row['upside_potential_%']:6.2f}% | Score: {row['composite_score']:6.2f}"
            )
        report.append("")
        
        # Summary statistics
        report.append("SUMMARY STATISTICS")
        report.append("-" * 80)
        buy_count = len(self.ranked_stocks[self.ranked_stocks['recommendation'] == 'BUY'])
        hold_count = len(self.ranked_stocks[self.ranked_stocks['recommendation'] == 'HOLD'])
        sell_count = len(self.ranked_stocks[self.ranked_stocks['recommendation'] == 'SELL'])
        
        report.append(f"Total Stocks Analyzed: {len(self.ranked_stocks)}")
        report.append(f"BUY Recommendations: {buy_count}")
        report.append(f"HOLD Recommendations: {hold_count}")
        report.append(f"SELL Recommendations: {sell_count}")
        report.append(f"Average Upside Potential: {self.ranked_stocks['upside_potential_%'].mean():.2f}%")
        report.append(f"Median Upside Potential: {self.ranked_stocks['upside_potential_%'].median():.2f}%")
        report.append("")
        
        # Best buys
        report.append("BEST BUY OPPORTUNITIES (BUY with >20% Upside)")
        report.append("-" * 80)
        best_buys = self.get_best_buy_opportunities(5)
        if not best_buys.empty:
            for _, row in best_buys.iterrows():
                report.append(
                    f"• {row['ticker']:6} ({row['company_name'][:30]:30}) | "
                    f"Target: ${row['target_price']:.2f} | +{row['upside_potential_%']:.2f}%"
                )
        else:
            report.append("No strong buy opportunities identified")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


if __name__ == "__main__":
    # Example usage
    print("Stock Ranker Module - Use in main.py for full functionality")
