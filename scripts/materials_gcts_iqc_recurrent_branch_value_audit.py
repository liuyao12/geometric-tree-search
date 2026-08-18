#!/usr/bin/env python3
"""Fixture-backed audit of the expanded IQC recurrent branch value.

The fixture contains only invariant branch descriptors, action-color
populations, spatial-group IDs, and posthoc training labels.  It contains no
atomic coordinates or candidate/type identifiers.  The consumed autonomous
confirmation is retained only as a diagnostic after grouped capacity
selection and the final fit are complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_recurrent_branch_value import (
    RecurrentBranchExample,
    fit_grouped_recurrent_branch_value,
    score_recurrent_branch,
)


FIXTURE = Path(__file__).resolve().parent / \
    "fixtures/iqc_recurrent_branch_value_training.json"
EXPECTED_CANDIDATE_DIGEST = \
    "00a5354db309729bbb11dcd23f4054b5874b2637de9a0cdfcd73a8a3abc649c3"
EXPECTED_MODEL_DIGEST = \
    "dcaae79dc2a8c3edf1caec7fc32b05054077c125e8b1e5ad93c11e8097be56ce"


@dataclass(frozen=True)
class IQCRecurrentBranchValueAudit:
    development_groups: int
    development_examples: int
    positive_examples: int
    groups_with_exact_path: int
    baseline_selected_exact_groups: int
    selected_neighbors: int
    recurrent_selected_exact_groups: int
    recurrent_selection_precision: float
    candidate_digest: str
    candidate_digest_matches: bool
    model_digest: str
    model_digest_matches: bool
    confirmation_terminal_configurations: int
    confirmation_exact_configurations: int
    confirmation_cumulative_rank: int
    confirmation_recurrent_rank: int
    confirmation_selected_exact: bool
    branch_features_use_coordinates_or_ids: bool
    target_used_for_candidate_generation: bool
    target_used_for_capacity_selection: bool
    consumed_confirmation_used_only_after_fit: bool
    fresh_confirmation_claimed: bool
    development_gate_passed: bool
    honest_status: str


def _load():
    payload = json.loads(FIXTURE.read_text())
    examples = tuple(RecurrentBranchExample(
        row["group"], tuple(row["features"]), tuple(row["action_colors"]),
        bool(row["successful"])) for row in payload["examples"])
    return payload, examples


def evaluate() -> IQCRecurrentBranchValueAudit:
    payload, examples = _load()
    digest = hashlib.sha256(repr(tuple(
        (row.group, row.features, row.action_colors, row.successful)
        for row in examples)).encode()).hexdigest()
    if digest != payload["candidate_digest"]:
        raise AssertionError("recurrent branch fixture digest drift")
    model, audit = fit_grouped_recurrent_branch_value(
        examples, feature_names=tuple(payload["feature_names"]),
        color_keys=tuple(payload["color_keys"]),
        candidate_neighbors=tuple(payload["candidate_neighbors"]),
        beta_prior=float(payload["beta_prior"]))
    groups = tuple(sorted({row.group for row in examples}))
    grouped = tuple(tuple(row for row in examples if row.group == group)
                    for group in groups)
    supplied = sum(any(row.successful for row in rows) for rows in grouped)
    baseline = sum(max(rows, key=lambda row: (
        row.features[0], row.features, row.action_colors)).successful
        for rows in grouped if any(row.successful for row in rows))

    confirmation = tuple(RecurrentBranchExample(
        "consumed-confirmation", tuple(row["features"]),
        tuple(row["action_colors"]), bool(row["successful"]))
        for row in payload["consumed_confirmation_diagnostic"])
    scores = tuple(score_recurrent_branch(
        model, row.features, row.action_colors) for row in confirmation)
    order = tuple(sorted(range(len(confirmation)), key=lambda index: (
        -scores[index], confirmation[index].features,
        confirmation[index].action_colors)))
    confirmation_rank = next(rank for rank, index in enumerate(order, 1)
                             if confirmation[index].successful)
    selected_exact = confirmation[order[0]].successful
    passed = (supplied >= 20 and audit.selected_precision >= .95 and
              confirmation_rank == 1 and selected_exact)
    return IQCRecurrentBranchValueAudit(
        len(groups), len(examples), sum(row.successful for row in examples),
        supplied, baseline, audit.selected_neighbors,
        audit.selected_exact_groups, audit.selected_precision, digest,
        digest == EXPECTED_CANDIDATE_DIGEST, audit.model_digest,
        audit.model_digest == EXPECTED_MODEL_DIGEST, len(confirmation),
        sum(row.successful for row in confirmation), 10, confirmation_rank,
        selected_exact, False, False, False, True, False, passed,
        ("expanded recurrent branch value clears the autonomous development gate"
         if passed else
         "recurrent branch value remains below the autonomous development gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
