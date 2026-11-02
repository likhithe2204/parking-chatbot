from app.vector_store import get_vector_store

# Each question lists every document that holds the answer.
QUERIES = {
    "where is the parking located": {"location.md", "directions_and_transport.md"},
    "how do I book a space": {"booking_process.md", "reservation_rules.md"},
    "does it have EV charging": {"parking_details.md", "ev_charging.md", "zones_and_vehicles.md"},
}

store = get_vector_store()
failed = 0
for query, expected in QUERIES.items():
    results = store.similarity_search(query, k=3)
    sources = [d.metadata["source"] for d in results]
    ok = bool(expected & set(sources))
    failed += not ok
    print(f"{'PASS' if ok else 'FAIL'} | {query} -> {sources}")

raise SystemExit(1 if failed else 0)