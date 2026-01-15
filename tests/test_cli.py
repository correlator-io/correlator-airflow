"""Tests for CLI module.

This module tests the airflow-correlator CLI commands.

Uses Click's CliRunner for CLI testing.
"""

import pytest
from click.testing import CliRunner

from airflow_correlator import __version__
from airflow_correlator.cli import cli

# =============================================================================
# A. Command Structure Tests
# =============================================================================


@pytest.mark.unit
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

    def test_cli_help_mentions_transport_configuration(self, runner: CliRunner) -> None:
        """Test that help text mentions transport configuration options."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        # Help should mention configuration options
        assert (
            "openlineage.yml" in result.output
            or "AIRFLOW__OPENLINEAGE__TRANSPORT" in result.output
        )

    def test_cli_help_mentions_correlator(self, runner: CliRunner) -> None:
        """Test that help text mentions Correlator."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Correlator" in result.output or "correlator" in result.output
