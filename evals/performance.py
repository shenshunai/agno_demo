"""
Performance Baseline Runner
=============================

Measures latency per entity and compares against saved baselines.
Baselines are established from actual runs, not hardcoded.

Usage:
    python -m evals perf                           # Compare against baselines
    python -m evals perf --update-baselines         # Establish baselines
    python -m evals perf --entity knowledge         # Single entity
    python -m evals perf --iterations 5             # More samples
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from evals.cases.smoke import all_smoke_tests
from evals.client import AgentOSClient
from evals.registry import ENTITIES

BASELINES_FILE = Path(__file__).parent / ".results" / "perf_baselines.json"

# Default regression threshold: fail if p95 exceeds baseline by this factor
REGRESSION_FACTOR = 1.5


def _load_baselines() -> dict[str, float]:
    """Load saved baselines. Returns empty dict if none exist."""
    if not BASELINES_FILE.exists():
        return {}
    try:
        return json.loads(BASELINES_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_baselines(baselines: dict[str, float]) -> Path:
    """Save baselines to disk."""
    BASELINES_FILE.parent.mkdir(parents=True, exist_ok=True)
    BASELINES_FILE.write_text(json.dumps(baselines, indent=2))
    return BASELINES_FILE


def _get_default_prompt(entity_id: str) -> str:
    """Get the first non-security smoke test prompt for an entity."""
    for t in all_smoke_tests():
        if t.entity_id == entity_id and t.group not in ("security", "graceful"):
            return t.prompt
    return f"Hello, test for {entity_id}"


def run_performance_tests(
    client: AgentOSClient,
    entity: str | None = None,
    iterations: int = 3,
    update_baselines: bool = False,
) -> list[dict]:
    """Run performance tests across entities.

    Returns list of result dicts with keys:
        entity_id, avg, p50, p95, max, baseline, status, reason
    """
    baselines = _load_baselines()

    entity_ids = [entity] if entity else list(ENTITIES.keys())
    entity_ids = [eid for eid in entity_ids if eid in ENTITIES]

    if not entity_ids:
        print(f"No entities found (entity={entity})")
        return []

    print(f"\n=== perf ({len(entity_ids)} entities, {iterations} iterations each) ===\n")

    results: list[dict] = []
    new_baselines: dict[str, float] = {}

    for i, entity_id in enumerate(entity_ids, 1):
        e = ENTITIES[entity_id]
        prompt = _get_default_prompt(entity_id)

        print(f"  [{i}/{len(entity_ids)}] {entity_id} ({e.type})...")

        timings: list[float] = []
        for _ in range(iterations):
            run_result = client.run(e.type, entity_id, prompt)
            if not run_result.error:
                timings.append(run_result.duration)

        if not timings:
            result: dict = {
                "entity_id": entity_id,
                "status": "ERROR",
                "reason": "all iterations failed",
                "duration": 0.0,
            }
            results.append(result)
            print("         ERROR — all iterations failed")
            continue

        avg = round(statistics.mean(timings), 2)
        p50 = round(statistics.median(timings), 2)
        p95 = round(sorted(timings)[min(len(timings) - 1, int(len(timings) * 0.95))], 2)
        max_t = round(max(timings), 2)

        baseline = baselines.get(entity_id)
        new_baselines[entity_id] = p95

        # Determine pass/fail
        if baseline is not None:
            passed = p95 <= baseline * REGRESSION_FACTOR
            status = "PASS" if passed else "FAIL"
        else:
            status = "PASS"  # No baseline — can't fail

        result = {
            "entity_id": entity_id,
            "avg": avg,
            "p50": p50,
            "p95": p95,
            "max": max_t,
            "iterations": len(timings),
            "baseline": baseline,
            "status": status,
            "duration": avg,
        }
        if status == "FAIL":
            result["reason"] = f"p95 {p95}s > {baseline}s * {REGRESSION_FACTOR}"

        results.append(result)

        baseline_str = f" (baseline: {baseline}s)" if baseline else " (no baseline)"
        icon = {"PASS": "PASS", "FAIL": "FAIL"}.get(status, "??? ")
        print(f"         {icon}  avg={avg}s  p50={p50}s  p95={p95}s  max={max_t}s{baseline_str}")

    # Summary
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    failed_count = sum(1 for r in results if r["status"] == "FAIL")
    error_count = sum(1 for r in results if r["status"] == "ERROR")

    print(f"\n{'=' * 50}")
    print(f"Results: {passed_count} passed, {failed_count} failed, {error_count} errors")
    print(f"{'=' * 50}")

    if update_baselines:
        path = _save_baselines(new_baselines)
        print(f"\nBaselines saved to {path} ({len(new_baselines)} entities)")

    return results
