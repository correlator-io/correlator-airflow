#!/usr/bin/env python
"""TC-001: Transport Registration

Objective: Verify `correlator` transport type is discoverable by OpenLineage.
Priority: P0 - Critical
Preconditions: correlator-airflow installed

Expected Results:
    - Entry point registered: True
    - Transport class importable: True
    - No import errors

Usage:
    uv run python tests/e2e/tc_001_transport_registration.py
"""

import sys
from importlib.metadata import entry_points


def main() -> int:
    """Run transport registration test.

    Returns:
        0 if test passed, 1 if failed.
    """
    print("TC-001: Transport Registration")
    print("=" * 50)

    # Check entry point is registered
    eps = entry_points(group="openlineage.transport")
    correlator_eps = [ep for ep in eps if ep.name == "correlator"]

    print(f"Entry point registered: {len(correlator_eps) > 0}")

    if not correlator_eps:
        print("\n[FAIL] Entry point 'correlator' not found")
        print("       Check that correlator-airflow is installed: uv pip install -e .")
        return 1

    ep = correlator_eps[0]
    print(f"Entry point value: {ep.value}")

    # Try to load the transport class
    try:
        transport_class = ep.load()
        print(f"Transport class loaded: {transport_class.__name__}")

        # Verify it has required attributes
        has_kind = hasattr(transport_class, "kind")
        has_config_class = hasattr(transport_class, "config_class")
        has_emit = hasattr(transport_class, "emit")

        print(f"Has 'kind' attribute: {has_kind}")
        print(f"Has 'config_class' attribute: {has_config_class}")
        print(f"Has 'emit' method: {has_emit}")

        if has_kind and has_config_class and has_emit:
            print(
                f"\n[PASS] Transport '{transport_class.kind}' is correctly registered"
            )
            return 0
        print("\n[FAIL] Transport missing required attributes")
        return 1
    except Exception as e:
        print(f"\n[FAIL] Failed to load transport class: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
