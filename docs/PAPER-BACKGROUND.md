# Paper Background — Deep Learning for Portfolio Optimization

Everything you need to know about the source paper before writing reproduction code.

**Citation:** Zihao Zhang, Stefan Zohren, Stephen Roberts. *Deep Learning for Portfolio
Optimization.* arXiv:2005.13665 [q-fin.PM], cross-listed cs.LG, q-fin.CP.
v1 27 May 2020 · v2 9 Jul 2020 · **v3 23 Jan 2021 (the version this document describes).**
Oxford-Man Institute of Quantitative Finance / University of Oxford.
Related DOI `10.3905/jfds.2020.1.042` (*Journal of Financial Data Science*); arXiv prints no
journal-reference string, so exact volume/issue/pages are unconfirmed.

**Evidence note, corrected 2026-09-21:** No code/data link was identified in the cited paper. This does not prove that no author code exists elsewhere. The paper tables below are transcriptions, not independently reproduced results. The local volatility/data audit observations remain unverified; see their corrected notes.

---

## 1. The core idea

Conventional portfolio construction is a two-step pipeline: **forecast expected returns, then
optimize weights** from those forecasts (Markowitz and descendants).

The paper's argument against this: a forecasting stage minimizes a *prediction* loss, which is not
the portfolio's actual objective. Good return predictions and good portfolios are different things.

So they **delete the forecasting step**. A neural network maps market history directly to portfolio
weights, trained by gradient *ascent* on the Sharpe ratio itself. The thing you care about is the
thing you optimize.

Three supporting design choices:

1. **Trade index ETFs, not individual stocks.** The index universe is small (vs ~5000 US equities)
   and cross-asset-class indices are largely uncorrelated or negatively correlated, whereas
   individual names within a class move together — the paper cites that over 75% of stocks are
   highly correlated with the market index. They explicitly reject adding *subsector* indices as
   too correlated to add diversification. (An assumption, not a tested result.)
2. **Don't chase raw returns.** Target return *per unit of risk*, then use volatility scaling to
   dial exposure to an investor's risk preference.
3. **Not reinforcement learning.** They note the resemblance but argue RL maximizes expected
   cumulative reward (profit), and Sharpe ratio cannot be directly optimized in that framing.

---

## 2. The universe

Four instruments, one per asset class:

| Ticker | Paper's description | Asset class |
|---|---|---|
| **VTI** | US total stock index | Equities |
| **AGG** | US aggregate bond index | Fixed income |
| **DBC** | US commodity index | Commodities |
| **VIX** | Volatility Index | Volatility |

The paper calls all four "popularly traded ETFs" with high liquidity and small expense ratios,
existing for more than 15 years.

### Volatility-series identity remains unresolved

The paper names VIX without a precise tradable instrument identifier. Raw index observations and futures-based products have different economics. The [instrument note](FINDING-VIX-INSTRUMENT.md) records the question and prior unverified observations. Those observations lack saved reconstruction scripts/manifests and do not establish the authors' inputs or a mathematical ceiling on their dynamic model.

