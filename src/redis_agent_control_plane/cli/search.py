"""Search command - Ad-hoc RAG queries."""

import sys

import click

from redis_agent_control_plane.rag.retriever import RedisRetriever


@click.command()
@click.argument("query")
@click.option(
    "--product",
    type=click.Choice(["redis_enterprise", "redis_cloud", "redis_stack"]),
    help="Filter by product area",
)
@click.option(
    "--category",
    type=click.Choice(["operate", "develop", "integrate"]),
    help="Filter by documentation category",
)
@click.option(
    "--max-results",
    "-n",
    type=int,
    default=5,
    help="Maximum number of results (default: 5)",
)
@click.option(
    "--show-content",
    is_flag=True,
    help="Show full content of each chunk",
)
def search(
    query: str,
    product: str | None,
    category: str | None,
    max_results: int,
    show_content: bool,
) -> None:
    """Search documentation using RAG (Retrieval-Augmented Generation).

    This command performs semantic search across Redis documentation
    and returns the most relevant chunks.

    Examples:

        \b
        # Basic search
        redis-agent-control-plane search "How do I enable TLS?"

        \b
        # Filter by product
        redis-agent-control-plane search "Active-Active setup" --product redis_enterprise

        \b
        # Show more results with full content
        redis-agent-control-plane search "Kubernetes deployment" -n 10 --show-content
    """
    try:
        # Build filters
        filters = {}
        if product:
            filters["product_area"] = product
        if category:
            filters["category"] = category

        # Perform search
        click.echo(f"Searching for: {query}")
        if filters:
            click.echo(f"Filters: {filters}")
        click.echo("")

        retriever = RedisRetriever()
        results = retriever.search(
            query=query,
            top_k=max_results,
            product_area=filters.get("product_area"),
            category=filters.get("category"),
        )

        if not results:
            click.echo("No results found.")
            return

        # Display results
        click.echo(f"Found {len(results)} results:")
        click.echo("=" * 80)
        click.echo("")

        for i, result in enumerate(results, 1):
            title = result.get("title", "Untitled")
            doc_path = result.get("doc_path", "Unknown")
            section = result.get("section_heading", "")
            content = result.get("content", "")
            distance = result.get("distance", 0.0)

            click.echo(f"{i}. {title}")
            click.echo(f"   Source: {doc_path}")
            if section:
                click.echo(f"   Section: {section}")
            click.echo(f"   Distance: {distance:.4f}")

            if show_content:
                click.echo("")
                click.echo("   Content:")
                # Indent content
                for line in content.split("\n"):
                    click.echo(f"   {line}")
            else:
                # Show preview
                preview = content[:150] + "..." if len(content) > 150 else content
                click.echo(f"   Preview: {preview}")

            click.echo("")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
