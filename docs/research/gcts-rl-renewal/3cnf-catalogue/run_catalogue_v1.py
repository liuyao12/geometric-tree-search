"""Unexecuted streaming fixed 3CNF catalogue comparison; no supplied answers.

One complete case is built, searched, independently checked, written and
released.  Only seventy lightweight summary rows survive between cases.
The external native terminal observation remains mandatory for acceptance.
"""
import time
BEGAN = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
import hashlib
import itertools
import json
from pathlib import Path
import resource
import sys
import types

VERSION = "fixed-70-3CNF-streaming-catalogue-runner-v1"
CLOCK_DOMAIN = "time.clock_gettime_ns(time.CLOCK_MONOTONIC)"
FROZEN_INPUTS = {
    "engine": ("2690280c314d57ea8b585d556ddc1a38b164c5ffe56ff831bc58e5bacc1724b3", 15493),
    "oracle": ("f0841090782102a121702f81c742a0d397f3ef3e59788a163426ccfe8447a472", 8821),
    "point_auditor": ("4081e574d38ea689ebdc846c0bb3760c4e202dd87e927db65cd902204319e84a", 18005),
    "ordinary": ("15ca1ca4f5a3a685ca4ac8fc45332d219d5594c97f64a07c7100d7da9fedc9d3", 7393),
    "verifier": ("7f1d192c67b858e1ef1a0fcc7a7a556671af534d29f607f156f028f0ad2345ea", 30551),
    "catalogue_verifier": ("fadee2e0f26379dfdf7cd45580723f2a24fc563b7d82fa38b641d1f022247639", 25659),
}
ARM_NAMES = ("ordinary_no", "ordinary_learned", "point_no", "point_learned")
POINT_LIMITS = {"maximum_nodes": 20000, "maximum_candidate_checks": 500000,
                "maximum_trace_events": 50000}
ORDINARY_LIMITS = {"maximum_nodes": 20000, "maximum_literal_checks": 500000,
                   "maximum_trace_events": 50000}


def need(value, message):
    if not value:
        raise ValueError(message)


def stamp():
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC)


def deadline():
    need(stamp() - BEGAN < 40000000000, "whole cold forty-second budget")
    need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 536870912,
         "sampled Darwin whole-worker 512 MiB cap")


def read_pin(item, maximum_bytes):
    need(type(item) is dict and set(item) == {"path", "sha256", "bytes"}, "raw pin fields")
    need(type(item["bytes"]) is int and 0 < item["bytes"] <= maximum_bytes,
         "bounded raw pin")
    path = Path(item["path"])
    need(path.is_absolute(), "absolute raw Source path")
    raw = path.read_bytes()
    need(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"],
         "exact same-buffer raw pin")
    return raw


def load_source(role, item, invocation):
    deadline()
    need((item["sha256"], item["bytes"]) == FROZEN_INPUTS[role], "exact " + role)
    raw = read_pin(item, 1048576)
    name = "_fixed_3cnf_" + str(invocation) + "_" + role
    need(name not in sys.modules, "fresh private Source module")
    module = types.ModuleType(name)
    module.__file__ = item["path"]
    sys.modules[name] = module
    exec(compile(raw, item["path"], "exec"), module.__dict__)
    deadline()
    return module


def satisfying_bits(clauses):
    return tuple(tuple((i, 1 if sign == 1 else 0) for i, sign in clause)
                 for clause in clauses)


def clause_true(clause, bits):
    return any(bits[i] == (1 if sign == 1 else 0) for i, sign in clause)


def boolean_check(result, seeds, accepted, point):
    if result["status"] == "UNKNOWN":
        need(result["solution"] is None and result["trace_complete"] is False,
             "UNKNOWN has no accepted witness")
        return
    extensions = [bits for bits in accepted if all(bits[i] == b for i, b in seeds)]
    expected = "FOUND" if extensions else (
        "EXHAUSTED_FINITE_MARKED_MODEL" if point else "EXHAUSTED_FINITE_CNF")
    need(result["status"] == expected and result["trace_complete"] is True,
         "complete outcome against original oracle")
    if expected == "FOUND":
        if point:
            marks = {(x, y): value for x, y, value in result["solution"]["marks"]}
            bits = [marks[6 * i, 2] for i in range(3)]
        else:
            bits = [b for _, b in result["solution"]]
        need(bits in extensions, "original-context complete witness")


