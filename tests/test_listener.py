"""Tests for Airflow listener module.

This module contains tests for the Airflow task lifecycle listener functions
that emit OpenLineage events to Correlator.

Test Coverage:
    - on_task_instance_running(): Emits START event
    - on_task_instance_success(): Emits COMPLETE event
    - on_task_instance_failed(): Emits FAIL event

Note:
    This is a skeleton test file. Full tests will be added after
    Task 1.3 (Core listener implementation) is complete.
"""

import pytest

from airflow_correlator.listener import (
    on_task_instance_failed,
    on_task_instance_running,
    on_task_instance_success,
)

# =============================================================================
# Tests for on_task_instance_running() - Skeleton
# =============================================================================


@pytest.mark.unit
def test_on_task_instance_running_raises_not_implemented() -> None:
    """Test that on_task_instance_running raises NotImplementedError.

    This test documents the expected behavior of the skeleton release.
    Once implemented, this test should be replaced with proper tests.
    """
    with pytest.raises(NotImplementedError) as exc_info:
        on_task_instance_running(
            previous_state=None,
            task_instance=None,
            session=None,
        )

    assert "not yet implemented" in str(exc_info.value).lower()


# =============================================================================
# Tests for on_task_instance_success() - Skeleton
# =============================================================================


@pytest.mark.unit
def test_on_task_instance_success_raises_not_implemented() -> None:
    """Test that on_task_instance_success raises NotImplementedError.

    This test documents the expected behavior of the skeleton release.
    Once implemented, this test should be replaced with proper tests.
    """
    with pytest.raises(NotImplementedError) as exc_info:
        on_task_instance_success(
            previous_state=None,
            task_instance=None,
            session=None,
        )

    assert "not yet implemented" in str(exc_info.value).lower()


# =============================================================================
# Tests for on_task_instance_failed() - Skeleton
# =============================================================================


@pytest.mark.unit
def test_on_task_instance_failed_raises_not_implemented() -> None:
    """Test that on_task_instance_failed raises NotImplementedError.

    This test documents the expected behavior of the skeleton release.
    Once implemented, this test should be replaced with proper tests.
    """
    with pytest.raises(NotImplementedError) as exc_info:
        on_task_instance_failed(
            previous_state=None,
            task_instance=None,
            session=None,
        )

    assert "not yet implemented" in str(exc_info.value).lower()


# =============================================================================
# Future Tests (to be implemented after Task 1.3)
# =============================================================================

# The following test signatures document what will be tested once
# the listener is fully implemented:
#
# class TestOnTaskInstanceRunning:
#     def test_emits_start_event()
#     def test_extracts_task_metadata()
#     def test_generates_run_id_from_task_instance()
#     def test_uses_dag_id_as_namespace()
#     def test_uses_task_id_as_job_name()
#     def test_handles_missing_task_metadata()
#
# class TestOnTaskInstanceSuccess:
#     def test_emits_complete_event()
#     def test_includes_execution_time()
#     def test_uses_same_run_id_as_start()
#
# class TestOnTaskInstanceFailed:
#     def test_emits_fail_event()
#     def test_includes_error_message()
#     def test_uses_same_run_id_as_start()
#
# class TestListenerIntegration:
#     def test_full_lifecycle_start_to_complete()
#     def test_full_lifecycle_start_to_fail()
#     def test_events_emitted_to_correlator()
