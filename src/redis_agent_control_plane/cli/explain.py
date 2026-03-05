"""Explain command - Pretty-print context pack as markdown."""

import json
import sys
from pathlib import Path

import click


@click.command()
@click.argument("context_pack", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output path for markdown report (default: stdout)",
)
def explain(context_pack: Path, output: Path | None) -> None:
    """Explain a context pack in human-readable markdown format.

    This command takes a context pack JSON file and generates a readable
    markdown report showing:
    - Deployment specification
    - Matched runbook and steps
    - Documentation references
    - RAG-retrieved context chunks

    Examples:

        \b
        # Print to stdout
        redis-agent-control-plane explain context_pack.json

        \b
        # Save to file
        redis-agent-control-plane explain context_pack.json -o report.md
    """
    try:
        # Load context pack
        with open(context_pack, encoding="utf-8") as f:
            data = json.load(f)

        # Generate markdown report
        report = _generate_markdown_report(data)

        # Output
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                f.write(report)
            click.echo(f"✓ Report saved to: {output}")
        else:
            click.echo(report)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _generate_markdown_report(data: dict) -> str:
    """Generate markdown report from context pack data."""
    lines = []

    # Header
    runbook_id = data.get("runbook_id", "Unknown")
    lines.append(f"# Context Pack: {runbook_id}")
    lines.append("")

    # Deployment Spec
    deployment_spec = data.get("deployment_spec", {})
    lines.append("## Deployment Specification")
    lines.append("")
    lines.append(f"- **Product:** {deployment_spec.get('product', 'Unknown')}")
    lines.append(f"- **Platform:** {deployment_spec.get('platform', 'Unknown')}")
    lines.append(f"- **Topology:** {deployment_spec.get('topology', 'Unknown')}")
    if deployment_spec.get("cloud_provider"):
        lines.append(f"- **Cloud Provider:** {deployment_spec['cloud_provider']}")
    lines.append("")

    # Steps
    steps = data.get("steps", [])
    lines.append(f"## Steps ({len(steps)})")
    lines.append("")

    for i, step_pack in enumerate(steps, 1):
        step_name = step_pack.get("step_name", "Unknown")
        step_desc = step_pack.get("step_description", "")

        lines.append(f"### {i}. {step_name}")
        lines.append("")
        lines.append(f"**Description:** {step_desc}")
        lines.append("")

        # Doc refs
        doc_refs = step_pack.get("deterministic_doc_refs", [])
        if doc_refs:
            lines.append("**Documentation:**")
            for ref in doc_refs:
                lines.append(f"- {ref.get('path', '')} → {ref.get('section', '')}")
            lines.append("")

        # RAG chunks for this step
        rag_chunks = step_pack.get("rag_chunks", [])
        if rag_chunks:
            lines.append(f"**RAG Context ({len(rag_chunks)} chunks):**")
            for j, chunk in enumerate(rag_chunks[:3], 1):  # Show first 3 per step
                title = chunk.get("title", "Untitled")
                doc_path = chunk.get("doc_path", "Unknown")
                distance = chunk.get("vector_distance", 0.0)
                content = chunk.get("content", "")

                lines.append(f"  {j}. {title} (distance: {distance:.4f})")
                lines.append(f"     Source: {doc_path}")
                # Show first 100 chars
                if len(content) > 100:
                    preview = content[:100] + "..."
                else:
                    preview = content
                lines.append(f"     > {preview}")
            if len(rag_chunks) > 3:
                lines.append(f"     *... and {len(rag_chunks) - 3} more chunks*")
            lines.append("")

    return "\n".join(lines)
