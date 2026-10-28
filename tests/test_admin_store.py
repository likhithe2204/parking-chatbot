import pytest

from app import admin_store as store

DEFAULTS = dict(
    first_name="Likhith",
    last_name="Edupuganti",
    car_number="TS09AB1234",
    start="2099-01-01 10:00",
    end="2099-01-01 12:00",
    note="Zone B has space",
)


@pytest.fixture
def db(tmp_path):
    return tmp_path / "admin.db"


def make(db, **overrides):
    return store.create_request(db_path=db, **{**DEFAULTS, **overrides})


def test_new_request_is_pending_with_an_id(db):
    record = make(db)
    assert record["id"].startswith("RES-")
    assert record["status"] == "PENDING"
    assert record["start"] == "2099-01-01 10:00"


def test_get_request_ignores_case(db):
    record = make(db)
    assert store.get_request(record["id"].lower(), db)["id"] == record["id"]


def test_get_unknown_request_returns_none(db):
    assert store.get_request("RES-NOPE00", db) is None


def test_list_filters_by_status(db):
    first = make(db)
    make(db, car_number="TS10CD5678")
    store.decide(first["id"], "APPROVED", db_path=db)
    assert len(store.list_requests(db_path=db)) == 2
    assert len(store.list_requests("PENDING", db)) == 1


def test_list_rejects_unknown_status(db):
    with pytest.raises(ValueError):
        store.list_requests("MAYBE", db)


def test_approval_is_recorded(db):
    record = make(db)
    decided = store.decide(record["id"], "APPROVED", "all good", db)
    assert decided["status"] == "APPROVED"
    assert decided["reason"] == "all good"
    assert decided["decided_at"] is not None


def test_request_cannot_be_decided_twice(db):
    record = make(db)
    store.decide(record["id"], "APPROVED", db_path=db)
    with pytest.raises(store.AlreadyDecided):
        store.decide(record["id"], "REFUSED", db_path=db)


def test_deciding_unknown_request_fails(db):
    with pytest.raises(store.RequestNotFound):
        store.decide("RES-NOPE00", "APPROVED", db_path=db)