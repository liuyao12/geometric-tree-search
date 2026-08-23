#!/usr/bin/env python3
"""Open IQC group 4 once after freezing marked and shuffled winner orders."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_bounded_lineage_value import (
    _correct, _truth_index, canonical_json)
from materials_gcts_iqc_fifth_block_rollout_preflight import \
    load_default_result as load_rollouts
from materials_gcts_iqc_fourth_block_autonomous_preflight import (
    CONFIRMATION_GROUP, SHUFFLES, load_default_result as load_preflight)
from materials_gcts_iqc_fourth_block_beam_fixture import \
    load_default_result as load_beams
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fourth_block_autonomous_confirmation_group4_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "099e82e536c30603cb3891a83f0dbb9453b190f1a674a186b6b13ed0df1cb008"
EXPECTED_RESULT_DIGEST = \
    "dbb5a83735a99b36f4c9019a8509f2c0000e0f0832c6501f0f977acb5eefdb97"


def evaluate():
    preflight = load_preflight()
    rollouts = load_rollouts()
    beams = load_beams()
    if (preflight["confirmation_target_opened"]
            or preflight["confirmation_target_used_for_fit_or_ranking"]
            or not preflight["winner_selected_before_target"]
            or rollouts["targets_opened"]
            or rollouts["target_or_correctness_used"]):
        raise AssertionError("autonomous confirmation inputs were not sealed")
    confirmation = next(row for row in rollouts["group_rows"]
                        if row["group"] == CONFIRMATION_GROUP)
    candidates = {}
    for source in confirmation["rows"]:
        key = (int(source["rank"]), int(source["parent_index"]),
               int(source["stable_index"]))
        candidates[key] = tuple((tuple(map(float, point)), str(color))
                                for point, color in source["actions"])
    candidate_digest = hashlib.sha256(canonical_json(tuple(
        (key, candidates[key]) for key in sorted(candidates)))).hexdigest()
    if (len(candidates) != preflight["confirmation_candidates"]
            or candidate_digest !=
            preflight["confirmation_candidate_digest"]):
        raise AssertionError("autonomous candidate receipt mutated")
    # This is the only confirmation-target construction in the workflow and
    # occurs after the marked and all 31 null orders are immutable.
    beam = beams["beams"][CONFIRMATION_GROUP]
    target, _ = oracle_crop_fast(beam["center"], beam["next_radius"])
    truth = _truth_index(target.positions, target.species)

    def exact(key):
        return all(_correct(point, color, truth)
                   for point, color in candidates[tuple(key)])

    marked_labels = tuple(exact(key) for key in preflight["marked_order"])
    marked_rank = next((rank for rank, value in enumerate(marked_labels, 1)
                        if value), None)
    null_ranks = []
    null_top_exact = []
    for row in preflight["shuffle_orders"]:
        labels = tuple(exact(key) for key in row["order"])
        null_ranks.append(next((rank for rank, value in enumerate(labels, 1)
                               if value), None))
        null_top_exact.append(labels[0])
    if marked_rank is None:
        p_value = 1.
    else:
        p_value = (1 + sum(rank is not None and rank <= marked_rank
                           for rank in null_ranks)) / (1 + SHUFFLES)
    exact_winner = bool(marked_labels[0])
    causal_gate = bool(exact_winner and p_value <= .05)
    body = {
        "schema_version": 1,
        "group": CONFIRMATION_GROUP,
        "source_preflight_result_digest": preflight["result_digest"],
        "source_rollout_result_digest": rollouts["result_digest"],
        "candidate_digest_before_target": candidate_digest,
        "candidates": len(candidates),
        "exact_candidates": sum(marked_labels),
        "marked_first_exact_rank": marked_rank,
        "marked_top_one_exact": exact_winner,
        "shuffle_count": SHUFFLES,
        "shuffle_first_exact_ranks": tuple(null_ranks),
        "shuffle_top_one_exact_count": sum(null_top_exact),
        "first_exact_rank_p_value": p_value,
        "causal_autonomous_winner_gate_passed": causal_gate,
        "target_opened_once_after_all_orders_frozen": True,
        "target_used_for_fit_ranking_or_execution": False,
        "candidate_receipt_unchanged_after_target": True,
        "autonomous_exact_fourth_block_continuation": exact_winner,
        "sustained_autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or body["group"] != CONFIRMATION_GROUP
            or body["shuffle_count"] != SHUFFLES
            or not body["target_opened_once_after_all_orders_frozen"]
            or body["target_used_for_fit_ranking_or_execution"]
            or not body["candidate_receipt_unchanged_after_target"]
            or body["sustained_autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("fourth-block autonomous confirmation drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("autonomous confirmation result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("autonomous confirmation fixture byte drift")
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
    print(json.dumps({key: row[key] for key in (
        "group", "candidates", "exact_candidates",
        "marked_first_exact_rank", "marked_top_one_exact",
        "shuffle_top_one_exact_count", "first_exact_rank_p_value",
        "causal_autonomous_winner_gate_passed",
        "autonomous_exact_fourth_block_continuation",
        "sustained_autonomous_growth_claimed", "result_digest")},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
