#!/usr/bin/env python3
"""Whole-nucleus audit of finite typed graphs on bounded IQC lineages.

This is deliberately a single, predeclared graph representation rather than
another wide hyperparameter search.  Each candidate is the unchanged complete
nine-action lineage.  Three canonical proper-SE(3) port graphs are frozen
before the consumed target is opened; the target supplies only the final
exact-lineage label.  The value model is refit while leaving out one entire
nucleus.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import (
    _shuffle, canonical_json, load_examples)
from materials_gcts_partial_port_graph_lineage_value import (
    PartialPortGraphLineageExample, PartialPortGraphLineageSpec,
    fit_partial_port_graph_lineage_value,
    score_partial_port_graph_lineage_value)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_bounded_lineage_graph_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "91151e4af3c62e4670cf63b12b26991c2bc19d313ea08e501bdc86702599dee2")
EXPECTED_RESULT_DIGEST = (
    "a06e7f50ad7f7bf0a4dee6506f7da54a8dabcf8721e72ac714bb8a076fcaa9b5")
SHUFFLES = 31
SPEC = PartialPortGraphLineageSpec(
    interaction_order=2, support_type_weight=.25, ridge=10.,
    minimum_feature_groups=2, steps=120, learning_rate=.16,
    parent_conditional=True, include_transitions=True)


def _model_rows(rows):
    return tuple(PartialPortGraphLineageExample(
        row.group, row.parent, row.graphs, row.exact) for row in rows)


def _rank(model, rows):
    scores = tuple(score_partial_port_graph_lineage_value(
        model, row.graphs) for row in rows)
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
    embedding_cache = {}
    for group in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != group)
        held = tuple(row for row in rows if row.group == group)
        model = fit_partial_port_graph_lineage_value(
            _model_rows(training), SPEC, embedding_cache=embedding_cache)
        exact, rank, index, score = _rank(model, held)
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


def evaluate(shuffles=0):
    rows, cases, candidate_digest, completion = load_examples()
    folds = _outer(rows)
    selected = sum(row["selected_exact"] for row in folds)
    nulls = []
    # The expensive complete null is required only when the observed selector
    # clears the preregistered 4/5 signal threshold.  A red selector cannot
    # become causal merely by comparing it with shuffled labels.
    requested = int(shuffles)
    executed = requested if selected >= 4 else 0
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
    full_model = fit_partial_port_graph_lineage_value(
        _model_rows(rows), SPEC, embedding_cache={})
    body = {
        "schema_version": 1,
        "spec": {
            "interaction_order": SPEC.interaction_order,
            "support_type_weight": SPEC.support_type_weight,
            "ridge": SPEC.ridge,
            "minimum_feature_groups": SPEC.minimum_feature_groups,
            "steps": SPEC.steps,
            "learning_rate": SPEC.learning_rate,
            "parent_conditional": SPEC.parent_conditional,
            "include_transitions": SPEC.include_transitions,
        },
        "groups": len(cases), "examples": len(rows),
        "positive_examples": sum(row.exact for row in rows),
        "stage_graphs_per_lineage": 3,
        "candidate_digest_frozen_before_targets": candidate_digest,
        "completion_result_digest": completion["result_digest"],
        "cases": cases, "outer_folds": folds,
        "outer_selected_exact_groups": selected,
        "outer_supplied_groups": len(folds),
        "outer_first_exact_rank_sum": sum(
            row["first_exact_rank"] or row["candidates"] + 1
            for row in folds),
        "full_feature_count": len(full_model.feature_keys),
        "full_model_digest": full_model.model_digest,
        "shuffle_controls_requested": requested,
        "shuffle_controls_executed": executed,
        "shuffle_controls": tuple(nulls),
        "shuffle_p_value": p_value,
        "grouped_graph_winner_gate_passed": bool(
            selected >= 4 and executed == SHUFFLES and p_value <= .05),
        "candidate_geometry_unchanged": True,
        "candidate_target_used": False,
        "targets_opened_after_candidate_freeze": True,
        "raw_ids_or_absolute_coordinates_in_graphs": False,
        "proper_se3_invariant_graphs": True,
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
            or body["raw_ids_or_absolute_coordinates_in_graphs"]
            or not body["proper_se3_invariant_graphs"]
            or not body["development_targets_consumed"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("bounded lineage graph-value result drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("bounded lineage graph-value digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("bounded lineage graph-value fixture drift")
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
        "shuffle_p_value", "grouped_graph_winner_gate_passed",
        "result_digest")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
