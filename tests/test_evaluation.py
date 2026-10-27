import json

from app.config import ROOT, STATIC_DIR
from app.evaluation import (
    answer_matches,
    percentile,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    summarize_latency,
)

EVAL_DIR = ROOT / "data" / "eval"


def test_precision_at_k():
    retrieved = ["a.md", "b.md", "a.md"]
    assert precision_at_k(retrieved, {"a.md"}, 3) == 2 / 3
    assert precision_at_k(retrieved, {"a.md"}, 1) == 1.0


def test_recall_at_k():
    retrieved = ["a.md", "c.md", "b.md"]
    assert recall_at_k(retrieved, {"a.md", "b.md"}, 1) == 0.5
    assert recall_at_k(retrieved, {"a.md", "b.md"}, 3) == 1.0


def test_reciprocal_rank():
    assert reciprocal_rank(["x.md", "a.md"], {"a.md"}) == 0.5
    assert reciprocal_rank(["x.md", "y.md"], {"a.md"}) == 0.0


def test_percentile_nearest_rank():
    values = list(range(1, 11))
    assert percentile(values, 50) == 5
    assert percentile(values, 95) == 10


def test_summarize_latency():
    summary = summarize_latency([100.0, 200.0, 300.0])
    assert summary["n"] == 3
    assert summary["mean"] == 200.0
    assert summary["max"] == 300.0


def test_answer_matches_needs_every_group():
    groups = [["40"], ["300"]]
    assert answer_matches("INR 40 per hour, INR 300 per day", groups)
    assert not answer_matches("INR 40 per hour", groups)


def test_answer_matches_blocks_forbidden_text():
    assert not answer_matches("Call 98765 now, it is private", [["private"]], ["98765"])


def test_eval_files_reference_existing_sources():
    cases = json.loads((EVAL_DIR / "retrieval_eval.json").read_text(encoding="utf-8"))
    assert len(cases) >= 10
    for case in cases:
        for source in case["relevant"]:
            assert (STATIC_DIR / source).exists()


def test_answer_eval_cases_are_well_formed():
    cases = json.loads((EVAL_DIR / "answer_eval.json").read_text(encoding="utf-8"))
    assert len(cases) >= 5
    for case in cases:
        assert case["question"]
        assert case["expect_all"]