"""Configuration settings for the stock screener with multi-model support."""

import os

from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# MODEL SELECTION
# ==============================================================================
# Choose your primary analysis model
ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL", "gemini-3.7-flash")  # Options: gpt-4-turbo, claude-3-haiku, moonshot, baichuan-4-finance, gemini-3.7-flash

# ==============================================================================
# API KEYS (Add these to your .env file)
# ==============================================================================

# OpenAI (for GPT-4 Turbo)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Anthropic (for Claude 3 Haiku)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Moonshot/Kimi (for Moonshot model)
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")

# Baichuan (for Baichuan 4 Finance)
BAICHUAN_API_KEY = os.getenv("BAICHUAN_API_KEY")

# Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# SEC EDGAR
SEC_EDGAR_USERNAME = os.getenv("SEC_EDGAR_USERNAME", "research@stockscreener.com")

# ==============================================================================
# STOCK UNIVERSE SETTINGS
# ==============================================================================
NASDAQ_100_LIMIT = int(os.getenv("NASDAQ_100_LIMIT", 100))

# ==============================================================================
# REPORT SETTINGS
# ==============================================================================
REPORT_CACHE_DAYS = int(os.getenv("REPORT_CACHE_DAYS", 30))
REPORTS_DIR = "data/reports"
CACHE_DIR = "data/cache"

# ==============================================================================
# ANALYSIS SETTINGS
# ==============================================================================

# Temperature controls model creativity (0.0 = deterministic, 1.0 = random)
ANALYSIS_TEMPERATURE = float(os.getenv("ANALYSIS_TEMPERATURE", 0.7))

# Max tokens for response (adjust based on model)
ANALYSIS_MAX_TOKENS = int(os.getenv("ANALYSIS_MAX_TOKENS", 2000))

# ==============================================================================
# MODEL-SPECIFIC SETTINGS
# ==============================================================================

MODEL_SETTINGS = {
    "gpt-4-turbo": {
        "model_name": "gpt-4-turbo-preview",
        "provider": "OpenAI",
        "cost_per_stock": 0.09,
        "api_key_env": "OPENAI_API_KEY",
        "api_endpoint": "https://api.openai.com/v1/chat/completions",
        "max_tokens": 2000,
        "temperature": 0.7,
        "quality_rating": 10,
        "best_for": "Premium analysis, investment decisions",
    },
    "claude-3-haiku": {
        "model_name": "claude-3-haiku-20240307",
        "provider": "Anthropic",
        "cost_per_stock": 0.003,
        "api_key_env": "ANTHROPIC_API_KEY",
        "api_endpoint": "https://api.anthropic.com/v1/messages",
        "max_tokens": 2000,
        "temperature": 0.7,
        "quality_rating": 8,
        "best_for": "Balanced cost/quality, production use",
    },
    "moonshot": {
        "model_name": "moonshot-v1-8k",
        "provider": "Kimi AI",
        "cost_per_stock": 0.001,
        "api_key_env": "MOONSHOT_API_KEY",
        "api_endpoint": "https://api.moonshot.cn/v1/chat/completions",
        "max_tokens": 2000,
        "temperature": 0.7,
        "quality_rating": 9,
        "best_for": "Production screening, good quality, cheap",
    },
    "baichuan-4-finance": {
        "model_name": "Baichuan4-Finance",
        "provider": "Baichuan Inc.",
        "cost_per_stock": 0.0005,
        "api_key_env": "BAICHUAN_API_KEY",
        "api_endpoint": "https://api.baichuan-ai.com/v1/chat/completions",
        "max_tokens": 2000,
        "temperature": 0.7,
        "quality_rating": 8,
        "best_for": "Volume screening, ultra-cheap",
    },
    "gemini-3.7-flash": {
        "model_name": GEMINI_MODEL_NAME,
        "provider": "Google Gemini",
        "cost_per_stock": 0.00375,
        "api_key_env": "GOOGLE_API_KEY",
        "api_endpoint": "https://generativelanguage.googleapis.com",
        "max_tokens": 2000,
        "temperature": 0.7,
        "quality_rating": 9,
        "best_for": "Fast, cheap, strong reasoning for screening workflows",
    },
}

# ==============================================================================
# COST ESTIMATION
# ==============================================================================


def estimate_analysis_cost(num_stocks: int, model: str = None) -> float:
    """Estimate cost of analyzing N stocks."""
    if model is None:
        model = ANALYSIS_MODEL

    if model not in MODEL_SETTINGS:
        return 0.0

    cost_per_stock = MODEL_SETTINGS[model]["cost_per_stock"]
    return num_stocks * cost_per_stock


