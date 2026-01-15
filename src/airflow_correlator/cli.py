"""Command-line interface for airflow-correlator.

This module provides the CLI entry point using Click framework.
Currently provides version information only.

Usage:
    $ airflow-correlator --version
    $ airflow-correlator --help

Architecture:
    correlator-airflow uses a custom OpenLineage Transport (not a listener).
    The OpenLineage provider's built-in listener handles task lifecycle events,
    and our transport sends them to Correlator.

    Configuration is done via:
    - openlineage.yml (recommended)
    - AIRFLOW__OPENLINEAGE__TRANSPORT environment variable

Requirements:
    - Airflow 2.11.0+ ONLY (older versions NOT supported)
    - apache-airflow-providers-openlineage>=2.0.0
"""

import click

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="airflow-correlator")
def cli() -> None:
    """airflow-correlator: Emit Airflow task events as OpenLineage events.

    Automatically connects Airflow task executions to incident correlation
    through OpenLineage events. Works with Correlator or any OpenLineage-
    compatible backend.

    Configuration:
        Option 1 - openlineage.yml:
            transport:
              type: correlator
              url: http://localhost:8080

        Option 2 - Environment variable:
            AIRFLOW__OPENLINEAGE__TRANSPORT='{"type": "correlator", "url": "..."}'

    For more information: https://github.com/correlator-io/correlator-airflow
    """
    pass


if __name__ == "__main__":
    cli()
