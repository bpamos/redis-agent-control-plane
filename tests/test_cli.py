"""Unit tests for CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from redis_agent_control_plane.main import cli


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


def test_cli_help(runner):
    """Test that CLI shows help message."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Redis Agent Control Plane" in result.output
    assert "plan" in result.output
    assert "explain" in result.output
    assert "search" in result.output
    assert "validate" in result.output
    assert "list" in result.output


def test_cli_version(runner):
    """Test that CLI shows version."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "redis-agent-control-plane" in result.output


def test_plan_help(runner):
    """Test plan command help."""
    result = runner.invoke(cli, ["plan", "--help"])
    assert result.exit_code == 0
    assert "Generate a context pack" in result.output
    assert "--spec" in result.output
    assert "--interactive" in result.output
    assert "--no-rag" in result.output


def test_explain_help(runner):
    """Test explain command help."""
    result = runner.invoke(cli, ["explain", "--help"])
    assert result.exit_code == 0
    assert "Explain a context pack" in result.output


def test_search_help(runner):
    """Test search command help."""
    result = runner.invoke(cli, ["search", "--help"])
    assert result.exit_code == 0
    assert "Search documentation" in result.output
    assert "--product" in result.output
    assert "--category" in result.output


def test_validate_help(runner):
    """Test validate command help."""
    result = runner.invoke(cli, ["validate", "--help"])
    assert result.exit_code == 0
    assert "Run validation scripts" in result.output
    assert "--runbooks" in result.output
    assert "--registry" in result.output
    assert "--steps" in result.output


def test_list_help(runner):
    """Test list command help."""
    result = runner.invoke(cli, ["list", "--help"])
    assert result.exit_code == 0
    assert "List available runbooks or steps" in result.output


def test_list_runbooks(runner):
    """Test list runbooks command."""
    result = runner.invoke(cli, ["list", "runbooks"])
    assert result.exit_code == 0
    assert "Found" in result.output
    assert "runbooks" in result.output


def test_list_steps(runner):
    """Test list steps command."""
    result = runner.invoke(cli, ["list", "steps"])
    assert result.exit_code == 0
    assert "Found" in result.output
    assert "steps" in result.output


def test_plan_missing_args(runner):
    """Test plan command without required arguments."""
    result = runner.invoke(cli, ["plan"])
    assert result.exit_code == 1
    assert "Error" in result.output


@patch("redis_agent_control_plane.cli.plan.RunbookRouter")
@patch("redis_agent_control_plane.cli.plan.ContextBuilder")
def test_plan_with_spec(mock_builder, mock_router, runner, tmp_path):
    """Test plan command with spec file."""
    # Create a test spec file
    spec_file = tmp_path / "test_spec.yaml"
    spec_file.write_text("""
deployment_spec:
  product: redis_enterprise
  platform: kubernetes
  topology: clustered
  networking:
    type: private
    vpc_cidr: "10.0.0.0/16"
  scale:
    nodes: 3
    shards: 1
    replicas: 1
""")

    # Mock the router to return a real runbook ID
    mock_router_instance = MagicMock()
    mock_router_instance.route.return_value = "runbook.redis_enterprise.kubernetes.clustered"
    mock_router.return_value = mock_router_instance

    # Mock the builder to avoid Redis dependency
    mock_context_pack = MagicMock()
    mock_context_pack.to_dict.return_value = {
        "runbook_id": "runbook.redis_enterprise.kubernetes.clustered",
        "step_id": "test_step",
        "step_name": "Test Step",
        "step_description": "Test description",
        "deterministic_doc_refs": [],
        "rag_chunks": [],
    }

    mock_builder_instance = MagicMock()
    mock_builder_instance.build_context_pack.return_value = mock_context_pack
    mock_builder.return_value = mock_builder_instance

    # Run command
    output_file = tmp_path / "context_pack.json"
    result = runner.invoke(
        cli, ["plan", "--spec", str(spec_file), "--output", str(output_file), "--no-rag"]
    )

    # Print output for debugging
    if result.exit_code != 0:
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")

    assert result.exit_code == 0
    assert "Matched runbook" in result.output
    assert output_file.exists()


def test_explain_missing_file(runner):
    """Test explain command with missing file."""
    result = runner.invoke(cli, ["explain", "nonexistent.json"])
    assert result.exit_code != 0


def test_validate_steps(runner):
    """Test validate command for steps."""
    result = runner.invoke(cli, ["validate", "--steps"])
    # Should run successfully if steps directory exists
    assert "Validating steps" in result.output
