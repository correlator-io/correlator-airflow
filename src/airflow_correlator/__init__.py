"""airflow-correlator: Emit Airflow task events as OpenLineage events.

This package provides an Airflow listener that captures task lifecycle events
and emits OpenLineage events for automated incident correlation.

Key Features:
    - Capture Airflow task START/COMPLETE/FAIL events
    - Construct OpenLineage events with task metadata
    - Emit events to Correlator or any OpenLineage-compatible backend
    - Zero-friction integration with existing Airflow workflows

Usage:
    $ airflow-correlator --version
    $ airflow-correlator config

Architecture:
    - listener: Task lifecycle hook functions
    - emitter: Construct and emit OpenLineage events
    - config: Configuration file loading utilities
    - cli: Command-line interface

For detailed documentation, see: https://github.com/correlator-io/correlator-airflow

Note:
    This is a skeleton implementation. Full functionality will be added after
    Task 1.2 research is complete.
"""

from importlib.metadata import PackageNotFoundError, version

__version__: str
try:
    __version__ = version("correlator-airflow")
except PackageNotFoundError:
    # Package not installed (development mode without editable install)
    __version__ = "0.0.0+dev"

__author__ = "Emmanuel King Kasulani"
__email__ = "kasulani@gmail.com"
__license__ = "Apache-2.0"

# Public API exports
__all__ = [
    "__version__",
    "create_run_event",
    "emit_events",
    "flatten_config",
    "load_yaml_config",
    "on_task_instance_failed",
    "on_task_instance_running",
    "on_task_instance_success",
]

from .config import flatten_config, load_yaml_config
from .emitter import create_run_event, emit_events
from .listener import (
    on_task_instance_failed,
    on_task_instance_running,
    on_task_instance_success,
)
