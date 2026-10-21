## Context

SPEC section 8 already defines the tiers and the paper's evaluation window; FINDING-DATA-SOURCING defines the snapshot contract and the adjustment formula. This change implements them for Yahoo and extends the evaluation end to 2026. The user asked for the thought process behind each decision, so each decision below states the choice, the reason and the risk. The user-facing explanation is in [HISTORICAL-DATA.md](../../../docs/HISTORICAL-DATA.md).

## Decisions

### 1. Source: Yahoo Finance through yfinance (user choice)
- **Why:** free, covers every ticker back to 2006, and was already the project's candidate source.
- **Risk:** Yahoo's terms do not allow redistribution, and Yahoo can revise history. Raw downloads and datasets therefore stay in git-ignored `data/`; only code, configs, hashes and documentation are committed. A later fetch may not match byte-for-byte, which is why the exact bytes are kept and hashed.

### 2. "The paper's original data" means a reconstruction
- **Why:** the authors never published their dataset or its source. The closest honest option is the same tickers and dates, downloaded from Yahoo.
- **Consequence:** every manifest says it is not the authors' data. Matching or missing the paper's Sharpe of 1.962 on this data cannot prove or disprove the paper.

### 3. Two volatility tiers, both run (user choice)
- **Tier 1, raw ^VIX:** closest to the paper's text ("VIX"), but the index cannot be bought, so returns earned from it are not achievable. Labelled NOT INVESTABLE.
- **Tier 2, VIXY:** a real ETF that tracks short-term VIX futures. It is tradable but behaves very differently (it loses value over time), and its history starts in January 2011, so training starts later.
- **Why both:** comparing them shows how much of any result depends on holding something that cannot be traded.

### 4. Two evaluation windows per tier
- **Paper window:** test from 2011-01-01 (tier 1) or 2013-01-01 (tier 2, so VIXY has enough training history) through 2020-04-30, the paper's last test date.
- **Extended window:** same starts, test through the latest downloaded date in 2026. The config says 2026-12-31; the existing planner clamps the end to the last available date, so the same config keeps working after a re-fetch.
- **Why the same start:** the extended run then contains the paper window as its first part, so the 2020-2026 period can be compared directly against it.

### 5. Total-return prices, not raw close
- **Why:** AGG and VTI pay regular distributions. Raw close ignores them and badly understates bond returns (the data note records about 18% raw vs about 89% total return for AGG over the paper period, unverified). The paper does not say which it used; total return is the economically correct choice for a portfolio.
- **How:** download with `auto_adjust=False, actions=True, repair=False`. Yahoo's Close is already split-adjusted, and so are its Dividends. Each day's gross return is (Close_t + Dividends_t + Capital Gains_t) / Close_{t-1}, compounded from 100. This is the formula already in FINDING-DATA-SOURCING.
- **Why not Yahoo's Adj Close:** its dividend adjustment is recomputed backwards from today, so old values change whenever a new dividend is paid. Building the index from the raw fields keeps the method explicit and testable.
- **Risk:** the model's price features become total-return index levels, not quoted prices; this is recorded as a deviation. Whether Yahoo's Dividends and Capital Gains columns ever double count for these ETFs is unverified; the code adds them and the code comment flags it.

### 6. Compute returns per ticker first, then keep common dates
- **Why:** if returns were computed after dropping dates, a distribution paid on a dropped date would be lost. Computing each ticker's index on its own full calendar and then keeping only dates where all four exist preserves every distribution in the next retained return.
- **Missing data:** the loader's only policy is "reject" (no filling). Dates where any ticker is missing are dropped, and their count is recorded in the manifest deviations. Nothing is forward-filled or invented.

### 7. Hyperparameters come from SPEC section 8 A0
- 50-day lookback, 64-unit LSTM, Adam 0.001, batch 64, 100 epochs, seed 7, cost 1 bp, CPU.
- **Why:** these are the paper's stated values where it gives them and the project's recorded defaults where it does not. Using them unchanged keeps this a test of the method, not of new tuning.
- **Not included:** volatility scaling (Equation 7), multiple seeds, 10 bp costs and the full baseline suite. SPEC lists these as later A1 work, and this change does not claim them.

### 8. Offline tests with an injected download function
- **Why:** unit tests must not depend on the network or on Yahoo staying the same. The download function is a parameter; tests pass hand-written CSV text in the shape yfinance writes, with hand-calculated expected returns.

### 9. Nothing runs yet (user instruction)
- yfinance is an optional extra and is not installed here. No fetch, training or walk-forward run happens. The commands are documented for when the user approves them.
