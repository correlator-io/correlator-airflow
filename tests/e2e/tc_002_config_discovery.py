#!/usr/bin/env python
"""TC-002: Configuration Discovery

Objective: Verify transport is discoverable via OpenLineage configuration methods.
Priority: P1 - High
Preconditions: Pre-test checklist complete, Correlator running

This test validates that the correlator transport can be loaded via:
    1. YAML config file (openlineage.yml)
    2. JSON environment variable (OPENLINEAGE_CONFIG)

Note: Custom transports require full module path in OpenLineage Python client config.
The short name 'correlator' only works in Airflow with the OpenLineage provider.

Usage:
    uv run python tests/e2e/tc_002_config_discovery.py

Note: Requires Correlator running at http://localhost:8080
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from openlineage.client import OpenLineageClient
from openlineage.client.event_v2 import Job, Run, RunEvent

print("TC-002: Configuration Discovery")
print("=" * 60)


def test_yaml_config() -> bool:
    """Test config via openlineage.yml file."""
    print("\n[1/2] Testing YAML config file...")

    config_path = Path(__file__).parent / "tc_002_openlineage.yml"
    os.environ["OPENLINEAGE_CONFIG"] = str(config_path)
    print(f"      Config: {config_path}")

    try:
        client = OpenLineageClient()

        run_id = str(uuid4())
        event = RunEvent(
            eventType="START",
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=Run(runId=run_id),
            job=Job(namespace="airflow://e2e-yaml-config", name="test_dag.yaml_task"),
            producer="https://github.com/correlator-io/correlator-airflow/e2e-test",
        )
        client.emit(event)

        print(f"      Emitted: runId={run_id}")
        print("      [PASS] YAML config")
        return True
    except Exception as e:
        print(f"      [FAIL] YAML config: {e}")
        return False
    finally:
        if "OPENLINEAGE_CONFIG" in os.environ:
            del os.environ["OPENLINEAGE_CONFIG"]


def test_json_env_var() -> bool:
    """Test config via JSON environment variable."""
    print("\n[2/2] Testing JSON env var...")

    config_json = '{"transport":{"type":"airflow_correlator.transport.CorrelatorTransport","url":"http://localhost:8080"}}'
    os.environ["OPENLINEAGE_CONFIG"] = config_json
    print(f"      Config: {config_json[:60]}...")

    try:
        client = OpenLineageClient()

        run_id = str(uuid4())
        event = RunEvent(
            eventType="START",
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=Run(runId=run_id),
            job=Job(namespace="airflow://e2e-json-config", name="test_dag.json_task"),
            producer="https://github.com/correlator-io/correlator-airflow/e2e-test",
        )
        client.emit(event)

        print(f"      Emitted: runId={run_id}")
        print("      [PASS] JSON env var")
        return True
    except Exception as e:
        print(f"      [FAIL] JSON env var: {e}")
        return False
    finally:
        if "OPENLINEAGE_CONFIG" in os.environ:
            del os.environ["OPENLINEAGE_CONFIG"]


def main() -> int:
    """Run all config discovery tests."""
    results = []

    results.append(("YAML config", test_yaml_config()))
    results.append(("JSON env var", test_json_env_var()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("[PASS] TC-002: Configuration Discovery")
    else:
        print("[FAIL] TC-002: Configuration Discovery")

    print()
    print("Verify in database:")
    print(
        '  psql "postgres://correlator:password@localhost:5432/correlator?sslmode=disable" -c \\'
    )
    print(
        "    \"SELECT run_id, job_namespace, job_name FROM job_runs WHERE job_namespace LIKE '%e2e%config%' ORDER BY created_at DESC LIMIT 5;\""
    )

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
