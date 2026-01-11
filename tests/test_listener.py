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
# A. on_task_instance_running() Tests - Skeleton
# =============================================================================


@pytest.mark.unit
class TestOnTaskInstanceRunning:
    """Tests for on_task_instance_running() function.

    Note: These are skeleton tests. Full tests will be added when
    on_task_instance_running() is implemented.
    """

    def test_raises_not_implemented(self) -> None:
        """Test that on_task_instance_running() raises NotImplementedError.

        This test verifies the skeleton behavior. It will be replaced with
        actual tests when on_task_instance_running() is implemented.
        """
        with pytest.raises(NotImplementedError, match="on_task_instance_running"):
            on_task_instance_running(None, None, None)


# =============================================================================
# B. on_task_instance_success() Tests - Skeleton
# =============================================================================


@pytest.mark.unit
class TestOnTaskInstanceSuccess:
    """Tests for on_task_instance_success() function.

    Note: These are skeleton tests. Full tests will be added when
    on_task_instance_success() is implemented.
    """

    def test_raises_not_implemented(self) -> None:
        """Test that on_task_instance_success() raises NotImplementedError.

        This test verifies the skeleton behavior. It will be replaced with
        actual tests when on_task_instance_success() is implemented.
        """
        with pytest.raises(NotImplementedError, match="on_task_instance_success"):
            on_task_instance_success(None, None, None)


# =============================================================================
# C. on_task_instance_failed() Tests - Skeleton
# =============================================================================


@pytest.mark.unit
class TestOnTaskInstanceFailed:
    """Tests for on_task_instance_failed() function.

    Note: These are skeleton tests. Full tests will be added when
    on_task_instance_failed() is implemented.
    """

    def test_raises_not_implemented(self) -> None:
        """Test that on_task_instance_failed() raises NotImplementedError.

        This test verifies the skeleton behavior. It will be replaced with
        actual tests when on_task_instance_failed() is implemented.
        """
        with pytest.raises(NotImplementedError, match="on_task_instance_failed"):
            on_task_instance_failed(None, None, None)
