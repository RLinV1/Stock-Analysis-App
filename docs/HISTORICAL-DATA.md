# Historical data through 2026

Status 2026-10-21: the acquisition code, configs and offline tests exist; the 13 offline tests pass. **No data has been downloaded and no model has been trained on it yet** (the user asked to hold off). Nothing here is a result.

## What gets tested

| Run | Volatility asset | Test period | Why |
|---|---|---|---|
| `tier1-paper` | raw ^VIX index | 2011-01-01 → 2020-04-30 | The paper's own window and closest reading of its "VIX" |
| `tier1-2026` | raw ^VIX index | 2011-01-01 → latest 2026 date | Same method, six more years of out-of-sample data |
| `tier2-paper` | VIXY ETF | 2013-01-01 → 2020-04-30 | Tradable volatility asset over the paper's window |
| `tier2-2026` | VIXY ETF | 2013-01-01 → latest 2026 date | Tradable version through 2026 |

All four use VTI (stocks), AGG (bonds) and DBC (commodities) plus the volatility asset, retrained every 24 months on all prior data, with the paper's 50-day lookback and 64-unit LSTM.

## Decisions and why

The full reasoning, with risks, is in the [design record](../openspec/changes/add-yahoo-historical-data/design.md). In short:

1. **Yahoo via yfinance** (your choice): free and covers 2006 onward. Yahoo does not allow redistribution, so downloads stay in git-ignored `data/` and are never committed.
2. **"Paper data" is a reconstruction.** The authors never published their dataset. Same tickers and dates from Yahoo is the closest honest stand-in, so a match or miss against the paper's Sharpe 1.962 does not prove or disprove the paper.
3. **Both volatility tiers** (your choice): raw ^VIX matches the paper's wording but cannot be bought; VIXY can be bought but behaves differently and only starts in 2011. Running both shows how much any result depends on an untradable asset.
4. **The same test start for both windows**, so the 2026 run contains the paper window and the 2020-2026 part can be compared against it. The 2026 configs say `2026-12-31`; the planner stops at the last downloaded date.
5. **Total-return prices.** Each day's return is (close + dividends + capital gains) / previous close. Raw close would ignore AGG's and VTI's distributions and badly understate bond returns. Yahoo's "Adj Close" is avoided because it is rewritten backwards every time a new dividend is paid.
6. **Returns are computed per ticker before dates are aligned**, so a dividend on a day another ticker did not trade is not lost. Days missing for any ticker are dropped, never filled, and the count is recorded.
7. **SPEC A0 hyperparameters, unchanged**: 50-day lookback, 64 units, Adam 0.001, batch 64, 100 epochs, seed 7, 1 bp cost, CPU. Volatility scaling, multiple seeds, 10 bp costs and the full baseline suite are later A1 work and are not part of these runs.

## How to run (after you approve it)

Install the optional data extra once (see [RUNNING.md](RUNNING.md) for creating `.venv` on each OS), then download both tiers. `--end` is exclusive, so `2026-10-22` includes 21 October 2026.

Windows (PowerShell):

```powershell
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install -e ".\research[data]"
& $py -m portfolio_lab.cli fetch-yahoo tier1 data\yahoo\tier1 --start 2006-01-01 --end 2026-10-22
& $py -m portfolio_lab.cli fetch-yahoo tier2 data\yahoo\tier2 --start 2006-01-01 --end 2026-10-22
& $py -m portfolio_lab.cli walk-forward data\yahoo\tier1\dataset\manifest.json --config research\configs\walk-forward-tier1-paper.json --output runs\tier1-paper
```

macOS and Linux:

```bash
py=.venv/bin/python
$py -m pip install -e "./research[data]"
$py -m portfolio_lab.cli fetch-yahoo tier1 data/yahoo/tier1 --start 2006-01-01 --end 2026-10-22
$py -m portfolio_lab.cli fetch-yahoo tier2 data/yahoo/tier2 --start 2006-01-01 --end 2026-10-22
$py -m portfolio_lab.cli walk-forward data/yahoo/tier1/dataset/manifest.json --config research/configs/walk-forward-tier1-paper.json --output runs/tier1-paper
```

Repeat the last command with the other three configs (`walk-forward-tier1-2026`, `walk-forward-tier2-paper` with the tier2 manifest, `walk-forward-tier2-2026`). Each output directory must be new; nothing is overwritten. Each fetch writes:

- `raw/<ticker>.csv`: the exact bytes yfinance returned
- `acquisition.json`: query options, yfinance version, retrieval time and SHA-256 of every raw file
- `dataset/manifest.json` and `dataset/prices.csv`: the validated dataset the model reads

Training time on CPU has not been measured for these sizes: about 100 epochs per fold across five to eight folds per run.

## Known limits

- Yahoo can revise history, so a later fetch may differ; the saved bytes and hashes are the record of what was used.
- Whether Yahoo ever reports the same payout in both Dividends and Capital Gains for these ETFs is unverified; the code adds them (flagged with a `shortcut:` comment).
- The model's price inputs are total-return index levels, not quoted prices. This is a declared deviation from the paper.
