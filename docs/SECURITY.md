# Security requirements by milestone

Corrected 2026-09-21. This is a design review and future control list, not a security assurance or penetration test.

## Current state and relevant threats

The current local Python runner loads checkpoints with weights_only=True, hashes inputs and writes checkpoints atomically. These reduce risks but do not make arbitrary model artifacts safe. No public API exists.
Future risks are untrusted datasets, unsafe/oversized model files, resource exhaustion through job submission, stale-worker publication, dependency supply-chain changes and accidental publication of secrets or restricted data.

## Local development and dependency installation

- Keep isolated environments and synthetic offline tests. Preserve weights_only=True and reject incompatible checkpoints.
- The Linux CPU worker now has a complete wheel/hash lock, explicit official torch wheel/PyPI-only ordinary dependencies and a clean hash-enforced image installation; see [worker instructions](../worker/README.md). The legacy Windows requirements input still uses multiple indexes and lacks a full Windows lock. Before its next install/upgrade, scope torch explicitly, lock all artifacts with hashes and verify a clean supported environment.
- A one-line --index-url change is not a complete recipe for all dependencies. [TOOLCHAIN.md](TOOLCHAIN.md) owns the planned installation approach.
- Package/model parsers still need bounds; hashes establish byte identity, not trust.
- No mandatory license choice, JDK installation or phone setup before local numerical coding.

## Before ingesting external datasets or manifests

- Validate size, row count, columns, date/session ordering, requested range, finite positive prices and corporate-action units. Reject malformed inputs explicitly.
- Validate the versioned schema and unknown fields; bound epochs, lookback, batch size, date range, assets, seed count, concurrency and run deadline before allocation or queueing.
- Never accept arbitrary user paths, URLs or executable code from imported manifests. Resolve artifact IDs through a trusted registry; restrict S3 prefixes and reject traversal.
- Network-dependent acquisition checks are opt-in integration checks; unit tests use synthetic fixtures.

## Before exposing API compute

- Authenticate compute-triggering endpoints, including private-tailnet access. Single-operator authentication is sufficient initially; no multi-tenant accounts are required.
- Apply body/rate limits, durable idempotency, leases/fencing, cancellation and hard deadlines per [SPEC.md](SPEC.md).
- Verify model/scaler hashes against registered metadata and parity evidence before inference. Do not trust an uploaded parity_verified flag.
- Load credentials from environment/secrets; local placeholders must never become real production credentials.
- Containers use least privilege. The API/worker images run as10001:10001; independent migration/API restart and network-disabled child checks pass. Docker contexts exclude local environment/account/agent/key files. Publish only the API on host loopback, while the process binds its container interface for Compose routing. Database/S3 stay internal; full Compose/S3 acceptance remains open.
- Sanitize errors and logs, restrict CORS to known origins, and scan runtime dependencies before exposure.

## Before phone access

- Tailscale is disconnected at user request; do not reconnect now.
- Once authorized, private HTTPS, tailnet access policy and a physical Android test are required. No public Funnel.
- The client bundle contains no embedded credentials; runtime credentials use platform-appropriate secure storage. Cached data is labelled; offline mutations are disabled.

## Before publication or deployment

- Choose the code license explicitly. Scan files/history for secrets and restricted data; configure pre-commit and CI checks when Git is initialized.
- Do not blanket-allow vendor samples under data/sample. Commit synthetic fixtures only unless permission is recorded.
- Review .gitignore for data, runs, model/checkpoint files and environment secrets; ignore rules alone are not a scan.
- Public GitHub Actions should use reviewed commit pins and minimum permissions; never expose secrets to untrusted pull-request code.
- Repeat Compose job recovery/persistence checks on K3s; public/paid hosting remains unapproved.

## Disclosure scope

A future public repository should offer a private security-reporting route. Manifest validation, model loading, access controls and reachable tailnet attack paths are in scope. Do not exclude a missing authentication control merely because the deployment is private. State deployment assumptions and provide best-effort response expectations without promising a service level.
