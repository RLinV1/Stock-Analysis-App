# Implementation record

## Acquisition code, configs, tests and run guides - 2026-10-21

Branch `feat/yahoo-data-2026` from main (d8c4305). Added `research/src/portfolio_lab/yahoo.py` (tier definitions, yfinance download with explicit query options, raw byte retention with SHA-256, per-ticker total-return index, common-date alignment with dropped-date count, labelled manifest through the existing `write_dataset`/`load_dataset`), the `fetch-yahoo` CLI command, the optional `data` extra pinning yfinance 1.7.0, and four walk-forward configs under `research/configs/` (tier1/tier2 x paper window/2026). Added docs/HISTORICAL-DATA.md (decisions in plain words, run commands for Windows, macOS and Linux) and docs/RUNNING.md (Python setup per OS, Docker Compose secrets/start/health/stop, mobile client), linked from the README. The design record holds the reasoning behind every decision, as the user asked.

Verification: `pytest tests/test_yahoo.py` passed 13/13 offline with hand-calculated total-return cases, a dropped-date distribution case, invalid values, existing-output refusal before any download and a full injected tier1 fetch accepted by the existing loader. `py_compile` passed for cli.py and yahoo.py. `openspec validate add-yahoo-historical-data --strict` passed.

Not run, per the user's instruction not to run the ML model yet: the full research suite (a started run was stopped before completion, so it gives no result), yfinance installation, any real download, and all four walk-forward runs. The macOS and Linux instructions and Docker Compose steps were written from the project files and have not been executed. `compose.yaml` does not pass `PORTFOLIO_CORS_ALLOWED_ORIGINS` to the API, so the web client against Compose is documented as unsupported rather than changed here.

## Fetch and verification - 2026-10-21

On the user's instruction, installed yfinance 1.7.0 (pandas 3.0.6) into the main checkout's .venv; `pip check` reported no broken requirements. Fetched tier1 and tier2 with `--start 2006-01-01 --end 2026-10-21` (exclusive, so today's possibly incomplete bar is excluded) into git-ignored `data/yahoo/tier1-2026-10-20` and `data/yahoo/tier2-2026-10-20` in the main checkout; `git check-ignore` confirms the ignore rule.

Verification without training: both manifests load through `load_dataset`; every raw file matches its recorded SHA-256. tier1 has 5,209 rows 2006-02-06 to 2026-10-20 with 25 dates dropped (before DBC's first trading day); tier2 has 3,972 rows 2011-01-04 to 2026-10-20 with 1,260 dropped (before VIXY existed). `plan_walk_forward` (planning only) gives 5/8 folds for tier1 paper/2026 and 4/7 for tier2, with no start shifts. Largest daily moves match known events (^VIX +115.6% 2018-02-05, VIXY +43.1% 2024-08-05, VTI +12.8% 2008-10-13); VIXY's six reverse splits and VTI's 2008 split produce no jumps. Capital gains were zero for all four ETFs, so the payout shortcut cannot double count in this snapshot. Total return 2006-02-06 to 2020-12-31: AGG +89.42%, VTI +312.45%, DBC -33.25%, within 2 points of the earlier unverified data-note figures (+89.25%, +310.61%, -33.60%).

Not run: any training or walk-forward execution (task 3.2), per the user's instruction.
