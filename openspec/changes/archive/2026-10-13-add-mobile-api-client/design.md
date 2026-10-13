## Decisions

- The OpenAPI file and JSON schemas in `contracts/` are the source of truth. The client mirrors them by hand; no code generator or schema runtime dependency is added.
- The caller supplies the Idempotency-Key. React Native's Hermes runtime has no guaranteed `crypto.randomUUID`, and a retried submission must reuse the same key, so key ownership belongs with the screen that owns the draft.
- Errors are a single `RunsApiError` with `kind` (`network`, `timeout`, `http`, `invalid_response`, `invalid_input`) plus optional HTTP status and stable problem `code`. A 404 without body maps to code `not_found`.
- A missing or null `errorCode` is normalized to null, because live serialization of null is unverified.
- The bearer token never appears in error messages. Where the token is stored on the phone and how the base URL is configured are open decisions for the later UI wiring change.
