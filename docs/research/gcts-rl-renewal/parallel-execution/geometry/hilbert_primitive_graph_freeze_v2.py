"""Freeze compatibility-only kernel repair and added synthetic diagnostic controls."""
import ast
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(65536), b""):
            h.update(data)
    return {"path": str(path.relative_to(ROOT)), "sha256": h.hexdigest(), "bytes": path.stat().st_size}


def main():
    start = time.perf_counter()
    destination = HERE / "plan-v2.json"
    if destination.exists():
        raise ValueError("immutable repair plan exists")
    original = json.loads((HERE / "plan-v1.json").read_text())
    lifetime = json.loads((HERE / "fixtures-lifetime-v1.json").read_text())
    assert lifetime["status"] == "unknown_or_failed" and lifetime["supervisor_wait_reaped"] is True
    previous = original["preserved_files"] + original["sources"] + original["inputs"]
    evidence = [pin(p) for p in sorted(HERE.iterdir()) if (p.name.endswith("-v1.json")
                or p.name.endswith("-v1.txt"))]
    previous += evidence
    preserved = {}
    for p in previous:
        actual = pin(ROOT / p["path"])
        assert actual == {k: p[k] for k in ("path", "sha256", "bytes")}
        if p["path"] in preserved:
            assert preserved[p["path"]] == actual
        preserved[p["path"]] = actual
    sources = sorted(HERE.glob("hilbert_primitive_graph*_v2.py"))
    for path in sources:
        ast.parse(path.read_text(), filename=str(path))
    plan = {**original, "version": "hilbert-complete-implicit-primitive-point-kernel-v2-compatibility-repair",
            "status": "frozen_repair_before_one_reviewed_synthetic_retry",
            "sources": [pin(p) for p in sources],
            "preserved_files": [preserved[k] for k in sorted(preserved)],
            "prior_v1_plan_pin": pin(HERE / "plan-v1.json"), "prior_v1_evidence": evidence,
            "repair": {"kernel_semantics": "No change: replace int.bit_count with exact nonnegative bin(mask).count('1'). Full recipe language, t/m, factors, domains, scheduler, rollback, fallback and identities unchanged.",
                       "fixture_additions": ["exhaustive 256 small population-count masks versus bitwise sum",
                                              "invalid-advice rejection increments existing metric and retains complete fallback"],
                       "versioning": "new kernel/fixture/supervisor/outer/freezer sources and v2 output names; all v1 bytes preserved",
                       "diff_pins": [pin(p) for p in sorted(HERE.glob("*-v2-diff.txt"))] +
                                    [pin(p) for p in sorted(HERE.glob("*_v2-diff.txt"))]},
            "resource_accounting": {"failed_v1_status": "unknown_or_failed_runtime_compatibility_before_fixture_receipt",
                "failed_v1_seconds": lifetime["full_supervisor_process_seconds_including_receipt_write"],
                "conservative_rounded_prior_seconds_used_by_gate": 0.520595542,
                "v1_peak_bytes": lifetime["conservative_host_peak_bytes"],
                "cumulative_fixture_wall_ceiling_seconds": 60,
                "remaining_v2_wall_seconds": 59.479404458,
                "host_ceiling_bytes": 536870912, "prior_failure_not_reclassified": True},
            "runtime_observation": {"python_executable": sys.executable, "python_version": sys.version,
                                    "stdlib_runtime_not_a_formal_correspondence_claim": True},
            "plan_preparation_seconds_before_write": time.perf_counter() - start}
    destination.write_text(json.dumps(plan, indent=2) + "\n")
    receipt = {"status": "repair_sources_inputs_costs_frozen_before_execution", "plan": pin(destination),
               "sources": len(sources), "inputs": len(plan["inputs"]), "preserved_entries": len(preserved),
               "source_syntax": "ast.parse only; no graph imported", "v2_executions": 0,
               "actual_model_executions": 0, "native_queries": 0,
               "freeze_seconds_before_receipt_write": time.perf_counter() - start}
    (HERE / "freeze-receipt-v2.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
