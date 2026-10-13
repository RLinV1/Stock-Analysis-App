# Backend status

The Java 21/Spring Boot 4.1.1 project compiles a strict consumer of the local synthetic request v1, matching the [Python hash fixture](../contracts/examples/synthetic-smoke.v1.sha256). The HTTP contract is [runs-api.v1.openapi.yaml](../contracts/runs-api.v1.openapi.yaml). Every route except the exact `/actuator/health` path requires the bearer credential.

| Route | Source state |
| --- | --- |
| `POST /api/v1/runs` | Tested (MockMvc), 2026-10-13 |
| `GET /api/v1/runs/{id}` | Tested (MockMvc), 2026-10-13 |
| `POST /api/v1/runs/{id}/cancel` | Tested (MockMvc), 2026-10-13 |
| `GET /api/v1/runs/{id}/manifest` | Tested (MockMvc and fake S3), 2026-10-13 |
| `GET /api/v1/runs` (paginated list) | Written 2026-10-13, not compiled or run |

Twenty-four Java tests passed on 2026-10-13 before the run list, the malformed-ID mapping and the PostgreSQL integration tests were written; those later additions have not been compiled. PostgreSQL transitions, actual migration, worker, S3, Compose and a live HTTP server remain unverified; this is not yet a working service.

With Java 21 and Maven 3.9.10 available, run `mvn -f backend/pom.xml test` from the repository root. This host's `mvn.cmd` wrapper returned `Access is denied` under the agent sandbox, so verification launched Maven's Java entry point directly with workspace-local `.maven-repo/` and `.maven-tmp/` directories. Maven Central access is needed when dependencies change. PostgreSQL integration tests use Testcontainers and are skipped when no Docker engine is available. The parent POM manages dependency versions, but a complete transitive dependency lock and container build are still open.
