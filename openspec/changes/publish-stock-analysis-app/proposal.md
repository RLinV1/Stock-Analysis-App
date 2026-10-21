## Why

The user directed this mobile app and its supporting project to the empty public GitHub repository `RLinV1/Stock-Analysis-App`, requested `main`, and explicitly selected Apache-2.0. The project already has Git history and unpublished source; publishing only a new README would omit the app.

## What Changes

- Preserve existing history and publish the current project on `main`, with the requested GitHub repository as `origin`.
- Name the repository README Stock-Analysis-App and adopt the selected Apache-2.0 code license without extending it to third-party data.
- Exclude local Graphify outputs from Git, preserve their local artifacts and record the stopped HTML verification and on-demand labeling policy.
- Scan candidate files and complete local history using the existing redacted scanner and an independently obtained official Gitleaks release before publication.
- Add a minimal pinned, read-only GitHub Actions secret-scanning workflow and verify the remote commit after push.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Publication and license metadata do not change application or numerical behavior.

## Impact

README/license, current publication wording, ignore rules, CI, OpenSpec records, local Git refs/configuration, and the user-selected public GitHub repository. The user now explicitly authorizes Git commits, branch/remote setup, publication scans and push; the older no-Git/no-push handoff restriction is superseded for this task. No training, research tests, GPU work, service/storage/phone access, deployment, history rewrite, force push, or new research capability is authorized or claimed. Existing unverified source remains labeled unverified.