def run_point(modules, clauses, active, seeds, accepted):
    deadline(); began = stamp()
    model = modules["engine"].build_cnf_model(
        3, satisfying_bits(clauses), active_guards=tuple(active),
        seed_bits=tuple(tuple(x) for x in seeds), maximum_candidates=256)
    built = stamp()
    result = modules["engine"].solve(model, **POINT_LIMITS)
    solved = stamp(); deadline()
    audit = modules["point_auditor"].audit_result(
        result, allow_unknown=result["status"] == "UNKNOWN")
    boolean_check(result, seeds, accepted, True)
    checked = stamp(); deadline()
    return result, audit, {"build_ns": built - began, "solve_ns": solved - built,
                           "check_ns": checked - solved, "inclusive_ns": checked - began}


def run_ordinary(modules, clauses, seeds, accepted):
    deadline(); began = stamp()
    encoded = satisfying_bits(clauses)
    boundary = tuple(tuple(x) for x in seeds)
    built = stamp()
    result = modules["ordinary"].solve_cnf(3, encoded, boundary, **ORDINARY_LIMITS)
    solved = stamp(); deadline()
    audit = modules["verifier"].verify_ordinary_result(result)
    boolean_check(result, seeds, accepted, False)
    checked = stamp(); deadline()
    return result, audit, {"build_ns": built - began, "solve_ns": solved - built,
                           "check_ns": checked - solved, "inclusive_ns": checked - began}


def make_case(index, masks, modules):
    began = stamp(); deadline()
    clauses = [[[i, 1 if (mask >> (2 - i)) & 1 else -1] for i in range(3)]
               for mask in masks]
    original = {"id": "T" + str(index).zfill(3), "variables": 3,
                "clauses": clauses, "prefixes": []}
    oracle_began = stamp()
    truth = modules["oracle"].evaluate_case(original)
    accepted = truth["modes"][1]["accepted_assignments"]
    oracle_end = stamp(); deadline()
    boundaries = [[[i, b]] for i in range(3) for b in (0, 1)]
    case = {"catalogue_index": index, "original": original,
            "discovery_boundaries": boundaries, "discovery": [], "discovery_audits": [],
            "proposal_log": [], "learned": [], "replay_boundaries": [[]] + boundaries,
            "arms": {arm: [] for arm in ARM_NAMES},
            "point_arm_audits": {arm: [] for arm in ARM_NAMES if arm.startswith("point_")},
            "ordinary_arm_audits": {arm: [] for arm in ARM_NAMES if arm.startswith("ordinary_")},
            "original_oracle": truth, "execution_order": [],
            "timings": {"oracle_ns": oracle_end - oracle_began, "discovery": [],
                        "certification_ns": 0, "replay": {arm: [] for arm in ARM_NAMES}}}
    seen = set()
    originals = {tuple(tuple(x) for x in clause) for clause in clauses}
    for bi, seeds in enumerate(boundaries):
        result, audit, timing = run_point(modules, clauses, range(4), seeds, accepted)
        case["discovery"].append(result); case["discovery_audits"].append(audit)
        case["timings"]["discovery"].append(timing)
        if result["status"] != "EXHAUSTED_FINITE_MARKED_MODEL":
            continue
        certify_began = stamp()
        candidate = tuple((i, 1 if bit == 0 else -1) for i, bit in seeds)
        entailed = all(clause_true(candidate, bits) for bits in accepted)
        selected = (entailed and candidate not in originals and candidate not in seen
                    and len(case["learned"]) < 2)
        proposal = {"discovery_boundary_index": bi, "clause": [list(x) for x in candidate],
                    "is_original": candidate in originals, "is_duplicate": candidate in seen,
                    "entailed": entailed, "selected": selected}
        case["proposal_log"].append(proposal)
        need(entailed, "whole exhausted singleton must certify its negation")
        if selected:
            case["learned"].append({"clause": proposal["clause"],
                                    "discovery_boundary_index": bi})
        seen.add(candidate)
        case["timings"]["certification_ns"] += stamp() - certify_began
        deadline()
    case["timings"]["whole_discovery_ns"] = stamp() - began
    combined = clauses + [entry["clause"] for entry in case["learned"]]
    for bi, seeds in enumerate(case["replay_boundaries"]):
        offset = (index + bi) % 4
        order = ARM_NAMES[offset:] + ARM_NAMES[:offset]
        case["execution_order"].append(list(order))
        for arm in order:
            if arm.startswith("point_"):
                active = range(len(combined)) if arm.endswith("_learned") else range(4)
                result, audit, timing = run_point(modules, combined, active, seeds, accepted)
                case["point_arm_audits"][arm].append(audit)
            else:
                library = combined if arm.endswith("_learned") else clauses
                result, audit, timing = run_ordinary(modules, library, seeds, accepted)
                case["ordinary_arm_audits"][arm].append(audit)
            case["arms"][arm].append(result)
            case["timings"]["replay"][arm].append(timing)
    case["timings"]["case_before_whole_verification_ns"] = stamp() - began
    deadline()
    return case


