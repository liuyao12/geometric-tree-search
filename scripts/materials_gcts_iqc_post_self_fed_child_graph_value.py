#!/usr/bin/env python3
"""Nested IQC value audit for typed target-free child-frontier graphs."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_child_frontier_graph_value import (
    ChildFrontierGraphExample, ChildFrontierGraphValueSpec,
    fit_child_frontier_graph_value, score_child_frontier_graph_value)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_post_self_fed_child_graph_dataset import (
    DEFAULT_FIXTURE as GRAPH_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_GRAPH_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_GRAPH_SHA256, graph_from_json,
    load_graph_fixture, validate_dataset)
from materials_gcts_iqc_post_self_fed_fusion_value import (
    MINIMUM_SELECTED_CORRECT_SITES,
    MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS, load_default_result as
    load_baseline_result)


SPEC = ChildFrontierGraphValueSpec(
    interaction_order=2, minimum_feature_groups=2, ridge=10., steps=100,
    learning_rate=.16)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_child_graph_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "e03d8ab6888f915cc0c43f46d5314032b94dda61c97e755bfb869495a22ec73d"
EXPECTED_AUDIT_DIGEST = \
    "5d333040f7a8b7922eb5fff08fac84499f9ca7ab5099b776bffcf82876bd4fc3"


@dataclass(frozen=True)
class Example:
    group: int
    stable_index: int
    graph: object
    exact: bool
    correct_sites: int


@dataclass(frozen=True)
class HeldoutFold:
    heldout_group: int
    terminal_supply: bool
    selected_stable_index: int
    selected_score: float
    selected_exact: bool
    selected_correct_sites: int
    first_exact_rank: int | None
    model_digest: str
    recurrent_features: int


def _load_examples():
    raw, payload = load_graph_fixture(GRAPH_FIXTURE)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_GRAPH_SHA256:
        raise AssertionError("child-graph fixture byte drift")
    dataset = validate_dataset(payload)
    if dataset["dataset_digest"] != EXPECTED_GRAPH_DIGEST:
        raise AssertionError("child-graph dataset drift")
    rows = tuple(Example(
        int(row["group"]), int(row["stable_index"]),
        graph_from_json(row["graph"]), bool(row["exact"]),
        int(row["correct_sites"]))
        for group in dataset["groups"] for row in group["rows"])
    return rows, dataset


def _fit(rows):
    return fit_child_frontier_graph_value(tuple(
        ChildFrontierGraphExample(row.group, row.graph, row.exact)
        for row in rows), SPEC)


def _group_result(model, held):
    scored = tuple((score_child_frontier_graph_value(model, row.graph), row)
                   for row in held)
    ordered = tuple(sorted(scored, key=lambda item: (
        -item[0], item[1].stable_index)))
    selected_score, selected = ordered[0]
    first_exact = next((rank for rank, (_score, row) in
                        enumerate(ordered, 1) if row.exact), None)
    return selected_score, selected, first_exact


def evaluate():
    rows, dataset = _load_examples()
    folds = []
    for heldout in range(dataset["development_groups"]):
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        model = _fit(training)
        score, selected, rank = _group_result(model, held)
        folds.append(HeldoutFold(
            heldout, any(row.exact for row in held), selected.stable_index,
            score, selected.exact, selected.correct_sites, rank,
            model.model_digest, len(model.feature_keys)))
    final_model = _fit(rows)
    selected_exact = sum(fold.selected_exact for fold in folds)
    selected_correct = sum(fold.selected_correct_sites for fold in folds)
    baseline = load_baseline_result()
    graph_stats = tuple(row.graph for row in rows)
    body = {
        "schema_version": 1,
        "child_graph_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["development_groups"],
        "terminal_examples": len(rows),
        "exact_examples": sum(row.exact for row in rows),
        "model_spec": asdict(SPEC),
        "folds": [asdict(fold) for fold in folds],
        "nested_supplied_groups": sum(fold.terminal_supply for fold in folds),
        "nested_selected_exact_groups": selected_exact,
        "nested_selected_correct_sites": selected_correct,
        "nested_first_exact_rank_sum": sum(
            fold.first_exact_rank or 0 for fold in folds),
        "final_model_digest": final_model.model_digest,
        "final_recurrent_features": len(final_model.feature_keys),
        "unique_child_graphs": len({row.canonical_digest
                                    for row in graph_stats}),
        "dead_end_child_nodes": sum(
            node.dead_end for graph in graph_stats for node in graph.nodes),
        "witnessed_child_edges": sum(
            edge.connection_witnessed for graph in graph_stats
            for edge in graph.edges),
        "conflict_child_edges": sum(graph.conflict_edges
                                    for graph in graph_stats),
        "baseline_selected_exact_groups":
            baseline["nested_selected_exact_groups"],
        "baseline_selected_correct_sites":
            baseline["nested_selected_correct_sites"],
        "minimum_selected_exact_supplied_groups":
            MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS,
        "minimum_selected_correct_sites": MINIMUM_SELECTED_CORRECT_SITES,
        "development_gate_passed": (
            selected_exact >= MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS
            and selected_correct >= MINIMUM_SELECTED_CORRECT_SITES),
        "candidate_geometry_unchanged": True,
        "typed_pose_port_incidence_used": True,
        "local_pairwise_compatibility_used": True,
        "dead_end_child_state_used": True,
        "target_used_for_graph_fit_or_ranking": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "audit_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("audit_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or body["child_graph_dataset_digest"] != EXPECTED_GRAPH_DIGEST
            or body["development_groups"] != 10
            or body["terminal_examples"] != 1278
            or body["exact_examples"] != 142
            or not body["candidate_geometry_unchanged"]
            or not body["typed_pose_port_incidence_used"]
            or not body["local_pairwise_compatibility_used"]
            or not body["dead_end_child_state_used"]
            or body["target_used_for_graph_fit_or_ranking"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("post-self-fed child-graph value drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("post-self-fed child-graph audit drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("post-self-fed child-graph value fixture drift")
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
