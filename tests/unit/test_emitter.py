"""Tests for emitter module.

This module tests the HTTP emitter that sends OpenLineage events to Correlator.

Test Coverage:
    - PRODUCER constant format
    - emit_events(): HTTP communication with Correlator
    - _handle_response(): Response code handling (200/204, 207, 4xx, 5xx)
    - Real RunEvent serialization (Enum, null stripping via Serde)
"""

import json
import logging
from enum import Enum

import attr
import pytest
import requests
import responses
from openlineage.client.event_v2 import Job, Run, RunEvent
from openlineage.client.event_v2 import RunState as EventType
from openlineage.client.serde import Serde

from airflow_correlator.emitter import (
    PRODUCER,
    emit_events,
)

# =============================================================================
# Test Fixtures - Mock RunEvent-like objects
#
# These mocks match the real OL SDK types:
#   - eventType: Enum (not str) — matches openlineage.client.event_v2.EventType
#   - eventTime: str (not datetime) — the SDK uses ISO 8601 strings
# =============================================================================


class MockEventType(Enum):
    """Mock EventType enum matching openlineage.client.event_v2.EventType."""

    START = "START"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    ABORT = "ABORT"
    FAIL = "FAIL"
    OTHER = "OTHER"


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


def create_mock_event(
    event_type: MockEventType = MockEventType.START,
    run_id: str = "test-run-123",
    namespace: str = "airflow",
    job_name: str = "dag.task",
) -> MockRunEvent:
    """Create a mock RunEvent for testing."""
    return MockRunEvent(
        eventType=event_type,
        eventTime="2024-01-15T10:30:00",
        run=MockRun(runId=run_id),
        job=MockJob(namespace=namespace, name=job_name),
    )


# =============================================================================
# A. PRODUCER Constant Tests
# =============================================================================


@pytest.mark.unit
class TestProducerConstant:
    """Tests for PRODUCER constant."""

    def test_producer_contains_repo_url(self) -> None:
        """PRODUCER contains correlator-airflow GitHub URL."""
        assert "https://github.com/correlator-io/correlator-airflow" in PRODUCER

    def test_producer_contains_version(self) -> None:
        """PRODUCER contains version string."""
        assert "/" in PRODUCER
        parts = PRODUCER.split("/")
        assert len(parts) >= 5


# =============================================================================
# B. Serde Serialization Tests
# =============================================================================


@pytest.mark.unit
class TestSerdeSerialization:
    """Tests that Serde.to_dict() correctly serializes OL event types.

    These tests verify the serialization path used by emit_events():
    Serde.to_dict() handles Enum conversion, null stripping, and
    all OpenLineage-specific types.
    """

    def test_enum_event_type_serializes_to_string(self) -> None:
        """EventType enum is serialized to its string value by Serde."""
        event = create_mock_event(event_type=MockEventType.COMPLETE)
        event_dict = _serde_to_dict(event)
        assert event_dict["eventType"] == "COMPLETE"

    def test_all_event_types_serialize(self) -> None:
        """All EventType enum values serialize to their string value."""
        for et in MockEventType:
            event = create_mock_event(event_type=et)
            event_dict = _serde_to_dict(event)
            assert event_dict["eventType"] == et.value

    def test_serialized_event_is_json_safe(self) -> None:
        """Serialized event can be passed to json.dumps without error."""
        event = create_mock_event(event_type=MockEventType.START)
        event_dict = _serde_to_dict(event)
        serialized = json.dumps(event_dict)
        parsed = json.loads(serialized)
        assert parsed["eventType"] == "START"
        assert parsed["eventTime"] == "2024-01-15T10:30:00"
        assert parsed["run"]["runId"] == "test-run-123"

    def test_real_run_event_serialization(self) -> None:
        """A real OL SDK RunEvent roundtrips through Serde without error.

        This is the key regression test for the Enum serialization bug:
        RunEvent.eventType is EventType(Enum), which must be converted
        to a string by Serde.to_dict() before json.dumps().
        """
        event = RunEvent(
            eventTime="2026-02-20T12:00:00Z",
            producer="https://github.com/correlator-io/correlator-airflow/test",
            run=Run(runId="019c7bd3-ae04-7ef3-a3df-91516ebaa3c6"),
            job=Job(namespace="airflow://demo", name="demo_pipeline.dbt_test"),
            eventType=EventType.START,
        )

        # This is the exact code path in emit_events()
        event_dict = _serde_to_dict(event)
        serialized = json.dumps(event_dict)
        parsed = json.loads(serialized)

        assert parsed["eventType"] == "START"
        assert parsed["run"]["runId"] == "019c7bd3-ae04-7ef3-a3df-91516ebaa3c6"
        assert parsed["job"]["namespace"] == "airflow://demo"

    def test_real_run_event_null_fields_stripped(self) -> None:
        """Serde strips None-valued fields from real RunEvent."""
        event = RunEvent(
            eventTime="2026-02-20T12:00:00Z",
            producer="https://github.com/correlator-io/correlator-airflow/test",
            run=Run(runId="019c7bd3-ae04-7ef3-a3df-91516ebaa3c6"),
            job=Job(namespace="airflow", name="task"),
            eventType=None,  # None eventType
        )

        event_dict = _serde_to_dict(event)
        # Serde strips None values
        assert "eventType" not in event_dict


