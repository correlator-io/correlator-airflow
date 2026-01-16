# Architecture

## Overview

`correlator-airflow` provides a **custom OpenLineage transport** that sends Airflow lineage events to Correlator for
automated incident correlation.

> **IMPORTANT:** This plugin requires **Airflow 2.11.0+ ONLY**. Older Airflow versions are NOT supported.

## Architecture Approach: Custom Transport

Unlike traditional Airflow plugins that implement listeners directly, `correlator-airflow` uses a **Custom OpenLineage
Transport** approach. This design decision provides significant advantages:

### Why Transport (Not Listener)?

| Aspect              | Listener Approach                   | Transport Approach (Chosen)        |
|---------------------|-------------------------------------|------------------------------------|
| **Extractor Logic** | Must reimplement all 50+ extractors | Reuses all built-in OL extractors  |
| **Maintenance**     | High - track OL spec changes        | Low - OL provider handles changes  |
| **Code Size**       | ~2000+ lines                        | ~150 lines                         |
| **Compatibility**   | Tied to specific Airflow versions   | Works with any OL provider version |

### The Key Insight

Correlator requires events wrapped in an array (`[{event}]`), but OpenLineage's `HttpTransport` sends single objects (
`{event}`). This format incompatibility is the primary reason for our custom transport.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Airflow (2.11.0+)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌─────────────────────┐    ┌───────────────────┐   │
│  │ Airflow Task │───►│ OL Provider Listener│───►│  OL Extractors    │   │
│  └──────────────┘    │ (built-in)          │    │  (50+ built-in)   │   │
│                      └─────────────────────┘    └─────────┬─────────┘   │
│                                                           │             │
│                                                           ▼             │
│                                                  ┌───────────────────┐  │
│                                                  │ RunEvent object   │  │
│                                                  └─────────┬─────────┘  │
│                                                            │            │
└────────────────────────────────────────────────────────────┼────────────┘
                                                             │
                                                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    correlator-airflow (this plugin)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐    ┌───────────────────┐    ┌──────────────┐   │
│  │ CorrelatorTransport │───►│   emit_events()   │───►│ attr.asdict()│   │
│  │ (receives RunEvent) │    │ (serializes event)│    │ (HTTP POST)  │   │
│  └─────────────────────┘    └───────────────────┘    └──────┬───────┘   │
│                                                             │           │
└─────────────────────────────────────────────────────────────┼───────────┘
                                                              │
                                                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              Correlator                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  POST /api/v1/lineage/events                                            │
│  Body: [{event}]  ◄── Array-wrapped (Correlator requirement)            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

### Transport (`transport.py`)

The core component that integrates with OpenLineage's transport system:

```python
class CorrelatorTransport(Transport):
    """OpenLineage transport that sends events to Correlator."""

    kind = "correlator"  # Used in openlineage.yml: type: correlator
    config_class = CorrelatorConfig

    def emit(self, event: RunEvent) -> None:
        """Emit a single event to Correlator (wrapped in array)."""
```

**Key responsibilities:**

- Receives `RunEvent` objects from OpenLineage provider
- Creates and configures HTTP session (SSL verification, timeout)
- Passes RunEvent to `emit_events()` (which handles serialization)
- Implements fire-and-forget pattern (errors logged, never raised)

### Emitter (`emitter.py`)

Serialization and HTTP communication layer with Correlator:

```python
def emit_events(
    events: list[Event],  # RunEvent, DatasetEvent, or JobEvent
    endpoint: str,
    api_key: Optional[str] = None,
    session: Optional[requests.Session] = None,
    timeout: int = 30,
) -> None:
    """Serialize and send events to Correlator's lineage endpoint."""
```

**Key responsibilities:**

- Serializes RunEvent objects using `attr.asdict()` with custom datetime/UUID handling
- Wraps events in array for Correlator API format
- Uses pre-configured HTTP session (or creates default)
- Handles all HTTP communication

**Response handling:**

- `200/204` - Success, log INFO message with summary
- `207 Multi-Status` - Partial success, log warnings for failed events
- `400/422` - Validation error, raise `ValueError`
- `429` - Rate limited, raise `ValueError`
- `5xx` - Server error, raise `ValueError`

**Error propagation:**

- Emitter raises exceptions on errors
- Transport catches all exceptions (fire-and-forget)
- This ensures lineage failures never affect Airflow task execution

### CLI (`cli.py`)

Minimal CLI for version info and utilities:

```bash
airflow-correlator --version
airflow-correlator --help
```

## OpenLineage Event Format

Events follow the OpenLineage v1.0 specification:

```json
{
  "eventTime": "2024-01-01T12:00:00Z",
  "eventType": "START|COMPLETE|FAIL",
  "producer": "https://github.com/correlator-io/correlator-airflow/{version}",
  "schemaURL": "https://openlineage.io/spec/1-0-0/OpenLineage.json",
  "run": {
    "runId": "{dag_run_id}.{task_id}"
  },
  "job": {
    "namespace": "airflow",
    "name": "{dag_id}.{task_id}"
  },
  "inputs": [
    ...
  ],
  "outputs": [
    ...
  ]
}
```

## Configuration

### Option 1: openlineage.yml (Recommended)

```yaml
transport:
  type: correlator
  url: http://localhost:8080
  api_key: ${CORRELATOR_API_KEY}
  timeout: 30
  verify_ssl: true
```

### Option 2: Environment Variable

```bash
export AIRFLOW__OPENLINEAGE__TRANSPORT='{"type": "correlator", "url": "http://localhost:8080"}'
```

## Requirements

- **Airflow 2.11.0+ ONLY** (older versions NOT supported)
- `apache-airflow-providers-openlineage>=2.0.0`
- `correlator-airflow` package installed

## Fire-and-Forget Pattern

Lineage emission follows a strict fire-and-forget pattern:

1. **Emitter** raises exceptions on any error (connection, timeout, validation)
2. **Transport** catches ALL exceptions and logs them
3. **Result**: Airflow task execution is NEVER affected by lineage failures

This design ensures observability doesn't impact reliability.

---

*Architecture last updated: January 14, 2026*
