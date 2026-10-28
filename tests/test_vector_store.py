from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from app import vector_store


def _use_fake_embeddings(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_store, "CHROMA_DIR", tmp_path)
    monkeypatch.setattr(
        vector_store, "get_embeddings", lambda: DeterministicFakeEmbedding(size=32)
    )


def test_store_returns_added_documents(monkeypatch, tmp_path):
    _use_fake_embeddings(monkeypatch, tmp_path)
    store = vector_store.get_vector_store()
    store.add_documents(
        [Document(page_content="Zone C has EV charging", metadata={"source": "a.md"})]
    )
    results = store.similarity_search("EV charging", k=1)
    assert results[0].metadata["source"] == "a.md"


def test_store_persists_between_instances(monkeypatch, tmp_path):
    _use_fake_embeddings(monkeypatch, tmp_path)
    first = vector_store.get_vector_store()
    first.add_documents(
        [Document(page_content="Booking needs approval", metadata={"source": "b.md"})]
    )
    second = vector_store.get_vector_store()
    assert len(second.similarity_search("approval", k=1)) == 1