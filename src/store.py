from __future__ import annotations

import pandas as pd
from pathlib import Path

from src.config import DATA_DIR


def _path(name: str) -> Path:
    return Path(DATA_DIR) / f"{name}.parquet"


def upsert_parquet(df: pd.DataFrame, name: str) -> None:
    """Append-or-replace rows by date in data/{name}.parquet."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    path = _path(name)
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        existing = pd.read_parquet(path)
        existing = existing[~existing["date"].isin(df["date"].unique())]
        df = pd.concat([existing, df], ignore_index=True)
    df.sort_values("date").reset_index(drop=True).to_parquet(path, index=False)
    print(f"Stored: {path} ({len(df['date'].unique())} dates)")


def load_parquet(name: str) -> pd.DataFrame:
    return pd.read_parquet(_path(name))
