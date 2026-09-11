"""Module for AI-powered equity research analysis supporting multiple models."""

import json
import os
import re
from datetime import datetime
from typing import Dict, Literal, Optional

import openai
import requests

from config import CACHE_DIR

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None


class MultiModelAnalyzer:
    """Supports multiple AI models for equity research analysis."""

    def __init__(
        self,
        model: Literal[
            "gpt-4-turbo",
            "claude-3-haiku",
            "moonshot",
            "baichuan-4-finance",
            "gemini-2.5-flash",
            "gemini-3.6-flash",
        ] = "gemini-3.6-flash",
    ):
        """Initialize analyzer with the specified model."""
        self.model = model
        self.setup_model()

    def setup_model(self):
        """Set up the selected model."""
        if self.model == "gpt-4-turbo":
            openai.api_key = os.getenv("OPENAI_API_KEY")
        elif self.model == "claude-3-haiku":
            if anthropic is None:
                raise ImportError("anthropic package required. Install with: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif self.model == "moonshot":
            if not os.getenv("MOONSHOT_API_KEY"):
                raise ValueError("MOONSHOT_API_KEY not set in environment")
        elif self.model == "baichuan-4-finance":
            if not os.getenv("BAICHUAN_API_KEY"):
                raise ValueError("BAICHUAN_API_KEY not set in environment")
        elif self.model.startswith("gemini"):
            if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set in environment")
            self.gemini_model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash")

    def create_research_prompt(
        self,
        ticker: str,
        company_name: str,
        report_text: str,
        financial_data: Dict,
    ) -> str:
        """Create a comprehensive research prompt for equity analysis."""
        prompt = f"""You are a senior analyst at a leading hedge fund with 20+ years of experience in equity research.

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

1. **INVESTMENT THESIS** (2-3 paragraphs)
2. **FINANCIAL ANALYSIS** (2-3 paragraphs)
3. **RISKS & CHALLENGES** (2-3 paragraphs)
4. **VALUATION ANALYSIS** (2-3 paragraphs)
5. **INVESTMENT RECOMMENDATION**
   - Rating: BUY / HOLD / SELL
   - Target Price (12-month): $XX.XX
   - Upside/Downside Potential: XX%
   - Key Catalysts (next 12 months)
6. **BULL & BEAR CASE**

Format your response in clear sections with specific numbers and actionable insights.
"""
        return prompt

    def analyze_with_gemini(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze stock using the Gemini API via the REST endpoint."""
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL_NAME", self.gemini_model_name if hasattr(self, "gemini_model_name") else "gemini-3.6-flash")

        if not api_key:
            return {"ticker": ticker, "error": "GOOGLE_API_KEY not set", "model": model_name}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2000,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            print("Gemini status:", response.status_code)
            print("Gemini content-type:", response.headers.get("Content-Type"))
            print("Gemini body preview:", response.text[:500])

            response.raise_for_status()
            result = response.json()

            if "error" in result:
                return {"ticker": ticker, "error": result["error"].get("message", "Unknown Gemini error"), "model": model_name}

            candidates = result.get("candidates", [])
            if not candidates:
                return {"ticker": ticker, "error": "No Gemini candidate returned", "model": model_name}

            analysis_text = candidates[0]["content"]["parts"][0]["text"]
            return {
                "ticker": ticker,
                "company_name": company_name,
                "analysis": analysis_text,
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            print(f"Gemini call failed for {ticker}: {exc}")
            return {"ticker": ticker, "error": str(exc), "model": model_name}

    def analyze_with_openai(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze stock using OpenAI GPT-4 Turbo."""
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
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
        except Exception as exc:
            return {"ticker": ticker, "error": str(exc), "model": "gpt-4-turbo"}

    def analyze_with_claude(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze stock using Anthropic Claude 3 Haiku."""
        if not hasattr(self, "client"):
            return {"ticker": ticker, "error": "Claude client not initialized", "model": "claude-3-haiku"}

        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            analysis_text = message.content[0].text
            return {
                "ticker": ticker,
                "company_name": company_name,
                "analysis": analysis_text,
                "model": "claude-3-haiku",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            return {"ticker": ticker, "error": str(exc), "model": "claude-3-haiku"}

    def analyze_with_moonshot(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze stock using Moonshot/Kimi."""
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        api_key = os.getenv("MOONSHOT_API_KEY")

        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {
                "model": "moonshot-v1-8k",
                "messages": [
                    {"role": "system", "content": "You are an expert equity research analyst."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            }

            response = requests.post("https://api.moonshot.cn/v1/chat/completions", headers=headers, json=data, timeout=30)
            result = response.json()

            if "error" in result:
                return {"ticker": ticker, "error": result["error"].get("message", "Unknown error"), "model": "moonshot"}

            analysis_text = result["choices"][0]["message"]["content"]
            return {
                "ticker": ticker,
                "company_name": company_name,
                "analysis": analysis_text,
                "model": "moonshot",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            return {"ticker": ticker, "error": str(exc), "model": "moonshot"}

    def analyze_with_baichuan(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze stock using Baichuan 4 Finance."""
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        api_key = os.getenv("BAICHUAN_API_KEY")

        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {
                "model": "Baichuan4-Finance",
                "messages": [
                    {"role": "system", "content": "You are an expert equity research analyst."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            }

            response = requests.post("https://api.baichuan-ai.com/v1/chat/completions", headers=headers, json=data, timeout=30)
            result = response.json()

            if "error" in result:
                return {"ticker": ticker, "error": result["error"].get("message", "Unknown error"), "model": "baichuan-4-finance"}

            analysis_text = result["choices"][0]["message"]["content"]
            return {
                "ticker": ticker,
                "company_name": company_name,
                "analysis": analysis_text,
                "model": "baichuan-4-finance",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            return {"ticker": ticker, "error": str(exc), "model": "baichuan-4-finance"}

    def analyze_stock(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Conduct AI-powered equity research analysis on a stock."""
        cache_file = os.path.join(CACHE_DIR, f"research_{ticker}_{self.model}.json")

        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as handle:
                cached = json.load(handle)
                if (datetime.now() - datetime.fromisoformat(cached["timestamp"])) .days < 7:
                    print(f"Loading cached analysis for {ticker} ({self.model})")
                    return cached

        print(f"Analyzing {ticker} with {self.model}...")

        if self.model == "gpt-4-turbo":
            result = self.analyze_with_openai(ticker, company_name, report_text, financial_data)
        elif self.model == "claude-3-haiku":
            result = self.analyze_with_claude(ticker, company_name, report_text, financial_data)
        elif self.model == "moonshot":
            result = self.analyze_with_moonshot(ticker, company_name, report_text, financial_data)
        elif self.model == "baichuan-4-finance":
            result = self.analyze_with_baichuan(ticker, company_name, report_text, financial_data)
        elif self.model.startswith("gemini"):
            result = self.analyze_with_gemini(ticker, company_name, report_text, financial_data)
        else:
            return {"ticker": ticker, "error": f"Unknown model: {self.model}"}

        if "error" not in result and "analysis" in result:
            analysis_text = result["analysis"]
            result["target_price"] = self._extract_target_price(analysis_text)
            result["recommendation"] = self._extract_recommendation(analysis_text)
            result["current_price"] = financial_data.get("current_price")

            if result["target_price"] and result["current_price"]:
                result["upside_potential"] = ((result["target_price"] - result["current_price"]) / result["current_price"]) * 100

        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, default=str)

        return result

    @staticmethod
    def _extract_target_price(analysis_text: str) -> Optional[float]:
        """Extract target price from analysis text."""
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
        """Extract investment recommendation from analysis text."""
        ratings = ["BUY", "HOLD", "SELL"]
        for rating in ratings:
            if re.search(rf"[^\w]{rating}[^\w]|^{rating}[^\w]|[^\w]{rating}$", analysis_text, re.IGNORECASE):
                return rating.upper()
        return None


def analyze_stock(
    ticker: str,
    company_name: str,
    report_text: str,
    financial_data: Dict,
    model: str = "gemini-3.6-flash",
) -> Dict:
    """Analyze a single stock with the specified model."""
    analyzer = MultiModelAnalyzer(model=model)
    return analyzer.analyze_stock(ticker, company_name, report_text, financial_data)


def analyze_multiple_stocks(stocks: Dict, model: str = "gemini-3.6-flash") -> Dict[str, Dict]:
    """Analyze multiple stocks with the specified model."""
    analyzer = MultiModelAnalyzer(model=model)
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
    print("  - gemini-3.6-flash (requires GOOGLE_API_KEY / GEMINI_API_KEY)")
