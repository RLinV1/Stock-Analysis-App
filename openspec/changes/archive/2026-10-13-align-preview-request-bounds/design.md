## Decision

Use the bounds in `contracts/synthetic-run-request.v1.schema.json` (lookback 10–50, epochs 1–3) as the single source for draft validation. Keep the constants in one place in the client so a later API client reuses them. Do not import the JSON schema into the bundle yet; that comes with the API client work.
