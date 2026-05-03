from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import DATA_DIR
from src.store import load_parquet


def _exists(name: str) -> bool:
    return (Path(DATA_DIR) / f"{name}.parquet").exists()


@st.cache_data(ttl=3600)
def load_di() -> pd.DataFrame:
    return load_parquet("di") if _exists("di") else pd.DataFrame()


@st.cache_data(ttl=3600)
def load_cupom() -> pd.DataFrame:
    return load_parquet("cupom") if _exists("cupom") else pd.DataFrame()


@st.cache_data(ttl=3600)
def load_di_raw() -> pd.DataFrame:
    return load_parquet("di_raw") if _exists("di_raw") else pd.DataFrame()


def get_available_dates(df: pd.DataFrame) -> list:
    if df.empty:
        return []
    return sorted(df["date"].unique().tolist(), reverse=True)
