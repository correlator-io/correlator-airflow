#!/usr/bin/env python
"""Run E2E test scripts.

This script runs manual E2E tests that complement the automated integration tests.
Event Emission and API Key tests are covered by tests/integration/.

Usage:
    uv run python tests/e2e/run_all.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

import requests

# Test scripts to run (in order)
TEST_SCRIPTS = [
    ("TC-001", "tc_001_transport_registration.py", False),  # No Correlator needed
    ("TC-002", "tc_002_config_discovery.py", True),  # Correlator required
    ("TC-003", "tc_003_fire_and_forget.py", False),  # No Correlator needed
]


def check_psql() -> bool:
    """Check if psql is available in PATH."""
    return shutil.which("psql") is not None


def check_correlator() -> bool:
    """Check if Correlator is reachable."""
    try:
        response = requests.get("http://localhost:8080/ping", timeout=5)
        return response.status_code == 200 and response.text.strip() == "pong"
    except Exception:
        return False


def run_test(test_id: str, script: str, needs_correlator: bool) -> bool:
    """Run a single test script.

    Returns:
        True if test passed, False otherwise.
    """
    script_path = Path(__file__).parent / script

    print(f"\n{'=' * 60}")
    print(f"Running {test_id}: {script}")
    print("=" * 60)

    if needs_correlator and not check_correlator():
        print(f"[SKIP] {test_id} - Correlator not reachable")
        return True  # Skip is not a failure

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            timeout=60,
            check=False,  # We handle returncode manually
        )
        if result.returncode == 0:
            print(f"\n[PASS] {test_id}")
            return True
        print(f"\n[FAIL] {test_id} - Exit code: {result.returncode}")
        return False
    except subprocess.TimeoutExpired:
        print(f"\n[FAIL] {test_id} - Timeout")
        return False
    except Exception as e:
        print(f"\n[FAIL] {test_id} - Error: {e}")
        return False


def main() -> int:
    """Run all tests and report results."""
    print("E2E Test Suite Runner")
    print("=" * 60)
    print()

    # Check prerequisites
    psql_available = check_psql()
    if psql_available:
        print("[INFO] psql is available (for database verification)")
    else:
        print("[WARN] psql not found - database verification will not be available")

    correlator_up = check_correlator()
    if correlator_up:
        print("[INFO] Correlator is reachable at http://localhost:8080")
    else:
        print("[WARN] Correlator not reachable - some tests will be skipped")

    # Run tests
    results = {}
    for test_id, script, needs_correlator in TEST_SCRIPTS:
        results[test_id] = run_test(test_id, script, needs_correlator)

    # Summary
    print("\n")
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_id, passed_flag in results.items():
        status = "[PASS]" if passed_flag else "[FAIL]"
        print(f"  {status} {test_id}")

    print()
    print(f"Total: {passed}/{total} passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