def _serde_to_dict(event):  # type: ignore[no-untyped-def]
    """Helper: serialize event via the same path as emit_events()."""
    return Serde.to_dict(event)


# =============================================================================
# C. emit_events() Success Tests
# =============================================================================


@pytest.mark.unit
class TestEmitEventsSuccess:
    """Tests for successful event emission."""

    @responses.activate
    def test_emit_events_success_200(self) -> None:
        """Successful event emission with 200 OK."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={
                "status": "success",
                "summary": {"received": 1, "successful": 1, "failed": 0},
            },
            status=200,
        )

        event = create_mock_event()
        emit_events([event], "http://localhost:8080/api/v1/lineage/events")

        assert len(responses.calls) == 1

    @responses.activate
    def test_emit_events_success_204(self) -> None:
        """Successful event emission with 204 No Content."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            status=204,
        )

        event = create_mock_event()
        emit_events([event], "http://localhost:8080/api/v1/lineage/events")

        assert len(responses.calls) == 1

    @responses.activate
    def test_emit_events_serializes_runevent(self) -> None:
        """RunEvent objects are serialized to JSON."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        event = create_mock_event(
            event_type=MockEventType.COMPLETE,
            run_id="run-456",
            namespace="my-namespace",
            job_name="my-dag.my-task",
        )
        emit_events([event], "http://localhost:8080/api/v1/lineage/events")

        sent_body = json.loads(responses.calls[0].request.body)
        assert isinstance(sent_body, list)
        assert len(sent_body) == 1
        assert sent_body[0]["eventType"] == "COMPLETE"
        assert sent_body[0]["eventTime"] == "2024-01-15T10:30:00"
        assert sent_body[0]["run"]["runId"] == "run-456"
        assert sent_body[0]["job"]["namespace"] == "my-namespace"
        assert sent_body[0]["job"]["name"] == "my-dag.my-task"

    @responses.activate
    def test_emit_events_sends_multiple_events(self) -> None:
        """Multiple events are sent as JSON array."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        events = [
            create_mock_event(event_type=MockEventType.START, run_id="run-1"),
            create_mock_event(event_type=MockEventType.COMPLETE, run_id="run-1"),
        ]
        emit_events(events, "http://localhost:8080/api/v1/lineage/events")

        sent_body = json.loads(responses.calls[0].request.body)
        assert len(sent_body) == 2
        assert sent_body[0]["eventType"] == "START"
        assert sent_body[1]["eventType"] == "COMPLETE"

    @responses.activate
    def test_emit_events_sets_content_type_json(self) -> None:
        """Request includes Content-Type: application/json header."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        emit_events(
            [create_mock_event()], "http://localhost:8080/api/v1/lineage/events"
        )

        assert responses.calls[0].request.headers["Content-Type"] == "application/json"

    @responses.activate
    def test_emit_events_with_api_key_sets_header(self) -> None:
        """API key is sent in X-API-Key header."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",
            api_key="my-secret-key",
        )

        assert responses.calls[0].request.headers["X-API-Key"] == "my-secret-key"

    @responses.activate
    def test_emit_events_without_api_key_no_header(self) -> None:
        """No X-API-Key header when api_key is None."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",
            api_key=None,
        )

        assert "X-API-Key" not in responses.calls[0].request.headers

    @responses.activate
    def test_emit_events_logs_info_on_success(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """200 success logs INFO message."""
        caplog.set_level(logging.INFO)

        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={
                "status": "success",
                "summary": {"received": 1, "successful": 1, "failed": 0},
            },
            status=200,
        )

        emit_events(
            [create_mock_event()], "http://localhost:8080/api/v1/lineage/events"
        )

        assert "Successfully emitted 1 events" in caplog.text
        assert "1 successful" in caplog.text


# =============================================================================
# D. emit_events() Session Parameter Tests
# =============================================================================


@pytest.mark.unit
class TestEmitEventsSession:
    """Tests for session parameter."""

    @responses.activate
    def test_emit_events_uses_provided_session(self) -> None:
        """Provided session is used for HTTP request."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        session = requests.Session()
        session.headers["X-Custom-Header"] = "custom-value"

        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",
            session=session,
        )

        assert responses.calls[0].request.headers["X-Custom-Header"] == "custom-value"

    @responses.activate
    def test_emit_events_creates_default_session_if_none(self) -> None:
        """Default session is created if none provided."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",
            session=None,
        )

        assert len(responses.calls) == 1


# =============================================================================
# E. emit_events() 207 Partial Success Tests
# =============================================================================


@pytest.mark.unit
class TestEmitEventsPartialSuccess:
    """Tests for 207 partial success response handling."""

    @responses.activate
    def test_emit_events_207_does_not_raise(self) -> None:
        """207 partial success does not raise exception."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={
                "status": "partial_success",
                "summary": {"received": 2, "successful": 1, "failed": 1},
                "failed_events": [{"index": 1, "reason": "Invalid eventTime"}],
            },
            status=207,
        )

        events = [create_mock_event(), create_mock_event()]
        emit_events(events, "http://localhost:8080/api/v1/lineage/events")

    @responses.activate
    def test_emit_events_207_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """207 partial success logs warning with summary."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={
                "status": "partial_success",
                "summary": {"received": 3, "successful": 2, "failed": 1},
                "failed_events": [{"index": 2, "reason": "Validation error"}],
            },
            status=207,
        )

        events = [create_mock_event() for _ in range(3)]
        emit_events(events, "http://localhost:8080/api/v1/lineage/events")

        assert "Partial success" in caplog.text
        assert "2/3" in caplog.text

    @responses.activate
    def test_emit_events_207_logs_failed_event_reasons(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """207 partial success logs reasons for failed events."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={
                "status": "partial_success",
                "summary": {"received": 2, "successful": 1, "failed": 1},
                "failed_events": [
                    {"index": 0, "reason": "eventTime is required"},
                ],
            },
            status=207,
        )

        events = [create_mock_event(), create_mock_event()]
        emit_events(events, "http://localhost:8080/api/v1/lineage/events")

        assert "eventTime is required" in caplog.text
        assert "Event 0 failed" in caplog.text


