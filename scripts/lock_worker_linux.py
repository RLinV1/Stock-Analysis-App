"""Turn a reviewed Linux pip resolution report into a closed wheel/hash lock.

Resolution is a separate opt-in network operation. This script performs no
downloads or installation and rejects unexpected artifact origins and targets.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
TORCH_URL = (
    "https://download.pytorch.org/whl/cpu/"
    "torch-2.8.0%2Bcpu-cp312-cp312-manylinux_2_28_x86_64.whl"
)


def canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def direct_requirements() -> dict[str, tuple[str, str]]:
    result = {}
    for file in (ROOT / "research/requirements-cpu.txt", ROOT / "worker/requirements.txt"):
        for line in file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line == "--extra-index-url https://download.pytorch.org/whl/cpu":
                continue  # Legacy host recipe; never copied to the Linux lock.
            match = re.fullmatch(r"([A-Za-z0-9_.-]+(?:\[[a-z,]+\])?)==([A-Za-z0-9.+_-]+)", line)
            if not match:
                raise ValueError("Direct requirements must contain exact supported pins")
            requirement, version = match.groups()
            name = canonical(requirement.split("[")[0])
            if name in result:
                raise ValueError("Duplicate direct requirement")
            result[name] = (requirement, version)
    return result


def generate(report: dict, roots: dict[str, tuple[str, str]]) -> str:
    environment = report.get("environment", {})
    expected = {"sys_platform": "linux", "platform_machine": "x86_64",
                "python_version": "3.12", "implementation_name": "cpython"}
    if report.get("version") != "1" or any(environment.get(k) != v for k, v in expected.items()):
        raise ValueError("Resolution must target Linux x86_64 CPython 3.12")
    pins = {}
    for item in report.get("install", []):
        metadata = item["metadata"]
        raw_name, version = metadata["name"], metadata["version"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", raw_name) or not re.fullmatch(r"[A-Za-z0-9.+_-]+", version):
            raise ValueError("Invalid package identity")
        name = canonical(raw_name)
        if name in pins:
            raise ValueError("Duplicate resolved package")
        artifact = item["download_info"]
        url = artifact["url"]
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.username or parsed.password or parsed.query
                or parsed.fragment or parsed.port is not None or not parsed.path.endswith(".whl")):
            raise ValueError("Only plain HTTPS wheel artifacts are supported")
        if name == "torch":
            if url != TORCH_URL or version != "2.8.0+cpu" or not item.get("is_direct"):
                raise ValueError("Torch must use the exact official CPU wheel")
            requirement = f"torch @ {url}"
        else:
            if parsed.hostname != "files.pythonhosted.org" or item.get("is_direct"):
                raise ValueError("Ordinary packages must resolve from PyPI wheels")
            requirement = f"{roots.get(name, (name, version))[0]}=={version}"
        digest = artifact.get("archive_info", {}).get("hashes", {}).get("sha256", "")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Every artifact needs a SHA-256")
        if name in roots and version != roots[name][1]:
            raise ValueError("Resolved direct version differs from the declared pin")
        pins[name] = f"{requirement} --hash=sha256:{digest}"
    if "torch" not in pins or not roots.keys() <= pins.keys():
        raise ValueError("Resolution omits a required direct package")
    header = (
        "# Linux x86_64 / CPython 3.12 CPU worker only; not a Windows or GPU lock.\n"
        "# Generated with scripts/lock_worker_linux.py from a reviewed pip report.\n"
        "# Torch uses its exact official CPU wheel; all other wheels use PyPI.\n"
        "--index-url https://pypi.org/simple\n"
        "--only-binary :all:\n"
        "--require-hashes\n\n"
    )
    return header + "\n".join(pins[name] for name in sorted(pins)) + "\n"


def resolution_input() -> str:
    roots = direct_requirements()
    if roots.get("torch") != ("torch", "2.8.0+cpu"):
        raise ValueError("Review the official wheel URL before changing the torch pin")
    return "\n".join(f"torch @ {TORCH_URL}" if name == "torch" else f"{requirement}=={version}"
                     for name, (requirement, version) in sorted(roots.items())) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, nargs="?")
    parser.add_argument("--write-input", type=Path,
                        help="Write exact resolution inputs without the legacy extra index")
    parser.add_argument("--output", type=Path, default=ROOT / "worker/requirements-linux.lock")
    args = parser.parse_args()
    if args.write_input:
        args.write_input.write_text(resolution_input(), encoding="utf-8")
        return
    if args.report is None:
        parser.error("provide a pip report or --write-input")
    lock = generate(json.loads(args.report.read_text(encoding="utf-8")), direct_requirements())
    args.output.write_text(lock, encoding="utf-8")


if __name__ == "__main__":
    main()
