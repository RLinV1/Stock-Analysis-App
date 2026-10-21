# Running the project

Three ways to run things, from smallest to largest:

1. **Research CLI** on your machine: datasets, training and walk-forward runs. Needs Python 3.12.
2. **Docker Compose**: PostgreSQL, LocalStack S3, the Spring Boot API and the Python worker. Needs Docker.
3. **Mobile/web client**: the Expo app that talks to the API. Needs Node 22.23.2.

Commands are run from the repository root unless a step says otherwise.

> **Tested so far:** the Windows steps are the ones used on the development PC. The macOS and Linux steps follow the same tools but have **not been run** on those systems. Full Compose with LocalStack has not been verified end to end; see the [handoff](../openspec/HANDOFF.md).

## 1. Research CLI

### Create the Python environment

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r research\requirements-cpu.txt
.\.venv\Scripts\python.exe -m pip install -e ".\research[data]"
```

Linux (x86_64):

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r research/requirements-cpu.txt
.venv/bin/python -m pip install -e "./research[data]"
```

macOS: the CPU-only `torch==2.8.0+cpu` wheel in `requirements-cpu.txt` is not published for macOS, so install from the package definition instead. PyPI's macOS torch 2.8.0 wheel is CPU/Apple-GPU capable; the project still trains on `cpu`.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e "./research[data]" pytest==8.4.2
```

The `[data]` extra adds yfinance for [historical downloads](HISTORICAL-DATA.md); leave it off if you only use synthetic data.

### Use it

Replace `PY` with `.\.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS/Linux.

```bash
PY -m portfolio_lab.cli synthetic data/demo                      # small labelled synthetic dataset
PY -m portfolio_lab.cli run data/demo/manifest.json --output runs/demo --epochs 3
PY -m pytest research/tests -q                                    # research test suite (trains tiny models)
```

Historical data and walk-forward commands are in [HISTORICAL-DATA.md](HISTORICAL-DATA.md). The research CLI needs no database, API or container.

## 2. Docker Compose

Compose starts everything the API needs without Kubernetes:

| Service | What it is | Port |
|---|---|---|
| `postgres` | PostgreSQL 17 database for runs and jobs | internal only |
| `localstack` + `s3-init` | Local S3 for run artifacts, plus a one-time bucket creation step | internal only |
| `migrate` | Applies the Liquibase schema, then exits | none |
| `api` | Spring Boot API | `127.0.0.1:8080` |
| `worker` | Python worker that claims and trains queued runs on CPU | none |

### Prerequisites

- Docker Desktop (Windows, macOS) or Docker Engine with the Compose plugin (Linux). Check with `docker compose version`.
- A LocalStack auth token: the pinned LocalStack image requires one.
- On Apple Silicon Macs, the worker image targets Linux x86_64, so Docker runs it under emulation (slower). This has not been tested.

### Configure secrets

Copy the example file and fill in all three values. `.env` is git-ignored; never commit it.

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
notepad .env
```

macOS and Linux:

```bash
cp .env.example .env
${EDITOR:-nano} .env
```

| Variable | Use |
|---|---|
| `POSTGRES_PASSWORD` | Database password; any long random string |
| `PORTFOLIO_OPERATOR_TOKEN` | Bearer token the app sends to the API; any long random string |
| `LOCALSTACK_AUTH_TOKEN` | Your LocalStack account token |

A random value can be made with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

### Start, check and stop

These commands are the same on every OS:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f api worker
```

The API is ready when `docker compose ps` shows `api` as healthy, or when this returns `"status":"UP"`:

```bash
curl http://127.0.0.1:8080/actuator/health
```

On Windows PowerShell use `curl.exe` instead of `curl`.

Stop the stack and keep its data:

```bash
docker compose down
```

`docker compose down -v` also **deletes the database and stored artifacts**. Use it only when you want a clean start.

## 3. Mobile and web client

From `mobile/`, on any OS (install [nvm](https://github.com/nvm-sh/nvm) on macOS/Linux or [nvm-windows](https://github.com/coreybutler/nvm-windows) on Windows):

```bash
cd mobile
nvm use 22.23.2
npm ci
npm run web       # browser at http://localhost:8081
npm run android   # Android device or emulator
```

In the app, connect to `http://127.0.0.1:8080` with your `PORTFOLIO_OPERATOR_TOKEN`. The web app on port 8081 needs the API started with `PORTFOLIO_CORS_ALLOWED_ORIGINS=http://localhost:8081`; `compose.yaml` does not pass that variable to the `api` service yet, so the web client against the Compose API is not supported without adding it there. A physical phone cannot reach `127.0.0.1` on your PC; private phone access is deferred. More client checks are in the [mobile README](../mobile/README.md).
