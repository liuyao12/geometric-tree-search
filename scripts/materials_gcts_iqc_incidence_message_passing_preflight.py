#!/usr/bin/env python3
"""Ten-nucleus preflight for bounded message passing on GCTS incidences."""

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
    FIT_GRID, JointFitAudit, JointFitSpec, _fit)
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER, _development_groups)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)


MESSAGE_ROUNDS = (1, 2)


@dataclass(frozen=True)
class MessagePassingAudit:
    rounds: int
    selected_fit: JointFitSpec
    fit_audits: tuple[JointFitAudit, ...]
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    message_node_types: int
    message_graph_types: int
    descriptor_digest: str


@dataclass(frozen=True)
class IncidenceMessagePassingPreflight:
    development_groups: int
    candidates_by_group: tuple[int, ...]
    positives_by_group: tuple[int, ...]
    candidate_graph_digest: str
    message_rounds: tuple[int, ...]
    round_audits: tuple[MessagePassingAudit, ...]
    selected_rounds: int
    selected_fit: JointFitSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    bounded_message_passing: bool
    selection_target_free: bool
    exact_candidate_geometry_changed: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def _round_audit(rounds):
    groups = _development_groups(
        joint_role_geometry=True, message_passing_rounds=rounds)
    statistics = _statistics(groups)
    fit_audits = []
    for spec in FIT_GRID:
        selected_groups = []
        model_digests = []
        weighted_fractions = []
        for heldout_index, rows in enumerate(groups):
            model = _fit(
                statistics, tuple(index for index in range(len(groups))
                                  if index != heldout_index), spec)
            model_digests.append(incidence_marking_digest(model))
            selected_groups.append(_ranked_antichain(tuple(
                (score_incidence_descriptor(model, row.descriptor), row)
                for row in rows), ACTIONS_PER_NUCLEUS))
            weighted_fractions.extend(sum(
                token in model.token_weights
                for token in row.descriptor.tokens) /
                max(1, len(row.descriptor.tokens)) for row in rows)
        correct_by_group = tuple(sum(row.successful for row in selected)
                                 for selected in selected_groups)
        total = sum(map(len, selected_groups))
        correct = sum(correct_by_group)
        fit_audits.append(JointFitAudit(
            spec, correct_by_group, total, correct, total - correct,
            correct / total if total else 0.,
            sum(count == ACTIONS_PER_NUCLEUS for count in correct_by_group),
            sum(weighted_fractions) / len(weighted_fractions),
            hashlib.sha256(repr(tuple(model_digests)).encode()).hexdigest()))
    selected = max(fit_audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        row.spec.minimum_groups, row.spec.minimum_support,
        -row.spec.shrinkage))
    node_types = {token for group in groups for row in group
                  for token in row.descriptor.tokens
                  if token[0] == "role-occupied-message-node"}
    graph_types = {token for group in groups for row in group
                   for token in row.descriptor.tokens
                   if token[0] == "role-occupied-message-graph"}
    descriptor_digest = hashlib.sha256(repr(tuple(
        (row.group, row.descriptor)
        for group in groups for row in group)).encode()).hexdigest()
    return groups, MessagePassingAudit(
        rounds, selected.spec, tuple(fit_audits),
        selected.selected_correct_by_group, selected.selected_actions,
        selected.selected_correct_actions, selected.selected_false_actions,
        selected.precision, selected.exact_groups, len(node_types),
        len(graph_types), descriptor_digest)


def evaluate() -> IncidenceMessagePassingPreflight:
    results = tuple(_round_audit(rounds) for rounds in MESSAGE_ROUNDS)
    groups = results[0][0]
    audits = tuple(result[1] for result in results)
    selected = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        -row.rounds))
    passed = bool(
        selected.selected_actions == ACTIONS_PER_NUCLEUS * len(groups) and
        selected.selected_correct_actions == selected.selected_actions and
        selected.exact_groups == len(groups))
    graph_digest = hashlib.sha256(repr(tuple(
        (row.group, row.point, row.color, row.minimum_distance)
        for group in groups for row in group)).encode()).hexdigest()
    return IncidenceMessagePassingPreflight(
        len(groups), tuple(map(len, groups)),
        tuple(sum(row.successful for row in group) for group in groups),
        graph_digest, MESSAGE_ROUNDS, audits, selected.rounds,
        selected.selected_fit, selected.selected_correct_by_group,
        selected.selected_actions, selected.selected_correct_actions,
        selected.selected_false_actions, selected.precision,
        selected.exact_groups, True, True, False,
        NEXT_CONFIRMATION_CENTER, False, passed,
        ("bounded incidence message passing passes ten-nucleus development"
         if passed else
         "bounded incidence message passing remains below development gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
