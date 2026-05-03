import base64
import json
from datetime import date

import requests

_BASE = "https://sistemaswebb3-derivativos.b3.com.br/referenceRatesProxy/Search/"
_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://sistemaswebb3-derivativos.b3.com.br/referenceRatesPage/all?language=pt-br",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://sistemaswebb3-derivativos.b3.com.br",
}
_SESSION = requests.Session()
_SESSION.headers.update(_HEADERS)

CURVE_IDS = {
    "DI": "PRE",
    "cupom_cambial": "DOC",
}


def fetch_csv(reference_date: date, curve: str) -> str:
    """
    Download the semicolon-delimited CSV for a curve on a given date.

    The API returns a base64-encoded latin-1 CSV string.
    Columns: Descrição da Taxa; Dias Úteis; Dias Corridos; Preço/Taxa
    """
    product_id = CURVE_IDS[curve]
    date_str = reference_date.strftime("%Y-%m-%d")
    payload = {
        "language": "pt-br",
        "id": product_id,
        "pageNumber": 1,
        "pageSize": 20,   # ignored by the download endpoint
        "date": date_str,
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    r = _SESSION.get(_BASE + "GetDownloadFile/" + encoded, timeout=30)
    r.raise_for_status()
    if not r.text.strip():
        raise ValueError(f"Empty response for {curve} on {reference_date}")
    return base64.b64decode(r.text).decode("latin-1")


def available_dates(curve: str = "DI") -> list[str]:
    """Return ISO date strings with available data (most recent first)."""
    product_id = CURVE_IDS[curve]
    payload = {"language": "pt-br", "id": product_id}
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    r = _SESSION.get(_BASE + "GetDate/" + encoded, timeout=30)
    r.raise_for_status()
    # Returns e.g. ["2026-04-17T00:00:00", ...]
    return [d[:10] for d in r.json()]
