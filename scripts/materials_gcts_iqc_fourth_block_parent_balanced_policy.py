#!/usr/bin/env python3
"""Fit and freeze the width-eight parent-balanced fourth-block policy."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import canonical_json
from materials_gcts_iqc_fourth_block_beam import parent_balanced_beam
from materials_gcts_iqc_fourth_block_winner_preflight import (
    CONFIRMATION_GROUP, DEVELOPMENT_GROUPS, _fit, _rows, _scores)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fourth_block_parent_balanced_policy_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "1644b8b2e7f67105b144218799f2d8ef21c95998efa4f6d99d7dac20a339807a"
EXPECTED_RESULT_DIGEST = \
    "e306cc4766b2209c69aabd1565fa74cd102b1ecfef63e1e88a80ac9dbdda7fd8"
PARENT_WIDTH = 8


def _selection(model, rows):
    scores = _scores(model, rows)
    indices = parent_balanced_beam(
        scores, tuple(row.parent_index for row in rows),
        tuple((row.stable_index, row.actions) for row in rows), PARENT_WIDTH)
    return tuple(indices), scores


def evaluate():
    by_group, terminal_receipt, beams = _rows()
    folds = []
    for heldout in DEVELOPMENT_GROUPS:
        training = tuple(row for group in DEVELOPMENT_GROUPS
                         if group != heldout for row in by_group[group])
        held = by_group[heldout]
        indices, _scores_row = _selection(_fit(training), held)
        exact_parents = {row.parent_index for row in held if row.exact}
        retained_exact_parents = {
            held[index].parent_index for index in indices
            if held[index].exact}
        folds.append({
            "heldout_group": heldout,
            "source_candidates": len(held),
            "retained_candidates": len(indices),
            "exact_candidates_retained": sum(
                held[index].exact for index in indices),
            "exact_parents": len(exact_parents),
            "exact_parents_retained": len(retained_exact_parents),
            "all_exact_parents_retained":
                retained_exact_parents == exact_parents,
        })
    development = tuple(row for group in DEVELOPMENT_GROUPS
                        for row in by_group[group])
    model = _fit(development)
    confirmation = by_group[CONFIRMATION_GROUP]
    indices, scores = _selection(model, confirmation)
    selected = tuple({
        "parent_index": confirmation[index].parent_index,
        "stable_index": confirmation[index].stable_index,
        "score": scores[index],
        "actions": confirmation[index].actions,
    } for index in indices)
    model_payload = {
        "feature_names": tuple(terminal_receipt["feature_names"]),
        "means": model[0], "scales": model[1], "weights": model[2],
        "contrasted_parent_strata": model[3],
    }
    model_digest = hashlib.sha256(canonical_json(model_payload)).hexdigest()
    selected_digest = hashlib.sha256(canonical_json(selected)).hexdigest()
    body = {
        "schema_version": 1,
        "source_terminal_feature_result_digest":
            terminal_receipt["result_digest"],
        "source_beam_result_digest": beams["result_digest"],
        "development_groups": DEVELOPMENT_GROUPS,
        "development_targets_consumed": True,
        "development_targets_opened_after_feature_freeze": True,
        "parent_width": PARENT_WIDTH,
        "outer_folds": tuple(folds),
        "model": model_payload,
        "model_digest": model_digest,
        "selection_group": CONFIRMATION_GROUP,
        "selection_source_candidates": len(confirmation),
        "selected_candidates": len(selected),
        "selected": selected,
        "selected_digest": selected_digest,
        "selection_target_opened": False,
        "selection_target_used_for_fit_or_ranking": False,
        "winner_selected": False,
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
            or tuple(body["development_groups"]) != DEVELOPMENT_GROUPS
            or not body["development_targets_consumed"]
            or not body["development_targets_opened_after_feature_freeze"]
            or body["parent_width"] != PARENT_WIDTH
            or not all(fold["all_exact_parents_retained"]
                       for fold in body["outer_folds"])
            or body["selection_group"] != CONFIRMATION_GROUP
            or body["selected_candidates"] != 64 * PARENT_WIDTH
            or len(body["selected"]) != body["selected_candidates"]
            or hashlib.sha256(canonical_json(body["model"])).hexdigest()
            != body["model_digest"]
            or hashlib.sha256(canonical_json(body["selected"])).hexdigest()
            != body["selected_digest"]
            or body["selection_target_opened"]
            or body["selection_target_used_for_fit_or_ranking"]
            or body["winner_selected"] or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("parent-balanced fourth-block policy drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("parent-balanced policy result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("parent-balanced policy fixture byte drift")
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
    print(json.dumps({
        "parent_width": row["parent_width"],
        "outer_folds": row["outer_folds"],
        "selection_source_candidates": row["selection_source_candidates"],
        "selected_candidates": row["selected_candidates"],
        "selection_target_opened": row["selection_target_opened"],
        "model_digest": row["model_digest"],
        "selected_digest": row["selected_digest"],
        "result_digest": row["result_digest"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
