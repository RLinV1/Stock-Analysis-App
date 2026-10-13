## Tasks

- [x] Add the connection form; connect only after a successful run list; show honest errors by kind.
- [x] Wire live run list, submission with a reused per-draft idempotency key, manual status refresh, cancel and manifest file list.
- [x] Keep offline behavior and demo labels; add fake-client tests including token redaction.
- [x] Run Jest and TypeScript on Node 22.23.2 (41/41 and clean on 2026-10-13).
- [ ] Decide Android cleartext handling for a local `http://` API (app config) or use HTTPS via the deferred Tailscale endpoint.
- [ ] Verify against a live API and on the physical Android phone before claiming the flow works.
- [ ] Record verification, validate OpenSpec and archive.

## Report viewer and UI continuation — 2026-10-13

- [ ] Write a typed report client/parser and manifest identity guard, with contract regression tests.
- [ ] Write a Results view with measured strategy metrics, evaluation context, undefined reasons, loading/error/retry and stale-response protection.
- [ ] Refine Apple-inspired typography, grouped surfaces and control spacing while preserving text scaling, press feedback, Android Back and synthetic labels.
- [ ] Write component coverage for report success, undefined metrics, loading/failure/retry and stale responses.
- [ ] Run client tests, TypeScript, lint, and rendered light/dark/large-text review when execution is permitted; validate OpenSpec before archive.
