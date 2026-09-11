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
        self.model = model
        self.setup_model()

    def setup_model(self):
        """Initialize model-specific API config."""
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
        """Create a research prompt that forces strict JSON output."""
        sector = financial_data.get("sector", "N/A")
        industry = financial_data.get("industry", "N/A")
        current_price = financial_data.get("current_price", "N/A")
        market_cap = financial_data.get("market_cap", "N/A")
        pe_ratio = financial_data.get("pe_ratio", "N/A")
        low = financial_data.get("52_week_low", "N/A")
        high = financial_data.get("52_week_high", "N/A")
        dividend_yield = financial_data.get("dividend_yield", "N/A")
        report_excerpt = report_text[:3000]

        return f"""
You are a senior analyst at a leading hedge fund with 20+ years of experience in equity research.

Imagine that you are analyzing {company_name} ({ticker}) based on the attached files and available relevant information. Provide a concise but rigorous research brief with a clear investment recommendation and a 12-month target price.

Use the following financial context:
- Company: {company_name} ({ticker})
- Sector: {sector}
- Industry: {industry}
- Current Price: ${current_price}
- Market Cap: ${market_cap}
- P/E Ratio: {pe_ratio}
- 52-week range: ${low} to ${high}
- Dividend Yield: {dividend_yield}

Recent report excerpt:
{report_excerpt}

Return ONLY valid JSON in this exact schema:
{{
  "recommendation": "BUY",
  "target_price": 123.45,
  "upside_potential": 18.5,
  "summary": "brief explanation"
}}

Rules:
- Do not return null.
- Always provide a numeric target_price and numeric upside_potential.
- If uncertain, still provide your best estimate.
- recommendation must be one of BUY, HOLD, or SELL.
- Do not include markdown fences, comments, or extra text outside the JSON.
""".strip()

    @staticmethod
    def _extract_json_from_text(text: str) -> Optional[Dict]:
        """Extract a JSON object from an LLM response."""
        if text is None:
            return None

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    return None
            return None

    def analyze_with_gemini(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Call Gemini API and parse strict JSON output."""
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        model_name = os.getenv(
            "GEMINI_MODEL_NAME",
            self.gemini_model_name if hasattr(self, "gemini_model_name") else "gemini-3.6-flash",
        )

        if not api_key:
            return {"ticker": ticker, "error": "GOOGLE_API_KEY not set", "model": model_name}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2000,
                "responseMimeType": "application/json",
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            print("DEBUG status:", response.status_code)
            print("DEBUG headers:", response.headers.get("Content-Type"))
            print("DEBUG body:", response.text[:4000])

            response.raise_for_status()
            result = response.json()

            if "error" in result:
                return {
                    "ticker": ticker,
                    "error": result["error"].get("message", "Unknown Gemini error"),
                    "model": model_name,
                }

            candidates = result.get("candidates", [])
            if not candidates:
                return {"ticker": ticker, "error": "No Gemini candidate returned", "model": model_name}

            text = candidates[0]["content"]["parts"][0].get("text", "")
            if not text:
                return {"ticker": ticker, "error": "Gemini response had no text", "model": model_name}

            parsed = self._extract_json_from_text(text)
            if not isinstance(parsed, dict):
                return {
                    "ticker": ticker,
                    "error": f"Gemini response was not valid JSON: {text[:500]}",
                    "model": model_name,
                }

            recommendation = parsed.get("recommendation", "HOLD")
            target_price = parsed.get("target_price")
            upside_potential = parsed.get("upside_potential")

            return {
                "ticker": ticker,
                "company_name": company_name,
                "recommendation": str(recommendation).upper(),
                "target_price": float(target_price) if target_price is not None else None,
                "upside_potential": float(upside_potential) if upside_potential is not None else None,
                "summary": parsed.get("summary", ""),
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as exc:
            print(f"Gemini call failed for {ticker}: {exc}")
            return {"ticker": ticker, "error": str(exc), "model": model_name}

    def analyze_with_openai(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze using OpenAI ChatCompletion API."""
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert equity research analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=2000,
            )

            analysis_text = response.choices[0].message.content
            parsed = self._extract_json_from_text(analysis_text)

            if not isinstance(parsed, dict):
                return {"ticker": ticker, "error": "OpenAI response was not valid JSON", "model": "gpt-4-turbo"}

            recommendation = parsed.get("recommendation")
            target_price = parsed.get("target_price")
            upside_potential = parsed.get("upside_potential")

            return {
                "ticker": ticker,
                "company_name": company_name,
                "recommendation": recommendation.upper() if isinstance(recommendation, str) else "HOLD",
                "target_price": float(target_price) if target_price is not None else None,
                "upside_potential": float(upside_potential) if upside_potential is not None else None,
                "summary": parsed.get("summary", ""),
                "model": "gpt-4-turbo",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            return {"ticker": ticker, "error": str(exc), "model": "gpt-4-turbo"}

    def analyze_with_claude(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze using Anthropic Claude."""
        if not hasattr(self, "client"):
            return {"ticker": ticker, "error": "Claude client not initialized", "model": "claude-3-haiku"}

        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            text = message.content[0].text
            parsed = self._extract_json_from_text(text)

            if not isinstance(parsed, dict):
                return {"ticker": ticker, "error": "Claude response was not valid JSON", "model": "claude-3-haiku"}

            recommendation = parsed.get("recommendation")
            target_price = parsed.get("target_price")
            upside_potential = parsed.get("upside_potential")

            return {
                "ticker": ticker,
                "company_name": company_name,
                "recommendation": recommendation.upper() if isinstance(recommendation, str) else "HOLD",
                "target_price": float(target_price) if target_price is not None else None,
                "upside_potential": float(upside_potential) if upside_potential is not None else None,
                "summary": parsed.get("summary", ""),
                "model": "claude-3-haiku",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            return {"ticker": ticker, "error": str(exc), "model": "claude-3-haiku"}

    def analyze_with_moonshot(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze using Moonshot API."""
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        api_key = os.getenv("MOONSHOT_API_KEY")

        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "moonshot-v1-8k",
                "messages": [
                    {"role": "system", "content": "You are an expert equity research analyst."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }

            response = requests.post("https://api.moonshot.cn/v1/chat/completions", headers=headers, json=payload, timeout=30)
            result = response.json()

            if "error" in result:
                return {"ticker": ticker, "error": result["error"].get("message", "Unknown error"), "model": "moonshot"}

            text = result["choices"][0]["message"]["content"]
            parsed = self._extract_json_from_text(text)

            if not isinstance(parsed, dict):
                return {"ticker": ticker, "error": "Moonshot response was not valid JSON", "model": "moonshot"}

            recommendation = parsed.get("recommendation")
            target_price = parsed.get("target_price")
            upside_potential = parsed.get("upside_potential")

            return {
                "ticker": ticker,
                "company_name": company_name,
                "recommendation": recommendation.upper() if isinstance(recommendation, str) else "HOLD",
                "target_price": float(target_price) if target_price is not None else None,
                "upside_potential": float(upside_potential) if upside_potential is not None else None,
                "summary": parsed.get("summary", ""),
                "model": "moonshot",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            return {"ticker": ticker, "error": str(exc), "model": "moonshot"}

    def analyze_with_baichuan(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze using Baichuan API."""
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        api_key = os.getenv("BAICHUAN_API_KEY")

        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "Baichuan4-Finance",
                "messages": [
                    {"role": "system", "content": "You are an expert equity research analyst."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }

            response = requests.post("https://api.baichuan-ai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            result = response.json()

            if "error" in result:
                return {"ticker": ticker, "error": result["error"].get("message", "Unknown error"), "model": "baichuan-4-finance"}

            text = result["choices"][0]["message"]["content"]
            parsed = self._extract_json_from_text(text)

            if not isinstance(parsed, dict):
                return {"ticker": ticker, "error": "Baichuan response was not valid JSON", "model": "baichuan-4-finance"}

            recommendation = parsed.get("recommendation")
            target_price = parsed.get("target_price")
            upside_potential = parsed.get("upside_potential")

            return {
                "ticker": ticker,
                "company_name": company_name,
                "recommendation": recommendation.upper() if isinstance(recommendation, str) else "HOLD",
                "target_price": float(target_price) if target_price is not None else None,
                "upside_potential": float(upside_potential) if upside_potential is not None else None,
                "summary": parsed.get("summary", ""),
                "model": "baichuan-4-finance",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            return {"ticker": ticker, "error": str(exc), "model": "baichuan-4-finance"}

    def analyze_stock(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze a single stock using the selected model."""
        cache_file = os.path.join(CACHE_DIR, f"research_{ticker}_{self.model}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as handle:
                    cached = json.load(handle)
                if "timestamp" in cached:
                    if (datetime.now() - datetime.fromisoformat(cached["timestamp"])).days < 7:
                        print(f"Loading cached analysis for {ticker} ({self.model})")
                        return cached
            except Exception:
                pass

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

        if "error" not in result:
            if result.get("recommendation") is None:
                result["recommendation"] = "HOLD"

        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, default=str)

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


def analyze_stock(
    ticker: str,
    company_name: str,
    report_text: str,
    financial_data: Dict,
    model: str = "gemini-3.6-flash",
) -> Dict:
    analyzer = MultiModelAnalyzer(model=model)
    return analyzer.analyze_stock(ticker, company_name, report_text, financial_data)


def analyze_multiple_stocks(stocks: Dict, model: str = "gemini-3.6-flash") -> Dict[str, Dict]:
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