def get_model_info(model: str = None) -> dict:
    """Get information about a model."""
    if model is None:
        model = ANALYSIS_MODEL

    return MODEL_SETTINGS.get(model, {})


# ==============================================================================
# COST COMPARISON HELPER
# ==============================================================================


def compare_model_costs(num_stocks: int) -> dict:
    """Compare costs across all models for analyzing N stocks."""
    comparison = {}
    for model, settings in MODEL_SETTINGS.items():
        cost = settings["cost_per_stock"] * num_stocks
        comparison[model] = {
            "cost": cost,
            "per_stock": settings["cost_per_stock"],
            "quality": settings["quality_rating"],
            "provider": settings["provider"],
        }
    return comparison


# ==============================================================================
# SCREENING STRATEGIES PRESETS
# ==============================================================================

SCREENING_STRATEGIES = {
    "budget": {
        "description": "Ultra-cheap screening (best for volume)",
        "screening_model": "baichuan-4-finance",
        "analysis_model": "baichuan-4-finance",
        "premium_model": None,
        "estimated_cost_per_100_stocks": 0.05,
    },
    "balanced": {
        "description": "Good quality at reasonable cost (RECOMMENDED)",
        "screening_model": "gemini-3.7-flash",
        "analysis_model": "gemini-3.7-flash",
        "premium_model": None,
        "estimated_cost_per_100_stocks": 0.38,
    },
    "hybrid": {
        "description": "Tiered approach for best results",
        "screening_model": "baichuan-4-finance",
        "analysis_model": "gemini-3.7-flash",
        "premium_model": "gpt-4-turbo",
        "estimated_cost_per_100_stocks": 0.50,
        "strategy": "Baichuan for all, Gemini for top 50%, GPT-4 for top 5%",
    },
    "premium": {
        "description": "Best quality only (highest cost)",
        "screening_model": "gpt-4-turbo",
        "analysis_model": "gpt-4-turbo",
        "premium_model": None,
        "estimated_cost_per_100_stocks": 9.00,
    },
}

# ==============================================================================
# DIRECTORIES & PATHS
# ==============================================================================

# Ensure directories exist
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# ==============================================================================
# VALIDATION & HEALTH CHECK
# ==============================================================================


def validate_configuration():
    """Validate that required configuration is set."""
    messages = []

    if ANALYSIS_MODEL not in MODEL_SETTINGS:
        messages.append(f"ERROR: ANALYSIS_MODEL '{ANALYSIS_MODEL}' not found")
        return False, messages

    api_key_env = MODEL_SETTINGS[ANALYSIS_MODEL]["api_key_env"]
    api_key = os.getenv(api_key_env)

    if not api_key:
        messages.append(f"WARNING: {api_key_env} not set in .env file")
        messages.append(f"         Will fail when trying to use {ANALYSIS_MODEL}")
    else:
        messages.append(f"✓ {api_key_env} is configured")

    if os.path.isdir(REPORTS_DIR):
        messages.append(f"✓ Reports directory: {REPORTS_DIR}")
    else:
        messages.append(f"⚠ Could not create reports directory: {REPORTS_DIR}")

    if os.path.isdir(CACHE_DIR):
        messages.append(f"✓ Cache directory: {CACHE_DIR}")
    else:
        messages.append(f"⚠ Could not create cache directory: {CACHE_DIR}")

    return len([m for m in messages if m.startswith("ERROR")]) == 0, messages


# ==============================================================================
# PRINT CONFIGURATION SUMMARY
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("STOCK SCREENER CONFIGURATION")
    print("=" * 80)

    print(f"\nActive Model: {ANALYSIS_MODEL}")
    model_info = get_model_info()
    if model_info:
        print(f"  Provider: {model_info.get('provider')}")
        print(f"  Cost per stock: ${model_info.get('cost_per_stock')}")
        print(f"  Quality rating: {model_info.get('quality_rating')}/10")
        print(f"  Best for: {model_info.get('best_for')}")

    print(f"\nDirectories:")
    print(f"  Reports: {REPORTS_DIR}")
    print(f"  Cache: {CACHE_DIR}")

    print(f"\nCost Estimates (for 100 stocks):")
    costs = compare_model_costs(100)
    for model, info in costs.items():
        print(f"  {model:20} ${info['cost']:8.2f}")

    print(f"\nConfiguration Status:")
    is_valid, messages = validate_configuration()
    for msg in messages:
        print(f"  {msg}")

    print(f"\nAvailable Strategies:")
    for strategy, details in SCREENING_STRATEGIES.items():
        print(f"  • {strategy:15} - {details['description']}")

    print("\n" + "=" * 80)