def summarize(case, audit, verification_ns):
    row = {"catalogue_index": case["catalogue_index"], "case_id": case["original"]["id"],
           "learned": case["learned"], "proposal_count": len(case["proposal_log"]),
           "discovery_outcomes": {}, "arms": {}, "case_verification_ns": verification_ns,
           "whole_discovery_ns": case["timings"]["whole_discovery_ns"],
           "all_boundaries_completed": audit["all_boundaries_completed"],
           "unknown_count": audit["unknown_count"],
           "marking_effect_totals": audit["marking_effect"]["totals"]}
    for result in case["discovery"]:
        status = result["status"]
        row["discovery_outcomes"][status] = row["discovery_outcomes"].get(status, 0) + 1
    for arm, results in case["arms"].items():
        outcomes = {}
        for result in results:
            outcomes[result["status"]] = outcomes.get(result["status"], 0) + 1
        keys = (("branch_decisions", "forced_placements", "backtracks")
                if arm.startswith("point_") else
                ("branch_decisions", "unit_decisions", "conflicts", "assignments", "restores", "literal_checks"))
        row["arms"][arm] = {
            "outcomes": outcomes,
            "timing_ns": {key: sum(t[key] for t in case["timings"]["replay"][arm])
                          for key in ("build_ns", "solve_ns", "check_ns", "inclusive_ns")},
            "representation_counters": {key: sum(r["stats" if arm.startswith("point_") else "work_counts"][key]
                                                   for r in results) for key in keys}}
    return row


