#!/usr/bin/env python3
"""Execute a later IQC block from group-heldout clusters-squared parents.

The parent IDs come from the frozen leave-one-nucleus-out option receipt.  For
each selected six-action parent, this audit discards the old frontier, treats
the parent's complete colored configuration as the new seed, and enumerates a
fresh bounded three-action block at ``R2 + Rseed``.  Four already-frozen branch
markings retain at most four terminals per parent.  All candidate trees,
scores, actions, and receipt digests freeze before the consumed larger target
annuli are generated and opened once for posthoc scoring.

This measures executable third-block *supply*.  The marking library still
retains alternatives and chooses no autonomous winner, so even an exact path
does not by itself certify autonomous, stationary, or exponential growth.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_child_graph_future_option_audit import (
    EXPECTED_AUDIT_DIGEST as OPTION_AUDIT_DIGEST,
    load_default_result as load_option_result)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import (
    BRANCH_VARIANTS, action_key, branch_features, load_default_runtime)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE as SOURCE_FIXTURE,
    EXPECTED_DATASET_DIGEST as SOURCE_DATASET_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_SOURCE_FIXTURE_SHA256,
    OUTER_ORACLE_LIFT_BOUND, SECOND_BLOCK_RADIUS, load_fixture_json,
    validate_dataset as validate_source_dataset)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, SEED_RADIUS)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_recurrent_branch_value import score_recurrent_branch


CHANNELS = tuple(BRANCH_VARIANTS)
THIRD_BLOCK_RADIUS = SECOND_BLOCK_RADIUS + SEED_RADIUS
TERMINAL_BEAM_WIDTH = 4
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_child_option_third_block_audit_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "e0374007a8146c7974011471a4fc76b0e3dc9031b692bf934b9cac9985e5a29b"
EXPECTED_RESULT_DIGEST = \
    "a1f6cfcef0d8801e57856bb65b02d8e78a525583d7e56e2b007f611092d486d5"


@dataclass(frozen=True)
class FrozenTerminal:
    stable_index: int
    actions: tuple
    channel_scores: tuple[float, ...]
    mean_score: float


@dataclass(frozen=True)
class FrozenParentExecution:
    parent_stable_index: int
    inherited_actions: tuple
    parent_actions: tuple
    parent_atoms: int
    candidate_counts_by_depth: tuple[int, ...]
    terminal_candidates: int
    terminals: tuple[FrozenTerminal, ...]
    selected_terminals: tuple[FrozenTerminal, ...]
    candidate_digest: str
    target_used: bool = False


def _colored_digest(positions, species):
    return hashlib.sha256(repr(tuple(sorted(
        (tuple(map(float, point)), str(color))
        for point, color in zip(positions, species)))).encode()).hexdigest()


def _key(point):
    return tuple(round(float(value), 6) for value in point)


def _selected_ids(option_result):
    if option_result["audit_digest"] != OPTION_AUDIT_DIGEST:
        raise AssertionError("parent-option receipt drift")
    return {int(fold["heldout_group"]): tuple(map(
        int, fold["selected_parent_ids"])) for fold in option_result["folds"]}


def _terminal_scores(state, runtime):
    full = branch_features(state)
    colors = tuple(color for _point, color in state.actions)
    return tuple(score_recurrent_branch(
        runtime["branch_models"][name][2],
        tuple(full[index] for index in BRANCH_VARIANTS[name]), colors)
        for name in CHANNELS)


def _portfolio(rows):
    selected = []
    for channel in range(len(CHANNELS)):
        order = sorted(rows, key=lambda row: (
            -row.channel_scores[channel], row.stable_index))
        winner = next((row for row in order
                       if row.stable_index not in {
                           prior.stable_index for prior in selected}), None)
        if winner is not None:
            selected.append(winner)
        if len(selected) == TERMINAL_BEAM_WIDTH:
            break
    if len(selected) < TERMINAL_BEAM_WIDTH:
        for row in sorted(rows, key=lambda item: (
                -item.mean_score, item.stable_index)):
            if row.stable_index not in {
                    prior.stable_index for prior in selected}:
                selected.append(row)
            if len(selected) == TERMINAL_BEAM_WIDTH:
                break
    return tuple(selected)


def _worker(payload):
    group_index, center, seed_positions, seed_species, source_group, parent_ids = \
        payload
    runtime = load_default_runtime()
    seed_source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    first_states, first_counts = _complete_states_at_radius(
        seed_source, runtime,
        SECOND_BLOCK_RADIUS - SEED_RADIUS)
    inherited = tuple(state for state in first_states if hashlib.sha256(
        repr(action_key(state.actions)).encode()).hexdigest()
        == source_group["inherited_action_digest"])
    if len(inherited) != 1:
        raise AssertionError(f"group {group_index} inherited state drift")
    inherited = inherited[0]
    second_source = SimpleNamespace(
        group=tuple(center), seed_positions=inherited.positions,
        seed_species=inherited.species)
    second_states, second_counts = _complete_states_at_radius(
        second_source, runtime, SECOND_BLOCK_RADIUS)
    second_states = tuple(sorted(
        second_states, key=lambda state: action_key(state.actions)))
    if (tuple(second_counts) != tuple(source_group["second_block_counts"])
            or len(second_states) != int(source_group["second_block_terminals"])
            or any(index < 0 or index >= len(second_states)
                   for index in parent_ids)):
        raise AssertionError(f"group {group_index} parent universe drift")
    executions = []
    for parent_id in parent_ids:
        parent = second_states[parent_id]
        third_source = SimpleNamespace(
            group=tuple(center), seed_positions=parent.positions,
            seed_species=parent.species)
        states, counts = _complete_states_at_radius(
            third_source, runtime, THIRD_BLOCK_RADIUS)
        states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
        terminal_rows = []
        for index, state in enumerate(states):
            scores = _terminal_scores(state, runtime)
            terminal_rows.append(FrozenTerminal(
                index, action_key(state.actions), scores,
                sum(scores) / len(CHANNELS)))
        terminals = tuple(terminal_rows)
        selected = _portfolio(terminals)
        candidate_payload = tuple(
            (row.stable_index, row.actions, row.channel_scores)
            for row in terminals)
        executions.append(FrozenParentExecution(
            parent_id, action_key(inherited.actions), action_key(parent.actions),
            len(parent.positions), tuple(counts), len(terminals), terminals,
            selected,
            hashlib.sha256(repr(candidate_payload).encode()).hexdigest()))
    body = {
        "group": group_index,
        "center": tuple(center),
        "seed_atoms": len(seed_positions),
        "seed_digest": _colored_digest(seed_positions, seed_species),
        "first_candidate_counts": tuple(first_counts),
        "second_candidate_counts": tuple(second_counts),
        "selected_parent_ids": tuple(parent_ids),
        "parents": tuple(asdict(row) for row in executions),
        "target_used": False,
    }
    return {**body, "receipt_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def _prepare_pool():
    import concurrent.futures.process as process
    try:
        process._check_system_limits()
    except PermissionError:
        process._check_system_limits = lambda: None


def evaluate(*, workers=4):
    source_raw, source_payload = load_fixture_json(SOURCE_FIXTURE)
    if hashlib.sha256(source_raw).hexdigest() != \
            EXPECTED_SOURCE_FIXTURE_SHA256:
        raise AssertionError("source terminal fixture byte drift")
    source = validate_source_dataset(source_payload)
    if source["dataset_digest"] != SOURCE_DATASET_DIGEST:
        raise AssertionError("source terminal dataset drift")
    option = load_option_result()
    selected = _selected_ids(option)

    seed_physical = math.ceil(max(math.dist((0., 0., 0.), center)
                                  for center in DEVELOPMENT_CENTERS)
                              + SEED_RADIUS)
    seed_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND, seed_physical)
    seeds = tuple(_crop(seed_oracle, center, SEED_RADIUS,
                        "IQC-third-block-development-seed")
                  for center in DEVELOPMENT_CENTERS)
    payloads = tuple((index, center, tuple(seed.positions),
                      tuple(seed.species), source["groups"][index],
                      selected[index])
                     for index, (center, seed) in enumerate(zip(
                         DEVELOPMENT_CENTERS, seeds)))
    if workers == 1:
        receipts = tuple(_worker(payload) for payload in payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            receipts = tuple(pool.map(_worker, payloads))
    receipt_body = {
        "schema_version": 1,
        "source_dataset_digest": source["dataset_digest"],
        "parent_option_audit_digest": option["audit_digest"],
        "third_block_radius": THIRD_BLOCK_RADIUS,
        "terminal_beam_width": TERMINAL_BEAM_WIDTH,
        "channels": CHANNELS,
        "groups": receipts,
        "target_open_count_before_receipt": 0,
        "target_used": False,
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt_body)).hexdigest()

    # Only now construct the consumed, larger development targets.
    target_physical = math.ceil(max(math.dist((0., 0., 0.), center)
                                    for center in DEVELOPMENT_CENTERS)
                                + THIRD_BLOCK_RADIUS)
    target_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND, target_physical)
    stable_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND + 1, target_physical)
    targets = tuple(_crop(target_oracle, center, THIRD_BLOCK_RADIUS,
                          "IQC-third-block-consumed-target")
                    for center in DEVELOPMENT_CENTERS)
    checks = tuple(_crop(stable_oracle, center, THIRD_BLOCK_RADIUS,
                         "IQC-third-block-target-bound-check")
                   for center in DEVELOPMENT_CENTERS)
    if any(_colored_digest(target.positions, target.species) !=
           _colored_digest(check.positions, check.species)
           for target, check in zip(targets, checks)):
        raise AssertionError("third-block target lift bound is unstable")

    scored_groups = []
    for receipt, target in zip(receipts, targets):
        truth = {_key(point): str(color) for point, color in
                 zip(target.positions, target.species)}
        parents = []
        for parent in receipt["parents"]:
            inherited_exact = all(truth.get(_key(point)) == color
                                  for point, color in parent["inherited_actions"])
            parent_exact = inherited_exact and all(
                truth.get(_key(point)) == color
                for point, color in parent["parent_actions"])
            all_terminals = []
            for terminal in parent["terminals"]:
                correct = sum(truth.get(_key(point)) == color
                              for point, color in terminal["actions"])
                all_terminals.append({
                    "stable_index": terminal["stable_index"],
                    "correct_actions": correct,
                    "exact": correct == len(terminal["actions"]),
                    "end_to_end_exact": (parent_exact and
                                           correct == len(terminal["actions"])),
                })
            by_index = {row["stable_index"]: row for row in all_terminals}
            terminals = tuple(by_index[terminal["stable_index"]]
                              for terminal in parent["selected_terminals"])
            exact_ids = {row["stable_index"] for row in all_terminals
                         if row["end_to_end_exact"]}
            channel_ranks = []
            for channel in range(len(CHANNELS)):
                order = tuple(item["stable_index"] for item in sorted(
                    parent["terminals"], key=lambda item: (
                        -item["channel_scores"][channel],
                        item["stable_index"])))
                channel_ranks.append(next((rank for rank, stable in
                                           enumerate(order, 1)
                                           if stable in exact_ids), None))
            mean_order = tuple(item["stable_index"] for item in sorted(
                parent["terminals"], key=lambda item: (
                    -item["mean_score"], item["stable_index"])))
            parents.append({
                "parent_stable_index": parent["parent_stable_index"],
                "parent_exact": parent_exact,
                "selected_terminals": tuple(terminals),
                "exact_terminal_supply": sum(row["end_to_end_exact"]
                                               for row in terminals),
                "complete_exact_terminal_supply": len(exact_ids),
                "first_exact_ranks_by_channel": tuple(channel_ranks),
                "mean_first_exact_rank": next((
                    rank for rank, stable in enumerate(mean_order, 1)
                    if stable in exact_ids), None),
            })
        scored_groups.append({
            "group": receipt["group"],
            "target_atoms": len(target.positions),
            "selected_exact_parents": sum(row["parent_exact"]
                                           for row in parents),
            "exact_third_block_paths": sum(
                row["exact_terminal_supply"] for row in parents),
            "complete_exact_third_block_paths": sum(
                row["complete_exact_terminal_supply"] for row in parents),
            "parents": tuple(parents),
        })
    supplied_groups = sum(row["selected_exact_parents"] > 0
                          for row in scored_groups)
    third_supply_groups = sum(row["exact_third_block_paths"] > 0
                              for row in scored_groups)
    complete_supply_groups = sum(
        row["complete_exact_third_block_paths"] > 0
        for row in scored_groups)
    body = {
        "schema_version": 1,
        "receipt": receipt_body,
        "receipt_digest": receipt_digest,
        "target_open_count": 1,
        "scored_groups": tuple(scored_groups),
        "selected_exact_parent_groups": supplied_groups,
        "exact_third_block_supply_groups": third_supply_groups,
        "complete_exact_third_block_supply_groups": complete_supply_groups,
        "exact_third_block_paths": sum(row["exact_third_block_paths"]
                                       for row in scored_groups),
        "complete_exact_third_block_paths": sum(
            row["complete_exact_third_block_paths"]
            for row in scored_groups),
        "target_used_for_parent_or_terminal_candidates": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "marking_library_selects_one_winner": False,
        "autonomous_commit_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    receipt = body["receipt"]
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or receipt["source_dataset_digest"] != SOURCE_DATASET_DIGEST
            or receipt["parent_option_audit_digest"] != OPTION_AUDIT_DIGEST
            or receipt["target_open_count_before_receipt"] != 0
            or receipt["target_used"]
            or hashlib.sha256(canonical_json(receipt)).hexdigest()
               != body["receipt_digest"]
            or body["target_open_count"] != 1
            or body["target_used_for_parent_or_terminal_candidates"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["marking_library_selects_one_winner"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("IQC third-block option execution drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("IQC third-block option result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("IQC third-block option fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.workers <= 0:
        raise SystemExit("--workers must be positive")
    row = evaluate(workers=args.workers)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
