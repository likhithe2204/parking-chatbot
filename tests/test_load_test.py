from app import load_test
from app.reservation import PLATE_PATTERN


def test_generated_plates_are_valid_and_unique():
    plates = [load_test.plate(i) for i in range(300)]
    assert len(set(plates)) == 300
    assert all(PLATE_PATTERN.match(p) for p in plates)


def test_admin_confirmation_holds_up_under_concurrent_load():
    result = load_test.run_admin_load(count=12, workers=4)
    assert result["errors"] == 0
    assert result["consistent"] is True


def test_mcp_recording_writes_every_booking_exactly_once_under_load():
    result = load_test.run_mcp_load(count=12, workers=4)
    assert result["errors"] == 0
    assert result["consistent"] is True
    assert result["checks"]["lines written"] == "12 of 12"


def test_report_lists_every_component_and_the_integrity_verdict():
    latency = {"n": 3, "mean": 1.0, "p50": 1.0, "p95": 2.0, "max": 2.0}
    results = {
        load_test.ADMIN: {"operations": 3, "workers": 2, "errors": 0, "throughput": 9.5,
                          "latency": latency, "checks": {"stored": "3 of 3"}, "consistent": True},
        load_test.MCP: {"operations": 3, "workers": 2, "errors": 1, "throughput": 4.0,
                        "latency": latency, "checks": {}, "consistent": False},
    }
    report = load_test.render_report(results)
    assert load_test.ADMIN in report
    assert load_test.MCP in report
    assert "stored: 3 of 3" in report
    assert "INCONSISTENT" in report