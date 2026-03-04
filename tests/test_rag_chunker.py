"""Tests for RAG chunker."""

from redis_agent_control_plane.rag.chunker import (
    Chunk,
    chunk_document,
    construct_chunk_id,
    construct_doc_url,
    construct_toc_path,
    contains_code_block,
    contains_procedural_list,
    contains_table,
    extract_category_from_path,
    extract_product_area_from_path,
    extract_sections,
    parse_frontmatter,
    split_at_paragraph_boundaries,
)
from redis_agent_control_plane.rag.ingest import Document


def test_parse_frontmatter():
    """Test frontmatter parsing."""
    content = """---
title: Test Document
description: A test document
categories:
  - operate
  - redis-enterprise
---

# Test Document

This is the content.
"""
    frontmatter, remaining = parse_frontmatter(content)

    assert frontmatter["title"] == "Test Document"
    assert frontmatter["description"] == "A test document"
    assert "categories" in frontmatter
    assert "# Test Document" in remaining
    assert "---" not in remaining


def test_parse_frontmatter_no_frontmatter():
    """Test parsing content without frontmatter."""
    content = "# Test Document\n\nThis is the content."
    frontmatter, remaining = parse_frontmatter(content)

    assert frontmatter == {}
    assert remaining == content


def test_extract_sections_h2_only():
    """Test extracting H2 sections without H3."""
    content = """## Section 1

Content for section 1.

## Section 2

Content for section 2.
"""
    sections = extract_sections(content)

    assert len(sections) == 2
    assert sections[0].heading == "Section 1"
    assert sections[0].level == 2
    assert "Content for section 1" in sections[0].content
    assert sections[1].heading == "Section 2"
    assert sections[1].level == 2


def test_extract_sections_h2_with_h3():
    """Test extracting H2 sections with H3 subsections."""
    content = """## Section 1

Intro content.

### Subsection 1.1

Content for subsection 1.1.

### Subsection 1.2

Content for subsection 1.2.

## Section 2

Content for section 2.
"""
    sections = extract_sections(content)

    # Should have 3 sections: 2 H3s from Section 1, and 1 H2 from Section 2
    assert len(sections) == 3
    assert sections[0].heading == "Subsection 1.1"
    assert sections[0].level == 3
    assert sections[0].parent_heading == "Section 1"
    assert sections[1].heading == "Subsection 1.2"
    assert sections[1].level == 3
    assert sections[1].parent_heading == "Section 1"
    assert sections[2].heading == "Section 2"
    assert sections[2].level == 2


def test_contains_code_block():
    """Test code block detection."""
    assert contains_code_block("```python\nprint('hello')\n```")
    assert not contains_code_block("No code here")


def test_contains_table():
    """Test table detection."""
    assert contains_table("| col1 | col2 |\n|------|------|\n| a | b |")
    assert not contains_table("No table here")


def test_contains_procedural_list():
    """Test procedural list detection."""
    assert contains_procedural_list("1. First step\n2. Second step")
    assert contains_procedural_list("- [ ] Task 1\n- [x] Task 2")
    assert not contains_procedural_list("- Regular list item")


def test_split_at_paragraph_boundaries():
    """Test splitting at paragraph boundaries."""
    content = "Para 1.\n\nPara 2.\n\nPara 3.\n\nPara 4."
    subchunks = split_at_paragraph_boundaries(content, max_size=20)

    assert len(subchunks) > 1
    for subchunk in subchunks:
        assert len(subchunk) <= 30  # Allow some margin


def test_extract_category_from_path():
    """Test category extraction from path."""
    assert extract_category_from_path("content/operate/rs/databases.md") == "operate"
    assert extract_category_from_path("content/integrate/redis-om.md") == "integrate"
    assert extract_category_from_path("content/develop/python.md") == "develop"
    assert extract_category_from_path("other/path.md") == "unknown"


def test_extract_product_area_from_path():
    """Test product area extraction from path."""
    assert extract_product_area_from_path("content/operate/rs/databases.md") == "redis_software"
    assert extract_product_area_from_path("content/operate/rc/databases.md") == "redis_cloud"
    assert extract_product_area_from_path("content/operate/stack/search.md") == "redis_stack"
    assert extract_product_area_from_path("content/operate/oss/commands.md") == "redis_oss"


def test_construct_doc_url():
    """Test doc URL construction."""
    url = construct_doc_url("content/operate/rs/databases/active-active.md")
    assert url == "https://redis.io/docs/latest/operate/rs/databases/active-active/"


def test_construct_toc_path():
    """Test TOC path construction."""
    toc = construct_toc_path("content/operate/rs/databases/active-active.md", "Planning")
    assert "operate" in toc
    assert "rs" in toc
    assert "databases" in toc
    assert "active-active" in toc
    assert "Planning" in toc


def test_construct_chunk_id():
    """Test chunk ID construction."""
    chunk_id = construct_chunk_id("content/operate/rs/databases/active-active.md", 5)
    assert "operate" in chunk_id
    assert "005" in chunk_id


def test_chunk_document():
    """Test document chunking."""
    doc = Document(
        file_path="content/operate/rs/databases.md",
        title="Databases",
        content="""---
title: Databases
---

## Overview

This is an overview.

## Configuration

This is configuration info.
""",
        source_repo="redis/docs",
    )

    chunks = chunk_document(doc)

    assert len(chunks) > 0
    assert all(isinstance(chunk, Chunk) for chunk in chunks)
    assert chunks[0].title == "Databases"
    assert chunks[0].category == "operate"
    assert chunks[0].product_area == "redis_software"
