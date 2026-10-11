"""Prospective full-language point-domain conformance, not target proof search.

Execution requires root review of full-model-plan-v1.json. The actual authored
24-row witness is only a separate low-level point verification control. Neither
it nor its word is read by the generic prefix transaction probes.
"""
import copy
import hashlib
import itertools
import json
import resource
import signal
import sys
import time
from pathlib import Path

import hilbert_primitive_graph_v2 as core

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def assert_pins(plan):
    for p in plan["sources"] + plan["inputs"] + plan["preserved_files"]:
        if core.pin(ROOT / p["path"]) != {k: p[k] for k in ("sha256", "bytes")}:
            raise ValueError("frozen full-model source/input changed: " + p["path"])


def raw_inventory(data):
    # Direct raw prototype representation reconstructed separately from factors.
    codes = {core.canonical(f): i for i, f in enumerate(data["formula_codes"])}
    rows = []
    for index, r in enumerate(data["recipes"]):
        rows.append({"index": index, "id": r["id"], "witness": r["primitive_witness"],
                     "formulas": r["ordered_premise_formulas"],
                     "output": codes[core.canonical(r["primitive_witness"]["formula"])],
                     "inputs": tuple(codes[core.canonical(f)] for f in r["ordered_premise_formulas"])})
    return rows


def raw_point_iterator(g, row, inventory):
    # Enumerate ALL raw offsets then reject by generic point capacity/agreement.
    # No factor count, strict-prior row masks, core point_data or core legal used.
    if g.totals[row] + 1 > 1:
        return
    for recipe in inventory:
        output = (1, row)
        if output in g.marks and g.marks[output] != recipe["output"]:
            continue
        arity = len(recipe["inputs"])
        offsets = itertools.product(range(1 - g.height, 0), repeat=arity) if arity else [()]
        for pair in offsets:
            marking = {output: recipe["output"]}
            refs = []
            valid = True
            for port, (offset, code) in enumerate(zip(pair, recipe["inputs"])):
                source = row + offset
                point = (1, source)
                if point in marking and marking[point] != code:
                    valid = False; break
                marking[point] = code
                marking[(2 + port, row)] = offset
                refs.append(source)
            if not valid or any(p in g.marks and g.marks[p] != v for p, v in marking.items()):
                continue
            key = core.Key(recipe["index"], row, tuple(refs))
            if key in g.excluded[row]:
                continue
            yield key, [[0, row, 1]], [[x, y, v] for (x, y), v in sorted(marking.items())]


def independently_decorate(g, key, inventory, t, m):
    data = inventory[key.recipe]
    command = copy.deepcopy(data["witness"])
    if key.refs:
        command["antecedent"], command["implication"] = key.refs
    prototype = {"recipe_id": data["id"], "primitive_witness": data["witness"],
                 "ordered_premise_formulas": data["formulas"],
                 "relative_ordered_input_offsets": [ref - key.row for ref in key.refs],
                 "orientation": "identity", "t": [[x, y - key.row, v] for x, y, v in t],
                 "m": [[x, y - key.row, v] for x, y, v in m], "marking_version": core.MARKING_VERSION,
                 "formula_registry_sha256": core.digest(g.formulas),
                 "authority_epoch": core.digest({k: v for k, v in g.authority.items() if k != "epoch"})}
    preimage = {"prototype_id": "primitive-prototype-" + core.digest(prototype),
                "prototype_preimage": prototype, "transform": [0, key.row],
                "context_id": core.digest(g.context), "ordered_input_rows": list(key.refs),
                "primitive_command": command, "t": t, "m": m,
                "authority_epoch": prototype["authority_epoch"],
                "formula_registry_sha256": prototype["formula_registry_sha256"]}
    return {"id": "aggregate-primitive-" + core.digest(preimage), "identity_preimage": preimage}


def compare_complete(g, inventory, *, label, representatives=None):
    rows = []
    for row in range(g.height):
        counted, per_recipe = 0, [0] * len(inventory)
        checksum = hashlib.sha256()
        sentinel = object()
        direct = raw_point_iterator(g, row, inventory)
        for implicit, raw in itertools.zip_longest(g.candidates(row), direct, fillvalue=sentinel):
            if implicit is sentinel or raw is sentinel:
                raise AssertionError("complete candidate iterator length mismatch: " + label)
            key, t, m = raw
            if implicit != key or g.point_data(implicit) != (t, m):
                raise AssertionError("complete raw candidate/t/m mismatch: " + label)
            checksum.update((core.canonical([key.data(), t, m]) + "\n").encode())
            counted += 1
            per_recipe[key.recipe] += 1
            if representatives is not None:
                representatives.setdefault((key.recipe, "first"), (key, t, m))
                representatives[(key.recipe, "last")] = (key, t, m)
        assert counted == g.domains[row].count
        assert (counted == 0) == (g.domains[row].count == 0)
        assert (counted == 1) == (g.domains[row].count == 1)
        rows.append({"row": row, "frontier": g.totals[row] < 1, "degree": counted,
                     "per_recipe_degree": per_recipe, "complete_key_t_m_stream_sha256": checksum.hexdigest()})
    return {"label": label, "rows": rows, "candidate_nodes": sum(r["degree"] for r in rows),
            "incidence_edges": sum(r["degree"] for r in rows),
            "frontier_points": sum(r["frontier"] for r in rows),
            "candidate_node_incidence_reason": "each primitive placement has exactly one unit positive-support edge"}


