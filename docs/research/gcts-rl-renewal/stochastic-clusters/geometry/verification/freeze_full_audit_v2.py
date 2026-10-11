"""Freeze the prospective independent audit; this never executes it."""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OWNER = ROOT / ".gcts-active/hilbert-aggregate-expansion-20261011"


def pin(path, role=None):
    result = {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "bytes": path.stat().st_size}
    if role is not None:
        result["role"] = role
    return result


def main():
    began = time.perf_counter()
    output = HERE / "full-audit-plan-v2.json"
    if output.exists():
        raise ValueError("prospective plan is immutable")
    producer_plan = json.loads((OWNER / "plan-v1.json").read_bytes())
    checkpoint = json.loads((OWNER / "production-checkpoint-v2.json").read_bytes())
    if checkpoint["status"] != "bounded_static_production_passed_independent_audit_pending":
        raise ValueError("no passed producer resource gate")
    inputs = list(producer_plan["inputs"])
    for item in inputs:
        path = ROOT / item["path"]
        if pin(path) != {key: item[key] for key in ("path", "sha256", "bytes")}:
            raise ValueError("input changed before audit freeze: " + item["path"])
    inputs.extend(pin(OWNER / name, role) for role, name in (
        ("scientific_producer_plan", "plan-v1.json"), ("repair_plan", "plan-v2.json"),
        ("production_checkpoint", "production-checkpoint-v2.json"),
        ("expansions", "expansions-v2.json.gz"), ("model", "model-v2.json.gz"),
        ("example_correspondence", "example-correspondence-v2.json"),
        ("historical_expansions", "expansions-v1.json.gz"), ("historical_model", "model-v1.json.gz"),
        ("historical_example", "example-correspondence-v1.json"),
        ("prior_production_stage", "stage-costs-v1.json"), ("prior_production_lifetime", "outer-lifetime-v1.json"),
        ("production_stage", "stage-costs-v2.json"), ("production_lifetime", "outer-lifetime-v2.json"),
        ("production_receipt", "production-v2.json"),
        ("serialization_receipt", "serialization-correspondence-v2.json")))
    inputs.extend(pin(HERE / name, role) for role, name in (
        ("toy_plan", "toy-plan-v1.json"), ("toy_fixture", "toy-fixtures-v1.json"),
        ("toy_receipt", "toy-receipt-v1.json"), ("prospective_v1_gate", "prospective-gate-v1.json")))
    # Producer source/old archive pins are evidence inputs, never imported code.
    extras = producer_plan["sources"] + producer_plan["preserved_files"]
    known = {item["path"] for item in inputs}
    for item in extras:
        if item["path"] not in known:
            inputs.append({**item, "role": "preserved_evidence_input"})
            known.add(item["path"])
    sources = [pin(HERE / name) for name in ("independent_aggregate_audit_v1.py",
        "independent_aggregate_full_v2.py", "independent_aggregate_lifetime_v2.py", "freeze_full_audit_v2.py")]
    plan = {"status": "frozen_waiting_root_review_no_audit_execution",
        "scope": "independent_full171_static_audit_no_activation", "version": "independent-aggregate-full-v2",
        "sources": sources, "inputs": inputs,
        "limits": {"full_lifetime_seconds": 180, "worker_alarm_seconds": 178,
                   "conservative_peak_rss_bytes": 536870912, "json_record_buffer_characters": 16777216},
        "resource_enforcement": {"time": "worker alarm plus whole observer deadline/kill/wait",
            "memory": "final kernel peak sum for isolated child and observer; no hard OS limit or ps sampling claim",
            "startup_and_final_worker_serialization": "included in observer lifetime",
            "final_lifetime_receipt_write": "excluded and unmeasured"},
        "worker_source": str((HERE / "independent_aggregate_full_v2.py").relative_to(ROOT)),
        "scientific_output_version": "hilbert-primitive-aggregate-static-v1",
        "outputs": {role: str((HERE / name).relative_to(ROOT)) for role, name in (
            ("audit", "audit-full-v2.json"), ("lifetime", "audit-lifetime-v2.json"),
            ("stdout", "audit-stdout-v2.txt"), ("stderr", "audit-stderr-v2.txt"))},
        "prospective_command": [sys.executable, "-B", str(HERE / "independent_aggregate_lifetime_v2.py"),
                                "--plan", str(output)],
        "method": ["Check source/recipient signatures, exact I.2 axiom images, closed role-preserving maps, every full transported body and ordered prior dependency alias.",
            "Independently validate all original and mapped commands in the six-rule relation; no status-only or point-only acceptance.",
            "Use an iterative local-call-frame interpreter, not producer recursion/imports, to rebuild every literal leaf, ordered assumption alias and recursive call.",
            "Reconstruct exact injective registry extension, sorted full recipe palette and every donor occurrence alias.",
            "Independently lower all canonical rows twice, rebuild all ordered receptor ports and aggregate unions, and compare every streamed actual record.",
            "Reconstruct the 24-row legacy word with the previously reviewed independent DAG implementation; retain old label semantics and independently bind fresh full t/m/registry/authority identities.",
            "Compute parametric 24/65 census by closed-form sums; do not materialize or claim a complete candidate graph.",
            "Run retained tiny controls and actual authority, registry, hidden marking, reference order, overcount and point-consistent-invalid-inference corruptions.",
            "Independently compare decoded historical/current serialization bytes without reclassifying failed first production."],
        "predicted_not_yet_independently_verified": {"definitions": 171, "leaves": 1845, "recipes": 229,
            "formulas": 217, "aliases": 630, "recursive_calls": 216, "legacy_rows": 24, "legacy_shared_rows": 5},
        "forbidden": ["producer imports", "native query or replay", "search or solver", "engine activation",
            "shared source mutation", "HTML or publication edits"],
        "remaining_open": ["complete primitive candidate graph", "general family embedding enumeration",
            "scheduler/fallback/rollback conformance", "conditional 65-row one-way lift construction",
            "formal compiler/native correspondence", "whole native acceptance"],
        "prior_costs": {"producer_failed_v1": checkpoint["prior_v1_unknown"],
            "producer_cumulative_seconds": checkpoint["cumulative_production_outer_seconds"],
            "toy_seconds_before_receipt": 0.0016255, "toy_startup_write": "unmeasured and excluded"},
        "preparation_seconds_before_plan_write": time.perf_counter() - began,
        "authoring_preparation": "unmeasured; not zero"}
    output.write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps({"plan": pin(output), "source_count": len(sources), "input_count": len(inputs)}))


if __name__ == "__main__":
    main()
