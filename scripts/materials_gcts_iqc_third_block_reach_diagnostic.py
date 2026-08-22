#!/usr/bin/env python3
"""Consumed-target reach diagnosis for missing IQC third-block supply.

The frozen third-block audit found exact retained parents in two nuclei but no
exact terminal anywhere in their bounded ``8×8×8`` trees.  This diagnostic is
allowed to use those already-consumed targets to follow *only correct* prefix
actions through the unchanged frontier.  It reports the marking rank required
at every step and the minimum uniform reach that would have exposed one exact
three-action path.  It is diagnosis only: target-guided branches are never
returned as a deployable search policy.
"""

from __future__ import annotations

import argparse
import gzip
import heapq
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_iqc_child_option_third_block_audit import (
    EXPECTED_RESULT_DIGEST as SOURCE_RESULT_DIGEST, THIRD_BLOCK_RADIUS,
    load_default_result as load_source_result)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, action_key, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _bounded_at_radius, _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE as TERMINAL_SOURCE_FIXTURE,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_TERMINAL_SOURCE_SHA256,
    OUTER_ORACLE_LIFT_BOUND, SECOND_BLOCK_RADIUS, load_fixture_json,
    validate_dataset as validate_terminal_source)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, _crop)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_pose_port_state_marking import score_pose_port_state
from materials_gcts_recursive_connections import local_cluster_types


MISSING_SUPPLY_GROUPS = (1, 2)
CURRENT_REACH = 8
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_third_block_reach_diagnostic_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "f63d612fd39e772ca2f9f6e0030375f5c4ade12f3734e7c1158c08686b736d94"
EXPECTED_RESULT_DIGEST = \
    "784652f5712342b33aac955f3aacc39058b33606d1a53f4ab52bf8a26efefb79"


@dataclass(frozen=True)
class ParentReach:
    group: int
    parent_stable_index: int
    expanded_states_by_depth: tuple[int, ...]
    ranked_candidates_by_depth: tuple[int, ...]
    correct_actions_seen_by_depth: tuple[int, ...]
    minimum_correct_rank_seen_by_depth: tuple[int | None, ...]
    maximum_correct_rank_seen_by_depth: tuple[int | None, ...]
    minimum_uniform_reach_for_exact_path: int | None
    minimum_rank_sum_for_exact_path: int | None
    current_reach_supplies_exact_path: bool
    frontier_geometry_has_exact_path: bool


def _key(point):
    return tuple(round(float(value), 6) for value in point)


def _state_key(state):
    """Quotient action-order permutations by the resulting colored cloud.

    The live search deliberately exposes commuting placements as one visible
    update while retaining a tree underneath.  For reach diagnosis, however,
    two correct prefixes that emit the same colored sites have the same future
    frontier.  Keeping both action histories creates a factorial blow-up and
    cannot improve either the minimum maximum rank or the minimum rank sum.
    """
    return tuple(sorted((str(color), *_key(point))
                        for point, color in zip(
                            state.positions, state.species)))


def _reconstruct_parents(group_index, parent_ids, seed, source_group, runtime):
    seed_source = SimpleNamespace(
        group=DEVELOPMENT_CENTERS[group_index],
        seed_positions=tuple(seed.positions), seed_species=tuple(seed.species))
    first_states, _ = _complete_states_at_radius(
        seed_source, runtime, TARGET_RADIUS)
    inherited = tuple(state for state in first_states if hashlib.sha256(
        repr(action_key(state.actions)).encode()).hexdigest()
        == source_group["inherited_action_digest"])
    if len(inherited) != 1:
        raise AssertionError("reach diagnostic inherited state drift")
    source = SimpleNamespace(
        group=DEVELOPMENT_CENTERS[group_index],
        seed_positions=inherited[0].positions,
        seed_species=inherited[0].species)
    states, counts = _complete_states_at_radius(
        source, runtime, SECOND_BLOCK_RADIUS)
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    if tuple(counts) != tuple(source_group["second_block_counts"]):
        raise AssertionError("reach diagnostic parent universe drift")
    return tuple((parent_id, states[parent_id]) for parent_id in parent_ids)


