"""Opt-in API/PostgreSQL and CPU-child image smoke; never starts LocalStack.

Requires already built local images and an authorized Docker engine. Credentials
live only in subprocess environments. Cleanup checks a unique ownership label.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
LABEL = "dev.portfoliolab.image-smoke"
WORKER_CHECK = """
import json, os, platform, tempfile, threading, time
from pathlib import Path
import numpy, torch
from training_process import execute_supervised
assert os.getuid() == 10001
request = json.loads(Path('/app/contracts/examples/synthetic-smoke.v1.json').read_text())
with tempfile.TemporaryDirectory(prefix='image-smoke-') as root:
    run = execute_supervised(request, Path(root), threading.Event(), deadline=time.monotonic() + 90)
    status = json.loads((run / 'status.json').read_text())
    report = json.loads((run / 'report.json').read_text())
    assert status['state'] == 'completed'
    assert set(report['strategies']) == {'lstm', 'equal_weight', 'stock_bond_60_40'}
    assert report['cost_bps'] == request['execution']['cost_bps']
    assert (run / 'checkpoint.pt').is_file() and (run / 'allocations.csv').is_file()
print(json.dumps({'uid': os.getuid(), 'python': platform.python_version(),
                  'torch': torch.__version__, 'numpy': numpy.__version__,
                  'strategies': sorted(report['strategies']), 'state': status['state']}))
