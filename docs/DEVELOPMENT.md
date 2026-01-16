# airflow-correlator Development Guide

Welcome to airflow-correlator! This guide gets you from clone to coding in minutes with our streamlined 8-command
development system.

---

## Quick Start

**New to this project?** One command gets you started:

```bash
git clone https://github.com/correlator-io/correlator-airflow.git
cd correlator-airflow
make start
```

That's it! The command will:

- ✅ Install UV package manager (if needed)
- ✅ Create virtual environment
- ✅ Install all dependencies (dev + runtime)
- ✅ Install pre-commit hooks
- ✅ Ready to code!

---

## The 8 Essential Commands

Our development workflow is built around **8 intent-based commands** that handle everything:

### 🚀 Getting Started

- **`make start`** - Begin working (setup environment + install dependencies)
- **`make install`** - Install/update dependencies (after changing pyproject.toml)
- **`make run`** - Execute CLI (default: shows help, or run test, run linter)

### 🛠️ Daily Development

- **`make check`** - Verify code quality (format + lint + typecheck + test + security)
- **`make fix`** - Repair issues (format + fix lints + clean artifacts)

### 🏗️ Build & Deploy

- **`make build`** - Create artifacts (clean + build wheel + sdist)
- **`make deploy`** - Verify package is ready for PyPI (local check before manual publish)

### 🔧 Maintenance

- **`make reset`** - Start fresh (clean everything + reset environment)

---

## Development Workflow

### First Time Setup

```bash
# Clone and start (zero configuration)
git clone https://github.com/correlator-io/correlator-airflow.git
cd correlator-airflow
make start                    # Complete environment setup

# You're ready to code!
```

### Daily Development

```bash
# Activate virtual environment
source .venv/bin/activate     # Linux/macOS
# or
.venv\Scripts\activate        # Windows

# Your daily commands:
make run                      # Run CLI (shows help)
make run test                 # Run all tests
make run coverage             # Run tests with coverage
make check                    # Code quality before commit

# Update dependencies
vim pyproject.toml            # Add new dependency
make install                  # Install/update dependencies

# Test CLI directly
airflow-correlator --version  # Test installed CLI

# Deactivate when done
deactivate
```

---

## Command Reference

### 🚀 `make start` - Smart Environment Setup

**Behavior**:

- Checks Python 3.9+ installation
- Installs UV package manager (if needed)
- Creates virtual environment (`.venv/`) if it doesn't exist
- Installs all dependencies (runtime + dev)
- Installs pre-commit hooks automatically
- Ready to code!

**Note:** Safe to run multiple times - skips venv creation if already exists.

### 📦 `make install` - Install/Update Dependencies

**Use when:**

- You added a new dependency to `pyproject.toml`
- You want to update existing dependencies
- You need to install the package in editable mode for testing

**Behavior**:

- Checks that virtual environment exists (fails with helpful message if not)
- Installs/updates dependencies from `pyproject.toml`
- Installs package in editable mode (`-e` flag)
- Changes to source code are immediately available

**Example workflow**:

```bash
# Add new dependency
vim pyproject.toml           # Add: pyyaml>=6.0

# Install it
make install                 # Installs pyyaml

# Use it immediately
python -c "import yaml; print(yaml.__version__)"
```

### 🏃 `make run` - Execute CLI (Default) or Operations

**Default behavior** (consistent with Correlator):

```bash
make run                      # Run CLI (shows help - main tool)
```

**Testing**:

```bash
make run test                 # All tests (unit + integration)
make run test unit            # Unit tests only (fast)
make run test integration     # Integration tests only
make run coverage             # Tests with coverage report
```

**Code Quality**:

```bash
make run linter               # Run ruff linter
make run typecheck            # Run mypy type checker
make run security             # Run bandit security scanner
```

### 🔍 `make check` - Code Quality

```bash
make check                    # Full quality suite:
                              # 1. Black formatter check
                              # 2. Ruff linter
                              # 3. Mypy type checker
                              # 4. Pytest (all tests)
                              # 5. Bandit security scan
```

### 🔧 `make fix` - Auto-Repair

```bash
make fix                      # Auto-fix what we can:
                              # 1. Format code with black
                              # 2. Fix lints with ruff --fix
                              # 3. Sort imports with ruff
```

### 🏗️ `make build` - Create Artifacts

```bash
make build                    # Clean + build package (wheel + sdist)
```

**Behavior:**

- Cleans old distribution files from `dist/`
- Builds wheel (`.whl`) and source distribution (`.tar.gz`)
- Shows file sizes for verification
- Fails fast with helpful error messages

