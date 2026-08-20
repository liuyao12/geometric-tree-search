#!/usr/bin/env python3
"""Nested IQC value for parent→child boundary-obligation transitions."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_branch_local_integrated_beam_diagnostic import (
    DEFAULT_FIXTURE as BEAM_FIXTURE,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_BEAM_SHA256,
    EXPECTED_RESULT_DIGEST as EXPECTED_BEAM_DIGEST,
    validate_result as validate_beam)
from materials_gcts_iqc_extended_development_preregistration import SEED_RADIUS
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import (
    _partial, action_key, load_default_runtime)
from materials_gcts_iqc_parent_child_macro_dataset import (
    DEFAULT_FIXTURE as MACRO_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_MACRO_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_MACRO_SHA256,
    FEATURE_NAMES as MACRO_FEATURE_NAMES,
    validate_dataset as validate_macro_dataset)
from materials_gcts_iqc_parent_child_macro_value import (
    Example, Representation, _fit, _group_result, _score)
from materials_gcts_iqc_parent_child_port_transition_dataset import (
    DEFAULT_FIXTURE as PORT_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_PORT_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_PORT_SHA256,
    FEATURE_NAMES as PORT_FEATURE_NAMES, transition_features,
    validate_dataset as validate_port_dataset)
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _replay_first_terminal)
from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS)
from materials_gcts_iqc_self_fed_terminal_dataset import OUTER_ORACLE_LIFT_BOUND
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


RIDGES = (.25, 1., 4., 16.)
SHUFFLES = 31
SHUFFLE_SEED = 20260820
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_parent_child_port_transition_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "a80222b685fe1af4c40efbe220feada884a80aba944dd53d45b1aa635d24865d"
EXPECTED_AUDIT_DIGEST = \
    "31166e0d907752086b41fad836f6328665697a160e1f4a7df3f1cef90ac8fc1e"


def _load(path, expected_sha, validator, expected_digest):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise AssertionError("transition-value source fixture byte drift")
    row = validator(json.loads(gzip.decompress(raw)))
    if row["dataset_digest"] != expected_digest:
        raise AssertionError("transition-value source digest drift")
    return row


def _representations():
    macro_width = len(MACRO_FEATURE_NAMES)
    graph_width = len(PORT_FEATURE_NAMES) // 3
    parent = tuple(range(macro_width, macro_width + graph_width))
    child = tuple(range(macro_width + graph_width,
                        macro_width + 2 * graph_width))
    delta = tuple(range(macro_width + 2 * graph_width,
                        macro_width + 3 * graph_width))
    macro = tuple(range(macro_width))
    return (
        Representation("parent-ports", parent),
        Representation("child-ports", child),
        Representation("port-delta", delta),
        Representation("child+delta-ports", child + delta),
        Representation("all-port-transition", parent + child + delta),
        Representation("macro+port-delta", macro + delta),
        Representation("macro+all-port-transition",
                       macro + parent + child + delta),
    )


def _examples():
    macro = _load(MACRO_FIXTURE, EXPECTED_MACRO_SHA256,
                  validate_macro_dataset, EXPECTED_MACRO_DIGEST)
    ports = _load(PORT_FIXTURE, EXPECTED_PORT_SHA256,
                  validate_port_dataset, EXPECTED_PORT_DIGEST)
    rows = []
    for macro_group, port_group in zip(macro["groups"], ports["groups"]):
        for left, right in zip(macro_group["rows"], port_group["rows"]):
            if (left["group"], left["stable_index"], left["exact"],
                    left["correct_sites"]) != (
                    right["group"], right["stable_index"], right["exact"],
                    right["correct_sites"]):
                raise AssertionError("macro/port row alignment drift")
            rows.append(Example(
                int(left["group"]), int(left["stable_index"]),
                tuple(map(float, left["features"]))
                + tuple(map(float, right["features"])),
                bool(left["exact"]), int(left["correct_sites"])))
    return tuple(rows), macro, ports


def _capacity(rows, representation, ridge):
    supplied = exact = correct = rank_sum = 0
    for group in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != group)
        held = tuple(row for row in rows if row.group == group)
        selected, rank = _group_result(
            _fit(training, representation, ridge), held)
        if rank is None:
            continue
        supplied += 1
        exact += int(selected.exact)
        correct += selected.correct_sites
        rank_sum += rank
    return supplied, exact, correct, rank_sum


def _select(rows):
    representations = _representations()
    candidates = tuple((
        _capacity(rows, representation, ridge), representation, ridge)
        for representation in representations for ridge in RIDGES)
    order = {row.name: index for index, row in enumerate(representations)}
    capacity, representation, ridge = min(candidates, key=lambda row: (
        -row[0][1], -row[0][2], row[0][3], len(row[1].indices),
        order[row[1].name], -row[2]))
    return capacity, representation, ridge, _fit(rows, representation, ridge)


def _replay_child(source, runtime, actions):
    """Recover the independently rooted second-block terminal.

    The branch-local audit restarts its action history after promoting the
    completed first block to the second block's seed.  Replaying the three
    child actions by appending them to ``parent_state`` therefore creates a
    six-action history that never existed in the frozen second tree.  Rebuild
    that exact target-free tree and identify the terminal by its frozen action
    key instead.
    """
    expected = tuple((tuple(point), str(color)) for point, color in actions)
    states, _counts = _complete_states_at_radius(
        source, runtime, SECOND_BLOCK_RADIUS)
    matches = tuple(state for state in states
                    if action_key(state.actions) == action_key(expected))
    unique = {(tuple(sorted(zip(state.positions, state.species))),
               action_key(state.actions)): state for state in matches}
    if len(unique) != 1:
        raise AssertionError("selected child lacks unique replay")
    return next(iter(unique.values()))


def _confirmation(model, macro, ports):
    raw = BEAM_FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_BEAM_SHA256:
        raise AssertionError("beam fixture byte drift")
    beam = validate_beam(json.loads(gzip.decompress(raw)))
    if beam["result_digest"] != EXPECTED_BEAM_DIGEST:
        raise AssertionError("beam result drift")
    physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SEED_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    seed = _crop(oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-port-transition-confirmation-seed")
    source = SimpleNamespace(
        group=CONFIRMATION_CENTER, seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species))
    runtime = load_default_runtime()
    scale = sum(group["nearest_neighbor_scale"] for group in macro["groups"]) \
        / macro["development_groups"]
    candidates = []
    for branch in beam["receipt"]["branches"]:
        parent_actions = tuple((tuple(point), str(color))
                               for point, color in branch["first_actions"])
        child_actions = tuple((tuple(point), str(color))
                              for point, color in
                              branch["selected_second_actions"])
        parent_state = _replay_first_terminal(source, runtime, parent_actions)
        second_source = SimpleNamespace(
            group=CONFIRMATION_CENTER,
            seed_positions=tuple(parent_state.positions),
            seed_species=tuple(parent_state.species))
        child_state = _replay_child(
            second_source, runtime, child_actions)
        _unused, parent_graph = _partial(
            source, parent_state, runtime["grouped_vocabulary"])
        _unused, child_graph = _partial(
            second_source, child_state, runtime["grouped_vocabulary"])
        from materials_gcts_iqc_parent_child_macro_dataset import macro_features
        features = macro_features(parent_actions, child_actions, scale) \
            + transition_features(asdict(parent_graph), asdict(child_graph))
        candidates.append((int(branch["first_rank"]), features))
    candidates = tuple(candidates)
    order = tuple(rank for rank, _features in sorted(
        candidates, key=lambda row: (-_score(model, row[1]), row[0])))
    labels = {int(row["first_rank"]): row for row in beam["scored_branches"]}
    exact = tuple(rank for rank in order
                  if labels[rank]["first_exact"]
                  and labels[rank]["second_exact"])
    return {
        "candidate_count": len(candidates),
        "candidate_digest": hashlib.sha256(
            canonical_json(candidates)).hexdigest(),
        "order": order,
        "selected_first_rank": order[0],
        "exact_path_ranks": tuple(order.index(rank) + 1 for rank in exact),
        "selected_end_to_end_exact": order[0] in exact,
        "target_used_for_features_or_ranking": False,
        "consumed_labels_joined_after_order": True,
    }


def evaluate():
    rows, macro, ports = _examples()
    folds = []
    for heldout in range(macro["development_groups"]):
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        capacity, representation, ridge, model = _select(training)
        selected, rank = _group_result(model, held)
        folds.append({
            "heldout_group": heldout,
            "terminal_supply": rank is not None,
            "selected_representation": representation.name,
            "selected_ridge": ridge,
            "selected_stable_index": selected.stable_index,
            "selected_exact": selected.exact,
            "selected_correct_sites": selected.correct_sites,
            "first_exact_rank": rank,
            "inner_capacity": capacity,
        })
    final_capacity, representation, ridge, model = _select(rows)
    nested_exact = sum(row["selected_exact"] for row in folds
                       if row["terminal_supply"])
    nested_correct = sum(row["selected_correct_sites"] for row in folds)
    development = tuple(_group_result(model, tuple(
        row for row in rows if row.group == group))[0]
        for group in range(macro["development_groups"]))
    development_exact = sum(row.exact for row in development)
    development_correct = sum(row.correct_sites for row in development)
    rng = random.Random(SHUFFLE_SEED)
    null_exact = []
    for _shuffle in range(SHUFFLES):
        shuffled = []
        for group in range(macro["development_groups"]):
            group_rows = tuple(row for row in rows if row.group == group)
            labels = [(row.exact, row.correct_sites) for row in group_rows]
            rng.shuffle(labels)
            shuffled.extend(Example(
                row.group, row.stable_index, row.features, exact, correct)
                for row, (exact, correct) in zip(group_rows, labels))
        shuffled_model = _fit(tuple(shuffled), representation, ridge)
        selected = tuple(_group_result(shuffled_model, tuple(
            row for row in rows if row.group == group))[0]
            for group in range(macro["development_groups"]))
        null_exact.append(sum(row.exact for row in selected))
    shuffle_p = (1 + sum(value >= development_exact for value in null_exact)) \
        / (SHUFFLES + 1)
    confirmation = _confirmation(model, macro, ports)
    body = {
        "schema_version": 1,
        "macro_dataset_digest": macro["dataset_digest"],
        "port_transition_dataset_digest": ports["dataset_digest"],
        "development_groups": macro["development_groups"],
        "examples": len(rows),
        "exact_examples": sum(row.exact for row in rows),
        "feature_count": len(rows[0].features),
        "representations": [asdict(row) for row in _representations()],
        "ridges": RIDGES,
        "folds": folds,
        "nested_supplied_groups": sum(row["terminal_supply"] for row in folds),
        "nested_selected_exact_groups": nested_exact,
        "nested_selected_correct_sites": nested_correct,
        "development_selected_exact_groups": development_exact,
        "development_selected_correct_sites": development_correct,
        "final_capacity": final_capacity,
        "final_representation": representation.name,
        "final_ridge": ridge,
        "final_model_digest": model.model_digest,
        "shuffle_exact_counts": tuple(null_exact),
        "shuffle_p": shuffle_p,
        "confirmation": confirmation,
        "raw_type_ids_in_features": False,
        "candidate_geometry_unchanged": True,
        "target_used_for_fit_or_ranking": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_commit_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "audit_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("audit_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["macro_dataset_digest"] != EXPECTED_MACRO_DIGEST
            or body["port_transition_dataset_digest"] != EXPECTED_PORT_DIGEST
            or body["development_groups"] != 10
            or body["examples"] != 1278
            or body["exact_examples"] != 142
            or body["raw_type_ids_in_features"]
            or not body["candidate_geometry_unchanged"]
            or body["target_used_for_fit_or_ranking"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("parent-child port-transition value drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("port-transition value digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("port-transition value fixture drift")
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