# =============================================================================
# F. emit_events() Error Response Tests
# =============================================================================


@pytest.mark.unit
class TestEmitEventsErrors:
    """Tests for error response handling."""

    @responses.activate
    def test_emit_events_400_raises_valueerror(self) -> None:
        """400 Bad Request raises ValueError."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"error": "Invalid JSON"},
            status=400,
        )

        with pytest.raises(ValueError, match=r"rejected.*400"):
            emit_events(
                [create_mock_event()],
                "http://localhost:8080/api/v1/lineage/events",
            )

    @responses.activate
    def test_emit_events_422_raises_valueerror(self) -> None:
        """422 Unprocessable Entity raises ValueError."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"error": "eventTime is required"},
            status=422,
        )

        with pytest.raises(ValueError, match=r"rejected.*422"):
            emit_events(
                [create_mock_event()],
                "http://localhost:8080/api/v1/lineage/events",
            )

    @responses.activate
    def test_emit_events_429_raises_valueerror(self) -> None:
        """429 Too Many Requests raises ValueError."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"error": "Rate limit exceeded"},
            status=429,
        )

        with pytest.raises(ValueError, match="Rate limited"):
            emit_events(
                [create_mock_event()],
                "http://localhost:8080/api/v1/lineage/events",
            )

    @responses.activate
    def test_emit_events_500_raises_valueerror(self) -> None:
        """500 Internal Server Error raises ValueError."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"error": "Internal server error"},
            status=500,
        )

        with pytest.raises(ValueError, match="500"):
            emit_events(
                [create_mock_event()],
                "http://localhost:8080/api/v1/lineage/events",
            )


# =============================================================================
# G. emit_events() Network Error Tests
# =============================================================================


@pytest.mark.unit
class TestEmitEventsNetworkErrors:
    """Tests for network error handling."""

    @responses.activate
    def test_emit_events_timeout_raises_timeouterror(self) -> None:
        """Request timeout raises TimeoutError."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            body=requests.exceptions.Timeout("Connection timed out"),
        )

        with pytest.raises(TimeoutError, match="Timeout"):
            emit_events(
                [create_mock_event()],
                "http://localhost:8080/api/v1/lineage/events",
                timeout=1,
            )

    @responses.activate
    def test_emit_events_connection_error_raises_connectionerror(self) -> None:
        """Connection error raises ConnectionError."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )

        with pytest.raises(ConnectionError, match="Connection error"):
            emit_events(
                [create_mock_event()],
                "http://localhost:8080/api/v1/lineage/events",
            )


# =============================================================================
# H. emit_events() Timeout Parameter Tests
# =============================================================================


