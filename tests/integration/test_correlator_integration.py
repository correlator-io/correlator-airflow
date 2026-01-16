"""Integration tests for correlator-airflow transport.

These tests require a running Correlator backend and PostgreSQL database.
They validate the full roundtrip: transport → Correlator API → database.

Requirements:
    - Correlator backend running (make start in correlator repo)
    - PostgreSQL accessible at localhost:5432
    - psql command available in PATH

Run with: make run test integration

Configuration via environment variables:
    CORRELATOR_URL: Correlator base URL (default: http://localhost:8080)
    CORRELATOR_DB_URL: PostgreSQL connection string
        (default: postgres://correlator:password@localhost:5432/correlator)
"""

import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import pytest
import requests
from openlineage.client.event_v2 import Job, Run, RunEvent

from airflow_correlator.transport import CorrelatorConfig, CorrelatorTransport

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

CORRELATOR_URL = os.environ.get("CORRELATOR_URL", "http://localhost:8080")
CORRELATOR_DB_URL = os.environ.get(
    "CORRELATOR_DB_URL",
    "postgres://correlator:password@localhost:5432/correlator?sslmode=disable",
)

# Test namespace to identify integration test events in database.
# see namespace conventions expected by correlator canonicalizer: https://github.com/correlator-io/correlator/blob/a8b9f68b1a998f7f9bc3302f0fe693cf6cdd4396/internal/canonicalization/canonicalizer.go#L43-L67
TEST_NAMESPACE = "airflow://integration-test-airflow"


# =============================================================================
# Fixtures
# =============================================================================


def _is_correlator_reachable() -> bool:
    """Check if Correlator backend is reachable."""
    try:
        response = requests.get(f"{CORRELATOR_URL}/ping", timeout=5)
        return response.status_code == 200 and response.text.strip() == "pong"
    except requests.exceptions.RequestException:
        return False


def _query_database(query: str) -> Optional[str]:
    """Execute SQL query via psql and return output.

    Args:
        query: SQL query to execute.

    Returns:
        Query output as string, or None if query failed.
    """
    try:
        result = subprocess.run(
            ["psql", CORRELATOR_DB_URL, "-t", "-c", query],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,  # We handle returncode manually
        )
        if result.returncode == 0:
            return result.stdout.strip()
        logger.warning(f"psql query failed: {result.stderr}")
        return None
    except subprocess.TimeoutExpired:
        logger.warning("psql query timed out")
        return None
    except FileNotFoundError:
        logger.warning("psql not found in PATH")
        return None


@pytest.fixture(scope="module")
def correlator_available() -> bool:
    """Check if Correlator is available for integration tests.

    This fixture is evaluated once per test module.

    Returns:
        True if Correlator is reachable, False otherwise.
    """
    available = _is_correlator_reachable()
    if not available:
        logger.warning(
            "⚠️ Correlator not reachable at %s - integration tests will be skipped",
            CORRELATOR_URL,
        )
    return available


@pytest.fixture
def skip_if_correlator_unavailable(correlator_available: bool) -> None:
    """Skip test if Correlator is not available.

    Args:
        correlator_available: Whether Correlator is reachable.
    """
    if not correlator_available:
        pytest.skip(f"⚠️ Correlator not reachable at {CORRELATOR_URL}")


@pytest.fixture
def transport() -> CorrelatorTransport:
    """Create CorrelatorTransport configured for integration testing.

    Returns:
        Configured CorrelatorTransport instance.
    """
    config = CorrelatorConfig(
        url=CORRELATOR_URL,
        timeout=30,
        verify_ssl=False,  # Local dev typically uses HTTP
    )
    return CorrelatorTransport(config)


