````markdown
# 🚀 Setup Guide: AI-Powered Stock Screener

Complete step-by-step guide to get the stock screener running with your choice of AI models.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Model Selection](#model-selection)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **OS**: Windows, macOS, or Linux
- **Internet**: Required for API calls
- **Disk Space**: ~100-200 MB for data and cache

### Check Python Version
```bash
python --version  # Should be 3.8+
```

## Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/d-imitar/stock-screener-ai.git
cd stock-screener-ai
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

If you encounter issues, try upgrading pip first:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Create Configuration File
```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your API keys
# Linux/macOS:
nano .env
# Windows:
notepad .env
```

## Model Selection

### Overview of Models

| Model | Cost | Quality | Best For |
|-------|------|---------|----------|
| **Baichuan 4 Finance** | $0.0005/stock | 8/10 | Budget screening |
| **Moonshot** | $0.001/stock | 9/10 | **Recommended** |
| **Claude 3 Haiku** | $0.003/stock | 8/10 | Balanced approach |
| **GPT-4 Turbo** | $0.09/stock | 10/10 | Premium quality |

### Recommendation for You
**Start with Moonshot** - it offers the best balance:
- ✓ Excellent quality (9/10)
- ✓ Very affordable ($0.001 per stock)
- ✓ Good English support
- ✓ Easy API access

## Configuration

### Choose Your Model

#### Option 1: Moonshot (Recommended)
```bash
# In .env file:
ANALYSIS_MODEL=moonshot
MOONSHOT_API_KEY=your_key_here
```

**Get API Key**: https://platform.moonshot.cn/

#### Option 2: Baichuan 4 Finance (Budget)
```bash
# In .env file:
ANALYSIS_MODEL=baichuan-4-finance
BAICHUAN_API_KEY=your_key_here
```

**Get API Key**: https://platform.baichuan-ai.com/

#### Option 3: GPT-4 Turbo (Premium)
```bash
# In .env file:
ANALYSIS_MODEL=gpt-4-turbo
OPENAI_API_KEY=your_key_here
```

**Get API Key**: https://platform.openai.com/api-keys

#### Option 4: Claude 3 Haiku (Balanced)
```bash
# In .env file:
ANALYSIS_MODEL=claude-3-haiku
ANTHROPIC_API_KEY=your_key_here
```

**Get API Key**: https://console.anthropic.com/

### Configuration Steps

1. **Get API Key**
   - Visit the provider's website (links above)
   - Sign up or log in
   - Generate an API key
   - Copy the key

2. **Add to .env**
   ```bash
   # Open .env file
   nano .env  # or your preferred editor
   
   # Paste your key:
   ANALYSIS_MODEL=moonshot
   MOONSHOT_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
   
   # Set SEC EDGAR email (any email works):
   SEC_EDGAR_USERNAME=your.email@example.com
   ```

3. **Save and Close**
   - Save the file
   - Don't commit .env to git!

### Full Configuration Example (.env)

```dotenv
# Model Selection
ANALYSIS_MODEL=moonshot

# API Keys (fill in the one you're using)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
MOONSHOT_API_KEY=sk-your-actual-key-here
BAICHUAN_API_KEY=

# SEC EDGAR
SEC_EDGAR_USERNAME=research@example.com

# Stock Universe
NASDAQ_100_LIMIT=100

# Caching
REPORT_CACHE_DAYS=30

# Analysis Settings
ANALYSIS_TEMPERATURE=0.7
ANALYSIS_MAX_TOKENS=2000
```

## Testing

### Step 1: Verify Configuration
```bash
python config.py
```

Expected output:
```
================================================================================
STOCK SCREENER CONFIGURATION
================================================================================

Active Model: moonshot
  Provider: Kimi AI
  Cost per stock: $0.001
  Quality rating: 9/10
  Best for: Production screening, good quality, cheap

Configuration Status:
  ✓ MOONSHOT_API_KEY is configured
  ✓ Reports directory: data/reports
  ✓ Cache directory: data/cache
```

### Step 2: Quick Test Run
```bash
# Test with a small sample (5 stocks only)
python main.py
```

This will:
1. Load 5 NASDAQ stocks
2. Download their latest 10-K reports
3. Analyze them with your selected model
4. Generate rankings
5. Export results

### Step 3: Check Results
Look for output files:
```bash
# CSV rankings
ls -la stock_rankings.csv

# JSON rankings
ls -la stock_rankings.json

# Sample output should look like:
# rank,ticker,company_name,recommendation,current_price,target_price,upside_potential_%
# 1,AAPL,Apple Inc.,BUY,150.25,165.00,9.82
```

## Troubleshooting

### API Key Issues

**Error: "No API key found"**
- Check that .env file exists
- Verify API key is correctly set
- Restart Python/terminal after editing .env
- Check there are no quotes around the key

**Error: "Invalid API key"**
- Generate a new API key from provider
- Remove old/expired key from .env
- Ensure you copied the entire key correctly

**Error: "API key not authorized"**
- Verify you have account credits/quota
- Check API key is for the correct model
- Confirm API key hasn't been revoked

### Model-Specific Issues

**Moonshot Issues**
- Verify key starts with `sk-`
- Check at: https://platform.moonshot.cn/
- Documentation: https://platform.moonshot.cn/docs

**Baichuan Issues**
- Verify you're using Baichuan4-Finance model
- Check at: https://platform.baichuan-ai.com/
- May need to fund account for API access

**OpenAI Issues**
- Check account has available credits
- Visit: https://platform.openai.com/account/billing/overview
- Verify key is for organization (if applicable)

**Anthropic Issues**
- Ensure Anthropic account is active
- Check at: https://console.anthropic.com/
- Verify no spending limits are hit

### Installation Issues

**Error: "Module not found"**
```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt

# Or install specific package
pip install openai anthropic requests python-dotenv yfinance
```

**Error: "Python version not supported"**
```bash
# Check Python version
python --version

# If < 3.8, upgrade Python from python.org
```

**Error: "No module named 'requests'"**
```bash
# Install requests
pip install requests
```

### Cache Issues

**Clear cached data:**
```bash
# Remove all cache
rm -rf data/cache data/reports

# Or just reports
rm -rf data/reports

# Or just analyses
rm -rf data/cache/*research*
```

**Cache will regenerate automatically on next run.**

### Cost Issues

**High costs with GPT-4?**
```bash
# Switch to cheaper model
# Edit .env:
ANALYSIS_MODEL=moonshot  # 180x cheaper!

# Or use hybrid approach (see COST_COMPARISON.md)
```

**Estimate costs first:**
```python
from config import estimate_analysis_cost, compare_model_costs

# Cost for 100 stocks
cost = estimate_analysis_cost(100, "moonshot")
print(f"Cost: ${cost}")

# Compare all models
costs = compare_model_costs(100)
for model, info in costs.items():
    print(f"{model}: ${info['cost']}")
```

## Advanced Setup

### Use Different Model per Step

Modify `main.py` to use different models for each step:

```python
from main import StockScreener
from equity_analyzer import MultiModelAnalyzer

screener = StockScreener()

# Step 1: Get universe
universe = screener.step_1_get_universe(limit=100)

# Step 2: Download reports
reports = screener.step_2_download_reports()

# Step 3a: Quick screening with cheap model
analyzer_cheap = MultiModelAnalyzer("baichuan-4-finance")
quick_results = {}
for ticker in universe['ticker'][:50]:
    quick_results[ticker] = analyzer_cheap.analyze_stock(...)

# Step 3b: Deep analysis with better model
analyzer_good = MultiModelAnalyzer("moonshot")
deep_results = {}
for ticker in top_50:
    deep_results[ticker] = analyzer_good.analyze_stock(...)
```

### Batch Processing

```bash
# Screen multiple batches of stocks
for batch in {1..5}; do
    # Process batch
    python main.py --batch $batch
done

# Combine results
python combine_results.py
```

### Production Setup

For running as a service:
```bash
# Install supervisor (Linux/macOS)
pip install supervisor

# Or use systemd for Linux
# Or Windows Task Scheduler
```

## Security Checklist

- [ ] .env file is in .gitignore
- [ ] API keys are never committed to git
- [ ] Permissions on .env are restricted (chmod 600)
- [ ] API keys are rotated periodically
- [ ] Different keys for dev/prod environments
- [ ] No API keys in logs or error messages
- [ ] Monitor API usage on provider dashboards

## Next Steps

1. **Review Cost Analysis**
   - Read COST_COMPARISON.md
   - Estimate your monthly costs
   - Choose optimal model

2. **Review Model Comparison**
   - Read MODEL_COMPARISON.md
   - Understand tradeoffs
   - Plan your strategy

3. **Run Full Screen**
   ```bash
   python main.py
   ```

4. **Review Results**
   - Open stock_rankings.csv
   - Analyze top 10 recommendations
   - Read detailed analyses

5. **Customize for Your Needs**
   - Modify config settings
   - Adjust stock universe
   - Build on the framework

## Support & Resources

- **Documentation**: README.md
- **Cost Analysis**: COST_COMPARISON.md
- **Model Comparison**: MODEL_COMPARISON.md
- **GitHub Issues**: Report bugs or request features

## Quick Reference

```bash
# Show configuration
python config.py

# Run screener
python main.py

# Estimate costs
python -c "from config import estimate_analysis_cost; print(estimate_analysis_cost(100))"

# Switch models
# Edit .env and change ANALYSIS_MODEL

# Clear cache
rm -rf data/cache data/reports

# Update dependencies
pip install --upgrade -r requirements.txt
```

## FAQ

**Q: Can I switch models mid-project?**
A: Yes! Just change ANALYSIS_MODEL in .env and restart.

**Q: How much will this cost?**
A: Depends on model. See COST_COMPARISON.md for details.

**Q: Can I analyze S&P 500?**
A: Yes! Set NASDAQ_100_LIMIT to 500 or higher.

**Q: How often should I run the screener?**
A: Weekly is typical. Reports update quarterly.

**Q: Is my data safe?**
A: Yes. All data stays local. Only reports are downloaded from SEC, analyses sent to AI API.

**Q: Can I use multiple models?**
A: Yes! See "Advanced Setup" section above.

---

**Ready to start screening? Run:**
```bash
python main.py
```

Happy investing! 🚀
````
