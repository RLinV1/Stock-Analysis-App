"""Yahoo Finance history as hashed local snapshots in the project's dataset format.

Downloaded data is for local research only: Yahoo does not grant redistribution,
so outputs belong under the git-ignored data/ directory.
"""

from __future__ import annotations

import csv
import io
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np

from .data import file_hash, write_dataset

# SPEC section 8 tiers: paper-faithful raw VIX index, and the tradable VIXY ETF.
TIERS = {
    "tier1": (("VTI", "stock"), ("AGG", "bond"), ("DBC", "other"), ("^VIX", "other")),
    "tier2": (("VTI", "stock"), ("AGG", "bond"), ("DBC", "other"), ("VIXY", "other")),
}
TIER_DEVIATIONS = {
    "tier1": "Raw ^VIX index is NOT INVESTABLE; returns earned from it are not achievable (fidelity hypothesis only)",
    "tier2": "VIXY (short-term VIX futures ETF) replaces the paper's VIX; its history starts in 2011",
}
QUERY = {"interval": "1d", "auto_adjust": False, "actions": True, "repair": False}


def yahoo_csv(symbol: str, start: str, end: str) -> bytes:
    """Download one ticker's daily history exactly as yfinance returns it."""
    import yfinance  # optional "data" extra; only needed for real downloads

    frame = yfinance.Ticker(symbol).history(start=start, end=end, raise_errors=True, **QUERY)
    return frame.to_csv().encode("utf-8")


def _number(row: dict, column: str, *, required: bool) -> float:
    text = row.get(column)
    if text in (None, ""):
        if required:
            raise ValueError(f"Missing {column} value")
        return 0.0
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"{column} must be finite")
    return value


def total_return_series(content: bytes) -> dict[str, float]:
    """Map each date to a total-return index starting at 100.

    Close and distributions are split-adjusted by Yahoo, so the gross return is
    (close_t + dividends_t + capital_gains_t) / close_{t-1}.
    """
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8"))))
    if len(rows) < 2:
        raise ValueError("History needs at least two rows")
    dates, closes, distributions = [], [], []
    for row in rows:
        day = date.fromisoformat(row["Date"][:10]).isoformat()
        close = _number(row, "Close", required=True)
        # shortcut: assumes Yahoo never repeats a capital gain inside Dividends; verify on real ETF data before A1 claims.
        paid = _number(row, "Dividends", required=False) + _number(row, "Capital Gains", required=False)
        if close <= 0 or paid < 0:
            raise ValueError(f"Invalid close or distribution on {day}")
        dates.append(day)
        closes.append(close)
        distributions.append(paid)
    if any(a >= b for a, b in zip(dates, dates[1:])):
        raise ValueError("History dates must be strictly increasing")
    close, paid = np.array(closes), np.array(distributions)
    index = 100 * np.cumprod(np.concatenate([[1.0], (close[1:] + paid[1:]) / close[:-1]]))
    return dict(zip(dates, index.tolist()))


def common_dates(series: dict[str, dict[str, float]]) -> list[str]:
    """Dates on which every ticker has a value; nothing is filled."""
    return sorted(set.intersection(*(set(values) for values in series.values())))


def fetch_tier(tier: str, start: str, end: str, output: Path, *,
               download: Callable[[str, str, str], bytes] = yahoo_csv) -> Path:
    """Download a tier into a new directory and return its validated manifest path.

    `end` is exclusive, as in yfinance.
    """
    if tier not in TIERS:
        raise ValueError(f"Tier must be one of {sorted(TIERS)}")
    if date.fromisoformat(start) >= date.fromisoformat(end):
        raise ValueError("Start must be before end")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    raw, series, hashes = output / "raw", {}, {}
    raw.mkdir()
    for symbol, _ in TIERS[tier]:
        path = raw / f"{symbol.lstrip('^')}.csv"
        path.write_bytes(download(symbol, start, end))
        hashes[symbol] = file_hash(path)
        series[symbol] = total_return_series(path.read_bytes())
    dates = common_dates(series)
    if len(dates) < 3:
        raise ValueError("Tickers share too few trading dates")
    dropped = len(set().union(*series.values())) - len(dates)
    prices = np.array([[series[symbol][day] for symbol, _ in TIERS[tier]] for day in dates])
    version = _yfinance_version()
    manifest = write_dataset(
        output / "dataset", dates, prices,
        [{"symbol": symbol, "role": role} for symbol, role in TIERS[tier]],
        kind="historical",
        source=f"Yahoo Finance via yfinance {version}, retrieved {retrieved_at}; see ../acquisition.json",
        license_note="Yahoo Finance terms: personal research use only, no redistribution; keep local and uncommitted",
        adjustment="Total-return index from 100: (split-adjusted Close + Dividends + Capital Gains) / previous Close",
        deviations=[
            "Reconstruction from Yahoo, not the authors' unpublished dataset",
            TIER_DEVIATIONS[tier],
            "Prices are total-return index levels, not quoted closes; Yahoo applies hindsight split adjustment",
            f"Kept only dates every ticker traded; {dropped} other dates dropped, none filled",
        ])
    (output / "acquisition.json").write_text(json.dumps({
        "tier": tier, "start": start, "end_exclusive": end, "query": QUERY,
        "client": f"yfinance {version}", "retrieved_at": retrieved_at,
        "raw_sha256": hashes, "dropped_dates": dropped,
    }, indent=2) + "\n", encoding="utf-8")
    return manifest


def _yfinance_version() -> str:
    try:
        import yfinance
    except ImportError:
        return "not installed"
    return yfinance.__version__
