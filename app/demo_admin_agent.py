import sys

from app.admin_agent import AdminAgent, decision_message


def main() -> None:
    agent = AdminAgent()

    if len(sys.argv) > 1:
        print(decision_message(agent.get_decision(sys.argv[1])))
        return

    result = agent.escalate(
        "Likhith", "Edupuganti", "TS09AB1234", "2026-12-02 09:00", "2026-12-02 13:00"
    )
    print(f"Request id: {result.request_id}")
    print(f"Note sent to the administrator: {result.note}")
    print(decision_message(result.record))


if __name__ == "__main__":
    main()