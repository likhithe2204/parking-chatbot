import math


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    top = retrieved[:k]
    if not top:
        return 0.0
    return sum(source in relevant for source in top) / len(top)


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for position, source in enumerate(retrieved, start=1):
        if source in relevant:
            return 1 / position
    return 0.0


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


def summarize_latency(values_ms: list[float]) -> dict:
    if not values_ms:
        return {"n": 0, "mean": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0}
    return {
        "n": len(values_ms),
        "mean": round(sum(values_ms) / len(values_ms), 1),
        "p50": round(percentile(values_ms, 50), 1),
        "p95": round(percentile(values_ms, 95), 1),
        "max": round(max(values_ms), 1),
    }


def answer_matches(
    answer: str, expect_all: list[list[str]], must_not: list[str] | None = None
) -> bool:
    text = answer.lower().replace("\u2019", "'")
    has_all = all(any(option.lower() in text for option in group) for group in expect_all)
    has_forbidden = any(bad.lower() in text for bad in (must_not or []))
    return has_all and not has_forbidden