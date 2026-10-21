import json

import pytest

from portfolio_lab.data import file_hash, load_dataset
from portfolio_lab.yahoo import TIERS, common_dates, fetch_tier, total_return_series

HEADER = "Date,Open,High,Low,Close,Adj Close,Volume,Dividends,Stock Splits,Capital Gains\n"


def history(*rows):
    """Rows of (date, close, dividends) in the CSV shape yfinance writes."""
    lines = [f"{day} 00:00:00-05:00,1,1,1,{close},{close},10,{paid},0.0,0.0\n" for day, close, paid in rows]
    return (HEADER + "".join(lines)).encode("utf-8")


def test_total_return_adds_same_day_distribution():
    series = total_return_series(history(("2020-01-02", 100, 0), ("2020-01-03", 102, 1), ("2020-01-06", 101, 0)))
    # 100 -> 100 * (102 + 1) / 100 = 103 -> 103 * 101 / 102
    assert list(series) == ["2020-01-02", "2020-01-03", "2020-01-06"]
    assert series["2020-01-03"] == pytest.approx(103.0)
    assert series["2020-01-06"] == pytest.approx(103 * 101 / 102)


def test_missing_capital_gains_column_counts_as_zero():
    content = b"Date,Close,Dividends\n2020-01-02,50,0\n2020-01-03,55,0.5\n"
    assert total_return_series(content)["2020-01-03"] == pytest.approx(100 * 55.5 / 50)


@pytest.mark.parametrize("bad", ["0", "-1", "nan", "inf", ""])
def test_invalid_close_is_rejected(bad):
    content = f"Date,Close,Dividends\n2020-01-02,50,0\n2020-01-03,{bad},0\n".encode()
    with pytest.raises(ValueError):
        total_return_series(content)


def test_unordered_dates_are_rejected():
    with pytest.raises(ValueError, match="strictly increasing"):
        total_return_series(history(("2020-01-03", 100, 0), ("2020-01-02", 101, 0)))


def test_distribution_on_dropped_date_is_kept():
    a = total_return_series(history(("2020-01-02", 100, 0), ("2020-01-03", 98, 2), ("2020-01-06", 99, 0)))
    b = total_return_series(history(("2020-01-02", 10, 0), ("2020-01-06", 11, 0)))
    assert common_dates({"A": a, "B": b}) == ["2020-01-02", "2020-01-06"]
    # The 2-unit payout on the dropped date still compounds into the next kept level.
    assert a["2020-01-06"] / a["2020-01-02"] == pytest.approx((98 + 2) / 100 * 99 / 98)


def fake_download(calls):
    def download(symbol, start, end):
        calls.append((symbol, start, end))
        days = ["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"]
        if symbol == "^VIX":
            days = days[:2] + days[3:]  # the index misses one session
        return history(*[(day, 100 + i, 0.5 if (symbol, i) == ("AGG", 2) else 0) for i, day in enumerate(days)])
    return download


def test_fetch_tier_writes_loadable_labelled_snapshot(tmp_path):
    calls = []
    manifest_path = fetch_tier("tier1", "2020-01-01", "2020-01-08", tmp_path / "tier1", download=fake_download(calls))
    dataset = load_dataset(manifest_path)
    assert dataset.symbols == [symbol for symbol, _ in TIERS["tier1"]]
    assert dataset.dates.tolist() == ["2020-01-02", "2020-01-03", "2020-01-07"]
    assert calls == [(symbol, "2020-01-01", "2020-01-08") for symbol, _ in TIERS["tier1"]]
    assert any("NOT INVESTABLE" in note for note in dataset.manifest["deviations"])
    assert any("1 other dates dropped" in note for note in dataset.manifest["deviations"])
    acquisition = json.loads((tmp_path / "tier1" / "acquisition.json").read_text())
    assert acquisition["raw_sha256"]["^VIX"] == file_hash(tmp_path / "tier1" / "raw" / "VIX.csv")
    assert acquisition["query"]["auto_adjust"] is False


def test_fetch_tier_refuses_existing_output_before_downloading(tmp_path):
    (tmp_path / "taken").mkdir()
    calls = []
    with pytest.raises(FileExistsError):
        fetch_tier("tier2", "2020-01-01", "2020-01-08", tmp_path / "taken", download=fake_download(calls))
    assert calls == []


@pytest.mark.parametrize("tier,start,end", [("tier9", "2020-01-01", "2020-02-01"),
                                            ("tier1", "2020-02-01", "2020-01-01")])
def test_fetch_tier_rejects_bad_arguments(tmp_path, tier, start, end):
    with pytest.raises(ValueError):
        fetch_tier(tier, start, end, tmp_path / "out", download=fake_download([]))
    assert not (tmp_path / "out").exists()
