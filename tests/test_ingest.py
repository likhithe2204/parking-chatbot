from langchain_core.documents import Document

from app.config import CHUNK_SIZE, STATIC_DIR
from app.ingest import load_documents, split_documents


def test_load_documents_reads_every_markdown_file():
    docs = load_documents()
    assert len(docs) == len(list(STATIC_DIR.glob("*.md")))
    assert all(d.metadata["source"].endswith(".md") for d in docs)


def test_loaded_documents_are_not_empty():
    assert all(d.page_content.strip() for d in load_documents())


def test_split_documents_respects_chunk_size_and_keeps_source():
    long_doc = Document(
        page_content="Parking is available. " * 100, metadata={"source": "x.md"}
    )
    chunks = split_documents([long_doc])
    assert len(chunks) > 1
    assert all(len(c.page_content) <= CHUNK_SIZE for c in chunks)
    assert all(c.metadata["source"] == "x.md" for c in chunks)