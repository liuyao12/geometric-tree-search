"""Synthetic point-contract fixtures; never loads the actual geometry model.

The direct enumerator below does not call Graph.point_data, factors, legal,
decorate or candidates when constructing or accepting a raw placement.
"""
import copy
import itertools
import json
import resource
import signal
import sys
import time
from pathlib import Path

import hilbert_primitive_graph_v1 as core

HERE = Path(__file__).resolve().parent
P, Q, R = ["pred", "P", []], ["pred", "Q", []], ["pred", "R", []]
IMP = ["imp", P, Q]
FORMULAS = [P, Q, IMP, R]


def recipe(name, formula, premises=(), rule="fixture_zero"):
    return {"id": "synthetic-" + name,
            "primitive_witness": {"rule": rule, "formula": copy.deepcopy(formula), "fixture_name": name},
            "ordered_premise_formulas": copy.deepcopy(list(premises))}


RECIPES = [recipe("p-first", P), recipe("q", Q), recipe("imp", IMP), recipe("p-second", P),
           recipe("literal-mp", Q, [P, IMP], "mp"),
           recipe("equal-ordered-port-fixture", Q, [P, P], "opaque_pair")]


def graph(height=3, *, recipes=RECIPES, formulas=FORMULAS, marks=(), roots=None):
    authority = {"label": "synthetic_point_fixture_not_logic", "activated": False, "native_accepted": False}
    authority["epoch"] = core.digest(authority)
    return core.PointGraph(height=height, formulas=formulas, recipe_data=recipes,
                           context={"ordered_local_premises": [], "fixture": True}, authority=authority,
                           fixed_marks=[(1, r, -1) for r in range(1 - height, 0)] + list(marks),
                           roots=roots, fixture=True)


def raw_points(data, row, offsets, formulas):
    codes = {core.canonical(f): k for k, f in enumerate(formulas)}
    witness = data["primitive_witness"]
    values = {(1, row): codes[core.canonical(witness["formula"])]}
    refs = []
    for port, (offset, formula) in enumerate(zip(offsets, data["ordered_premise_formulas"])):
        source = row + offset
        code = codes[core.canonical(formula)]
        if (1, source) in values and values[(1, source)] != code:
            return None
        values[(1, source)] = code
        values[(2 + port, row)] = offset
        refs.append(source)
    return [[0, row, 1]], [[x, y, v] for (x, y), v in sorted(values.items())], tuple(refs)


def raw_domain(g, row, recipe_data=RECIPES):
    result = {}
    if g.totals[row] == 1:
        return result
    for index, data in enumerate(recipe_data):
        arity = len(data["ordered_premise_formulas"])
        offsets = itertools.product(range(1 - g.height, 0), repeat=arity) if arity else [()]
        for offset in offsets:
            points = raw_points(data, row, offset, g.formulas)
            if points is None:
                continue
            t, m, refs = points
            if any((x, y) in g.marks and g.marks[(x, y)] != v for x, y, v in m):
                continue
            # These exterior sentinel checks, not a strict-prior generator shortcut,
            # remove all translated prototypes whose referenced rows are negative.
            key = core.Key(index, row, refs)
            if key not in g.excluded[row]:
                result[key] = (t, m)
    return result


def compare(g, recipe_data=RECIPES, with_ids=False):
    checked = 0
    for row in range(g.height):
        direct = raw_domain(g, row, recipe_data)
        implicit = list(g.candidates(row))
        assert implicit == sorted(direct), "full iterator order/set differs from raw prototype enumeration"
        assert len(implicit) == g.domains[row].count
        assert (len(implicit) == 0) == (g.domains[row].count == 0)
        assert (len(implicit) == 1) == (g.domains[row].count == 1)
        for key in implicit:
            assert g.point_data(key) == direct[key]
            if with_ids:
                actual = g.decorate(key)
                data = recipe_data[key.recipe]
                t, m = direct[key]
                witness = copy.deepcopy(data["primitive_witness"])
                command = copy.deepcopy(witness)
                if key.refs:
                    if witness["rule"] == "mp":
                        command.update(antecedent=key.refs[0], implication=key.refs[1])
                    else:
                        command["ordered_refs"] = list(key.refs)
                proto = {"recipe_id": data["id"], "primitive_witness": witness,
                         "ordered_premise_formulas": data["ordered_premise_formulas"],
                         "relative_ordered_input_offsets": [r - key.row for r in key.refs],
                         "orientation": "identity", "t": [[x, y - key.row, v] for x, y, v in t],
                         "m": [[x, y - key.row, v] for x, y, v in m],
                         "marking_version": core.MARKING_VERSION, "formula_registry_sha256": g.registry_sha,
                         "authority_epoch": g.authority_epoch}
                full = {"prototype_id": "primitive-prototype-" + core.digest(proto),
                        "prototype_preimage": proto, "transform": [0, key.row], "context_id": g.context_id,
                        "ordered_input_rows": list(key.refs), "primitive_command": command, "t": t, "m": m,
                        "authority_epoch": g.authority_epoch, "formula_registry_sha256": g.registry_sha}
                assert actual["identity_preimage"] == full
                assert actual["id"] == "aggregate-primitive-" + core.digest(full)
            checked += 1
    return checked


