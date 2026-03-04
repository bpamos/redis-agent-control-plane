#!/usr/bin/env python3
"""Corpus inventory script: scan ../docs, extract metadata, tag, and export manifest."""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Directories to skip during scanning
SKIP_DIRS = {
    ".git",
    "node_modules",
    "build",
    "dist",
    "site",
    "public",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def extract_title(content: str) -> str | None:
    """Extract title from first '# ' heading in markdown content."""
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def apply_heuristic_tags(rel_path: str) -> list[str]:
    """Apply heuristic tags based on path keywords."""
    tags = []
    path_lower = rel_path.lower()

    # Redis Enterprise
    if any(
        keyword in path_lower
        for keyword in ["redis-enterprise", "/enterprise/", "/rs/", "/operate/rs/"]
    ):
        tags.append("redis_enterprise")

    # Redis Cloud
    if any(keyword in path_lower for keyword in ["/redis-cloud/", "/cloud/", "/rc/"]):
        tags.append("redis_cloud")

    # Redis Stack
    if "/stack/" in path_lower:
        tags.append("redis_stack")

    # Default: Redis OSS or general
    if not tags:
        tags.append("redis_oss_or_general")

    return tags


def should_skip_directory(path: Path) -> bool:
    """Check if directory should be skipped during traversal."""
    return path.name in SKIP_DIRS


def discover_markdown_files(source_path: Path) -> list[Path]:
    """Recursively discover .md files, skipping non-content directories."""
    markdown_files = []

    def walk_directory(directory: Path) -> None:
        """Recursively walk directory tree."""
        try:
            for item in directory.iterdir():
                if item.is_dir():
                    if not should_skip_directory(item):
                        walk_directory(item)
                elif item.is_file() and item.suffix == ".md":
                    markdown_files.append(item)
        except PermissionError as e:
            print(f"Warning: Permission denied for {directory}: {e}", file=sys.stderr)

    walk_directory(source_path)
    return markdown_files


def extract_directory_prefix(rel_path: str, depth: int = 2) -> str:
    """Extract directory prefix (first N path segments)."""
    parts = Path(rel_path).parts
    if len(parts) <= depth:
        return str(Path(*parts[:-1])) if len(parts) > 1 else "(root)"
    return str(Path(*parts[:depth]))


def build_inventory(source_path: Path, source_repo: str = "redis/docs") -> list[dict]:
    """Build corpus inventory with metadata and tags."""
    if not source_path.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path}")

    if not source_path.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_path}")

    markdown_files = discover_markdown_files(source_path)
    inventory = []

    for file_path in markdown_files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Skipping unreadable file {file_path}: {e}", file=sys.stderr)
            continue

        rel_path = str(file_path.relative_to(source_path))
        title = extract_title(content)
        char_count = len(content)
        tags = apply_heuristic_tags(rel_path)

        record = {
            "source_repo": source_repo,
            "rel_path": rel_path,
            "title": title,
            "char_count": char_count,
            "tags": tags,
        }
        inventory.append(record)

    return inventory


def write_manifest(inventory: list[dict], output_path: Path) -> None:
    """Write inventory to JSONL manifest file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for record in inventory:
            f.write(json.dumps(record) + "\n")


def print_summary(inventory: list[dict]) -> None:
    """Print inventory summary statistics."""
    total_files = len(inventory)
    total_chars = sum(record["char_count"] for record in inventory)

    # Count by directory prefix
    prefix_counts = Counter(extract_directory_prefix(record["rel_path"]) for record in inventory)

    # Count by tag
    tag_counts: defaultdict[str, int] = defaultdict(int)
    for record in inventory:
        for tag in record["tags"]:
            tag_counts[tag] += 1

    print(f"\n{'='*70}")
    print("Corpus Inventory Summary")
    print(f"{'='*70}")
    print(f"Total files: {total_files:,}")
    print(f"Total characters: {total_chars:,}")
    print(f"{'='*70}\n")

    print("Top 20 Directory Prefixes by File Count:")
    print(f"{'Prefix':<40} {'Count':>10}")
    print("-" * 70)
    for prefix, count in prefix_counts.most_common(20):
        print(f"{prefix:<40} {count:>10,}")

    print(f"\n{'='*70}\n")
    print("Tag Distribution:")
    print(f"{'Tag':<40} {'Count':>10}")
    print("-" * 70)
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        print(f"{tag:<40} {count:>10,}")
    print(f"{'='*70}\n")


def main() -> int:
    """Main entry point for corpus inventory."""
    parser = argparse.ArgumentParser(description="Build corpus inventory with metadata and tags")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("../docs"),
        help="Path to corpus directory (default: ../docs)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/corpus_manifest.jsonl"),
        help="Output manifest path (default: data/corpus_manifest.jsonl)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="redis/docs",
        help="Source repository name (default: redis/docs)",
    )

    args = parser.parse_args()

    try:
        print(f"Building inventory from: {args.source}")
        inventory = build_inventory(args.source, args.repo)

        print(f"Writing manifest to: {args.output}")
        write_manifest(inventory, args.output)

        print_summary(inventory)

        print(f"✓ Manifest written to: {args.output}")
        print(f"✓ Total records: {len(inventory):,}")
        return 0
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
