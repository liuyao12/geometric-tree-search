#!/usr/bin/env python3
"""Consumed IQC audit of a compute-matched channel-diverse action reach.

The existing third-block executor ranks every frontier pose with one frozen
pose/port probability and renders only the first eight.  The consumed reach
diagnostic shows four exact paths whose local bottleneck rank is twelve.  This
audit does *not* set the reach to twelve.  Instead, it spends the same eight
child expansions on three scalar leaders and one leader from each of the five
already-frozen pose/port evidence channels.

All parent replay, candidate selection, three-action trees, and digests freeze
before the already-consumed larger targets are constructed.  The target then
scores supply only.  Because the selector was proposed after inspecting the
consumed reach failure, success is development evidence, not confirmation or
authorization to deploy it.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_iqc_child_option_third_block_audit import (
    EXPECTED_RESULT_DIGEST as SOURCE_RESULT_DIGEST, THIRD_BLOCK_RADIUS,
    load_default_result as load_source_result)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, action_key, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _bounded_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    OUTER_ORACLE_LIFT_BOUND, SECOND_BLOCK_RADIUS)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, _crop)
from materials_gcts_iqc_third_block_reach_diagnostic import (
    EXPECTED_RESULT_DIGEST as REACH_RESULT_DIGEST,
    MISSING_SUPPLY_GROUPS, load_default_result as load_reach_result)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_pose_port_state_marking import (
    select_pose_port_channel_diverse)
from materials_gcts_recursive_connections import local_cluster_types


ACTION_BUDGET = 8
BASELINE_SLOTS = 3
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_third_block_channel_reach_audit_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "8b3e9e937e5b9f8089c70125f21abaa0c204303543cc1a075078d9d6ee093654"
EXPECTED_RESULT_DIGEST = \
    "235fe0d5f2555521772688246a05109490ebd2017196db6dad51fed9bf684e5b"


@dataclass(frozen=True)
class ParentChannelReach:
    group: int
    parent_stable_index: int
    inherited_valid_action_orders: int
    parent_valid_action_orders: int
    candidate_counts_by_depth: tuple[int, ...]
    terminal_candidates: int
    terminal_actions: tuple[tuple, ...]
    candidate_digest: str
    target_used: bool = False


def _key(point):
    return tuple(round(float(value), 6) for value in point)


def _state_key(state):
    return tuple(sorted((str(color), *_key(point))
                        for point, color in zip(
                            state.positions, state.species)))


def _initial_state(source, runtime, radius):
    frontier = _bounded_at_radius(
        runtime["connection"], source,
        local_cluster_types(source.seed_positions, source.seed_species,
                            CLUSTER_EDGES), radius)
    return FusionSearchState(
        tuple(source.seed_positions), tuple(source.seed_species), frontier,
        (), (), (), 0., ())


def _replay_unordered(source, runtime, actions, radius):
    """Replay one frozen action *set* without assuming its stored sort order."""
    actions = tuple((tuple(map(float, point)), str(color))
                    for point, color in actions)
    finals = {}
    valid_orders = 0

    def visit(state, remaining):
        nonlocal valid_orders
        if not remaining:
            valid_orders += 1
            finals.setdefault(_state_key(state), state)
            return
        descriptors = _descriptors(
            state.positions, state.species, state.proposals,
            UPSTREAM_ANGULAR_BIN_WIDTH)
        by_key = {}
        for point in state.proposals.votes:
            by_key.setdefault(_key(point), []).append(point)
        for index, (stored_point, color) in enumerate(remaining):
            matches = tuple(point for point in by_key.get(
                _key(stored_point), ()) if str(_dominant_source_color(
                    state.proposals, point)) == color)
            if len(matches) != 1:
                continue
            point = matches[0]
            child = _child(
                source, runtime["connection"], runtime["state_model"],
                state, point, descriptors[point], radius)
            visit(child, remaining[:index] + remaining[index + 1:])

    visit(_initial_state(source, runtime, radius), actions)
    if valid_orders < 1 or len(finals) != 1:
        raise AssertionError(
            "frozen unordered actions did not replay to one colored state")
    return next(iter(finals.values())), valid_orders


def _channel_diverse_points(state, runtime):
    descriptors = _descriptors(
        state.positions, state.species, state.proposals,
        UPSTREAM_ANGULAR_BIN_WIDTH)
    if len(descriptors) <= ACTION_BUDGET:
        return tuple(sorted(descriptors)), descriptors
    selected = select_pose_port_channel_diverse(
        runtime["state_model"], descriptors, budget=ACTION_BUDGET,
        baseline_slots=BASELINE_SLOTS, votes=state.proposals.votes,
        tie_keys={point: point for point in descriptors})
    return selected, descriptors


def _channel_tree(source, runtime):
    states = (_initial_state(source, runtime, THIRD_BLOCK_RADIUS),)
    counts = []
    for _depth in range(3):
        children = {}
        for state in states:
            points, descriptors = _channel_diverse_points(state, runtime)
            for point in points:
                child = _child(
                    source, runtime["connection"], runtime["state_model"],
                    state, point, descriptors[point], THIRD_BLOCK_RADIUS)
                key = action_key(child.actions)
                prior = children.get(key)
                if prior is None or (child.cumulative, child.actions) > \
                        (prior.cumulative, prior.actions):
                    children[key] = child
        states = tuple(sorted(children.values(),
                              key=lambda row: action_key(row.actions)))
        counts.append(len(states))
    return states, tuple(counts)


def _source_exact_parent_receipts(source, groups=None):
    groups = (tuple(int(group["group"])
                    for group in source["scored_groups"])
              if groups is None else tuple(map(int, groups)))
    admitted = frozenset(groups)
    exact_ids = {
        int(group["group"]): tuple(int(parent["parent_stable_index"])
                                   for parent in group["parents"]
                                   if parent["parent_exact"])
        for group in source["scored_groups"]
        if int(group["group"]) in admitted and
        any(parent["parent_exact"] for parent in group["parents"])}
    receipts = {int(group["group"]): group
                for group in source["receipt"]["groups"]}
    result = {}
    for group, ids in exact_ids.items():
        by_id = {int(parent["parent_stable_index"]): parent
                 for parent in receipts[group]["parents"]}
        result[group] = tuple(by_id[parent_id] for parent_id in ids)
    return result


def evaluate():
    source = load_source_result()
    reach = load_reach_result()
    if (source["result_digest"] != SOURCE_RESULT_DIGEST or
            reach["result_digest"] != REACH_RESULT_DIGEST or
            reach["frontier_geometry_has_exact_path"] != 4 or
            reach["current_reach_supplies_exact_path"] != 0):
        raise AssertionError("upstream third-block reach evidence drift")
    parent_receipts = _source_exact_parent_receipts(
        source, MISSING_SUPPLY_GROUPS)
    if tuple(sorted(parent_receipts)) != MISSING_SUPPLY_GROUPS or \
            sum(map(len, parent_receipts.values())) != 4:
        raise AssertionError("missing-reach parent identities drift")

    seed_physical = math.ceil(max(math.dist((0., 0., 0.), center)
                                  for center in DEVELOPMENT_CENTERS)
                              + SEED_RADIUS)
    seed_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND, seed_physical)
    seeds = tuple(_crop(seed_oracle, center, SEED_RADIUS,
                        "IQC-channel-reach-consumed-seed")
                  for center in DEVELOPMENT_CENTERS)
    runtime = load_default_runtime()
    rows = []
    for group in MISSING_SUPPLY_GROUPS:
        center = DEVELOPMENT_CENTERS[group]
        seed = seeds[group]
        original = SimpleNamespace(
            group=tuple(center), seed_positions=tuple(seed.positions),
            seed_species=tuple(seed.species))
        first_receipt = parent_receipts[group][0]
        inherited, inherited_orders = _replay_unordered(
            original, runtime, first_receipt["inherited_actions"],
            TARGET_RADIUS)
        for receipt in parent_receipts[group]:
            if receipt["inherited_actions"] != \
                    first_receipt["inherited_actions"]:
                raise AssertionError("group inherited action-set drift")
            second = SimpleNamespace(
                group=tuple(center), seed_positions=inherited.positions,
                seed_species=inherited.species)
            parent, parent_orders = _replay_unordered(
                second, runtime, receipt["parent_actions"],
                SECOND_BLOCK_RADIUS)
            third = SimpleNamespace(
                group=tuple(center), seed_positions=parent.positions,
                seed_species=parent.species)
            terminals, counts = _channel_tree(third, runtime)
            terminal_actions = tuple(action_key(state.actions)
                                     for state in terminals)
            payload = (
                group, int(receipt["parent_stable_index"]), counts,
                terminal_actions)
            rows.append(ParentChannelReach(
                group, int(receipt["parent_stable_index"]), inherited_orders,
                parent_orders, counts, len(terminals), terminal_actions,
                hashlib.sha256(repr(payload).encode()).hexdigest()))

    receipt_payload = tuple(asdict(row) for row in rows)
    receipt_digest = hashlib.sha256(
        canonical_json(receipt_payload)).hexdigest()

    # The target is constructed only after every action and digest is frozen.
    target_physical = math.ceil(max(math.dist((0., 0., 0.), center)
                                    for center in DEVELOPMENT_CENTERS)
                                + THIRD_BLOCK_RADIUS)
    target_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND, target_physical)
    targets = tuple(_crop(target_oracle, center, THIRD_BLOCK_RADIUS,
                          "IQC-channel-reach-consumed-target")
                    for center in DEVELOPMENT_CENTERS)
    scored = []
    for row in rows:
        target = targets[row.group]
        truth = {_key(point): str(color) for point, color in zip(
            target.positions, target.species)}
        exact = tuple(actions for actions in row.terminal_actions
                      if all(truth.get(_key(point)) == str(color)
                             for point, color in actions))
        scored.append({
            "group": row.group,
            "parent_stable_index": row.parent_stable_index,
            "exact_terminal_paths": len(exact),
            "supplied": bool(exact),
        })
    supplied_parents = sum(row["supplied"] for row in scored)
    supplied_groups = len({row["group"] for row in scored if row["supplied"]})
    body = {
        "schema_version": 1,
        "source_result_digest": source["result_digest"],
        "reach_result_digest": reach["result_digest"],
        "missing_supply_groups": MISSING_SUPPLY_GROUPS,
        "action_budget": ACTION_BUDGET,
        "baseline_slots": BASELINE_SLOTS,
        "channel_slots": len(runtime["state_model"].channel_families),
        "matched_child_expansion_budget": True,
        "receipt": receipt_payload,
        "receipt_digest": receipt_digest,
        "scored_parents": tuple(scored),
        "parents_scored": len(scored),
        "supplied_parents": supplied_parents,
        "supplied_groups": supplied_groups,
        "baseline_supplied_parents": 0,
        "target_open_count": 1,
        "target_used_for_parent_replay_or_candidate_selection": False,
        "selector_proposed_after_consumed_failure": True,
        "consumed_development_only": True,
        "causal_superiority_claimed": False,
        "fresh_confirmation_claimed": False,
        "autonomous_commit_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["source_result_digest"] != SOURCE_RESULT_DIGEST or
            body["reach_result_digest"] != REACH_RESULT_DIGEST or
            tuple(body["missing_supply_groups"]) != MISSING_SUPPLY_GROUPS or
            body["action_budget"] != ACTION_BUDGET or
            body["baseline_slots"] != BASELINE_SLOTS or
            body["channel_slots"] != 5 or
            not body["matched_child_expansion_budget"] or
            body["parents_scored"] != 4 or
            body["supplied_parents"] != 4 or
            body["supplied_groups"] != 2 or
            body["baseline_supplied_parents"] != 0 or
            body["target_open_count"] != 1 or
            body["target_used_for_parent_replay_or_candidate_selection"] or
            not body["selector_proposed_after_consumed_failure"] or
            not body["consumed_development_only"] or
            body["causal_superiority_claimed"] or
            body["fresh_confirmation_claimed"] or
            body["autonomous_commit_claimed"] or
            body["stationary_or_exponential_claimed"]):
        raise AssertionError("IQC third-block channel reach audit drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("IQC channel reach result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("IQC channel reach fixture byte drift")
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
