import json
from typing import Optional

import pandas as pd
import streamlit as st

from config import ANALYSIS_MODEL
from main import StockScreener


st.set_page_config(page_title="Stock Screener AI", page_icon="📈", layout="wide")


def _run_screen(limit: int, sample: int, model: str) -> tuple[Optional[pd.DataFrame], dict, str]:
    screener = StockScreener(model=model)
    results = screener.run_full_screen(limit_universe=limit, sample_analysis=sample)
    ranked_df = screener.ranked_df
    report = screener.generate_report() if ranked_df is not None and not ranked_df.empty else "No ranked data available."
    return ranked_df, results, report


def main() -> None:
    st.title("📈 Stock Screener AI")
    st.caption("AI-assisted stock screening, ranking, and equity research dashboard")

    with st.sidebar:
        st.header("Configuration")
        selected_model = st.selectbox(
            "Analysis model",
            options=["gpt-4-turbo", "claude-3-haiku", "moonshot", "baichuan-4-finance"],
            index=["gpt-4-turbo", "claude-3-haiku", "moonshot", "baichuan-4-finance"].index(ANALYSIS_MODEL),
        )
        limit = st.slider("Stocks to screen", min_value=5, max_value=100, value=20, step=5)
        sample = st.slider("Stocks to analyze", min_value=1, max_value=20, value=5, step=1)

        st.markdown("---")
        st.write("Demo mode: if no API keys are configured, the app automatically uses a deterministic fallback recommendation engine.")
        run_button = st.button("Run screener", type="primary")

    if run_button:
        with st.spinner("Running the screening pipeline..."):
            ranked_df, results, report = _run_screen(limit=limit, sample=sample, model=selected_model)

        st.subheader("Summary")
        st.json(results)

        st.subheader("Top opportunities")
        if ranked_df is not None and not ranked_df.empty:
            st.dataframe(ranked_df[[
                "rank",
                "ticker",
                "company_name",
                "recommendation",
                "current_price",
                "target_price",
                "upside_potential_%",
                "composite_score",
            ]], use_container_width=True)
        else:
            st.info("No ranked stock data was generated. Check the console logs for details.")

        st.subheader("Research summary")
        st.text(report)
    else:
        st.info("Use the sidebar to configure the screen and click 'Run screener' to generate rankings.")


if __name__ == "__main__":
    main()
