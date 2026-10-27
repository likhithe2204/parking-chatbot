import argparse
import json
import os
import statistics
import time
from datetime import datetime

from dotenv import load_dotenv

from app.config import CHUNK_OVERLAP, CHUNK_SIZE, EMBEDDING_MODEL, ROOT
from app.evaluation import (
    answer_matches,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    summarize_latency,
)
from app.guardrails import check_input
from app.rag import retrieve
from app.tools import format_availability, format_prices, format_working_hours

load_dotenv()

EVAL_DIR = ROOT / "data" / "eval"
REPORT_PATH = ROOT / "docs" / "evaluation_report.md"
KS = (1, 2, 3)
REPEATS = 2
LOOPS = 20


def _load(name: str) -> list[dict]:
    return json.loads((EVAL_DIR / name).read_text(encoding="utf-8"))


def _time_ms(fn, *args):
    start = time.perf_counter()
    result = fn(*args)
    return result, (time.perf_counter() - start) * 1000


def evaluate_retrieval() -> dict:
    cases = _load("retrieval_eval.json")
    retrieve("warm up", k=1)

    metrics = {f"{name}@{k}": [] for name in ("precision", "recall") for k in KS}
    ranks, latencies, misses = [], [], []

    for case in cases:
        docs, ms = _time_ms(retrieve, case["question"], max(KS))
        latencies.append(ms)
        sources = [d.metadata["source"] for d in docs]
        relevant = set(case["relevant"])

        for k in KS:
            metrics[f"precision@{k}"].append(precision_at_k(sources, relevant, k))
            metrics[f"recall@{k}"].append(recall_at_k(sources, relevant, k))
        ranks.append(reciprocal_rank(sources, relevant))

        if recall_at_k(sources, relevant, max(KS)) < 1:
            misses.append(
                f"{case['question']} -> got {sources}, wanted {sorted(relevant)}"
            )

    summary = {name: statistics.mean(values) for name, values in metrics.items()}
    summary["mrr"] = statistics.mean(ranks)
    return {
        "count": len(cases),
        "metrics": summary,
        "latency": summarize_latency(latencies),
        "misses": misses,
    }


def evaluate_components() -> dict:
    samples = [
        "My email is test.user@example.com, where is the parking?",
        "What are your prices for a car?",
    ]
    check_input(samples[0])

    guard = [_time_ms(check_input, s)[1] for _ in range(LOOPS) for s in samples]
    sql_calls = (
        (format_availability, "Zone A"),
        (format_prices, "car"),
        (format_working_hours, "Monday"),
    )
    sql = [_time_ms(fn, arg)[1] for _ in range(LOOPS) for fn, arg in sql_calls]
    return {
        "Input guardrail (Presidio)": summarize_latency(guard),
        "SQL lookup tools": summarize_latency(sql),
    }


def evaluate_agent() -> dict:
    from app.agent import build_agent, chat

    cases = _load("answer_eval.json")
    agent = build_agent()
    chat(agent, "Hello", "eval-warmup")

    latencies, failures = [], []
    passed = total = 0
    for i, case in enumerate(cases):
        for rep in range(REPEATS):
            reply, ms = _time_ms(chat, agent, case["question"], f"eval-{i}-{rep}")
            latencies.append(ms)
            total += 1
            if answer_matches(reply, case["expect_all"], case.get("must_not", [])):
                passed += 1
            else:
                failures.append(f"{case['question']} -> {reply[:120]!r}")

    return {
        "passed": passed,
        "total": total,
        "latency": summarize_latency(latencies),
        "failures": failures,
    }


def _latency_row(name: str, stats: dict) -> str:
    return (
        f"| {name} | {stats['n']} | {stats['mean']} | "
        f"{stats['p50']} | {stats['p95']} | {stats['max']} |"
    )


def render_report(retrieval: dict, components: dict, agent: dict | None) -> str:
    m = retrieval["metrics"]
    lines = [
        "# Evaluation Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Configuration",
        "",
        f"- Embedding model: {EMBEDDING_MODEL}",
        f"- Chunk size / overlap: {CHUNK_SIZE} / {CHUNK_OVERLAP}",
        f"- LLM deployment: {os.environ.get('DIAL_DEPLOYMENT', 'n/a')}",
        f"- Retrieval questions: {retrieval['count']}",
        "",
        "## Retrieval quality",
        "",
        "| K | Precision@K | Recall@K |",
        "|---|---|---|",
    ]
    for k in KS:
        lines.append(f"| {k} | {m[f'precision@{k}']:.2f} | {m[f'recall@{k}']:.2f} |")
    lines += [
        "",
        f"MRR: {m['mrr']:.2f}",
        "",
        "Precision counts chunks, Recall counts source documents. The knowledge base is",
        "small (a few chunks per document), so Precision@K is naturally lower than Recall@K.",
        "",
    ]
    if retrieval["misses"]:
        lines += ["Questions where Recall@3 was below 1.0:", ""]
        lines += [f"- {miss}" for miss in retrieval["misses"]]
        lines.append("")

    if agent:
        lines += [
            "## Answer accuracy (end to end)",
            "",
            f"Passed {agent['passed']} of {agent['total']} runs "
            f"({agent['passed'] / agent['total']:.0%}).",
            "",
        ]
        if agent["failures"]:
            lines += [f"- {failure}" for failure in agent["failures"]]
            lines.append("")

    lines += [
        "## Latency (milliseconds)",
        "",
        "| Component | Runs | Mean | p50 | p95 | Max |",
        "|---|---|---|---|---|---|",
        _latency_row("Retrieval (embedding + Chroma)", retrieval["latency"]),
    ]
    for name, stats in components.items():
        lines.append(_latency_row(name, stats))
    if agent:
        lines.append(_latency_row("Full chatbot reply (guardrails + agent + LLM)", agent["latency"]))
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-llm", action="store_true", help="skip the LLM based checks")
    args = parser.parse_args()

    print("Running retrieval evaluation...")
    retrieval = evaluate_retrieval()
    print("Measuring component latency...")
    components = evaluate_components()
    agent = None
    if not args.skip_llm:
        print("Running end to end answer checks (needs VPN)...")
        agent = evaluate_agent()

    report = render_report(retrieval, components, agent)
    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print("\n" + report)
    print(f"Report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()