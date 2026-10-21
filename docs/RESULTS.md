# Results: LSTM vs classical and simple portfolios (2026-10-21)

First trained results of the paper's method on Yahoo data. One seed (7), 1 bp trading cost, no volatility scaling, CPU. Treat these as a first measurement, not a conclusion: see [limits](#limits) before quoting any number.

## Setup

- **Model:** the paper's LSTM (50-day lookback, 64 units, softmax long-only weights), trained to maximize Sharpe. Adam 0.001, batch 64, up to 100 epochs, best epoch chosen on the last 10% of each training period.
- **Walk-forward:** retrain every 24 months on all earlier data; test only on the following, unseen period. Every fold's training and validation data end before its test period starts.
- **Data:** Yahoo total-return prices through 2026-10-20 ([details](HISTORICAL-DATA.md)). Tier 1 uses the raw ^VIX index, which cannot be bought. Tier 2 uses the tradable VIXY fund.
- **Strategies compared, all with the same daily accounting and 1 bp cost:**
  - **LSTM:** the paper's model.
  - **Mean-variance:** classical Markowitz. It takes the last 50 days of returns, finds the long-only maximum-Sharpe mix, and re-estimates daily ([how](../openspec/changes/archive/2026-10-21-add-classical-baseline/design.md)).
  - **60/40:** 60% VTI, 40% AGG.
  - **Equal weight:** 25% in each of the four assets.

## Results

Sharpe is annualized (√252 × daily mean / daily standard deviation, no risk-free rate). Turnover is the sum of daily absolute weight changes.

### Tier 1: ^VIX index (not investable)

| Strategy | Paper window 2011-01 to 2020-04 | Through 2026-10 | Max drawdown through 2026 |
|---|---|---|---|
| LSTM | **2.03** | **1.46** | 25.5% |
| 60/40 | 0.84 | 0.89 | 22.6% |
| Equal weight | 0.82 | 0.86 | 18.3% |
| Mean-variance | 0.13 | 0.04 | 61.5% |

### Tier 2: VIXY fund (tradable)

| Strategy | Paper window 2013-01 to 2020-04 | Through 2026-10 | Max drawdown through 2026 |
|---|---|---|---|
| LSTM | **1.09** | 0.75 | 23.4% |
| 60/40 | 0.87 | **0.91** | 22.6% |
| Equal weight | −0.51 | −0.38 | 63.7% |
| Mean-variance | −0.00 | −0.20 | 57.1% |

### After the paper only (2020-05 to 2026-10)

The 2026 runs split into the years the paper covered and the years after:

| Tier | LSTM | 60/40 | Equal weight | Mean-variance |
|---|---|---|---|---|
| Tier 1 (^VIX) | 1.44 | 0.96 | 0.92 | −0.09 |
| Tier 2 (VIXY) | **0.45** | **0.96** | −0.25 | −0.43 |

For comparison, the paper reports 1.86 for its LSTM and 0.76 for its mean-variance baseline at the same 1 bp cost without volatility scaling (Panel A).

## What this shows

1. **On the paper's window with the paper's (untradable) VIX index, the method reproduces:** Sharpe 2.03 vs the paper's 1.86, far ahead of every baseline.
2. **The tradable version is much weaker.** With VIXY the paper-window Sharpe drops to 1.09. Part of the tier 1 result comes from holding an index nobody can buy.
3. **The edge fades after 2020.** With VIXY, the LSTM's Sharpe after April 2020 is 0.45 against 0.96 for plain 60/40, and its turnover rises sharply (daily turnover 0.4-0.67 in 2022-2024).
4. **Raw classical mean-variance is the weakest strategy everywhere.** It rebalances almost as much as the LSTM, because small changes in 50-day return estimates swing its weights. This is the well-known weakness of unshrunk mean-variance, and this version is deliberately raw.
5. **Tier 1 after 2023 leans on the VIX index.** In 2026 the tier 1 model holds 57% ^VIX on average, and its volatility over the full 2011-2026 run is 23%, against 12% in the paper window. As a result, its post-2020 Sharpe of 1.44 is not achievable in practice.

## Checks that passed

- **Causality.** In all 24 fold runs, training and validation ended before the fold's test period.
- **Determinism.** Each paper-window run reproduces the matching folds of its 2026 run exactly: same best epochs, losses and allocations.
- **Accounting.** The comparison recomputed the LSTM, equal-weight and 60/40 results from saved allocations, and they matched each run report exactly.
- **Tests.** The research suite passed 706/706 on the committed code.
- **Reproducibility.** Every run's manifest records its dataset hash and source fingerprint. The code committed with these results has fingerprint `5dcb2a42eb22959b…`, matching tier1-2026, tier2-paper and tier2-2026. tier1-paper ran before `classical.py` existed, so its fingerprint (`33ba1cfcf9f0b5a8…`) differs; the training code was otherwise identical.

## Limits

- **One seed.** Run-to-run variation is unmeasured, so differences of a few tenths of Sharpe may be noise.
- **Overfitting.** In-sample daily Sharpe reaches about 0.7 by the end of training, against 0.15-0.28 on validation. The best epoch varies widely between folds (4 to 100).
- **Input drift.** Price-level inputs are standardized with training-period statistics. By 2026, VTI is about 5 standard deviations above its last fold's training mean, so the model extrapolates. The paper used price inputs too.
- **Costs left out of training.** Trading costs are charged in evaluation only, so the model never learns to trade less.
- **Not the full paper setup.** No volatility scaling (the paper's headline 1.96), no 10 bp results, and only 4 of the paper's 7 baselines.
- **Yahoo reconstruction.** The data is not the authors' unpublished data.

## Reproduce

Commands are in [HISTORICAL-DATA.md](HISTORICAL-DATA.md#how-to-run). Wall times on this PC's CPU, one thread per run (three ran in parallel):

| Run | Wall time |
|---|---|
| tier1-paper | 6.1 min |
| tier1-2026 | 14.3 min |
| tier2-paper | 3.9 min |
| tier2-2026 | 9.3 min |

Outputs are in git-ignored `runs/yahoo/` in the main checkout.
