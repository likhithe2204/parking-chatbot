from app import chat as chat_module


def test_loop_answers_then_exits(monkeypatch, capsys):
    inputs = iter(["hello", "", "exit"])
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
    monkeypatch.setattr(chat_module, "build_agent", lambda: object())
    monkeypatch.setattr(
        chat_module, "chat", lambda agent, message, thread_id: f"echo {message}"
    )
    chat_module.main()
    assert "Bot: echo hello" in capsys.readouterr().out


def test_exit_stops_without_calling_the_agent(monkeypatch):
    calls = []
    monkeypatch.setattr("builtins.input", lambda _="": "exit")
    monkeypatch.setattr(chat_module, "build_agent", lambda: object())
    monkeypatch.setattr(chat_module, "chat", lambda *args, **kwargs: calls.append(1))
    chat_module.main()
    assert calls == []