def must_reject(call):
    try:
        call()
    except (ValueError, TypeError, IndexError):
        return
    raise AssertionError("negative fixture was accepted")


def main():
    start = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("synthetic gate child alarm")))
    signal.alarm(55)
    records = []
    def passed(name, **extra):
        records.append({"name": name, "status": "passed", **extra})

    comparisons, candidates = 0, 0
    ports = [()] + [(x, row, value) for x in (2, 3) for row in range(3) for value in (0, -1, -2)]
    for values in itertools.product((None, 0, 1, 2), repeat=3):
        formula_marks = [(1, row, value) for row, value in enumerate(values) if value is not None]
        for port in ports:
            g = graph(marks=formula_marks + ([port] if port else []))
            candidates += compare(g)
            comparisons += 1
    passed("exhaustive_tiny_raw_prototypes_formula_and_remote_port_states", states=comparisons,
           accepted_placements_compared=candidates, includes_zero_absent_negative_exterior=True)
    g = graph()
    identity_candidates = compare(g, with_ids=True)
    passed("lazy_full_decorated_identity_raw_reconstruction", candidates=identity_candidates)

    a = core.Key(4, 2, (0, 1)); b = core.Key(4, 2, (1, 0))
    assert g.decorate(a)["id"] != g.decorate(b)["id"]
    assert g.decorate(core.Key(0, 1))["id"] != g.decorate(core.Key(3, 1))["id"]
    passed("same_output_distinct_ordered_refs_and_recipe_witnesses")
    repeated = core.Key(5, 2, (0, 0))
    assert g.legal(repeated) and g.point_data(repeated)[1].count([1, 0, 0]) == 1
    assert [2, 2, -2] in g.point_data(repeated)[1] and [3, 2, -2] in g.point_data(repeated)[1]
    assert not g.legal(core.Key(4, 2, (0, 0)))
    passed("equal_premise_repeated_ordered_ports_retained_distinct_premises_conflict")

    g = graph(marks=[(1, 0, 1), (1, 2, 999)])
    assert g.domains[0].count == 1 and g.decision().kind == "dead" and g.decision().row == 2
    passed("global_distant_dead_before_local_forced")
    g = graph(marks=[(1, 2, 2)])
    assert g.domains[0].count > 1 and g.decision().kind == "forced" and g.decision().row == 2
    passed("global_forced_before_earlier_branch")
    g = graph(marks=[(1, 1, 0), (1, 2, 0)], roots=(0, 5, 5))
    assert g.domains[0].count > g.domains[1].count > 1 and g.decision().row == 0
    core.Executor(g).step(core.Key(0, 0))
    assert g.selected[core.Key(0, 0)] == 1 and g.point_generation(0) == 0
    passed("earliest_generation_before_degree_and_root_generation_not_visit_index")

    g = graph()
    before = g.semantic_state(); checkpoint = g.checkpoint()
    g._apply_legal(core.Key(0, 0))
    compare(g)
    old = g.domains[2].count
    g._apply_legal(core.Key(2, 1))
    assert g.domains[2].count != old
    compare(g)
    excluded = next(g.candidates(2))
    g.exclude_failed_child(excluded)
    compare(g)
    child = g.checkpoint(); child_state = g.semantic_state()
    g._apply_legal(next(g.candidates(2)))
    g.rollback(child)
    assert g.semantic_state() == child_state
    g.rollback(checkpoint)
    assert g.semantic_state() == before
    passed("distant_dependency_updates_and_exact_nested_rollback_with_mark_reference_counts_and_exclusions")

    zero = graph(marks=[(2, 2, 0)])
    absent = graph()
    assert all(k.recipe != 4 for k in zero.candidates(2))
    assert any(k.recipe == 4 for k in absent.candidates(2))
    assert any(k.recipe == 0 for k in zero.candidates(2))
    assert graph(marks=[(1, 0, 0)]).domains[0].count < graph().domains[0].count
    passed("assigned_zero_is_not_absence_and_unused_ports_remain_absent")

    g = graph()
    key = core.Key(0, 0)
    assert g.validate_cluster([key, key], g.model_epoch) == (key,)
    must_reject(lambda: g.validate_cluster([key, core.Key(3, 0)], g.model_epoch))
    must_reject(lambda: g.validate_cluster([key], "stale-epoch"))
    g._apply_legal(key)
    assert g.validate_cluster([key, key], g.model_epoch) == (key,)
    passed("shared_exact_identity_once_and_distinct_overcapacity_stale_authority_rejected")

    g = graph(marks=[(1, 2, 2)])
    proposal = core.Key(0, 0)
    assert g.validate_cluster([proposal], g.model_epoch) == (proposal,)
    must_reject(lambda: core.Executor(g).step(proposal))
    allkeys = list(g.candidates(0))
    reordered = list(g.candidates_with_preferences(0, [allkeys[-1]]))
    assert reordered[0] == allkeys[-1] and set(reordered) == set(allkeys) and len(reordered) == len(allkeys)
    passed("valid_ineligible_hint_cannot_bypass_scheduler_complete_base_fallback")

    corrupted = copy.deepcopy(RECIPES)
    corrupted[4]["ordered_premise_formulas"][1] = ["imp", Q, Q]
    must_reject(lambda: graph(recipes=corrupted, formulas=FORMULAS + [["imp", Q, Q]]))
    for marks in ([(1, 0, True)], [(True, 0, 0)], [(1, False, 0)]):
        must_reject(lambda marks=marks: graph(marks=marks))
    must_reject(lambda: graph(height=True))
    must_reject(lambda: graph(formulas=FORMULAS + [P]))
    passed("logical_invalid_but_mark_consistent_mp_boolean_values_and_noninjective_registry_rejected")

    # A synthetic four-row boundary creates a genuine failed branch under the
    # reference generation order. This is not a geometry target search.
    tinyrecipes = [recipe("irrelevant-r-first", R), recipe("p", P), recipe("imp", IMP),
                   recipe("mp", Q, [P, IMP], "mp")]
    g = graph(4, recipes=tinyrecipes, marks=[(1, 3, 1)], roots=(0, 0, 0, 5))
    initial = g.semantic_state()
    unknown = core.Executor(g).solve(max_attempts=0, seconds=1)
    assert unknown["status"] == "unknown_budget" and g.semantic_state() == initial
    solved = core.Executor(g).solve(max_attempts=100, seconds=2)
    assert solved["status"] == "finite_exact_point_tiling" and g.metrics["backtracks"] > 0
    assert solved["certificate"]["native_accepted"] is False
    compare(g, tinyrecipes)
    passed("synthetic_executor_failed_child_parent_exclusion_budget_unknown_and_exact_point_reconstruction",
           attempts=solved["attempts"], backtracks=g.metrics["backtracks"])

    # Exhausted synthetic marked region has no target-supporting zero/MP type.
    g = graph(2, recipes=[recipe("p-only", P)], marks=[(1, 1, 1)])
    initial = g.semantic_state()
    exhausted = core.Executor(g).solve(max_attempts=100, seconds=1)
    assert exhausted["status"] == "exhausted_finite_marked_subtree" and g.semantic_state() == initial
    passed("exhausted_finite_marked_fixture_is_not_unrestricted_theorem_nonprovability")

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    outcome = {"status": "passed_authored_synthetic_point_kernel_fixtures_pending_independent_gate",
               "records": records, "fixture_count": len(records), "states": comparisons,
               "compared_placements": candidates, "seconds_before_write": time.perf_counter() - start,
               "child_kernel_peak_rss_bytes_before_write": peak,
               "actual_geometry_model_loaded": False, "actual_geometry_graph_constructed": False,
               "actual_geometry_target_searches": 0, "native_queries": 0,
               "native_authority_activated": False,
               "remaining": ["independent synthetic kernel replay", "actual full-model conformance gate",
                             "independent decoded whole logical certificates", "native/compiler correspondence"]}
    (HERE / "fixtures-outcome-v1.json").write_text(json.dumps(outcome, indent=2) + "\n")
    print(json.dumps({"status": outcome["status"], "fixtures": len(records), "states": comparisons,
                      "compared_placements": candidates, "kernel_peak_rss_bytes": peak}))


if __name__ == "__main__":
    main()
