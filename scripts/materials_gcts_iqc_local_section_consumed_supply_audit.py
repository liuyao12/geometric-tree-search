#!/usr/bin/env python3
"""Consumed-data supply audit for the fifth IQC marking channel.

The frozen local-section model was refit on all three already-consumed nuclei,
so this audit is development evidence only.  Candidate selection is completed
before each consumed target is reopened.  Target coordinates then label exact
prefixes and verify the newly recovered children through the third block.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_three_block_marking_library_execution import (
    select_marking_library_children)
from materials_gcts_iqc_three_block_portfolio_execution import (
    _third_parent_worker)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_local_section_consumed_supply_audit_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "a8791ba54c6795d14cf79510e08e9bae4c03c58cf8c3e2fd9cc06e729c2ab0ac")
EXPECTED_RESULT_DIGEST = (
    "bad3b0a6298c99c511b9ddff1389ef1f24094203535df37a3df5a42efdcfe742")
SEED_RADIUS = 9.
POSITION_TOLERANCE = 1e-5
CASES = (
    ("consumed-development",
     "fixtures/iqc_three_block_portfolio_rehearsal_v1.json.gz",
     (-70., 10., 70.)),
    ("fresh-four-parent-red",
     "fixtures/iqc_three_block_portfolio_confirmation_v1.json.gz",
     (-220., 80., 140.)),
    ("fresh-complete-parent-red",
     "fixtures/iqc_complete_parent_confirmation_v1.json.gz",
     (20., 220., -160.)),
)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def _action_key(action):
    point, color = action
    return tuple(map(float, point)), str(color)


def _correct(action, by_species):
    point, color = _action_key(action)
    return min(math.dist(point, candidate)
               for candidate in by_species[color]) <= POSITION_TOLERANCE


def evaluate():
    case_rows = []
    exact_groups = supplied_groups = incremental_groups = 0
    recovered_third_lineages = 0
    for name, relative, center in CASES:
        source_raw = (ROOT / relative).read_bytes()
        receipt = json.loads(gzip.decompress(source_raw))["receipt"]
        branches = tuple(SimpleNamespace(**row)
                         for row in receipt["second_branches"])
        seed, _seed_ids = oracle_crop_fast(center, SEED_RADIUS)

        # Freeze all selections before reopening this already-consumed target.
        library = select_marking_library_children(
            branches=branches, seed_positions=seed.positions,
            seed_species=seed.species)
        selection_digest = library["digest"]
        legacy = dict(library["legacy_rows"])
        local = dict(library["local_rows"])
        union = dict(library["union_rows"])

        target, _target_ids = oracle_crop_fast(center, receipt["radii"][2])
        by_species = {color: tuple(point for point, species in zip(
            target.positions, target.species) if species == color)
                      for color in set(target.species)}
        groups = []
        for branch in branches:
            if not all(_correct(action, by_species)
                       for action in branch.first_actions):
                continue
            exact_children = tuple(child for child, actions in enumerate(
                branch.second_actions) if all(
                    _correct(action, by_species) for action in actions))
            if not exact_children:
                continue
            exact_groups += 1
            legacy_exact = tuple(child for child in exact_children
                                 if child in legacy[branch.first_rank])
            local_exact = tuple(child for child in exact_children
                                if child in local[branch.first_rank])
            union_exact = tuple(child for child in exact_children
                                if child in union[branch.first_rank])
            supplied_groups += bool(union_exact)
            incremental = tuple(child for child in local_exact
                                if child not in legacy_exact)
            incremental_groups += bool(incremental)
            third_rows = []
            for child in incremental:
                payload = (
                    center, seed.positions, seed.species,
                    branch.first_actions,
                    ((child, branch.second_actions[child]),),
                    branch.first_rank, *receipt["radii"])
                counts, lineages = _third_parent_worker(payload)[0]
                scores = tuple(sum(_correct(action, by_species)
                                   for action in lineage.all_actions)
                               for lineage in lineages)
                exact = tuple(lineage.third_stable_index
                              for lineage, score in zip(lineages, scores)
                              if score == 9)
                recovered_third_lineages += len(exact)
                third_rows.append({
                    "child": child,
                    "candidate_counts": counts,
                    "lineages": len(lineages),
                    "best_correct_actions": max(scores, default=0),
                    "exact_nine_action_lineages": len(exact),
                    "exact_third_stable_indices": exact,
                })
            groups.append({
                "parent": branch.first_rank,
                "exact_children": exact_children,
                "legacy_exact_children": legacy_exact,
                "local_selected_children": local[branch.first_rank],
                "local_exact_children": local_exact,
                "union_exact_children": union_exact,
                "incremental_exact_children": incremental,
                "third_block_incremental_audit": third_rows,
            })
        case_rows.append({
            "name": name,
            "center": center,
            "source_fixture_sha256": hashlib.sha256(source_raw).hexdigest(),
            "selection_digest_frozen_before_consumed_target":
                selection_digest,
            "exact_child_groups": groups,
        })
    model = library["model"]
    body = {
        "schema_version": 1,
        "cases": case_rows,
        "local_section_model_digest": model.model_digest,
        "local_section_model_refit_on_all_consumed_cases": True,
        "grouped_hyperparameter_selection_used": True,
        "exact_child_groups": exact_groups,
        "union_supplied_exact_child_groups": supplied_groups,
        "incremental_local_section_supply_groups": incremental_groups,
        "incremental_exact_nine_action_lineages":
            recovered_third_lineages,
        "candidate_selection_target_used": False,
        "consumed_targets_opened_after_selection": True,
        "consumed_target_development_audit_only": True,
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
            not body["local_section_model_refit_on_all_consumed_cases"] or
            body["candidate_selection_target_used"] or
            not body["consumed_targets_opened_after_selection"] or
            not body["consumed_target_development_audit_only"] or
            body["fresh_confirmation_claimed"] or
            body["winner_or_autonomous_growth_claimed"] or
            body["stationary_or_exponential_claimed"]):
        raise AssertionError("local-section consumed supply audit drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("local-section consumed result digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("local-section consumed fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate())
        text = json.dumps(row, indent=2, sort_keys=True) + "\n"
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps({
        "exact_child_groups": row["exact_child_groups"],
        "union_supplied_exact_child_groups":
            row["union_supplied_exact_child_groups"],
        "incremental_local_section_supply_groups":
            row["incremental_local_section_supply_groups"],
        "incremental_exact_nine_action_lineages":
            row["incremental_exact_nine_action_lineages"],
        "result_digest": row["result_digest"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
