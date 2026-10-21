## Context and discrepancy

The CLI uses permissive json.loads for run config and saved resume config, unlike newer control/artifact boundaries. RunConfig.validate invokes shared type validation only for raw/full-training modes. The active add-explicit-sharpe-window-diagnostic delta/task1.5 says to preserve legacy default validation scope. This change intentionally tightens malformed-input rejection for the default path as well; the valid default values, loss, objective window, normalization, batching and service/fold scopes stay unchanged. Parent integration will reconcile that older wording and shared handoff/config context.

## Decisions

- Load both explicit --config and saved resume manifest through load_json_object. Resume requires a config object; constructor TypeError becomes a ValueError describing required/declared RunConfig fields, without catching arbitrary runner TypeError.
- Validate the resulting RunConfig before calling run_experiment. This prevents malformed settings from reaching dispatch even if a downstream adapter is replaced. RunConfig.validate remains authoritative for direct callers.
- Run shared type preflight before range checks and CUDA availability. Counts/seeds are exact Python ints excluding bool; learning rate/cost are finite Python int/float excluding bool and float-overflowing integers; split endpoints/device are strings. Date membership/order remains the dataset sampler's responsibility.
- Keep valid Python integer learning-rate/cost values supported and preserve all dataclass defaults. The strict preflight adds no device probe itself.
- Do not broaden service schemas or alter training/model/loss behavior. No test/project process, import, GPU work or command is run; root owns any authorized local commits.

## Verification plan

Write CLI cases for explicit config and saved resume mapping/constructor errors, duplicate/nested duplicate fields, nonfinite and overflow tokens, malformed controls, and valid explicit/default/alternate config forwarding. Write direct-run cases forbidding dataset/runtime/training/CUDA calls on malformed default controls and retaining existing evidence. All are unrun; source inspection is the only available verification. Validate OpenSpec and run compatibility checks only after execution is authorized; no archival before those gates.
