"""Module for AI-powered equity research analysis using OpenAI."""

import os
import json
from typing import Dict, Optional
import openai
from config import OPENAI_API_KEY, ANALYSIS_MODEL, ANALYSIS_TEMPERATURE, CACHE_DIR
from datetime import datetime

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY


def create_research_prompt(ticker: str, company_name: str, report_text: str, financial_data: Dict) -> str:
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
{report_text[:3000]}  # Limit to first 3000 characters for token efficiency

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


def analyze_stock(ticker: str, company_name: str, report_text: str, financial_data: Dict) -> Dict:
    """Conduct AI-powered equity research analysis on a stock.
    
    Args:
        ticker: Stock ticker symbol
        company_name: Company name
        report_text: Latest 10-K/10-Q report text
        financial_data: Dictionary with current financial metrics
        
    Returns:
        Dictionary containing research analysis and recommendation
    """
    cache_file = os.path.join(CACHE_DIR, f"research_{ticker}.json")
    
    # Check cache first
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cached = json.load(f)
            if (datetime.now() - datetime.fromisoformat(cached['timestamp'])).days < 7:
                print(f"Loading cached analysis for {ticker}")
                return cached
    
    try:
        prompt = create_research_prompt(ticker, company_name, report_text, financial_data)
        
        print(f"Analyzing {ticker} with OpenAI...")
        
        response = openai.ChatCompletion.create(
            model=ANALYSIS_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert equity research analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=ANALYSIS_TEMPERATURE,
            max_tokens=2000
        )
        
        analysis_text = response.choices[0].message.content
        
        # Parse the response to extract key metrics
        research_result = {
            "ticker": ticker,
            "company_name": company_name,
            "analysis": analysis_text,
            "timestamp": datetime.now().isoformat(),
            "model": ANALYSIS_MODEL,
            "current_price": financial_data.get('current_price'),
            "target_price": extract_target_price(analysis_text),
            "recommendation": extract_recommendation(analysis_text),
        }
        
        # Calculate upside potential
        if research_result["target_price"] and research_result["current_price"]:
            research_result["upside_potential"] = (
                (research_result["target_price"] - research_result["current_price"]) 
                / research_result["current_price"] * 100
            )
        
        # Cache the result
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(research_result, f, indent=2, default=str)
        
        return research_result
        
    except Exception as e:
        print(f"Error analyzing {ticker}: {str(e)}")
        return {
            "ticker": ticker,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def extract_target_price(analysis_text: str) -> Optional[float]:
    """Extract target price from analysis text.
    
    Args:
        analysis_text: Analysis text from OpenAI
        
    Returns:
        Target price as float or None
    """
    import re
    
    # Look for patterns like "Target Price: $XX.XX"
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


def extract_recommendation(analysis_text: str) -> Optional[str]:
    """Extract investment recommendation from analysis text.
    
    Args:
        analysis_text: Analysis text from OpenAI
        
    Returns:
        Recommendation (BUY, HOLD, SELL) or None
    """
    import re
    
    # Look for rating/recommendation
    ratings = ['BUY', 'HOLD', 'SELL']
    
    for rating in ratings:
        if re.search(rf'[^\w]{rating}[^\w]|^{rating}[^\w]|[^\w]{rating}$', analysis_text, re.IGNORECASE):
            return rating.upper()
    
    return None


def analyze_multiple_stocks(stocks: Dict) -> Dict[str, Dict]:
    """Analyze multiple stocks and return results.
    
    Args:
        stocks: Dictionary with ticker as key and stock data as value
                Expected format: {"ticker": {"company_name": "...", "report_text": "...", "financial_data": {...}}}
        
    Returns:
        Dictionary of analysis results keyed by ticker
    """
    results = {}
    
    for ticker, stock_data in stocks.items():
        result = analyze_stock(
            ticker=ticker,
            company_name=stock_data.get("company_name"),
            report_text=stock_data.get("report_text", ""),
            financial_data=stock_data.get("financial_data", {})
        )
        results[ticker] = result
    
    return results


if __name__ == "__main__":
    # Example usage
    test_data = {
        "AAPL": {
            "company_name": "Apple Inc.",
            "report_text": "Sample 10-K report text...",
            "financial_data": {
                "current_price": 150.00,
                "market_cap": 2300000000000,
                "pe_ratio": 25.5,
                "52_week_low": 130.0,
                "52_week_high": 165.0,
                "dividend_yield": 0.005,
                "sector": "Technology",
                "industry": "Consumer Electronics"
            }
        }
    }
    
    results = analyze_multiple_stocks(test_data)
    print(json.dumps(results, indent=2, default=str))
