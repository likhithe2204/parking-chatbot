from app.agent import build_agent, chat


def main() -> None:
    agent = build_agent()
    print("Hyderabad Central Parking assistant. Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        print(f"Bot: {chat(agent, user_input, thread_id='session-1')}\n")


if __name__ == "__main__":
    main()