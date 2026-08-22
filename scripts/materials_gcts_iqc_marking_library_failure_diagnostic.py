#!/usr/bin/env python3
"""Consumed-target diagnosis of the fresh five-channel IQC failure."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_marking_library_confirmation import (
    DEFAULT_FIXTURE as CONFIRMATION_FIXTURE, load_default_result)
from materials_gcts_iqc_marking_library_confirmation_preregistration import (
    CONFIRMATION_CENTER, SEED_RADIUS, THIRD_BLOCK_RADIUS)
from materials_gcts_iqc_three_block_portfolio_execution import (
    _prepare_pool, _third_parent_worker)
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_local_section_child_marking import (
    load_default_marking, rank_child_states)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_marking_library_failure_diagnostic_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "c37eff0a44f7aa803141fc536fc327e63fda71234da82e5153cb3067facf1d1f")
EXPECTED_RESULT_DIGEST = (
    "d830e2926dd81e2292c8ee5654761ad3804980549a5949e8af027013dc3e08e6")
POSITION_TOLERANCE = 1e-5


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def _correct(action, by_species):
    point, color = action
    return min(math.dist(point, candidate)
               for candidate in by_species[color]) <= POSITION_TOLERANCE


def evaluate(workers=2):
    confirmation = load_default_result(CONFIRMATION_FIXTURE)
    receipt = confirmation["receipt"]
    seed, _ = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    model, _artifact = load_default_marking()
    local_ranks = {}
    for branch_row in receipt["second_branches"]:
        branch = SimpleNamespace(**branch_row)
        ranked = rank_child_states(
            model=model, seed_positions=seed.positions,
            seed_species=seed.species, branch=branch)
        local_ranks[branch.first_rank] = {
            child: (rank, score) for rank, (child, score, _sites)
            in enumerate(ranked, 1)}

    # The immutable fresh receipt is already red and consumed.  Reopen its
    # target only after all ranking tables above have been reconstructed.
    target, _ = oracle_crop_fast(CONFIRMATION_CENTER, THIRD_BLOCK_RADIUS)
    by_species = {color: tuple(point for point, species in zip(
        target.positions, target.species) if species == color)
                  for color in set(target.species)}
    legacy = {int(parent): tuple(children) for parent, children
              in receipt["legacy_child_ids_by_parent"]}
    local = {int(parent): tuple(children) for parent, children
             in receipt["local_child_ids_by_parent"]}
    union = {int(parent): tuple(children) for parent, children
             in receipt["selected_child_ids_by_parent"]}
    exact_rows = []
    payloads = []
    identities = []
    for branch_row in receipt["second_branches"]:
        branch = SimpleNamespace(**branch_row)
        if not all(_correct(action, by_species)
                   for action in branch.first_actions):
            continue
        for child, actions in enumerate(branch.second_actions):
            if not all(_correct(action, by_species) for action in actions):
                continue
            legacy_ranks = []
            for channel in range(4):
                order = sorted(range(len(branch.second_actions)),
                               key=lambda index: (
                                   -branch.second_channel_scores[index][
                                       channel], index))
                legacy_ranks.append(order.index(child) + 1)
            rank, score = local_ranks[branch.first_rank][child]
            exact_rows.append({
                "parent": branch.first_rank,
                "child": child,
                "legacy_channel_ranks": legacy_ranks,
                "local_section_rank": rank,
                "local_section_score": score,
                "legacy_selected": child in legacy[branch.first_rank],
                "local_selected": child in local[branch.first_rank],
                "union_selected": child in union[branch.first_rank],
            })
            payloads.append((
                CONFIRMATION_CENTER, seed.positions, seed.species,
                branch.first_actions, ((child, actions),),
                branch.first_rank, *receipt["radii"]))
            identities.append((branch.first_rank, child))
    _prepare_pool()
    if workers == 1:
        results = tuple(_third_parent_worker(payload)
                        for payload in payloads)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = tuple(pool.map(_third_parent_worker, payloads))
    for row, result in zip(exact_rows, results):
        counts, lineages = result[0]
        scores = tuple(sum(_correct(action, by_species)
                           for action in lineage.all_actions)
                       for lineage in lineages)
        exact = tuple(lineage.third_stable_index
                      for lineage, score in zip(lineages, scores)
                      if score == 9)
        row["third_candidate_counts"] = counts
        row["third_lineages"] = len(lineages)
        row["best_correct_actions"] = max(scores, default=0)
        row["exact_nine_action_lineages"] = len(exact)
        row["exact_third_stable_indices"] = exact
    body = {
        "schema_version": 1,
        "confirmation_result_digest": confirmation["result_digest"],
        "confirmation_receipt_digest": confirmation["receipt_digest"],
        "confirmation_remains_red": not confirmation[
            "fresh_marking_library_three_block_supply_confirmed"],
        "exact_complete_second_children": exact_rows,
        "exact_complete_second_child_count": len(exact_rows),
        "omitted_exact_second_child_count": sum(
            not row["union_selected"] for row in exact_rows),
        "exact_nine_action_lineages_after_posthoc_expansion": sum(
            row["exact_nine_action_lineages"] for row in exact_rows),
        "failure_localized_to_child_ranking_truncation": bool(
            exact_rows and
            all(not row["union_selected"] for row in exact_rows) and
            all(row["exact_nine_action_lineages"] > 0
                for row in exact_rows)),
        "candidate_selection_target_used": False,
        "diagnostic_children_chosen_posthoc": True,
        "consumed_target_diagnostic_only": True,
        "fresh_confirmation_claimed": False,
        "winner_or_autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or
            not body["confirmation_remains_red"] or
            body["candidate_selection_target_used"] or
            not body["diagnostic_children_chosen_posthoc"] or
            not body["consumed_target_diagnostic_only"] or
            body["fresh_confirmation_claimed"] or
            body["winner_or_autonomous_growth_claimed"] or
            body["stationary_or_exponential_claimed"]):
        raise AssertionError("marking-library failure diagnostic drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("marking-library diagnostic digest drift")
    return row


def load_default_diagnostic(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("marking-library diagnostic fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate(args.workers))
        text = json.dumps(row, indent=2, sort_keys=True) + "\n"
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    else:
        row = load_default_diagnostic()
    print(json.dumps(row, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
