## 1. Documentation (this change)

- [x] 1.1 Fetch and read arXiv:2005.13665v3 in full
- [x] 1.2 Write `docs/PAPER-BACKGROUND.md` with architecture, loss, protocol, all result panels, and the reproduction risk list
- [x] 1.3 Write `docs/PRD.md` with positioning, personas, user stories, acceptance criteria, scope, non-goals, risks
- [x] 1.4 Write `docs/SPEC.md` with run manifest contract, API, schema, ONNX boundary, testing, parameter defaults
- [x] 1.5 Rewrite `DESIGN.md` for the Java/Spring Boot and Expo stack
- [x] 1.6 Record the HANDOFF, DESIGN.md, and config.yaml discrepancies in the proposal
- [x] 1.7 Update `openspec/config.yaml` context: Kotlin/Quarkus → Java/Spring Boot, Kotlin Android → Expo
- [x] 1.8 Update `AGENTS.md` required-stack line to match
- [x] 1.9 Update `openspec/HANDOFF.md` to reflect actual state, including that research code exists
- [ ] 1.10 User review and acceptance of proposed defaults (licensing, manifest schema, parameter defaults, seed list)

## 2. Blocking research audits

- [x] 2.1 Write the volatility investigation note. Corrected 2026-09-21: prior figures remain unverified; this checkbox records document delivery, not a completed empirical audit.
- [ ] 2.1a Reconstruct and resolve the annual-versus-daily rebalancing discrepancy before attributing a specific implementation to the paper.
- [ ] 2.1b Run Tier 1 and explain agreement or divergence with Table 1; do not tune held-out results to force a match.
- [x] 2.2 Write the data investigation note. Corrected 2026-09-21: provider permissions and adjustment measurements remain unverified; no universal redistribution prohibition is established.
- [ ] 2.3 Record both outcomes as deviations with rationale
- [x] 2.4 Record provisional instrument/data treatments in SPEC section 8, explicitly preserving unknown author inputs and unverified acquisition/adjustment.

## 5. Additional documentation (this change, added after audits)

- [x] 5.1 Write `docs/SECURITY.md` — threat model, findings against actual code, phase-gating milestones
- [x] 5.2 Write `docs/READINESS.md` — the gate before implementation, with Definition of Done for Phase A
- [x] 5.3 Write `README.md` — public face for humans, with an AI-agent orientation section
- [x] 5.4 Verify all internal documentation links resolve (0 broken)
- [ ] 5.5 Complete milestone-specific security checks before dependency upgrades, network exposure or publication; local synthetic implementation is not gated on all future checks.

## 3. Phase A1 — research (subsequent implementation change)

