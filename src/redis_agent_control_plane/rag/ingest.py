"""Markdown ingestion for redis/docs corpus."""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Document:
    """Represents an ingested markdown document."""

    file_path: str
    title: str | None
    content: str
    source_repo: str


# Directories to skip during ingestion
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


def should_skip_directory(path: Path) -> bool:
    """Check if directory should be skipped during traversal."""
    return path.name in SKIP_DIRS


def load_markdown_file(file_path: Path) -> str | None:
    """Load markdown file content as UTF-8, return None if unreadable."""
    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"Warning: Skipping unreadable file {file_path}: {e}", file=sys.stderr)
        return None


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


def ingest_corpus(source_path: Path, source_repo: str = "redis/docs") -> list[Document]:
    """Ingest markdown corpus from source path."""
    if not source_path.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path}")

    if not source_path.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source_path}")

    markdown_files = discover_markdown_files(source_path)
    documents = []

    for file_path in markdown_files:
        content = load_markdown_file(file_path)
        if content is None:
            continue

        relative_path = file_path.relative_to(source_path)
        title = extract_title(content)

        doc = Document(
            file_path=str(relative_path),
            title=title,
            content=content,
            source_repo=source_repo,
        )
        documents.append(doc)

    return documents


def print_ingestion_summary(documents: list[Document]) -> None:
    """Print summary of ingested documents."""
    total_chars = sum(len(doc.content) for doc in documents)

    print(f"\n{'='*60}")
    print("Ingestion Summary")
    print(f"{'='*60}")
    print(f"Markdown files loaded: {len(documents)}")
    print(f"Total characters: {total_chars:,}")
    print(f"{'='*60}\n")

    if documents:
        sample = documents[0]
        content_preview = sample.content[:200].replace("\n", " ")
        print("Sample Document:")
        print(f"  Path: {sample.file_path}")
        print(f"  Title: {sample.title or '(no title)'}")
        print(f"  Content preview: {content_preview}...")
        print(f"{'='*60}\n")


def main() -> int:
    """Main entry point for ingestion smoke-check."""
    parser = argparse.ArgumentParser(description="Ingest markdown files from redis/docs corpus")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("../docs"),
        help="Path to corpus directory (default: ../docs)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="redis/docs",
        help="Source repository name (default: redis/docs)",
    )

    args = parser.parse_args()

    try:
        documents = ingest_corpus(args.source, args.repo)
        print_ingestion_summary(documents)
        return 0
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