def _diagnose(group_index, parent_id, parent, truth, runtime):
    source = SimpleNamespace(
        group=DEVELOPMENT_CENTERS[group_index],
        seed_positions=parent.positions, seed_species=parent.species)
    frontier = _bounded_at_radius(
        runtime["connection"], source,
        local_cluster_types(source.seed_positions, source.seed_species,
                            CLUSTER_EDGES), THIRD_BLOCK_RADIUS)
    initial = FusionSearchState(
        tuple(source.seed_positions), tuple(source.seed_species), frontier,
        (), (), (), 0., ())
    # Uniform-cost search over the lexicographic path cost
    # (maximum local rank, rank sum).  Candidate edges are expanded lazily, so
    # a rank-100 child is never rendered while a rank-9 solution remains in
    # the queue.  Canonical colored-state keys quotient commuting action
    # permutations without changing any frontier geometry.
    expanded = [0, 0, 0]
    ranked = [0, 0, 0]
    correct_seen = [0, 0, 0]
    correct_ranks = [[], [], []]
    expansion_cache = {}
    best = {(_state_key(initial), 0): (0, 0)}
    queue = []
    serial = 0

    def push(cost, kind, payload):
        nonlocal serial
        serial += 1
        heapq.heappush(queue, (cost[0], cost[1], serial, kind, payload))

    push((0, 0), "state", (initial, 0))
    solution = None
    while queue:
        maximum, total, _serial, kind, payload = heapq.heappop(queue)
        cost = (maximum, total)
        if kind == "state":
            state, depth = payload
            state_key = _state_key(state)
            if best.get((state_key, depth)) != cost:
                continue
            if depth == 3:
                solution = cost
                break
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
                -score_pose_port_state(
                    runtime["state_model"], descriptors[point]),
                -state.proposals.votes[point], point)))
            actions = tuple((rank, point, descriptors[point])
                            for rank, point in enumerate(ordered, 1)
                            if truth.get(_key(point)) == str(
                                _dominant_source_color(
                                    state.proposals, point)))
            expansion_cache[(state_key, depth)] = actions
            expanded[depth] += 1
            ranked[depth] += len(ordered)
            correct_seen[depth] += len(actions)
            correct_ranks[depth].extend(rank for rank, _point, _ in actions)
            if actions:
                rank, _point, _descriptor = actions[0]
                edge_cost = (max(maximum, rank), total + rank)
                push(edge_cost, "edge", (state, state_key, depth, cost, 0))
            continue

        state, state_key, depth, base_cost, action_index = payload
        if best.get((state_key, depth)) != base_cost:
            continue
        actions = expansion_cache[(state_key, depth)]
        rank, point, descriptor = actions[action_index]
        child = _child(
            source, runtime["connection"], runtime["state_model"], state,
            point, descriptor, THIRD_BLOCK_RADIUS)
        child_cost = (max(base_cost[0], rank), base_cost[1] + rank)
        child_key = _state_key(child)
        old = best.get((child_key, depth + 1))
        if old is None or child_cost < old:
            best[(child_key, depth + 1)] = child_cost
            push(child_cost, "state", (child, depth + 1))
        next_index = action_index + 1
        if next_index < len(actions):
            next_rank = actions[next_index][0]
            next_cost = (max(base_cost[0], next_rank),
                         base_cost[1] + next_rank)
            push(next_cost, "edge", (
                state, state_key, depth, base_cost, next_index))

    minimum_uniform = solution[0] if solution else None
    minimum_sum = solution[1] if solution else None
    return ParentReach(
        group_index, parent_id, tuple(expanded), tuple(ranked),
        tuple(correct_seen),
        tuple(min(values) if values else None for values in correct_ranks),
        tuple(max(values) if values else None for values in correct_ranks),
        minimum_uniform, minimum_sum,
        minimum_uniform is not None and minimum_uniform <= CURRENT_REACH,
        solution is not None)


