from app.messages import RECORDING_NOTES, decision_message, status_message

APPROVED = {"id": "RES-AAAAAA", "status": "APPROVED", "reason": "see you then"}
REFUSED = {"id": "RES-AAAAAA", "status": "REFUSED", "reason": "zone full"}


def test_pending_message():
    assert "still waiting" in decision_message({"id": "RES-AAAAAA", "status": "PENDING"})


def test_approval_includes_the_reason():
    text = decision_message(APPROVED)
    assert "approved" in text
    assert "see you then" in text


def test_a_refusal_is_never_worded_as_an_approval():
    text = decision_message(REFUSED)
    assert "refused" in text
    assert "approved" not in text


def test_status_message_adds_the_saving_outcome():
    assert RECORDING_NOTES["RECORDED"].strip() in status_message(APPROVED, "RECORDED")
    assert "could not be saved" in status_message(APPROVED, "RECORD_FAILED")
    assert status_message(REFUSED, "NOT_APPROVED") == decision_message(REFUSED)

def test_a_booking_without_a_free_space_is_explained():
    text = status_message(APPROVED, "NO_SPACE")
    assert "no space is free" in text
    assert "not saved" in text