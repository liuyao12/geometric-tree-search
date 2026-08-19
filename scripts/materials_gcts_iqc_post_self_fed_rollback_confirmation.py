#!/usr/bin/env python3
"""One-shot spatial confirmation of the frozen two-marking rollback rule.

The candidate phase has no target/scorer argument.  It selects a first block
with the already-frozen fusion runtime, constructs the second-block marking
portfolio, executes the public 12-step discharge rule on both retained states,
and hashes the complete receipt.  Only then may ``_TargetGate.open`` construct
the confirmation target exactly once for posthoc scoring.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import math
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_child_frontier_graph_value import (
    ChildFrontierGraphExample, ChildFrontierGraphUtilityExample,
    fit_child_frontier_graph_utility_value, fit_child_frontier_graph_value,
    score_child_frontier_graph_utility_value,
    score_child_frontier_graph_value)
from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, percentile_ranks,
    select_equivariant_port_fusion)
from materials_gcts_iqc_frozen_fusion_artifact import (
    canonical_json, fusion_value_from_payload)
from materials_gcts_iqc_frozen_fusion_runtime import (
    COLORS, FusionSearchState, _child, _local_section, _partial, action_key,
    branch_features, freeze_nucleus, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_post_self_fed_child_graph_dataset import (
    terminal_child_graph)
from materials_gcts_iqc_post_self_fed_child_graph_value import (
    SPEC as CHILD_SPEC, _load_examples as _load_graph_examples)
from materials_gcts_iqc_post_self_fed_fusion_value import (
    load_default_result as load_base_result)
from materials_gcts_iqc_post_self_fed_marking_portfolio import (
    load_default_result as load_portfolio_result)
from materials_gcts_iqc_post_self_fed_port_discharge_dataset import _rollout
from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST, MANIFEST,
    MAXIMUM_RETAINED_CANDIDATES, ROLLBACK_HORIZON, ROLLBACK_METRIC,
    SECOND_BLOCK_RADIUS, SEED_RADIUS, TARGET_OPEN_LIMIT, TARGET_RADIUS,
    validate_preregistration)
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_recurrent_prototype_connection_audit import _bounded
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    OUTER_ORACLE_LIFT_BOUND, terminal_successor_features)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, _crop)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_recursive_connections import local_cluster_types


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_rollback_confirmation_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = ""
EXPECTED_RESULT_DIGEST = ""
HARNESS_LOGIC_COMMIT = "6200ec60d11d2fc308b988bbcf2f3492ac6e1ef9"


def _key(point):
    return tuple(round(value, 6) for value in point)


def _minimum_distance(positions):
    return min(math.dist(left, right)
               for index, left in enumerate(positions)
               for right in positions[index + 1:]
               if math.dist(left, right) > 1e-8)


def _colored_digest(positions, species):
    return hashlib.sha256(repr(tuple(sorted(
        (tuple(map(float, point)), str(color))
        for point, color in zip(positions, species)))).encode()).hexdigest()


def _replay_first_terminal(source, runtime, actions):
    """Recover a selected state from its three frozen exact actions."""
    prototypes = local_cluster_types(
        source.seed_positions, source.seed_species, CLUSTER_EDGES)
    frontier = _bounded(runtime["connection"], source, prototypes)
    initial = FusionSearchState(
        tuple(source.seed_positions), tuple(source.seed_species), frontier,
        (), (), (), 0., ())
    expected = action_key(actions)
    matches = []
    for order in itertools.permutations(expected):
        state = initial
        valid = True
        for point, color in order:
            if point not in state.proposals.votes:
                valid = False
                break
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            child = _child(
                source, runtime["connection"], runtime["state_model"], state,
                point, descriptors[point], TARGET_RADIUS)
            if child.actions[-1][1] != color:
                valid = False
                break
            state = child
        if valid and action_key(state.actions) == expected:
            matches.append(state)
    unique = {(_colored_digest(state.positions, state.species),
               action_key(state.actions)): state for state in matches}
    if len(unique) != 1:
        raise AssertionError("selected first terminal lacks unique replay")
    return next(iter(unique.values()))


def _second_block_candidates(source, states, runtime):
    base = load_base_result()
    base_model = fusion_value_from_payload(base["final_model_payload"])
    portfolio = load_portfolio_result()
    graph_rows, _graph_data = _load_graph_examples()
    topology = fit_child_frontier_graph_value(tuple(
        ChildFrontierGraphExample(row.group, row.graph, row.exact)
        for row in graph_rows), CHILD_SPEC)
    utility = fit_child_frontier_graph_utility_value(tuple(
        ChildFrontierGraphUtilityExample(
            row.group, row.graph, row.correct_sites)
        for row in graph_rows), CHILD_SPEC)
    if (topology.model_digest != portfolio["final_topology_model_digest"]
            or utility.model_digest !=
            portfolio["final_utility_model_digest"]
            or base_model.model_digest != portfolio["base_fusion_model_digest"]):
        raise AssertionError("frozen marking portfolio model drift")

    minimum = _minimum_distance(source.seed_positions)
    rows = []
    for stable_index, state in enumerate(states):
        partial, graph = _partial(
            source, state, runtime["grouped_vocabulary"])
        features = (tuple(branch_features(state)) + _local_section(state)
                    + partial + terminal_successor_features(
                        state, runtime["state_model"], source.group,
                        SECOND_BLOCK_RADIUS))
        colors = tuple(color for _point, color in state.actions)
        child_graph = terminal_child_graph(
            source, state, runtime, minimum)
        rows.append({
            "stable_index": stable_index,
            "state": state,
            "features": features,
            "colors": colors,
            "partial_graph": graph,
            "child_graph": child_graph,
        })
    base_candidates = tuple(EquivariantPortFusionCandidate(
        row["features"], row["colors"], row["partial_graph"],
        row["stable_index"]) for row in rows)
    base_selection = select_equivariant_port_fusion(
        base_model, base_candidates)
    base_rank = percentile_ranks(base_selection.fused_scores)
    topology_scores = tuple(score_child_frontier_graph_value(
        topology, row["child_graph"]) for row in rows)
    utility_scores = tuple(score_child_frontier_graph_utility_value(
        utility, row["child_graph"]) for row in rows)
    topology_order = tuple(sorted(range(len(rows)), key=lambda index: (
        -topology_scores[index], rows[index]["stable_index"])))
    utility_rank = percentile_ranks(utility_scores)
    yield_order = tuple(sorted(range(len(rows)), key=lambda index: (
        -(base_rank[index] + utility_rank[index]),
        rows[index]["stable_index"])))
    retained = []
    for marking, index in (("typed-child-topology", topology_order[0]),
                           ("local-section+ordinal-yield", yield_order[0])):
        stable = rows[index]["stable_index"]
        if any(row["stable_index"] == stable for row in retained):
            continue
        retained.append({**rows[index], "marking": marking})
    if not retained or len(retained) > MAXIMUM_RETAINED_CANDIDATES:
        raise AssertionError("invalid frozen rollback portfolio width")
    candidate_digest = hashlib.sha256(repr(tuple(
        (row["stable_index"], action_key(row["state"].actions),
         row["features"], row["colors"],
         row["partial_graph"].canonical_digest,
         row["child_graph"].canonical_digest)
        for row in rows)).encode()).hexdigest()
    return tuple(rows), tuple(retained), candidate_digest, {
        "topology_model_digest": topology.model_digest,
        "utility_model_digest": utility.model_digest,
        "base_model_digest": base_model.model_digest,
    }


def _trace_score(trace):
    if ROLLBACK_METRIC != "frontier_vote_mass":
        raise AssertionError("unsupported preregistered rollback metric")
    steps = trace["steps"]
    if not steps:
        return 0.
    used = steps[:min(ROLLBACK_HORIZON, len(steps))]
    return float(used[-1]["frontier_vote_mass_after"])


class _TargetGate:
    def __init__(self):
        self.open_count = 0

    def open(self):
        if self.open_count >= TARGET_OPEN_LIMIT:
            raise AssertionError("confirmation target may open exactly once")
        self.open_count += 1
        physical = math.ceil(math.dist((0., 0., 0.), CONFIRMATION_CENTER)
                             + SECOND_BLOCK_RADIUS)
        oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
        check, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND + 1, physical)
        target = _crop(
            oracle, CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS,
            "IQC-rollback-confirmation-target")
        stable = _crop(
            check, CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS,
            "IQC-rollback-confirmation-target-bound-check")
        if (_colored_digest(target.positions, target.species)
                != _colored_digest(stable.positions, stable.species)):
            raise AssertionError("confirmation target lift bound is unstable")
        return target


def evaluate():
    if validate_preregistration() != EXPECTED_MANIFEST_DIGEST:
        raise AssertionError("confirmation preregistration unavailable")
    runtime = load_default_runtime()

    # Construct only the small seed crop before the target gate opens.
    seed_physical = math.ceil(math.dist((0., 0., 0.), CONFIRMATION_CENTER)
                              + SEED_RADIUS)
    seed_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND, seed_physical)
    seed = _crop(seed_oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-rollback-confirmation-seed")
    source = SimpleNamespace(
        group=CONFIRMATION_CENTER, seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species))
    first = freeze_nucleus(
        runtime, center=CONFIRMATION_CENTER,
        seed_positions=source.seed_positions,
        seed_species=source.seed_species, target_radius=TARGET_RADIUS)
    selected_first = first.terminals[first.fusion_stable_index]
    first_state = _replay_first_terminal(
        source, runtime, selected_first.actions)
    second_source = SimpleNamespace(
        group=CONFIRMATION_CENTER, seed_positions=first_state.positions,
        seed_species=first_state.species)
    second_states, second_counts = _complete_states_at_radius(
        second_source, runtime, SECOND_BLOCK_RADIUS)
    second_states = tuple(sorted(
        second_states, key=lambda state: action_key(state.actions)))
    rows, retained, second_digest, model_digests = \
        _second_block_candidates(second_source, second_states, runtime)
    traced = []
    for row in retained:
        trace = _rollout(second_source, row["state"], runtime)
        traced.append({
            "stable_index": row["stable_index"],
            "marking": row["marking"],
            "actions": action_key(row["state"].actions),
            "trace": trace,
            "rollback_score": _trace_score(trace),
        })
    selected = min(traced, key=lambda row: (
        -row["rollback_score"], row["stable_index"]))
    receipt = {
        "schema_version": 1,
        "preregistration_digest": EXPECTED_MANIFEST_DIGEST,
        "harness_logic_commit": HARNESS_LOGIC_COMMIT,
        "center": CONFIRMATION_CENTER,
        "seed_atoms": len(seed.positions),
        "seed_digest": _colored_digest(seed.positions, seed.species),
        "first_candidate_digest": first.candidate_digest,
        "first_candidate_counts": first.candidate_counts_by_depth,
        "first_retained_counts": first.retained_counts_by_depth,
        "first_selected_stable_index": first.fusion_stable_index,
        "first_selected_actions": action_key(first_state.actions),
        "first_selected_state_digest": _colored_digest(
            first_state.positions, first_state.species),
        "second_candidate_counts": second_counts,
        "second_candidate_count": len(rows),
        "second_candidate_digest": second_digest,
        "model_digests": model_digests,
        "retained": traced,
        "selected_second_stable_index": selected["stable_index"],
        "rollback_metric": ROLLBACK_METRIC,
        "rollback_horizon": ROLLBACK_HORIZON,
        "target_open_count_before_receipt": 0,
        "target_used": False,
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()

    gate = _TargetGate()
    if gate.open_count != 0:
        raise AssertionError("target gate opened before receipt")
    target = gate.open()
    truth = {_key(point): str(color) for point, color in
             zip(target.positions, target.species)}
    first_correct = sum(truth.get(_key(point)) == color
                        for point, color in first_state.actions)
    selected_state = second_states[selected["stable_index"]]
    second_correct = sum(truth.get(_key(point)) == color
                         for point, color in selected_state.actions)
    retained_scored = tuple({
        "stable_index": row["stable_index"],
        "exact": all(truth.get(_key(point)) == color
                     for point, color in row["actions"]),
        "correct_actions": sum(truth.get(_key(point)) == color
                               for point, color in row["actions"]),
    } for row in traced)
    portfolio_contains_exact = any(row["exact"] for row in retained_scored)
    selected_exact = second_correct == len(selected_state.actions)
    separation = min(math.dist(CONFIRMATION_CENTER, center)
                     for center in MANIFEST["prior_centers"])
    domain_disjoint = separation > MANIFEST[
        "minimum_required_domain_separation"]
    gates = {
        "first_block_exact_actions": first_correct == 3,
        "portfolio_contains_exact_second_block": portfolio_contains_exact,
        "rollback_selected_exact_second_block": selected_exact,
        "end_to_end_correct_actions": first_correct + second_correct == 6,
        "target_open_count": gate.open_count == TARGET_OPEN_LIMIT,
        "raw_training_target_domains_disjoint": domain_disjoint,
    }
    success = all(gates.values())
    body = {
        "schema_version": 1,
        "preregistration_digest": EXPECTED_MANIFEST_DIGEST,
        "harness_logic_commit": HARNESS_LOGIC_COMMIT,
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "target_open_count": gate.open_count,
        "target_atoms": len(target.positions),
        "target_digest": _colored_digest(target.positions, target.species),
        "minimum_prior_center_separation": separation,
        "domain_disjoint": domain_disjoint,
        "first_correct_actions": first_correct,
        "second_correct_actions": second_correct,
        "end_to_end_correct_actions": first_correct + second_correct,
        "retained_posthoc_scores": retained_scored,
        "portfolio_contains_exact_second_block": portfolio_contains_exact,
        "rollback_selected_exact_second_block": selected_exact,
        "success_gates": gates,
        "fresh_confirmation_passed": success,
        "autonomous_finite_two_block_commit_gate_passed": success,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or body["preregistration_digest"] != EXPECTED_MANIFEST_DIGEST
            or body["harness_logic_commit"] != HARNESS_LOGIC_COMMIT
            or body["receipt"]["target_used"]
            or body["receipt"]["target_open_count_before_receipt"] != 0
            or hashlib.sha256(canonical_json(body["receipt"])).hexdigest()
            != body["receipt_digest"]
            or body["target_open_count"] != TARGET_OPEN_LIMIT
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("rollback confirmation result drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("rollback confirmation digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("rollback confirmation fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