"""


class ImageSmoke:
    @property
    def stage(self) -> str:
        return self._stage

    @stage.setter
    def stage(self, value: str) -> None:
        self._stage = value
        print("Image smoke: " + value, file=sys.stderr, flush=True)

    def __init__(self, api_image: str, worker_image: str):
        self.api_image, self.worker_image = api_image, worker_image
        self.owner = uuid.uuid4().hex
        self.prefix = "portfolio-smoke-" + self.owner[:12]
        self.network = self.prefix + "-network"
        self.volume = self.prefix + "-postgres-data"
        self.containers: list[str] = []
        self.stage = "initialization"
        self.environment = dict(os.environ,
                                POSTGRES_PASSWORD=secrets.token_urlsafe(32),
                                PORTFOLIO_OPERATOR_TOKEN=secrets.token_urlsafe(32),
                                AWS_EC2_METADATA_DISABLED="true")
        self.environment["DATABASE_PASSWORD"] = self.environment["POSTGRES_PASSWORD"]
        self.opener = build_opener(ProxyHandler({}))

    def docker(self, *args: str, timeout: float = 180, required: bool = True):
        result = subprocess.run(["docker", *args], env=self.environment, capture_output=True,
                                text=True, timeout=timeout, encoding="utf-8", errors="replace")
        if required and result.returncode:
            raise RuntimeError("Docker operation failed")
        return result

    def labels(self) -> list[str]:
        return ["--label", f"{LABEL}={self.owner}"]

    def api_environment(self) -> list[str]:
        return ["-e", "DATABASE_URL=jdbc:postgresql://postgres:5432/portfolio_lab",
                "-e", "DATABASE_USER=portfolio_lab", "-e", "DATABASE_PASSWORD",
                "-e", "PORTFOLIO_OPERATOR_TOKEN", "-e", "AWS_EC2_METADATA_DISABLED"]

    def start(self, name: str, *args: str) -> None:
        self.containers.append(name)
        self.docker("run", "--detach", "--name", name, *self.labels(), *args)

    def request(self, path: str, *, method: str = "GET", body: dict | None = None,
                key: str | None = None, authenticated: bool = True):
        headers = {"Content-Type": "application/json"}
        if authenticated:
            headers["Authorization"] = "Bearer " + self.environment["PORTFOLIO_OPERATOR_TOKEN"]
        if key:
            headers["Idempotency-Key"] = key
        payload = None if body is None else json.dumps(body).encode()
        request = Request(self.base_url + path, data=payload, headers=headers, method=method)
        try:
            response = self.opener.open(request, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            content = response.read(65537)
            assert len(content) <= 65536
            assert self.environment["PORTFOLIO_OPERATOR_TOKEN"].encode() not in content
            return response.status, json.loads(content)

    def ready(self) -> None:
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                status, body = self.request("/actuator/health", authenticated=False)
                if status == 200 and body.get("status") == "UP":
                    return
            except (OSError, URLError, ValueError):
                pass
            time.sleep(0.5)
        raise TimeoutError("API readiness exceeded budget")

    def refresh_address(self, api: str) -> None:
        # Docker may choose another host port when an automatic binding restarts.
        address = self.docker("port", api, "8080/tcp").stdout.strip()
        assert re.fullmatch(r"127\.0\.0\.1:[0-9]+", address)
        self.base_url = "http://" + address

    def cleanup(self) -> list[str]:
        failures = []
        resources = [("container", name) for name in reversed(self.containers)]
        resources += [("volume", self.volume), ("network", self.network)]
        for kind, name in resources:
            field = ".Config.Labels" if kind == "container" else ".Labels"
            try:
                result = self.docker(kind, "inspect", name, "--format", "{{json " + field + "}}",
                                     required=False, timeout=20)
                if result.returncode:
                    if "no such" not in result.stderr.lower():
                        failures.append(name)
                    continue
                if (json.loads(result.stdout) or {}).get(LABEL) != self.owner:
                    failures.append(name)
                    continue
                arguments = [kind, "rm"] + (["--force", "--volumes"] if kind == "container" else [])
                self.docker(*arguments, name, timeout=30)
            except (OSError, subprocess.SubprocessError, ValueError, RuntimeError):
                failures.append(name)
        return failures

    def run(self) -> dict:
        self.stage = "image identity"
        identities = {}
        for name, image in (("api", self.api_image), ("worker", self.worker_image)):
            metadata = json.loads(self.docker("image", "inspect", image).stdout)[0]
            assert metadata["Config"]["User"] == "10001:10001"
            assert metadata["Architecture"] == "amd64" and metadata["Os"] == "linux"
            identities[name] = {"reference": image, "id": metadata["Id"], "user": metadata["Config"]["User"]}
        self.stage = "disposable PostgreSQL"
        self.docker("network", "create", *self.labels(), self.network)
        self.docker("volume", "create", *self.labels(), self.volume)
        postgres = self.prefix + "-postgres"
        self.start(postgres, "--network", self.network, "--network-alias", "postgres",
                   "--mount", f"type=volume,source={self.volume},target=/var/lib/postgresql/data",
                   "-e", "POSTGRES_PASSWORD", "-e", "POSTGRES_USER=portfolio_lab",
                   "-e", "POSTGRES_DB=portfolio_lab", "postgres:17.11")
        deadline = time.monotonic() + 60
        while self.docker("exec", postgres, "pg_isready", "-U", "portfolio_lab", "-d", "portfolio_lab",
                          required=False).returncode:
            if time.monotonic() >= deadline:
                raise TimeoutError("PostgreSQL readiness exceeded budget")
            time.sleep(0.5)
        self.stage = "non-web migration image"
        migration = self.prefix + "-migrate"
        self.containers.append(migration)
        self.docker("run", "--name", migration, *self.labels(), "--network", self.network,
                    *self.api_environment(), self.api_image, "--spring.main.web-application-type=none")
        applied = self.docker("exec", postgres, "psql", "-U", "portfolio_lab", "-d", "portfolio_lab",
                              "-Atc", "SELECT count(*) FROM databasechangelog").stdout.strip()
        assert applied == "2"
        self.stage = "non-root API image"
        api = self.prefix + "-api"
        self.start(api, "--network", self.network, "--publish", "127.0.0.1::8080",
                   *self.api_environment(), self.api_image)
        self.refresh_address(api)
        self.ready()
        assert self.docker("exec", api, "id", "-u").stdout.strip() == "10001"
        self.stage = "authenticated API and transactional idempotency"
        route = "/api/v1/runs"
        assert self.request(route, authenticated=False)[0] == 401
        request = json.loads((ROOT / "contracts/examples/synthetic-smoke.v1.json").read_text(encoding="utf-8"))
        key = "image-smoke-" + self.owner
        code, accepted = self.request(route, method="POST", body=request, key=key)
        assert code == 202
        run_id = str(uuid.UUID(accepted["runId"]))
        assert self.request(route, method="POST", body=request, key=key) == (202, accepted)
        changed = json.loads(json.dumps(request))
        changed["model"]["epochs"] = 2
        assert self.request(route, method="POST", body=changed, key=key)[0] == 409
        assert self.request(route + "/" + run_id)[1]["state"] == "QUEUED"
        self.stage = "API restart persistence"
        self.docker("restart", "--time", "10", api)
        self.refresh_address(api)
        self.ready()
        self.stage = "database restart persistence"
        self.docker("restart", "--time", "10", postgres)
        self.ready()
        assert self.request(route, method="POST", body=request, key=key) == (202, accepted)
        code, cancelled = self.request(route + "/" + run_id + "/cancel", method="POST")
        assert code == 200 and cancelled["state"] == "CANCELLED"
        assert any(item["runId"] == run_id and item["state"] == "CANCELLED"
                   for item in self.request(route)[1]["items"])
        self.stage = "network-disabled non-root training child"
        worker = self.prefix + "-worker"
        self.containers.append(worker)
        trained = self.docker("run", "--name", worker, *self.labels(), "--network", "none",
                              "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev", "--cpus", "2",
                              "--memory", "1g", self.worker_image, "python", "-c", WORKER_CHECK)
        training = json.loads(trained.stdout)
        return {"kind": "independent-image-smoke", "verifiedAt": datetime.now(timezone.utc).isoformat(),
                "images": identities, "training": training,
                "checks": ["non-root-images", "automatic-migration", "bearer-required", "idempotent-submit",
                           "conflicting-body-409", "api-restart", "database-restart", "queued-cancel",
                           "list-readback", "network-disabled-read-only-worker-child"],
                "excluded": ["LocalStack", "S3", "artifact-routes", "worker-job-publication",
                             "full-Compose", "physical-Android"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-image", default="portfolio-lab-api:local")
    parser.add_argument("--worker-image", default="portfolio-lab-worker:local")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    smoke = ImageSmoke(args.api_image, args.worker_image)
    evidence = None
    try:
        evidence = smoke.run()
    except Exception as error:
        print(f"Image smoke failed during {smoke.stage}: {type(error).__name__}; private details suppressed.", file=sys.stderr)
    finally:
        failures = smoke.cleanup()
    if failures:
        print("Cleanup incomplete for owned resources: " + ", ".join(failures), file=sys.stderr)
    if evidence is None or failures:
        return 1
    evidence["cleanup"] = "all owned containers, volume and network removed"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
