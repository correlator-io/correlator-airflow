"""OpenLineage event emitter for Correlator.

This module handles HTTP communication with Correlator's lineage endpoint.
Consistent with correlator-dbt emitter pattern for PDK compatibility.

The emitter:
    - Accepts RunEvent objects (serialization via OL SDK's Serde)
    - Sends events to Correlator's /api/v1/lineage/events endpoint
    - Handles response codes (200/204, 207 partial success, 4xx, 5xx)
    - Raises exceptions on errors (transport layer catches them)

Architecture:
    Transport configures session → passes RunEvent to emit_events → HTTP POST

Requirements:
    - Airflow 2.11.0+ ONLY (older versions NOT supported)
    - apache-airflow-providers-openlineage>=2.0.0
"""

import logging
from typing import Optional, Union

import requests
from openlineage.client.event_v2 import (
    DatasetEvent,
    JobEvent,
    RunEvent,
)
from openlineage.client.serde import Serde

from airflow_correlator import __version__

logger = logging.getLogger(__name__)

# Producer URL for OpenLineage events (consistent with correlator-dbt)
# Note: Not used in Transport approach (OL provider sets producer), but kept for
# potential future use (e.g., manual event construction)
PRODUCER = f"https://github.com/correlator-io/correlator-airflow/{__version__}"

# Type alias for OpenLineage event types
Event = Union[RunEvent, DatasetEvent, JobEvent]


def emit_events(
    events: list[Event],
    endpoint: str,
    api_key: Optional[str] = None,
    session: Optional[requests.Session] = None,
    timeout: int = 30,
) -> None:
    """Emit OpenLineage events to Correlator.

    Serializes events and sends to Correlator's lineage endpoint.
    Events are wrapped in an array (Correlator API requirement).

    Args:
        events: List of OpenLineage event objects (RunEvent, DatasetEvent, JobEvent).
        endpoint: Full Correlator API endpoint URL.
        api_key: Optional API key for X-API-Key header.
        session: Pre-configured requests.Session. If None, creates default session.
        timeout: Request timeout in seconds (default: 30, matches dbt-correlator).

    Raises:
        ConnectionError: If unable to connect to Correlator.
        TimeoutError: If request times out.
        ValueError: If Correlator returns an error response (4xx, 5xx).

    Example:
        >>> from openlineage.client.run import RunEvent
        >>> events = [run_event]  # RunEvent object
        >>> emit_events(events, "http://localhost:8080/api/v1/lineage/events")
    """
    if session is None:
        session = requests.Session()

    # Serialize events using the OL SDK's Serde, which handles Enum conversion,
    # null stripping, and all OL-specific types. The SDK owns its type system;
    # we delegate serialization to it rather than reimplementing.
    event_dicts = [Serde.to_dict(event) for event in events]

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = session.post(
            endpoint,
            json=event_dicts,
            headers=headers,
            timeout=timeout,
        )
        _handle_response(response, len(events))

    except requests.exceptions.Timeout as e:
        raise TimeoutError(f"Timeout emitting events to {endpoint}") from e
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Connection error emitting events to {endpoint}") from e


def _handle_response(response: requests.Response, event_count: int) -> None:
    """Handle Correlator API response (matches correlator-dbt pattern).

    Args:
        response: HTTP response from Correlator.
        event_count: Number of events that were sent.

    Raises:
        ValueError: If response indicates an error (4xx, 5xx).
    """
    # Success: 200 OK or 204 No Content
    if response.status_code in (200, 204):
        logger.info(f"Successfully emitted {event_count} events")

        # Parse summary if available (200 with body)
        if response.status_code == 200 and response.text:
            try:
                body = response.json()
                if "summary" in body:
                    summary = body["summary"]
                    logger.info(
                        f"Response: {summary.get('successful', 0)} successful, "
                        f"{summary.get('failed', 0)} failed"
                    )
            except (ValueError, KeyError):
                pass  # Response parsing is best-effort
        return

    # Partial success: 207 Multi-Status
    if response.status_code == 207:
        try:
            body = response.json()
            summary = body.get("summary", {})
            successful = summary.get("successful", 0)
            received = summary.get("received", event_count)
            failed_events = body.get("failed_events", [])

            logger.warning(
                f"Partial success: {successful}/{received} events succeeded. "
                f"Failed events: {failed_events}"
            )

            # Log individual failures for debugging
            for failed in failed_events:
                index = failed.get("index", "?")
                reason = failed.get("reason", "Unknown error")
                logger.error(f"Event {index} failed: {reason}")
        except (ValueError, KeyError):
            logger.warning("Partial success (207) but could not parse response")
        return

    # Client errors: 4xx
    if response.status_code == 429:
        raise ValueError("Rate limited by Correlator")

    if 400 <= response.status_code < 500:
        raise ValueError(
            f"Event rejected by Correlator ({response.status_code}): "
            f"{response.text[:500]}"
        )

    # Server errors: 5xx or unexpected codes
    raise ValueError(
        f"Correlator returned {response.status_code}: {response.text[:500]}"
    )