def main(plan_path):
    deadline()
    need(sys.platform == "darwin", "pinned Darwin terminal RSS byte semantics")
    raw_plan = Path(plan_path).read_bytes()
    need(len(raw_plan) <= 1048576, "bounded plan")
    plan = json.loads(raw_plan)
    need(plan["schema"] == "ROOT-fixed-3CNF-catalogue-plan-v1", "plan schema")
    need(type(plan["invocation"]) is int and plan["invocation"] >= 1, "invocation")
    need(set(plan["inputs"]) == set(FROZEN_INPUTS), "exact six Source roles")
    for field, expected in (("worker_seconds", 40), ("whole_native_seconds", 40),
                            ("whole_tool_seconds", 60), ("worker_peak_bytes", 536870912),
                            ("case_count", 70), ("discovery_solves", 420), ("replay_solves", 1960),
                            ("maximum_candidates", 256), ("maximum_learned_clauses", 2)):
        need(type(plan[field]) is int and plan[field] == expected, "fixed " + field)
    need(plan["point_limits"] == POINT_LIMITS and plan["ordinary_limits"] == ORDINARY_LIMITS,
         "original finite work limits")
    for field in ("maximum_output_bytes", "maximum_case_bytes"):
        need(type(plan[field]) is int and 1 <= plan[field] <= 536870912, "output budget")
    need(plan["maximum_case_bytes"] <= plan["maximum_output_bytes"], "whole line budget")
    own = read_pin(plan["runner"], 1048576)
    need(Path(plan["runner"]["path"]) == Path(__file__), "executed original runner path")
    del own
    output = Path(plan["output_directory"])
    need(output.is_absolute() and output.is_dir() and not list(output.iterdir()), "exclusive empty output")
    modules = {role: load_source(role, plan["inputs"][role], plan["invocation"])
               for role in FROZEN_INPUTS}
    source_loaded = stamp(); deadline()
    plan_sha = hashlib.sha256(raw_plan).hexdigest()
    entire_hash = hashlib.sha256(); cases_hash = hashlib.sha256()
    total_bytes = 0; case_bytes = 0; case_count = 0
    summaries = []

    def write_record(stream, value, case_line=False):
        nonlocal total_bytes, case_bytes
        deadline()
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n"
        need(len(raw) <= plan["maximum_case_bytes"], "complete bounded JSONL record")
        need(total_bytes + len(raw) <= plan["maximum_output_bytes"], "whole JSONL output bound")
        need(stream.write(raw) == len(raw), "whole canonical line write")
        stream.flush()
        entire_hash.update(raw); total_bytes += len(raw)
        if case_line:
            cases_hash.update(raw); case_bytes += len(raw)
        deadline()

    with (output / "catalogue-results.jsonl").open("xb") as stream:
        write_record(stream, {"schema": "fixed-3CNF-catalogue-header-v1", "version": VERSION,
                              "plan_sha256": plan_sha, "config": plan,
                              "worker_began_ns": BEGAN, "source_loading_complete_ns": source_loaded,
                              "scope": "Finite same-context clause learning; query catalogue reused, no RL or held-out claim."})
        for index, masks in enumerate(itertools.combinations(range(8), 4)):
            case = make_case(index, masks, modules)
            checking = stamp(); deadline()
            audit = modules["catalogue_verifier"].verify_case(
                case, modules["verifier"].verify_ordinary_result)
            checked = stamp(); deadline()
            need(audit["valid_saved_case"] is True and type(audit["all_boundaries_completed"]) is bool
                 and type(audit["unknown_count"]) is int and audit["unknown_count"] >= 0,
                 "complete independent case audit wire")
            actual_unknown = sum(r["status"] == "UNKNOWN" for r in case["discovery"]) + sum(
                r["status"] == "UNKNOWN" for values in case["arms"].values() for r in values)
            need(audit["unknown_count"] == actual_unknown
                 and audit["all_boundaries_completed"] is (actual_unknown == 0), "honest UNKNOWN coverage")
            row = summarize(case, audit, checked - checking)
            write_record(stream, {"schema": "fixed-3CNF-catalogue-case-record-v1", "case": case,
                                  "independent_verification": audit,
                                  "case_verification_ns": checked - checking}, case_line=True)
            summaries.append(row); case_count += 1
            del case, audit, row
        need(case_count == 70, "complete catalogue EOF")
        discovery_count = sum(sum(row["discovery_outcomes"].values()) for row in summaries)
        replay_count = sum(sum(arm["outcomes"].values())
                           for row in summaries for arm in row["arms"].values())
        need(discovery_count == 420 and replay_count == 1960, "complete observed solve counts")
        complete = all(row["all_boundaries_completed"] for row in summaries)
        write_record(stream, {"schema": "fixed-3CNF-catalogue-completion-v1",
                              "status": "PASS" if complete else "UNKNOWN", "case_count": case_count,
                              "discovery_solves": discovery_count, "replay_solves": replay_count,
                              "case_lines_sha256": cases_hash.hexdigest(), "case_lines_bytes": case_bytes,
                              "preceding_bytes": total_bytes, "preceding_sha256": entire_hash.hexdigest(),
                              "worker_before_footer_ns": stamp(),
                              "native_terminal_and_external_caller_required": True})
    deadline()
    summary = {"schema": "fixed-3CNF-catalogue-summary-v1", "version": VERSION,
               "status": "PASS" if complete else "UNKNOWN", "case_count": case_count,
               "discovery_solves": discovery_count, "replay_solves": replay_count, "cases": summaries,
               "case_lines_sha256": cases_hash.hexdigest(), "case_lines_bytes": case_bytes,
               "catalogue_jsonl_sha256": entire_hash.hexdigest(), "catalogue_jsonl_bytes": total_bytes,
               "plan_sha256": plan_sha, "worker_began_ns": BEGAN,
               "worker_before_summary_ns": stamp(),
               "self_peak_before_summary_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               "ROOT_resource_accepted": False, "full_point_contract_qualified": False,
               "held_out_generalization": False, "RL_used": False, "Q_qualification_changed": False,
               "statistical_speedup_established": False}
    raw_summary = json.dumps(summary, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n"
    need(total_bytes + len(raw_summary) <= plan["maximum_output_bytes"], "whole files bound")
    with (output / "summary.json").open("xb") as stream:
        need(stream.write(raw_summary) == len(raw_summary), "whole summary write")
    deadline()
    print(json.dumps({"status": summary["status"], "case_count": case_count,
                      "discovery_solves": discovery_count, "replay_solves": replay_count,
                      "output_bytes": total_bytes + len(raw_summary)}, sort_keys=True), flush=True)
    deadline()


if __name__ == "__main__":
    need(len(sys.argv) == 2, "sole frozen plan path")
    main(sys.argv[1])
