"""Plan command - Generate context pack from deployment spec."""

import json
import sys
from pathlib import Path

import click
import yaml

from redis_agent_control_plane.orchestration.context_builder import ContextBuilder
from redis_agent_control_plane.orchestration.deployment_spec import DeploymentSpec
from redis_agent_control_plane.orchestration.router import RunbookRouter


@click.command()
@click.option(
    "--spec",
    type=click.Path(exists=True, path_type=Path),
    help="Path to deployment spec YAML file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="context_pack.json",
    help="Output path for context pack JSON (default: context_pack.json)",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive mode - prompt for deployment spec fields",
)
@click.option(
    "--no-rag",
    is_flag=True,
    help="Skip RAG retrieval (deterministic only)",
)
def plan(spec: Path | None, output: Path, interactive: bool, no_rag: bool) -> None:
    """Generate a context pack from a deployment specification.

    This command takes a deployment spec (YAML) and generates a complete
    context pack (JSON) containing:
    - Matched runbook with ordered steps
    - Documentation references
    - RAG-retrieved context chunks (unless --no-rag)

    Examples:

        \b
        # Generate from spec file
        redis-agent-control-plane plan --spec deployment.yaml

        \b
        # Interactive mode
        redis-agent-control-plane plan --interactive

        \b
        # Skip RAG retrieval
        redis-agent-control-plane plan --spec deployment.yaml --no-rag
    """
    try:
        # Get deployment spec
        if interactive:
            deployment_spec = _interactive_spec()
        elif spec:
            deployment_spec = _load_spec_from_file(spec)
        else:
            click.echo("Error: Either --spec or --interactive must be provided", err=True)
            sys.exit(1)

        # Route to runbook
        click.echo(f"Routing deployment spec: {deployment_spec.to_runbook_id()}")
        router = RunbookRouter()
        runbook_id = router.route(deployment_spec)
        click.echo(f"✓ Matched runbook: {runbook_id}")

        # Load runbook
        click.echo("Loading runbook...")
        from pathlib import Path as PathLib

        workspace_root = PathLib(__file__).parent.parent.parent.parent
        runbook_relative = runbook_id.replace("runbook.", "").replace(".", "/")
        runbook_path = workspace_root / "runbooks" / runbook_relative
        runbook_path = runbook_path.with_suffix(".yaml")

        from redis_agent_control_plane.orchestration.runbook import Runbook

        runbook = Runbook.from_yaml(runbook_path)

        # Build context packs for each step
        click.echo(f"Building context packs for {len(runbook.steps)} steps...")
        builder = ContextBuilder()
        context_packs = []

        for step in runbook.steps:
            context_pack = builder.build_context_pack(
                runbook=runbook,
                step=step,
                deployment_spec=deployment_spec,
                use_rag=not no_rag,
            )
            context_packs.append(context_pack.to_dict())

        # Save to file
        output.parent.mkdir(parents=True, exist_ok=True)
        result_data = {
            "runbook_id": runbook_id,
            "deployment_spec": deployment_spec.to_dict(),
            "steps": context_packs,
        }
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2)

        click.echo(f"✓ Context pack saved to: {output}")
        click.echo(f"  - Runbook: {runbook_id}")
        click.echo(f"  - Steps: {len(context_packs)}")
        if not no_rag:
            total_chunks = sum(len(cp["rag_chunks"]) for cp in context_packs)
            click.echo(f"  - Total RAG chunks: {total_chunks}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _load_spec_from_file(spec_path: Path) -> DeploymentSpec:
    """Load deployment spec from YAML file."""
    with open(spec_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "deployment_spec" in data:
        data = data["deployment_spec"]

    return DeploymentSpec.from_dict(data)


def _interactive_spec() -> DeploymentSpec:
    """Prompt user for deployment spec fields interactively."""
    from redis_agent_control_plane.orchestration.deployment_spec import (
        NetworkingConfig,
        ScaleConfig,
    )

    click.echo("Interactive deployment spec builder")
    click.echo("=" * 40)

    product = click.prompt(
        "Product",
        type=click.Choice(["redis_enterprise", "redis_cloud", "redis_stack"]),
        default="redis_enterprise",
    )

    platform = click.prompt(
        "Platform",
        type=click.Choice(["vm", "kubernetes", "eks", "gke", "aks", "openshift"]),
        default="kubernetes",
    )

    topology = click.prompt(
        "Topology",
        type=click.Choice(["single_node", "clustered", "active_active"]),
        default="clustered",
    )

    # Networking
    networking_type = click.prompt(
        "Networking type",
        type=click.Choice(["public", "private", "vpc_peering"]),
        default="private",
    )
    tls_enabled = click.confirm("Enable TLS?", default=True)
    networking = NetworkingConfig(type=networking_type, tls_enabled=tls_enabled)

    # Scale
    nodes = click.prompt("Number of nodes", type=int, default=3)
    shards = click.prompt("Number of shards", type=int, default=1)
    replicas = click.prompt("Number of replicas", type=int, default=1)
    scale = ScaleConfig(nodes=nodes, shards=shards, replicas=replicas)

    return DeploymentSpec(
        product=product, platform=platform, topology=topology, networking=networking, scale=scale
    )
