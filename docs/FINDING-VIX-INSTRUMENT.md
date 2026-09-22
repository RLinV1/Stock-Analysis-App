# Volatility instrument investigation

Corrected 2026-09-21. **Unverified research observations; author input identity unresolved.** This replaces the earlier conclusion that an audit established how the authors constructed their data.

## Established distinction

The [paper](https://arxiv.org/html/2005.13665v3) names VIX without a precise tradable proxy. VIX index observations and futures-based products are different series. The [VIXY issuer](https://www.proshares.com/our-etfs/strategic/vixy) describes futures exposure and explicitly distinguishes it from VIX. This justifies separate experiments; it does not establish the authors' data or invalidate their result.

## Prior observations retained for reproduction

The earlier audit reported these daily-constant-weight comparisons over a claimed 2011-01-03 to 2020-04-30 window:

| Allocation | Claimed index volatility | Paper volatility | Claimed VIXY volatility | Claimed index mean return | Paper mean return | Claimed VIXY mean return |
|---|---|---|---|---|---|---|
| 1 | .298 | .303 | .133 | .244 | .282 | -.073 |
| 2 | .208 | .212 | .086 | .228 | .249 | -.026 |
| 3 | .252 | .256 | .120 | .195 | .228 | -.059 |
| 4 | .097 | .123 | .050 | .145 | .152 | .018 |

These are **not verified project results**. No reconstruction script, exact input manifest, or saved output was found in the review. Prior reported VIXY total return -99.61%, VXX/VIXY correlation .987, tracking gap .35 percentage points/year, average index/proxy gap about 52 percentage points/year, and static Sharpe optima 1.219/2.072 share this limitation. Do not cite them as measurements established by this repository.

The fourth row has positive expected return in both variants. The earlier “wrong sign on every expected return” wording was incorrect.

## Withdrawn conclusions

A dynamic long-only portfolio is not bounded by the full-period return of the best individual asset or by a static-weight optimum. A returns +10% then -10%, B returns -10% then +10%: each ends at -1%, while switching A to B yields +21%. This arithmetic counterexample says nothing about predicting that switch. The earlier claim that 31.3% was mathematically impossible is withdrawn.

Volatility products do not mechanically lose money in every period. No quantitative statement about model allocation, proxy performance, or the paper's attainable returns follows without the actual experiment.

## Outstanding evidence

1. Save acquisition/adjustment code, source/access notes, exact dataset hashes and calculation scripts.
2. Reconcile annual rebalancing stated by the paper with the earlier daily-constant-weight reconstruction. The earlier annual-rebalance numbers (.143 mean/.382 volatility) are also unverified.
3. Establish actual available trading dates and corporate-action handling. A product beginning in 2011 cannot train a model before 2011.
4. Run the documented fidelity hypothesis and explain discrepancies. A close numerical match is evidence of consistency, not proof of source identity.
5. Seek author clarification if warranted; no messages are authorized by this document.

## Experimental treatment

[SPEC.md section 8](SPEC.md#8-numerical-defaults-and-instrument-tiers) defines the dates and minimum history:
- Tier 1: raw index, explicitly not investable.
- Tier 2: VIXY throughout with later evaluation; no VXX splice by default.
- Tier 3: three-asset diagnostic on the same dates as Tier 2.
- Compare matched-window reruns with common protocol, costs and seeds. Report allocation distributions as observations; equal performance alone does not prove a sleeve never contributed.

Publication may state what was tested and what remains unknown. Do not claim a flaw in named researchers' work from these provisional tables.
