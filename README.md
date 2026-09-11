````markdown
# 📈 AI-Powered Stock Screener

An intelligent stock screening system that combines fundamental analysis, SEC filings, and AI-powered equity research to identify investment opportunities in the NASDAQ 100.

## Overview

This stock screener automates the equity research process by:

1. Selecting Investment Universe - Loads NASDAQ 100 stocks with current market data
2. Downloading Reports - Fetches latest 10-K and 10-Q filings from SEC EDGAR
3. Conducting Research - Uses AI models to analyze financial reports and generate investment recommendations
4. Ranking Opportunities - Scores stocks based on upside potential and creates investment thesis rankings

## Features

✨ AI-Powered Analysis
- Uses GPT-4, Claude, Moonshot, or Baichuan to analyze SEC filings as a senior hedge fund analyst
- Generates investment theses with target prices and recommendation summaries
- Supports a demo fallback when API credentials are unavailable

📊 Financial Data Integration
- Real-time stock pricing via yfinance
- SEC EDGAR integration for official filings
- Financial metrics: P/E ratio, market cap, dividend yield, 52-week ranges

🎯 Intelligent Ranking
- Ranks stocks by upside potential (Target Price / Current Price)
- Composite scoring: 50% upside, 30% recommendation, 20% valuation
- Filters for best BUY opportunities with risk assessment

💾 Smart Caching
- Caches stock universe data, reports, and analyses
- Reduces API calls and improves performance
- Configurable cache expiration (default: 30 days)

📤 Export Capabilities
- Export rankings to CSV and JSON formats
- Comprehensive summary reports with key statistics

## Quick Start

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Set up environment

```bash
cp .env.example .env
```

Update `.env` with your chosen model and credentials. If you do not have an API key yet, the project still runs in demo mode.

### 3) Run the CLI

```bash
python main.py --limit 20 --sample 5 --model moonshot
```

Optional demo-only execution:

```bash
python main.py --demo-only --limit 20 --sample 5
```

### 4) Run the dashboard

```bash
streamlit run app.py
```

This opens a browser-based dashboard for running the screener and visualizing top opportunities.

## Programmatic Usage

```python
from main import StockScreener

screener = StockScreener(model="moonshot")
results = screener.run_full_screen(limit_universe=20, sample_analysis=5)
print(results)
print(screener.generate_report())
```

## Project Structure

```text
stock-screener-ai/
├── app.py                    # Streamlit dashboard
├── main.py                   # CLI orchestration and entry point
├── stock_universe.py         # Step 1: Load NASDAQ 100 stocks
├── report_downloader.py      # Step 2: Download SEC reports
├── equity_analyzer.py        # Step 3: AI-powered analysis
├── stock_ranker.py           # Step 4: Ranking & scoring
├── config.py                # Configuration & environment variables
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore file
├── README.md                # Project documentation
├── data/
│   ├── reports/
│   └── cache/
└── stock_rankings.csv       # Generated output (if created by the screener)
```

## Configuration

The default model is configured in `config.py` and can be overridden in `.env`:

```env
ANALYSIS_MODEL=moonshot
MOONSHOT_API_KEY=your_key_here
SEC_EDGAR_USERNAME=your_email@example.com
```

## Demo Mode

The project is designed to run even without a live API key. When credentials are missing, the analyzer falls back to a deterministic demo recommendation so the pipeline can still produce ranked output for testing and UI validation.

## Troubleshooting

### OpenAI compatibility

The project uses the `openai` 1.x client API. If you see issues related to `ChatCompletion`, ensure your installed version is compatible and that your code uses the `OpenAI()` client object.

### Reporting or API issues

- Make sure `.env` exists and contains valid keys
- Check network access to yfinance and SEC EDGAR
- Clear cached data if needed:

```bash
rm -rf data/cache data/reports
```

## Contributing

Contributions are welcome. Good next steps include:
- Improving SEC filing parsing quality
- Enhanced valuation models
- Better dashboard visualizations
- More robust data refresh logic

## License

MIT License

## Disclaimer

This project is intended for educational and research purposes only. It does not constitute financial advice.
````
