"""Adaptive H2/H3 chunking for Redis documentation."""

import re
from dataclasses import dataclass
from typing import Any

import yaml  # type: ignore

from redis_agent_control_plane.rag.ingest import Document


@dataclass
class Chunk:
    """Represents a chunk of a document with metadata."""

    # Content
    content: str

    # Metadata fields
    source: str
    doc_path: str
    doc_url: str
    title: str
    category: str
    product_area: str
    section_heading: str
    toc_path: str
    chunk_id: str
    chunk_index: int
    subchunk_index: int


@dataclass
class Section:
    """Represents a section extracted from a document."""

    heading: str
    content: str
    level: int  # 2 for H2, 3 for H3
    parent_heading: str | None = None


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Returns:
        Tuple of (frontmatter_dict, content_without_frontmatter)
    """
    # Check if content starts with ---
    if not content.startswith("---"):
        return {}, content

    # Find the closing ---
    lines = content.split("\n")
    end_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break

    if end_index == -1:
        return {}, content

    # Extract frontmatter
    frontmatter_text = "\n".join(lines[1:end_index])
    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        frontmatter = {}

    # Return content without frontmatter
    remaining_content = "\n".join(lines[end_index + 1 :])
    return frontmatter, remaining_content


def extract_sections(content: str) -> list[Section]:
    """Extract H2 and H3 sections from markdown content.

    Uses adaptive strategy:
    - If H2 has H3 subsections, split by H3
    - If H2 has no H3 subsections, keep entire H2 as one section
    """
    sections: list[Section] = []
    lines = content.split("\n")

    current_h2: str | None = None
    current_h2_content: list[str] = []
    current_h3: str | None = None
    current_h3_content: list[str] = []
    h2_has_h3 = False

    for line in lines:
        # Check for H2 heading
        h2_match = re.match(r"^##\s+(.+)$", line)
        if h2_match:
            # Save previous H3 if exists
            if current_h3 and current_h2:
                sections.append(
                    Section(
                        heading=current_h3,
                        content="\n".join(current_h3_content).strip(),
                        level=3,
                        parent_heading=current_h2,
                    )
                )
                current_h3 = None
                current_h3_content = []

            # Save previous H2 if exists and has no H3
            if current_h2 and not h2_has_h3:
                sections.append(
                    Section(
                        heading=current_h2,
                        content="\n".join(current_h2_content).strip(),
                        level=2,
                    )
                )

            # Start new H2
            current_h2 = h2_match.group(1).strip()
            current_h2_content = [line]
            h2_has_h3 = False
            continue

        # Check for H3 heading
        h3_match = re.match(r"^###\s+(.+)$", line)
        if h3_match and current_h2:
            # Save previous H3 if exists
            if current_h3:
                sections.append(
                    Section(
                        heading=current_h3,
                        content="\n".join(current_h3_content).strip(),
                        level=3,
                        parent_heading=current_h2,
                    )
                )

            # Start new H3
            current_h3 = h3_match.group(1).strip()
            current_h3_content = [line]
            h2_has_h3 = True
            continue

        # Add line to current section
        if current_h3:
            current_h3_content.append(line)
        elif current_h2:
            current_h2_content.append(line)

    # Save final section
    if current_h3 and current_h2:
        sections.append(
            Section(
                heading=current_h3,
                content="\n".join(current_h3_content).strip(),
                level=3,
                parent_heading=current_h2,
            )
        )
    elif current_h2 and not h2_has_h3:
        sections.append(
            Section(
                heading=current_h2,
                content="\n".join(current_h2_content).strip(),
                level=2,
            )
        )

    return sections


def contains_code_block(content: str) -> bool:
    """Check if content contains a code block (```)."""
    return "```" in content


def contains_table(content: str) -> bool:
    """Check if content contains a markdown table (|...|)."""
    for line in content.split("\n"):
        if "|" in line and line.strip().startswith("|"):
            return True
    return False


def contains_procedural_list(content: str) -> bool:
    """Check if content contains a numbered list or checklist."""
    for line in content.split("\n"):
        stripped = line.strip()
        # Check for numbered list (1. 2. etc.)
        if re.match(r"^\d+\.\s+", stripped):
            return True
        # Check for checklist (- [ ] or - [x])
        if re.match(r"^-\s+\[[ x]\]\s+", stripped):
            return True
    return False


def split_at_paragraph_boundaries(content: str, max_size: int = 1500) -> list[str]:
    """Split content at paragraph boundaries (double newline).

    Args:
        content: Content to split
        max_size: Maximum size of each subchunk

    Returns:
        List of subchunks
    """
    paragraphs = content.split("\n\n")
    subchunks: list[str] = []
    current_chunk: list[str] = []
    current_size = 0

    for paragraph in paragraphs:
        para_size = len(paragraph)

        # If adding this paragraph exceeds max_size, save current chunk
        if current_size + para_size > max_size and current_chunk:
            subchunks.append("\n\n".join(current_chunk))
            current_chunk = [paragraph]
            current_size = para_size
        else:
            current_chunk.append(paragraph)
            current_size += para_size + 2  # +2 for \n\n

    # Add final chunk
    if current_chunk:
        subchunks.append("\n\n".join(current_chunk))

    return subchunks


def extract_category_from_path(doc_path: str) -> str:
    """Extract category from document path.

    Args:
        doc_path: Relative document path

    Returns:
        Category: operate, integrate, develop, or unknown
    """
    path_lower = doc_path.lower()
    if "operate/" in path_lower or "/operate/" in path_lower:
        return "operate"
    elif "integrate/" in path_lower or "/integrate/" in path_lower:
        return "integrate"
    elif "develop/" in path_lower or "/develop/" in path_lower:
        return "develop"
    else:
        return "unknown"


def extract_product_area_from_path(doc_path: str) -> str:
    """Extract product area from document path.

    Args:
        doc_path: Relative document path

    Returns:
        Product area: redis_software, redis_cloud, redis_stack, or redis_oss
    """
    path_lower = doc_path.lower()
    if "/rs/" in path_lower or "redis-enterprise" in path_lower or "/enterprise/" in path_lower:
        return "redis_software"
    elif "/rc/" in path_lower or "redis-cloud" in path_lower or "/cloud/" in path_lower:
        return "redis_cloud"
    elif "/stack/" in path_lower:
        return "redis_stack"
    else:
        return "redis_oss"


def construct_doc_url(doc_path: str) -> str:
    """Construct public URL from document path.

    Args:
        doc_path: Relative document path

    Returns:
        Public URL
    """
    # Remove 'content/' prefix if present
    path = doc_path
    if path.startswith("content/"):
        path = path[8:]

    # Remove .md extension
    if path.endswith(".md"):
        path = path[:-3]

    # Construct URL
    return f"https://redis.io/docs/latest/{path}/"


def construct_toc_path(doc_path: str, section_heading: str) -> str:
    """Construct table of contents path (breadcrumb).

    Args:
        doc_path: Relative document path
        section_heading: Section heading

    Returns:
        TOC path (breadcrumb navigation path)
    """
    # Extract path components
    path = doc_path
    if path.startswith("content/"):
        path = path[8:]
    if path.endswith(".md"):
        path = path[:-3]

    components = path.split("/")
    toc_parts = components + [section_heading]
    return " > ".join(toc_parts)


def construct_chunk_id(doc_path: str, chunk_index: int) -> str:
    """Construct unique chunk ID.

    Args:
        doc_path: Relative document path
        chunk_index: Chunk index

    Returns:
        Chunk ID (e.g., "operate_rs_aa_planning_001")
    """
    # Extract path components
    path = doc_path
    if path.startswith("content/"):
        path = path[8:]
    if path.endswith(".md"):
        path = path[:-3]

    # Replace slashes with underscores
    path_id = path.replace("/", "_").replace("-", "_")
    return f"{path_id}_{chunk_index:03d}"


def chunk_document(doc: Document) -> list[Chunk]:
    """Chunk a document using adaptive H2/H3 strategy.

    Args:
        doc: Document to chunk

    Returns:
        List of chunks with metadata
    """
    # Parse frontmatter
    frontmatter, content = parse_frontmatter(doc.content)

    # Extract metadata from frontmatter and path
    title = frontmatter.get("title") or doc.title or "Untitled"
    category = extract_category_from_path(doc.file_path)
    product_area = extract_product_area_from_path(doc.file_path)
    doc_url = construct_doc_url(doc.file_path)

    # Extract sections
    sections = extract_sections(content)

    # Create chunks
    chunks: list[Chunk] = []
    chunk_index = 0

    for section in sections:
        section_content = section.content
        section_heading = section.heading

        # Build TOC path
        if section.parent_heading:
            toc_path = construct_toc_path(
                doc.file_path, f"{section.parent_heading} > {section_heading}"
            )
        else:
            toc_path = construct_toc_path(doc.file_path, section_heading)

        # Check for code blocks, tables, or procedural lists
        has_code_block = contains_code_block(section_content)
        has_table = contains_table(section_content)
        has_procedural_list = contains_procedural_list(section_content)

        # Preserve code blocks, tables, and lists intact
        if has_code_block or has_table or has_procedural_list:
            chunk = Chunk(
                content=section_content,
                source=doc.source_repo,
                doc_path=doc.file_path,
                doc_url=doc_url,
                title=title,
                category=category,
                product_area=product_area,
                section_heading=section_heading,
                toc_path=toc_path,
                chunk_id=construct_chunk_id(doc.file_path, chunk_index),
                chunk_index=chunk_index,
                subchunk_index=0,
            )
            chunks.append(chunk)
            chunk_index += 1

        # Split long sections into subchunks
        elif len(section_content) > 2000:
            subchunks = split_at_paragraph_boundaries(section_content, max_size=1500)
            for subchunk_index, subchunk_content in enumerate(subchunks):
                chunk = Chunk(
                    content=subchunk_content,
                    source=doc.source_repo,
                    doc_path=doc.file_path,
                    doc_url=doc_url,
                    title=title,
                    category=category,
                    product_area=product_area,
                    section_heading=section_heading,
                    toc_path=toc_path,
                    chunk_id=construct_chunk_id(doc.file_path, chunk_index),
                    chunk_index=chunk_index,
                    subchunk_index=subchunk_index,
                )
                chunks.append(chunk)
            chunk_index += 1

        # Normal section (< 2000 chars)
        else:
            chunk = Chunk(
                content=section_content,
                source=doc.source_repo,
                doc_path=doc.file_path,
                doc_url=doc_url,
                title=title,
                category=category,
                product_area=product_area,
                section_heading=section_heading,
                toc_path=toc_path,
                chunk_id=construct_chunk_id(doc.file_path, chunk_index),
                chunk_index=chunk_index,
                subchunk_index=0,
            )
            chunks.append(chunk)
            chunk_index += 1

    return chunks