def independent_decision(g, comparison):
    rows = [r for r in comparison["rows"] if r["frontier"]]
    if any(r["degree"] == 0 for r in rows):
        row = min(r["row"] for r in rows if r["degree"] == 0)
        kind, count = "dead", 0
    elif any(r["degree"] == 1 for r in rows):
        row = min(r["row"] for r in rows if r["degree"] == 1)
        kind, count = "forced", 1
    elif not rows:
        return core.Decision("complete", None, 0, None)
    else:
        def generation(r):
            return min([g.roots[r]] + [generation for key, generation in g.selected.items() if key.row == r])
        selected = min(rows, key=lambda r: (generation(r["row"]), r["degree"], r["row"]))
        row, kind, count = selected["row"], "branch", selected["degree"]
    gen = min([g.roots[row]] + [generation for key, generation in g.selected.items() if key.row == row])
    return core.Decision(kind, row, count, gen)


def identity_control(g, key, inventory):
    data = inventory[key.recipe]
    marking = {(1, key.row): data["output"]}
    for port, (ref, code) in enumerate(zip(key.refs, data["inputs"])):
        if (1, ref) in marking and marking[(1, ref)] != code:
            raise ValueError("independent identity control found local conflict")
        marking[(1, ref)] = code
        marking[(2 + port, key.row)] = ref - key.row
    t = [[0, key.row, 1]]
    m = [[x, y, v] for (x, y), v in sorted(marking.items())]
    assert g.point_data(key) == (t, m)
    expected = independently_decorate(g, key, inventory, t, m)
    actual = g.decorate(key)
    assert actual["id"] == expected["id"] and actual["identity_preimage"] == expected["identity_preimage"]
    return {"key": key.data(), "id": actual["id"], "preimage_sha256": core.digest(expected["identity_preimage"])}


