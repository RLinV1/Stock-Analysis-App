## Decisions

### 1. Mean-variance as the classical model
- **Why:** it is the textbook forecast-then-optimize method and the paper's MV baseline: 50-day moving estimates, updated daily, Sharpe-maximizing weights.
- **Choices the paper leaves open** (SPEC risk 13): long-only and fully invested, matching the LSTM's softmax constraint so both face the same rules; no covariance shrinkage; no risk-free rate, matching the paper's Sharpe objective. This is a raw textbook MV and deliberately not a practitioner-hardened one.

### 2. Exact subset solver instead of a general optimizer
- **Why:** for long-only maximum Sharpe, the optimal nonzero weights equal the unconstrained tangency solution on that subset. With 4 assets there are 15 subsets, so checking all of them is exact, fast and deterministic, with no starting point, tolerance or convergence failure. SciPy's SLSQP is local and approximate and would run about 2,000-4,000 times per run.
- **Fallback:** single assets are always candidates, so all-negative means still give a valid portfolio (the best single asset). A window where every asset has zero volatility raises an error instead of inventing weights.
- **When to switch:** many assets (subsets double per asset) or extra constraints such as weight caps; then SciPy is the right tool.
- **SciPy's role:** installed at the user's request and used in tests as an independent cross-check; the exact solver matched or beat SciPy's best of four starts on 25 random four-asset cases.

### 3. Compute after training, on the run's own test dates
- **Why:** MV needs no training, so it runs on a finished walk-forward run instead of changing the training pipeline and its strict fold contracts. It uses the run's dataset snapshot, test dates, float32 target returns and cost, and the same `continuous_results` accounting.
- **Self-check:** the command recomputes the run's recorded strategies (LSTM, equal-weight, 60/40) from `allocations.csv` and refuses to write unless their metrics match the run report exactly. This proves MV is scored with identical accounting.
- **Causality:** weights for target day t use only the 50 returns into days t-50 to t-1, the same one-day lag as the LSTM; a test changes later prices and checks earlier weights stay identical.

### 4. Outputs never overwrite
- The comparison JSON is created exclusively; existing files and run directories are never modified.
