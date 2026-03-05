#!/usr/bin/env python3
"""Interactive CLI tool for testing routing logic and debugging.

This script provides an interactive interface to test the RunbookRouter
and see how different DeploymentSpecs map to runbooks.

Usage:
    python scripts/test_routing.py
    python scripts/test_routing.py --spec '{"product": "redis_enterprise", "platform": "vm", "topology": "single_node"}'
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from redis_agent_control_plane.orchestration.deployment_spec import (
    DeploymentSpec,
    NetworkingConfig,
    NetworkingType,
    Platform,
    Product,
    ScaleConfig,
    Topology,
)
from redis_agent_control_plane.orchestration.router import (
    RunbookNotFoundError,
    RunbookRouter,
)


def create_spec_from_dict(spec_dict: dict) -> DeploymentSpec:
    """Create DeploymentSpec from dictionary.

    Args:
        spec_dict: Dictionary with deployment spec fields

    Returns:
        DeploymentSpec instance
    """
    # Extract networking config if present
    networking = None
    if "networking" in spec_dict:
        net_dict = spec_dict["networking"]
        networking = NetworkingConfig(
            type=net_dict.get("type", "private"),
            tls_enabled=net_dict.get("tls_enabled", False),
        )
    else:
        # Default networking
        networking = NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=False)

    # Extract scale config if present
    scale = None
    if "scale" in spec_dict:
        scale_dict = spec_dict["scale"]
        scale = ScaleConfig(
            nodes=scale_dict.get("nodes", 1),
            shards=scale_dict.get("shards", 1),
            replicas=scale_dict.get("replicas", 0),
        )
    else:
        # Default scale based on topology
        topology = spec_dict.get("topology", "single_node")
        if topology == "clustered":
            scale = ScaleConfig(nodes=3, shards=1, replicas=1)
        elif topology == "active_active":
            scale = ScaleConfig(nodes=2, shards=1, replicas=1)
        else:
            scale = ScaleConfig(nodes=1, shards=1, replicas=0)

    # Create DeploymentSpec (strings will be auto-converted to enums)
    return DeploymentSpec(
        product=spec_dict.get("product", "redis_enterprise"),
        platform=spec_dict.get("platform", "vm"),
        topology=spec_dict.get("topology", "single_node"),
        networking=networking,
        scale=scale,
        cloud_provider=spec_dict.get("cloud_provider"),
        requirements=spec_dict.get("requirements", []),
    )


def print_banner():
    """Print welcome banner."""
    print("=" * 80)
    print("Redis Agent Control Plane - Routing Test CLI")
    print("=" * 80)
    print()


def print_available_runbooks(router: RunbookRouter):
    """Print all available runbooks."""
    runbooks = router.list_available_runbooks()
    print(f"\n📚 Available Runbooks ({len(runbooks)}):")
    print("-" * 80)
    for runbook_id in sorted(runbooks):
        print(f"  • {runbook_id}")
    print()


def print_deployment_spec(spec: DeploymentSpec):
    """Print deployment spec in a readable format."""
    print("\n📋 Deployment Specification:")
    print("-" * 80)
    print(f"  Product:    {spec.product.value}")
    print(f"  Platform:   {spec.platform.value}")
    print(f"  Topology:   {spec.topology.value}")
    if spec.networking:
        print(f"  Networking: {spec.networking.type.value}, TLS={spec.networking.tls_enabled}")
    if spec.scale:
        print(f"  Scale:      nodes={spec.scale.nodes}, shards={spec.scale.shards}, replicas={spec.scale.replicas}")
    if spec.cloud_provider:
        print(f"  Cloud:      {spec.cloud_provider.value}")
    print()


def test_routing(router: RunbookRouter, spec: DeploymentSpec):
    """Test routing for a given deployment spec."""
    print_deployment_spec(spec)
    
    try:
        runbook_id = router.route(spec)
        print(f"✅ Routed to: {runbook_id}")
        
        # Try to load the runbook
        runbook = router.load_runbook(runbook_id)
        print(f"\n📖 Runbook Details:")
        print(f"  Name:         {runbook.name}")
        print(f"  Version:      {runbook.version}")
        print(f"  Steps:        {len(runbook.steps)}")
        print(f"  Prerequisites: {len(runbook.prerequisites)}")
        print(f"  Validations:  {len(runbook.post_validations)}")
        print(f"  Description:  {runbook.description[:80]}...")
        
    except RunbookNotFoundError as e:
        print(f"❌ Routing failed: {e}")


def interactive_mode(router: RunbookRouter):
    """Run interactive mode for testing routing."""
    print("\n🔧 Interactive Routing Test Mode")
    print("=" * 80)
    print("\nEnter deployment specifications to test routing.")
    print("Type 'help' for examples, 'list' for available runbooks, 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("routing> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == "help":
                print_help()
                continue
            
            if user_input.lower() == "list":
                print_available_runbooks(router)
                continue
            
            # Parse as JSON
            try:
                spec_dict = json.loads(user_input)
                spec = create_spec_from_dict(spec_dict)
                test_routing(router, spec)
            except json.JSONDecodeError:
                print("❌ Invalid JSON. Type 'help' for examples.")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


def print_help():
    """Print help with examples."""
    print("\n📖 Examples:")
    print("-" * 80)
    print("\n1. VM Single Node:")
    print('   {"product": "redis_enterprise", "platform": "vm", "topology": "single_node"}')
    
    print("\n2. VM 3-Node Cluster:")
    print('   {"product": "redis_enterprise", "platform": "vm", "topology": "clustered"}')
    
    print("\n3. Kubernetes Cluster:")
    print('   {"product": "redis_enterprise", "platform": "kubernetes", "topology": "clustered"}')
    
    print("\n4. Redis Cloud:")
    print('   {"product": "redis_cloud", "platform": "aws", "topology": "vpc_peering"}')
    
    print("\n5. With Networking:")
    print('   {"product": "redis_enterprise", "platform": "vm", "topology": "clustered", "networking": {"type": "private", "tls_enabled": true}}')
    
    print("\n6. With Scale:")
    print('   {"product": "redis_enterprise", "platform": "kubernetes", "topology": "clustered", "scale": {"nodes": 3, "shards": 2, "replicas": 1}}')
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive CLI tool for testing routing logic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python scripts/test_routing.py

  # Test a specific spec
  python scripts/test_routing.py --spec '{"product": "redis_enterprise", "platform": "vm", "topology": "single_node"}'

  # List available runbooks
  python scripts/test_routing.py --list
        """,
    )
    parser.add_argument(
        "--spec",
        type=str,
        help="JSON deployment spec to test (skips interactive mode)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available runbooks and exit",
    )
    parser.add_argument(
        "--runbooks-dir",
        type=str,
        default="runbooks",
        help="Path to runbooks directory (default: runbooks)",
    )

    args = parser.parse_args()

    # Initialize router
    runbooks_dir = Path(args.runbooks_dir)
    if not runbooks_dir.exists():
        print(f"❌ Runbooks directory not found: {runbooks_dir}")
        return 1

    router = RunbookRouter(runbooks_dir=runbooks_dir)

    print_banner()

    # List mode
    if args.list:
        print_available_runbooks(router)
        return 0

    # Single spec mode
    if args.spec:
        try:
            spec_dict = json.loads(args.spec)
            spec = create_spec_from_dict(spec_dict)
            test_routing(router, spec)
            return 0
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    # Interactive mode
    interactive_mode(router)
    return 0


if __name__ == "__main__":
    sys.exit(main())

