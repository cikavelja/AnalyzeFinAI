"""Tests for app/chunking/chunker.py"""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.chunking.chunker import DEFAULT_CHUNK_SIZE, chunk_text
from app.models.document import DocumentChunk

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def doc_id():
    return uuid4()


@pytest.fixture
def short_text() -> str:
    return "Hello, world!"


@pytest.fixture
def long_text() -> str:
    # 5000 chars > DEFAULT_CHUNK_SIZE (2000)
    return "A" * 5000


# ---------------------------------------------------------------------------
# Success paths
# ---------------------------------------------------------------------------

def test_chunker_short_text_returns_single_chunk(doc_id, short_text: str) -> None:
    chunks = chunk_text(short_text, doc_id)
    assert len(chunks) == 1
    assert chunks[0].text == short_text


def test_chunker_returns_document_chunks(doc_id, short_text: str) -> None:
    chunks = chunk_text(short_text, doc_id)
    assert all(isinstance(c, DocumentChunk) for c in chunks)


def test_chunker_document_id_set(doc_id, short_text: str) -> None:
    chunks = chunk_text(short_text, doc_id)
    assert all(c.document_id == doc_id for c in chunks)


def test_chunker_long_text_produces_multiple_chunks(doc_id, long_text: str) -> None:
    chunks = chunk_text(long_text, doc_id)
    assert len(chunks) > 1


def test_chunker_chunks_indexed_sequentially(doc_id, long_text: str) -> None:
    chunks = chunk_text(long_text, doc_id)
    indices = [c.index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunker_chunk_size_respected(doc_id) -> None:
    text = "B" * 6000
    chunks = chunk_text(text, doc_id, chunk_size=1000, overlap=0)
    assert all(len(c.text) <= 1000 for c in chunks)


def test_chunker_overlap_creates_context_continuity(doc_id) -> None:
    text = "X" * 3000
    chunks = chunk_text(text, doc_id, chunk_size=1000, overlap=200)
    # The start of chunk 1 should contain chars from the end of chunk 0
    if len(chunks) > 1:
        assert chunks[1].text[:200] == chunks[0].text[-200:]


def test_chunker_word_count_populated(doc_id, short_text: str) -> None:
    chunks = chunk_text(short_text, doc_id)
    assert chunks[0].word_count is not None
    assert chunks[0].word_count >= 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_chunker_empty_string_returns_one_empty_chunk(doc_id) -> None:
    chunks = chunk_text("", doc_id)
    assert len(chunks) == 1
    assert chunks[0].text == ""


def test_chunker_whitespace_only_returns_one_empty_chunk(doc_id) -> None:
    chunks = chunk_text("   ", doc_id)
    assert len(chunks) == 1


def test_chunker_exact_chunk_size_text_returns_one_chunk(doc_id) -> None:
    text = "C" * DEFAULT_CHUNK_SIZE
    chunks = chunk_text(text, doc_id)
    assert len(chunks) == 1