def main():
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("full graph conformance alarm")))
    signal.alarm(170)
    planpath = HERE / "full-model-plan-v1.json"
    plan = json.loads(planpath.read_text())
    assert_pins(plan)
    roles = {e["role"]: ROOT / e["path"] for e in plan["inputs"]}
    data = core.read_json(roles["primitive_model"])
    inventory = raw_inventory(data)
    graph = core.frozen_model(ROOT, plan)
    initial_state = graph.semantic_state()
    assert graph.initial_selected == tuple(graph.order) and len(graph.order) == 3
    assert graph.totals == [1, 1, 1] + [0] * 21
    assert all(graph.selected[k] == 0 for k in graph.initial_selected)
    representatives = {}
    comparisons = [compare_complete(graph, inventory, label="initial_complete_universe", representatives=representatives)]
    assert graph.decision() == independent_decision(graph, comparisons[-1])
    identities = [identity_control(graph, p[0], inventory) for _, p in sorted(representatives.items())]
    represented_recipes = {recipe for recipe, _ in representatives}

    # This prefix depends only on the complete graph's stable base ordering. It
    # never loads a solution/witness word and deliberately cannot complete Q.
    checkpoint = graph.checkpoint()
    prefix = []
    for index in range(8):
        decision = graph.decision()
        assert decision == independent_decision(graph, comparisons[-1])
        if decision.kind in ("dead", "complete"):
            break
        key = next(graph.candidates(decision.row))
        identities.append(identity_control(graph, key, inventory))
        core.Executor(graph).step(key)
        assert graph.selected[key] == 1  # Every finite target root remains gen0.
        prefix.append({"key": key.data(), "decision": {"kind": decision.kind, "row": decision.row,
                                                       "count": decision.count, "generation": decision.generation}})
        comparisons.append(compare_complete(graph, inventory, label="prefix_after_" + str(index + 1)))
    assert len(prefix) <= 8 and graph.totals != [1] * 24
    graph.rollback(checkpoint)
    assert graph.semantic_state() == initial_state
    comparisons.append(compare_complete(graph, inventory, label="prefix_full_rollback"))

    # Catalog-only probes: not alternative target-search branches or an executor
    # shortcut. A distant MP reads unfilled prior rows through remote markings.
    mp_key = next(key for row in reversed(range(24)) for key in graph.candidates(row)
                  if graph.recipes[key.recipe].inputs)
    identities.append(identity_control(graph, mp_key, inventory))
    checkpoint = graph.checkpoint()
    graph._apply_legal(mp_key)
    comparisons.append(compare_complete(graph, inventory, label="remote_mp_catalog_transaction"))
    graph.rollback(checkpoint)
    assert graph.semantic_state() == initial_state
    comparisons.append(compare_complete(graph, inventory, label="remote_mp_full_rollback"))
    axiom_index = next(r.index for r in graph.recipes if r.witness["rule"] == "axiom")
    assert graph.recipes[axiom_index].output == 0
    zero_key = core.Key(axiom_index, 3)
    checkpoint = graph.checkpoint()
    assert (1, 3) not in graph.marks
    identities.append(identity_control(graph, zero_key, inventory))
    graph._apply_legal(zero_key)
    assert graph.marks[(1, 3)] == 0
    comparisons.append(compare_complete(graph, inventory, label="assigned_formula_zero_catalog_transaction"))
    graph.rollback(checkpoint)
    assert graph.semantic_state() == initial_state
    comparisons.append(compare_complete(graph, inventory, label="formula_zero_full_rollback"))

    # Read the authored proof ONLY now, after all generic graph probes. This is
    # a separate catalog verification control, never a scheduler search path.
    witness = core.read_json(roles["authored_witness_control"])
    control = core.frozen_model(ROOT, plan)
    witness_ids = []
    for placement in witness["placements"]:
        refs = tuple(placement["ordered_inputs"])
        key = core.Key(control.recipe_index[placement["recipe_id"]], placement["row"], refs)
        actual = control.decorate(key)
        assert actual["command"] == placement["command"]
        assert actual["t"] == placement["t"] and actual["m"] == placement["m"]
        assert actual["id"] == placement["id"] and actual["identity_preimage"] == placement["identity_preimage"]
        witness_ids.append(actual["id"])
        if key not in control.selected:
            control._apply_legal(key)
    point_control = control.point_certificate()
    assert point_control["native_accepted"] is False and len(point_control["placements"]) == 24

    assert_pins(plan)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    result = {"status": "passed_authored_full_primitive_point_graph_controls_pending_independent_audit",
              "plan_sha256": hashlib.sha256(planpath.read_bytes()).hexdigest(),
              "source_bindings": graph.source_bindings, "model_epoch": graph.model_epoch,
              "inventory": {"recipes": len(inventory), "formula_codes": len(graph.formulas),
                            "named_source_definitions_previously_checked": 171},
              "initial_semantic_state_sha256": core.digest(initial_state),
              "complete_comparisons": comparisons, "complete_state_count": len(comparisons),
              "all_candidate_comparisons": sum(c["candidate_nodes"] for c in comparisons),
              "lazy_identity_checks": identities, "represented_recipe_count": len(represented_recipes),
              "generic_prefix": prefix, "generic_prefix_not_target_search": True,
              "catalog_only_probes": {"remote_mp_key": mp_key.data(), "formula_zero_key": zero_key.data()},
              "authored_witness_control": {"rows": 24, "full_id_stream_sha256": core.digest(witness_ids),
                  "point_certificate_sha256": core.digest(point_control),
                  "status": "read_only_authored_catalog_replay_not_discovered_or_reference_search_path",
                  "existing_independent_whole_primitive_logical_audit": core.pin(roles["primitive_logical_audit"]),
                  "fresh_native_acceptance": False},
              "metrics_are_cumulative_authored_probe_work": graph.metrics,
              "kernel_peak_rss_bytes_before_write": peak,
              "worker_seconds_before_write": time.perf_counter() - started,
              "new_geometry_target_searches": 0, "new_native_queries": 0,
              "native_engine_or_authority_activation": False, "new_RL_training": False,
              "cluster_continuation": "not established; v2 immutable preference-set scope gap retained",
              "logical_native_compiler_correspondence": "finite prior source logical audit bound; native/compiler correspondence open",
              "source_authoring_wall_cost": "not instrumented, not zero"}
    path = HERE / "full-model-outcome-v1.json"
    if path.exists():
        raise ValueError("immutable full-model result exists")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "complete_states": len(comparisons),
                      "all_candidate_comparisons": result["all_candidate_comparisons"],
                      "lazy_identity_checks": len(identities), "represented_recipes": len(represented_recipes),
                      "kernel_peak_rss_bytes": peak, "geometry_target_searches": 0, "native_queries": 0}))


if __name__ == "__main__":
    main()
