"""Main entry point for Redis Agent Control Plane."""

import sys

from redis_agent_control_plane import __version__


def main() -> int:
    """Main entry point - minimal smoke check."""
    print(f"Redis Agent Control Plane v{__version__}")
    print("Status: Initialized")
    print("Ready for development.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
