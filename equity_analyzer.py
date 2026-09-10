"""Module for AI-powered equity research analysis supporting multiple models."""

import os
import json
import re
from typing import Dict, Optional, Literal
from datetime import datetime
from config import CACHE_DIR

# Model imports
import openai

# For Claude 3 Haiku support
try:
    import anthropic
except ImportError:
    anthropic = None

# For Moonshot support
try:
    import requests
except ImportError:
    requests = None


class MultiModelAnalyzer:
    """Supports multiple AI models for equity research analysis."""
    
    def __init__(self, model: Literal["gpt-4-turbo", "claude-3-haiku", "moonshot", "baichuan-4-finance"] = "gpt-4-turbo"):
        """Initialize analyzer with specified model.
        
        Args:
            model: Model to use for analysis
        """
        self.model = model
        self.setup_model()
    
    def setup_model(self):
        """Setup the selected model."""
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
    
    def create_research_prompt(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> str:
        """Create a comprehensive research prompt for equity analysis.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            report_text: Latest 10-K/10-Q report text
            financial_data: Dictionary with current financial metrics
            
        Returns:
            Formatted prompt for equity research
        """
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
   - Key investment drivers
   - Competitive advantages/disadvantages
   - Market opportunity

2. **FINANCIAL ANALYSIS** (2-3 paragraphs)
   - Revenue growth trends
   - Profitability metrics
   - Cash flow analysis
   - Balance sheet strength

3. **RISKS & CHALLENGES** (2-3 paragraphs)
   - Key downside risks
   - Competitive threats
   - Regulatory/macro concerns

4. **VALUATION ANALYSIS** (2-3 paragraphs)
   - Current valuation metrics
   - Peer comparison
   - Intrinsic value estimate

5. **INVESTMENT RECOMMENDATION**
   - Rating: BUY / HOLD / SELL
   - Target Price (12-month): $XX.XX
   - Upside/Downside Potential: XX%
   - Key Catalysts (next 12 months)

6. **BULL & BEAR CASE** (1-2 paragraphs each)
   - Bull case: Why it could outperform
   - Bear case: Why it could underperform

Format your response in clear sections with specific numbers and actionable insights.
"""
        return prompt
    
    def analyze_with_openai(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze stock using OpenAI GPT-4 Turbo.
        
        Args:
            ticker: Stock ticker
            company_name: Company name
            report_text: Report text
            financial_data: Financial data
            
        Returns:
            Analysis result
        """
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert equity research analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
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
    
    def analyze_with_claude(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze stock using Anthropic Claude 3 Haiku.
        
        Args:
            ticker: Stock ticker
            company_name: Company name
            report_text: Report text
            financial_data: Financial data
            
        Returns:
            Analysis result
        """
        if not self.client:
            return {"ticker": ticker, "error": "Claude client not initialized", "model": "claude-3-haiku"}
        
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        
        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis_text = message.content[0].text
            
            return {
                "ticker": ticker,
                "company_name": company_name,
                "analysis": analysis_text,
                "model": "claude-3-haiku",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"ticker": ticker, "error": str(e), "model": "claude-3-haiku"}
    
    def analyze_with_moonshot(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze stock using Moonshot/Kimi.
        
        Args:
            ticker: Stock ticker
            company_name: Company name
            report_text: Report text
            financial_data: Financial data
            
        Returns:
            Analysis result
        """
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        api_key = os.getenv("MOONSHOT_API_KEY")
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "moonshot-v1-8k",
                "messages": [
                    {"role": "system", "content": "You are an expert equity research analyst."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
            }
            
            response = requests.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
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
        except Exception as e:
            return {"ticker": ticker, "error": str(e), "model": "moonshot"}
    
    def analyze_with_baichuan(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Analyze stock using Baichuan 4 Finance.
        
        Args:
            ticker: Stock ticker
            company_name: Company name
            report_text: Report text
            financial_data: Financial data
            
        Returns:
            Analysis result
        """
        prompt = self.create_research_prompt(ticker, company_name, report_text, financial_data)
        api_key = os.getenv("BAICHUAN_API_KEY")
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "Baichuan4-Finance",
                "messages": [
                    {"role": "system", "content": "You are an expert equity research analyst."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
            }
            
            response = requests.post(
                "https://api.baichuan-ai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
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
        except Exception as e:
            return {"ticker": ticker, "error": str(e), "model": "baichuan-4-finance"}
    
    def analyze_stock(self, ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
        """Conduct AI-powered equity research analysis on a stock.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            report_text: Latest 10-K/10-Q report text
            financial_data: Dictionary with current financial metrics
            
        Returns:
            Dictionary containing research analysis and recommendation
        """
        cache_file = os.path.join(CACHE_DIR, f"research_{ticker}_{self.model}.json")
        
        # Check cache first
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                if (datetime.now() - datetime.fromisoformat(cached['timestamp'])).days < 7:
                    print(f"Loading cached analysis for {ticker} ({self.model})")
                    return cached
        
        print(f"Analyzing {ticker} with {self.model}...")
        
        # Route to appropriate model
        if self.model == "gpt-4-turbo":
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
            # Extract metrics
            analysis_text = result["analysis"]
            result["target_price"] = self._extract_target_price(analysis_text)
            result["recommendation"] = self._extract_recommendation(analysis_text)
            result["current_price"] = financial_data.get('current_price')
            
            # Calculate upside potential
            if result["target_price"] and result["current_price"]:
                result["upside_potential"] = (
                    (result["target_price"] - result["current_price"]) 
                    / result["current_price"] * 100
                )
        
        # Cache the result
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        return result
    
    @staticmethod
    def _extract_target_price(analysis_text: str) -> Optional[float]:
        """Extract target price from analysis text."""
        patterns = [
            r'Target Price[:\s]+\$?([\d.]+)',
            r'Price Target[:\s]+\$?([\d.]+)',
            r'12-month target[:\s]+\$?([\d.]+)',
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
        ratings = ['BUY', 'HOLD', 'SELL']
        
        for rating in ratings:
            if re.search(rf'[^\w]{rating}[^\w]|^{rating}[^\w]|[^\w]{rating}$', analysis_text, re.IGNORECASE):
                return rating.upper()
        
        return None


# Backward compatibility functions
def analyze_stock(ticker: str, company_name: str, report_text: str, financial_data: Dict, 
                 model: str = "gpt-4-turbo") -> Dict:
    """Analyze a single stock with specified model."""
    analyzer = MultiModelAnalyzer(model=model)
    return analyzer.analyze_stock(ticker, company_name, report_text, financial_data)


def analyze_multiple_stocks(stocks: Dict, model: str = "gpt-4-turbo") -> Dict[str, Dict]:
    """Analyze multiple stocks with specified model."""
    analyzer = MultiModelAnalyzer(model=model)
    results = {}
    
    for ticker, stock_data in stocks.items():
        result = analyzer.analyze_stock(
            ticker=ticker,
            company_name=stock_data.get("company_name"),
            report_text=stock_data.get("report_text", ""),
            financial_data=stock_data.get("financial_data", {})
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
