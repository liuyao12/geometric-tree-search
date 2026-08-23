#!/usr/bin/env python3
"""Freeze a causal fourth-block shortlist before opening IQC nucleus 4.

The selector is fit only on the already-consumed nuclei 2 and 3.  Its fixed
35-dimensional representation is the target-blind terminal feature receipt:
local marking probabilities, votes, pose/port channels, and immediate frontier
support.  Nucleus 4 is ranked but never scored here; the top 32 branches are a
bounded tree-search frontier, not an autonomous winner claim.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import (
    _correct, _truth_index, canonical_json)
from materials_gcts_iqc_fourth_block_beam_fixture import (
    load_default_result as load_beams)
from materials_gcts_iqc_fourth_block_terminal_features import (
    FEATURE_NAMES, load_default_result as load_features)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fourth_block_winner_preflight_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "bf12919ed15e9dc91b120430cd45b83017ed90fe84cdcfac3087223c83e828f8"
EXPECTED_RESULT_DIGEST = \
    "c0a3f680c7a12691f4578be06d77c76dd0cc05784740cdcbd00e7c628f3e1623"
DEVELOPMENT_GROUPS = (2, 3)
CONFIRMATION_GROUP = 4
SHORTLIST = 32


@dataclass(frozen=True)
class _Example:
    group: int
    parent_index: int
    stable_index: int
    features: tuple[float, ...]
    actions: tuple
    exact: bool


def _rows(open_development_targets=True):
    receipt = load_features()
    beams = load_beams()
    by_group = {}
    for group_row in receipt["group_rows"]:
        group = int(group_row["group"])
        truth = None
        if group in DEVELOPMENT_GROUPS and open_development_targets:
            beam = beams["beams"][group]
            target, _ = oracle_crop_fast(beam["center"], beam["next_radius"])
            truth = _truth_index(target.positions, target.species)
        rows = []
        for parent in group_row["parents"]:
            for candidate in parent["rows"]:
                actions = tuple((tuple(map(float, point)), str(color))
                                for point, color in candidate["actions"])
                exact = bool(truth is not None and all(
                    _correct(point, color, truth)
                    for point, color in actions))
                rows.append(_Example(
                    group, int(parent["parent_index"]),
                    int(candidate["stable_index"]),
                    tuple(map(float, candidate["features"])), actions, exact))
        by_group[group] = tuple(rows)
    return by_group, receipt, beams


def _fit(rows):
    import numpy as np
    matrix = np.asarray([row.features for row in rows], dtype=float)
    labels = np.asarray([row.exact for row in rows], dtype=bool)
    means = matrix.mean(axis=0)
    scales = matrix.std(axis=0)
    scales[scales < 1e-9] = 1.
    normalized = (matrix - means) / scales
    contrasts = []
    for group, parent in sorted({(row.group, row.parent_index)
                                 for row in rows}):
        mask = np.asarray([row.group == group and row.parent_index == parent
                           for row in rows])
        if labels[mask].any() and (~labels[mask]).any():
            contrasts.append(normalized[mask & labels].mean(axis=0) -
                             normalized[mask & ~labels].mean(axis=0))
    if len(contrasts) < 2:
        raise AssertionError("winner marking lacks contrasted exact parents")
    weights = np.asarray(contrasts).mean(axis=0)
    return tuple(map(float, means)), tuple(map(float, scales)), \
        tuple(map(float, weights)), len(contrasts)


def _scores(model, rows):
    import numpy as np
    means, scales, weights, _contrasts = model
    matrix = np.asarray([row.features for row in rows], dtype=float)
    return tuple(map(float, ((matrix - np.asarray(means)) /
                             np.asarray(scales)) @ np.asarray(weights)))


def _order(model, rows):
    scores = _scores(model, rows)
    return tuple(sorted(range(len(rows)), key=lambda index: (
        -scores[index], rows[index].parent_index,
        rows[index].stable_index, repr(rows[index].actions)))), scores


def evaluate():
    by_group, feature_receipt, beams = _rows()
    folds = []
    for heldout in DEVELOPMENT_GROUPS:
        training = tuple(row for group in DEVELOPMENT_GROUPS
                         if group != heldout for row in by_group[group])
        held = by_group[heldout]
        model = _fit(training)
        order, _scores_row = _order(model, held)
        first_exact = next(rank for rank, index in enumerate(order, 1)
                           if held[index].exact)
        folds.append({
            "heldout_group": heldout,
            "candidates": len(held),
            "exact_candidates": sum(row.exact for row in held),
            "first_exact_rank": first_exact,
            "top_one_exact": held[order[0]].exact,
            "contrasted_training_parents": model[3],
        })
    training = tuple(row for group in DEVELOPMENT_GROUPS
                     for row in by_group[group])
    model = _fit(training)
    confirmation = by_group[CONFIRMATION_GROUP]
    order, scores = _order(model, confirmation)
    selected = tuple({
        "rank": rank,
        "parent_index": confirmation[index].parent_index,
        "stable_index": confirmation[index].stable_index,
        "score": scores[index],
        "actions": confirmation[index].actions,
    } for rank, index in enumerate(order[:SHORTLIST], 1))
    model_payload = {
        "feature_names": FEATURE_NAMES,
        "means": model[0], "scales": model[1], "weights": model[2],
        "contrasted_parent_strata": model[3],
    }
    model_digest = hashlib.sha256(canonical_json(model_payload)).hexdigest()
    shortlist_digest = hashlib.sha256(canonical_json(selected)).hexdigest()
    body = {
        "schema_version": 1,
        "source_terminal_feature_result_digest":
            feature_receipt["result_digest"],
        "source_beam_result_digest": beams["result_digest"],
        "development_groups": DEVELOPMENT_GROUPS,
        "development_targets_consumed": True,
        "development_targets_opened_after_feature_freeze": True,
        "outer_folds": tuple(folds),
        "representation": "causal-terminal-coupled-plus-future",
        "feature_count": len(FEATURE_NAMES),
        "model": model_payload,
        "model_digest": model_digest,
        "confirmation_group": CONFIRMATION_GROUP,
        "confirmation_candidates": len(confirmation),
        "confirmation_target_opened": False,
        "confirmation_target_used_for_fit_or_ranking": False,
        "shortlist_size": SHORTLIST,
        "shortlist": selected,
        "shortlist_digest": shortlist_digest,
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
            or body["feature_count"] != len(FEATURE_NAMES)
            or body["confirmation_group"] != CONFIRMATION_GROUP
            or body["confirmation_target_opened"]
            or body["confirmation_target_used_for_fit_or_ranking"]
            or body["shortlist_size"] != SHORTLIST
            or len(body["shortlist"]) != SHORTLIST
            or hashlib.sha256(canonical_json(body["model"])).hexdigest()
            != body["model_digest"]
            or hashlib.sha256(canonical_json(body["shortlist"])).hexdigest()
            != body["shortlist_digest"]
            or body["winner_selected"] or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("fourth-block winner preflight drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("winner preflight result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("winner preflight fixture byte drift")
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
        "outer_folds": row["outer_folds"],
        "confirmation_candidates": row["confirmation_candidates"],
        "shortlist_size": row["shortlist_size"],
        "confirmation_target_opened": row["confirmation_target_opened"],
        "winner_selected": row["winner_selected"],
        "model_digest": row["model_digest"],
        "shortlist_digest": row["shortlist_digest"],
        "result_digest": row["result_digest"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
