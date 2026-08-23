#!/usr/bin/env python3
"""Freeze an autonomous fourth-block winner and null orders on IQC group 4."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
from dataclasses import dataclass, replace
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import (
    _correct, _truth_index, canonical_json)
from materials_gcts_iqc_fifth_block_rollout_preflight import (
    load_default_result as load_rollouts)
from materials_gcts_iqc_fourth_block_beam_fixture import (
    load_default_result as load_beams)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fourth_block_autonomous_preflight_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "21346a1e29d80ba2c9cc666b3557408e8fa21c973696e0aa8aad93aac032c59b"
EXPECTED_RESULT_DIGEST = \
    "89cc6777612cab6883b73c4052d8460f8fbaade575ace944acd5e7a548ad74a8"
DEVELOPMENT_GROUPS = (2, 3)
CONFIRMATION_GROUP = 4
SHUFFLES = 31
RIDGE = 1.


@dataclass(frozen=True)
class _Row:
    group: int
    rank: int
    parent_index: int
    stable_index: int
    features: tuple[float, ...]
    actions: tuple
    exact: bool = False


def _rows():
    rollouts = load_rollouts()
    beams = load_beams()
    by_group = {}
    for group_row in rollouts["group_rows"]:
        group = int(group_row["group"])
        truth = None
        if group in DEVELOPMENT_GROUPS:
            beam = beams["beams"][group]
            target, _ = oracle_crop_fast(beam["center"], beam["next_radius"])
            truth = _truth_index(target.positions, target.species)
        rows = []
        for source in group_row["rows"]:
            actions = tuple((tuple(map(float, point)), str(color))
                            for point, color in source["actions"])
            rows.append(_Row(
                group, int(source["rank"]), int(source["parent_index"]),
                int(source["stable_index"]),
                (float(source["linear_score"]),) +
                tuple(map(float, source["features"])), actions,
                bool(truth is not None and all(
                    _correct(point, color, truth)
                    for point, color in actions))))
        by_group[group] = tuple(rows)
    return by_group, rollouts, beams


def _fit(rows):
    import numpy as np
    matrix = np.asarray([row.features for row in rows], dtype=float)
    means = matrix.mean(axis=0)
    scales = matrix.std(axis=0)
    scales[scales < 1e-9] = 1.
    normalized = (matrix - means) / scales
    contrasts = []
    for group in sorted({row.group for row in rows}):
        mask = np.asarray([row.group == group for row in rows])
        labels = np.asarray([row.exact for row in rows])
        if not labels[mask].any() or not (~labels[mask]).any():
            raise AssertionError("autonomous fit needs both labels per group")
        contrasts.append(normalized[mask & labels].mean(axis=0) -
                         normalized[mask & ~labels].mean(axis=0))
    contrasts = np.asarray(contrasts)
    average = contrasts.mean(axis=0)
    dispersion = ((contrasts - average) ** 2).mean(axis=0)
    weights = average / (RIDGE + dispersion)
    return tuple(map(float, means)), tuple(map(float, scales)), \
        tuple(map(float, weights))


def _order(model, rows):
    import numpy as np
    means, scales, weights = map(np.asarray, model)
    matrix = np.asarray([row.features for row in rows], dtype=float)
    scores = tuple(map(float, ((matrix - means) / scales) @ weights))
    order = tuple(sorted(range(len(rows)), key=lambda index: (
        -scores[index], rows[index].rank, rows[index].parent_index,
        rows[index].stable_index)))
    return order, scores


def _key(row):
    return (row.rank, row.parent_index, row.stable_index)


def _shuffled(rows, iteration):
    result = []
    for group in DEVELOPMENT_GROUPS:
        group_rows = tuple(row for row in rows if row.group == group)
        labels = [row.exact for row in group_rows]
        seed = int(hashlib.sha256(
            f"fourth-block-autonomous-null:{iteration}:{group}".encode()
        ).hexdigest()[:16], 16)
        random.Random(seed).shuffle(labels)
        result.extend(replace(row, exact=bool(label))
                      for row, label in zip(group_rows, labels))
    return tuple(result)


def evaluate():
    by_group, rollouts, beams = _rows()
    folds = []
    for heldout in DEVELOPMENT_GROUPS:
        training = tuple(row for group in DEVELOPMENT_GROUPS
                         if group != heldout for row in by_group[group])
        held = by_group[heldout]
        order, _scores = _order(_fit(training), held)
        folds.append({
            "heldout_group": heldout,
            "candidates": len(held),
            "exact_candidates": sum(row.exact for row in held),
            "first_exact_rank": next(
                rank for rank, index in enumerate(order, 1)
                if held[index].exact),
            "top_one_exact": held[order[0]].exact,
        })
    development = tuple(row for group in DEVELOPMENT_GROUPS
                        for row in by_group[group])
    confirmation = by_group[CONFIRMATION_GROUP]
    model = _fit(development)
    order, scores = _order(model, confirmation)
    marked_order = tuple(_key(confirmation[index]) for index in order)
    shuffle_orders = []
    for iteration in range(SHUFFLES):
        null_model = _fit(_shuffled(development, iteration))
        null_order, _null_scores = _order(null_model, confirmation)
        shuffle_orders.append({
            "iteration": iteration,
            "order": tuple(_key(confirmation[index])
                           for index in null_order),
        })
    candidate_digest = hashlib.sha256(canonical_json(tuple(
        (_key(row), row.actions) for row in confirmation))).hexdigest()
    model_payload = {
        "feature_names": ("fourth-block-linear-score",) + tuple(
            rollouts["rollout_feature_names"]),
        "means": model[0], "scales": model[1], "weights": model[2],
        "ridge": RIDGE,
    }
    model_digest = hashlib.sha256(canonical_json(model_payload)).hexdigest()
    orders_digest = hashlib.sha256(canonical_json(
        (marked_order, shuffle_orders))).hexdigest()
    body = {
        "schema_version": 1,
        "source_rollout_result_digest": rollouts["result_digest"],
        "source_beam_result_digest": beams["result_digest"],
        "development_groups": DEVELOPMENT_GROUPS,
        "development_targets_consumed": True,
        "development_targets_opened_after_rollout_freeze": True,
        "outer_folds": tuple(folds),
        "model": model_payload,
        "model_digest": model_digest,
        "confirmation_group": CONFIRMATION_GROUP,
        "confirmation_candidates": len(confirmation),
        "confirmation_candidate_digest": candidate_digest,
        "marked_order": marked_order,
        "marked_top_score": scores[order[0]],
        "shuffle_count": SHUFFLES,
        "shuffle_orders": tuple(shuffle_orders),
        "orders_digest": orders_digest,
        "confirmation_target_opened": False,
        "confirmation_target_used_for_fit_or_ranking": False,
        "winner_selected_before_target": True,
        "winner_confirmed": False,
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
            or not body["development_targets_opened_after_rollout_freeze"]
            or body["confirmation_group"] != CONFIRMATION_GROUP
            or body["confirmation_candidates"] != 32
            or len(body["marked_order"]) != 32
            or body["shuffle_count"] != SHUFFLES
            or len(body["shuffle_orders"]) != SHUFFLES
            or hashlib.sha256(canonical_json(body["model"])).hexdigest()
            != body["model_digest"]
            or hashlib.sha256(canonical_json(
                (body["marked_order"], body["shuffle_orders"]))).hexdigest()
            != body["orders_digest"]
            or body["confirmation_target_opened"]
            or body["confirmation_target_used_for_fit_or_ranking"]
            or not body["winner_selected_before_target"]
            or body["winner_confirmed"] or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("fourth-block autonomous preflight drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("autonomous preflight result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("autonomous preflight fixture byte drift")
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
        "winner_key": row["marked_order"][0],
        "shuffle_count": row["shuffle_count"],
        "confirmation_target_opened": row["confirmation_target_opened"],
        "winner_confirmed": row["winner_confirmed"],
        "model_digest": row["model_digest"],
        "orders_digest": row["orders_digest"],
        "result_digest": row["result_digest"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
