"""Correlator transport for OpenLineage events.

This transport sends OpenLineage events to Correlator's /api/v1/lineage/events
endpoint using a configured HTTP session.

Why Custom Transport:
    Correlator API requires: [{ event }]
    OpenLineage HttpTransport sends: { event }
    This format incompatibility requires a custom transport.

Usage:
    Configure in openlineage.yml or via AIRFLOW__OPENLINEAGE__TRANSPORT env var.
    See docs/CONFIGURATION.md for details.

Requirements:
    - Airflow 2.11.0+ ONLY (older versions NOT supported)
    - apache-airflow-providers-openlineage>=2.0.0
"""

import logging
from typing import Any, Optional

import attr
import requests
from openlineage.client.transport import Config, Transport

from airflow_correlator.emitter import Event, emit_events

logger = logging.getLogger(__name__)


@attr.define  # type: ignore[attr-defined]
class CorrelatorConfig(Config):
    """Configuration for Correlator transport.

    This config is loaded by OpenLineage's transport discovery mechanism
    from openlineage.yml or environment variables.

    Attributes:
        url: Correlator API base URL (e.g., http://localhost:8080).
        api_key: Optional API key for X-API-Key header authentication.
        timeout: Request timeout in seconds (default: 30).
        verify_ssl: Whether to verify SSL certificates (default: True).
    """

    url: str = ""
    api_key: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True

    @classmethod
    def from_dict(cls, params: dict[str, Any]) -> "CorrelatorConfig":
        """Create config from dictionary (OpenLineage config loader).

        Called by OpenLineage's transport discovery to load config from
        openlineage.yml or AIRFLOW__OPENLINEAGE__TRANSPORT JSON.

        Args:
            params: Dictionary of configuration parameters.

        Returns:
            CorrelatorConfig instance.
        """
        return cls(  # type: ignore[call-arg]
            url=params.get("url", ""),
            api_key=params.get("api_key"),
            timeout=params.get("timeout", 30),
            verify_ssl=params.get("verify_ssl", True),
        )


class CorrelatorTransport(Transport):
    """OpenLineage transport that sends events to Correlator.

    This transport:
    1. Receives RunEvent from OpenLineage provider
    2. Passes event to emit_events() which handles serialization
    3. Uses pre-configured HTTP session for requests
    4. Handles response codes (200/204, 207, 4xx, 5xx)

    Errors are logged but never raised (fire-and-forget pattern).
    This ensures lineage emission failures don't affect Airflow task execution.

    Requirements:
        - Airflow 2.11.0+ ONLY (older versions NOT supported)
        - apache-airflow-providers-openlineage>=2.0.0

    Example openlineage.yml:
        transport:
          type: correlator
          url: http://localhost:8080
          api_key: ${CORRELATOR_API_KEY}
          timeout: 30
          verify_ssl: true

    Example environment variable:
        AIRFLOW__OPENLINEAGE__TRANSPORT='{"type": "correlator", "url": "http://localhost:8080"}'
    """

    kind = "correlator"
    config_class = CorrelatorConfig

    def __init__(self, config: CorrelatorConfig) -> None:
        """Initialize transport with configuration.

        Creates a pre-configured HTTP session with timeout and SSL settings.
        This session is passed to emit_events() for all requests.

        Args:
            config: Transport configuration from OpenLineage config loader.
        """
        self.config = config
        self.log = logging.getLogger(__name__)

        # Create configured HTTP session
        self._session = requests.Session()
        self._session.verify = config.verify_ssl
        # Note: timeout is set per-request via session.request() timeout param
        # We store it for use in emit(), but Session doesn't have a timeout attr

        if not config.url:
            self.log.warning(
                "Correlator URL not configured. Events will not be emitted. "
                "Set 'url' in openlineage.yml or AIRFLOW__OPENLINEAGE__TRANSPORT."
            )

    def emit(self, event: Event) -> None:  # type: ignore[override]
        """Emit a single OpenLineage event to Correlator.

        Passes the event to emit_events() which handles serialization and
        HTTP communication. Errors are logged but not raised (fire-and-forget).

        Args:
            event: OpenLineage event (RunEvent, DatasetEvent, or JobEvent) to emit.
        """
        if not self.config.url:
            return

        try:
            # Pass RunEvent directly - emit_events handles serialization
            emit_events(
                events=[event],
                endpoint=f"{self.config.url.rstrip('/')}/api/v1/lineage/events",
                api_key=self.config.api_key,
                session=self._session,
                timeout=self.config.timeout,
            )

        except Exception as e:
            # Fire-and-forget: log and continue, never raise
            # This ensures lineage failures don't affect Airflow task execution
            self.log.error(
                f"Failed to emit lineage event to Correlator: {e}",
                exc_info=True,
            )
