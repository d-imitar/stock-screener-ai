import json
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from config import ANALYSIS_MODEL
from main import StockScreener


st.set_page_config(page_title="Stock Screener AI", page_icon="📈", layout="wide")


def _run_screen(limit: int, sample: int, model: str, demo_only: bool) -> Tuple[Optional[pd.DataFrame], dict, str]:
    screener = StockScreener(model=model, demo_only=demo_only)
    results = screener.run_full_screen(limit_universe=limit, sample_analysis=sample)
    ranked_df = screener.ranked_df
    report = screener.generate_report() if ranked_df is not None and not ranked_df.empty else "No ranked data available."
    return ranked_df, results, report


def _render_metric(label: str, value: str, delta: str = "") -> None:
    st.metric(label=label, value=value, delta=delta)


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
        demo_only = st.checkbox("Force demo mode", help="Ignore external API keys and use deterministic fallback analysis.")

        st.markdown("---")
        st.write("Demo mode: if no API keys are configured, the app automatically uses a deterministic fallback recommendation engine.")
        run_button = st.button("Run screener", type="primary")

    if run_button:
        with st.spinner("Running the screening pipeline..."):
            ranked_df, results, report = _run_screen(limit=limit, sample=sample, model=selected_model, demo_only=demo_only)

        st.subheader("Summary")
        if results:
            col1, col2, col3 = st.columns(3)
            with col1:
                _render_metric("Universe size", str(results.get("universe_size", 0)))
            with col2:
                _render_metric("Stocks analyzed", str(results.get("stocks_analyzed", 0)))
            with col3:
                _render_metric("Top opportunity", str(results.get("top_opportunity", "N/A")))
            st.json(results)

        st.subheader("Top opportunities")
        if ranked_df is not None and not ranked_df.empty:
            chart_df = ranked_df[["rank", "ticker", "company_name", "recommendation", "current_price", "target_price", "upside_potential_%", "composite_score"]].copy()
            st.bar_chart(chart_df.set_index("ticker")["upside_potential_%"])
            st.dataframe(chart_df, use_container_width=True)
        else:
            st.info("No ranked stock data was generated. Check the console logs for details.")

        st.subheader("Research summary")
        st.text(report)
    else:
        st.info("Use the sidebar to configure the screen and click 'Run screener' to generate rankings.")


if __name__ == "__main__":
    main()
