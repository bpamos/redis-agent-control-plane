"""Smoke tests to verify basic functionality."""

from redis_agent_control_plane import __version__
from redis_agent_control_plane.main import main


def test_version():
    """Verify version is set."""
    assert __version__ == "0.1.0"


def test_main_runs():
    """Verify main entry point runs without error."""
    result = main()
    assert result == 0
