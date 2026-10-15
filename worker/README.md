# CPU worker image

The worker image targets Linux x86_64 / CPython 3.12.14 and runs as UID/GID 10001. Its immutable Python base and [26-wheel lock](requirements-linux.lock) retain the current direct numerical versions. Torch uses the exact official CPU wheel; ordinary dependencies use PyPI. Installation is isolated, binary-only and hash-required, followed by `pip check`. This is not a Windows/GPU lock or a complete experiment replay contract.

From the repository root, with authorized Docker access:

```powershell
docker build -t portfolio-lab-api:local -f backend/Dockerfile .
docker build --platform linux/amd64 -t portfolio-lab-worker:local -f worker/Dockerfile .
python scripts/smoke_images.py --output .maven-tmp/image-smoke.json
```

The smoke creates uniquely labelled disposable PostgreSQL/network/volume/container resources. It verifies automatic migration, non-root API authentication/idempotency/cancellation and API/database restart persistence, then runs a real synthetic training child in the read-only worker image with networking disabled. Generated credentials are passed only through child-process environments. Cleanup checks ownership before deleting resources and reports incomplete cleanup. It never starts LocalStack, invokes artifact routes or verifies worker job publication. Full Compose/S3 and durable recovery retain their separate acceptance gates.

To refresh the Linux lock deliberately, generate exact input pins without the legacy host recipe's global extra index:

```powershell
python scripts/lock_worker_linux.py --write-input .maven-tmp/linux-lock-input.txt
$taskOutput = Join-Path (Get-Location) '.maven-tmp'
docker run --rm --mount "type=bind,source=$taskOutput,target=/output" python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -m pip --isolated install --dry-run --ignore-installed --only-binary=:all: --index-url https://pypi.org/simple --report /output/linux-lock-report.json -r /output/linux-lock-input.txt
python scripts/lock_worker_linux.py .maven-tmp/linux-lock-report.json
```

Review changes before rebuilding. The offline generator validates platform, wheel origins, hashes and direct pins; the clean hash-enforced image installation checks the full dependency closure. Updating torch requires reviewing its exact wheel URL, target and hash. Re-run numerical/recovery checks in the rebuilt environment. The report and downloaded artifacts stay in ignored scratch space; the reviewed lock is tracked.

The root Windows research environment still uses its existing requirements input and has no full Windows hash lock. Linux clean-install verification does not establish cross-platform numerical equivalence. See the [service implementation record](../openspec/changes/build-synthetic-service-slice/implementation.md) for current image and runtime evidence.
