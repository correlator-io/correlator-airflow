# correlator-airflow

**Accelerate Airflow incident resolution with automated correlation**

[![PyPI version](https://img.shields.io/pypi/v/correlator-airflow.svg)](https://pypi.org/project/correlator-airflow/)
[![codecov](https://codecov.io/gh/correlator-io/correlator-airflow/graph/badge.svg?token=aJSV0DqMgZ)](https://codecov.io/gh/correlator-io/correlator-airflow)
[![Python Version](https://img.shields.io/pypi/pyversions/correlator-airflow.svg)](https://pypi.org/project/correlator-airflow/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

## What It Does

Automatically connects Airflow task executions to incident correlation:

- Emits OpenLineage events for task lifecycle (START/COMPLETE/FAIL)
- Links task failures to upstream data quality issues
- Provides direct navigation from incident to root cause
- Reuses all 50+ built-in OpenLineage extractors

---

## Quick Start

> **IMPORTANT:** Requires **Airflow 2.11.0+** and `apache-airflow-providers-openlineage>=2.0.0`

### 1. Install

```bash
pip install correlator-airflow apache-airflow-providers-openlineage
```

### 2. Configure OpenLineage Transport

**Option A: openlineage.yml (Recommended)**

Create `openlineage.yml` in your Airflow home directory:

```yaml
transport:
  type: correlator
  url: http://localhost:8080
  api_key: ${CORRELATOR_API_KEY}
```

**Option B: Environment Variable**

```bash
export AIRFLOW__OPENLINEAGE__TRANSPORT='{"type": "correlator", "url": "http://localhost:8080"}'
```

### 3. Run Your DAGs

That's it. Your Airflow task executions are now being correlated.

---

## How It Works

`correlator-airflow` provides a **custom OpenLineage transport** that integrates with Airflow's built-in OpenLineage
provider:

```
Airflow Task → [OL Provider Listener] → [OL Extractors] → [CorrelatorTransport] → Correlator
              └────── Built into Airflow ──────┘         └─── This plugin ───┘
```

See [Architecture](docs/ARCHITECTURE.md) for technical details.

---

## Why It Matters

**The Problem:** When data pipelines fail, teams spend significant time manually hunting through Airflow logs, lineage
graphs, and job histories to find the root cause.

**What You Get:** Automated correlation between Airflow task executions and data quality test results, putting you in
control of incidents instead of reacting to them.

**Key Benefits:**

- **Faster incident resolution**: Automated correlation reduces investigation time
- **Eliminate tool switching**: One correlation view instead of navigating multiple dashboards
- **Instant root cause**: Direct path from task failure to problematic upstream job
- **Zero-friction setup**: Simple configuration, no code changes required

**Built on Standards:** Uses OpenLineage, the industry standard for data lineage. No vendor lock-in, no proprietary
formats.

---

## Versioning

This package follows [Semantic Versioning](https://semver.org/) with the following guidelines:

- **0.x.y versions** (e.g., 0.1.0, 0.2.0) indicate **initial development phase**:
  - The API is not yet stable and may change between minor versions
  - Features may be added, modified, or removed without major version changes
  - Not recommended for production-critical systems without pinned versions

- **1.0.0 and above** will indicate a **stable API** with semantic versioning guarantees:
  - MAJOR version for incompatible API changes
  - MINOR version for backwards-compatible functionality additions
  - PATCH version for backwards-compatible bug fixes

The current version is in early development stage, so expect possible API changes until the 1.0.0 release.

---

## Documentation

**For detailed usage, configuration, and development:**

- **Configuration**: [docs/CONFIGURATION.md](docs/CONFIGURATION.md) - All CLI options, config file, environment variables
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Internal design, data flow, OpenLineage events
- **Development**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development setup, testing, local environment
- **Contributing**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) - Contribution guidelines, branch naming, commit format
- **Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Release process, versioning, PyPI publishing

---

## Requirements

- **Python 3.9+**
- **Airflow 2.11.0+ ONLY** (older versions NOT supported)
- `apache-airflow-providers-openlineage>=2.0.0`
- [Correlator](https://github.com/correlator-io/correlator)

---

## Links

- **Correlator**: https://github.com/correlator-io/correlator
- **dbt Plugin**: https://github.com/correlator-io/correlator-dbt
- **OpenLineage**: https://openlineage.io/
- **Issues**: https://github.com/correlator-io/correlator-airflow/issues
- **Discussions**: https://github.com/correlator-io/correlator/discussions

---

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.