- [x] 3.1 `protocol.py` — expanding walk-forward fold generation, 24-month retrain boundaries (standalone planner delivered in 2026-10-15-add-walk-forward-protocol; training orchestration remains 3.11).
- [x] 3.2 Causality tests that deliberately attempt lookahead and assert failure (fold/sample tests delivered; end-to-end multi-fold training checks remain 3.11).
- [ ] 3.3 `baselines.py` — Allocations 1–4, MV, MD, DWP on shared data, folds, and cost model
- [ ] 3.4 Synthetic-data test with a known optimal allocation; assert the model approaches it
- [ ] 3.5 Input-normalization experiment (gap #2) — establish whether the model trains at all
- [ ] 3.6 Sharpe-window experiment (gap #3)
- [ ] 3.7 Costs-in-loss versus evaluation-only experiment (gap #4)
- [ ] 3.8 `sweep.py` — multi-seed and cost sweeps
- [ ] 3.9 Manifest emission and verification round-trip
- [ ] 3.10 Findings writeup with honest result, whatever direction it falls
- [ ] 3.11 Integrate fold plans into A1 training/evaluation with frozen per-fold model/scaler, retained versions and end-to-end future-mutation tests before claiming walk-forward model execution.

## 4. Verification

- [x] 4.1 `openspec validate` passes for this change
- [x] 4.2 Documentation cross-references resolve (no links to missing files)
- [x] 4.3 Reconcile current documents so planned capabilities are labelled; preserve superseded assertions only in historical review/implementation records

## Notes

## 10. User-supplied UI direction and test preparation — 2026-10-09

Scope: preserve and apply the attached apple-design guidance to planned Expo/Android and web UI. Keep the approved stack, native Android navigation and honest experiment states. The user requested thorough preparation/testing and continuation on GPT-6-Sol after this phase.

- [x] 10.1 Preserve the supplied skill text and document native/web adaptations, screen flows, visual/interaction rules and accessibility requirements.
- [x] 10.2 Add behavioral UI deltas and explicit automated/manual acceptance checks; distinguish planned checks from executed research tests.
- [x] 10.3 Reconcile current evidence, requirements and handoff, then validate the OpenSpec/documentation updates before model continuation.

## 9. Final implementation readiness — 2026-09-21

Scope: independently check research and architecture, inspect installed tools without starting services, correct residual planning contradictions, and provide a concrete delivery sequence. Preserve required A1/B/C/D scope; stage a first usable synthetic app slice before the full research program. Minor research packaging/comment cleanup is owned by reproduce-portfolio-learning section 5.

- [x] 9.1 Record independent research/architecture findings and local environment evidence, distinguishing architecture readiness from runnable full-stack verification.
- [x] 9.2 Reconcile current planning artifacts and document the first usable slice, milestone dependencies and acceptance checks.
- [x] 9.3 Run strict OpenSpec and document consistency checks, reconcile the handoff, and deliver the readiness verdict and game plan.

## 8. Stack and architecture sign-off review — 2026-09-21

Scope: verify approved technologies against primary documentation, clarify daily inference versus retraining, and correct deployment/worker assumptions. No install, account creation, paid plan, connectivity or implementation is authorized by this review.

- [x] 8.1 Verify compatibility assumptions and record an approval/verification matrix in DESIGN and TOOLCHAIN.
- [x] 8.2 Reconcile LocalStack prerequisites, Windows K3s path, worker lease enforcement and research cadence across planning contracts.
- [x] 8.3 Validate OpenSpec and documentation links; record what is approved versus still awaiting implementation evidence.
- [x] 8.4 Provide the requested tech-stack image, labelling the architecture as planned and K3s/ONNX as later work.

## 7. Apply review corrections — authorized 2026-09-21

The user requested fixing the review. Reconcile the newer Spring Boot/Expo design across current instructions; correct unsupported research assertions; specify tier dates, durable jobs, and verification; keep existing code unchanged and distinguish design from implementation. License/publication approval and actual historical verification remain separate.

- [x] 7.1 Reconcile stack, milestone ownership, current state, and agent handoff.
- [x] 7.2 Correct research claims, evidence labels, tier dates, data snapshot and publication rules.
- [x] 7.3 Define worker lifecycle, canonical API/schema, manifest replay and inference requirements; synchronize behavioral deltas.
- [x] 7.4 Align readiness/security/toolchain guidance; scan links and contradictions and run strict OpenSpec validation.

## 6. Requirements review requested 2026-09-21

Scope: review the updated documents against each other, the latest user instructions, and actual source. Record actionable findings and verification without choosing a disputed stack or implementing the proposed architecture.

- [x] 6.1 Inspect requirements, active OpenSpec artifacts, source, and evidence; check document links, strict validation, and existing tests.
- [x] 6.2 Write a prioritized review with concrete corrections, distinguishing confirmed defects from unresolved choices.
- [x] 6.3 Reconcile handoff and implementation evidence with this review; preserve unresolved requirements as open.

The review ran 17 existing tests successfully. These document corrections change no numerical code, so tests are not repeated solely for wording changes. Publication/license choices and actual research/service implementation remain open; do not archive this change as fully implemented.

## 11. Whole-project requirements coverage — 2026-10-13

- [x] 11.1 Write docs/REQUIREMENTS-COVERAGE.md mapping accepted/proposed/deferred requirements, evidence, owners and remaining gates.
- [x] 11.2 Reconcile stale implementation-status statements without promoting source to runtime evidence.
- [x] 11.3 Record source-only review and pending checks; validate links/OpenSpec when process execution is permitted.
## 12. Source/evidence reconciliation — 2026-10-17

- [ ] 12.1 Reconcile DESIGN, README and requirements coverage with bounded prior database/browser/image evidence and current unverified research source; condense HANDOFF without dropping decisions/gates.
- [ ] 12.2 After process authorization, validate OpenSpec/links and actual source status before claiming this documentation reconciliation verified. Preserve prior records and all unresolved acceptance gates.
- [ ] 12.3 Reconcile normalization/window/cost/learnability guides and research/service coverage with current source, then verify documentation/OpenSpec when authorized. Preserve prior evidence scopes, unchecked empirical gates and valid-method versus input-validation distinctions.
