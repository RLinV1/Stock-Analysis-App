# Historical data through 2026

Status 2026-10-21: both tiers were downloaded through 2026-10-20 and verified (below). **No model has been trained on them yet** (the user asked to hold off), so nothing here is a model result.

## Downloaded snapshots (local only, git-ignored)

| Tier | Folder | Rows | First → last date | Dates dropped |
|---|---|---|---|---|
| tier1 | `data/yahoo/tier1-2026-10-20` | 5,209 | 2006-02-06 → 2026-10-20 | 25 (before DBC started trading on 2006-02-06) |
| tier2 | `data/yahoo/tier2-2026-10-20` | 3,972 | 2011-01-04 → 2026-10-20 | 1,260 (2006-2010, before VIXY existed) |

Checks that passed: the project loader accepted both datasets; every raw file matches its recorded SHA-256; the fold planner (planning only, no training) gives 5 folds for tier1-paper, 8 for tier1-2026, 4 for tier2-paper and 7 for tier2-2026, with no start-date shifts. The largest one-day moves are real market events (VTI +12.8% on 2008-10-13, ^VIX +115.6% on 2018-02-05, VIXY +43.1% on 2024-08-05), and VIXY's six reverse splits cause no jumps. Capital gains were zero for all four ETFs, so payouts cannot be double counted in this snapshot.

Cross-check against the earlier, unverified [data note](FINDING-DATA-SOURCING.md) figures for 2006-02-06 → 2020-12-31: AGG +89.42% (note: +89.25%), VTI +312.45% (note: +310.61%), DBC −33.25% (note: −33.60%). The small differences are consistent with Yahoo revising history between fetches.

What the raw numbers already show, before any model: raw ^VIX ends the tier1 period up 32.7%, while VIXY loses almost 100% of its value from 2011 to 2026. Holding the tradable volatility asset is very different from holding the index the paper names.

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

## How to run

Install the optional data extra once (see [RUNNING.md](RUNNING.md) for creating `.venv` on each OS), then download both tiers. `--end` is exclusive: set it to today's date so a possibly incomplete bar for today is left out. The snapshots above used `--end 2026-10-21`. Each output folder must be new, so pick a fresh name for a re-fetch. The walk-forward commands train the model; they have not been run yet.

Windows (PowerShell):

```powershell
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install -e ".\research[data]"
& $py -m portfolio_lab.cli fetch-yahoo tier1 data\yahoo\tier1-2026-10-20 --start 2006-01-01 --end 2026-10-21
& $py -m portfolio_lab.cli fetch-yahoo tier2 data\yahoo\tier2-2026-10-20 --start 2006-01-01 --end 2026-10-21
& $py -m portfolio_lab.cli walk-forward data\yahoo\tier1-2026-10-20\dataset\manifest.json --config research\configs\walk-forward-tier1-paper.json --output runs\tier1-paper
```

macOS and Linux:

```bash
py=.venv/bin/python
$py -m pip install -e "./research[data]"
$py -m portfolio_lab.cli fetch-yahoo tier1 data/yahoo/tier1-2026-10-20 --start 2006-01-01 --end 2026-10-21
$py -m portfolio_lab.cli fetch-yahoo tier2 data/yahoo/tier2-2026-10-20 --start 2006-01-01 --end 2026-10-21
$py -m portfolio_lab.cli walk-forward data/yahoo/tier1-2026-10-20/dataset/manifest.json --config research/configs/walk-forward-tier1-paper.json --output runs/tier1-paper
```

Repeat the last command with the other three configs (`walk-forward-tier1-2026`, `walk-forward-tier2-paper` with the tier2 manifest, `walk-forward-tier2-2026`). Each output directory must be new; nothing is overwritten. Each fetch writes:

- `raw/<ticker>.csv`: the exact bytes yfinance returned
- `acquisition.json`: query options, yfinance version, retrieval time and SHA-256 of every raw file
- `dataset/manifest.json` and `dataset/prices.csv`: the validated dataset the model reads

Training time on CPU has not been measured for these sizes: about 100 epochs per fold across five to eight folds per run.

## Known limits

- Yahoo can revise history, so a later fetch may differ; the saved bytes and hashes are the record of what was used.
- The code adds Dividends and Capital Gains. Capital gains were zero for all four ETFs in this fetch; recheck before adding other tickers (flagged with a `shortcut:` comment).
- The model's price inputs are total-return index levels, not quoted prices. This is a declared deviation from the paper.
