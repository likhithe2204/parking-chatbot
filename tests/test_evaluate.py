from app.evaluate import render_report

LATENCY = {"n": 13, "mean": 8.0, "p50": 8.0, "p95": 10.0, "max": 10.0}

RETRIEVAL = {
    "count": 13,
    "metrics": {
        "precision@1": 0.9,
        "precision@2": 0.6,
        "precision@3": 0.4,
        "recall@1": 0.8,
        "recall@2": 0.9,
        "recall@3": 1.0,
        "hit@1": 0.9,
        "hit@2": 1.0,
        "hit@3": 1.0,
        "mrr": 0.95,
    },
    "latency": LATENCY,
    "misses": [],
}
COMPONENTS = {"SQL lookup tools": LATENCY}
AGENT = {"passed": 16, "total": 16, "latency": LATENCY, "failures": []}


def test_report_has_retrieval_and_latency_sections():
    report = render_report(RETRIEVAL, COMPONENTS, None)
    assert "## Retrieval quality" in report
    assert "## Latency (milliseconds)" in report
    assert "## Answer accuracy" not in report


def test_report_includes_agent_results_when_given():
    report = render_report(RETRIEVAL, COMPONENTS, AGENT)
    assert "Passed 16 of 16 runs (100%)" in report
    assert report.count("## Retrieval quality") == 1


def test_report_shows_hit_at_k_and_explains_it():
    report = render_report(RETRIEVAL, COMPONENTS, None)
    assert "| K | Precision@K | Recall@K | Hit@K |" in report
    assert "Hit@K asks the practical question" in report
    assert "Every question found at least one relevant document" in report


def test_report_lists_questions_with_no_relevant_document():
    miss = "Where is it? -> got ['a.md'], wanted one of ['b.md']"
    report = render_report({**RETRIEVAL, "misses": [miss]}, COMPONENTS, None)
    assert "no relevant document was found in the top 3" in report
    assert miss in report