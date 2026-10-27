from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHUNK_OVERLAP, CHUNK_SIZE, STATIC_DIR
from app.vector_store import get_vector_store


def load_documents() -> list[Document]:
    docs = []
    for path in sorted(STATIC_DIR.glob("*.md")):
        docs.append(
            Document(
                page_content=path.read_text(encoding="utf-8"),
                metadata={"source": path.name},
            )
        )
    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(docs)


def ingest() -> int:
    docs = load_documents()
    chunks = split_documents(docs)

    store = get_vector_store()
    store.reset_collection()
    store.add_documents(chunks)

    print(f"Loaded {len(docs)} documents")
    print(f"Created {len(chunks)} chunks")
    print("Stored in Chroma collection 'parking_static'")
    return len(chunks)


if __name__ == "__main__":
    ingest()