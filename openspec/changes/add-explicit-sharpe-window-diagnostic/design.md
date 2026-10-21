## Context

The existing negative_sharpe formula is stabilized negative mean gross return divided by population-standard-deviation-with-epsilon. The training loop updates once per chronological minibatch, merging a one-target final remainder. Validation selects on the whole validation split. The paper's intended objective window remains unresolved; this change adds a declared engineering control, not an interpretation of author behavior.

## Decisions

- Append objective_window='minibatch' to RunConfig, accepting only minibatch/full-training before device/data access. Existing default arithmetic/batch schedule remain unchanged by design.
- For full-training, use every chronological training target as one optimizer batch per epoch, independent of configured minibatch size. Continue using batch_size for inference/validation prediction. Do not include validation/test targets in training loss.
- Keep the loss formula, epsilon, clipping, optimizer and validation selection unchanged. Retain a dynamic objective declaration whose training_scope matches the requested window, and record optimizer_steps per epoch so the update-count difference is visible.
- Full-training is not gradient accumulation or a memory-saving implementation: it retains the full training graph and may require more memory. Caller settings and existing run budgets do not constitute a memory/time guarantee. No computation runs now.
- Raw and standardized local fixed-holdout modes may use either objective control, with both choices in config identity. A changed window rejects local resume while preserving evidence. Current-source local repeat validates the declared objective corresponding to config.
- Explicitly pin service and fold config adapters to minibatch, reject full-training direct folds before runtime, and keep existing group/sweep fields. Pin the learnability fixture to its original minibatch scope, which already contains one full training batch due to its fixture budget.
- A later paired study must freeze its protocol and retain both methods' results/failures. Different window modes generally change optimizer updates per epoch and are not an isolated batch-size effect; disclose that confound and do not tune on held-out outcomes.

## Verification plan and limitations

Check metadata/default parity and a hand-calculated example where mean minibatch Sharpe differs from full-window Sharpe. With configured batch size at least the training count, both controls must produce identical seeded numerical results apart from declared method metadata. Add multi-batch step-count, invalid-mode/no-runtime, changed-window resume and current raw/default repeat gates. All checks are unrun. No rolling loss window, paper reproduction or empirical conclusion is delivered.
