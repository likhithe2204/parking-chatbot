import time

from app import chat as chat_module


class FakeWorkflow:
    def __init__(self, fail=False, saved=0, updates=None, reconcile_error=None):
        self.fail = fail
        self.saved = saved
        self.updates = updates or []
        self.reconcile_error = reconcile_error
        self.sent = []

    def reconcile(self):
        if self.reconcile_error:
            raise self.reconcile_error
        return self.saved

    def poll(self):
        updates, self.updates = self.updates, []
        return updates

    def send(self, session, message):
        if self.fail:
            raise RuntimeError("boom")
        self.sent.append((session, message))
        return f"echo {message}"


def run(monkeypatch, inputs, workflow, pause=0.0):
    feed = iter(inputs)

    def fake_input(_prompt=""):
        time.sleep(pause)
        return next(feed)

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(chat_module, "create_workflow", lambda: workflow)
    chat_module.main()


def test_loop_answers_skips_empty_lines_and_exits(monkeypatch, capsys):
    workflow = FakeWorkflow()
    run(monkeypatch, ["hello", "", "exit"], workflow)
    assert workflow.sent == [("session-1", "hello")]
    assert "Bot: echo hello" in capsys.readouterr().out


def test_exit_stops_without_calling_the_workflow(monkeypatch):
    workflow = FakeWorkflow()
    run(monkeypatch, ["exit"], workflow)
    assert workflow.sent == []


def test_a_failure_gives_a_friendly_reply(monkeypatch, capsys):
    run(monkeypatch, ["hello", "exit"], FakeWorkflow(fail=True))
    output = capsys.readouterr().out
    assert "something went wrong" in output
    assert "boom" not in output


def test_decisions_are_announced_without_the_customer_asking(monkeypatch, capsys):
    monkeypatch.setattr(chat_module, "POLL_SECONDS", 0.01)
    workflow = FakeWorkflow(updates=[("session-1", "Good news: approved.")])
    run(monkeypatch, ["exit"], workflow, pause=0.3)
    assert "[Update] Good news: approved." in capsys.readouterr().out


def test_bookings_waiting_from_earlier_are_saved_at_startup(monkeypatch, capsys):
    run(monkeypatch, ["exit"], FakeWorkflow(saved=2))
    assert "Saved 2 approved booking(s)" in capsys.readouterr().out


def test_a_failed_startup_check_does_not_stop_the_chat(monkeypatch, capsys):
    workflow = FakeWorkflow(reconcile_error=RuntimeError("down"))
    run(monkeypatch, ["hello", "exit"], workflow)
    output = capsys.readouterr().out
    assert "could not check earlier bookings" in output
    assert "Bot: echo hello" in output