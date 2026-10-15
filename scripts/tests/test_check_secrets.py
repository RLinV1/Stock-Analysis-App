"""Tests for scripts/check_secrets.py.

These tests exercise the pure scanning functions on strings and temporary
files; no Git repository is needed. Fixture secrets are assembled from
fragments at runtime so this file never contains a literal that the scanner
itself would flag when run with --all.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import check_secrets as cs  # noqa: E402


def _rules(findings):
    return [f.rule for f in findings]


# Fragments joined at runtime (see module docstring).
AWS_KEY = "AK" + "IA" + "Q7W3E5R6T8Y2U4I9"
AWS_SESSION_KEY = "AS" + "IA" + "Z9X8C7V6B5N4M3L2"
GH_CLASSIC = "gh" + "p_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
GH_FINE = "github" + "_pat_" + "11ABCDEFG0123456789_abcdefghijKLMNOP"
SLACK = "xo" + "xb-" + "1234567890-abcdefABCDEF"
LOCALSTACK = "l" + "s-" + "Ab12Cd34-Ef56-Gh78-Ij90-Kl12Mn34Op56"
LOCALSTACK_LONG = "l" + "s-" + "aBcD1234eFgH5678iJkL9012"
JWT = (
    "ey" + "J" + "hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    + ".ey" + "J" + "zdWIiOiIxMjM0NTY3ODkwIn0"
    + ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
)
PRIVATE_KEY_HEADER = "-----BEGIN " + "RSA PRIVATE" + " KEY-----"
OPENSSH_KEY_HEADER = "-----BEGIN " + "OPENSSH PRIVATE" + " KEY-----"
PLAIN_KEY_HEADER = "-----BEGIN " + "PRIVATE" + " KEY-----"
GENERIC_VALUE = "Zq8" + "vN2xLp4Rt7Wm1Ks"
PW = "pass" + "word"
TOK = "to" + "ken"


# --------------------------------------------------------------------------
# Positive cases: each rule fires
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line, rule",
    [
        (PRIVATE_KEY_HEADER, "private-key"),
        (OPENSSH_KEY_HEADER, "private-key"),
        (PLAIN_KEY_HEADER, "private-key"),
        ("aws_key_id = " + AWS_KEY, "aws-access-key-id"),
        ("id: " + AWS_SESSION_KEY, "aws-access-key-id"),
        ("GH=" + GH_CLASSIC, "github-token"),
        ("remote uses " + GH_FINE, "github-token"),
        ("hook " + SLACK, "slack-token"),
        ("LOCALSTACK_AUTH_" + "TOKEN=" + LOCALSTACK, "localstack-auth-token"),
        ("auth " + LOCALSTACK_LONG, "localstack-auth-token"),
        ("Authorization: Bearer " + JWT, "jwt"),
        (PW + " = '" + GENERIC_VALUE + "'", "generic-secret-assignment"),
        ("DB_" + PW.upper() + '="' + GENERIC_VALUE + '"', "generic-secret-assignment"),
        ("api_key: " + GENERIC_VALUE, "generic-secret-assignment"),
        ('"client_secret": "' + GENERIC_VALUE + '"', "generic-secret-assignment"),
        ("auth-" + TOK + " => " + GENERIC_VALUE, "generic-secret-assignment"),
        ("passwd=" + GENERIC_VALUE, "generic-secret-assignment"),
    ],
)
def test_rule_positive(line, rule):
    assert rule in _rules(cs.scan_text("f.txt", line))


def test_finding_reports_path_and_line():
    text = "first line\nsecond line\n" + PW + " = '" + GENERIC_VALUE + "'\n"
    findings = cs.scan_text("conf/app.yaml", text)
    assert len(findings) == 1
    assert findings[0].format().startswith("conf/app.yaml:3: generic-secret-assignment")


def test_specific_and_generic_do_not_double_report():
    findings = cs.scan_text("f", TOK + " = '" + GH_CLASSIC + "'")
    assert _rules(findings) == ["github-token"]


# --------------------------------------------------------------------------
# Negative cases: allowlisted and benign content
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line",
    [
        # compose.yaml LocalStack test credentials
        "      AWS_ACCESS_KEY_ID: test",
        "      AWS_SECRET_ACCESS_KEY: test",
        # compose.yaml interpolation
        '      POSTGRES_' + PW.upper() + ': "${POSTGRES_' + PW.upper() + ':?set it in .env}"',
        '      PORTFOLIO_OPERATOR_' + TOK.upper() + ': "${PORTFOLIO_OPERATOR_' + TOK.upper() + '}"',
        # .env.example empty values
        "POSTGRES_" + PW.upper() + "=",
        "LOCALSTACK_AUTH_" + TOK.upper() + "=",
        # backend fake operator token
        '.addFilters(new LocalOperatorFilter("unit-test-' + 'secret-123"))',
        '.header("Authorization", "Bearer unit-test-' + 'secret-123")',
        TOK + ' = "unit-test-' + 'secret-1234567890"',
        # documented placeholders
        PW + ' = "validation-only-' + 'Value12345678"',
        PW + " = <your-" + PW + "-here-12345678>",
        "api_key = ExampleKey" + "1234567890abcdef",
        PW + " = changeme" + "1234567890ABC",
        # AWS documentation example key contains EXAMPLE
        "aws = " + "AK" + "IA" + "IOSFODNN7EXAMPLE",
        # inline allow marker
        PW + " = '" + GENERIC_VALUE + "'  # secret-scan: " + "allow",
        # short, single-class or code-reference values
        PW + " = 'short1'",
        TOK + " = 'alllowercaselettersonly'",
        TOK + " = uuid.uuid4()",
        "current_" + TOK + " = job.token",
        "secret = os.environ.get('DATABASE_" + PW.upper() + "_FILE_PATH_1234')",
        "description: OPERATOR_" + TOK.upper() + ", at least 16 characters. Never logged.",
        PW + ' = "a sentence with 16+ characters 123"',
        # ls- words that are not LocalStack tokens
        "git " + "ls-files -z",
        "git " + "ls-remote origin",
        "ls-" + "abcdefghijklmnopqrstuvwxyz",
    ],
)
def test_allowlisted_or_benign_negative(line):
    assert cs.scan_text("f", line) == []


@pytest.mark.parametrize(
    "value",
    ["", "   ", "test", "TEST", "${VAR}", "${VAR:-default}", "<placeholder>",
     "unit-test-secret-123", "validation-only", "my-example-value", "changeme"],
)
def test_is_allowlisted_value(value):
    assert cs.is_allowlisted_value(value)


def test_real_looking_value_not_allowlisted():
    assert not cs.is_allowlisted_value(GENERIC_VALUE)


# --------------------------------------------------------------------------
# Redaction
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "secret",
    [AWS_KEY, GH_CLASSIC, GH_FINE, SLACK, LOCALSTACK, JWT, GENERIC_VALUE, PRIVATE_KEY_HEADER],
)
def test_redaction_never_contains_full_secret(secret):
    redacted = cs.redact(secret)
    assert secret not in redacted
    assert redacted == "redacted"


def test_formatted_output_never_contains_secret():
    lines = [
        "k = " + AWS_KEY,
        "x " + GH_CLASSIC,
        "x " + SLACK,
        "x " + LOCALSTACK,
        "x " + JWT,
        PW + " = '" + GENERIC_VALUE + "'",
    ]
    findings = cs.scan_text("f", "\n".join(lines))
    assert len(findings) == len(lines)
    secrets = [AWS_KEY, GH_CLASSIC, SLACK, LOCALSTACK, JWT, GENERIC_VALUE]
    for f in findings:
        out = f.format()
        for s in secrets:
            assert s not in out


def test_short_value_uses_constant_redaction():
    assert cs.redact("abcdefgh") == "redacted"


def test_redaction_never_includes_a_prefix():
    assert cs.redact(GH_CLASSIC) == "redacted"


# --------------------------------------------------------------------------
# Filenames, skips, binary and size limits
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [".env", "backend/.env", ".env.local", "certs/server.pem", "tls/server.key",
     "store.p12", "home/.ssh/id_rsa", "id_ed25519"],
)
def test_sensitive_filename_flagged(path):
    finding = cs.check_filename(path)
    assert finding is not None and finding.rule == "sensitive-filename"


@pytest.mark.parametrize(
    "path", [".env.example", "docs/env.md", "id_rsa.pub", "keys.py", "README.md"]
)
def test_benign_filename_not_flagged(path):
    assert cs.check_filename(path) is None


def test_env_file_flagged_by_scan_bytes_even_when_empty():
    assert _rules(cs.scan_bytes(".env", b"")) == ["sensitive-filename"]


def test_env_example_not_flagged_by_scan_bytes():
    content = ("POSTGRES_" + PW.upper() + "=\nPORTFOLIO_OPERATOR_" + TOK.upper() + "=\n").encode()
    assert cs.scan_bytes(".env.example", content) == []


def test_binary_content_skipped():
    data = b"\x89PNG\x00\x01" + ("k = " + AWS_KEY).encode()
    assert cs.scan_bytes("image.png", data) == []


def test_binary_detection_only_sniffs_first_8_kib():
    data = ("k = " + AWS_KEY + "\n").encode() + b"a" * (8 * 1024) + b"\x00"
    assert _rules(cs.scan_bytes("late-nul.txt", data)) == ["aws-access-key-id"]


def test_oversized_file_skipped():
    data = ("k = " + AWS_KEY + "\n").encode() + b"a" * (cs.MAX_BYTES)
    assert cs.scan_bytes("big.txt", data) == []


@pytest.mark.parametrize(
    "path",
    ["mobile/node_modules/pkg/index.js", ".venv/lib/site.py", "backend/.maven-repo/x.pom",
     "runs/abc/manifest.json", "data/raw/prices.txt"],
)
def test_excluded_paths_skipped(path):
    assert cs.scan_bytes(path, ("k = " + AWS_KEY).encode()) == []


def test_nested_data_dir_is_not_skipped():
    assert cs.scan_bytes("mobile/src/data/x.ts", ("k = " + AWS_KEY).encode()) != []


# --------------------------------------------------------------------------
# Working-tree path mode (no git required)
# --------------------------------------------------------------------------


def test_main_with_paths_reports_and_exits_1(tmp_path, capsys):
    secret_file = tmp_path / "settings.txt"
    secret_file.write_text(PW + " = '" + GENERIC_VALUE + "'\n", encoding="utf-8")
    assert cs.main([str(secret_file)]) == 1
    out = capsys.readouterr().out
    assert "generic-secret-assignment" in out
    assert GENERIC_VALUE not in out


def test_main_with_clean_dir_exits_0(tmp_path):
    (tmp_path / "ok.txt").write_text("nothing to see\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("POSTGRES_" + PW.upper() + "=\n", encoding="utf-8")
    nm = tmp_path / "node_modules"
    nm.mkdir()
    (nm / "leak.txt").write_text("k = " + AWS_KEY + "\n", encoding="utf-8")
    assert cs.main([str(tmp_path)]) == 0


def test_main_flags_env_file_in_dir(tmp_path, capsys):
    (tmp_path / ".env").write_text("", encoding="utf-8")
    assert cs.main([str(tmp_path)]) == 1
    assert "sensitive-filename" in capsys.readouterr().out


def test_main_missing_path_exits_2(tmp_path):
    assert cs.main([str(tmp_path / "does-not-exist.txt")]) == 2


def test_main_paths_with_mode_flag_is_usage_error(tmp_path):
    with pytest.raises(SystemExit) as exc:
        cs.main(["--all", str(tmp_path)])
    assert exc.value.code == 2
