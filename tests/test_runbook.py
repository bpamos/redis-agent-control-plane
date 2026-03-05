"""Unit tests for Runbook dataclass and YAML loader."""

from pathlib import Path

import pytest

from redis_agent_control_plane.orchestration.runbook import Runbook


def test_runbook_load_from_yaml():
    """Test loading a runbook from YAML file."""
    # Use the sample runbook we created
    runbook_path = Path("runbooks/redis_enterprise/kubernetes/clustered.yaml")

    if not runbook_path.exists():
        pytest.skip(f"Runbook file not found: {runbook_path}")

    runbook = Runbook.from_yaml(runbook_path)

    # Verify basic fields
    assert runbook.id == "runbook.redis_enterprise.kubernetes.clustered"
    assert runbook.name == "Redis Enterprise on Kubernetes - 3-Node Cluster"
    assert runbook.version == "2.0.0"
    assert len(runbook.description) > 0

    # Verify prerequisites
    assert len(runbook.prerequisites) > 0
    assert runbook.prerequisites[0].check == "kubectl_installed"
    assert "kubectl" in runbook.prerequisites[0].command

    # Verify steps
    assert len(runbook.steps) > 0
    assert runbook.steps[0].id == "step_1"
    assert runbook.steps[0].name == "Install Redis Enterprise Operator"
    assert len(runbook.steps[0].doc_refs) > 0
    assert runbook.steps[0].rag_assist is not None
    assert runbook.steps[0].tool == "kubectl"
    assert runbook.steps[0].validation is not None

    # Verify post-validations
    assert len(runbook.post_validations) > 0
    assert runbook.post_validations[0].check == "operator_running"

    # Verify rollback
    assert len(runbook.rollback) > 0
    assert "delete" in runbook.rollback[0].command.lower()


def test_runbook_load_single_node():
    """Test loading single-node runbook."""
    runbook_path = Path("runbooks/redis_enterprise/kubernetes/single_node.yaml")

    if not runbook_path.exists():
        pytest.skip(f"Runbook file not found: {runbook_path}")

    runbook = Runbook.from_yaml(runbook_path)

    assert runbook.id == "runbook.redis_enterprise.kubernetes.single_node"
    assert "single" in runbook.name.lower() or "Single" in runbook.name
    assert len(runbook.steps) > 0


def test_runbook_load_vm():
    """Test loading VM runbook."""
    runbook_path = Path("runbooks/redis_enterprise/vm/single_node.yaml")

    if not runbook_path.exists():
        pytest.skip(f"Runbook file not found: {runbook_path}")

    runbook = Runbook.from_yaml(runbook_path)

    assert runbook.id == "runbook.redis_enterprise.vm.single_node"
    assert len(runbook.steps) > 0
    assert len(runbook.prerequisites) > 0


def test_runbook_load_redis_cloud():
    """Test loading Redis Cloud runbook."""
    runbook_path = Path("runbooks/redis_cloud/aws/vpc_peering.yaml")

    if not runbook_path.exists():
        pytest.skip(f"Runbook file not found: {runbook_path}")

    runbook = Runbook.from_yaml(runbook_path)

    assert runbook.id == "runbook.redis_cloud.aws.vpc_peering"
    assert "cloud" in runbook.name.lower() or "Cloud" in runbook.name
    assert len(runbook.steps) > 0


def test_runbook_load_active_active():
    """Test loading Active-Active runbook."""
    runbook_path = Path("runbooks/redis_enterprise/kubernetes/active_active.yaml")

    if not runbook_path.exists():
        pytest.skip(f"Runbook file not found: {runbook_path}")

    runbook = Runbook.from_yaml(runbook_path)

    assert runbook.id == "runbook.redis_enterprise.kubernetes.active_active"
    assert "active" in runbook.name.lower() or "Active" in runbook.name
    assert len(runbook.steps) > 0


def test_runbook_file_not_found():
    """Test error handling when runbook file not found."""
    runbook_path = Path("runbooks/nonexistent/runbook.yaml")

    with pytest.raises(FileNotFoundError, match="Runbook file not found"):
        Runbook.from_yaml(runbook_path)


def test_runbook_invalid_yaml(tmp_path):
    """Test error handling for invalid YAML."""
    # Create a temporary invalid YAML file
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("invalid: yaml: content: [")

    with pytest.raises(Exception):  # YAML parsing error
        Runbook.from_yaml(invalid_yaml)


def test_runbook_missing_required_field(tmp_path):
    """Test error handling for missing required fields."""
    # Create a YAML file missing the 'runbook' key
    invalid_yaml = tmp_path / "missing_key.yaml"
    invalid_yaml.write_text("some_other_key: value")

    with pytest.raises(ValueError, match="missing 'runbook' key"):
        Runbook.from_yaml(invalid_yaml)


def test_runbook_step_structure():
    """Test runbook step structure in detail."""
    runbook_path = Path("runbooks/redis_enterprise/kubernetes/clustered.yaml")

    if not runbook_path.exists():
        pytest.skip(f"Runbook file not found: {runbook_path}")

    runbook = Runbook.from_yaml(runbook_path)

    # Check first step in detail
    step = runbook.steps[0]
    assert step.id is not None
    assert step.name is not None
    assert step.description is not None

    # Check doc refs
    if len(step.doc_refs) > 0:
        doc_ref = step.doc_refs[0]
        assert doc_ref.path is not None
        assert doc_ref.section is not None

    # Check RAG assist
    if step.rag_assist is not None:
        assert step.rag_assist.query is not None
        assert isinstance(step.rag_assist.filters, dict)
        assert step.rag_assist.max_results > 0

    # Check validation
    if step.validation is not None:
        assert step.validation.command is not None
        assert step.validation.expect is not None
        assert step.validation.retry >= 1
