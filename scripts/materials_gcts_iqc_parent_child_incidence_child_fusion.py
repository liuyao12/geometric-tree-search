#!/usr/bin/env python3
"""Consumed-development fusion of transition incidence and child frontier."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from materials_gcts_child_frontier_graph_value import (
    score_child_frontier_graph_value)
from materials_gcts_equivariant_port_fusion_value import percentile_ranks
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_parent_child_port_incidence_value import (
    _fit as fit_incidence, _load_examples as load_incidence)
from materials_gcts_iqc_post_self_fed_child_graph_value import (
    _fit as fit_child, _load_examples as load_child)
from materials_gcts_learned_equivariant_port_value import (
    score_learned_equivariant_port_value)


WEIGHTS = (.5, 1., 2.)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_parent_child_incidence_child_fusion_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "853213b85c4af19e27d8d2c5558e84e8963ee994044404bb0497d81b9cc88a81"
EXPECTED_AUDIT_DIGEST = \
    "742e64029754a617270b0e6e95a3fd4261a9e3ad29bc8f38fae2ecc783472584"


def evaluate():
    incidence, incidence_data = load_incidence()
    children, child_data = load_child()
    left = {(row.group, row.stable_index): row for row in incidence}
    right = {(row.group, row.stable_index): row for row in children}
    if left.keys() != right.keys():
        raise AssertionError("fusion candidate identity drift")
    incidence_cache, child_cache = {}, {}
    folds = []
    totals = {weight: [0, 0, 0] for weight in WEIGHTS}
    for heldout in range(incidence_data["development_groups"]):
        incidence_model = fit_incidence(tuple(
            row for row in incidence if row.group != heldout), incidence_cache)
        child_model = fit_child(tuple(
            row for row in children if row.group != heldout))
        keys = tuple(sorted(key for key in left if key[0] == heldout))
        incidence_ranks = percentile_ranks(tuple(
            score_learned_equivariant_port_value(
                incidence_model, left[key].graph,
                embedding_cache=incidence_cache) for key in keys))
        child_ranks = percentile_ranks(tuple(
            score_child_frontier_graph_value(
                child_model, right[key].graph, embedding_cache=child_cache)
            for key in keys))
        rows = []
        for weight in WEIGHTS:
            order = tuple(sorted(range(len(keys)), key=lambda index: (
                -(incidence_ranks[index] + weight * child_ranks[index]),
                keys[index][1])))
            selected = left[keys[order[0]]]
            exact = tuple(index for index in order if left[keys[index]].exact)
            rank = order.index(exact[0]) + 1 if exact else None
            totals[weight][0] += int(selected.exact)
            totals[weight][1] += selected.correct_sites
            totals[weight][2] += rank or 0
            rows.append({
                "child_rank_weight": weight,
                "selected_stable_index": selected.stable_index,
                "selected_exact": selected.exact,
                "selected_correct_sites": selected.correct_sites,
                "first_exact_rank": rank,
            })
        folds.append({"heldout_group": heldout, "weights": rows})
    capacities = tuple({
        "child_rank_weight": weight,
        "selected_exact_groups": totals[weight][0],
        "selected_correct_sites": totals[weight][1],
        "first_exact_rank_sum": totals[weight][2],
    } for weight in WEIGHTS)
    body = {
        "schema_version": 1,
        "incidence_dataset_digest": incidence_data["dataset_digest"],
        "child_graph_dataset_digest": child_data["dataset_digest"],
        "development_groups": incidence_data["development_groups"],
        "examples": len(incidence),
        "weights": WEIGHTS,
        "capacities": capacities,
        "folds": folds,
        "all_weights_same_accuracy_plateau": len({
            (row["selected_exact_groups"], row["selected_correct_sites"])
            for row in capacities}) == 1,
        "best_selected_exact_groups": max(
            row["selected_exact_groups"] for row in capacities),
        "best_selected_correct_sites": max(
            row["selected_correct_sites"] for row in capacities),
        "candidate_sets_identical": True,
        "exploratory_consumed_weight_sweep": True,
        "target_used_for_fit_or_ranking": False,
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
            or body["development_groups"] != 10
            or body["examples"] != 1278
            or tuple(body["weights"]) != WEIGHTS
            or not body["candidate_sets_identical"]
            or not body["exploratory_consumed_weight_sweep"]
            or body["target_used_for_fit_or_ranking"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("incidence/child fusion audit drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("incidence/child fusion result drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("incidence/child fusion fixture drift")
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
