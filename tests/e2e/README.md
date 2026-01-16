# E2E Test Scripts

Manual end-to-end test scripts for correlator-airflow.

These tests complement the manual integration tests in `tests/integration/`.
Event Emission and API Key tests are covered in the integration tests.

## Prerequisites

1. **Correlator backend running** (for TC-002)
   ```bash
   cd ../correlator && make start
   curl http://localhost:8080/ping  # Should return: pong
   ```

2. **correlator-airflow installed**
   ```bash
   make start  # In correlator-airflow repo
   ```

3. **psql available** (for database verification)
   ```bash
   psql --version  # Should show PostgreSQL client version
   ```

## Test Cases

| Script                             | Test Case                             | Correlator Required | Priority |
|------------------------------------|---------------------------------------|---------------------|----------|
| `tc_001_transport_registration.py` | Transport discoverable by OpenLineage | No                  | P0       |
| `tc_002_config_discovery.py`       | Config via YAML and JSON env var      | Yes                 | P1       |
| `tc_003_fire_and_forget.py`        | Errors don't raise exceptions         | No                  | P0       |

## Running Tests

### Individual Tests

```bash
# TC-001: Transport Registration (no Correlator needed)
uv run python tests/e2e/tc_001_transport_registration.py

# TC-002: Config Discovery (YAML + JSON)
uv run python tests/e2e/tc_002_config_discovery.py

# TC-003: Fire-and-Forget (no Correlator needed)
uv run python tests/e2e/tc_003_fire_and_forget.py
```

### Run All

```bash
uv run python tests/e2e/run_all.py
```

## Database Verification

After running tests, verify events in database:

```bash
psql "postgres://correlator:password@localhost:5432/correlator?sslmode=disable" -c \
  "SELECT run_id, job_namespace, job_name, event_type FROM job_runs WHERE job_namespace LIKE '%e2e%' ORDER BY created_at DESC LIMIT 10;"
```

## Cleanup

```bash
# Remove test data from database
psql "postgres://correlator:password@localhost:5432/correlator?sslmode=disable" -c \
  "DELETE FROM job_runs WHERE job_namespace LIKE '%e2e%';"
```