[SPEC section 8](SPEC.md#8-numerical-defaults-and-instrument-tiers) separates a non-investable fidelity hypothesis from a later-starting VIXY experiment and matched-window diagnostics. Choosing a treatment does not resolve the historical identity.

---

## 3. Architecture

**Networks compared:** fully connected (FCN), convolutional (CNN), and LSTM. They conclude LSTM
wins for daily financial data — FCN overfits badly (too many parameters, one set per input
feature); CNNs with large filters underfit, "overfiltering" inputs into oversmoothed solutions
(though they remain good candidates for high-frequency limit-order-book data); the LSTM's gating
summarizes long history with fewer trainable parameters.

> **No quantitative FCN/CNN/LSTM comparison is reported.** Only the LSTM ("DLS") appears in the
> results. This is stated experience, not a measured ablation — which means *running that ablation
> ourselves is an original contribution, not just reproduction.*

**The model actually used:**

| Component | Specification |
|---|---|
| Network | **Single LSTM layer, 64 units** |
| Inputs | Close prices **and** daily returns, per asset |
| Lookback | **50 days** |
| Feature count | 4 assets × 2 series × 50 days = **400 features** |
| Output | **Softmax**, one node per asset |
| Constraint | Long-only: `wᵢ,ₜ ∈ [0,1]`, `Σᵢ wᵢ,ₜ = 1` |
| Optimizer | Adam |
| Batch size | 64 |
| Validation | 10% of training data held out |
| Epochs | ~100 |

They keep returns alongside prices even though returns derive from prices — partly to evaluate
Equation 7, partly as momentum features. They state feature selection is not their focus, and that
they deliberately did **not** fine-tune hyperparameters, to show the end-to-end pipeline works.

**Leverage:** not permitted at the weight level (weights sum to 1). But the volatility-scaling
multiplier `σ_tgt/σᵢ,ₜ₋₁` in Equation 7 changes effective gross exposure and can push positions
above or below 1. The paper discusses no cap on this multiplier.

**Never stated:** dropout (never mentioned), learning rate value, weight initialization, gradient
clipping, **whether inputs are normalized**, sequence-to-one vs sequence-to-sequence output, seeds,
or framework. See §7.

---

## 4. The objective function

Sharpe ratio, **maximized** by gradient ascent. Risk-free rate omitted "for simplicity" (the
authors' words, an acknowledged simplification).

```
Eq 1    L = E(R_p) / Std(R_p)

Eq 2    L_T = E(R_p,t) / sqrt( E(R²_p,t) − (E(R_p,t))² )
        E(R_p,t) = (1/T) Σ_{t=1..T} R_p,t

Eq 3    R_p,t = Σ_{i=1..n} w_{i,t-1} · r_{i,t}
        r_{i,t} = (p_{i,t} / p_{i,t-1}) − 1

Eq 4    w_{i,t} = f(θ | x_t)

Eq 6    θ_new := θ_old + α · ∂L_T/∂θ          ← gradient ASCENT
```

Two details that matter for implementation:

- **Population standard deviation**, not sample — the denominator uses `1/T`, not `1/(T−1)`.
  Your existing `negative_sharpe` in `model.py` correctly uses `unbiased=False`.
- **One-step lag.** Weights formed at `t−1` apply to returns at `t`. Getting this wrong is
  lookahead bias and silently inflates every result.

### Volatility scaling and transaction costs (Equation 7)

```
Eq 7    R_p,t = Σ_i (σ_tgt/σ_{i,t-1}) · w_{i,t-1} · r_{i,t}
              − C · Σ_i | (σ_tgt/σ_{i,t-1})·w_{i,t-1} − (σ_tgt/σ_{i,t-2})·w_{i,t-2} |
```

- **σ_tgt = 0.10** (10% annualized) in every scaled result.
- **σᵢ,ₜ₋₁** is an ex-ante estimate: exponentially weighted moving standard deviation, **50-day
  window**, on `r_{i,t}`. *The EWM decay parameter is not given.*
- Cost is proportional to the daily change in **vol-scaled** traded value. Linear costs only — no
  bid-ask model, no market impact, no slippage.
- **C ∈ {0.01%, 0.1%}** — i.e. 1bp and 10bp. (The paper writes `(=1bs=0.0001)`; "bs" for basis
  point is nonstandard but 1bp = 0.01% is unambiguous.)

Note that cost is charged on the *vol-scaled* position change, so volatility scaling itself
generates turnover even for a nominally static allocation. This is why the "annual rebalance"
baselines incur any cost at all.

---

## 5. Data and evaluation protocol

| | |
|---|---|
| Range | **2006–2020**, daily |
| Test period | **2011 → end of April 2020** (includes the COVID crash) |
| Source | Not identified. Only an Oxford-Man Institute acknowledgement. |
| Split | **Expanding (anchored) walk-forward.** Retrained **every 2 years** using all data to that point. |
| Validation | 10% of training data, for hyperparameter tuning and overfitting control |

**This is not a single train/test split.** A fixed chronological holdout can be causal, but does not reproduce this walk-forward protocol. The paper's test period concatenates out-of-sample segments from successive retrains.

*Not stated:* whether the 10% validation split is chronological or random (**random would leak**),
exact retrain boundary dates, warm-start vs re-initialize at each retrain, exact first/last dates,
or dividend/split adjustment convention — which matters enormously for AGG, a bond ETF with
substantial monthly distributions.

---

## 6. Results

Metrics annualized except MDD, % of + Ret, and Ave.P/Ave.L. **The annualization factor is never
stated** (252? 260? 365?). Calmar is not reported. The proposed model is labelled **DLS**.

### Baselines, named precisely

| Name | Definition |
|---|---|
| **Allocation 1** | 25% stocks / 25% bonds / 25% commodities / 25% volatility |
| **Allocation 2** | 50% / 10% / 20% / 20% |
| **Allocation 3** | 10% / 50% / 20% / 20% |
| **Allocation 4** | 40% / 40% / 10% / 10% |
| **MV** | Mean-variance (Markowitz). 50-day moving-average estimates, daily updates, Sharpe-maximizing weights |
| **MD** | Maximum diversification (Choueifaty & Coignard; Theron & Van Vuuren). Same estimation |
| **DWP** | Diversity-weighted portfolio from Stochastic Portfolio Theory (Kom Samo & Vervuurt) |

Allocations 1–4 are fixed-ratio pension-fund-style strategies, **rebalanced annually**.

### Panel A — No volatility scaling, C = 0.01%

| Model | E(R) | Std(R) | Sharpe | DD(R) | Sortino | MDD | %+Ret | P/L |
|---|---|---|---|---|---|---|---|---|
| Allocation 1 | 0.282 | 0.303 | 0.929 | 0.136 | 2.065 | 0.142 | 0.479 | 1.193 |
| Allocation 2 | 0.249 | 0.212 | 1.173 | 0.095 | 2.616 | 0.097 | 0.483 | 1.254 |
| Allocation 3 | 0.228 | 0.256 | 0.890 | 0.116 | 1.962 | 0.122 | 0.476 | 1.183 |
| Allocation 4 | 0.152 | 0.123 | 1.228 | 0.052 | 2.932 | 0.081 | 0.505 | 1.349 |
| MV | 0.082 | 0.108 | 0.759 | 0.069 | 1.192 | 0.195 | 0.562 | 1.199 |
| MD | 0.462 | 0.523 | 0.882 | 0.239 | 1.931 | 0.273 | 0.473 | 1.182 |
| DWP | 0.051 | 0.102 | 0.493 | 0.067 | 0.740 | 0.179 | 0.549 | 1.107 |
| **DLS** | **0.313** | 0.168 | **1.858** | 0.099 | **3.135** | 0.102 | 0.537 | **1.518** |

### Panel B — Volatility scaled (σ_tgt = 0.10), C = 0.01% — **the headline**

| Model | E(R) | Std(R) | Sharpe | DD(R) | Sortino | MDD | %+Ret | P/L |
|---|---|---|---|---|---|---|---|---|
| Allocation 1 | 0.160 | 0.105 | 1.526 | 0.061 | 2.629 | 0.111 | 0.554 | 1.289 |
| Allocation 2 | 0.123 | 0.106 | 1.146 | 0.065 | 1.861 | 0.127 | 0.549 | 1.211 |
| Allocation 3 | 0.145 | 0.105 | 1.383 | 0.061 | 2.396 | **0.105** | 0.542 | 1.259 |
| Allocation 4 | 0.164 | 0.104 | 1.579 | 0.064 | 2.588 | 0.112 | **0.565** | 1.303 |
| MV | 0.112 | 0.100 | 1.120 | 0.063 | 1.767 | 0.211 | 0.561 | 1.213 |
| MD | 0.157 | 0.106 | 1.484 | 0.065 | 2.414 | 0.125 | **0.565** | 1.297 |
| DWP | 0.089 | 0.109 | 0.818 | 0.069 | 1.291 | 0.115 | 0.556 | 1.148 |
| **DLS** | **0.206** | 0.105 | **1.962** | 0.062 | **3.322** | 0.123 | 0.559 | **1.375** |

**Headline: Sharpe 1.962.** The authors claim DLS is best on all metrics here except drawdown. Be
precise about that claim — Allocation 3 beats DLS on MDD (0.105 vs 0.123), Allocations 1 and 3 edge
it on DD(R), and Allocation 4 and MD beat it on % positive returns. DLS clearly wins E(R), Sharpe,
Sortino, and P/L ratio.

### Panel C — Volatility scaled, C = 0.1%

| Model | E(R) | Std(R) | Sharpe | DD(R) | Sortino | MDD | %+Ret | P/L |
|---|---|---|---|---|---|---|---|---|
| Allocation 1 | 0.133 | 0.105 | 1.274 | 0.061 | 2.172 | 0.113 | 0.548 | 1.236 |
| Allocation 2 | 0.105 | 0.107 | 0.986 | 0.066 | 1.590 | 0.244 | 0.547 | 1.179 |
| Allocation 3 | 0.117 | 0.105 | 1.110 | 0.061 | 1.903 | 0.107 | 0.538 | 1.203 |
| Allocation 4 | 0.135 | 0.104 | 1.299 | 0.064 | 2.108 | 0.114 | 0.559 | 1.244 |
| MV | 0.019 | 0.101 | 0.191 | 0.066 | 0.293 | 0.324 | 0.537 | 1.033 |
| MD | 0.095 | 0.106 | 0.899 | 0.066 | 1.431 | 0.145 | 0.549 | 1.171 |
| DWP | **−0.083** | 0.110 | **−0.753** | 0.074 | **−1.129** | **0.627** | 0.508 | 0.880 |
| **DLS** | **0.148** | 0.105 | **1.403** | 0.063 | **2.327** | 0.125 | 0.547 | 1.272 |

### Cost sensitivity — DLS from 1bp to 10bp

| Metric | C=0.01% | C=0.1% | Δ |
|---|---|---|---|
| E(R) | 0.206 | 0.148 | −0.058 |
| Sharpe | **1.962** | **1.403** | **−0.559** |
| Sortino | 3.322 | 2.327 | −0.995 |
| MDD | 0.123 | 0.125 | +0.002 |

The authors' explanation: DLS produces better realized trade returns but adjusts positions
**daily**, accumulating far larger costs. The reallocation baselines rebalance only annually, so
their daily position changes come solely from vol-scaling and their costs stay minimal. At 10bp,
Allocations 3 and 4 become comparable to DLS. They frame this as the method surviving unfavorable
conditions; it can equally be read as the edge being turnover-dependent.

DWP collapses to −0.753 Sharpe with a 0.627 drawdown, consistent with high turnover under heavy
costs. MV degrades severely (Sharpe 0.191, MDD 0.324).

### COVID-19 behavior (§4.5, narrative only)

Diverse holdings entering 2020. After a small equity dip in early February the portfolio moved
almost entirely into bonds, with small residual equity and very small volatility/commodity
positions. By the 24 February crash it was concentrated in bonds. When bonds fell mid-March, the
*raw* weights barely moved but the *scaled* bond position dropped sharply because volatility
spiked — which the authors credit for the small drawdown.

### Sensitivity analysis (§4.6)

`Eq 8: S_i = (dL/dx_i) / max_j |dL/dx_j|` (following Moody & Saffell). Feature importance varies
over time, but **the most recent observations consistently dominate** — which the authors suggest
means a shorter lookback than 50 days may suffice. (As printed, Eq 8 lacks an absolute value in the
numerator despite being called "absolute normalised sensitivity"; likely a typesetting slip.)

---

## 7. Reproduction risk list

The paper does not specify all inputs needed for an exact independent replay. These are the decisions you must make yourself — and
**every one of them is a documented deviation in our writeup.**

| # | Gap | Why it matters | Severity |
|---|---|---|---|
| 1 | **VIX instrument** | Unresolved author-series identity; tiered experiments are a documented treatment, not proof. [Investigation](FINDING-VIX-INSTRUMENT.md) | Critical |
| 2 | **Input normalization** | Never stated. Raw 2006–2020 close prices into an LSTM, unnormalized, across four different scales, is unusual and may not train at all | 🔴 Critical |
| 3 | **Sharpe window T in the loss** | Mini-batch? Rolling window? Full training set? Unspecified | 🔴 Critical |
| 4 | **Are costs in the training objective?** | Eq 7 appears in the *results* section. If costs are evaluation-only, the model never learns to control turnover — which would explain the 10bp degradation | 🔴 Critical |
| 5 | Data source & adjustment | Original snapshot unavailable; provider/adjustment candidates and prior figures remain unverified. [Investigation](FINDING-DATA-SOURCING.md) | High |
| 6 | Validation split construction | Chronological vs random. Random leaks | 🟠 High |
| 7 | Annualization factor | 252 / 260 / 365 never given | 🟠 High |
| 8 | Learning rate | Symbolic α only | 🟡 Medium |
| 9 | EWM decay for volatility | Only the 50-day window is given | 🟡 Medium |
| 10 | Retrain specifics | Boundary dates, warm-start vs re-init | 🟡 Medium |
| 11 | Sequence output convention | Many-to-one vs per-timestep | 🟡 Medium |
| 12 | DWP parameters | Diversity parameter p and cap-weight source, for a 4-ETF universe | 🟡 Medium |
| 13 | MV specifics | Long-only constraint? Covariance regularization? Solver? | 🟡 Medium |
| 14 | **No seeds or variance reported** | With no error bars, a reproducer cannot tell whether Sharpe 1.7 vs 1.962 is a failed reproduction or normal run-to-run noise | 🔴 Critical |

Also absent: statistical significance testing on the Sharpe differences, and any FCN/CNN/LSTM
comparison table.

---

## 8. What this means for our project

**Gap #14 motivates a test.** Multiple seeds can measure sensitivity in our chosen implementation. They cannot by themselves establish the authors' run variance or whether their reported value was a lucky draw. Report the distribution and its limitations.

**Our three research objectives, in priority order:**

1. **Reproduce faithfully** where the paper is specific, and document every forced choice where
   it isn't.
2. **Report multi-seed variance** — the thing the paper omits.
3. **Resolve the VIX question honestly** — report both a tradable-proxy result and a raw-index
   result, and show the gap between them.

**The honest-result principle.** If the edge disappears under a tradable volatility instrument and
realistic costs, *that is the finding, and we publish it*. A reproduction that reports "we could not
replicate under tradable assumptions, and here is exactly why" is more valuable than one that
quietly tunes until the number matches. This is also what makes the result defensible in front of
anyone who probes it.

**What we do not claim.** Not investment advice, not a trading system, not a validated strategy.
See [PRD product boundary](PRD.md#product-boundary).
