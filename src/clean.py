import io
from datetime import date

import pandas as pd


def parse_csv(csv_text: str, reference_date: date) -> pd.DataFrame:
    """
    Parse the B3 semicolon-delimited CSV into a clean DataFrame.

    Expected columns: Descrição da Taxa; Dias Úteis; Dias Corridos; Preço/Taxa
    Returns: date, tenor_bd (business days, 252/year), tenor_cd (calendar days, 360/year), rate (% p.a.).
    """
    df = pd.read_csv(
        io.StringIO(csv_text),
        sep=";",
        header=0,
        usecols=[1, 2, 3],
        names=["tenor_bd", "tenor_cd", "rate"],
        dtype={"tenor_bd": int, "tenor_cd": int, "rate": str},
    )
    df["rate"] = df["rate"].str.replace(",", ".").astype(float)
    df = df.drop_duplicates("tenor_bd").sort_values("tenor_bd").reset_index(drop=True)
    df.insert(0, "date", reference_date)
    return df
