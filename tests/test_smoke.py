"""Smoke tests to verify basic functionality."""

from click.testing import CliRunner

from redis_agent_control_plane import __version__
from redis_agent_control_plane.main import cli


def test_version():
    """Verify version is set."""
    assert __version__ == "1.0.0"


def test_cli_runs():
    """Verify CLI entry point runs without error."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Redis Agent Control Plane" in result.output
