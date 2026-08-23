#!/usr/bin/env python3
"""Consumed-target diagnosis of missing exact IQC fourth-block supply.

This audit is explicitly non-deployable: after the target-blind shard receipt
is frozen, it opens the consumed group-0 target and follows only correct
frontier actions.  It reports whether the unchanged learned geometry contains
an exact three-action path and the marking rank needed to expose it.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import heapq
import json
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import \
    _dominant_source_color
from materials_gcts_iqc_bounded_lineage_value import (
    _correct, _truth_index, canonical_json)
from materials_gcts_iqc_fourth_block_beam_fixture import \
    load_default_result as load_beams
from materials_gcts_iqc_fourth_block_extension import load_group
from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import \
    UPSTREAM_ANGULAR_BIN_WIDTH
from materials_gcts_iqc_self_fed_complete_frontier_execution import \
    _bounded_at_radius
from materials_gcts_iqc_spatial_beam_transfer_benchmark import CLUSTER_EDGES
from materials_gcts_iqc_three_block_channel_execution import \
    _replay_action_set
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_pose_port_state_marking import score_pose_port_state
from materials_gcts_recursive_connections import local_cluster_types


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_fourth_block_reach_group0_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "2d965ea33d6e2e967a9c96291d77ab9d0fed01d2973a95a79ff72a151a3e1b68"
EXPECTED_RESULT_DIGEST = \
    "5fc038f29d614ab921dc75402a54738ae80cc15a679e9a6e45dbd1b6f7d1a472"
GROUP = 0
DEPTH = 3


def _point_key(point):
    return tuple(round(float(value), 6) for value in point)


def _state_key(state):
    return tuple(sorted((str(color), *_point_key(point))
                        for point, color in zip(
                            state.positions, state.species)))


def _diagnose(source, runtime, radius, truth):
    frontier = _bounded_at_radius(
        runtime["connection"], source,
        local_cluster_types(source.seed_positions, source.seed_species,
                            CLUSTER_EDGES), radius)
    initial = FusionSearchState(
        tuple(source.seed_positions), tuple(source.seed_species), frontier,
        (), (), (), 0., ())
    expanded = [0] * DEPTH
    ranked = [0] * DEPTH
    correct_seen = [0] * DEPTH
    correct_ranks = [[] for _ in range(DEPTH)]
    cache = {}
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
        cost = maximum, total
        if kind == "state":
            state, depth = payload
            key = _state_key(state)
            if best.get((key, depth)) != cost:
                continue
            if depth == DEPTH:
                solution = cost
                break
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
                -score_pose_port_state(runtime["state_model"],
                                       descriptors[point]),
                -state.proposals.votes[point], point)))
            actions = tuple((rank, point, descriptors[point])
                            for rank, point in enumerate(ordered, 1)
                            if _correct(
                                point, str(_dominant_source_color(
                                    state.proposals, point)), truth))
            cache[(key, depth)] = actions
            expanded[depth] += 1
            ranked[depth] += len(ordered)
            correct_seen[depth] += len(actions)
            correct_ranks[depth].extend(rank for rank, _point, _ in actions)
            if actions:
                rank = actions[0][0]
                push((max(maximum, rank), total + rank), "edge",
                     (state, key, depth, cost, 0))
            continue
        state, key, depth, base_cost, index = payload
        if best.get((key, depth)) != base_cost:
            continue
        actions = cache[(key, depth)]
        rank, point, descriptor = actions[index]
        child = _child(
            source, runtime["connection"], runtime["state_model"], state,
            point, descriptor, radius)
        child_cost = max(base_cost[0], rank), base_cost[1] + rank
        child_key = _state_key(child)
        old = best.get((child_key, depth + 1))
        if old is None or child_cost < old:
            best[(child_key, depth + 1)] = child_cost
            push(child_cost, "state", (child, depth + 1))
        next_index = index + 1
        if next_index < len(actions):
            next_rank = actions[next_index][0]
            push((max(base_cost[0], next_rank), base_cost[1] + next_rank),
                 "edge", (state, key, depth, base_cost, next_index))
    return {
        "expanded_states_by_depth": tuple(expanded),
        "ranked_candidates_by_depth": tuple(ranked),
        "correct_actions_seen_by_depth": tuple(correct_seen),
        "minimum_correct_rank_seen_by_depth": tuple(
            min(values) if values else None for values in correct_ranks),
        "maximum_correct_rank_seen_by_depth": tuple(
            max(values) if values else None for values in correct_ranks),
        "minimum_uniform_reach_for_exact_path":
            solution[0] if solution else None,
        "minimum_rank_sum_for_exact_path": solution[1] if solution else None,
        "frontier_geometry_has_exact_path": solution is not None,
    }


def evaluate():
    beams = load_beams()
    extension = load_group(GROUP)
    beam = beams["beams"][GROUP]
    if (extension["heldout_target_opened"] or
            extension["target_used_for_extension"]):
        raise AssertionError("reach source was not target sealed")
    target, _ = oracle_crop_fast(beam["center"], beam["next_radius"])
    truth = _truth_index(target.positions, target.species)
    exact = tuple(row for row in beam["candidates"] if all(
        _correct(point, color, truth) for point, color in row["actions"]))
    if len(exact) != 1:
        raise AssertionError("group-0 beam exact-parent identity drift")
    rejected_ids = {tuple(row["lineage_id"])[1]
                    for row in extension["results"]
                    if row["status"] == "rejected"}
    if exact[0]["stable_index"] in rejected_ids:
        raise AssertionError("target-blind replay pruned exact parent")
    seed, _ = oracle_crop_fast(beam["center"], beam["seed_radius"])
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=tuple(beam["center"]), seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species))
    actions = tuple((tuple(point), color)
                    for point, color in exact[0]["actions"])
    for stage, radius in enumerate(beam["replay_radii"]):
        state, _orders = _replay_action_set(
            source, runtime, actions[3 * stage:3 * stage + 3], radius)
        source = SimpleNamespace(
            group=tuple(beam["center"]), seed_positions=state.positions,
            seed_species=state.species)
    diagnosis = _diagnose(source, runtime, beam["next_radius"], truth)
    body = {
        "schema_version": 1,
        "group": GROUP,
        "source_beam_result_digest": beams["result_digest"],
        "source_extension_result_digest": extension["result_digest"],
        "exact_parent_stable_index": exact[0]["stable_index"],
        "beam_exact_parent_count": len(exact),
        "replay_rejected_branches": extension["lineages_replay_rejected"],
        "replay_rejected_exact_parents": 0,
        **diagnosis,
        "target_opened_only_for_diagnosis": True,
        "target_used_for_deployable_ranking": False,
        "diagnostic_path_returned_to_policy": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1 or body["group"] != GROUP
            or body["beam_exact_parent_count"] != 1
            or body["replay_rejected_exact_parents"] != 0
            or not body["target_opened_only_for_diagnosis"]
            or body["target_used_for_deployable_ranking"]
            or body["diagnostic_path_returned_to_policy"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("fourth-block reach diagnostic drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("fourth-block reach result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("fourth-block reach fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate())
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps({key: row[key] for key in (
        "group", "replay_rejected_branches",
        "correct_actions_seen_by_depth",
        "minimum_correct_rank_seen_by_depth",
        "maximum_correct_rank_seen_by_depth",
        "minimum_uniform_reach_for_exact_path",
        "minimum_rank_sum_for_exact_path",
        "frontier_geometry_has_exact_path", "result_digest")},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
