# Architecture

> **Note:** This is a placeholder document. Full architecture documentation will be added after Task 1.7 (Integration test) is complete.

## Overview

`correlator-airflow` is an Airflow plugin that emits OpenLineage events to Correlator for automated incident correlation.

## Components

### Listener (`listener.py`)

The listener hooks into Airflow's task lifecycle events:

- `on_task_instance_running()` - Emits START event when task begins
- `on_task_instance_success()` - Emits COMPLETE event when task succeeds
- `on_task_instance_failed()` - Emits FAIL event when task fails

### Emitter (`emitter.py`)

Constructs and emits OpenLineage events to Correlator:

- `create_run_event()` - Creates OpenLineage RunEvent
- `emit_events()` - Sends events via HTTP POST

### Configuration (`config.py`)

Handles configuration loading:

- YAML config file (`.airflow-correlator.yml`)
- Environment variable interpolation
- Priority: CLI args > env vars > config file > defaults

### CLI (`cli.py`)

Minimal CLI for configuration and debugging:

- `airflow-correlator --version` - Show version
- `airflow-correlator --help` - Show help

## Data Flow

```
Airflow Task Execution
        │
        ▼
┌───────────────────┐
│  Listener Hooks   │
│  (lifecycle)      │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Event Emitter    │
│  (OpenLineage)    │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│    Correlator     │
│    (backend)      │
└───────────────────┘
```

## OpenLineage Event Structure

Events follow the OpenLineage v1.0 specification:

```json
{
  "eventTime": "2024-01-01T12:00:00Z",
  "eventType": "START|COMPLETE|FAIL",
  "producer": "https://github.com/correlator-io/airflow-correlator/{version}",
  "schemaURL": "https://openlineage.io/spec/1-0-0/OpenLineage.json",
  "run": {
    "runId": "{dag_run_id}.{task_id}"
  },
  "job": {
    "namespace": "airflow",
    "name": "{dag_id}.{task_id}"
  },
  "inputs": [...],
  "outputs": [...]
}
```

## Integration Points

- **Airflow**: Task lifecycle hooks via `ListenerPlugin`
- **Correlator**: HTTP POST to `/api/v1/lineage/events`
- **OpenLineage**: Standard event format

---

*Full documentation will be added in Task 1.3 (Core listener implementation).*
