## Scope

Request v1 uses only the project's generated three-asset data and A0 fixed holdout. Fields are explicit: `contract_version`, `dataset` (`kind`, `observations`, `seed`), `model` (`lookback`, `hidden_size`, `epochs`), and `execution` (`seed`, integer `cost_bps`). Unknown fields and unsupported versions fail closed. Conservative limits (140–420 rows, 10–50 lookback, 8–64 hidden units, 1–3 epochs) keep one CPU experiment small. The example is deliberately one epoch.

`batch_size=32`, `learning_rate=0.001`, and `device=cpu` are recorded adapter constants. Train/validation cutoffs use the current CLI's `pretest=floor(0.7*n)` and `train=floor(0.9*pretest)` on the generated ordered dates. The execution writes its copied dataset and existing A0 manifest/report in a normal run directory. The request and its SHA-256 are saved alongside it, not inserted into the A0 manifest or labelled v2.

## Identity and validation

The hash is SHA-256 of UTF-8 JSON with sorted keys, compact separators and no NaN/Infinity. All numeric request fields are integers, so Java and Python can agree on canonical bytes without floating-point serialization rules. A later Java API must verify this against shared fixtures before using it for idempotency. The Python validator independently checks the schema's supported shape and range; schema equivalence is tested against its declared properties, required sets and bounds. JSON Schema is the published cross-runtime contract; this implementation does not claim a separate JSON Schema engine has validated it.

Validation happens before creating output directories. A staging directory under the chosen output root holds generated input during execution and is removed after success or failure; `run_experiment` retains its own dataset copy. The local CLI does not enqueue, retry or claim jobs.

## Verification and limitations

Unit tests cover unsupported versions, missing/extra fields, booleans, out-of-range integers and canonical key-order independence. An integration test executes one 140-row, one-epoch request and checks the retained request, digest, manifest and completed report. Existing 59 research tests must still pass. The hash is not a provenance guarantee and the generated data is not historical market data.
