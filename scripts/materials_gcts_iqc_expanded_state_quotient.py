#!/usr/bin/env python3
"""Fit finite conditional incidence states on 18 disjoint IQC nuclei."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass

from materials_gcts_incidence_state_marking import (
    IncidenceStateSpec, fit_incidence_state_group_statistics,
    incidence_state_group_statistics,
    incidence_state_marking_digest, score_incidence_state_marking)
from materials_gcts_incidence_token_marking import IncidenceTokenExample
from materials_gcts_iqc_expanded_development_baseline import _expanded_groups
from materials_gcts_iqc_incidence_geometry_selection import _ranked_antichain
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)


SIGNATURE_LEVELS = (
    ("role-occupied-message-node", "role-occupied-message-edge",
     "role-occupied-message-graph", "coarse-role", "predicted-colors"),
    ("role-occupied-message-node", "role-occupied-message-graph",
     "coarse-role"),
    ("role-occupied-message-graph", "coarse-role"),
    ("coarse-role", "predicted-colors", "occupied-count"),
)
STATE_GRID = tuple(IncidenceStateSpec(
    SIGNATURE_LEVELS, support, groups, shrinkage)
    for support, groups, shrinkage in (
        (4, 2, 1.), (16, 3, 1.), (32, 4, 1.), (64, 5, 1.)))


@dataclass(frozen=True)
class StateQuotientAudit:
    spec: IncidenceStateSpec
    supported_states_by_fold_and_level: tuple[tuple[int, ...], ...]
    fold_model_digest: str
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int


@dataclass(frozen=True)
class ExpandedStateQuotient:
    total_groups: int
    state_grid: tuple[IncidenceStateSpec, ...]
    audits: tuple[StateQuotientAudit, ...]
    selected_spec: IncidenceStateSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    exact_candidate_geometry_changed: bool
    expanded_targets_used_for_development_fit: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def evaluate() -> ExpandedStateQuotient:
    groups, _crop_counts = _expanded_groups()
    examples_by_group = tuple(tuple(IncidenceTokenExample(
        row.group, row.descriptor, row.successful) for row in group)
        for group in groups)
    statistics = incidence_state_group_statistics(
        examples_by_group, signature_levels=SIGNATURE_LEVELS)
    audits = []
    for spec in STATE_GRID:
        selected = []
        state_counts = []
        model_digests = []
        for heldout_index, rows in enumerate(groups):
            model = fit_incidence_state_group_statistics(
                statistics, tuple(index for index in range(len(groups))
                                  if index != heldout_index), spec=spec)
            state_counts.append(tuple(sum(
                row.total >= spec.minimum_support and
                row.independent_groups >= spec.minimum_groups
                for row in level.values())
                for level in model.evidence_by_level))
            model_digests.append(incidence_state_marking_digest(model))
            selected.append(_ranked_antichain(tuple(
                (score_incidence_state_marking(model, row.descriptor), row)
                for row in rows), ACTIONS_PER_NUCLEUS))
        correct_by_group = tuple(sum(row.successful for row in group)
                                 for group in selected)
        total = sum(map(len, selected))
        correct = sum(correct_by_group)
        audits.append(StateQuotientAudit(
            spec, tuple(state_counts), hashlib.sha256(repr(tuple(
                model_digests)).encode()).hexdigest(), correct_by_group,
            total, correct, total - correct,
            correct / total if total else 0.,
            sum(value == ACTIONS_PER_NUCLEUS for value in correct_by_group)))
    selected = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        row.spec.minimum_groups, row.spec.minimum_support))
    passed = selected.selected_actions == 2 * len(groups) and \
        selected.selected_correct_actions == selected.selected_actions
    return ExpandedStateQuotient(
        len(groups), STATE_GRID, tuple(audits), selected.spec,
        selected.selected_correct_by_group, selected.selected_actions,
        selected.selected_correct_actions, selected.selected_false_actions,
        selected.precision, selected.exact_groups, False, True,
        NEXT_CONFIRMATION_CENTER, False, passed,
        "finite conditional states pass expanded development" if passed else
        "finite conditional states remain below expanded development gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
