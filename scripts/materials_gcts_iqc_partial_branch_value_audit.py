#!/usr/bin/env python3
"""Fixture-backed audit of depth-conditioned IQC partial-branch values."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_recurrent_branch_value_heads import (
    DepthBranchExample, fit_grouped_depth_branch_values)
from materials_gcts_recurrent_branch_value import RecurrentBranchExample, _fit
from materials_gcts_recurrent_state_diverse_beam import (
    RecurrentStateBeamCandidate, RecurrentStateBeamSpec,
    select_recurrent_state_diverse_beam)


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixtures/iqc_partial_branch_value_training.json"
CLOSED_LOOP = ROOT / \
    "fixtures/iqc_partial_branch_value_closed_loop_diagnostic.json"
EXPECTED_CANDIDATE_DIGEST = \
    "649fd2786f9030051bf160f6ff9dbc850c89002f25d44cc25d907e9c2769606c"
EXPECTED_MODEL_DIGEST = \
    "02a2982c4b155f823dfb29b9532a9d6b016e00adc4c57c10e09bfffc5e4fe572"
DIVERSITY_SPECS = (
    (1, RecurrentStateBeamSpec(4., 1, 4)),
    (2, RecurrentStateBeamSpec(4., 2, 4)),
    (3, RecurrentStateBeamSpec(2., 1, 8)),
)


@dataclass(frozen=True)
class IQCPartialBranchValueAudit:
    groups: int
    stages: int
    examples: int
    positive_examples: int
    search_schedule: tuple[int, ...]
    diversity_beam: int
    color_population_quota: int
    candidate_digest: str
    candidate_digest_matches: bool
    selected_neighbors_by_depth: tuple[tuple[int, int], ...]
    supplied_stages_by_depth: tuple[int, ...]
    selected_exact_stages_by_depth: tuple[int, ...]
    supplied_stages: int
    selected_exact_stages: int
    selected_precision: float
    model_digest: str
    model_digest_matches: bool
    branch_features_use_coordinates_or_ids: bool
    target_used_for_fit_or_capacity_selection: bool
    frozen_snapshot_gate_passed: bool
    recurrent_state_diversity_specs: tuple[tuple[int, float, int, int], ...]
    recurrent_state_supplied_stages_by_depth: tuple[int, ...]
    recurrent_state_retained_exact_by_depth: tuple[int, ...]
    recurrent_state_retained_exact_stages: int
    recurrent_state_snapshot_gate_passed: bool
    consumed_closed_loop_beam_widths: tuple[int, ...]
    consumed_closed_loop_exact_terminals: tuple[int, ...]
    consumed_closed_loop_selected_correct_sites: tuple[int, ...]
    consumed_target_reopened_only_after_confirmation: bool
    consumed_recurrent_state_candidate_counts: tuple[int, ...]
    consumed_recurrent_state_retained_counts: tuple[int, ...]
    consumed_recurrent_state_exact_terminals: int
    consumed_recurrent_state_selected_correct_sites: int
    autonomous_closed_loop_gate_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def evaluate() -> IQCPartialBranchValueAudit:
    payload = json.loads(FIXTURE.read_text())
    examples = tuple(DepthBranchExample(
        int(row["group"]), int(row["depth"]), tuple(row["features"]),
        tuple(row["action_colors"]), bool(row["successful"]))
        for row in payload["examples"])
    digest = hashlib.sha256(repr(tuple(
        (row.group, row.features, row.action_colors, row.successful)
        for row in examples)).encode()).hexdigest()
    model, audit = fit_grouped_depth_branch_values(
        examples, feature_names=tuple(payload["feature_names"]),
        color_keys=tuple(payload["color_keys"]),
        candidate_neighbors=tuple(payload["candidate_neighbors"]),
        beta_prior=float(payload["beta_prior"]))
    chosen = dict(audit.selected_neighbors_by_depth)
    selected = []
    supplied = []
    for depth in audit.depths:
        row = next(row for row in audit.capacities
                   if row.depth == depth and
                   row.neighbors == chosen[depth])
        selected.append(row.selected_exact_groups)
        supplied.append(row.supplied_groups)
    snapshot_passed = (
        audit.supplied_stages >= 85 and audit.selected_precision >= .95)
    grouped = {(group, depth): [] for group in range(audit.groups)
               for depth in audit.depths}
    for ordinal, row in enumerate(examples):
        grouped[row.group, row.depth].append((ordinal, row))
    retained_by_depth = []
    supplied_by_depth = []
    selected_neighbors = dict(audit.selected_neighbors_by_depth)
    for depth, spec in DIVERSITY_SPECS:
        supplied_count = retained_count = 0
        for heldout in range(audit.groups):
            training = tuple(RecurrentBranchExample(
                row.group, row.features, row.action_colors, row.successful)
                for row in examples
                if row.depth == depth and row.group != heldout)
            head = _fit(
                training, tuple(payload["feature_names"]),
                tuple(payload["color_keys"]), selected_neighbors[depth],
                float(payload["beta_prior"]))
            stage = grouped[heldout, depth]
            supplied_here = any(row.successful for _ordinal, row in stage)
            candidates = tuple(RecurrentStateBeamCandidate(
                row.features, row.action_colors,
                (heldout, depth, ordinal), row)
                for ordinal, row in stage)
            retained_rows = select_recurrent_state_diverse_beam(
                head, candidates, spec)
            retained_here = any(row.payload.successful
                                for row in retained_rows)
            supplied_count += int(supplied_here)
            retained_count += int(supplied_here and retained_here)
        supplied_by_depth.append(supplied_count)
        retained_by_depth.append(retained_count)
    diversity_retained = sum(retained_by_depth)
    diversity_passed = diversity_retained == sum(supplied_by_depth) == 85
    closed = json.loads(CLOSED_LOOP.read_text())
    closed_passed = any(closed["exact_terminal_configurations"])
    return IQCPartialBranchValueAudit(
        audit.groups, len(audit.depths) * audit.groups, audit.examples,
        audit.positive_examples, tuple(payload["search_schedule"]),
        int(payload["diversity_beam"]),
        int(payload["color_population_quota"]), digest,
        digest == EXPECTED_CANDIDATE_DIGEST == payload["candidate_digest"],
        audit.selected_neighbors_by_depth, tuple(supplied), tuple(selected),
        audit.supplied_stages, audit.selected_exact_stages,
        audit.selected_precision, audit.model_digest,
        audit.model_digest == EXPECTED_MODEL_DIGEST, False,
        audit.target_used_for_fit_or_capacity_selection, snapshot_passed,
        tuple((depth, spec.state_bin_width, spec.quota_per_state,
               spec.beam_width) for depth, spec in DIVERSITY_SPECS),
        tuple(supplied_by_depth), tuple(retained_by_depth),
        diversity_retained, diversity_passed,
        tuple(closed["beam_widths"]),
        tuple(closed["exact_terminal_configurations"]),
        tuple(closed["selected_correct_sites"]),
        bool(closed["target_reopened_after_immutable_confirmation"]),
        tuple(closed["recurrent_state_candidate_counts"]),
        tuple(closed["recurrent_state_retained_counts"]),
        int(closed["recurrent_state_exact_terminals"]),
        int(closed["recurrent_state_selected_correct_sites"]),
        closed_passed, False,
        ("recurrent state diversity preserves every supplied frozen prefix "
         "but remains red in closed-loop autonomous IQC scheduling"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
