# Toolchain — installed state and candidates

Corrected 2026-09-21. Registry existence, installed compatibility, model export and performance are separate checks.

## Official-source architecture check — 2026-09-21

| Choice | Evidence and implementation implication |
|---|---|
| Java 21 + Spring Boot | Current Spring Boot 4.1.1 documentation supports Java 17–26, so Java 21 is compatible at the framework level. Select and lock an actual release with integration tests before scaffolding; this check is not an automatic upgrade or native-image approval. |
| Expo/React Native | Current SDK 57 documents Node 22.13.x minimum, above installed 22.12.0. Candidate: Node 24 LTS and SDK 57 with exact patch at least 57.0.17 (documented Hermes/startup fixes). Keep SDK/native dependencies compatible via expo install, then validate with Expo Doctor and Android/web checks before accepting the lock. |
| PostgreSQL job queue | PostgreSQL explicitly identifies SKIP LOCKED as useful for queue-like tables. Short claims plus leases/fencing remain application responsibilities. |
| Compose | Service readiness and successful initialization must be configured explicitly; ordering alone does not make a database ready. |
| LocalStack | Current AWS images require LOCALSTACK_AUTH_TOKEN, including free Hobby access. Confirm eligibility/features and persistence before integration; do not assume offline startup or that a volume alone restores service state. |
| K3s | Linux is the runtime target; k3d runs K3s in containers and is the planned Windows-host local route. |

Primary sources checked: [Spring requirements](https://docs.spring.io/spring-boot/system-requirements.html), [Expo SDK](https://docs.expo.dev/versions/latest/), [PostgreSQL locking](https://www.postgresql.org/docs/current/sql-select.html), [Compose readiness](https://docs.docker.com/compose/how-tos/startup-order/), [LocalStack images](https://docs.localstack.cloud/aws/customization/other-installations/docker-images/), [LocalStack plans](https://www.localstack.cloud/pricing), [persistence](https://docs.localstack.cloud/aws/developer-tools/snapshots/persistence/), [K3s requirements](https://docs.k3s.io/installation/requirements), [k3d](https://k3d.io/stable/).

This is a documented architecture compatibility review. No new runtime was installed, no account/token was obtained, and no cross-service smoke test was performed.

Additional primary sources checked in the independent review: [Expo SDK 57 release notes](https://expo.dev/changelog/sdk-57) and [Node release status](https://nodejs.org/en/about/previous-releases). These support candidates, not a tested project lock.

### Local host inspection — 2026-09-21

- Python 3.12.14, PyTorch 2.8.0+cpu and filelock 3.32.6 import successfully; CPU tensor arithmetic and pip check pass.
- Java 21.0.2 exists at C:/Program Files/Java/jdk-21; PATH currently selects Java 24.0.1. Select a maintained Java 21 patch in the build/container lock rather than treating this old installed patch as deployment-ready.
- Update 2026-10-10: Node 22.23.2 was installed through nvm and used explicitly for the Expo 57.0.27/React Native 0.86.3 client. New shells still resolve the older 22.12.0 symlink; verify the executable before tests/builds. Seven component tests, TypeScript, web and Android exports pass. Expo's offline package check uses a bundled map and is less conclusive than an online doctor run. npm audit with dev packages omitted reported 12 moderate and 23 high advisories; triage before release or network exposure.
- Docker client 28.3.2 and Compose 2.38.2-desktop.1 are installed. Elevated inspection resolved desktop-linux but could not find its engine pipe. Container startup is unverified; the engine must be started/checked for the Compose milestone.
- adb and k3d were not on PATH; this is not proof they are absent elsewhere and neither blocks local numerical work.
- No service was started and Tailscale was not changed. Update 2026-09-23: Git history now exists; the full dependency lock remains absent.

### Existing local Python environment

Python 3.12 in project .venv; research requirements pin torch 2.8.0+cpu, numpy 2.2.6, psutil 7.0.0, filelock 3.32.6, pytest 8.4.2 and setuptools 80.9.0. The existing suite passed 17 tests in the review. This is not an ONNX or GPU test. filelock is now explicitly declared at its existing installed version; no package was upgraded.

A Spring Boot 4.1.1 parent POM now resolves into ignored workspace-local Maven cache and two Java contract tests pass using JDK 21.0.2. The `mvn.cmd` wrapper failed under the agent sandbox, so Maven's Java launcher was used. This is a tested scaffold, not an API or a full transitive lock. No clean container installation is verified. OpenSpec 1.13.0 works through its installed CLI; Node 22.12.0 emitted dependency-engine warnings in earlier setup.

## Candidate versions, not upgrade instructions

The 2026-09-21 review queried the public PyPI registry and confirmed torch 2.14.0, numpy 2.5.3, yfinance 1.7.0, uv 0.12.17 and onnxruntime 1.30.0 exist. It did not install or test them together.

Earlier release-note assertions about ONNX IR/opset changes, pandas defaults, uv hash behavior and mandatory torch upgrades were not independently validated in this project. They must not drive upgrades until checked against official release-specific documentation and an actual compatibility test. No upgrade is required solely because a newer version exists.

## Planned dependency workflow

Before changing dependencies:
1. Keep direct imports explicitly declared (filelock was corrected in the readiness cleanup), separating research/runtime/test/export extras.
2. Use package-specific index mapping: the PyTorch CPU index is explicit and torch-only; ordinary dependencies resolve from the intended primary index.
3. Generate a full transitive lock with hashes for the target Windows CPU environment and future Linux container environment. Verify a frozen/hash-enforced clean installation for each.
4. Run numerical/recovery tests and retain the exact environment identity. Changed runtime versions invalidate same-environment replay assumptions.

This workflow is planned; no uv.lock or full hash lock currently exists. Do not replace requirements with an untested example command.

## ONNX and JVM milestone

Use the actual 64-unit fixed-lookback model for the first export test. Select exporter mode and opset explicitly, verify installed exporter dependencies, and load the graph with the selected Python and Java runtimes.
Record actual IR/opset and runtime compatibility; package version similarity alone does not establish it. Export every fold's model/preprocessing contract and test parity under SPEC tolerances.
Dynamic sequence length is optional and not a reason to block the initial fixed-window API. Serve only registered, hash-verified artifacts.

## Java and client milestone

Java 21 is the planned JDK. Select a supported Spring Boot release and verify PostgreSQL/LocalStack Testcontainers integration; do not assume every service obtains all connection configuration automatically.
Select an Expo SDK and its supported Node/React Native dependencies together; test chart rendering and caching on physical Android and web. Native and web share code but still need separate verification.
These selections occur before B/C implementation; they do not gate A0.

## Hardware

Default to one single-threaded CPU run. Benchmark memory and elapsed time before increasing concurrency. Eight workers may compete for memory and do not have demonstrated linear speedup.
GPU support/performance is untested. Keep device selection explicit and compare measured runtime/determinism before adopting CUDA. Do not claim the GPU is slower or faster based on parameter count alone.
