"""Prospective source/input/limit freeze; does not import or construct a graph."""
import ast
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OLD = ROOT / ".gcts-active/hilbert-aggregate-expansion-20261011"
AUDIT = ROOT / ".gcts-active/hilbert-aggregate-independent-audit-20261011"


def pin(path):
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(65536), b""):
            h.update(data)
    return {"path": str(path.relative_to(ROOT)), "sha256": h.hexdigest(), "bytes": path.stat().st_size}


def main():
    start = time.perf_counter()
    path = HERE / "plan-v1.json"
    if path.exists():
        raise ValueError("immutable prospective plan exists")
    sources = sorted(HERE.glob("hilbert_primitive_graph*_v1.py"))
    for source in sources:
        ast.parse(source.read_text(), filename=str(source))
    inputs = []
    for role, source in [
        ("master_contract", ROOT / "docs/basic-tiling-algorithm.md"),
        ("primitive_model", OLD / "model-v2.json.gz"),
        ("primitive_logical_audit", AUDIT / "audit-full-v2.json"),
        ("primitive_logical_audit_lifetime", AUDIT / "audit-lifetime-v2.json"),
        ("primitive_logical_audit_parser_scope", AUDIT / "parser-scope-v2.json"),
        ("primitive_logical_audit_completion", AUDIT / "completion-receipt-v2.json"),
        ("static_export", OLD / "export-final-v1.json"),
        ("static_production", OLD / "production-checkpoint-v2.json"),
        ("complete_family_template_projection", OLD / "reader-data-v2.json"),
        ("independent_prospective_executor_gate", ROOT / ".gcts-active/stochastic-replay-review-20261011/primitive-executor-gates-v1.json"),
        ("factorization_argument", HERE / "factorization-v1.json"),
    ]:
        inputs.append({"role": role, **pin(source)})
    previous = json.loads((OLD / "plan-v1.json").read_text())["preserved_files"]
    previous += json.loads((OLD / "export-final-v1.json").read_text())["files"]
    previous += json.loads((AUDIT / "integration-v2.json").read_text())["files"]
    previous += [pin(OLD / "export-final-v1.json"), pin(AUDIT / "integration-v2.json")]
    preserved = {}
    for p in previous:
        actual = pin(ROOT / p["path"])
        assert actual == {k: p[k] for k in ("path", "sha256", "bytes")}
        if p["path"] in preserved:
            assert preserved[p["path"]] == actual
        preserved[p["path"]] = actual
    plan = {
        "version": "hilbert-complete-implicit-primitive-point-kernel-v1",
        "status": "frozen_before_synthetic_fixture_execution_actual_model_gate_separate",
        "sources": [pin(p) for p in sources], "inputs": inputs,
        "preserved_files": [preserved[k] for k in sorted(preserved)],
        "finite_production_language": {"named_definitions": 171, "recipes": 229, "formula_codes": 217,
            "boundary_rows": 24, "global_hypothesis_seed_rows": [0, 1, 2],
            "canonical_local_definition_contexts_are_not_recipient_hypotheses": True,
            "orientation": "identity", "transformation": "vertical integer translation only",
            "arithmetic": "integer unit occupancy, injective integer formula marks, signed integer offsets",
            "raw_alignment_grammar_census_previously_audited": 1830264,
            "locally_consistent_strict_prior_grammar_census_previously_audited": 584952,
            "counts_are_not_initial_graph_degree_measurements": True},
        "synthetic_gate": {"authorized_scope": "small point-contract fixtures only, no actual geometry model loading",
            "wall_ceiling_seconds": 60, "child_alarm_seconds": 55, "supervisor_ceiling_seconds": 56,
            "host_ceiling_bytes": 536870912, "phase_runs": 1,
            "prospective_exhaustive_states": 1216,
            "controls": ["full raw translated prototype comparison, degree/singleton/order/point data",
                "independent lazy decorated identity reconstruction", "equal ordered premise ports",
                "formula/port assigned zero versus absence", "global dead/forced/generation order",
                "distant dependencies and exact rollback including reference counts/local exclusions",
                "shared identity, incompatible and stale/ineligible proposals, full base fallback",
                "point-consistent invalid MP schema", "bool-vs-int and registry collision",
                "synthetic finite exhausted/unknown/solved transaction control"],
            "enforcement": "task-owned fail-closed sampled process RSS/time watchdog, child SIGALRM, kernel peak rejection; no OS soft-limit claim",
            "outer_measurement": "fixture and supervisor final receipt serialization included; outer own receipt write separately disclosed"},
        "actual_model_execution_gate": {"status": "not_authorized_by_this_fixture_plan_root_review_required",
            "proposed_next_scope": "construct full 24-row implicit graph, compare complete initial row counts/full base iterations against independent direct enumeration, verify distant updates/rollback and lazy identities; authored proof only read-only witness control",
            "target_searches": 0, "native_queries": 0, "compiler_changes": 0,
            "new_policies": 0, "existing_native_authority_activation": False},
        "logical_scope": "Exact-byte already independently checked finite primitive palette, host point graph only. Synthetic fixture language is not a logic. Any found production tiling still requires independent whole decoded primitive logical validation; native/compiler correspondence open.",
        "search_implementation_scope": "Executor source is authored, not run on the actual geometry recipient. Full fallback and scheduler must be independently audited before target search.",
        "source_authoring_cost": "wall time not instrumented; not reported as zero",
        "plan_preparation_seconds_before_write": time.perf_counter() - start,
        "new_native_queries": 0, "actual_model_executions": 0,
        "geometry_target_searches": 0, "new_RL_training": False,
    }
    path.write_text(json.dumps(plan, indent=2) + "\n")
    receipt = {"status": "frozen_source_input_budget_before_execution", "plan": pin(path),
               "sources": len(sources), "inputs": len(inputs), "preserved_entries": len(preserved),
               "syntax": "ast.parse only; no source imported", "source_execution": "this freezer only",
               "actual_model_executions": 0, "native_queries": 0,
               "freeze_seconds_before_receipt_write": time.perf_counter() - start}
    (HERE / "freeze-receipt-v1.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
