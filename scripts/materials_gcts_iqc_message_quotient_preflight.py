#!/usr/bin/env python3
"""Train-development grid for a finite quotient of IQC message colors."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass

from materials_gcts_incidence_token_marking import (
    incidence_marking_digest, score_incidence_descriptor)
from materials_gcts_iqc_incidence_geometry_selection import (
    _ranked_antichain, _statistics)
from materials_gcts_iqc_joint_incidence_graph_preflight import (
    JointFitSpec, _fit)
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER, _development_groups)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)


@dataclass(frozen=True, order=True)
class MessageQuotientSpec:
    distance_divisor: int
    role_mode: str
    encoding: str


QUOTIENT_GRID = (
    *(MessageQuotientSpec(divisor, role_mode, "exact")
      for divisor in (2, 4, 8)
      for role_mode in ("coarse", "colors")),
    *(MessageQuotientSpec(divisor, "coarse", "incidence")
      for divisor in (2, 4)),
)
FIT_GRID = (JointFitSpec(4, 2, .5), JointFitSpec(16, 4, .25))


@dataclass(frozen=True)
class QuotientAudit:
    quotient: MessageQuotientSpec
    fit: JointFitSpec
    node_types: int
    graph_types: int
    descriptor_digest: str
    model_digest: str
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int


@dataclass(frozen=True)
class MessageQuotientPreflight:
    quotient_grid: tuple[MessageQuotientSpec, ...]
    fit_grid: tuple[JointFitSpec, ...]
    audits: tuple[QuotientAudit, ...]
    selected_quotient: MessageQuotientSpec
    selected_fit: JointFitSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    exact_candidate_geometry_changed: bool
    selection_target_free: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def evaluate() -> MessageQuotientPreflight:
    audits = []
    for quotient in QUOTIENT_GRID:
        groups = _development_groups(
            joint_role_geometry=True,
            message_passing_rounds=1,
            message_distance_divisor=quotient.distance_divisor,
            message_role_mode=quotient.role_mode,
            message_encoding=quotient.encoding)
        statistics = _statistics(groups)
        node_types = {token for group in groups for row in group
                      for token in row.descriptor.tokens
                      if token[0] == "role-occupied-message-node"}
        graph_types = {token for group in groups for row in group
                       for token in row.descriptor.tokens
                       if token[0] == "role-occupied-message-graph"}
        descriptor_digest = hashlib.sha256(repr(tuple(
            (row.group, row.descriptor)
            for group in groups for row in group)).encode()).hexdigest()
        for fit in FIT_GRID:
            selected_groups = []
            model_digests = []
            for heldout_index, rows in enumerate(groups):
                model = _fit(statistics, tuple(
                    index for index in range(len(groups))
                    if index != heldout_index), fit)
                model_digests.append(incidence_marking_digest(model))
                selected_groups.append(_ranked_antichain(tuple(
                    (score_incidence_descriptor(model, row.descriptor), row)
                    for row in rows), ACTIONS_PER_NUCLEUS))
            correct_by_group = tuple(sum(
                row.successful for row in selected)
                for selected in selected_groups)
            total = sum(map(len, selected_groups))
            correct = sum(correct_by_group)
            audits.append(QuotientAudit(
                quotient, fit, len(node_types), len(graph_types),
                descriptor_digest, hashlib.sha256(repr(tuple(
                    model_digests)).encode()).hexdigest(), correct_by_group,
                total, correct, total - correct,
                correct / total if total else 0.,
                sum(count == ACTIONS_PER_NUCLEUS
                    for count in correct_by_group)))
    selected = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        -row.node_types, -row.graph_types,
        row.fit.minimum_groups, row.fit.minimum_support))
    passed = bool(selected.selected_actions == 20 and
                  selected.selected_correct_actions == 20 and
                  selected.exact_groups == 10)
    return MessageQuotientPreflight(
        QUOTIENT_GRID, FIT_GRID, tuple(audits), selected.quotient,
        selected.fit, selected.selected_correct_by_group,
        selected.selected_actions, selected.selected_correct_actions,
        selected.selected_false_actions, selected.precision,
        selected.exact_groups, False, True, NEXT_CONFIRMATION_CENTER,
        False, passed,
        ("finite message quotient passes ten-nucleus development"
         if passed else
         "finite message quotient remains below development gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
