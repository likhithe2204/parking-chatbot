from langchain_core.documents import Document

from app import rag


class FakeStore:
    def similarity_search(self, question, k=3):
        return [
            Document(page_content=f"card {i}", metadata={"source": "a.md"})
            for i in range(k)
        ]


def test_retrieve_returns_k_documents(monkeypatch):
    monkeypatch.setattr(rag, "_store", lambda: FakeStore())
    assert len(rag.retrieve("where", k=2)) == 2


def test_answer_sends_retrieved_context_to_the_chain(monkeypatch):
    captured = {}

    class FakeChain:
        def invoke(self, payload):
            captured.update(payload)
            return "fake answer"

    monkeypatch.setattr(rag, "_store", lambda: FakeStore())
    monkeypatch.setattr(rag, "_chain", lambda: FakeChain())

    assert rag.answer("where is it?") == "fake answer"
    assert "card 0" in captured["context"]
    assert captured["question"] == "where is it?"


def test_prompt_needs_context_and_question():
    assert set(rag.prompt.input_variables) == {"context", "question"}