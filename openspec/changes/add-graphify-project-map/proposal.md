## Why

The user requested `/graphify .` and then asked to install Graphify in Codex. Graphify 0.9.93 is installed in an isolated uv tool environment, but its skill is currently installed only for Claude.

## What Changes

- Register the existing Graphify package's Codex skill at user scope so this project can use it.
- Detect the current project corpus and follow Graphify's size gate before extraction.
- Generate an interactive graph, JSON, and an audit report when the corpus scope is resolved.
- Curate only the most important community names; label remaining numbered communities on demand, as requested by the user.
- Record actual setup, extraction coverage, verification, and any limitations immediately.

## Capabilities

### New Capabilities

None. This is development tooling and generated documentation.

### Modified Capabilities

None. Product and research behavior remain unchanged.

## Impact

User-level Codex skill files and project graph outputs/documentation. The current request authorizes Graphify installation and graph generation only; existing restrictions on project tests, training, GPU work, services, storage, phone access, and push remain in effect. No API credential setup or external graph publication is required.

The user subsequently stopped the HTML load check. Preserve the generated page locally without claiming rendered verification.
