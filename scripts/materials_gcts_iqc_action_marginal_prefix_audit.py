#!/usr/bin/env python3
"""Consumed-only audit of one structural fallback per IQC parent."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_action_marginal_prefix_schedule import \
    select_action_marginal_prefixes
from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_iqc_joint_child_action_marking_fit import CASES
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_joint_prefix_schedule import (
    load_default_schedule, schedule_prefixes)


ROOT = Path(__file__).resolve().parent


def _correct(actions, truth):
    return all(colored_action_labels(actions, truth, tolerance=1e-5))


def evaluate(*, maximum_fallbacks=None,
             require_universal_avoidance=False):
    schedule, _artifact = load_default_schedule()
    cases = []
    exact_groups = joint_supplied = augmented_supplied = 0
    total_selected = total_fallbacks = fallbacks_avoiding_universal = 0
    for name, relative, center in CASES:
        raw = (ROOT / relative).read_bytes()
        receipt = json.loads(gzip.decompress(raw))["receipt"]
        branches = tuple(SimpleNamespace(**row)
                         for row in receipt["second_branches"])
        seed, _ = oracle_crop_fast(center, 9.)
        scheduled = schedule_prefixes(
            schedule=schedule, seed_positions=seed.positions,
            seed_species=seed.species, branches=branches)
        selection = select_action_marginal_prefixes(
            scheduled=scheduled, branches=branches,
            maximum_fallbacks=maximum_fallbacks,
            require_universal_avoidance=require_universal_avoidance)
        # Candidate identities and the structural selection digest are frozen
        # before reopening this already-consumed development target.
        target, _ = oracle_crop_fast(center, receipt["radii"][1])
        truth = colored_position_index(
            target.positions, target.species, tolerance=1e-5)
        joint_ids = {(int(row[0]), int(row[1]))
                     for row in selection["joint_rows"]}
        selected_ids = {(int(row[0]), int(row[1]))
                        for row in selection["selected_rows"]}
        case_groups = []
        for branch in branches:
            if not _correct(branch.first_actions, truth):
                continue
            exact = tuple(child for child, actions in enumerate(
                branch.second_actions) if _correct(actions, truth))
            if not exact:
                continue
            parent = int(branch.first_rank)
            joint_hit = any((parent, child) in joint_ids for child in exact)
            selected_hit = any((parent, child) in selected_ids
                               for child in exact)
            exact_groups += 1
            joint_supplied += joint_hit
            augmented_supplied += selected_hit
            case_groups.append((parent, exact, joint_hit, selected_hit))
        universal = set(selection["joint_universal_actions"])
        avoided = 0
        for row in selection["diverse_fallback_rows"]:
            branch = branches[int(row[0]) - 1]
            actions = set((tuple(point), str(color)) for point, color in
                          tuple(branch.first_actions) +
                          tuple(branch.second_actions[int(row[1])]))
            avoided += not bool(actions & universal)
        total_selected += len(selection["selected_rows"])
        total_fallbacks += len(selection["diverse_fallback_rows"])
        fallbacks_avoiding_universal += avoided
        cases.append({
            "name": name,
            "source_fixture_sha256": hashlib.sha256(raw).hexdigest(),
            "joint_prefixes": len(selection["joint_rows"]),
            "diverse_fallbacks": len(selection["diverse_fallback_rows"]),
            "selected_prefixes": len(selection["selected_rows"]),
            "joint_universal_actions": len(universal),
            "fallbacks_avoiding_every_universal_action": avoided,
            "exact_groups": tuple(case_groups),
            "selection_digest_frozen_before_consumed_target":
                selection["selected_prefix_digest"],
        })
    body = {
        "schema_version": 1,
        "cases": tuple(cases),
        "exact_child_groups": exact_groups,
        "joint_supplied_exact_groups": joint_supplied,
        "augmented_supplied_exact_groups": augmented_supplied,
        "selected_prefixes_across_cases": total_selected,
        "fallback_prefixes_across_cases": total_fallbacks,
        "fallbacks_avoiding_every_universal_action":
            fallbacks_avoiding_universal,
        "maximum_fallbacks_per_case": maximum_fallbacks,
        "universal_avoidance_required":
            bool(require_universal_avoidance),
        "candidate_selection_target_used": False,
        "targets_opened_only_after_selection_freeze": True,
        "consumed_development_audit_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_or_exponential_growth_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode()).hexdigest()}


def evaluate_compute_bounded():
    return evaluate(maximum_fallbacks=4,
                    require_universal_avoidance=True)


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    computed = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode()).hexdigest()
    if (computed != digest or row["candidate_selection_target_used"] or
            not row["targets_opened_only_after_selection_freeze"] or
            not row["consumed_development_audit_only"] or
            row["fresh_confirmation_claimed"] or
            row["autonomous_or_exponential_growth_claimed"] or
            row["joint_supplied_exact_groups"] !=
            row["exact_child_groups"] or
            row["augmented_supplied_exact_groups"] !=
            row["exact_child_groups"]):
        raise AssertionError("action-marginal prefix audit drift")
    return row


def main():
    row = validate_result(evaluate())
    print(json.dumps(row, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
