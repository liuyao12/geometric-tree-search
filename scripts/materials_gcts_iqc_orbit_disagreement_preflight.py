#!/usr/bin/env python3
"""Ten-nucleus preflight for an orbit-disagreement channel selector.

The previously consumed confirmation nucleus is now development evidence.  A
held-out fold uses the low-rank channel view whenever detailed and channel
top-score orbit cardinalities disagree, and the detailed view otherwise.  The
next confirmation centre is declared but neither its seed nor target is
constructed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_incidence_token_marking import (
    incidence_marking_digest, score_incidence_descriptor,
    score_incidence_descriptor_by_channel)
from materials_gcts_iqc_continuous_section_confirmation import (
    CONFIRMATION_CENTER as CONSUMED_CONFIRMATION_CENTER)
from materials_gcts_iqc_incidence_geometry_selection import (
    _fit_from_groups, _ranked_antichain, _statistics)
from materials_gcts_iqc_incidence_token_preflight import (
    _CandidateSource, _build_candidate_fixture,
    _candidate_groups_for_geometry, _key, _minimum_distance)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS, COMPLETED_TRAINING_CENTERS, DISTANCE_BIN_WIDTH,
    MAXIMUM_NEIGHBORS, NEIGHBORHOOD_REACH)


NEXT_CONFIRMATION_CENTER = (0., 50., 0.)
SELECTION_RULE = "channel when top-band cardinalities differ; detailed otherwise"


@dataclass(frozen=True)
class OrbitDisagreementPreflight:
    development_centers: tuple[tuple[float, float, float], ...]
    next_confirmation_center: tuple[float, float, float]
    selection_rule: str
    candidate_graph_digest: str
    descriptor_digest: str
    fold_model_digest: str
    candidates_by_group: tuple[int, ...]
    positives_by_group: tuple[int, ...]
    detailed_top_band_by_group: tuple[int, ...]
    channel_top_band_by_group: tuple[int, ...]
    selected_view_by_group: tuple[str, ...]
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    minimum_next_center_separation: float
    required_center_separation: float
    next_domains_disjoint: bool
    selection_rule_target_free: bool
    candidate_geometry_changed_between_views: bool
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def _top_band_size(scored):
    top = max(score for score, _row in scored)
    return sum(abs(score - top) <= 1e-15 for score, _row in scored)


def _development_sources():
    prototypes, connection, original_sources = _build_candidate_fixture()
    seed = _seed_crop(CONSUMED_CONFIRMATION_CENTER)
    target = _open_target(CONSUMED_CONFIRMATION_CENTER)
    proposals = _bounded_proposals(
        connection, prototypes, seed, CONSUMED_CONFIRMATION_CENTER)
    consumed_source = _CandidateSource(
        CONSUMED_CONFIRMATION_CENTER, proposals, tuple(seed.positions),
        tuple(seed.species), {_key(point): color for point, color in zip(
            target.positions, target.species)},
        _minimum_distance(seed.positions))
    sources = original_sources + (consumed_source,)
    return sources


def _development_groups(*, joint_role_geometry=False,
                        message_passing_rounds=0):
    return _candidate_groups_for_geometry(
        _development_sources(), neighborhood_reach=NEIGHBORHOOD_REACH,
        distance_bin_width=DISTANCE_BIN_WIDTH,
        maximum_neighbors=MAXIMUM_NEIGHBORS,
        joint_role_geometry=joint_role_geometry,
        message_passing_rounds=message_passing_rounds)


def evaluate() -> OrbitDisagreementPreflight:
    groups = _development_groups()
    statistics = _statistics(groups)
    detailed_bands = []
    channel_bands = []
    selected_views = []
    selected_groups = []
    model_digests = []
    for heldout_index, rows in enumerate(groups):
        model = _fit_from_groups(
            statistics, tuple(index for index in range(len(groups))
                              if index != heldout_index))
        model_digests.append(incidence_marking_digest(model))
        detailed = tuple((score_incidence_descriptor(
            model, row.descriptor), row) for row in rows)
        channel = tuple((score_incidence_descriptor_by_channel(
            model, row.descriptor), row) for row in rows)
        detailed_band = _top_band_size(detailed)
        channel_band = _top_band_size(channel)
        selected_view = "channel" if channel_band != detailed_band \
            else "detailed"
        detailed_bands.append(detailed_band)
        channel_bands.append(channel_band)
        selected_views.append(selected_view)
        selected_groups.append(_ranked_antichain(
            channel if selected_view == "channel" else detailed,
            ACTIONS_PER_NUCLEUS))

    correct_by_group = tuple(
        sum(row.successful for row in selected) for selected in selected_groups)
    selected_total = sum(map(len, selected_groups))
    correct_total = sum(correct_by_group)
    exact_groups = sum(count == ACTIONS_PER_NUCLEUS
                       for count in correct_by_group)
    minimum_separation = min(
        math.dist(NEXT_CONFIRMATION_CENTER, center)
        for center in COMPLETED_TRAINING_CENTERS +
        (CONSUMED_CONFIRMATION_CENTER,))
    required_separation = 2. * EVALUATION_TARGET_RADIUS
    passed = bool(
        selected_total == ACTIONS_PER_NUCLEUS * len(groups) and
        correct_total == selected_total and exact_groups == len(groups) and
        minimum_separation > required_separation)
    graph_digest = hashlib.sha256(repr(tuple(
        (row.group, row.point, row.color, row.minimum_distance)
        for group in groups for row in group)).encode()).hexdigest()
    descriptor_digest = hashlib.sha256(repr(tuple(
        (row.group, row.descriptor)
        for group in groups for row in group)).encode()).hexdigest()
    model_digest = hashlib.sha256(repr(tuple(model_digests)).encode()).hexdigest()
    return OrbitDisagreementPreflight(
        COMPLETED_TRAINING_CENTERS + (CONSUMED_CONFIRMATION_CENTER,),
        NEXT_CONFIRMATION_CENTER, SELECTION_RULE, graph_digest,
        descriptor_digest, model_digest, tuple(map(len, groups)),
        tuple(sum(row.successful for row in group) for group in groups),
        tuple(detailed_bands), tuple(channel_bands), tuple(selected_views),
        correct_by_group, selected_total, correct_total,
        selected_total - correct_total,
        correct_total / selected_total if selected_total else 0., exact_groups,
        minimum_separation, required_separation,
        minimum_separation > required_separation, True, False, False, passed,
        ("orbit-disagreement selector passes ten-nucleus development"
         if passed else
         "orbit-disagreement selector remains below the development gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
