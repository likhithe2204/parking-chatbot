from app.vector_store import get_vector_store

QUERIES = {
    "where is the parking located": "location.md",
    "how do I book a space": "booking_process.md",
    "does it have EV charging": "parking_details.md",
}

store = get_vector_store()
for query, expected in QUERIES.items():
    results = store.similarity_search(query, k=3)
    sources = [d.metadata["source"] for d in results]
    status = "PASS" if expected in sources else "FAIL"
    print(f"{status} | {query} -> {sources}")