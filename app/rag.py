from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.llm import get_llm
from app.vector_store import get_vector_store

SYSTEM_PROMPT = """You are the assistant for Hyderabad Central Parking.
Answer the customer's question using only the context below.
If the answer is not in the context, say you do not have that information.
Keep answers short and friendly.

Context:
{context}"""

prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{question}")]
)


@lru_cache(maxsize=1)
def _store():
    return get_vector_store()


@lru_cache(maxsize=1)
def _chain():
    return prompt | get_llm() | StrOutputParser()


def retrieve(question: str, k: int = 3):
    return _store().similarity_search(question, k=k)


def answer(question: str, k: int = 3) -> str:
    docs = retrieve(question, k=k)
    context = "\n\n".join(d.page_content for d in docs)
    return _chain().invoke({"context": context, "question": question})