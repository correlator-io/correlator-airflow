"""correlator-airflow: Custom OpenLineage transport for Correlator.

This plugin provides a custom transport that integrates with Airflow's OpenLineage
provider. The OpenLineage provider handles task lifecycle events and extraction,
while our transport sends the events to Correlator's API.

Key Features:
    - Zero-config integration with Airflow's OpenLineage provider
    - Reuses all 50+ built-in OpenLineage extractors
    - Array-wrapped events for Correlator API compatibility
    - Fire-and-forget: lineage failures don't affect task execution

Architecture:
    Airflow Task → [OL Provider Listener] → [OL Extractors] → [CorrelatorTransport] → Correlator

Requirements:
    - Airflow 2.11.0+ ONLY (older versions NOT supported)
    - apache-airflow-providers-openlineage>=2.0.0

Configuration:
    Option 1 - openlineage.yml:
        transport:
          type: correlator
          url: http://localhost:8080
          api_key: ${CORRELATOR_API_KEY}

    Option 2 - Environment variable:
        AIRFLOW__OPENLINEAGE__TRANSPORT='{"type": "correlator", "url": "http://localhost:8080"}'

For detailed documentation, see: https://github.com/correlator-io/correlator-airflow
"""

from importlib.metadata import PackageNotFoundError, version

__version__: str
try:
    __version__ = version("correlator-airflow")
except PackageNotFoundError:
    # Package not installed (development mode without editable install)
    __version__ = "0.0.0+dev"

__author__ = "Correlator Team"
__license__ = "Apache-2.0"

# Public API exports
__all__ = [
    "CorrelatorConfig",
    "CorrelatorTransport",
    "__version__",
    "emit_events",
]

from airflow_correlator.emitter import emit_events
from airflow_correlator.transport import CorrelatorConfig, CorrelatorTransport
