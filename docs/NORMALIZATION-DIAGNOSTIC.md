# Explicit normalization diagnostic controls

Status 2026-10-17: **unrun source only**. Sampler/runner controls and regression
cases are written; no import, test, model or GPU operation ran. This does not
complete A1's normalization study or select a preferred method. See the
[active tasks](../openspec/changes/add-explicit-normalization-diagnostic/tasks.md)
and [implementation history](../openspec/changes/add-explicit-normalization-diagnostic/implementation.md).

Local fixed-holdout RunConfig now records `normalization`:

| Value | Features and retained transform |
|---|---|
| `train-only` | Existing price/simple-return features standardized using prior training inputs only; default behavior preserved by design |
| `raw` | The same prior-window price/simple-return features without fitted standardization; recorded mean0 and scale1 |

Both use the same chronological masks, next-return targets and float32 conversion.
Raw inputs can saturate the LSTM or overflow float32. The source rejects nonfinite
samples; it does not silently standardize, clip or switch modes. The gross-return
objective, optimizer, validation model selection and evaluation-only costs are
unchanged by this control.

Preserving the default here means preserving valid train-only calculations by
design. It does not establish current-source compatibility, unchanged acceptance
of malformed settings, or compatibility with artifacts from earlier source.
Configuration/source identity and resume/repeat checks still apply.

The existing local `portfolio-lab run DATASET --config SETTINGS --output OUTPUT`
path accepts the recorded RunConfig field. Use actual dataset split dates and
declare the full intended experiment settings before execution. There is no new
normalization CLI flag, accepted seed/cost grid or automatic paired study.
Configuration identity, checkpoint identity, model config and manifest deviations
retain the chosen mode. A changed-mode resume must reject while preserving prior
evidence. Fresh raw runs can use the bounded same-environment local repeat path;
that is not external replay verification.

The closed synthetic service request has no new option: its adapter explicitly
selects `train-only`. Walk-forward groups and sweeps keep their current config and
preprocessing scope. Direct raw fold execution is rejected before dataset/device
or training access. Extending raw preprocessing to folds would require its own
scope and verification.

After explicit process authorization, verify default parity, raw feature/target
alignment, causal mutations, finite conversion rejection, service/fold boundaries
and actual raw run/repeat/resume. Broader compatibility must pass before claiming
the controls work. Separately freeze the paired normalization study's data,
settings, training/validation comparison and held-out protocol; retain both modes'
failures and results without choosing or tuning against held-out outcomes.
