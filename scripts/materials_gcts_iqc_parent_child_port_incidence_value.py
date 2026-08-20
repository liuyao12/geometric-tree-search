#!/usr/bin/env python3
"""Whole-nucleus value audit for exact parent→child port incidence."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_branch_local_integrated_beam_diagnostic import (
    DEFAULT_FIXTURE as BEAM_FIXTURE,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_BEAM_SHA256,
    EXPECTED_RESULT_DIGEST as EXPECTED_BEAM_DIGEST,
    validate_result as validate_beam)
from materials_gcts_iqc_extended_development_preregistration import SEED_RADIUS
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_parent_child_port_incidence_dataset import (
    DEFAULT_FIXTURE as DATASET_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_DATASET_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_DATASET_SHA256,
    validate_dataset)
from materials_gcts_iqc_parent_child_macro_dataset import (
    DEFAULT_FIXTURE as MACRO_FIXTURE,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_MACRO_SHA256,
    validate_dataset as validate_macro_dataset)
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _replay_first_terminal)
from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER)
from materials_gcts_iqc_self_fed_terminal_dataset import OUTER_ORACLE_LIFT_BOUND
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_learned_equivariant_port_value import (
    LearnedEquivariantPortExample, LearnedEquivariantPortSpec,
    fit_learned_equivariant_port_value,
    score_learned_equivariant_port_value)
from materials_gcts_parent_child_port_incidence_transition import (
    combine_port_incidence_transition_blocks,
    port_incidence_transition_block)
from materials_gcts_partial_irregular_port_graph import PartialIrregularPortGraph
from materials_gcts_iqc_self_fed_terminal_dataset import graph_from_json


SPEC = LearnedEquivariantPortSpec(
    interaction_order=3, support_type_weight=0., ridge=10.,
    minimum_feature_groups=2, steps=100, learning_rate=.16,
    objective="pairwise-aggregated")
SHUFFLES = 31
SHUFFLE_SEED = 20260820
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_parent_child_port_incidence_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "e0cc01a6bafcb3e841914b2917fb56c81e0d25473ee9847647e358bd1eb9f2b8"
EXPECTED_AUDIT_DIGEST = \
    "ace7d90fc37571788dd0a764b10bb1e48219259c56d790465b69058af26c5191"


@dataclass(frozen=True)
class Example:
    group: int
    stable_index: int
    graph: PartialIrregularPortGraph
    exact: bool
    correct_sites: int


def _load_examples():
    raw = DATASET_FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_DATASET_SHA256:
        raise AssertionError("incidence dataset fixture byte drift")
    dataset = validate_dataset(json.loads(gzip.decompress(raw)))
    if dataset["dataset_digest"] != EXPECTED_DATASET_DIGEST:
        raise AssertionError("incidence dataset digest drift")
    rows = tuple(Example(
        int(row["group"]), int(row["stable_index"]),
        graph_from_json(row["graph"]), bool(row["exact"]),
        int(row["correct_sites"]))
        for group in dataset["groups"] for row in group["rows"])
    return rows, dataset


def _fit(rows, cache):
    return fit_learned_equivariant_port_value(tuple(
        LearnedEquivariantPortExample(row.group, row.graph, row.exact)
        for row in rows), SPEC, embedding_cache=cache)


def _group_result(model, rows, cache):
    scores = tuple(score_learned_equivariant_port_value(
        model, row.graph, embedding_cache=cache)
                   for row in rows)
    order = tuple(sorted(range(len(rows)), key=lambda index: (
        -scores[index], rows[index].stable_index)))
    exact = tuple(index for index in order if rows[index].exact)
    return rows[order[0]], (order.index(exact[0]) + 1 if exact else None)


def _confirmation(model, dataset, cache):
    raw = BEAM_FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_BEAM_SHA256:
        raise AssertionError("branch-local beam fixture byte drift")
    beam = validate_beam(json.loads(gzip.decompress(raw)))
    if beam["result_digest"] != EXPECTED_BEAM_DIGEST:
        raise AssertionError("branch-local beam result drift")
    physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SEED_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    seed = _crop(oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-port-incidence-confirmation-seed")
    source = SimpleNamespace(
        group=CONFIRMATION_CENTER, seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species))
    runtime = load_default_runtime()
    grouped = runtime["grouped_vocabulary"]
    macro_raw = MACRO_FIXTURE.read_bytes()
    if hashlib.sha256(macro_raw).hexdigest() != EXPECTED_MACRO_SHA256:
        raise AssertionError("macro fixture byte drift")
    macro = validate_macro_dataset(json.loads(gzip.decompress(macro_raw)))
    scale = sum(float(group["nearest_neighbor_scale"])
                for group in macro["groups"]) / macro["development_groups"]
    candidates = []
    for branch in beam["receipt"]["branches"]:
        parent_actions = tuple((tuple(point), str(color)) for point, color in
                               branch["first_actions"])
        child_actions = tuple((tuple(point), str(color)) for point, color in
                              branch["selected_second_actions"])
        parent_state = _replay_first_terminal(source, runtime, parent_actions)
        parent = port_incidence_transition_block(
            grouped.vocabulary, grouped.training_group_support,
            tuple(source.seed_positions), tuple(source.seed_species),
            tuple(point for point, _color in parent_actions),
            tuple(color for _point, color in parent_actions), "parent")
        child = port_incidence_transition_block(
            grouped.vocabulary, grouped.training_group_support,
            tuple(parent_state.positions), tuple(parent_state.species),
            tuple(point for point, _color in child_actions),
            tuple(color for _point, color in child_actions), "child")
        graph = combine_port_incidence_transition_blocks(
            parent, child, distance_scale=scale)
        candidates.append((int(branch["first_rank"]), graph))
    candidates = tuple(candidates)
    scores = tuple(score_learned_equivariant_port_value(
        model, graph, embedding_cache=cache)
                   for _rank, graph in candidates)
    order = tuple(candidates[index][0] for index in sorted(
        range(len(candidates)), key=lambda index: (
            -scores[index], candidates[index][0])))
    candidate_digest = hashlib.sha256(canonical_json(tuple(
        (rank, graph.canonical_digest) for rank, graph in candidates
    ))).hexdigest()
    labels = {int(row["first_rank"]): row for row in beam["scored_branches"]}
    exact = tuple(rank for rank in order
                  if labels[rank]["first_exact"]
                  and labels[rank]["second_exact"])
    return {
        "candidate_count": len(candidates),
        "candidate_digest": candidate_digest,
        "order": order,
        "selected_first_rank": order[0],
        "exact_path_ranks": tuple(order.index(rank) + 1 for rank in exact),
        "selected_end_to_end_exact": order[0] in exact,
        "target_used_for_features_or_ranking": False,
        "consumed_labels_joined_after_order": True,
    }


def evaluate():
    rows, dataset = _load_examples()
    embedding_cache = {}
    folds = []
    for heldout in range(dataset["development_groups"]):
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        model = _fit(training, embedding_cache)
        selected, rank = _group_result(model, held, embedding_cache)
        folds.append({
            "heldout_group": heldout,
            "terminal_supply": rank is not None,
            "selected_stable_index": selected.stable_index,
            "selected_exact": selected.exact,
            "selected_correct_sites": selected.correct_sites,
            "first_exact_rank": rank,
            "model_digest": model.model_digest,
        })
    model = _fit(rows, embedding_cache)
    development = tuple(_group_result(model, tuple(
        row for row in rows if row.group == group), embedding_cache)[0]
        for group in range(dataset["development_groups"]))
    development_exact = sum(row.exact for row in development)
    development_correct = sum(row.correct_sites for row in development)
    rng = random.Random(SHUFFLE_SEED)
    null_exact = []
    for _shuffle in range(SHUFFLES):
        shuffled = []
        for group in range(dataset["development_groups"]):
            group_rows = tuple(row for row in rows if row.group == group)
            labels = [row.exact for row in group_rows]
            rng.shuffle(labels)
            shuffled.extend(Example(
                row.group, row.stable_index, row.graph, label,
                row.correct_sites) for row, label in zip(group_rows, labels))
        shuffled_model = _fit(tuple(shuffled), embedding_cache)
        selected = tuple(_group_result(shuffled_model, tuple(
            row for row in rows if row.group == group), embedding_cache)[0]
            for group in range(dataset["development_groups"]))
        null_exact.append(sum(row.exact for row in selected))
    shuffle_p = (1 + sum(value >= development_exact for value in null_exact)) \
        / (SHUFFLES + 1)
    nested_supplied = sum(row["terminal_supply"] for row in folds)
    nested_exact = sum(row["selected_exact"] for row in folds
                       if row["terminal_supply"])
    nested_correct = sum(row["selected_correct_sites"] for row in folds)
    confirmation = _confirmation(model, dataset, embedding_cache)
    body = {
        "schema_version": 1,
        "dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["development_groups"],
        "examples": len(rows),
        "exact_examples": sum(row.exact for row in rows),
        "spec": asdict(SPEC),
        "folds": folds,
        "nested_supplied_groups": nested_supplied,
        "nested_selected_exact_groups": nested_exact,
        "nested_selected_correct_sites": nested_correct,
        "development_selected_exact_groups": development_exact,
        "development_selected_correct_sites": development_correct,
        "final_model_digest": model.model_digest,
        "cached_graph_embeddings": len(embedding_cache),
        "shuffle_exact_counts": tuple(null_exact),
        "shuffle_p": shuffle_p,
        "confirmation": confirmation,
        "identity_preserving_incidence_used": True,
        "raw_type_ids_in_graph": False,
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
            or body["dataset_digest"] != EXPECTED_DATASET_DIGEST
            or body["development_groups"] != 10
            or body["examples"] != 1278
            or body["exact_examples"] != 142
            or not body["identity_preserving_incidence_used"]
            or body["raw_type_ids_in_graph"]
            or not body["candidate_geometry_unchanged"]
            or body["target_used_for_fit_or_ranking"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("parent-child incidence value drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("parent-child incidence value digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("parent-child incidence value fixture drift")
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
