# Cost-aware objective prerequisite history

## Planned file-only math prerequisite — 2026-10-17

Read current evaluator cost/initial-position conventions, loss stabilization and A1 task3.7. Define an isolated explicit-prior-target tensor primitive before editing, retaining the current idealized target-turnover arithmetic and rejecting invalid inputs. Current runner/service/fold/sweep training remains gross-return/evaluation-only; no boundary policy or experiment result is accepted. Planning artifacts were written manually without validation. No imports, tensor/model/test/device/GPU/project process execution is authorized.
## Explicit-boundary tensor source written — 2026-10-17

Added isolated cost_objective.py with required previous_target, differentiable within-window target turnover/net returns and stabilized net-Sharpe loss. Source guards cover tensor shape/floating dtype/device, finite normalized targets, finite asset returns/cost and nonfinite/bankrupt net arithmetic/loss. The primitive neither converts/detaches inputs nor chooses a boundary policy. Its declaration states no runner integration and idealized target-turnover limitations. No current objective/config/request route changed. No tensor/import/test/model/device/GPU/process execution occurred; all numerical/gradient verification remains open.
## Intermediate-moment source guard — 2026-10-17

Source arithmetic review caught a finite-result trap: overflowing variance can make a finite zero loss through division by infinity. The new isolated primitive now rejects nonfinite mean/variance before forming its loss. Add a float32 finite-return/overflowing-variance case alongside the planned gradient tests. No tensor or numerical code ran. The existing gross objective is unchanged here; its finite-intermediate review is a separate follow-through concern.
## Cost math regression source written — 2026-10-17

Added fixed hand-accounting/evaluator parity and stabilized-loss checks, explicit carried-window handoff versus cash reset, zero-cost loss/gradient equality and smooth softmax finite-difference gradient cases. Invalid scalar/tensor/dtype/shape/target/return/bankruptcy and finite-return/overflowing-variance cases are written. No tensor operation, autograd/gradient check, test, source import, training, model or GPU/process execution ran. Expected numerical/gradient properties remain unverified; current runner methods remain gross-return only.
## Planned shared stabilized-loss guard — 2026-10-17

Share the new net primitive's finite-moment checks with the existing gross loss through one model helper, owned alongside add-walk-forward-training's numerical correction. The loss formula/epsilon stays unchanged and no cost-aware route is enabled. Preserve the net overflow case and add ordinary exact loss/gradient equality checks. No tensor/model/test/process will execute.
## Shared loss guard and explicit-gradient source written — 2026-10-17

The isolated net loss now uses the common guarded stabilized-loss helper instead of duplicating the formula/finite checks. Added unrun CPU/meta device-mismatch and explicit prior-target gradient-preservation cases without requiring a GPU tensor. Existing net/evaluator/boundary/zero-cost/finite-difference/overflow assertions remain unrun. No boundary/gradient-detachment policy or cost-aware runner route was selected or enabled; no project/tensor/model/test/GPU/process executed.
## Primitive source guide and canonical boundary — 2026-10-17

Added COST-OBJECTIVE-PRIMITIVE.md and formula/window/annualization declarations, with explicit idealized accounting, prior-target/gradient choice and no runner integration or selected boundary policy. README, SPEC, DESIGN and HANDOFF link this source-only prerequisite; current gross-training/evaluation-only-cost routes and unrun gradient/numerical status remain explicit. No link/OpenSpec validation, imports, tensor/autograd/model/test/device/GPU or project/storage process ran.
