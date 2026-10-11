"""Freeze actual full-language conformance source/input/budget before execution."""
import ast
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OLD = ROOT / ".gcts-active/hilbert-aggregate-expansion-20261011"


def pin(path):
    path = Path(path)
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            sha.update(block)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha.hexdigest(), "bytes": path.stat().st_size}


def main():
    start = time.perf_counter()
    target = HERE / "full-model-plan-v1.json"
    if target.exists():
        raise ValueError("immutable full-model prospective freeze exists")
    prior = json.loads((HERE / "plan-v2.json").read_text())
    sources = [HERE / "hilbert_primitive_graph_v2.py"] + sorted(HERE.glob("hilbert_primitive_graph_full*_v1.py"))
    for source in sources:
        ast.parse(source.read_text(), filename=str(source))
    previous = prior["preserved_files"] + prior["sources"] + prior["inputs"]
    previous += [pin(p) for p in sorted(HERE.iterdir()) if p.is_file() and
                 (p.name.endswith("-v1.json") or p.name.endswith("-v2.json")
                  or p.name.endswith("-v1.txt") or p.name.endswith("-v2.txt")
                  or p.name.endswith("_v2-diff.txt"))]
    preserved = {}
    for p in previous:
        actual = pin(ROOT / p["path"])
        assert actual == {k: p[k] for k in ("path", "sha256", "bytes")}
        if p["path"] in preserved:
            assert preserved[p["path"]] == actual
        preserved[p["path"]] = actual
    inputs = list(prior["inputs"])
    inputs += [{"role": "authored_witness_control", **pin(OLD / "example-correspondence-v2.json")},
               {"role": "frozen_synthetic_parent_plan", **pin(HERE / "plan-v2.json")},
               {"role": "authored_synthetic_kernel_outcome", **pin(HERE / "fixtures-outcome-v2.json")},
               {"role": "authored_synthetic_kernel_lifetime", **pin(HERE / "fixtures-lifetime-v2.json")},
               {"role": "fixed_preference_control_gap", **pin(HERE / "conformance-scope-v1.json")},
               {"role": "actual_model_readiness", **pin(HERE / "actual-model-readiness-v1.json")}]
    plan = {"version": "hilbert-full-24-primitive-point-domain-conformance-gate-v1",
            "status": "frozen_prospective_actual_model_phase_root_review_required_before_execution",
            "sources": [pin(p) for p in sources], "inputs": inputs,
            "preserved_files": [preserved[k] for k in sorted(preserved)],
            "producer_limits": {"wall_seconds": 180, "child_alarm_seconds": 170,
                                "supervisor_seconds": 175, "host_bytes": 536870912,
                                "runs_authorized_by_this_plan": 0,
                                "execution_requires_root_review": True},
            "independent_audit": "Separate agent source/input/full-lifetime gate must be independently frozen and reviewed; this producer cannot supply independent acceptance.",
            "model": prior["finite_production_language"],
            "complete_enumeration": {"universe": "All 229 exact recipes, all 24 positive-support row alignments, every raw pair of allowed negative offsets. Generic t-capacity/local and distant m agreement reject prototypes.",
                "algorithm": "Independent streaming direct prototype iterator versus implicit candidate iterator, key-by-key and exact t/m at every row; complete degrees, zero/singleton and per-recipe count/stream digest receipts.",
                "maximum_locally_consistent_strict_prior_placements_per_state": 584952,
                "prospective_complete_states_maximum": 14,
                "counts_are_predictions_or_prior_grammar_census_not_new_results": True,
                "memory": "No materialized full candidate table/SHA identity list; one raw/current candidate streamed. First/last representative per recipe retained for lazy identity checks."},
            "probes": [
                {"name": "complete_initial_graph_and_all_recipe_identity_representatives",
                 "all_rows": 24, "all_recipes": 229, "recipe_representative_count": "measured only if it has a legal initial candidate; missing recipes reported, never silently removed"},
                {"name": "generic_base_scheduler_prefix", "maximum_derived_placements": 8,
                 "candidate_selection": "Stable full base iterator at independently recomputed reference decision point; no hint, learner or target proof word.",
                 "stop": "After eight or earlier dead state; no DFS, backtracking, subtree exhaustion, learned pruning or target proof assertion.",
                 "proof_region_cannot_complete": "Three initial seeds plus at most eight placements is fewer than 24 required rows.",
                 "after_each": "Full complete-domain comparison; placed generation one since all roots remain zero.",
                 "rollback": "Exact semantic state including totals, marks/reference counts, selection/order/gens, domains and local exclusions."},
                {"name": "remote_mp_catalog_transaction", "scheduler_claim": "none for low-level probe",
                 "candidate": "First MP in descending output row full base iterator; reads possibly untouched prior rows through m, then exhaustive graph update comparison and exact rollback."},
                {"name": "assigned_formula_zero_catalog_transaction", "candidate": "Exact I.2 axiom recipe at row three, code zero remains assigned; full domains then exact rollback."},
                {"name": "isolated_read_only_authored_24_row_point_witness", "source_read_order": "Only after all generic probes. Never supplied to generic prefix, learner, initial proof state or preference set.",
                 "meaning": "Literal command/ref/t/m/full-ID comparison and low-level legal catalog replay, complete target/all-mark reconstruction; authored verification control, not discovered reference search path.",
                 "logical_authority": "Existing independent full primitive audit bound; no new native acceptance."}],
            "identity_scope": "Complete per-key recipe witness, ordered refs, t/m, context, registry, authority. Representatives and visited/control identities are independently reconstructed; no inference from same formula or legacy label.",
            "limits_enforcement": "Task-owned sampled RSS/time watchdog fails closed and kills/reaps owned child; child SIGALRM and final conservative kernel peaks. No OS soft-limit claim. Outer lifetime includes producer/supervisor final serialization, own outer receipt write separately disclosed.",
            "conformance_scope": "Complete primitive point graph/base scheduler controls only, independent audit still required. Frozen v2 has fixed preference-set scope, not full pending-cluster revalidation/lifecycle conformance.",
            "cost_accounting": {"prior_synthetic_runtime_unknown_seconds": 0.520595542,
                                "prior_synthetic_v2_pass_seconds": 0.844840583,
                                "prior_synthetic_cumulative_seconds": 1.365436125,
                                "new_full_model_preparation_execution_audit": "Measured separately; no fresh native query. Prior admission/native replays and resource failures remain bound in old export.",
                                "source_authoring_wall_time": "not instrumented, not zero"},
            "plan_preparation_seconds_before_write": time.perf_counter() - start,
            "new_native_queries": 0, "geometry_target_searches": 0, "new_RL_training": False,
            "existing_engine_or_native_authority_activation": False,
            "native_compiler_correspondence": "open, not established by point conformance",
            "full_model_executions_at_freeze": 0}
    target.write_text(json.dumps(plan, indent=2) + "\n")
    receipt = {"status": "full_language_conformance_sources_inputs_budget_frozen_before_execution",
               "plan": pin(target), "sources": len(sources), "inputs": len(inputs),
               "preserved_entries": len(preserved), "syntax": "ast.parse only, no model/graph imported",
               "actual_model_executions": 0, "native_queries": 0, "target_searches": 0,
               "freeze_seconds_before_receipt_write": time.perf_counter() - start}
    (HERE / "full-model-freeze-v1.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
