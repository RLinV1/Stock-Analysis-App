# Cost-aware objective math prerequisite

Status 2026-10-17: **unrun isolated source only**. No tensor operation, gradient
check, model, test, import or GPU operation ran. No cost-aware runner/control,
training-window boundary policy or paired study is enabled. Current runs still
train on gross returns and apply costs in evaluation. See the
[active tasks](../openspec/changes/add-cost-aware-objective-primitive/tasks.md)
and [implementation history](../openspec/changes/add-cost-aware-objective-primitive/implementation.md).

The new `cost_objective.py` math requires an explicit `previous_target`. It must
be all cash or a normalized long-only target with matching assets/dtype/device.
For each supplied row, net return is gross target return minus cost rate times
the two-sided L1 change from the previous target. The first row uses the caller's
argument; later rows use adjacent current-window targets. This reuses the current
idealized accounting convention, with no drift, slippage or self-financing
execution model. It is not a recovered paper implementation.

`net_returns_for_objective` returns the differentiable net path.
`negative_net_sharpe` applies the existing population-variance stabilization and
epsilon to that path. No input is converted, clipped or detached. Supplying a
prior target with or without a gradient remains an explicit caller choice;
the primitive does not select how minibatches/folds should join.

Inputs must be matching real floating tensors with at least two target rows,
finite normalized nonnegative weights, asset returns above -100%, and an explicit
finite real scalar cost within 0..100bps. The normalized-target sum checks use an
absolute tolerance of `1e-6`; this is validation tolerance, not target repair.
Nonfinite/bankrupt net paths reject.
The shared gross/net stabilized-loss helper also rejects nonfinite mean, variance
or final loss: overflowing variance cannot silently look like a zero objective.
Ordinary formula/epsilon/gradient compatibility is unverified.

Future CPU gates cover hand answers, existing evaluator parity from cash, carried
target versus reset behavior, joined-window accounting, zero-cost gross/net loss
and gradient equality, finite-difference gradients away from turnover kinks,
explicit prior gradients and malformed/overflow inputs. They have not run.

Before any runner integration, separately define and record training/validation
window boundaries, previous-target/gradient policy, objective metadata and paired
protocol. Preserve current gross methods and report every outcome. A passing
math gate would not establish learning quality, realistic transaction execution,
historical performance or a preferred cost policy.
