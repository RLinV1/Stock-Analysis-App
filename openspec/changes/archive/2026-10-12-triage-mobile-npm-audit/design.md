## Decision

Accept the current advisories for local development and recheck on every Expo SDK upgrade and before any publication or network exposure. Do not apply npm's suggested fixes: they downgrade `expo` to 44.0.6 and `react-native` to 0.84.1, which breaks the Expo 57 client. Do not force overrides into Expo/Metro/Jest internals without upstream support.

## Rationale

All 35 entries collapse to four root advisories, all in build, bundler, test or iOS-prebuild tooling, none imported by app source:

| Root package (installed) | Advisory | Reached through | Patched release |
| --- | --- | --- | --- |
| `braces` 3.0.3 | GHSA-vfj7-8cjw-p6xm, stack exhaustion on deeply nested glob patterns | `micromatch`, Metro, Jest | None; 3.0.3 is latest |
| `node-forge` 1.4.0 | GHSA-86w9-cpqp-85rv, lax PKCS#1 v1.5 signature parsing | `@expo/code-signing-certificates` (Expo CLI) | None; 1.4.0 is latest |
| `sprintf-js` 1.0.3 | GHSA-hp3w-g68c-fv3c, DoS on unbounded precision | `argparse` 1.x, `js-yaml` 3.x, Jest/istanbul | Advisory covers all versions |
| `uuid` 7.0.3 | GHSA-w5hq-g745-h8pq, missing bounds check when `buf` is passed to v3/v5/v6 | `xcode` via `@expo/config-plugins` | 11.1.1+, but `xcode` pins 7.x |

Exploitation needs attacker-controlled glob patterns, attacker-supplied signatures to verify, attacker-controlled format strings, or a caller passing a buffer to uuid v3/v5/v6. The local workflow supplies none of these. Expo Updates code signing is not used.
