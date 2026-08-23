#!/usr/bin/env python3
"""Whole-nucleus IQC winner audit for temporal support/port incidence.

The immutable nine-action candidate set is unchanged.  The representation is
one target-blind graph linking action supports across all three stages; exact
target sites are opened only after every graph and candidate digest is frozen.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import (
    _shuffle, canonical_json, load_examples)
from materials_gcts_temporal_partial_port_graph import (
    TemporalPortGraphExample, TemporalPortGraphValueSpec,
    fit_temporal_port_graph_value, score_temporal_port_graph_value)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_bounded_temporal_graph_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "23b394fd050759f04f125468703d52cdbf78a58db24ec905aa8f25d752ad2401")
EXPECTED_RESULT_DIGEST = (
    "59066f11b7069238a0fc6b8beccc276485e24cd630581e73fac3a050b54645bc")
SHUFFLES = 31
SPEC = TemporalPortGraphValueSpec(
    ridge=10., minimum_feature_groups=2, steps=120,
    learning_rate=.16, parent_conditional=True)


def _model_rows(rows):
    return tuple(TemporalPortGraphExample(
        row.group, row.parent, row.temporal_graph, row.exact) for row in rows)


def _rank(model, rows, cache):
    scores = tuple(score_temporal_port_graph_value(
        model, row.temporal_graph, embedding_cache=cache) for row in rows)
    full = tuple(sorted(range(len(rows)), key=lambda index: (
        -scores[index], repr(rows[index].tie_key))))
    parent_tops = tuple(min(
        (index for index, row in enumerate(rows) if row.parent == parent),
        key=lambda index: (-scores[index], repr(rows[index].tie_key)))
        for parent in sorted({row.parent for row in rows}))
    order = tuple(sorted(parent_tops, key=lambda index: (
        -scores[index], repr(rows[index].tie_key))))
    first_exact = next((rank for rank, index in enumerate(full, 1)
                        if rows[index].exact), None)
    return bool(rows[order[0]].exact), first_exact, order[0], scores[order[0]]


def _outer(rows):
    folds = []
    cache = {}
    for group in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != group)
        held = tuple(row for row in rows if row.group == group)
        model = fit_temporal_port_graph_value(
            _model_rows(training), SPEC, embedding_cache=cache)
        exact, rank, index, score = _rank(model, held, cache)
        folds.append({
            "group": group, "nucleus": held[0].nucleus,
            "candidates": len(held),
            "exact_lineages": sum(row.exact for row in held),
            "selected_exact": exact, "first_exact_rank": rank,
            "selected_parent": held[index].parent,
            "selected_score": score,
            "training_feature_count": len(model.feature_keys),
            "model_digest": model.model_digest,
        })
    return tuple(folds)


def evaluate(shuffles=SHUFFLES):
    rows, cases, candidate_digest, completion = load_examples()
    if (any(row.temporal_graph.target_used for row in rows)
            or any(row.temporal_graph.raw_atom_ids_retained for row in rows)):
        raise AssertionError("temporal candidate graph leaked forbidden state")
    folds = _outer(rows)
    selected = sum(row["selected_exact"] for row in folds)
    requested = int(shuffles)
    executed = requested if selected >= 4 else 0
    nulls = []
    for trial in range(executed):
        shuffled = _outer(_shuffle(rows, trial))
        nulls.append({
            "iteration": trial,
            "selected_exact_groups": sum(
                row["selected_exact"] for row in shuffled),
            "first_exact_rank_sum": sum(
                row["first_exact_rank"] or row["candidates"] + 1
                for row in shuffled),
        })
    p_value = ((1 + sum(row["selected_exact_groups"] >= selected
                        for row in nulls)) / (1 + len(nulls))) \
        if nulls else 1.
    cache = {}
    model = fit_temporal_port_graph_value(
        _model_rows(rows), SPEC, embedding_cache=cache)
    body = {
        "schema_version": 1,
        "spec": {
            "ridge": SPEC.ridge,
            "minimum_feature_groups": SPEC.minimum_feature_groups,
            "steps": SPEC.steps,
            "learning_rate": SPEC.learning_rate,
            "parent_conditional": SPEC.parent_conditional,
        },
        "groups": len(cases), "examples": len(rows),
        "positive_examples": sum(row.exact for row in rows),
        "temporal_actions_per_lineage": 9,
        "temporal_stages_per_lineage": 3,
        "candidate_digest_frozen_before_targets": candidate_digest,
        "completion_result_digest": completion["result_digest"],
        "cases": cases, "outer_folds": folds,
        "outer_selected_exact_groups": selected,
        "outer_supplied_groups": len(folds),
        "outer_first_exact_rank_sum": sum(
            row["first_exact_rank"] or row["candidates"] + 1
            for row in folds),
        "full_feature_count": len(model.feature_keys),
        "full_model_digest": model.model_digest,
        "shuffle_controls_requested": requested,
        "shuffle_controls_executed": executed,
        "shuffle_controls": tuple(nulls),
        "shuffle_p_value": p_value,
        "grouped_temporal_winner_gate_passed": bool(
            selected >= 4 and executed == SHUFFLES and p_value <= .05),
        "candidate_geometry_unchanged": True,
        "candidate_target_used": False,
        "targets_opened_after_candidate_freeze": True,
        "raw_atom_ids_retained": False,
        "absolute_coordinates_retained": False,
        "proper_se3_invariant_graphs": True,
        "cross_stage_incidence_preserved": True,
        "development_targets_consumed": True,
        "fresh_confirmation_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or not body["candidate_geometry_unchanged"]
            or body["candidate_target_used"]
            or not body["targets_opened_after_candidate_freeze"]
            or body["raw_atom_ids_retained"]
            or body["absolute_coordinates_retained"]
            or not body["proper_se3_invariant_graphs"]
            or not body["cross_stage_incidence_preserved"]
            or not body["development_targets_consumed"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("bounded temporal graph-value result drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("bounded temporal graph-value digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("bounded temporal graph-value fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--shuffles", type=int, default=SHUFFLES)
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate(args.shuffles))
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps({key: row[key] for key in (
        "groups", "examples", "positive_examples",
        "outer_selected_exact_groups", "outer_first_exact_rank_sum",
        "full_feature_count", "shuffle_controls_executed",
        "shuffle_p_value", "grouped_temporal_winner_gate_passed",
        "result_digest")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
