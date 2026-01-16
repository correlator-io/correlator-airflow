#!/usr/bin/env python
"""TC-003: Fire-and-Forget Behavior

Objective: Verify transport doesn't raise exceptions on failure.
Priority: P0 - Critical
Preconditions: correlator-airflow installed (Correlator NOT required - tests failure handling)

Expected Results:
    - No exception raised: Script completes with exit code 0
    - Success message: "[PASS] emit() completed..." printed

Usage:
    uv run python tests/e2e/tc_003_fire_and_forget.py
"""

import logging
import sys
from datetime import datetime, timezone
from uuid import uuid4

from openlineage.client.event_v2 import Job, Run, RunEvent

from airflow_correlator.transport import CorrelatorConfig, CorrelatorTransport


def main() -> int:
    """Run fire-and-forget behavior test.

    Returns:
        0 if test passed, 1 if failed.
    """
    print("TC-003: Fire-and-Forget Behavior")
    print("=" * 50)

    # Suppress verbose stack traces from transport error logging.
    # The transport logs with exc_info=True which produces full tracebacks.
    # For this test, we only care that no exception is raised to the caller.
    logging.basicConfig(level=logging.CRITICAL)

    # Point to non-existent endpoint (should fail but not raise)
    config = CorrelatorConfig(
        url="http://localhost:9999",  # Non-existent port
        timeout=5,
    )
    transport = CorrelatorTransport(config)

    event = RunEvent(
        eventType="START",
        eventTime=datetime.now(timezone.utc).isoformat(),
        run=Run(runId=str(uuid4())),
        job=Job(namespace="airflow://fire-forget-test", name="test_dag.test_task"),
        producer="https://github.com/correlator-io/correlator-airflow/e2e-test",
    )

    print("Attempting to emit to non-existent endpoint (http://localhost:9999)...")
    print("This should NOT raise an exception (fire-and-forget pattern).")
    print()

    try:
        # This should NOT raise an exception
        transport.emit(event)

        print()
        print("[PASS] emit() completed without raising exception")
        print("       Fire-and-forget behavior is working correctly")
        return 0
    except Exception as e:
        print()
        print(f"[FAIL] emit() raised an exception: {e}")
        print("       Fire-and-forget behavior is NOT working")
        return 1


if __name__ == "__main__":
    sys.exit(main())
