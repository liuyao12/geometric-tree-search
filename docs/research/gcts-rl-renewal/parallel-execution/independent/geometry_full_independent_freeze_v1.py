"""Freeze prospective source/data/resource gate; does not load actual model."""
import ast
import hashlib
import json
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PRODUCER = ROOT / ".gcts-active/hilbert-primitive-executor-20261011"


def pin(path, role=None):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    entry = dict(path=str(path.relative_to(ROOT)), sha256=h.hexdigest(), bytes=path.stat().st_size)
    if role:
        entry["role"] = role
    return entry


def main():
    began = time.perf_counter()
    planpath = HERE / "geometry-full-independent-plan-v1.json"
    if planpath.exists():
        raise ValueError("immutable independent full plan exists")
    oldpath = PRODUCER / "full-model-plan-v1.json"
    old = json.loads(oldpath.read_bytes())
    sources = [pin(HERE / name) for name in ("geometry_full_independent_audit_v1.py", "geometry_full_independent_owner_v1.py", "geometry_full_independent_freeze_v1.py")]
    for source in sources:
        ast.parse((ROOT / source["path"]).read_text(), filename=source["path"])
    inputs = list(old["inputs"])
    for path, role in ((oldpath, "producer_plan"),
                       (PRODUCER / "full-model-outcome-v1.json", "producer_outcome"),
                       (PRODUCER / "full-model-lifetime-v1.json", "producer_lifetime"),
                       (PRODUCER / "full-model-supervision-v1.json", "producer_supervision"),
                       (PRODUCER / "hilbert_primitive_graph_v2.py", "kernel_under_test"),
                       (ROOT / ".gcts-active/hilbert-aggregate-independent-audit-20261011/independent_aggregate_audit_v1.py", "independent_symbolic_checker"),
                       (HERE / "geometry-independent-result-v1.json", "independent_tiny_fixtures"),
                       (HERE / "geometry-independent-lifetime-v1.json", "independent_tiny_lifetime")):
        inputs.append(pin(path, role))
    preserved = list(old["preserved_files"]) + old["sources"]
    for entry in sources + inputs + preserved:
        actual = pin(ROOT / entry["path"])
        if any(actual[k] != entry[k] for k in ("sha256", "bytes")):
            raise ValueError("frozen source/input mismatch " + entry["path"])
    lifetime = json.loads((PRODUCER / "full-model-lifetime-v1.json").read_bytes())
    plan = dict(status="frozen_prospective_independent_full_model_audit_root_review_required",
        version="independent-full-24-primitive-point-and-logical-word-v1", sources=sources, inputs=inputs, preserved_files=preserved,
        worker_path=str((HERE / "geometry_full_independent_audit_v1.py").relative_to(ROOT)),
        owner_path=str((HERE / "geometry_full_independent_owner_v1.py").relative_to(ROOT)),
        result_path=str((HERE / "geometry-full-independent-result-v1.json").relative_to(ROOT)),
        lifetime_path=str((HERE / "geometry-full-independent-lifetime-v1.json").relative_to(ROOT)),
        stdout_path=str((HERE / "geometry-full-independent-stdout-v1.txt").relative_to(ROOT)),
        stderr_path=str((HERE / "geometry-full-independent-stderr-v1.txt").relative_to(ROOT)),
        whole_seconds=180, child_seconds=170, peak_bytes=536870912, execution_requires_root_review=True,
        prospective_scope=["Independently validate every recipe's exact symbolic witness against fixed guarded I.2 and ordered three-premise global context.",
                           "Reconstruct all boundary roots, exterior/target marks, formula injectivity, authority/registry/recipe identities and exact grammar census.",
                           "Stream every raw negative-offset prototype for every row against separate independent t/m state. Compare complete kernel iterator/key/t/m/count/zero/singleton, full recorded stream hashes and all per-recipe counts in all fourteen producer states.",
                           "Independently reconstruct full state including assigned-zero versus absence, marking reference counts, selected order/generations, factor representation and complete rollback. Factor reconstruction supplies state representation only; raw enumeration supplies domain authority.",
                           "Reconstruct every468 lazy decorated identity and each generic eight-step base scheduler decision; catalog remote MP and code-zero controls remain separate.",
                           "Load authored24 word only after generic probes; independently check every primitive inference/ordered prior reference, complete point union and exact whole certificate/ID hashes.",
                           "Check actual corrupted ordered refs, forward refs, locally consistent point shapes with invalid logical inference, registry/authority/port/identity mismatches, t-overcount and ordered seed aliases."],
        no_authority_upgrade=["No target DFS, subtree exhaustion, learned policy, native query or compiler activation.",
                              "Finite full-state controls do not prove all execution states; tiny adversarial dead/forced/generation tests remain their separately scoped evidence.",
                              "Existing fixed preference-set cluster continuation lifecycle gap remains open.",
                              "Authored word is a read-only verification control, not discovered proof or RL result; native/compiler/Wang correspondence remains open."],
        independence="No producer or author-auditor imports. Under-test kernel class methods are compared against new independent direct enumeration/state/identity code; independent previously frozen SymbolicChecker validates every inference. No prior auditor main is executed.",
        resource_enforcement="Sole direct child owner with170s alarm and180s whole wall kill/reap; conservative fresh child plus owner kernel peaks after exit, unchanged512MiB; no hard OS memory cap claim.",
        clock_scope="Pin hashes, parsing, all domain/state/logical checks, result serialization and worker lifecycle included. Owner own final lifetime receipt write and source authoring outside stage timer and disclosed separately.",
        producer_costs_bound=pin(PRODUCER / "full-model-lifetime-v1.json"),
        prior_independent_tiny_costs_bound=pin(HERE / "geometry-independent-lifetime-v1.json"),
        prior_author_synthetic_failure_and_retry_seconds=1.365436125,
        prior_geometry_static_unknowns="All preserved source/output/receipt pins copied from frozen producer plan unchanged; no prior failure is relabeled.",
        predictions_not_results=dict(states=14, candidate_comparisons=3173785, initial_candidates=332130, recipes=229, formula_codes=217, lazy_identities=468),
        target_searches=0, native_queries=0, training_episodes=0, actual_independent_model_audits_at_freeze=0,
        preparation_seconds_before_plan_write=time.perf_counter() - began,
        source_authoring_wall_time="not instrumented; not zero")
    with planpath.open("x") as stream:
        json.dump(plan, stream, indent=2); stream.write("\n")
    archivepath = HERE / "geometry-full-independent-sources-v1.zip"
    with zipfile.ZipFile(archivepath, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for entry in sources + [e for e in inputs if e["role"] in ("kernel_under_test", "independent_symbolic_checker")]:
            archive.write(ROOT / entry["path"], entry["path"])
    receipt = dict(status="frozen_source_ready_no_actual_execution", plan=pin(planpath), source_archive=pin(archivepath),
                   source_pins=len(sources), input_pins=len(inputs), preserved_pins=len(preserved),
                   actual_model_loads=0, actual_graph_audits=0, target_searches=0, native_queries=0,
                   preparation_seconds_before_receipt_write=time.perf_counter() - began)
    with (HERE / "geometry-full-independent-source-ready-v1.json").open("x") as stream:
        json.dump(receipt, stream, indent=2); stream.write("\n")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