def evaluate():
    source = load_source_result()
    if source["result_digest"] != SOURCE_RESULT_DIGEST:
        raise AssertionError("third-block source result drift")
    source_raw, source_payload = load_fixture_json(TERMINAL_SOURCE_FIXTURE)
    if hashlib.sha256(source_raw).hexdigest() != \
            EXPECTED_TERMINAL_SOURCE_SHA256:
        raise AssertionError("terminal source fixture drift")
    terminal_source = validate_terminal_source(source_payload)
    exact_parent_ids = {
        int(group["group"]): tuple(int(parent["parent_stable_index"])
                                   for parent in group["parents"]
                                   if parent["parent_exact"])
        for group in source["scored_groups"]
        if int(group["group"]) in MISSING_SUPPLY_GROUPS}
    if tuple(sorted(exact_parent_ids)) != MISSING_SUPPLY_GROUPS:
        raise AssertionError("missing-supply group identity drift")

    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS)
                         + THIRD_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    seeds = tuple(_crop(oracle, center, SEED_RADIUS,
                        "IQC-third-reach-consumed-seed")
                  for center in DEVELOPMENT_CENTERS)
    targets = tuple(_crop(oracle, center, THIRD_BLOCK_RADIUS,
                          "IQC-third-reach-consumed-target")
                    for center in DEVELOPMENT_CENTERS)
    runtime = load_default_runtime()
    rows = []
    for group_index in MISSING_SUPPLY_GROUPS:
        truth = {_key(point): str(color) for point, color in zip(
            targets[group_index].positions, targets[group_index].species)}
        parents = _reconstruct_parents(
            group_index, exact_parent_ids[group_index], seeds[group_index],
            terminal_source["groups"][group_index], runtime)
        print(f"reach diagnostic: group {group_index} reconstructed "
              f"{len(parents)} exact parents", file=sys.stderr, flush=True)
        for parent_id, parent in parents:
            row = _diagnose(group_index, parent_id, parent, truth, runtime)
            rows.append(row)
            print(f"reach diagnostic: group {group_index} parent {parent_id} "
                  f"minimum reach {row.minimum_uniform_reach_for_exact_path}",
                  file=sys.stderr, flush=True)
    body = {
        "schema_version": 1,
        "source_result_digest": source["result_digest"],
        "missing_supply_groups": MISSING_SUPPLY_GROUPS,
        "current_reach": CURRENT_REACH,
        "parents": tuple(asdict(row) for row in rows),
        "parents_diagnosed": len(rows),
        "frontier_geometry_has_exact_path": sum(
            row.frontier_geometry_has_exact_path for row in rows),
        "current_reach_supplies_exact_path": sum(
            row.current_reach_supplies_exact_path for row in rows),
        "maximum_required_uniform_reach": max((
            row.minimum_uniform_reach_for_exact_path or 0 for row in rows),
            default=0),
        "target_guided_diagnostic_only": True,
        "target_used_for_deployable_candidate_selection": False,
        "candidate_or_marking_changed": False,
        "fresh_confirmation_claimed": False,
        "autonomous_commit_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["source_result_digest"] != SOURCE_RESULT_DIGEST
            or tuple(body["missing_supply_groups"]) != MISSING_SUPPLY_GROUPS
            or body["current_reach"] != CURRENT_REACH
            or body["parents_diagnosed"] != 4
            or body["frontier_geometry_has_exact_path"] != 4
            or body["current_reach_supplies_exact_path"] != 0
            or body["maximum_required_uniform_reach"] != 12
            or not body["target_guided_diagnostic_only"]
            or body["target_used_for_deployable_candidate_selection"]
            or body["candidate_or_marking_changed"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("IQC third-block reach diagnostic drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("IQC third-block reach result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("IQC third-block reach fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
