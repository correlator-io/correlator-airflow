# Configuration

> **Note:** This is a placeholder document. Full configuration documentation will be added after Task 1.7 (Integration
> test) is complete.

## Overview

`correlator-airflow` can be configured through:

1. **Environment variables** (highest priority)
2. **Configuration file** (`.airflow-correlator.yml`)
3. **Airflow connections** (for credentials)

## Environment Variables

| Variable              | Description                           | Default |
|-----------------------|---------------------------------------|---------|
| `CORRELATOR_ENDPOINT` | Correlator API endpoint               | -       |
| `CORRELATOR_API_KEY`  | API key for authentication            | -       |
| `OPENLINEAGE_URL`     | Fallback endpoint (dbt-ol compatible) | -       |
| `OPENLINEAGE_API_KEY` | Fallback API key (dbt-ol compatible)  | -       |

### Priority Order

```
CLI args > CORRELATOR_* env vars > OPENLINEAGE_* env vars > config file > defaults
```

## Configuration File

Create `.airflow-correlator.yml` in your project directory:

```yaml
correlator:
  endpoint: http://localhost:8080/api/v1/lineage/events
  namespace: airflow
  api_key: ${CORRELATOR_API_KEY}  # Environment variable interpolation
```

### File Locations

The plugin searches for configuration files in this order:

1. Explicit path via `--config` option
2. `.airflow-correlator.yml` in current directory
3. `.airflow-correlator.yaml` in current directory
4. `.airflow-correlator.yml` in home directory
5. `.airflow-correlator.yaml` in home directory

## Airflow Configuration

### Enable the Listener

Add to your `airflow.cfg`:

```ini
[core]
# Enable OpenLineage listener
executor_callback_class = airflow_correlator.listener.CorrelatorLineageListener
```

Or via environment variable:

```bash
export AIRFLOW__CORE__EXECUTOR_CALLBACK_CLASS=airflow_correlator.listener.CorrelatorLineageListener
```

### Connection Configuration

Create an Airflow connection for Correlator credentials:

```bash
airflow connections add correlator \
  --conn-type http \
  --conn-host localhost \
  --conn-port 8080 \
  --conn-schema https \
  --conn-password your-api-key
```

## Configuration Options

| Option                 | Type   | Description                                |
|------------------------|--------|--------------------------------------------|
| `correlator.endpoint`  | string | Correlator API endpoint URL                |
| `correlator.namespace` | string | OpenLineage namespace (default: `airflow`) |
| `correlator.api_key`   | string | API key for authentication                 |

## Examples

### Minimal Configuration

```yaml
# .airflow-correlator.yml
correlator:
  endpoint: http://localhost:8080/api/v1/lineage/events
```

### Production Configuration

```yaml
# .airflow-correlator.yml
correlator:
  endpoint: https://correlator.example.com/api/v1/lineage/events
  namespace: production
  api_key: ${CORRELATOR_API_KEY}
```

### Environment Variables Only

```bash
export CORRELATOR_ENDPOINT=http://localhost:8080/api/v1/lineage/events
export CORRELATOR_API_KEY=your-api-key
```

---

*Full documentation will be added in Task 1.3 (Core listener implementation).*
