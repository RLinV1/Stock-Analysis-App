# Portfolio Lab client

This Expo/TypeScript client targets Android and web; iOS is deferred. Offline mode offers synthetic sample screens and disables submission/cancellation. The connected flow has source and fake-client tests for authenticated run listing, bounded synthetic submission, manual status refresh, cancellation and measured Results (report, equity and allocations). A connection becomes active only after the run list succeeds. Credentials remain in memory. A real browser/API/PostgreSQL smoke passed connect/list/submit/status/cancel on 2026-10-15. Completed Results use fixture/artifact tests; physical Android acceptance remains open.

Use Node 22.23.2 (`.nvmrc`). From this directory:

```powershell
nvm use 22.23.2
node --version # confirm 22.23.2 before running npm
npm ci
npm run typecheck
npm run lint
npm test
npm run export:web
```

Android JavaScript/Hermes bundle verification uses `npx expo export --platform android`. Exports compile static bundles; they do not establish rendered appearance, accessibility or service/device behavior. App/dev server startup (`npm run web` or `npm run android`) requires the user's authorization for this workspace. Android cleartext HTTP versus the deferred private HTTPS endpoint remains an open decision; do not enable broad cleartext access merely to make a connection test pass. Tailscale remains disconnected.

On this PC, new shells sometimes select an older nvm symlink even after `nvm use`. If `node --version` is below 22.13, put `C:\Users\rlin7\AppData\Local\nvm\v22.23.2` first on that shell's PATH and retry. The project-local `.expo-tmp` and `.jest-cache` directories are ignored build scratch space.

Jest covers offline navigation/validation, typed API response contracts, injected-client run/report behavior, result date/strategy controls, independent retries and stale-response guards. Additional layout checks cover narrow windows and 200% text settings without disabling native text scaling. These are component checks, not screenshots or TalkBack evidence. See the [implementation record](../openspec/changes/connect-preview-to-service/implementation.md) for exact check results and limitations.

Lint uses pinned Expo 57-compatible development tooling (ESLint 9.39.5 and eslint-config-expo 57.0.2), the Expo flat configuration, and zero permitted warnings. ESLint 9 is deprecated upstream but matches this installed Expo CLI's major-version default; revisit with Expo tooling upgrades. Prior npm advisory triage is recorded under [triage-mobile-npm-audit](../openspec/changes/archive/2026-10-12-triage-mobile-npm-audit/design.md); recheck on Expo upgrades and before publication/exposure.

With an authorized app already running at `http://localhost:8081`, `node browser-check.cjs` runs browser checks using a separately available Playwright package (`NODE_PATH` can point to Codex's bundled node_modules) and installed Chrome. No browser dependency is added to the app. Set `PORTFOLIO_BROWSER_CHANNEL` to select another installed Chromium channel, `PORTFOLIO_WEB_URL` for another local app URL, and `PORTFOLIO_BROWSER_EVIDENCE` for an evidence directory. The harness intercepts synthetic API fixtures; it never establishes a real service connection. It verifies offline validation, Enter activation, rejected credentials, measured report/independent equity retries and date/strategy controls at light 1280×844 and dark 390×844, plus doubled CSS text on the narrow screen. This is browser text enlargement, not Android system font scaling.

The [2026-10-15 screenshots and check results](../docs/evidence/mobile-web-2026-10-15/README.md) record the rendered fixture review and separate real API smoke. Native TalkBack, phone, reduced-motion/performance and real completed-result acceptance remain pending.

For the separate real API smoke, run `node browser-live-check.cjs` with the same Playwright setup, authorized app/API/PostgreSQL already running, and `PORTFOLIO_CORS_ALLOWED_ORIGINS=http://localhost:8081` on the API. Store the ephemeral `PORTFOLIO_OPERATOR_TOKEN` only in ignored `../.env.runtime-test`, or select another ignored credential file/key with `PORTFOLIO_RUNTIME_ENV_PATH`/`PORTFOLIO_RUNTIME_TOKEN_KEY`. The harness submits one synthetic request and cancels it while queued. It never calls LocalStack/artifact routes. `PORTFOLIO_LIVE_API_URL` selects another local API; evidence goes to the configured browser evidence directory.
