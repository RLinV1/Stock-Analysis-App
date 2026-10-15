# Backend status

The Java 21/Spring Boot 4.1.1 project compiles a strict consumer of the local synthetic request v1, matching the [Python hash fixture](../contracts/examples/synthetic-smoke.v1.sha256). The HTTP contract is [runs-api.v1.openapi.yaml](../contracts/runs-api.v1.openapi.yaml). Every route except the exact `/actuator/health` path requires the bearer credential.

| Route | Source state |
| --- | --- |
| `POST /api/v1/runs` | Tested (MockMvc), 2026-10-13 |
| `GET /api/v1/runs/{id}` | Tested (MockMvc), 2026-10-13 |
| `POST /api/v1/runs/{id}/cancel` | Tested (MockMvc), 2026-10-13 |
| `GET /api/v1/runs/{id}/manifest` | Tested (MockMvc and fake S3), 2026-10-13 |
| `GET /api/v1/runs` (paginated list) | Compiled and tested with MockMvc |
| `GET /api/v1/runs/{id}/report` | Tested with MockMvc and hash-checked artifact fixtures |
| `GET /api/v1/runs/{id}/equity-curve` | Tested against retained A0 report output and MockMvc |
| `GET /api/v1/runs/{id}/allocations` | Tested against retained A0 CSV output and MockMvc |

Java contract/changelog/artifact/result/MVC/CORS suites pass (61/61, 2026-10-15). A separate run passed all 14 Testcontainers PostgreSQL repository cases and applied both Liquibase migrations; worker SQL passed 40/40 real PostgreSQL cases. See the [handoff](../openspec/HANDOFF.md) for evidence and limits. S3 publication, containerized worker and Compose acceptance remain unverified.

Browser access is disabled by default. For the authorized local Expo web flow, set `PORTFOLIO_CORS_ALLOWED_ORIGINS=http://localhost:8081` before starting the API. Multiple exact HTTP(S) origins may be comma-separated; wildcards, credentials, paths, queries/fragments and invalid ports fail startup. Only canonical API paths, GET/POST and Authorization/Content-Type/Idempotency-Key headers are permitted. A validated preflight needs no token; every actual API request still requires the bearer credential. Cookies are disabled. Bind host smoke servers with `SERVER_ADDRESS=127.0.0.1`; this setting is separate from container networking.

The final full Java package passes 76/76, including automatic Liquibase startup on fresh PostgreSQL and application-context reopening/transaction rollback. Boot 4 requires the Liquibase starter; bare liquibase-core does not supply its auto-configuration. The actual browser connect/list/submit/status/cancel smoke also passes; see [retained evidence](../docs/evidence/mobile-web-2026-10-15/README.md). Completed-result/S3 acceptance remains open.

With Java 21 and Maven 3.9.10 available, run `mvn -f backend/pom.xml test` from the repository root. This host's `mvn.cmd` wrapper returned `Access is denied` under the agent sandbox, so verification launched Maven's Java entry point directly with workspace-local `.maven-repo/` and `.maven-tmp/` directories. Maven Central access is needed when dependencies change. PostgreSQL integration tests use Testcontainers and are skipped when no Docker engine is available. The parent POM manages dependency versions, but a complete transitive dependency lock and container build are still open.
