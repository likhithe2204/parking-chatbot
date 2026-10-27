from app.rag import answer

QUESTIONS = [
    "Where is the parking located?",
    "How many zones are there and which one has EV charging?",
    "How do I make a reservation?",
    "What is the weather in Hyderabad today?",
]

for q in QUESTIONS:
    print(f"Q: {q}")
    print(f"A: {answer(q)}\n")