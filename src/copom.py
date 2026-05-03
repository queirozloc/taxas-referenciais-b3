"""
Flat-Forward Copom (FFC) methodology.
Reference: Bristotti (2018), Carreira & Brostowicz (2016).

The Selic/CDI only changes at COPOM meetings, so the DI forward rate is
constant between consecutive meetings. Each segment's implied rate is the
annualised flat-forward computed from raw DI knots (~277 points per day).
"""
from __future__ import annotations

from datetime import date
from typing import Union

import numpy as np
import pandas as pd

from src.brazil_calendar import count_business_days

# COPOM decision dates (second day of each meeting, when the rate is announced).
# Source: BCB calendar. Verify/update as new calendars are published.
COPOM_MEETINGS: list[date] = [
    # 2024
    date(2024, 1, 31), date(2024, 3, 20), date(2024, 5, 8),
    date(2024, 6, 19), date(2024, 7, 31), date(2024, 9, 18),
    date(2024, 11, 6), date(2024, 12, 11),
    # 2025
    date(2025, 1, 29), date(2025, 3, 19), date(2025, 5, 7),
    date(2025, 6, 18), date(2025, 7, 30), date(2025, 9, 17),
    date(2025, 11, 5), date(2025, 12, 10),
    # 2026
    date(2026, 1, 28), date(2026, 3, 18), date(2026, 5, 6),
    date(2026, 6, 17), date(2026, 7, 29), date(2026, 9, 16),
    date(2026, 11, 4), date(2026, 12, 9),
    # 2027
    date(2027, 1, 27), date(2027, 3, 17), date(2027, 5, 5),
    date(2027, 6, 16), date(2027, 7, 28), date(2027, 9, 15),
    date(2027, 11, 3), date(2027, 12, 8),
]


def _to_date(d) -> date:
    return pd.Timestamp(d).date()


def flat_forward_df(
    knots_bd: np.ndarray,
    knots_rate: np.ndarray,
    query_bd: float,
) -> float:
    """
    Return the discount factor at query_bd via piecewise flat-forward interpolation.

    DF(T) = 1 / (1 + r/100)^(T/252)
    forward f(T1,T2) = [DF(T1)/DF(T2)]^(252/(T2-T1)) - 1
    DF(τ) = DF(T1) * (1+f)^(-(τ-T1)/252)  for τ ∈ [T1, T2]
    """
    dfs = 1.0 / (1.0 + knots_rate / 100.0) ** (knots_bd / 252.0)

    idx = int(np.searchsorted(knots_bd, query_bd, side="right")) - 1
    idx = max(0, min(idx, len(knots_bd) - 2))

    t1, t2 = knots_bd[idx], knots_bd[idx + 1]
    df1, df2 = dfs[idx], dfs[idx + 1]

    fwd = (df1 / df2) ** (252.0 / (t2 - t1)) - 1.0
    return float(df1 * (1.0 + fwd) ** (-(query_bd - t1) / 252.0))


def build_copom_snapshot(
    di_raw_day: pd.DataFrame,
    curve_date: Union[date, pd.Timestamp],
) -> pd.DataFrame:
    """
    For each future COPOM meeting within the raw-curve range, compute the
    implied flat-forward rate for that inter-meeting segment.

    di_raw_day: single-date slice of di_raw with columns [tenor_bd, rate].
    Returns DataFrame[meeting_date, implied_rate (% p.a.)].
    """
    curve_date = _to_date(curve_date)

    sub = di_raw_day[["tenor_bd", "rate"]].drop_duplicates("tenor_bd").sort_values("tenor_bd")
    knots_bd = sub["tenor_bd"].to_numpy(dtype=float)
    knots_rate = sub["rate"].to_numpy(dtype=float)
    max_tenor = knots_bd.max()

    future_meetings = [m for m in COPOM_MEETINGS if m > curve_date]

    records = []
    prev_df = 1.0
    prev_tenor = 0.0

    for meeting in future_meetings:
        tenor = float(count_business_days(curve_date, meeting))
        if tenor <= 0 or tenor > max_tenor:
            break

        curr_df = flat_forward_df(knots_bd, knots_rate, tenor)
        if curr_df <= 0 or prev_df <= 0:
            break

        dt = tenor - prev_tenor
        if dt > 0:
            implied_rate = ((prev_df / curr_df) ** (252.0 / dt) - 1.0) * 100.0
            records.append({"meeting_date": meeting, "implied_rate": round(implied_rate, 4)})

        prev_df = curr_df
        prev_tenor = tenor

    return pd.DataFrame(records)


def build_copom_evolution(
    di_raw_df: pd.DataFrame,
    meeting_date: Union[date, pd.Timestamp],
) -> pd.DataFrame:
    """
    For each curve date in di_raw_df, extract the implied rate for meeting_date.
    Returns DataFrame[curve_date, implied_rate (% p.a.)].
    """
    meeting_date = _to_date(meeting_date)
    records = []

    for curve_date, group in di_raw_df.groupby("date"):
        snapshot = build_copom_snapshot(group, curve_date)
        row = snapshot[snapshot["meeting_date"] == meeting_date]
        if not row.empty:
            records.append({
                "curve_date": _to_date(curve_date),
                "implied_rate": row["implied_rate"].iloc[0],
            })

    return pd.DataFrame(records)
