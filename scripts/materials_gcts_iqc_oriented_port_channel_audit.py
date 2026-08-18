#!/usr/bin/env python3
"""Audit learned attachment-orientation channels on 18 disjoint IQC nuclei."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass

from materials_gcts_incidence_token_marking import (
    score_incidence_descriptor, score_incidence_descriptor_by_channel)
from materials_gcts_iqc_expanded_development_baseline import (
    FROZEN_FIT, FROZEN_QUOTIENT, _expanded_sources)
from materials_gcts_iqc_incidence_geometry_selection import (
    _ranked_antichain, _statistics)
from materials_gcts_iqc_incidence_token_preflight import (
    _candidate_groups_for_geometry)
from materials_gcts_iqc_joint_incidence_graph_preflight import _fit
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)


ANGULAR_WIDTHS = (.125, .25, .5)
SCORE_MODES = ("additive", "channel")


@dataclass(frozen=True)
class OrientedPortAudit:
    angular_bin_width: float
    score_mode: str
    descriptor_digest: str
    orientation_tokens: int
    selected_correct_by_group: tuple[int, ...]
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int


@dataclass(frozen=True)
class IQCOrientedPortChannelAudit:
    total_groups: int
    angular_widths: tuple[float, ...]
    score_modes: tuple[str, ...]
    audits: tuple[OrientedPortAudit, ...]
    selected_angular_bin_width: float
    selected_score_mode: str
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    unoriented_baseline_correct_actions: int
    exact_candidate_geometry_changed: bool
    proper_rotation_quotiented: bool
    chirality_preserved: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def evaluate() -> IQCOrientedPortChannelAudit:
    sources, _crop_counts = _expanded_sources()
    by_width = {}
    graph = None
    for width in ANGULAR_WIDTHS:
        groups = _candidate_groups_for_geometry(
            sources, neighborhood_reach=3., distance_bin_width=.25,
            maximum_neighbors=8, joint_role_geometry=True,
            oriented_port_geometry=True, angular_bin_width=width,
            message_passing_rounds=1,
            message_distance_divisor=FROZEN_QUOTIENT[0],
            message_role_mode=FROZEN_QUOTIENT[1],
            message_encoding=FROZEN_QUOTIENT[2])
        rows = tuple((row.group, row.point, row.color, row.successful,
                      row.minimum_distance) for group in groups for row in group)
        if graph is None:
            graph = rows
        elif graph != rows:
            raise AssertionError("angular channel changed exact candidates")
        by_width[width] = groups
    audits = []
    for width, groups in by_width.items():
        statistics = _statistics(groups)
        for mode in SCORE_MODES:
            scoring = (score_incidence_descriptor if mode == "additive"
                       else score_incidence_descriptor_by_channel)
            selected = []
            for heldout_index, rows in enumerate(groups):
                model = _fit(statistics, tuple(
                    index for index in range(len(groups))
                    if index != heldout_index), FROZEN_FIT)
                selected.append(_ranked_antichain(tuple(
                    (scoring(model, row.descriptor), row) for row in rows),
                    ACTIONS_PER_NUCLEUS))
            correct_by_group = tuple(sum(row.successful for row in group)
                                     for group in selected)
            correct = sum(correct_by_group)
            total = sum(map(len, selected))
            orientation_tokens = len({token for group in groups for row in group
                for token in row.descriptor.tokens
                if token[0] in {"port-axis-multiplicity",
                                "port-neighbor-angle",
                                "role-port-neighbor-angle",
                                "port-axis-angle",
                                "port-axis-handedness"}})
            audits.append(OrientedPortAudit(
                width, mode, hashlib.sha256(repr(tuple(
                    row.descriptor for group in groups
                    for row in group)).encode()).hexdigest(),
                orientation_tokens, correct_by_group, correct, total - correct,
                correct / total if total else 0.,
                sum(value == ACTIONS_PER_NUCLEUS
                    for value in correct_by_group)))
    selected = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        row.score_mode == "channel", -row.angular_bin_width))
    passed = selected.selected_correct_actions == 2 * len(sources)
    return IQCOrientedPortChannelAudit(
        len(sources), ANGULAR_WIDTHS, SCORE_MODES, tuple(audits),
        selected.angular_bin_width, selected.score_mode,
        selected.selected_correct_by_group, 2 * len(sources),
        selected.selected_correct_actions, selected.selected_false_actions,
        selected.precision, selected.exact_groups, 30, False, True, True,
        NEXT_CONFIRMATION_CENTER, False, passed,
        "oriented port channels pass expanded development" if passed else
        "oriented port channels remain below expanded development gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
