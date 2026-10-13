# scripts

## check_secrets.py

Dependency-free (Python standard library only) regular-expression secret
scanner. Run it before any publication, push to a shared remote, or as an
optional pre-commit hook.

```sh
python scripts/check_secrets.py              # same as --staged
python scripts/check_secrets.py --staged     # staged content (what will be committed)
python scripts/check_secrets.py --all        # every tracked file in the working tree
python scripts/check_secrets.py path/ file   # explicit working-tree files or directories
```

- `--staged` lists files with `git diff --cached --name-only -z --diff-filter=ACMR`
  and reads each staged blob with `git show :<path>`, so unstaged edits do not
  hide or add findings.
- `--all` lists files with `git ls-files -z` and reads them from the working tree.
- Explicit paths cannot be combined with `--staged` or `--all`.

Exit status: `0` no findings, `1` findings, `2` usage or Git error.

Output is one line per finding, `path:line: rule [redacted]`. The redacted
form is at most the first four characters plus an ellipsis; the matched value
is never printed. Filename findings use line `0`.

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
  and paths under top-level `runs/` or `data/`.
- Binary files (a NUL byte in the first 8 KiB) and files larger than 2 MiB.
  Their filenames are still checked.

### Optional pre-commit hook

Not installed by default. To opt in, create `.git/hooks/pre-commit` containing:

```sh
#!/bin/sh
exec python scripts/check_secrets.py --staged
```

On macOS/Linux also run `chmod +x .git/hooks/pre-commit`. Git for Windows runs
the hook through its bundled shell, so `python` must be on that shell's `PATH`.
Hooks are local to each clone and are not shared through the repository.

### Tests

```sh
python -m pytest scripts/tests
```

The tests call the scanning functions on strings and temporary files and do
not need a Git repository. Fixture secrets are assembled from fragments at
runtime so the test file does not trip the scanner.

### Limits

- This is a line-based regular-expression scanner. It misses secrets split
  across lines, encoded, compressed, inside binary files or in files over
  2 MiB, and formats it has no rule for. It can also raise false positives.
- `--staged` and `--all` inspect only current content, not Git history. A
  secret committed earlier and later removed is still in history.
- It is a cheap local gate, not a substitute for a dedicated scanner. Before
  the repository is made public, run `gitleaks` or `trufflehog` over the full
  history as well.
