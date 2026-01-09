"""Tests for OpenLineage event emitter module.

This module contains tests for constructing OpenLineage events and
emitting them to Correlator.

Test Coverage:
    - emit_events(): Send events to OpenLineage backend
    - create_run_event(): Build OpenLineage RunEvent

Note:
    This is a skeleton test file. Full tests will be added after
    Task 1.3 (Core listener implementation) is complete.
"""

import pytest

from airflow_correlator.emitter import (
    PRODUCER,
    create_run_event,
    emit_events,
)

# =============================================================================
# Tests for PRODUCER constant
# =============================================================================


@pytest.mark.unit
def test_producer_contains_correlator_io() -> None:
    """Test that PRODUCER constant contains correlator-io identifier.

    The producer field identifies the plugin that generated the event.
    It should follow the format: https://github.com/correlator-io/airflow-correlator/{version}
    """
    assert "correlator-io" in PRODUCER
    assert "airflow-correlator" in PRODUCER


# =============================================================================
# Tests for emit_events() - Skeleton
# =============================================================================


@pytest.mark.unit
def test_emit_events_raises_not_implemented() -> None:
    """Test that emit_events raises NotImplementedError in skeleton release.

    This test documents the expected behavior of the skeleton release.
    Once implemented, this test should be replaced with proper tests.
    """
    with pytest.raises(NotImplementedError) as exc_info:
        emit_events(
            events=[],
            endpoint="http://localhost:8080/api/v1/lineage/events",
        )

    assert "not yet implemented" in str(exc_info.value).lower()


@pytest.mark.unit
def test_emit_events_with_api_key_raises_not_implemented() -> None:
    """Test that emit_events with API key raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        emit_events(
            events=[],
            endpoint="http://localhost:8080/api/v1/lineage/events",
            api_key="test-api-key",
        )


# =============================================================================
# Tests for create_run_event() - Skeleton
# =============================================================================


@pytest.mark.unit
def test_create_run_event_raises_not_implemented() -> None:
    """Test that create_run_event raises NotImplementedError in skeleton release.

    This test documents the expected behavior of the skeleton release.
    Once implemented, this test should be replaced with proper tests.
    """
    with pytest.raises(NotImplementedError) as exc_info:
        create_run_event(
            event_type="START",
            run_id="550e8400-e29b-41d4-a716-446655440000",
            job_name="dag_id.task_id",
            job_namespace="airflow",
        )

    assert "not yet implemented" in str(exc_info.value).lower()


@pytest.mark.unit
def test_create_run_event_with_inputs_raises_not_implemented() -> None:
    """Test that create_run_event with inputs raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        create_run_event(
            event_type="COMPLETE",
            run_id="550e8400-e29b-41d4-a716-446655440000",
            job_name="dag_id.task_id",
            job_namespace="airflow",
            inputs=[{"namespace": "postgres", "name": "public.users"}],
            outputs=[{"namespace": "postgres", "name": "public.processed_users"}],
        )


# =============================================================================
# Future Tests (to be implemented after Task 1.3)
# =============================================================================

# The following test signatures document what will be tested once
# the emitter is fully implemented:
#
# class TestEmitEvents:
#     def test_emit_event_sends_post_request_to_correlator()
#     def test_emit_event_handles_success_response()
#     def test_emit_event_handles_partial_success_response()
#     def test_emit_event_with_api_key_includes_header()
#     def test_emit_event_handles_connection_error()
#     def test_emit_event_handles_http_error_response()
#     def test_emit_event_handles_timeout()
#     def test_emit_events_handles_empty_list()
#
# class TestCreateRunEvent:
#     def test_create_run_event_start()
#     def test_create_run_event_complete()
#     def test_create_run_event_fail()
#     def test_create_run_event_with_inputs_and_outputs()
#     def test_create_run_event_serializes_to_json()
