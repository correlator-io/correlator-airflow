"""Tests for CorrelatorTransport.

This module tests the OpenLineage transport that sends events to Correlator.

Test Coverage:
    - CorrelatorConfig: Configuration loading from dict
    - CorrelatorTransport: Event emission to Correlator
    - Session configuration and usage
"""

from enum import Enum
from unittest.mock import patch

import attr
import pytest
import requests

from airflow_correlator.transport import (
    CorrelatorConfig,
    CorrelatorTransport,
)

# =============================================================================
# Test Fixtures
#
# These mocks match the real OL SDK types:
#   - eventType: Enum (not str) — matches openlineage.client.event_v2.EventType
#   - eventTime: str (not datetime) — the SDK uses ISO 8601 strings
# =============================================================================


class MockEventType(Enum):
    """Mock EventType enum matching openlineage.client.event_v2.EventType."""

    START = "START"
    COMPLETE = "COMPLETE"


@attr.define
class MockRun:
    """Mock OpenLineage Run object."""

    runId: str


@attr.define
class MockJob:
    """Mock OpenLineage Job object."""

    namespace: str
    name: str


@attr.define
class MockRunEvent:
    """Mock OpenLineage RunEvent for testing."""

    eventType: MockEventType
    eventTime: str
    run: MockRun
    job: MockJob


def create_mock_event() -> MockRunEvent:
    """Create a mock RunEvent for testing."""
    return MockRunEvent(
        eventType=MockEventType.START,
        eventTime="2024-01-15T10:30:00",
        run=MockRun(runId="test-run-123"),
        job=MockJob(namespace="airflow", name="dag.task"),
    )


# =============================================================================
# A. CorrelatorConfig Tests
# =============================================================================


@pytest.mark.unit
class TestCorrelatorConfig:
    """Tests for CorrelatorConfig dataclass."""

    def test_from_dict_with_all_fields(self) -> None:
        """Config loads all fields from dictionary."""
        params = {
            "url": "http://localhost:8080",
            "api_key": "test-api-key",
            "timeout": 60,
            "verify_ssl": False,
        }
        config = CorrelatorConfig.from_dict(params)

        assert config.url == "http://localhost:8080"
        assert config.api_key == "test-api-key"
        assert config.timeout == 60
        assert config.verify_ssl is False

    def test_from_dict_with_defaults(self) -> None:
        """Config uses defaults for missing optional fields."""
        params = {"url": "http://localhost:8080"}
        config = CorrelatorConfig.from_dict(params)

        assert config.url == "http://localhost:8080"
        assert config.api_key is None
        assert config.timeout == 30
        assert config.verify_ssl is True

    def test_from_dict_empty_url(self) -> None:
        """Config handles empty URL (will be validated by transport)."""
        params = {}
        config = CorrelatorConfig.from_dict(params)

        assert config.url == ""
        assert config.api_key is None

    def test_direct_instantiation(self) -> None:
        """Config can be instantiated directly with keyword args."""
        config = CorrelatorConfig(
            url="http://correlator:8080",
            api_key="my-key",
            timeout=45,
            verify_ssl=False,
        )

        assert config.url == "http://correlator:8080"
        assert config.api_key == "my-key"
        assert config.timeout == 45
        assert config.verify_ssl is False


# =============================================================================
# B. CorrelatorTransport Class Attributes Tests
# =============================================================================


@pytest.mark.unit
class TestCorrelatorTransportAttributes:
    """Tests for CorrelatorTransport class attributes."""

    def test_kind_is_correlator(self) -> None:
        """Transport kind is 'correlator' for OpenLineage discovery."""
        assert CorrelatorTransport.kind == "correlator"

    def test_config_class_is_correlator_config(self) -> None:
        """Transport config_class is CorrelatorConfig."""
        assert CorrelatorTransport.config_class is CorrelatorConfig


# =============================================================================
# C. CorrelatorTransport Initialization Tests
# =============================================================================


