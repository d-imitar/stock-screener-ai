"""Module for AI-powered equity research analysis supporting multiple models."""

import json
import os
import re
from datetime import datetime
from typing import Dict, Literal, Optional

from config import ANALYSIS_MODEL, CACHE_DIR, GEMINI_MODEL_NAME

# OpenAI SDK
try:
    import openai
except ImportError:  # pragma: no cover - optional dependency
    openai = None

# Claude support
try:
    import anthropic
except ImportError:  # pragma: no cover - optional dependency
    anthropic = None

# Gemini support
try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - optional dependency
    genai = None

# For Moonshot/Baichuan support
try:
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None


class MultiModelAnalyzer:
    """Supports multiple AI models for equity research analysis."""

    def __init__(
        self,
        model: Optional[Literal["gpt-4-turbo", "claude-3-haiku", "moonshot", "baichuan-4-finance", "gemini-3.7-flash"]] = None,
        demo_only: bool = False,
    ):
        self.model = model or ANALYSIS_MODEL
        self.demo_only = demo_only
        self.client = None
        self.api_key = None
        self.setup_model()

    def setup_model(self):
        if self.model == "gpt-4-turbo":
            self.api_key = os.getenv("OPENAI_API_KEY")
            if self.api_key and not self.demo_only and openai is not None:
                self.client = openai.OpenAI(api_key=self.api_key)
            else:
                self.client = None
        elif self.model == "claude-3-haiku":
            if anthropic is None:
                raise ImportError("anthropic package required. Install with: pip install anthropic")
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
            self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key and not self.demo_only else None
        elif self.model == "moonshot":
            self.api_key = os.getenv("MOONSHOT_API_KEY")
        elif self.model == "baichuan-4-finance":
            self.api_key = os.getenv("BAICHUAN_API_KEY")
        elif self.model == "gemini-3.7-flash":
            if genai is None:
                raise ImportError("google-generativeai package required. Install with: pip install google-generativeai")
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if self.api_key and not self.demo_only:
                genai.configure(api_key=self.api_key)

    def _should_use_demo_fallback(self) -> bool:
        return self.demo_only or not bool(self.api_key or self.client)

    def _generate_demo_result(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        current_price = float(financial_data.get("current_price") or 0.0)
        if current_price <= 0:
            current_price = 100.0

        target_price = current_price * 1.22
        upside = ((target_price - current_price) / current_price) * 100
        recommendation = "BUY" if upside > 20 else "HOLD" if upside > 5 else "SELL"

        analysis_text = (
            f"INVESTMENT THESIS\n"
            f"{company_name} ({ticker}) appears attractively positioned in its sector, with stable competitive advantages and an improving operating backdrop. "
            f"The business benefits from durable demand, pricing power, and a balanced cost structure.\n\n"
            f"VALUATION ANALYSIS\n"
            f"Current price: ${current_price:.2f}. Target price: ${target_price:.2f}. Upside potential: {upside:.2f}%.\n"
            f"Rating: {recommendation}.\n\n"
            f"Key Catalysts: strong operating leverage, margin expansion, and continued demand from the core customer base.\n\n"
            f"Risk Factors: macro slowdown, competition, and execution risk."
        )

        return {
            "ticker": ticker,
            "company_name": company_name,
            "analysis": analysis_text,
            "model": self.model,
            "timestamp": datetime.now().isoformat(),
            "target_price": target_price,
            "recommendation": recommendation,
            "current_price": current_price,
            "upside_potential": upside,
            "demo_mode": True,
        }

    def create_research_prompt(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> str:
        return f"""You are a senior analyst at a leading hedge fund with 20+ years of experience in equity research.

Analyze {company_name} ({ticker}) based on the recent financial report and available information.

COMPANY: {company_name} ({ticker})
SECTOR: {financial_data.get('sector', 'N/A')}
INDUSTRY: {financial_data.get('industry', 'N/A')}

CURRENT FINANCIAL METRICS:
- Current Price: ${financial_data.get('current_price', 'N/A')}
- Market Cap: ${financial_data.get('market_cap', 'N/A')}
- P/E Ratio: {financial_data.get('pe_ratio', 'N/A')}
- 52-Week Range: ${financial_data.get('52_week_low', 'N/A')} - ${financial_data.get('52_week_high', 'N/A')}
- Dividend Yield: {financial_data.get('dividend_yield', 'N/A')}

RECENT FINANCIAL REPORT EXCERPT:
{report_text[:3000]}

Please provide a comprehensive equity research report including:

1. **INVESTMENT THESIS**
2. **FINANCIAL ANALYSIS**
3. **RISKS & CHALLENGES**
4. **VALUATION ANALYSIS**
5. **INVESTMENT RECOMMENDATION**
    - Rating: BUY / HOLD / SELL
    - Target Price (12-month): $XX.XX
    - Upside/Downside Potential: XX%
6. **BULL & BEAR CASE**

Format your response in clear sections with specific numbers and actionable insights.
"""

    def analyze_with_gemini(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        if self._should_use_demo_fallback():
            return self._generate_demo_result(ticker, company_name, report_text, financial_data)

        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        try:
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            response = model.generate_content(prompt)
            text = response.text if hasattr(response, "text") else str(response)
            return {
                "ticker": ticker,
                "company_name": company_name,
                "analysis": text,
                "model": "gemini-3.7-flash",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"ticker": ticker, "error": str(e), "model": "gemini-3.7-flash"}

    def analyze_with_openai(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        if self._should_use_demo_fallback():
            return self._generate_demo_result(ticker, company_name, report_text, financial_data)

        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert equity research analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            analysis_text = response.choices[0].message.content
            return {
                "ticker": ticker,
                "company_name": company_name,
                "analysis": analysis_text,
                "model": "gpt-4-turbo",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"ticker": ticker, "error": str(e), "model": "gpt-4-turbo"}

    def analyze_stock(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        if self._should_use_demo_fallback():
            result = self._generate_demo_result(ticker, company_name, report_text, financial_data)
            os.makedirs(CACHE_DIR, exist_ok=True)
            cache_file = os.path.join(CACHE_DIR, f"research_{ticker}_{self.model}.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, default=str)
            return result

        cache_file = os.path.join(CACHE_DIR, f"research_{ticker}_{self.model}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if "timestamp" in cached and (datetime.now() - datetime.fromisoformat(cached["timestamp"])).days < 7:
                    print(f"Loading cached analysis for {ticker} ({self.model})")
                    return cached

        print(f"Analyzing {ticker} with {self.model}...")

        if self.model == "gemini-3.7-flash":
            result = self.analyze_with_gemini(ticker, company_name, report_text, financial_data)
        elif self.model == "gpt-4-turbo":
            result = self.analyze_with_openai(ticker, company_name, report_text, financial_data)
        elif self.model == "claude-3-haiku":
            result = self.analyze_with_claude(ticker, company_name, report_text, financial_data)
        elif self.model == "moonshot":
            result = self.analyze_with_moonshot(ticker, company_name, report_text, financial_data)
        elif self.model == "baichuan-4-finance":
            result = self.analyze_with_baichuan(ticker, company_name, report_text, financial_data)
        else:
            return {"ticker": ticker, "error": f"Unknown model: {self.model}"}

        if "error" not in result and "analysis" in result:
            analysis_text = result["analysis"]
            result["target_price"] = self._extract_target_price(analysis_text)
            result["recommendation"] = self._extract_recommendation(analysis_text)
            result["current_price"] = financial_data.get("current_price")
            if result["target_price"] and result["current_price"]:
                result["upside_potential"] = ((result["target_price"] - result["current_price"]) / result["current_price"]) * 100

        if "target_price" not in result and not result.get("error"):
            current_price = float(financial_data.get("current_price") or 0.0)
            if current_price > 0:
                result["target_price"] = current_price * 1.20
                result["recommendation"] = result.get("recommendation") or "BUY"
                result["upside_potential"] = ((result["target_price"] - current_price) / current_price) * 100

        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)

        return result

    @staticmethod
    def _extract_target_price(analysis_text: str) -> Optional[float]:
        patterns = [
            r"Target Price[:\s]+\$?([\d.]+)",
            r"Price Target[:\s]+\$?([\d.]+)",
            r"12-month target[:\s]+\$?([\d.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None

    @staticmethod
    def _extract_recommendation(analysis_text: str) -> Optional[str]:
        ratings = ["BUY", "HOLD", "SELL"]
        for rating in ratings:
            if re.search(rf"[^\w]{rating}[^\w]|^{rating}[^\w]|[^\w]{rating}$", analysis_text, re.IGNORECASE):
                return rating.upper()
        return None


def analyze_stock(ticker: str, company_name: str, report_text: str, financial_data: Dict, model: Optional[str] = None, demo_only: bool = False) -> Dict:
    analyzer = MultiModelAnalyzer(model=model or ANALYSIS_MODEL, demo_only=demo_only)
    return analyzer.analyze_stock(ticker, company_name, report_text, financial_data)


def analyze_multiple_stocks(stocks: Dict, model: Optional[str] = None, demo_only: bool = False) -> Dict[str, Dict]:
    analyzer = MultiModelAnalyzer(model=model or ANALYSIS_MODEL, demo_only=demo_only)
    results = {}
    for ticker, stock_data in stocks.items():
        result = analyzer.analyze_stock(
            ticker=ticker,
            company_name=stock_data.get("company_name"),
            report_text=stock_data.get("report_text", ""),
            financial_data=stock_data.get("financial_data", {}),
        )
        results[ticker] = result
    return results


if __name__ == "__main__":
    print("Multi-model equity analyzer loaded")
    print("Supported models:")
    print("  - gpt-4-turbo (requires OPENAI_API_KEY)")
    print("  - claude-3-haiku (requires ANTHROPIC_API_KEY)")
    print("  - moonshot (requires MOONSHOT_API_KEY)")
    print("  - baichuan-4-finance (requires BAICHUAN_API_KEY)")
    print("  - gemini-3.7-flash (requires GOOGLE_API_KEY)")
    print("  - demo fallback (automatic when no API key is configured)")
