# Implementation record

Planned on 2026-10-11 before code edits. This bounded local request is an adapter toward the future Spring/PostgreSQL/Python service. No HTTP, queue, LocalStack, Compose or v2 replay is implemented by this change. Verification pending.

Added `contracts/synthetic-run-request.v1.schema.json` and a one-epoch example. The schema closes all objects, requires an explicit version and bounds integer-only model/execution inputs. It is not yet validated by an independent JSON Schema engine; Python adapter and tests are next.

Added the Python request adapter, canonical hash, local `synthetic-run` CLI path and behavioral tests. The first targeted pytest invocation reached collection but produced 13 fixture setup errors because its workspace-local `--basetemp` parent did not exist; two no-temp tests passed. This is a test-location setup error, not a contract result. Rerun under the ignored `runs/` parent is pending.

The corrected targeted run passed 15/15 tests in 17.45 seconds, including a completed one-epoch synthetic experiment, invalid-request rejection before file creation, duplicate-key rejection, canonical hash fixture and retained request/report/input checks. Full research regression, CLI invocation and OpenSpec validation are still pending.

The documented `synthetic-run` CLI command completed a separate local one-epoch run and exited 0, printing its run path. README, SPEC, DESIGN and READINESS now distinguish this request adapter from unbuilt v2 replay, HTTP, queue and Compose. The full regression and final validation remain pending.

Full research regression passed 74/74 in 40.35 seconds. Strict OpenSpec validation passed 7/7, including this change, and `git diff --check` exited 0 with existing line-ending warnings. README, DESIGN, SPEC, START-HERE, READINESS and REPRODUCTION now reflect the tested local adapter. An independent Draft 2020-12 schema validator was unavailable; the Python adapter covers the schema's deliberately limited closed-object/constant/integer subset and tests assert its declared shape. Cross-language hash agreement, packaging the schema into a worker image and service security are future work. Sync/archive pending.

Updated the OpenSpec context from the former 59-test A0 count to the passing 74-test suite and local CLI status. All four bounded tasks are complete; performing final validation and archive now, with main-spec sync through OpenSpec.

Strict validation passed 7/7 immediately before archive. OpenSpec synced the three new `synthetic-run-contract` requirements into the main spec and archived this completed change as `2026-10-11-add-synthetic-run-contract`. The transient archive lock was removed afterward; final main-spec and Git checks are recorded in the handoff. Durable API/worker/Compose and independent schema-engine validation remain open follow-up work, not requirements of this bounded local change.

Post-archive strict spec validation initially failed 2/3 because OpenSpec generated a placeholder `Purpose` for the newly created main capability spec. Replaced only that generated placeholder with the contract's actual purpose; rerun pending. The lock's tracked deletion remained intact.

Final rerun passed strict spec validation 3/3 and all OpenSpec validation 7/7. `git diff --check` exited 0; the exact archive lock path is ignored and its former tracked copy remains deleted in Git. All referenced new contract/spec files exist. No Docker, API, Java/Python interop or physical Android check was run in this change.
