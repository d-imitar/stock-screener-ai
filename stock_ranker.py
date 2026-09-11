"""Module for ranking stocks based on upside potential and investment metrics."""

import json
import os
from datetime import datetime
from typing import Dict, Optional

import pandas as pd

from config import CACHE_DIR


class StockRanker:
    """Ranks stocks based on upside potential and other investment metrics."""

    def __init__(self):
        self.ranked_stocks = pd.DataFrame()
        self.ranking_timestamp = None

    def calculate_upside_potential(self, target_price: float, current_price: float) -> float:
        if current_price is None or current_price <= 0:
            return 0.0
        if target_price is None:
            return 0.0
        return ((target_price - current_price) / current_price) * 100

    @staticmethod
    def _safe_recommendation(value: Optional[str]) -> str:
        if value is None:
            return "HOLD"
        return str(value).upper()

    @staticmethod
    def _safe_float(value):
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_numeric_text(value, default: str = "N/A") -> str:
        if value is None:
            return default
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return default

    def rank_stocks(self, analysis_results: Dict, stock_universe: pd.DataFrame) -> pd.DataFrame:
        ranked_data = []

        for ticker, analysis in analysis_results.items():
            if not isinstance(analysis, dict):
                continue

            if "error" in analysis:
                continue

            stock_info = stock_universe[stock_universe["ticker"] == ticker]
            if stock_info.empty:
                continue

            row = stock_info.iloc[0]

            current_price = self._safe_float(row.get("current_price"))
            recommendation = self._safe_recommendation(analysis.get("recommendation"))
            target_price = self._safe_float(analysis.get("target_price"))

            upside_potential = 0.0
            if current_price is not None and target_price is not None and current_price > 0:
                upside_potential = self.calculate_upside_potential(target_price, current_price)

            risk_score = self._get_risk_score(recommendation)
            composite_score = self._calculate_composite_score(
                upside_potential=upside_potential,
                recommendation=recommendation,
                pe_ratio=self._safe_float(row.get("pe_ratio")),
            )

            ranked_data.append(
                {
                    "ticker": ticker,
                    "company_name": analysis.get("company_name", row.get("company_name", "N/A")),
                    "current_price": current_price,
                    "target_price": target_price,
                    "upside_potential_%": round(upside_potential, 2),
                    "recommendation": recommendation,
                    "risk_score": risk_score,
                    "composite_score": composite_score,
                    "pe_ratio": self._safe_float(row.get("pe_ratio")),
                    "market_cap": self._safe_float(row.get("market_cap")),
                    "sector": row.get("sector", "N/A"),
                    "industry": row.get("industry", "N/A"),
                    "52_week_high": self._safe_float(row.get("52_week_high")),
                    "52_week_low": self._safe_float(row.get("52_week_low")),
                    "dividend_yield": self._safe_float(row.get("dividend_yield")),
                }
            )

        df = pd.DataFrame(ranked_data)

        if not df.empty:
            df = df.sort_values("upside_potential_%", ascending=False).reset_index(drop=True)
            df["rank"] = range(1, len(df) + 1)

            df["recommendation"] = df["recommendation"].fillna("HOLD")
            df["upside_potential_%"] = df["upside_potential_%"].fillna(0.0)

            cols = [
                "rank",
                "ticker",
                "company_name",
                "recommendation",
                "current_price",
                "target_price",
                "upside_potential_%",
                "composite_score",
                "risk_score",
                "pe_ratio",
                "sector",
                "industry",
                "market_cap",
                "52_week_high",
                "52_week_low",
                "dividend_yield",
            ]
            df = df[[col for col in cols if col in df.columns]]

        self.ranked_stocks = df
        self.ranking_timestamp = datetime.now()
        return df

    def _get_risk_score(self, recommendation: str) -> float:
        risk_map = {"BUY": 2.0, "HOLD": 5.0, "SELL": 8.0}
        return risk_map.get(str(recommendation).upper(), 5.0)

    def _calculate_composite_score(
        self,
        upside_potential: float,
        recommendation: str,
        pe_ratio: Optional[float],
    ) -> float:
        upside_score = min(max(upside_potential / 2, 0), 100)

        recommendation_score = {"BUY": 100, "HOLD": 50, "SELL": 0}.get(
            str(recommendation).upper(), 50
        )

        valuation_score = 50
        if pe_ratio and pe_ratio > 0:
            pe_target = 20
            valuation_score = max(0, 100 - (abs(pe_ratio - pe_target) / pe_target) * 50)

        composite = (upside_score * 0.5) + (recommendation_score * 0.3) + (valuation_score * 0.2)
        return round(composite, 2)

    def get_top_stocks(self, n: int = 10) -> pd.DataFrame:
        if self.ranked_stocks.empty:
            return pd.DataFrame()
        return self.ranked_stocks.head(n)

    def get_best_buy_opportunities(self, n: int = 10, min_upside: float = 20.0) -> pd.DataFrame:
        """Get best BUY opportunities with minimum upside potential."""
        if self.ranked_stocks.empty:
            return pd.DataFrame()

        buys = self.ranked_stocks[
            (self.ranked_stocks["recommendation"] == "BUY")
            & (self.ranked_stocks["upside_potential_%"] >= min_upside)
        ]

        return buys.head(n)

    def export_rankings(self, filename: str = "stock_rankings.csv") -> str:
        if self.ranked_stocks.empty:
            print("No stocks to export")
            return ""

        output_path = os.path.join(CACHE_DIR, filename)
        os.makedirs(CACHE_DIR, exist_ok=True)

        self.ranked_stocks.to_csv(output_path, index=False)
        print(f"Rankings exported to {output_path}")
        return output_path

    def export_to_json(self, filename: str = "stock_rankings.json") -> str:
        if self.ranked_stocks.empty:
            return ""

        output_path = os.path.join(CACHE_DIR, filename)
        os.makedirs(CACHE_DIR, exist_ok=True)

        export_data = {
            "timestamp": self.ranking_timestamp.isoformat() if self.ranking_timestamp else None,
            "total_stocks": len(self.ranked_stocks),
            "stocks": json.loads(self.ranked_stocks.to_json(orient="records")),
        }

        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(export_data, handle, indent=2)

        print(f"Rankings exported to {output_path}")
        return output_path

    def generate_summary_report(self) -> str:
        if self.ranked_stocks.empty:
            return "No stocks to report"

        report = []
        report.append("=" * 80)
        report.append("STOCK SCREENER RANKING REPORT")
        report.append(
            f"Generated: {self.ranking_timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.ranking_timestamp else 'N/A'}"
        )
        report.append("=" * 80)
        report.append("")

        report.append("TOP 10 OPPORTUNITIES (By Upside Potential)")
        report.append("-" * 80)
        top_10 = self.get_top_stocks(10)

        for _, row in top_10.iterrows():
            rec = row.get("recommendation") or "HOLD"
            target = self._safe_float(row.get("target_price"))
            current = self._safe_float(row.get("current_price"))
            upside = self._safe_float(row.get("upside_potential_%"))
            score = self._safe_float(row.get("composite_score"))

            target_text = self._safe_numeric_text(target, "N/A")
            current_text = self._safe_numeric_text(current, "N/A")
            upside_text = self._safe_numeric_text(upside, "N/A")
            score_text = self._safe_numeric_text(score, "N/A")

            report.append(
                f"{int(row['rank']):2}. {row['ticker']:6} | {rec:5} | "
                f"${current_text:>8} → ${target_text:>8} | "
                f"+{upside_text:>6}% | Score: {score_text:>6}"
            )
        report.append("")

        report.append("SUMMARY STATISTICS")
        report.append("-" * 80)
        buy_count = len(self.ranked_stocks[self.ranked_stocks["recommendation"] == "BUY"])
        hold_count = len(self.ranked_stocks[self.ranked_stocks["recommendation"] == "HOLD"])
        sell_count = len(self.ranked_stocks[self.ranked_stocks["recommendation"] == "SELL"])

        report.append(f"Total Stocks Analyzed: {len(self.ranked_stocks)}")
        report.append(f"BUY Recommendations: {buy_count}")
        report.append(f"HOLD Recommendations: {hold_count}")
        report.append(f"SELL Recommendations: {sell_count}")
        report.append(f"Average Upside Potential: {self.ranked_stocks['upside_potential_%'].mean():.2f}%")
        report.append(f"Median Upside Potential: {self.ranked_stocks['upside_potential_%'].median():.2f}%")
        report.append("")

        report.append("BEST BUY OPPORTUNITIES (BUY with >20% Upside)")
        report.append("-" * 80)
        best_buys = self.get_best_buy_opportunities(5)
        if not best_buys.empty:
            for _, row in best_buys.iterrows():
                target = self._safe_float(row.get("target_price"))
                upside = self._safe_float(row.get("upside_potential_%"))
                target_text = self._safe_numeric_text(target, "N/A")
                upside_text = self._safe_numeric_text(upside, "N/A")
                report.append(
                    f"• {row['ticker']:6} ({row['company_name'][:30]:30}) | "
                    f"Target: ${target_text} | +{upside_text}%"
                )
        else:
            report.append("No strong buy opportunities identified")
        report.append("")

        report.append("=" * 80)
        return "\n".join(report)


if __name__ == "__main__":
    print("Stock Ranker Module - Use in main.py for full functionality")