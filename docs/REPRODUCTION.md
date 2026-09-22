# Paper audit and implementation contract

This project implements a bounded **paper-inspired** experiment, not a verified reproduction of the published performance. Reference: Zhang, Zohren, Roberts, [Deep Learning for Portfolio Optimization, v3](https://arxiv.org/html/2005.13665v3), especially equations 2-7 and section 4.3.

| Item | Paper | First implementation |
| --- | --- | --- |
| Model | One LSTM layer, 64 units; softmax portfolio weights | Same architecture; CPU default |
| Features | 50 observations; closing price and daily return per series | Same window/features; training-only standardization added and disclosed |
| Objective | Direct Sharpe optimization | Negative batch Sharpe, population variance, zero risk-free rate; 1e-8 variance floor |
| Training | Adam, batches of 64, generally 100 epochs | Same defaults; explicit seed and bounded epoch configuration; no shuffled temporal split |
| Validation | 10% training data; exact temporal selection not specified | A0 CLI: final approximately 10% of pre-test raw rows; usable target fraction differs after lookback. Explicit date boundaries can override this. |
| Test | 2011-April 2020, retraining every two years | Configurable fixed chronological holdout; no rolling retraining yet |
| Universe | VTI, AGG, DBC, VIX described as ETFs | VIX mapping unresolved; use explicit supplied universe and mark any experiment adapted |
| Baselines | Four allocations plus MV, MD, DWP | Equal-weight and 60/40 stock/bond, rebalanced daily; full original baseline suite not implemented |
| Costs | Absolute allocation changes; 1 and 10 bps examples | L1 target-weight changes times per-unit cost; initial entry from cash charged; no final liquidation charge |
| Scaling | Unscaled and volatility-targeted experiments | Unscaled only; no leverage |
| Dataset access | Original files/precise provider not supplied by the paper | Synthetic fixtures plus provenance-checked user/public data; no exact reproduction label |

## VIX and data interpretation

The paper labels VIX as an ETF without a precise tradable instrument identifier. Cboe publishes [historical VIX index data](https://www.cboe.com/tradable-products/vix/vix-historical-data); index observations do not identify the investment product used by the authors. Do not silently replace VIX with a futures-based product or treat its percentage change as achievable ETF returns. Resolving this requires original data or author clarification.

Historical runs using a different asset set remain useful method experiments. Their results must not be presented as reproducing the paper's table or as evidence that its claims are confirmed. No source used here supplies a redistribution license for vendor historical prices; downloaded data stays in ignored local data storage, with source/access/adjustment notes in the manifest.

## Timing and metrics

The A0 CLI defaults to a pre-test boundary at floor(70% of raw rows) and a training boundary at floor(90% of those pre-test rows). With 420 rows and lookback 50, validation has 30 of the 244 usable pre-test targets (about 12.3%). This is an implementation default, not a recovered paper rule. A1's validation target counts and minimum history are separately defined in [SPEC.md](SPEC.md).

Each sample ends at a decision-date close and predicts weights for the following close-to-close return. Future rows cannot enter that sample or the fitted scaler. Training target dates end before validation, which ends before testing; validation uses historical context where needed but no future targets. Executing at an observed closing price is a simplifying paper-inspired assumption; actual orders after the close cannot guarantee that price. Price adjustments may incorporate later corporate actions, so a snapshot is not necessarily a point-in-time database.

The differentiable objective uses gross returns. Reports deduct the stated target-weight-change cost. This matches a simplified target-turnover convention, not a full drift-aware execution simulator. All strategies share this convention. Initial allocation is charged from all-cash; no terminal sale is simulated. Equal-weight and 60/40 target portfolios rebalance daily, unlike the paper's annual allocation baselines.

Reports use 252 trading periods/year, population standard deviation, arithmetic-mean annualized Sharpe with a zero risk-free rate, compounded cumulative return, and drawdown relative to an initial wealth of one. Near-zero volatility yields a null Sharpe with an explanation. We report all configured seeds/costs rather than selecting the best test outcome. Learning rate 0.001, gradient clipping at 1.0, chronological minibatches, and best-validation-epoch selection are declared choices; they must not be mistaken for recovered unpublished details.

## Reproducibility boundary

One CPU thread and deterministic PyTorch algorithms are used for local reproducibility. Checkpoint equality is verified on the same environment and data. Cross-version, cross-device, and CPU/GPU bitwise identity is not promised. Content fingerprints capture the numerical source files, not just a git commit, since this directory was not a git repository at initial implementation.

## Milestone evidence

Implementation/tests and local-run results will be linked from the README and the active OpenSpec implementation record. No published return is a target the implementation must achieve.