### 🚀 `make deploy` - Local Release Verification

**Purpose:** Local developer convenience command for manual releases.

**Note:** GitHub workflows handle automated releases. This command is for manual verification before publishing.

```bash
make deploy                   # Local release preparation:
                              # 1. Run quality checks (make check)
                              # 2. Build package (make build)
                              # 3. Show manual publish command
```

**Use when:**

- Testing release process locally
- Manual emergency releases
- Verifying package before publishing

**For normal releases:** Let GitHub workflows handle it automatically via PR merge.

### 💥 `make reset` - Nuclear Reset

```bash
make reset                    # When things go wrong:
                              # - Remove build artifacts
                              # - Remove cache directories
                              # - Remove virtual environment
                              # - Fresh state
```

---

## Development Environment Details

### Prerequisites

**Required**:

- **Python 3.9+** - Minimum supported version
- **Git** - Version control
- **UV** - Package manager (installed automatically by `make start`)

**Optional**:

- **make** - For convenient commands (or run commands directly)
- **Docker** - For integration testing with [Correlator](https://github.com/correlator-io/correlator)
- **Airflow** - For end-to-end testing

### Tech Stack

**Runtime**:

- **Python 3.9+** - Language
- **Click** - CLI framework
- **Pydantic** - Configuration management
- **openlineage-python** - OpenLineage client

**Development**:

- **UV** - Fast package manager
- **pytest** - Testing framework
- **black** - Code formatter
- **ruff** - Fast linter
- **mypy** - Type checker
- **pre-commit** - Git hooks

---

## Testing

### Test Directory Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests (fast, isolated, mocked)
├── integration/         # Integration tests (requires Correlator)
└── e2e/                 # E2E tests (manual validation scripts)
```

### Test Categories

- **Unit Tests** (`tests/unit/`): Fast, isolated, mocked dependencies
- **Integration Tests** (`tests/integration/`): Requires running Correlator backend
- **E2E Tests** (`tests/e2e/`): Manual validation scripts for pre-release testing

### Running Tests

```bash
# All tests (unit only by default - integration tests are skipped)
make run test

# Unit tests only
make run test unit

# Integration tests only (requires Correlator running)
make run test integration

# E2E tests (manual validation scripts)
make run test e2e

# Coverage reporting
make run coverage             # With HTML report in htmlcov/

# Specific test file (direct pytest)
pytest tests/unit/test_transport.py -v

# Specific test function (direct pytest)
pytest tests/unit/test_transport.py::TestCorrelatorTransportEmit -v

# With coverage for specific module (direct pytest)
pytest tests/unit/test_transport.py --cov=airflow_correlator.transport --cov-report=term-missing
```

> **Note:** Integration tests are skipped by default via `-m "not integration"` in `pyproject.toml`.
> This ensures `make check` and CI/CD pipelines run only unit tests.

### Test Conventions

**Unit Tests** (fast, isolated):

```python
import pytest


@pytest.mark.unit
def test_create_run_event():
    """Test creation of OpenLineage RunEvent."""
    # Use mocked data
    event = create_run_event(
        event_type="START",
        run_id="test-run-id",
        job_name="dag.task",
        job_namespace="airflow",
    )
    assert event["eventType"] == "START"
```

**Integration Tests** (requires Correlator):

```python
import pytest


@pytest.mark.integration
def test_emit_event_to_correlator():
    """Test emitting OpenLineage event to Correlator."""
    # Requires Correlator running
    event = create_run_event(...)
    response = emit_events([event], correlator_url)
    assert response.status_code == 200
```

**Test Fixtures** (reusable test data):

```python
@pytest.fixture
def sample_task_instance():
    """Create a mock Airflow TaskInstance."""
    mock_ti = Mock()
    mock_ti.task_id = "test_task"
    mock_ti.dag_id = "test_dag"
    mock_ti.run_id = "manual__2024-01-01T00:00:00+00:00"
    return mock_ti


def test_with_fixture(sample_task_instance):
    result = on_task_instance_running(sample_task_instance)
    assert result is not None
```

### Integration Tests

Integration tests validate the full roundtrip from transport to Correlator database. They are **intentionally excluded**
from CI/CD pipelines and require manual execution.

#### Why Integration Tests Are Not in CI/CD

| Reason                  | Explanation                                                       |
|-------------------------|-------------------------------------------------------------------|
| **External dependency** | Tests require a running Correlator backend (Docker containers)    |
| **Not mocked**          | Tests hit a real Correlator instance and real PostgreSQL database |
| **Environment setup**   | Requires `psql` client and network access to Correlator           |
| **Execution time**      | Slower than unit tests due to network I/O and database queries    |

#### When to Run Integration Tests

Run integration tests **locally** in these scenarios:

- **Before a release** - Validate the transport works end-to-end before publishing to PyPI
- **After a major refactor** - Ensure refactored code still integrates correctly with Correlator
- **After fixing a transport/emitter bug** - Verify the fix works against a real backend
- **When adding new event types** - Confirm new events are accepted and stored correctly
- **When Correlator API changes** - Validate compatibility with updated backend

#### Running Integration Tests

**Prerequisites:**

1. Correlator backend running (`make start` in correlator repo)
2. PostgreSQL accessible at `localhost:5432`
3. `psql` command available in PATH

**Execution:**

```bash
# Start Correlator (in correlator repo)
cd ../correlator && make start

# Verify Correlator is running
curl http://localhost:8080/ping  # Should return: pong

# Run integration tests
make run test integration
```

**Expected output (Correlator running):**

```
tests/integration/test_correlator_integration.py::TestCorrelatorIntegration::test_transport_emits_event_to_correlator PASSED
tests/integration/test_correlator_integration.py::TestCorrelatorIntegration::test_complete_event_lifecycle PASSED
tests/integration/test_correlator_integration.py::TestCorrelatorIntegration::test_api_returns_success_response PASSED
```

**Expected output (Correlator NOT running):**

```
SKIPPED [1] tests/integration/test_correlator_integration.py: ⚠️ Correlator not reachable at http://localhost:8080
```

#### Configuration

Integration tests can be configured via environment variables:

| Variable            | Default                                                                    | Description                                   |
|---------------------|----------------------------------------------------------------------------|-----------------------------------------------|
| `CORRELATOR_URL`    | `http://localhost:8080`                                                    | Correlator API base URL                       |
| `CORRELATOR_DB_URL` | `postgres://correlator:password@localhost:5432/correlator?sslmode=disable` | PostgreSQL connection string for verification |

#### Integration Test Location

```
tests/integration/
├── __init__.py
└── test_correlator_integration.py    # Transport → Correlator → DB roundtrip tests
```

---

## Code Quality

### Pre-Commit Hooks

Pre-commit hooks run automatically before each commit:

```bash
# Install hooks (done automatically by make start)
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

### Manual Quality Checks

```bash
# Full quality suite (before pushing)
make check                    # format + lint + typecheck + test + security

# Individual tools
make run linter               # Run ruff linter
make run typecheck            # Run mypy type checker
make run security             # Run bandit security scanner

# Fix common issues
make fix                      # Auto-fix: format + fix lints + sort imports
```

### Type Checking

```bash
# Check all files (via Makefile)
make run typecheck

# Check specific file (direct mypy)
mypy src/airflow_correlator/transport.py

# Ignore specific error (direct mypy)
mypy --disable-error-code=import-untyped src/airflow_correlator/

# Show error codes (direct mypy - for configuring mypy.ini)
mypy --show-error-codes src/
```

---

## Building and Packaging

### Local Development Build

```bash
# Build package distributions (wheel + sdist)
make build

# Install in editable mode for local testing
make install                  # Installs in editable mode with all dev dependencies

# Test CLI installation
airflow-correlator --version
airflow-correlator --help

# Uninstall
pip uninstall correlator-airflow -y
```

### Testing Package Installation

```bash
# Create fresh test environment
python -m venv test-env
source test-env/bin/activate

# Install from local build
pip install dist/correlator_airflow-*.whl

# Test CLI
airflow-correlator --version

# Cleanup
deactivate
rm -rf test-env
```

---

## Integration with Correlator

### Local Correlator Setup

```bash
# Clone Correlator (separate repo)
git clone https://github.com/correlator-io/correlator.git
cd correlator
make run                    # Starts Correlator on localhost:8080

# Test connection
curl http://localhost:8080/health
```

### End-to-End Testing

```bash
# Terminal 1: Start Correlator
cd ../correlator
make run

# Terminal 2: Run Airflow with correlator-airflow
cd ../correlator-airflow
source .venv/bin/activate

# Set environment variables
export OPENLINEAGE_URL=http://localhost:8080/api/v1/lineage
export OPENLINEAGE_NAMESPACE=test

# Run Airflow tasks and verify events in Correlator
curl http://localhost:8080/api/v1/correlation/view | jq
```

---

## Troubleshooting

### Common Issues

**🔧 UV Installation Problems**

```bash
# Manual UV installation
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv

# Verify installation
uv --version
```

**🐛 Virtual Environment Issues**

```bash
# Remove and recreate
make reset
make start

# Or manually
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**⚡ Test Failures**

```bash
# Run with verbose output
pytest -vv

# Run specific test
pytest tests/unit/test_transport.py::TestCorrelatorTransportEmit::test_emit_calls_emit_events_with_correct_params -vv

# Show print statements
pytest -s

# Show locals on failure
pytest --showlocals
```

**🔍 Import Errors**

```bash
# Ensure package is installed in editable mode
make install

# Or reinstall from scratch
make reset
make start

# Verify installation
pip show correlator-airflow
```

### Diagnostic Tools

**Environment Check**:

```bash
# Python version
python --version

# UV version
uv --version

# Installed packages
pip list

# Package location
pip show correlator-airflow

# Virtual environment
which python
```

**Test Debugging**:

```bash
# Run with debugger
pytest --pdb

# Run until first failure
pytest -x

# Re-run failed tests
pytest --lf

# Show slowest tests
pytest --durations=10
```

---

## Getting Help

### Command Help

```bash
make help                     # Show all make commands
airflow-correlator --help     # CLI help
pytest --help                 # pytest options
```

### Further Reading

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical design
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Release process

---

## Pro Tips 💡

### Efficient Workflows

**Fast Feedback Loop**:

```bash
# Quick CLI testing
make run                      # Run CLI (shows help and options)

# Quick test iteration
make run test                 # Run all tests

# Watch mode (requires pytest-watch - install separately)
pip install pytest-watch
ptw -- -v                     # Re-runs tests on file change
```

**Pre-Commit Workflow**:

```bash
make fix                      # Auto-fix formatting and lints
make check                    # Full quality check
git add .
git commit -s -m "minor: add feature"
```

**Testing Specific Module**:

```bash
# Test + coverage for single module
pytest tests/unit/test_transport.py \
  --cov=airflow_correlator.transport \
  --cov-report=term-missing \
  --cov-report=html
```

### IDE Integration

**VS Code**:

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "-v"
  ],
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

