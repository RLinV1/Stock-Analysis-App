# scripts

## Independent container and Linux dependency checks

`python scripts/smoke_images.py` checks already-built local API/worker images against disposable PostgreSQL, including non-root migration, bearer/idempotency/cancel, API/database restart and network-disabled real child training. It requires authorized Docker access, creates environment-only ephemeral credentials and deletes only uniquely owned resources. It never starts LocalStack or calls artifact routes. See [worker instructions](../worker/README.md) and [retained evidence](../docs/evidence/container-images-2026-10-15/README.md).

`python scripts/lock_worker_linux.py --write-input .maven-tmp/linux-lock-input.txt` emits exact Linux resolution inputs without the legacy global extra index. After a deliberate trusted pip resolution in Linux, `python scripts/lock_worker_linux.py .maven-tmp/linux-lock-report.json` validates platform, wheel origins, hashes and declared direct pins before writing the worker lock. The script itself does no network access or installation. Complete regeneration and clean-image checks are documented in the worker README.

## check_secrets.py

Dependency-free (Python standard library only) regular-expression secret
scanner. Run it before any publication, push to a shared remote, or as an
optional pre-commit hook.

```sh
python scripts/check_secrets.py              # same as --staged
python scripts/check_secrets.py --staged     # staged content (what will be committed)
python scripts/check_secrets.py --all        # every tracked file in the working tree
python scripts/check_secrets.py --history    # local refs, HEAD and reflog history
python scripts/check_secrets.py --history --no-history-allowlist # unfiltered audit
python scripts/check_secrets.py path/ file   # explicit working-tree files or directories
```

- `--staged` lists files with `git diff --cached --name-only -z --diff-filter=ACMR`
  and reads each staged blob with `git show :<path>`, so unstaged edits do not
  hide or add findings.
- `--all` lists files with `git ls-files -z` and reads them from the working tree.
- `--history` scans unique objects reachable from all local refs, HEAD and
  reflogs, with Git replacement objects disabled. It checks removed blobs,
  commit/tag messages and sensitive tree-entry filenames. Shallow repositories
  fail with exit 2: fetch/obtain complete history separately before scanning.
  Unreachable objects absent from refs/HEAD/reflogs are outside this scan.
- Default history mode excludes reviewed exact object/rule/line tuples in
  `secret_scan_history_allowlist.json` and reports the exclusion count. The four
  current entries are historical mobile authentication test fixtures; each
  rationale names its test file without recording a value. Object IDs bind the
  whole reviewed blob, so changed content, another line or another rule cannot
  inherit the exclusion. `--no-history-allowlist` reports these findings too.
- Explicit paths cannot be combined with `--staged`, `--all` or `--history`.

Exit status: `0` no findings, `1` findings, `2` usage or Git error.

Output is one line per finding, `path:line: rule [redacted]`. Neither the matched value
nor its prefix is printed. History labels use `git:<object-id>` (and a tree-entry
number for filenames), so historical filenames cannot disclose tokens. Use
object IDs to investigate privately; do not paste raw object contents into logs.
Filename findings use line `0`. Raw Git diagnostics are suppressed on failure.

### Rules

| Rule | Matches |
| --- | --- |
| `private-key` | PEM private-key headers (RSA, EC, OPENSSH, ENCRYPTED, PKCS#8 and so on) |
| `aws-access-key-id` | `AKIA`/`ASIA` followed by 16 uppercase letters or digits |
| `github-token` | `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_` with 36+ characters; `github_pat_` tokens |
| `slack-token` | `xoxb-`, `xoxa-`, `xoxp-`, `xoxr-`, `xoxs-` tokens |
| `localstack-auth-token` | `ls-` followed by 20+ alphanumerics or a UUID-shaped body, containing both a letter and a digit |
| `jwt` | Three base64url segments whose first two start with `eyJ` |
| `generic-secret-assignment` | A key containing `password`, `passwd`, `secret`, `token`, `api_key`/`apikey`/`api-key` or `auth_token`, assigned (`=`, `:`, `:=`, `=>`) a quoted or bare value of 16+ characters with no whitespace that contains both letters and digits. A leading `Bearer `/`Basic `/`Token ` is ignored. Bare values followed by `(` or `[` are treated as code, not literals |
| `sensitive-filename` | `.env` and `.env.*` (except `.env.example`), `*.pem`, `*.key`, `*.p12`, `id_rsa`, `id_dsa`, `id_ecdsa`, `id_ed25519` |

### Allowlist

A matched value is ignored when it is empty, exactly `test` (any case),
contains `${` interpolation, contains `validation-only`, `unit-test-secret`,
`example` or `changeme` (any case), or contains a `<...>` placeholder. This
covers the LocalStack `test` credentials and `${...}` interpolation in
`compose.yaml`, the empty values in `.env.example`, and the backend's fake
`unit-test-secret-123` token.

After reviewing a false positive, add an inline `secret-scan: allow` comment
to that line. The private-key rule ignores the value allowlist but honours the
inline comment.

### Skipped content

- Paths with a `node_modules/`, `.venv/` or `.maven-repo/` component anywhere,
  build/cache paths and paths under top-level `runs/` or `data/` are skipped in
  working-tree/staged modes. History deliberately scans objects from these paths
  too, because force-added secrets remain a risk.
- Binary files (a NUL byte in the first 8 KiB) and files larger than 2 MiB.
  Their filenames are still checked.

### Repository-local pre-commit hook

The repo-owned hook is `.githooks/pre-commit`. After reviewing existing hook
configuration (`git config --show-origin --get core.hooksPath` and the active
hook directory), activate it for this clone only:

```sh
git config --local core.hooksPath .githooks
```

On macOS/Linux also run `chmod +x .githooks/pre-commit` if the checkout did not
preserve executable mode. Git for Windows runs the hook through its bundled
shell. The hook prefers `.venv/Scripts/python.exe`, then `.venv/bin/python`,
then `python3`/`python` on PATH. A missing interpreter or scanner failure blocks
the commit. It checks index blobs, so unstaged edits cannot hide staged findings.
The script is shared; activation is local to each clone. Git hooks can be
bypassed and do not replace a publication scan or future CI controls.

### Tests

```sh
python -m pytest scripts/tests
```

Tests cover pure functions and real temporary Git repositories, removed/reflog/
other-ref content, messages, filename privacy, replacement objects, shallow
history and real pre-commit rejection/success. They require Git; hook tests use
Git for Windows' bundled shell or `sh`. Fixture secrets are assembled from
fragments at runtime so test sources do not trip the scanner.

### Limits

- This is a line-based regular-expression scanner. It misses secrets split
  across lines, encoded, compressed, inside binary files or in files over
  2 MiB, and formats it has no rule for. It can also raise false positives.
- `--staged` and `--all` inspect current content; run `--history` separately for
  removed historical material. History mode retains the same binary/2 MiB
  content limits and allowlist. An oversized tree fails rather than silently
  skipping its filenames. No scan here classifies restricted/vendor data.
- It is a cheap local gate, not a substitute for a dedicated scanner. Before
  the repository is made public, run `gitleaks` or `trufflehog` over the full
  history as well.
