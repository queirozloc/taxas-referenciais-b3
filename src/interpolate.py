import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

from .config import DI_TENORS_BD, CUPOM_TENORS_CD

_CURVE_CONFIG = {
    "DI":            ("tenor_bd", DI_TENORS_BD),
    "cupom_cambial": ("tenor_cd", CUPOM_TENORS_CD),
}


def interpolate_curve(df: pd.DataFrame, curve: str) -> pd.DataFrame:
    """
    Apply a not-a-knot cubic spline and evaluate at the standard tenors for the curve.

    DI        → business days (252/year), tenors defined in config.DI_TENORS_BD
    cupom_cambial → calendar days (360/year), tenors defined in config.CUPOM_TENORS_CD

    Returns DataFrame with columns: date, tenor, rate.
    """
    x_col, target_tenors = _CURVE_CONFIG[curve]

    reference_date = df["date"].iloc[0]
    sub = df[[x_col, "rate"]].drop_duplicates(x_col).sort_values(x_col)
    x = sub[x_col].values.astype(float)
    y = sub["rate"].values.astype(float)

    cs = CubicSpline(x, y, bc_type="not-a-knot")

    valid = [t for t in target_tenors if x[0] <= t <= x[-1]]
    if not valid:
        raise ValueError(
            f"No target tenors fall within observed range [{x[0]:.0f}, {x[-1]:.0f}] "
            f"for {curve} on {reference_date}"
        )

    return pd.DataFrame({"date": reference_date, "tenor": valid, "rate": cs(valid)})
