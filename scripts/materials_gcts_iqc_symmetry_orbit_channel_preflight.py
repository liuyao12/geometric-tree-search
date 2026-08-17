#!/usr/bin/env python3
"""Symmetry-orbit selection between detailed and low-rank GCTS sections.

The exact 44,602-action graph is unchanged.  For each held-out IQC nucleus a
token marking is fit on the other eight.  Two deterministic views are scored:
the detailed token section and a channel projection that averages within each
semantic token family.  The view whose exact top-score equality band contains
more actions is chosen; ties prefer the detailed section.  This selection uses
neither target labels nor absolute coordinates.  The reserved confirmation
nucleus is not imported or constructed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass

from materials_gcts_incidence_token_marking import (
    incidence_marking_digest, score_incidence_descriptor,
    score_incidence_descriptor_by_channel)
from materials_gcts_iqc_channel_count_confirmation import (
    CONFIRMATION_CENTER as EIGHTH_CENTER)
from materials_gcts_iqc_contextual_value_confirmation import (
    CONFIRMATION_CENTER as NINTH_CENTER)
from materials_gcts_iqc_incidence_geometry_selection import (
    _fit_from_groups, _ranked_antichain, _statistics)
from materials_gcts_iqc_incidence_token_preflight import (
    _build_candidate_sources, _candidate_groups_for_geometry)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    CONFIRMATION_CENTER as FOURTH_CENTER, TRAINING_CENTERS)
from materials_gcts_iqc_rank_value_confirmation import (
    CONFIRMATION_CENTER as SIXTH_CENTER)
from materials_gcts_iqc_robust_persistent_beam_confirmation import (
    CONFIRMATION_CENTER as FIFTH_CENTER)
from materials_gcts_iqc_three_context_confirmation import (
    CONFIRMATION_CENTER as TENTH_CENTER)


NEIGHBORHOOD_REACH = 3.
DISTANCE_BIN_WIDTH = .25
MAXIMUM_NEIGHBORS = 8
ACTIONS_PER_NUCLEUS = 2
COMPLETED_TRAINING_CENTERS = (
    TRAINING_CENTERS + (FOURTH_CENTER, FIFTH_CENTER, SIXTH_CENTER,
                        EIGHTH_CENTER, NINTH_CENTER, TENTH_CENTER))


@dataclass(frozen=True)
class SymmetryOrbitChannelPreflight:
    training_centers: tuple[tuple[float, float, float], ...]
    neighborhood_reach: float
    distance_bin_width: float
    maximum_neighbors: int
    candidate_graph_digest: str
    descriptor_digest: str
    fold_model_digest: str
    candidates_by_group: tuple[int, ...]
    positives_by_group: tuple[int, ...]
    detailed_top_band_by_group: tuple[int, ...]
    channel_top_band_by_group: tuple[int, ...]
    selected_view_by_group: tuple[str, ...]
    detailed_correct_by_group: tuple[int, ...]
    channel_correct_by_group: tuple[int, ...]
    orbit_selected_correct_by_group: tuple[int, ...]
    detailed_correct_actions: int
    channel_correct_actions: int
    orbit_selected_actions: int
    orbit_selected_correct_actions: int
    orbit_selected_false_actions: int
    orbit_selected_precision: float
    exact_groups: int
    selection_rule_target_free: bool
    candidate_geometry_changed_between_views: bool
    reserved_confirmation_center_imported_or_accessed: bool
    development_gate_passed: bool
    honest_status: str


def _top_band_size(scored):
    top = max(score for score, _row in scored)
    return sum(abs(score - top) <= 1e-15 for score, _row in scored)


def _score(rows, model, scorer):
    return tuple((scorer(model, row.descriptor), row) for row in rows)


def evaluate():
    groups = _candidate_groups_for_geometry(
        _build_candidate_sources(),
        neighborhood_reach=NEIGHBORHOOD_REACH,
        distance_bin_width=DISTANCE_BIN_WIDTH,
        maximum_neighbors=MAXIMUM_NEIGHBORS)
    statistics = _statistics(groups)
    detailed_bands = []
    channel_bands = []
    selected_views = []
    detailed_groups = []
    channel_groups = []
    selected_groups = []
    model_digests = []
    for heldout_index, rows in enumerate(groups):
        model = _fit_from_groups(
            statistics, tuple(index for index in range(len(groups))
                              if index != heldout_index))
        model_digests.append(incidence_marking_digest(model))
        detailed = _score(rows, model, score_incidence_descriptor)
        channel = _score(
            rows, model, score_incidence_descriptor_by_channel)
        detailed_band = _top_band_size(detailed)
        channel_band = _top_band_size(channel)
        selected_view = "channel" if channel_band > detailed_band \
            else "detailed"
        detailed_bands.append(detailed_band)
        channel_bands.append(channel_band)
        selected_views.append(selected_view)
        detailed_groups.append(_ranked_antichain(
            detailed, ACTIONS_PER_NUCLEUS))
        channel_groups.append(_ranked_antichain(
            channel, ACTIONS_PER_NUCLEUS))
        selected_groups.append(_ranked_antichain(
            channel if selected_view == "channel" else detailed,
            ACTIONS_PER_NUCLEUS))

    correct = lambda selected: tuple(
        sum(row.successful for row in group) for group in selected)
    detailed_correct = correct(detailed_groups)
    channel_correct = correct(channel_groups)
    selected_correct = correct(selected_groups)
    selected_total = sum(map(len, selected_groups))
    selected_correct_total = sum(selected_correct)
    exact_groups = sum(count == ACTIONS_PER_NUCLEUS
                       for count in selected_correct)
    passed = bool(
        selected_total == ACTIONS_PER_NUCLEUS * len(groups) and
        selected_correct_total == selected_total and
        exact_groups == len(groups))
    graph_digest = hashlib.sha256(repr(tuple(
        (row.group, row.point, row.color, row.minimum_distance)
        for group in groups for row in group)).encode()).hexdigest()
    descriptor_digest = hashlib.sha256(repr(tuple(
        (row.group, row.descriptor)
        for group in groups for row in group)).encode()).hexdigest()
    model_digest = hashlib.sha256(repr(tuple(model_digests)).encode()).hexdigest()
    return SymmetryOrbitChannelPreflight(
        COMPLETED_TRAINING_CENTERS, NEIGHBORHOOD_REACH,
        DISTANCE_BIN_WIDTH, MAXIMUM_NEIGHBORS, graph_digest,
        descriptor_digest, model_digest,
        tuple(map(len, groups)),
        tuple(sum(row.successful for row in group) for group in groups),
        tuple(detailed_bands), tuple(channel_bands), tuple(selected_views),
        detailed_correct, channel_correct, selected_correct,
        sum(detailed_correct), sum(channel_correct), selected_total,
        selected_correct_total, selected_total - selected_correct_total,
        selected_correct_total / selected_total if selected_total else 0.,
        exact_groups, True, False, False, passed,
        ("symmetry-orbit channel selection passes the development gate"
         if passed else
         "symmetry-orbit channel selection remains below the development "
         "gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
