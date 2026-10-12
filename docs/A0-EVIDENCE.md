# A0 local execution evidence

Recorded 2026-10-09. **Synthetic engineering evidence only.** These runs do not establish historical investment performance or reproduce the paper's result table.

## Retained artifacts

- [Machine-readable evidence](../runs/cpu-evidence-2026-10-09-a3ea8ef5/evidence.json)
- [Reference manifest](../runs/cpu-evidence-2026-10-09-a3ea8ef5/runs/20261009T213904-c7dc4165d298/manifest.json) and [reference report](../runs/cpu-evidence-2026-10-09-a3ea8ef5/runs/20261009T213904-c7dc4165d298/report.json)
- [Fresh-repeat comparison](../runs/cpu-evidence-2026-10-09-a3ea8ef5/repeats/repeat-44c0cc0bf9244bce8a97c2daedab9b2e/comparison.json)
- [Resume comparison](../runs/cpu-evidence-2026-10-09-a3ea8ef5/resume-comparison.json)
- [Resumed run report](../runs/cpu-evidence-2026-10-09-a3ea8ef5/runs/20261009T213922-bf412bf7d03d/report.json)

Artifacts are local ignored outputs under runs/, not committed vendor data. The evidence JSON retains configuration, environment, source/data identities and reference artifact checksums. It also records all three strategy metrics; none is a historical headline result.

## Fixed smoke configuration

| Setting | Value |
|---|---|
| Dataset | 420 synthetic weekday observations, generator seed 2026, three assets |
| Model | Single LSTM layer, 64 units, 50-observation inputs |
| Training | Three epochs, batch size 64, learning rate 0.001, seed 7 |
| Costs | 1 bps per unit of two-sided target turnover |
| Splits | 214 training / 30 validation / 126 test targets |
| Strategies | LSTM, equal-weight, stock/bond 60/40 |
| Device | CPU, one PyTorch thread |
| Environment | Python 3.12.14; PyTorch 2.8.0+cpu; NumPy 2.2.6; psutil 7.0.0; filelock 3.32.6 |

These values were recorded before examining the result. This is one bounded smoke configuration, not a parameter search or a multi-seed research finding.

## Measured outcomes

| Check | Observed result |
|---|---|
| Reference run call, including setup | 5.899 seconds |
| Runner training/evaluation timer | 0.421 seconds |
| Maximum sampled process RSS | 284.81 MiB |
| Fresh repeat | matched; maximum absolute difference 0; 3987 compared values |
| Completed-epoch interruption | Stopped after epoch 1; resumed to epoch 3 |
| Resumed versus uninterrupted outputs | matched; maximum absolute difference 0 |
| Original reference artifacts | Byte hashes unchanged after repeat |
| Resumed manifest | Original bytes unchanged |
| Combined test suite | 59 passed in 54.22 seconds |
| GPU | Not exercised; installed PyTorch build is CPU-only |

RSS is sampled at startup, epoch boundaries and completion. It is not a continuously measured peak or a prediction of full Compose memory use. The runner's timer excludes some initialization and serialization; the outer call measurement includes setup. Neither is a repeated performance benchmark.

Repeat was exercised through the actual CLI in a separate process. The comparison uses absolute tolerance 1e-7, relative tolerance zero, and exact dates/counts/order/null explanations. Resource measurements and generated run IDs are excluded. The full reports retain numerical differences.

## Provenance and limitations

Git commit: eab38cc573db43c27ed97bc2420580a57b78464d. Source dirty: true, because the new implementation is uncommitted. Numerical source fingerprint: f638a03ff9bc5ec92b99fd87f4a9ece30f669f24a8cfb21fd4c9d6291c1f5f33. Dataset content SHA-256: d9544df02117eef131d55046377a950c7a6980ab4949dc13b775fdd8c29099e4.

The commit alone does not retrieve this dirty source. A0 fingerprints and local comparisons are not the complete source snapshots, dependency locks, artifact integrity chain or external v2 verification planned for A1. Model/checkpoint files are present but not deserialized or authenticated by repeat.

Local inspection found no provenance-validated historical snapshot available for this continuation. No market data was fetched or evaluated; original input-provider/volatility-series assumptions remain unresolved. This is an explicit synthetic-only outcome, not a claim that historical data cannot be obtained. Historical seed/cost comparisons (A0 task 4.2) remain unfinished.

## Re-run

The [README quickstart](../README.md#run-the-local-prototype) generates a fresh dataset and runs the same small CLI configuration. The saved [config](../runs/cpu-evidence-2026-10-09-a3ea8ef5/config.json) supplies exact split dates for the retained run. Use its copied dataset for repeat; changing numerical source/runtime requires a new reference experiment rather than relabelling incompatible inputs.
