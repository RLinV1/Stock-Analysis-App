## Context

The existing features interleave each asset's price and simple return. A target at indexi uses only rowsi-lookback throughi-1. Train-only standardization fits through the row preceding the final training target. A1 task3.5 requests a normalization experiment; current execution is prohibited and the paper's exact preprocessing remains unknown.

## Decisions

- Add `normalization: str = "train-only"` at the end of RunConfig to preserve existing positional fields/default behavior. Accept only train-only/raw, including before any device probe. Include the field through existing config identity/checkpoint/model serialization; current source fingerprints still prevent silently replaying old source.
- Add the same keyword-only choice to make_samples. Keep the train-only branch's existing operations unchanged. Raw mode uses a zero mean and unit scale with the same feature/target construction and float32 conversion. These arrays are explicit identity-transform metadata, not fitted statistics.
- Disclose the selected mode in manifest deviations. Fixed-holdout raw runs can use existing local repeat/resume with exact config identity. Changing modes must reject resume without replacing retained evidence.
- Preserve the closed synthetic service request: explicitly pass train-only in its adapter. Walk-forward group/sweep configs retain their current explicit fields and standardization; reject raw direct-fold execution rather than accidentally extending the fold protocol before its own acceptance work.
- Freeze a future paired study before execution; this change provides controls and regression gates only. Do not choose raw/standardized based on held-out outcomes or claim that one trains better.

## Risks and limitations

Raw price scales can saturate the LSTM or fail finite float32 conversion. Reject overflow through the existing finite-sample guard; do not silently normalize or clip. Current-source run identity now records the mode, so freshly generated metadata/repeat/resume and service/fold compatibility require execution. This is not rolling normalization, a cost-aware objective or historical evidence.
