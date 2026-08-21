#!/usr/bin/env python3
"""Broaden stage-local rollout training with target-free score quantiles.

For every development nucleus, retain the eight connection-ranked terminals
used at execution plus eight deterministic score-quantile terminals from the
remaining eligible tree.  The broader train-only corpus supplies genuine
failure diversity without changing the top-eight execution portfolio.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path

from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_obligation_expanded_preregistration import (
    DEVELOPMENT_CENTERS, SEED_RADIUS)
from materials_gcts_iqc_stage_local_prefix_dataset import (
    load_default_dataset as load_prefix_dataset)
from materials_gcts_iqc_stage_local_prefix_marking_audit import (
    _eligible, _flatten, _freeze_receipts, _real_labels, _row_id, _score,
    _select_rows)
from materials_gcts_iqc_stage_local_rollout_dataset import _build_geometry
from materials_gcts_iqc_stage_local_site_selector_audit import PREFIX_SPECS
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_stage_local_augmented_rollout_development_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = ""
EXPECTED_DATASET_DIGEST = ""
EXECUTION_TERMINALS = 8
TRAINING_QUANTILE_TERMINALS = 8


def _augmented_shortlist(rows, labels, receipts):
    selected_keys = {}
    for depth, (spec, budget) in enumerate(zip(
            PREFIX_SPECS[:2], (4, 8)), start=1):
        candidates = _eligible(tuple(
            row for row in rows if row["depth"] == depth),
            selected_keys, depth)
        table = receipts[(depth, spec.variant)]
        scores = {_row_id(row): _score(
            table[_row_id(row)], labels, spec) for row in candidates}
        selected = _select_rows(candidates, scores, budget)
        selected_keys = {group: {
            row["action_key_frozen"] for row in group_rows}
                         for group, group_rows in selected.items()}
    depth, spec = 3, PREFIX_SPECS[2]
    candidates = _eligible(tuple(row for row in rows if row["depth"] == 3),
                           selected_keys, depth)
    table = receipts[(depth, spec.variant)]
    scores = {_row_id(row): _score(
        table[_row_id(row)], labels, spec) for row in candidates}
    result = []
    for group in sorted({row["group"] for row in candidates}):
        ranked = sorted((row for row in candidates if row["group"] == group),
                        key=lambda row: (-scores[_row_id(row)],
                                         repr(row["action_key_frozen"])))
        top = ranked[:EXECUTION_TERMINALS]
        remaining = ranked[EXECUTION_TERMINALS:]
        if len(remaining) < TRAINING_QUANTILE_TERMINALS:
            raise AssertionError("insufficient stage-local negative pool")
        indices = tuple(round(index * (len(remaining) - 1) /
                              (TRAINING_QUANTILE_TERMINALS - 1))
                        for index in range(TRAINING_QUANTILE_TERMINALS))
        if len(set(indices)) != TRAINING_QUANTILE_TERMINALS:
            raise AssertionError("stage-local quantile ranks collide")
        chosen = top + [remaining[index] for index in indices]
        result.extend({
            **row, "candidate_index": index,
            "execution_eligible": index < EXECUTION_TERMINALS,
            "connection_score": scores[_row_id(row)],
            "source_rank": ranked.index(row) + 1,
        } for index, row in enumerate(chosen))
    return tuple(result)


def build_dataset(*, workers=1):
    source = load_prefix_dataset()
    rows = _flatten(source)
    receipts, _records, receipt_digest = _freeze_receipts(rows)
    shortlist = _augmented_shortlist(rows, _real_labels(rows), receipts)
    by_group = {group: tuple(row for row in shortlist
                             if row["group"] == group)
                for group in range(source["consumed_development_groups"])}
    seeds = tuple(oracle_crop_fast(center, SEED_RADIUS)[0]
                  for center in DEVELOPMENT_CENTERS)
    payloads = tuple((
        group, center, seed.positions, seed.species,
        tuple(row["action_key_frozen"] for row in by_group[group]))
        for group, (center, seed) in enumerate(zip(DEVELOPMENT_CENTERS, seeds)))
    geometry = _build_geometry(payloads, workers)
    geometry_digest = _digest(tuple(
        row["geometry_digest_before_label_join"] for row in geometry))
    groups = []
    for frozen in geometry:
        labelled = []
        for row, source_row in zip(frozen["rows"], by_group[frozen["group"]]):
            labelled.append({
                **row,
                "execution_eligible": source_row["execution_eligible"],
                "connection_score": source_row["connection_score"],
                "source_rank": source_row["source_rank"],
                "site_correct": tuple(source_row["site_correct"]),
                "correct_sites": int(source_row["correct_sites"]),
                "exact": bool(source_row["viable_prefix"]),
            })
        groups.append({
            **frozen, "rows": tuple(labelled),
            "labels_joined_after_all_rollouts_froze": True,
        })
    body = {
        "schema_version": 1,
        "source_dataset_digest": source["dataset_digest"],
        "development_groups": len(groups),
        "candidate_count": sum(len(group["rows"]) for group in groups),
        "candidates_per_group": 16,
        "execution_candidates_per_group": EXECUTION_TERMINALS,
        "training_quantile_candidates_per_group": TRAINING_QUANTILE_TERMINALS,
        "prefix_receipt_digest": receipt_digest,
        "geometry_digest_before_any_label_join": geometry_digest,
        "groups": tuple(groups),
        "all_labels_joined_after_all_rollouts_froze": True,
        "targets_used_for_candidate_reconstruction_or_rollout": False,
        "quantile_augmentation_used_labels": False,
        "confirmation_data_imported_or_used": False,
        "consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "dataset_digest": _digest(body)}


def validate_dataset(row):
    body = dict(row)
    digest = body.pop("dataset_digest")
    if _digest(body) != digest or body["development_groups"] != 20 or \
            body["candidate_count"] != 320 or \
            body["execution_candidates_per_group"] != 8 or \
            not body["all_labels_joined_after_all_rollouts_froze"] or \
            body["targets_used_for_candidate_reconstruction_or_rollout"] or \
            body["quantile_augmentation_used_labels"] or \
            body["confirmation_data_imported_or_used"] or \
            body["fresh_confirmation_claimed"] or \
            body["autonomous_growth_claimed"] or \
            body["stationary_or_exponential_claimed"]:
        raise AssertionError("augmented stage-local rollout dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("unexpected augmented rollout dataset")
    return row


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("augmented rollout fixture byte drift")
    return validate_dataset(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int,
                        default=max(1, min(4, os.cpu_count() or 1)))
    args = parser.parse_args()
    if args.write and DEFAULT_FIXTURE.exists():
        raise RuntimeError("augmented rollout fixture already exists")
    row = build_dataset(workers=max(1, args.workers))
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
