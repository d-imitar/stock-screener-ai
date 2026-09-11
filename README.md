````markdown
# 📈 AI-Powered Stock Screener

An intelligent stock screening system that combines fundamental analysis, SEC filings, and AI-powered equity research to identify investment opportunities in the NASDAQ 100.

## Overview

This stock screener automates the equity research process by:

1. **Selecting Investment Universe** - Loads NASDAQ 100 stocks with current market data
2. **Downloading Reports** - Fetches latest 10-K and 10-Q filings from SEC EDGAR
3. **Conducting Research** - Uses OpenAI GPT-4 to analyze financial reports and generate investment recommendations
4. **Ranking Opportunities** - Scores stocks based on upside potential and creates investment thesis rankings

## Features

✨ **AI-Powered Analysis**
- Uses GPT-4 to analyze SEC filings as a senior hedge fund analyst
- Generates comprehensive investment theses with specific target prices
- Evaluates bull and bear cases with quantitative metrics

📊 **Financial Data Integration**
- Real-time stock pricing via yfinance
- SEC EDGAR integration for official filings
- Financial metrics: P/E ratio, market cap, dividend yield, 52-week ranges

🎯 **Intelligent Ranking**
- Ranks stocks by upside potential (Target Price / Current Price)
- Composite scoring: 50% upside, 30% recommendation, 20% valuation
- Filters for best BUY opportunities with risk assessment

💾 **Smart Caching**
- Caches stock universe data, reports, and analyses
- Reduces API calls and improves performance
- Configurable cache expiration (default: 30 days)

📤 **Export Capabilities**
- Export rankings to CSV and JSON formats
- Comprehensive summary reports with key statistics
- Detailed investment recommendations

## Installation

### Prerequisites
- Python 3.8+
- OpenAI API key (for equity research analysis)
- Internet connection for data fetching

### Setup

1. Clone the repository:
```bash
git clone https://github.com/d-imitar/stock-screener-ai.git
cd stock-screener-ai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your_actual_api_key_here
SEC_EDGAR_USERNAME=your_email@example.com
```

## Usage

### Quick Start

Run the complete screening pipeline:

```bash
python main.py
```

This will:
- Load NASDAQ 100 stocks
- Download latest 10-K reports
- Analyze stocks using AI
- Generate rankings
- Export results to CSV and JSON

### Programmatic Usage

```python
from main import StockScreener

# Initialize screener
screener = StockScreener()

# Step 1: Get investment universe
universe = screener.step_1_get_universe(limit=50)

# Step 2: Download reports
reports = screener.step_2_download_reports(report_type="10-K")

# Step 3: Conduct research analysis
analysis = screener.step_3_conduct_research(sample_size=10)

# Step 4: Rank stocks by upside potential
rankings = screener.step_4_rank_stocks()

# Generate report
report = screener.generate_report()
print(report)

# Export results
screener.export_results(format="csv")
screener.export_results(format="json")
```

### Individual Module Usage

```python
# Get stock universe
from stock_universe import get_stock_universe
universe = get_stock_universe()

# Download SEC reports
from report_downloader import get_latest_reports
reports = get_latest_reports(["AAPL", "MSFT"], report_type="10-K")

# Analyze stocks with AI
from equity_analyzer import analyze_stock
analysis = analyze_stock(
    ticker="AAPL",
    company_name="Apple Inc.",
    report_text="10-K report content...",
    financial_data={
        "current_price": 150.0,
        "sector": "Technology",
        # ... more metrics
    }
)

# Rank stocks
from stock_ranker import StockRanker
ranker = StockRanker()
rankings = ranker.rank_stocks(analysis_results, stock_universe)
```

## Project Structure

```
stock-screener-ai/
├── main.py                    # Main orchestrator & entry point
├── stock_universe.py          # Step 1: Load NASDAQ 100 stocks
├── report_downloader.py       # Step 2: Download SEC reports
├── equity_analyzer.py         # Step 3: AI-powered analysis
├── stock_ranker.py           # Step 4: Ranking & scoring
├── config.py                 # Configuration & environment variables
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore file
├── README.md                # This file
└── data/
    ├── reports/             # Cached SEC reports
    └── cache/               # Cached analyses and rankings
```

## Configuration

Edit `config.py` or `.env` to customize:

```python
# Stock Universe Settings
NASDAQ_100_LIMIT=100              # Number of stocks to screen

# Report Settings
REPORT_CACHE_DAYS=30              # Cache expiration for reports

# Analysis Settings
ANALYSIS_MODEL="gpt-4"            # OpenAI model to use
ANALYSIS_TEMPERATURE=0.7          # Model creativity (0-1)

# SEC EDGAR
SEC_EDGAR_USERNAME="your_email@example.com"  # For rate limiting
```

## Output

The screener generates:

### Rankings CSV
```
rank,ticker,company_name,recommendation,current_price,target_price,upside_potential_%,composite_score
1,NVDA,NVIDIA Corporation,BUY,875.42,1050.00,20.0,82.15
2,MSFT,Microsoft Corporation,BUY,370.25,425.00,14.8,78.42
...
```

### Rankings JSON
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "total_stocks": 50,
  "stocks": [
    {
      "rank": 1,
      "ticker": "NVDA",
      "recommendation": "BUY",
      "current_price": 875.42,
      "target_price": 1050.00,
      "upside_potential_%": 20.0
    }
  ]
}
```

### Summary Report
```
STOCK SCREENER RANKING REPORT
Generated: 2024-01-15 10:30:45
================================================================================

TOP 10 OPPORTUNITIES (By Upside Potential)
────────────────────────────────────────────────────────────────────────────────
 1. NVDA   | BUY   | $   875.42 → $ 1050.00 | +20.00% | Score:  82.15
 2. MSFT   | BUY   | $   370.25 → $  425.00 | +14.80% | Score:  78.42
...
```

## How It Works

### Step 1: Stock Universe Selection
- Fetches NASDAQ 100 stocks using yfinance
- Retrieves current prices, market cap, P/E ratios
- Stores metadata for analysis

### Step 2: Report Download
- Uses SEC EDGAR API to find 10-K and 10-Q filings
- Downloads and caches report text
- Reduces redundant API calls

### Step 3: Equity Research Analysis
- Sends financial data + report to GPT-4
- Generates senior analyst investment thesis
- Extracts target price and recommendation
- Caches analysis (7-day expiration)

### Step 4: Stock Ranking
- Calculates upside potential: (Target Price - Current Price) / Current Price
- Composite score: 50% upside, 30% recommendation, 20% valuation
- Ranks stocks for best opportunities

## API Costs & Optimization

### OpenAI API
- ~$0.30-0.50 per stock analysis (GPT-4)
- Cache results with 7-day TTL to reduce costs

### yfinance
- Free, no authentication required

### SEC EDGAR
- Free, public API
- Requires email (configure in .env)

## Troubleshooting

### "OpenAI API Error"
- Check OPENAI_API_KEY in .env
- Verify API key has sufficient credits

### "Cache issues"
```bash
rm -rf data/cache data/reports
```

## Contributing

Contributions welcome! Areas for improvement:
- Better SEC filing parsing
- Enhanced sentiment analysis
- Technical analysis indicators
- Web UI with Streamlit

## License

MIT License - see LICENSE file for details

## Disclaimer

**This is for educational and research purposes only.** Stock analysis generated by this tool should not be considered professional investment advice. Always conduct your own due diligence before making investment decisions.

---

**Happy investing! 🚀**
````
