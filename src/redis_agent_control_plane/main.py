"""Main entry point for Redis Agent Control Plane CLI."""

import click

from redis_agent_control_plane import __version__
from redis_agent_control_plane.cli.explain import explain
from redis_agent_control_plane.cli.list_cmd import list_cmd
from redis_agent_control_plane.cli.plan import plan
from redis_agent_control_plane.cli.search import search
from redis_agent_control_plane.cli.validate import validate


@click.group()
@click.version_option(version=__version__, prog_name="redis-agent-control-plane")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Redis Agent Control Plane - Deterministic deployment planning with RAG-powered context.

    This tool helps you plan Redis Enterprise deployments by:
    - Routing deployment specs to validated runbooks
    - Retrieving relevant documentation via RAG
    - Assembling context packs for deployment execution
    """
    ctx.ensure_object(dict)


# Register commands
cli.add_command(plan)
cli.add_command(explain)
cli.add_command(search)
cli.add_command(validate)
cli.add_command(list_cmd, name="list")


if __name__ == "__main__":
    cli()
