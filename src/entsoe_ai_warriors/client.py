"""ENTSO-E API client wrapper."""

import os

from dotenv import load_dotenv
from entsoe import EntsoePandasClient


def get_client() -> EntsoePandasClient:
    """Load API key from environment (.env or Streamlit secrets) and return an ENTSO-E client."""
    load_dotenv()
    api_key = os.environ.get("ENTSOE_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets["ENTSOE_API_KEY"]
        except Exception:
            pass
    if not api_key:
        raise RuntimeError(
            "ENTSOE_API_KEY not found. Set it in .env or Streamlit secrets."
        )
    return EntsoePandasClient(api_key=api_key)
