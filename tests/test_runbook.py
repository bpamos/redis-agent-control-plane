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

    # Verify steps (now using step_ref)
    assert len(runbook.steps) > 0
    assert runbook.steps[0].id == "install_operator"
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


def test_step_resolution():
    """Test that step references are resolved correctly."""
    runbook_path = Path("runbooks/redis_enterprise/kubernetes/clustered.yaml")

    if not runbook_path.exists():
        pytest.skip(f"Runbook file not found: {runbook_path}")

    runbook = Runbook.from_yaml(runbook_path)

    # Verify that steps were loaded from step files
    assert len(runbook.steps) >= 4

    # First step should be install_operator
    assert runbook.steps[0].id == "install_operator"
    assert runbook.steps[0].name == "Install Redis Enterprise Operator"
    assert runbook.steps[0].tool == "kubectl"

    # Second step should be wait_operator_ready
    assert runbook.steps[1].id == "wait_operator_ready"
    assert runbook.steps[1].name == "Wait for operator to be ready"


def test_step_parameter_substitution():
    """Test that parameters are substituted in step commands."""
    runbook_path = Path("runbooks/redis_enterprise/kubernetes/clustered.yaml")

    if not runbook_path.exists():
        pytest.skip(f"Runbook file not found: {runbook_path}")

    runbook = Runbook.from_yaml(runbook_path)

    # Check that $NAMESPACE parameter is in the command
    # (it should remain as $NAMESPACE since it's a runbook-level variable)
    assert runbook.steps[0].command is not None
    assert "kubectl" in runbook.steps[0].command


def test_load_step_from_file():
    """Test loading a step from a YAML file."""
    steps_dir = Path("steps")

    if not steps_dir.exists():
        pytest.skip(f"Steps directory not found: {steps_dir}")

    step_ref = "redis_enterprise/kubernetes/install_operator"
    step_data = Runbook._load_step_from_file(step_ref, steps_dir)

    assert step_data["id"] == "install_operator"
    assert step_data["name"] == "Install Redis Enterprise Operator"
    assert step_data["tool"] == "kubectl"
    assert "parameters" in step_data
    assert len(step_data["parameters"]) > 0


def test_merge_parameters():
    """Test parameter merging with defaults and overrides."""
    step_data = {
        "id": "test_step",
        "name": "Test Step",
        "command": "kubectl apply -n $NAMESPACE",
        "parameters": [
            {"name": "namespace", "type": "string", "default": "default"},
            {"name": "replicas", "type": "int", "default": 3},
        ],
    }

    # Test with no overrides - should use default value
    merged = Runbook._merge_parameters(step_data, None)
    assert "default" in merged["command"]  # Default value substituted

    # Test with overrides - should use override value
    merged = Runbook._merge_parameters(step_data, {"namespace": "production"})
    assert "production" in merged["command"]  # Override value substituted


def test_step_validation_with_parameters():
    """Test that validation commands also get parameter substitution."""
    step_data = {
        "id": "test_step",
        "name": "Test Step",
        "command": "kubectl get pods -n $NAMESPACE",
        "validation": {
            "command": "kubectl get deployment test -n $NAMESPACE",
            "expect": "test",
            "retry": 5,
        },
        "parameters": [{"name": "namespace", "type": "string", "default": "default"}],
    }

    merged = Runbook._merge_parameters(step_data, {"namespace": "production"})
    assert merged["validation"] is not None
    assert "production" in merged["validation"]["command"]  # Parameter substituted


def test_inline_steps_still_work():
    """Test that runbooks with inline steps (not step_ref) still work."""
    runbook_path = Path("runbooks/redis_enterprise/vm/single_node.yaml")

    if not runbook_path.exists():
        pytest.skip(f"Runbook file not found: {runbook_path}")

    runbook = Runbook.from_yaml(runbook_path)

    # VM runbooks still use inline steps
    assert len(runbook.steps) > 0
    # These should have step_1, step_2, etc. as IDs
    assert runbook.steps[0].id.startswith("step_")


def test_mixed_inline_and_ref_steps():
    """Test that a runbook can have both inline and referenced steps."""
    # Create a temporary test runbook with mixed steps
    import tempfile

    test_runbook = """
runbook:
  id: test.mixed
  name: "Test Mixed Steps"
  description: "Test runbook with mixed step types"
  version: "1.0.0"

  steps:
    - step_ref: redis_enterprise/kubernetes/install_operator
      parameters:
        namespace: "test"

    - id: inline_step
      name: "Inline Step"
      description: "This is an inline step"
      tool: kubectl
      command: "kubectl get pods"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(test_runbook)
        temp_path = Path(f.name)

    try:
        steps_dir = Path("steps")
        if not steps_dir.exists():
            pytest.skip("Steps directory not found")

        runbook = Runbook.from_yaml(temp_path, steps_dir=steps_dir)

        assert len(runbook.steps) == 2
        assert runbook.steps[0].id == "install_operator"  # From step_ref
        assert runbook.steps[1].id == "inline_step"  # Inline
    finally:
        temp_path.unlink()


def test_step_file_not_found():
    """Test that missing step files raise appropriate error."""
    import tempfile

    test_runbook = """
runbook:
  id: test.missing
  name: "Test Missing Step"
  description: "Test runbook with missing step reference"
  version: "1.0.0"

  steps:
    - step_ref: nonexistent/step/path
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(test_runbook)
        temp_path = Path(f.name)

    try:
        steps_dir = Path("steps")
        if not steps_dir.exists():
            pytest.skip("Steps directory not found")

        with pytest.raises(FileNotFoundError):
            Runbook.from_yaml(temp_path, steps_dir=steps_dir)
    finally:
        temp_path.unlink()