@pytest.fixture
def unique_run_id() -> str:
    """Generate a unique run ID for test isolation.

    Returns:
        UUID string for this test run.
    """
    return str(uuid4())


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration
class TestCorrelatorIntegration:
    """Integration tests requiring running Correlator backend."""

    def test_transport_emits_event_to_correlator(
        self,
        skip_if_correlator_unavailable: None,
        transport: CorrelatorTransport,
        unique_run_id: str,
    ) -> None:
        """Event emitted via transport is stored in Correlator database.

        This test validates the full roundtrip:
        1. Create RunEvent with unique run ID
        2. Emit via transport
        3. Query database to verify event was stored
        """
        # Arrange: Create test event
        event = RunEvent(
            eventType="START",
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=Run(runId=unique_run_id),
            job=Job(namespace=TEST_NAMESPACE, name="test_dag.integration_task"),
            producer="https://github.com/correlator-io/correlator-airflow/integration-test",
        )

        # Act: Emit event
        transport.emit(event)

        # Assert: Verify event in database
        # Query for the job run using the canonical ID format: namespace:runId
        query = f"""
            SELECT run_id, job_namespace, job_name, event_type
            FROM job_runs
            WHERE run_id = '{unique_run_id}' AND job_namespace = '{TEST_NAMESPACE}'
            LIMIT 1;
        """
        result = _query_database(query)

        assert result is not None, "Database query failed - check psql connectivity"
        assert (
            unique_run_id in result
        ), f"Event not found in database. Query result: {result}"
        assert (
            f"{TEST_NAMESPACE}" in result
        ), f"Namespace mismatch. Query result: {result}"

    def test_complete_event_lifecycle(
        self,
        skip_if_correlator_unavailable: None,
        transport: CorrelatorTransport,
        unique_run_id: str,
    ) -> None:
        """START and COMPLETE events are both stored in database.

        This test validates the complete event lifecycle:
        1. Emit START event
        2. Emit COMPLETE event (same run ID)
        3. Verify both events stored
        """
        job_name = "test_dag.lifecycle_task"

        # Emit START event
        start_event = RunEvent(
            eventType="START",
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=Run(runId=unique_run_id),
            job=Job(namespace=TEST_NAMESPACE, name=job_name),
            producer="https://github.com/correlator-io/correlator-airflow/integration-test",
        )
        transport.emit(start_event)

        # Emit COMPLETE event
        complete_event = RunEvent(
            eventType="COMPLETE",
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=Run(runId=unique_run_id),
            job=Job(namespace=TEST_NAMESPACE, name=job_name),
            producer="https://github.com/correlator-io/correlator-airflow/integration-test",
        )
        transport.emit(complete_event)

        # Verify both events in database
        query = f"""
            SELECT COUNT(*)
            FROM job_runs
            WHERE run_id = '{unique_run_id}' AND job_namespace = '{TEST_NAMESPACE}';
        """
        result = _query_database(query)

        assert result is not None, "Database query failed"
        count = int(result.strip()) if result.strip().isdigit() else 0
        assert count >= 1, f"Expected at least 1 event, found {count}"

    def test_api_returns_success_response(
        self,
        skip_if_correlator_unavailable: None,
        unique_run_id: str,
    ) -> None:
        """Direct API call returns expected success response format.

        This test validates the Correlator API response format directly,
        without going through the transport layer.
        """
        # Arrange: Create event payload
        event_payload = [
            {
                "eventType": "START",
                "eventTime": datetime.now(timezone.utc).isoformat(),
                "run": {"runId": unique_run_id},
                "job": {"namespace": TEST_NAMESPACE, "name": "test_dag.api_test_task"},
                "producer": "https://github.com/correlator-io/correlator-airflow/integration-test",
                "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json",
            }
        ]

        # Act: Send directly to API
        response = requests.post(
            f"{CORRELATOR_URL}/api/v1/lineage/events",
            json=event_payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        # Assert: Verify response format
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        body = response.json()
        assert body.get("status") == "success", f"Expected success status: {body}"
        assert "summary" in body, f"Missing summary in response: {body}"
        assert (
            body["summary"].get("successful", 0) >= 1
        ), f"No successful events: {body}"


# =============================================================================
# Cleanup Fixture (Optional)
# =============================================================================


@pytest.fixture(scope="module", autouse=False)
def cleanup_test_events() -> None:
    """Clean up test events from database after all tests.

    This fixture is NOT autouse - enable manually if needed.
    Usually test data is left for inspection after integration tests.
    """
    yield  # Run tests first

    # Cleanup after tests
    cleanup_query = f"""
        DELETE FROM job_runs
        WHERE job_namespace = '{TEST_NAMESPACE}';
    """
    result = _query_database(cleanup_query)
    if result is not None:
        logger.info("Cleaned up integration test events from database")
