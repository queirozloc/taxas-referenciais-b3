"""
Usage:
    python main.py                              # run for today → Excel
    python main.py 2026-04-17                   # single date → Excel
    python main.py 2026-01-02 2026-04-17        # date range → Excel
    python main.py --store                      # today → Parquet
    python main.py 2026-04-17 --store           # single date → Parquet
    python main.py 2026-01-02 2026-04-17 --store
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from src.config import OUTPUT_DIR
from src.download import fetch_csv
from src.clean import parse_csv
from src.interpolate import interpolate_curve
from src.export import export_to_excel


def run(start: date, end: date, store: bool = False) -> None:
    di_frames: list[pd.DataFrame] = []
    cupom_frames: list[pd.DataFrame] = []
    di_raw_frames: list[pd.DataFrame] = []
    cupom_raw_frames: list[pd.DataFrame] = []

    current = start
    while current <= end:
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        print(f"Processing {current.isoformat()} ...", end=" ", flush=True)
        try:
            di_csv = fetch_csv(current, "DI")
            di_clean = parse_csv(di_csv, current)
            di_frames.append(interpolate_curve(di_clean, "DI"))
            if store:
                di_raw_frames.append(di_clean)

            cupom_csv = fetch_csv(current, "cupom_cambial")
            cupom_clean = parse_csv(cupom_csv, current)
            cupom_frames.append(interpolate_curve(cupom_clean, "cupom_cambial"))
            if store:
                cupom_raw_frames.append(cupom_clean)

            print("ok")
        except Exception as exc:
            print(f"skipped ({exc})")

        current += timedelta(days=1)

    if not di_frames:
        print("No data collected.")
        return

    if store:
        from src.store import upsert_parquet
        upsert_parquet(pd.concat(di_frames, ignore_index=True), "di")
        upsert_parquet(pd.concat(cupom_frames, ignore_index=True), "cupom")
        if di_raw_frames:
            upsert_parquet(pd.concat(di_raw_frames, ignore_index=True), "di_raw")
        if cupom_raw_frames:
            upsert_parquet(pd.concat(cupom_raw_frames, ignore_index=True), "cupom_raw")
    else:
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"taxas_b3_{start}_{end}.xlsx"
        export_to_excel(
            pd.concat(di_frames, ignore_index=True),
            pd.concat(cupom_frames, ignore_index=True),
            str(output_path),
        )


def _parse_args() -> tuple[date, date, bool]:
    store = "--store" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--store"]
    today = date.today()
    if len(args) == 0:
        return today, today, store
    if len(args) == 1:
        d = date.fromisoformat(args[0])
        return d, d, store
    return date.fromisoformat(args[0]), date.fromisoformat(args[1]), store


if __name__ == "__main__":
    start, end, store = _parse_args()
    run(start, end, store)