**PyCharm**:

- Python Interpreter: Settings → Project → Python Interpreter → Add → Virtualenv Environment → Existing →
  `.venv/bin/python`
- Test Runner: Settings → Tools → Python Integrated Tools → Testing → Default test runner: pytest
- Type Checker: Settings → Editor → Inspections → Python → Type checker: Mypy

### Performance Optimization

**Fast Test Execution**:

```bash
# Unit tests only (fastest feedback)
make run test unit            # Seconds, not minutes

# All tests
make run test                 # Unit + integration

# Parallel execution (requires pytest-xdist - install separately)
pip install pytest-xdist
pytest -n auto                # Use all CPU cores
```

**Faster Dependency Installation**:

```bash
# UV is already fast, but you can cache aggressively
uv pip install --cache-dir ~/.cache/uv -e ".[dev]"
```

### Git Configuration

#### **First-Time Setup (Required)**

```bash
# Set your name and email (required for signed commits)
git config --global user.name "Your Full Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --global --list | grep user
```

#### **Signed Commits**

All commits must be signed-off:

```bash
# Every commit needs -s flag
git commit -s -m "minor: add new feature"

# Configure alias for convenience
git config --global alias.cs "commit -s"
git cs -m "patch: fix transport bug"
```

#### **SSH Key Setup (Recommended)**

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Display public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys

# Test connection
ssh -T git@github.com

# Update remote to use SSH
git remote set-url origin git@github.com:correlator-io/correlator-airflow.git
```

---

## Development Best Practices

### Code Style

- **Follow PEP 8** - Enforced by black and ruff
- **Type hints everywhere** - Public APIs must be fully typed
- **Docstrings** - Use Google style for all public functions
- **Keep functions small** - Single responsibility principle
- **Test-driven development** - Write tests first when possible

### Testing Best Practices

- **Fast unit tests** - Mock external dependencies
- **Integration tests for critical paths** - Real Airflow tasks
- **90%+ coverage** - Required before merging
- **Clear test names** - `test_on_task_instance_running_emits_start_event`
- **Arrange-Act-Assert** - Structure all tests this way

### Documentation

- **Update README** - For user-facing changes
- **Update ARCHITECTURE** - For design decisions
- **Inline comments** - For complex logic only
- **Docstrings** - For all public APIs
- **Type hints as documentation** - Self-documenting code

---

*Happy coding! 🚀*
