# Implementation record

Planned on 2026-10-13 before client edits. Found during the service review: `mobile/src/PortfolioApp.tsx` validated lookback 10–100 and epochs 1–5, while request v1 and the Java/Python validators allow 10–50 and 1–3. The archived mobile change gives no rationale for the wider bounds; it predates the contract by one day.

Moved the bounds into `LOOKBACK`/`EPOCHS` constants in `PortfolioApp.tsx` (lookback 10–50, epochs 1–3) and derived the error text from them. Tests now reject lookback 0, non-numeric and 51, epochs 0 and 4, and accept the four boundary values 10, 50, 1 and 3. On Node 22.23.2: Jest 13/13 passed in 50.0 s and `tsc --noEmit` passed. The app was not started (user instruction); no web/Android export, device or visual check was run for this text-only change. Start experiment remains disabled.

Strict validation passed on 2026-10-13; archived with the requirement synced to the main mobile shell spec.

The first archive attempt stopped on a stale `.openspec-archive.lock` (PID 25244, not running) left by the previous archive in this session. Removed that ignored file after checking the PID, archived, and removed the recreated lock. All OpenSpec items validate strictly (8/8).
