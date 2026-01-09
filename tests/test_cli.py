"""Tests for CLI module.

This module tests the airflow-correlator CLI commands, including:
- Command structure and options
- Configuration file loading
- Environment variable fallbacks
- Credential resolution

Uses Click's CliRunner for CLI testing.
"""

from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from airflow_correlator import __version__
from airflow_correlator.cli import cli, load_config_callback, resolve_credentials

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def runner() -> CliRunner:
    """Create Click test runner."""
    return CliRunner()


# =============================================================================
# A. Command Structure Tests
# =============================================================================


class TestCommandStructure:
    """Tests for CLI command structure and options."""

    def test_cli_version_option(self, runner: CliRunner) -> None:
        """Test that --version option shows correct version."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output
        assert "airflow-correlator" in result.output

    def test_cli_help_option(self, runner: CliRunner) -> None:
        """Test that --help option shows help text."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "airflow-correlator" in result.output


# =============================================================================
# B. Load Config Callback Tests
# =============================================================================


class TestLoadConfigCallback:
    """Tests for load_config_callback function."""

    def test_load_config_callback_with_valid_file(
        self, tmp_path: Path, runner: CliRunner
    ) -> None:
        """Test that load_config_callback loads valid config file."""
        config_file = tmp_path / ".airflow-correlator.yml"
        config_file.write_text(
            """\
correlator:
  endpoint: http://config-endpoint:8080/api/v1/lineage/events
  namespace: from-config
"""
        )

        # Create a test context
        @click.command()
        @click.option(
            "--config",
            callback=load_config_callback,
            expose_value=True,
            is_eager=True,
        )
        @click.pass_context
        def test_cmd(ctx: click.Context, config: str) -> None:
            # Check that default_map was set
            click.echo(f"default_map: {ctx.default_map}")

        result = runner.invoke(test_cmd, ["--config", str(config_file)])

        assert result.exit_code == 0
        assert "correlator_endpoint" in result.output
        assert "http://config-endpoint:8080/api/v1/lineage/events" in result.output

    def test_load_config_callback_missing_file_error(
        self, tmp_path: Path, runner: CliRunner
    ) -> None:
        """Test that explicit missing config file raises error."""
        non_existent = tmp_path / "does-not-exist.yml"

        @click.command()
        @click.option(
            "--config",
            callback=load_config_callback,
            expose_value=True,
            is_eager=True,
        )
        def test_cmd(config: str) -> None:
            pass

        result = runner.invoke(test_cmd, ["--config", str(non_existent)])

        assert result.exit_code != 0
        assert (
            "not found" in result.output.lower() or "invalid" in result.output.lower()
        )

    def test_load_config_callback_invalid_yaml_error(
        self, tmp_path: Path, runner: CliRunner
    ) -> None:
        """Test that invalid YAML config file raises error."""
        config_file = tmp_path / "invalid.yml"
        config_file.write_text("invalid: yaml: [unclosed")

        @click.command()
        @click.option(
            "--config",
            callback=load_config_callback,
            expose_value=True,
            is_eager=True,
        )
        def test_cmd(config: str) -> None:
            pass

        result = runner.invoke(test_cmd, ["--config", str(config_file)])

        assert result.exit_code != 0
        assert "invalid" in result.output.lower() or "yaml" in result.output.lower()

    def test_load_config_callback_auto_discovery(
        self, tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that config file is auto-discovered in cwd without --config."""
        config_file = tmp_path / ".airflow-correlator.yml"
        config_file.write_text(
            """\
correlator:
  endpoint: http://auto-discovered:8080/api/v1/lineage/events
"""
        )

        monkeypatch.chdir(tmp_path)

        @click.command()
        @click.option(
            "--config",
            callback=load_config_callback,
            expose_value=True,
            is_eager=True,
        )
        @click.pass_context
        def test_cmd(ctx: click.Context, config: str) -> None:
            click.echo(f"default_map: {ctx.default_map}")

        result = runner.invoke(test_cmd, [])

        assert result.exit_code == 0
        assert "http://auto-discovered:8080/api/v1/lineage/events" in result.output


# =============================================================================
# C. Resolve Credentials Tests
# =============================================================================


class TestResolveCredentials:
    """Tests for resolve_credentials function."""

    def test_resolve_credentials_cli_args_used(self) -> None:
        """Test that CLI args are used when provided."""
        endpoint, api_key = resolve_credentials(
            endpoint="http://cli-endpoint:8080",
            api_key="cli-api-key",
        )

        assert endpoint == "http://cli-endpoint:8080"
        assert api_key == "cli-api-key"

    def test_resolve_credentials_correlator_env_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CORRELATOR_* env vars are used as fallback."""
        monkeypatch.setenv("CORRELATOR_ENDPOINT", "http://correlator-env:8080")
        monkeypatch.setenv("CORRELATOR_API_KEY", "correlator-env-key")

        endpoint, api_key = resolve_credentials(
            endpoint=None,
            api_key=None,
        )

        assert endpoint == "http://correlator-env:8080"
        assert api_key == "correlator-env-key"

    def test_resolve_credentials_openlineage_env_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that OPENLINEAGE_* env vars are used as fallback."""
        monkeypatch.setenv("OPENLINEAGE_URL", "http://openlineage-env:5000")
        monkeypatch.setenv("OPENLINEAGE_API_KEY", "openlineage-env-key")

        endpoint, api_key = resolve_credentials(
            endpoint=None,
            api_key=None,
        )

        assert endpoint == "http://openlineage-env:5000"
        assert api_key == "openlineage-env-key"

    def test_resolve_credentials_correlator_takes_priority_over_openlineage(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CORRELATOR_* env vars take priority over OPENLINEAGE_*."""
        monkeypatch.setenv("CORRELATOR_ENDPOINT", "http://correlator:8080")
        monkeypatch.setenv("CORRELATOR_API_KEY", "correlator-key")
        monkeypatch.setenv("OPENLINEAGE_URL", "http://openlineage:5000")
        monkeypatch.setenv("OPENLINEAGE_API_KEY", "openlineage-key")

        endpoint, api_key = resolve_credentials(
            endpoint=None,
            api_key=None,
        )

        assert endpoint == "http://correlator:8080"
        assert api_key == "correlator-key"

    def test_resolve_credentials_missing_endpoint_raises_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that missing endpoint raises UsageError."""
        # Clear any env vars
        monkeypatch.delenv("CORRELATOR_ENDPOINT", raising=False)
        monkeypatch.delenv("OPENLINEAGE_URL", raising=False)

        with pytest.raises(click.UsageError) as exc_info:
            resolve_credentials(endpoint=None, api_key=None)

        error_message = str(exc_info.value)
        assert "correlator-endpoint" in error_message.lower()

    def test_resolve_credentials_api_key_optional(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that API key is optional (can be None)."""
        monkeypatch.setenv("CORRELATOR_ENDPOINT", "http://localhost:8080")
        monkeypatch.delenv("CORRELATOR_API_KEY", raising=False)
        monkeypatch.delenv("OPENLINEAGE_API_KEY", raising=False)

        endpoint, api_key = resolve_credentials(
            endpoint=None,
            api_key=None,
        )

        assert endpoint == "http://localhost:8080"
        assert api_key is None


# =============================================================================
# D. dbt-ol Environment Variable Compatibility Tests
# =============================================================================


class TestDbtOlEnvVarCompatibility:
    """Tests for dbt-ol compatible environment variable fallbacks.

    airflow-correlator supports dbt-ol environment variables as fallbacks
    to simplify migration from dbt-ol.

    Priority order:
    1. CLI arguments (highest)
    2. CORRELATOR_* env vars
    3. OPENLINEAGE_* env vars (lowest)
    """

    def test_openlineage_url_fallback_when_no_endpoint_provided(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that OPENLINEAGE_URL env var is used when no endpoint provided."""
        monkeypatch.setenv(
            "OPENLINEAGE_URL", "http://openlineage-backend:5000/api/v1/lineage"
        )

        endpoint, _ = resolve_credentials(endpoint=None, api_key=None)

        assert endpoint == "http://openlineage-backend:5000/api/v1/lineage"

    def test_correlator_endpoint_takes_priority_over_openlineage_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CORRELATOR_ENDPOINT takes priority over OPENLINEAGE_URL."""
        monkeypatch.setenv(
            "CORRELATOR_ENDPOINT", "http://correlator:8080/api/v1/lineage/events"
        )
        monkeypatch.setenv("OPENLINEAGE_URL", "http://openlineage:5000/api/v1/lineage")

        endpoint, _ = resolve_credentials(endpoint=None, api_key=None)

        assert endpoint == "http://correlator:8080/api/v1/lineage/events"

    def test_openlineage_api_key_fallback_when_no_api_key_provided(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that OPENLINEAGE_API_KEY env var is used when no API key provided."""
        monkeypatch.setenv(
            "CORRELATOR_ENDPOINT", "http://localhost:8080/api/v1/lineage/events"
        )
        monkeypatch.setenv("OPENLINEAGE_API_KEY", "openlineage-api-key-123")

        _, api_key = resolve_credentials(endpoint=None, api_key=None)

        assert api_key == "openlineage-api-key-123"

    def test_correlator_api_key_takes_priority_over_openlineage_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CORRELATOR_API_KEY takes priority over OPENLINEAGE_API_KEY."""
        monkeypatch.setenv(
            "CORRELATOR_ENDPOINT", "http://localhost:8080/api/v1/lineage/events"
        )
        monkeypatch.setenv("CORRELATOR_API_KEY", "correlator-api-key-456")
        monkeypatch.setenv("OPENLINEAGE_API_KEY", "openlineage-api-key-123")

        _, api_key = resolve_credentials(endpoint=None, api_key=None)

        assert api_key == "correlator-api-key-456"

    def test_missing_endpoint_shows_helpful_error_message(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that missing endpoint shows error mentioning all options."""
        monkeypatch.delenv("CORRELATOR_ENDPOINT", raising=False)
        monkeypatch.delenv("OPENLINEAGE_URL", raising=False)

        with pytest.raises(click.UsageError) as exc_info:
            resolve_credentials(endpoint=None, api_key=None)

        error_message = str(exc_info.value)
        # Error should mention all ways to provide endpoint
        assert (
            "CORRELATOR_ENDPOINT" in error_message
            or "correlator-endpoint" in error_message
        )
        assert "OPENLINEAGE_URL" in error_message


# =============================================================================
# E. Config File Integration Tests
# =============================================================================


class TestConfigFileIntegration:
    """Tests for config file integration with CLI."""

    def test_env_var_interpolation_in_config_file(
        self,
        runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that env vars in config file are expanded."""
        monkeypatch.setenv("MY_ENDPOINT", "http://from-env:8080/api/v1/lineage/events")

        config_file = tmp_path / ".airflow-correlator.yml"
        config_file.write_text(
            """\
correlator:
  endpoint: ${MY_ENDPOINT}
"""
        )

        @click.command()
        @click.option(
            "--config",
            callback=load_config_callback,
            expose_value=True,
            is_eager=True,
        )
        @click.pass_context
        def test_cmd(ctx: click.Context, config: str) -> None:
            click.echo(f"default_map: {ctx.default_map}")

        result = runner.invoke(test_cmd, ["--config", str(config_file)])

        assert result.exit_code == 0
        assert "http://from-env:8080/api/v1/lineage/events" in result.output