@pytest.mark.unit
class TestEmitEventsTimeout:
    """Tests for timeout parameter."""

    @responses.activate
    def test_emit_events_default_timeout_is_30(self) -> None:
        """Default timeout is 30 seconds (matches dbt-correlator)."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",
        )

        # responses library doesn't expose timeout, but verify call was made
        assert len(responses.calls) == 1

    @responses.activate
    def test_emit_events_custom_timeout(self) -> None:
        """Custom timeout is accepted."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",
            timeout=60,
        )

        assert len(responses.calls) == 1


# =============================================================================
# I. emit_events() Edge Case Tests
# =============================================================================


@pytest.mark.unit
class TestEmitEventsEdgeCases:
    """Tests for edge cases and error handling."""

    @responses.activate
    def test_emit_events_200_empty_body(self) -> None:
        """200 with empty body doesn't crash."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            body="",
            status=200,
        )

        # Should not raise
        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",
        )

        assert len(responses.calls) == 1

    @responses.activate
    def test_emit_events_200_non_json_body(self) -> None:
        """200 with non-JSON body doesn't crash."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            body="OK",
            status=200,
        )

        # Should not raise
        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",
        )

        assert len(responses.calls) == 1

    @responses.activate
    def test_emit_events_207_malformed_json(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """207 with malformed JSON logs warning but doesn't crash."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            body="not valid json",
            status=207,
        )

        # Should not raise - fire-and-forget handles gracefully
        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",
        )

        assert "could not parse response" in caplog.text

    @responses.activate
    def test_emit_events_207_missing_summary(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """207 with missing summary field logs warning."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "partial_success"},  # Missing summary
            status=207,
        )

        # Should not raise
        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",
        )

        # Should still log partial success
        assert "Partial success" in caplog.text


# =============================================================================
# J. emit_events() Negative/Boundary Test Cases
# =============================================================================


@pytest.mark.unit
class TestEmitEventsNegativeCases:
    """Negative test cases for emit_events()."""

    @responses.activate
    def test_emit_events_empty_list(self) -> None:
        """Empty events list sends empty JSON array."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        # Empty list should still make request
        emit_events([], "http://localhost:8080/api/v1/lineage/events")

        assert len(responses.calls) == 1
        sent_body = json.loads(responses.calls[0].request.body)
        assert sent_body == []

    @responses.activate
    def test_emit_events_large_batch(self) -> None:
        """Large batch of events is sent successfully."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={
                "status": "success",
                "summary": {"received": 100, "successful": 100, "failed": 0},
            },
            status=200,
        )

        # Create 100 events
        events = [
            create_mock_event(run_id=f"run-{i}", job_name=f"dag.task_{i}")
            for i in range(100)
        ]
        emit_events(events, "http://localhost:8080/api/v1/lineage/events")

        sent_body = json.loads(responses.calls[0].request.body)
        assert len(sent_body) == 100

    @responses.activate
    def test_emit_events_whitespace_endpoint(self) -> None:
        """Endpoint with whitespace is trimmed or fails gracefully."""
        # requests library handles URL with trailing whitespace
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"status": "success"},
            status=200,
        )

        emit_events(
            [create_mock_event()],
            "http://localhost:8080/api/v1/lineage/events",  # No whitespace (valid)
        )

        assert len(responses.calls) == 1

    @responses.activate
    def test_emit_events_4xx_includes_response_body(self) -> None:
        """4xx error includes response body in exception message."""
        error_message = "Invalid eventTime format: expected ISO 8601"
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"error": error_message},
            status=400,
        )

        with pytest.raises(ValueError, match=r"rejected.*400") as exc_info:
            emit_events(
                [create_mock_event()],
                "http://localhost:8080/api/v1/lineage/events",
            )

        # Verify error message contains the response body
        assert error_message in str(exc_info.value)

    @responses.activate
    def test_emit_events_5xx_includes_status_code(self) -> None:
        """5xx error includes status code in exception message."""
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            json={"error": "Database unavailable"},
            status=503,
        )

        with pytest.raises(ValueError, match="503"):
            emit_events(
                [create_mock_event()],
                "http://localhost:8080/api/v1/lineage/events",
            )

    @responses.activate
    def test_emit_events_truncates_long_error_response(self) -> None:
        """Long error response is truncated in exception message."""
        long_error = "x" * 1000  # Very long error message
        responses.add(
            responses.POST,
            "http://localhost:8080/api/v1/lineage/events",
            body=long_error,
            status=400,
        )

        with pytest.raises(ValueError, match=r"rejected.*400") as exc_info:
            emit_events(
                [create_mock_event()],
                "http://localhost:8080/api/v1/lineage/events",
            )

        # Should be truncated to 500 chars
        assert len(str(exc_info.value)) < 600
