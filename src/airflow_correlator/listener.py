"""Correlator Lineage Listener for Airflow.

This module provides listener functions that hook into Airflow's task lifecycle
events and emit OpenLineage events to Correlator.

The listener captures:
    - Task start events (on_task_instance_running)
    - Task success events (on_task_instance_success)
    - Task failure events (on_task_instance_failed)

Usage:
    Configure in airflow.cfg or via environment variables.
    See docs/CONFIGURATION.md for details.

Note:
    This is a skeleton implementation. The actual listener architecture
    (class vs functions, Airflow plugin registration) will be determined
    after Task 1.2 research is complete.
"""

from typing import Any


def on_task_instance_running(
    previous_state: Any,
    task_instance: Any,
    session: Any,
) -> None:
    """Handle task instance running event.

    Emits an OpenLineage START event when a task begins execution.

    Args:
        previous_state: The previous state of the task instance.
        task_instance: The Airflow TaskInstance object.
        session: The SQLAlchemy session.

    Raises:
        NotImplementedError: Skeleton implementation - not yet functional.
    """
    raise NotImplementedError(
        "on_task_instance_running() is not yet implemented. "
        "This is a skeleton release."
    )


def on_task_instance_success(
    previous_state: Any,
    task_instance: Any,
    session: Any,
) -> None:
    """Handle task instance success event.

    Emits an OpenLineage COMPLETE event when a task succeeds.

    Args:
        previous_state: The previous state of the task instance.
        task_instance: The Airflow TaskInstance object.
        session: The SQLAlchemy session.

    Raises:
        NotImplementedError: Skeleton implementation - not yet functional.
    """
    raise NotImplementedError(
        "on_task_instance_success() is not yet implemented. "
        "This is a skeleton release."
    )


def on_task_instance_failed(
    previous_state: Any,
    task_instance: Any,
    session: Any,
) -> None:
    """Handle task instance failure event.

    Emits an OpenLineage FAIL event when a task fails.

    Args:
        previous_state: The previous state of the task instance.
        task_instance: The Airflow TaskInstance object.
        session: The SQLAlchemy session.

    Raises:
        NotImplementedError: Skeleton implementation - not yet functional.
    """
    raise NotImplementedError(
        "on_task_instance_failed() is not yet implemented. "
        "This is a skeleton release."
    )