@pytest.mark.unit
class TestCorrelatorTransportInit:
    """Tests for CorrelatorTransport initialization."""

    def test_init_creates_session(self) -> None:
        """Transport creates a requests.Session on init."""
        config = CorrelatorConfig(url="http://localhost:8080")
        transport = CorrelatorTransport(config)

        assert hasattr(transport, "_session")
        assert isinstance(transport._session, requests.Session)

    def test_init_configures_session_verify_ssl_true(self) -> None:
        """Session is configured with verify_ssl=True by default."""
        config = CorrelatorConfig(url="http://localhost:8080", verify_ssl=True)
        transport = CorrelatorTransport(config)

        assert transport._session.verify is True

    def test_init_configures_session_verify_ssl_false(self) -> None:
        """Session is configured with verify_ssl=False when specified."""
        config = CorrelatorConfig(url="http://localhost:8080", verify_ssl=False)
        transport = CorrelatorTransport(config)

        assert transport._session.verify is False

    def test_init_logs_warning_when_url_not_configured(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Transport logs warning when URL is not configured."""
        config = CorrelatorConfig(url="")
        CorrelatorTransport(config)

        assert "Correlator URL not configured" in caplog.text


# =============================================================================
# D. CorrelatorTransport.emit() Tests
# =============================================================================


@pytest.mark.unit
class TestCorrelatorTransportEmit:
    """Tests for CorrelatorTransport.emit() method."""

    def test_emit_calls_emit_events_with_correct_params(self) -> None:
        """Emit calls emit_events with event, endpoint, api_key, session, timeout."""
        config = CorrelatorConfig(
            url="http://localhost:8080",
            api_key="test-key",
            timeout=45,
            verify_ssl=False,
        )
        transport = CorrelatorTransport(config)
        mock_event = create_mock_event()

        with patch("airflow_correlator.transport.emit_events") as mock_emit:
            transport.emit(mock_event)

            mock_emit.assert_called_once()
            call_kwargs = mock_emit.call_args[1]

            assert call_kwargs["events"] == [mock_event]
            assert (
                call_kwargs["endpoint"] == "http://localhost:8080/api/v1/lineage/events"
            )
            assert call_kwargs["api_key"] == "test-key"
            assert call_kwargs["session"] is transport._session
            assert call_kwargs["timeout"] == 45

    def test_emit_strips_trailing_slash_from_url(self) -> None:
        """Emit strips trailing slash from URL before appending path."""
        config = CorrelatorConfig(url="http://localhost:8080/")
        transport = CorrelatorTransport(config)

        with patch("airflow_correlator.transport.emit_events") as mock_emit:
            transport.emit(create_mock_event())

            call_kwargs = mock_emit.call_args[1]
            assert (
                call_kwargs["endpoint"] == "http://localhost:8080/api/v1/lineage/events"
            )

    def test_emit_without_url_does_nothing(self) -> None:
        """Emit with empty URL does nothing (no-op)."""
        config = CorrelatorConfig(url="")
        transport = CorrelatorTransport(config)

        with patch("airflow_correlator.transport.emit_events") as mock_emit:
            transport.emit(create_mock_event())
            mock_emit.assert_not_called()

    def test_emit_passes_configured_session(self) -> None:
        """Emit passes the transport's configured session to emit_events."""
        config = CorrelatorConfig(url="http://localhost:8080", verify_ssl=False)
        transport = CorrelatorTransport(config)

        with patch("airflow_correlator.transport.emit_events") as mock_emit:
            transport.emit(create_mock_event())

            call_kwargs = mock_emit.call_args[1]
            session = call_kwargs["session"]

            # Verify session has SSL verification disabled
            assert session.verify is False


# =============================================================================
# E. CorrelatorTransport Fire-and-Forget Tests
# =============================================================================


@pytest.mark.unit
class TestCorrelatorTransportFireAndForget:
    """Tests for fire-and-forget behavior."""

    def test_emit_catches_emit_events_exceptions(self) -> None:
        """Emit catches exceptions from emit_events (fire-and-forget)."""
        config = CorrelatorConfig(url="http://localhost:8080")
        transport = CorrelatorTransport(config)

        with patch("airflow_correlator.transport.emit_events") as mock_emit:
            mock_emit.side_effect = ConnectionError("Connection refused")

            # Should not raise - fire-and-forget
            transport.emit(create_mock_event())

    def test_emit_catches_timeout_errors(self) -> None:
        """Emit catches TimeoutError from emit_events."""
        config = CorrelatorConfig(url="http://localhost:8080")
        transport = CorrelatorTransport(config)

        with patch("airflow_correlator.transport.emit_events") as mock_emit:
            mock_emit.side_effect = TimeoutError("Request timed out")

            # Should not raise - fire-and-forget
            transport.emit(create_mock_event())

    def test_emit_catches_value_errors(self) -> None:
        """Emit catches ValueError from emit_events (server errors)."""
        config = CorrelatorConfig(url="http://localhost:8080")
        transport = CorrelatorTransport(config)

        with patch("airflow_correlator.transport.emit_events") as mock_emit:
            mock_emit.side_effect = ValueError("Server returned 500")

            # Should not raise - fire-and-forget
            transport.emit(create_mock_event())

    def test_emit_logs_error_on_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Emit logs error when emit_events raises exception."""
        config = CorrelatorConfig(url="http://localhost:8080")
        transport = CorrelatorTransport(config)

        with patch("airflow_correlator.transport.emit_events") as mock_emit:
            mock_emit.side_effect = ConnectionError("Connection refused")

            transport.emit(create_mock_event())

            assert "Failed to emit lineage event" in caplog.text


# =============================================================================
# F. Integration Tests
# =============================================================================


@pytest.mark.unit
class TestCorrelatorTransportIntegration:
    """Integration tests for CorrelatorTransport."""

    def test_emit_passes_event_object_directly(self) -> None:
        """Transport passes RunEvent object directly to emit_events (no serialization)."""
        config = CorrelatorConfig(url="http://localhost:8080")
        transport = CorrelatorTransport(config)
        event = create_mock_event()

        with patch("airflow_correlator.transport.emit_events") as mock_emit:
            transport.emit(event)

            call_kwargs = mock_emit.call_args[1]
            events = call_kwargs["events"]

            # Event is passed directly, not serialized
            assert len(events) == 1
            assert events[0] is event  # Same object reference

    def test_full_config_flow(self) -> None:
        """Test complete config → transport → emit flow."""
        # Simulate OpenLineage config loading
        params = {
            "url": "http://correlator.example.com",
            "api_key": "secret-key",
            "timeout": 60,
            "verify_ssl": False,
        }
        config = CorrelatorConfig.from_dict(params)

        # Create transport
        transport = CorrelatorTransport(config)

        # Verify transport is configured correctly
        assert transport.config.url == "http://correlator.example.com"
        assert transport._session.verify is False

        # Emit event
        with patch("airflow_correlator.transport.emit_events") as mock_emit:
            transport.emit(create_mock_event())

            call_kwargs = mock_emit.call_args[1]
            assert (
                call_kwargs["endpoint"]
                == "http://correlator.example.com/api/v1/lineage/events"
            )
            assert call_kwargs["api_key"] == "secret-key"
            assert call_kwargs["timeout"] == 60
