# Requirements review — 2026-09-21

## Resolution after user requested fixes

The numbered findings below preserve the original review, not current requirements. Current documents supersede their quoted old text.

- Stack reconciled to Spring Boot/Expo/Python and explicitly confirmed by the user's updated AGENTS.md.
- Invalid return-ceiling claims withdrawn; prior measurements labelled unverified; public-facing claims removed.
- SPEC now defines viable tier dates, VIXY-only tradable default, matched-window comparisons, durable jobs, replay outcomes/tolerances and per-fold inference provenance.
- DESIGN/PRD/OpenSpec separate A0, A1 and later service/client milestones. Status now acknowledges the existing prototype.
- Snapshot, publication, security/readiness and toolchain guidance corrected; implementation and empirical checks remain open where evidence is absent.
- Documentation correction does not reproduce the audit figures or implement the newly defined services/schema.
- Final checks after corrections: OpenSpec 4/4 passed; 41 Markdown files checked with no unresolved local files/headings or duplicate requirement titles. Application tests were not repeated for documentation-only edits.

The research direction is coherent, but these documents are not yet a consistent implementation contract. This review records defects and proposed corrections; it does not accept a new stack, license, or research default. Priority 1 means resolve before implementing the affected component or publishing its claim; priority 2 means clarify before that milestone ships.

## Priority 1 findings

### 1. Two incompatible application stacks remain authoritative

`AGENTS.md` and `openspec/config.yaml` require Kotlin Android and Kotlin/Quarkus. `DESIGN.md` sections 1/9 and `SPEC.md` section 1 specify Java/Spring Boot and React Native/Expo. The product-change proposal says the user accepted that replacement, while tasks 1.7–1.9 and READINESS still await acceptance. The latest user-supplied working agreement retains Kotlin/Quarkus. The earlier question about FastAPI/Django is another option, not an implemented backend.

Resolve the controlling stack decision, then synchronize instructions, config, handoff, roadmap, and both active changes. Preserve Python/PyTorch research work, which is independent of this choice. Do not generate two application stacks.

### 2. The claimed return ceiling is mathematically invalid

`FINDING-VIX-INSTRUMENT.md` section 3b infers that a dynamic long-only allocator cannot return 31.3% because the best individual asset returned 12%. A bound on fixed-weight average returns does not bound time-varying weights. Counterexample: A returns +10%, then -10%; B returns -10%, then +10%. Each finishes at -1%, while holding A then B yields +21%. This is an arithmetic counterexample, not evidence that such switching can be predicted.

Remove the impossibility conclusion. The reported best static Sharpe also is not a ceiling on a dynamic model. Instrument ambiguity remains worth investigating, but these arguments cannot establish that the paper's result is unachievable. Section 1a's own fourth row is positive under both instruments, contradicting “wrong sign on every expected return”; that phrase also appears in README and PAPER-BACKGROUND.

### 3. Audit measurements lack reproducible local evidence

The audit documents report reconstructed baseline tables, a 0.987 correlation, a 0.35pp tracking gap, and precise adjusted-return figures. No reconstruction scripts, input-hash manifests, or saved audit outputs were found in the inspected project. The implementation record explicitly says those figures were not independently verified. Existing tests exercise synthetic data and cannot validate those findings.

Preserve these numbers as unverified audit observations until scripts and provenance can regenerate them. Resolve the documented annual-versus-daily rebalancing mismatch before claiming a match. Change “resolved” to distinguish a chosen experimental treatment from establishing which series the authors actually used. README already contains the assertions that it promises not to publish until verification is complete.

