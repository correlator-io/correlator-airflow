# Configuration

## Overview

`correlator-airflow` provides a **custom OpenLineage transport** that sends Airflow lineage events to Correlator.
Configuration is done through OpenLineage's standard configuration mechanisms.

> **IMPORTANT:** Requires **Airflow 2.11.0+** and `apache-airflow-providers-openlineage>=2.0.0`

---

## Transport Type Names

The transport type name depends on how you're using OpenLineage:

| Context                                    | Transport Type                                     | Why                                       |
|--------------------------------------------|----------------------------------------------------|-------------------------------------------|
| **Airflow** (with OpenLineage provider)    | `correlator`                                       | Airflow's provider discovers entry points |
| **OpenLineage Python client** (standalone) | `airflow_correlator.transport.CorrelatorTransport` | Client requires full module path          |

---

## Configuration Options

### Option 1: Airflow Environment Variable (Recommended for Airflow)

```bash
export AIRFLOW__OPENLINEAGE__TRANSPORT='{"type": "correlator", "url": "http://localhost:8080"}'
```

### Option 2: openlineage.yml (For Airflow)

Create `openlineage.yml` in your Airflow home directory (`$AIRFLOW_HOME`):

```yaml
transport:
  type: correlator
  url: http://localhost:8080
  api_key: ${CORRELATOR_API_KEY}
```

### Option 3: openlineage.yml (For Standalone OpenLineage Client)

When using the OpenLineage Python client directly (not through Airflow), use the full module path:

```yaml
transport:
  type: airflow_correlator.transport.CorrelatorTransport
  url: http://localhost:8080
  api_key: ${CORRELATOR_API_KEY}
```

---

## Configuration Parameters

| Option       | Type   | Default    | Description                  |
|--------------|--------|------------|------------------------------|
| `url`        | string | (required) | Correlator API base URL      |
| `api_key`    | string | null       | API key for X-API-Key header |
| `timeout`    | int    | 30         | Request timeout in seconds   |
| `verify_ssl` | bool   | true       | Verify SSL certificates      |

---

## Environment Variable Interpolation

Use `${VAR_NAME}` syntax in `openlineage.yml` for sensitive values:

```yaml
transport:
  type: correlator
  url: ${CORRELATOR_URL}
  api_key: ${CORRELATOR_API_KEY}
  timeout: 30
  verify_ssl: true
```

---

## Configuration Examples

### Local Development (Airflow)

```yaml
# openlineage.yml (in $AIRFLOW_HOME)
transport:
  type: correlator
  url: http://localhost:8080
  verify_ssl: false
```

### Production (Airflow)

```yaml
# openlineage.yml (in $AIRFLOW_HOME)
transport:
  type: correlator
  url: https://correlator.example.com
  api_key: ${CORRELATOR_API_KEY}
  timeout: 60
  verify_ssl: true
```

### Airflow Environment Variable Only (No Config File)

```bash
# Set transport configuration as JSON
export AIRFLOW__OPENLINEAGE__TRANSPORT='{
  "type": "correlator",
  "url": "https://correlator.example.com",
  "api_key": "your-api-key",
  "timeout": 30
}'
```

### Standalone OpenLineage Client (Non-Airflow)

```yaml
# openlineage.yml
transport:
  type: airflow_correlator.transport.CorrelatorTransport
  url: http://localhost:8080
```

Or via environment variable:

```bash
export OPENLINEAGE_CONFIG='{"transport":{"type":"airflow_correlator.transport.CorrelatorTransport","url":"http://localhost:8080"}}'
```

---

## How It Works

The configuration is loaded by OpenLineage's transport discovery mechanism:

1. OpenLineage provider reads `openlineage.yml` or `AIRFLOW__OPENLINEAGE__TRANSPORT`
2. Finds `type: correlator` and looks up the registered transport
3. Calls `CorrelatorConfig.from_dict()` with the configuration parameters
4. Creates `CorrelatorTransport` instance with the config

```
openlineage.yml → OpenLineage Config Loader → CorrelatorConfig → CorrelatorTransport
```

---

## File Locations

OpenLineage searches for `openlineage.yml` in these locations (in order):

1. Path specified by `OPENLINEAGE_CONFIG` environment variable
2. Current working directory
3. `$AIRFLOW_HOME` directory
4. User's home directory (`~`)

---

## Verifying Configuration

### Check Transport Registration (Airflow)

```bash
# Verify the correlator transport is registered
python -c "from importlib.metadata import entry_points; eps = entry_points(group='openlineage.transport'); print([ep.name for ep in eps if ep.name == 'correlator'])"
# Expected: ['correlator']
```

### Check Transport Registration (Standalone)

```python
from airflow_correlator.transport import CorrelatorTransport, CorrelatorConfig

config = CorrelatorConfig(url="http://localhost:8080")
transport = CorrelatorTransport(config)
print(f"Transport created: {transport.kind}")
# Expected: correlator
```

### Test Connection

```bash
# Send a test event to verify connectivity
curl -X POST http://localhost:8080/api/v1/lineage/events \
  -H "Content-Type: application/json" \
  -d '[{
    "eventTime": "2024-01-01T12:00:00Z",
    "eventType": "START",
    "producer": "https://github.com/correlator-io/correlator-airflow/test",
    "schemaURL": "https://openlineage.io/spec/1-0-0/OpenLineage.json",
    "run": {"runId": "test-run-123"},
    "job": {"namespace": "airflow", "name": "test.task"}
  }]'
```

---

## Troubleshooting

### Events Not Being Sent

1. **Check OpenLineage is enabled:**
   ```bash
   # Ensure provider is installed
   pip show apache-airflow-providers-openlineage
   ```

2. **Check transport configuration:**
   ```bash
   # Verify environment variable
   echo $AIRFLOW__OPENLINEAGE__TRANSPORT
   
   # Or check openlineage.yml exists
   cat $AIRFLOW_HOME/openlineage.yml
   ```

3. **Check Correlator is reachable:**
   ```bash
   curl http://localhost:8080/ping
   # Expected: pong
   ```

### SSL Certificate Errors

For self-signed certificates in development:

```yaml
transport:
  type: correlator
  url: https://localhost:8080
  verify_ssl: false  # Only for development!
```

### Connection Timeouts

Increase timeout for slow networks:

```yaml
transport:
  type: correlator
  url: http://correlator:8080
  timeout: 60  # 60 seconds
```

---

## Security Considerations

1. **Never commit API keys** - Use environment variables with `${VAR_NAME}` syntax
2. **Use HTTPS in production** - Always use TLS for production deployments
3. **Don't disable SSL verification in production** - Only use `verify_ssl: false` for local development