The distinction between VIX and a futures-based product is supported by the [VIXY issuer documentation](https://www.proshares.com/our-etfs/strategic/vixy). That source does not verify this project's reconstructed returns or the authors' original input data.

### 4. Tradable-tier dates cannot support the specified first fold

`SPEC.md` section 3 combines a VXX example, data starting in 2006, and testing from January 2011. Section 8 instead specifies VIXY backfill before 2018. The instrument audit acknowledges VIXY data starts in 2011, leaving no pre-2011 training history for this tier.

Define separate data ranges and folds for each tier. Require enough historical observations for training, validation, and lookback before the first tradable test. Compare tiers over a declared common evaluation window where relevant. Specify a return-based splice and rebasing rule; concatenating price levels of different instruments would introduce an artificial jump. Using futures for earlier history would require its own explicit model and data contract.

### 5. Launch, cancellation, and recovery have no worker contract

`SPEC.md` sections 2/5 promise asynchronous launches, cancellation, and verification reruns, while the architecture only describes Python writing artifacts and Java reading them. The Compose/K3s plan omits a managed training worker and a job-delivery mechanism. Offline mutation replay in section 6 can duplicate expensive training requests.

Specify a durable job mechanism, submission idempotency, worker ownership/leases, heartbeat expiry, retries, cancellation acknowledgement, and how artifact publication becomes a completed database result. Include the worker in Compose and later K3s. A PostgreSQL-backed queue is one possible small first implementation, not an accepted choice. Test worker crashes and duplicate submissions. This is also the clearest opportunity to demonstrate the distributed-systems skills the user wants.

### 6. “Verify a manifest” is not sufficiently defined

`SPEC.md` section 3 provides only a Sharpe tolerance but promises agreement for all metrics. It does not define null/undefined metrics, numerical tolerances per metric, or whether changed inputs can ever earn MATCH when numbers happen to agree. Its S3 key plus parity boolean does not capture preprocessing and asset ordering required to reproduce served inference. There is no Git repository in this directory, while the new manifest requires a commit; the existing runner uses source fingerprints instead.

Define an executable versioned schema, ordered feature/asset contract, preprocessing artifacts and hashes, per-metric tolerances, and distinct input-identity versus numerical-comparison outcomes. A missing input cannot simply be treated as a numerical mismatch. Distinguish unsupported replay from a failed result comparison. Specify one model/checkpoint and scaler per walk-forward fold, including how a serving model is selected. The OpenSpec seed-variance scenario also should not treat “standard deviation comparable to the gap” as a statistical proof of indistinguishability.

## Priority 2 findings

### 7. Current status and milestone scope contradict each other

README says implementation has not started; HANDOFF said no training code exists. Source and 17 passing tests exist. `SPEC.md` section 4 labels `data.py` as fetching/adjusting data and `metrics.py` as including Sortino; those functions are not implemented. The first research change promises a bounded fixed holdout and two baselines, while the newer documents require walk-forward, seven baselines, and three instrument tiers. PRD assigns verification story C2 to Phase B, but READINESS requires its round trip for Phase A.

Separate implemented prototype, current milestone, and full reproduction. Reconcile task ownership between the two open changes instead of silently expanding the first one. Choose whether CLI verification ships in Phase A and HTTP verification in Phase B. Choose one API/database contract: DESIGN section 4 uses allocation/evaluation endpoints and tables, while SPEC section 5 uses run/sweep endpoints and different model fields. Document the migration or make DESIGN reference SPEC.

### 8. Data snapshot and redistribution rules contradict their own assumptions

The data audit calls raw Yahoo fields immutable despite also saying Close is retrospectively split-adjusted. Later splits can change historical levels; snapshots and adjustment conventions still matter. Its adjustment formula omits capital-gains distributions even though the schema records them. A refetched-data hash is an identity check, not a guarantee the source will reproduce identical bytes forever.

The same document prohibits redistribution, but recommends committing real sample CSVs and labels all derived returns as freely publishable. No specific permission for those exceptions is recorded. Its blanket claim that no free data is redistributable also conflicts with the alternatives it names later. Narrow conclusions to the evaluated datasets and access terms, use synthetic CI samples, and verify rights for each published artifact. Do not equate transforming prices into returns with establishing redistribution permission. This review did not re-establish every provider's legal terms; the Yahoo terms request failed.

### 9. Readiness gates block unrelated work and contradict themselves

READINESS says every open item must be green before `protocol.py`, then correctly says the rebalancing discrepancy blocks public claims rather than implementation. JDK/Node setup, a final public license, and phone connectivity also need not block local Python tests. SECURITY treats its milestones as proposed but makes all seven M0 items prerequisites for any code; the disclosure policy excludes tailnet issues that its threat model includes.

Gate each action on its actual prerequisites: numerical checks before research claims, access controls before exposing compute, publication checks before publishing. Keep phone connectivity deferred per the user. Resolve the disclosure-scope inconsistency. Reconcile the dependency installation recipe in SECURITY with TOOLCHAIN's explicit package-index mapping and a tested lockfile; the one-line hash example is not a complete installation recipe.

### 10. Version checks are not compatibility or performance checks

The PyPI registry confirms the documented releases torch 2.14.0, numpy 2.5.3, yfinance 1.7.0, uv 0.12.17, and onnxruntime 1.30.0 exist. This review did not verify every release-note claim in TOOLCHAIN, install the proposed upgrades, export ONNX, or test Java inference. Claims of near-linear eight-worker scaling and a GPU slowdown need local measurements. Keep them as hypotheses, retain the one-run default until measured, and test export with the actual fixed-window model before making a dynamic-sequence exporter upgrade mandatory.

Registry sources: [torch](https://pypi.org/pypi/torch/json), [numpy](https://pypi.org/pypi/numpy/json), [yfinance](https://pypi.org/pypi/yfinance/json), [uv](https://pypi.org/pypi/uv/json), [onnxruntime](https://pypi.org/pypi/onnxruntime/json).

## Checks performed

- Read current requirements, design/product/technical/security/readiness/research documents, current spec, active change artifacts, and relevant source/tests.
- Strict OpenSpec validation: 4 passed, 0 failed. This validates structure, not cross-document semantics.
- Local Markdown file-link scan: 40 documents, zero unresolved targets; heading anchors were not checked.
- Existing test suite: 17 passed in 9.23 seconds, CPU, no code changes. Initial attempts hit a sandbox temp-directory permission error and then a missing parent directory; a fresh workspace-local temp directory resolved both.
- No Git repository, application API, mobile client, Compose stack, K3s manifests, or historical-result artifacts were found. Tests train tiny synthetic models; this is not a historical reproduction result.
- Tailscale was disconnected at the user's earlier request; installation/service retained. No phone setup or backend exposure performed.

Recommended next step: reconcile stack authority and milestone boundaries, then implement the smallest research/API/worker path against one contract. Keep the VIX conclusion provisional while collecting reproducible evidence.
