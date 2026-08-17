#!/usr/bin/env python3
"""One-shot sealed IQC confirmation of the symmetry-orbit channel rule.

The rule and all hyperparameters were frozen in development commit 644d69f.
The reserved outer target is constructed exactly once, only after the fitted
model, exact candidate graph, both score views, selected view, and two selected
actions have immutable digests.  The target is used only for posthoc scoring.
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
    candidate_incidence_descriptors, incidence_marking_digest,
    score_incidence_descriptor, score_incidence_descriptor_by_channel)
from materials_gcts_iqc_continuous_section_confirmation import (
    CONFIRMATION_CENTER)
from materials_gcts_iqc_incidence_geometry_selection import (
    _fit_from_groups, _ranked_antichain, _statistics)
from materials_gcts_iqc_incidence_token_preflight import (
    _Candidate, _build_candidate_fixture, _key, _minimum_distance)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS, COMPLETED_TRAINING_CENTERS, DISTANCE_BIN_WIDTH,
    MAXIMUM_NEIGHBORS, NEIGHBORHOOD_REACH)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT


FROZEN_DEVELOPMENT_COMMIT = "644d69f"
SELECTION_RULE = "larger exact score-equality orbit; detailed wins ties"
PROTOCOL_PAYLOAD = (
    FROZEN_DEVELOPMENT_COMMIT, CONFIRMATION_CENTER,
    EVALUATION_TARGET_RADIUS, NEIGHBORHOOD_REACH, DISTANCE_BIN_WIDTH,
    MAXIMUM_NEIGHBORS, ACTIONS_PER_NUCLEUS, SELECTION_RULE)
PROTOCOL_DIGEST = hashlib.sha256(repr(PROTOCOL_PAYLOAD).encode()).hexdigest()


@dataclass(frozen=True)
class SymmetryOrbitChannelConfirmation:
    frozen_development_commit: str
    protocol_digest: str
    training_centers: tuple[tuple[float, float, float], ...]
    confirmation_center: tuple[float, float, float]
    neighborhood_reach: float
    distance_bin_width: float
    maximum_neighbors: int
    actions_requested: int
    model_digest: str
    candidate_graph_digest: str
    descriptor_digest: str
    detailed_top_band: int
    channel_top_band: int
    selected_view: str
    selected_action_digest: str
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    minimum_center_separation: float
    required_center_separation: float
    spatial_domains_disjoint: bool
    confirmation_seed_atoms: int
    confirmation_target_atoms: int
    event_order: tuple[str, ...]
    target_open_count: int
    target_materialized_after_selection_freeze: bool
    target_used_for_fit_or_selection: bool
    confirmation_gate_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def _top_band_size(scored):
    top = max(score for score, _row in scored)
    return sum(abs(score - top) <= 1e-15 for score, _row in scored)


def evaluate() -> SymmetryOrbitChannelConfirmation:
    events = []
    prototypes, connection, training_sources = _build_candidate_fixture()
    training_groups = []
    for source in training_sources:
        descriptors = candidate_incidence_descriptors(
            source.proposals, distance_scale=HIDDEN_UNIT,
            neighborhood_reach=NEIGHBORHOOD_REACH,
            distance_bin_width=DISTANCE_BIN_WIDTH,
            maximum_neighbors=MAXIMUM_NEIGHBORS,
            occupied_positions=source.seed_positions,
            occupied_species=source.seed_species)
        rows = []
        for point in sorted(source.proposals.votes):
            if any(math.dist(point, occupied) <
                   source.minimum_distance - 1e-8
                   for occupied in source.seed_positions):
                continue
            color = _dominant_source_color(source.proposals, point)
            rows.append(_Candidate(
                source.group, point, color, descriptors[point],
                source.truth.get(_key(point)) == color,
                source.minimum_distance))
        training_groups.append(tuple(rows))
    statistics = _statistics(tuple(training_groups))
    model = _fit_from_groups(
        statistics, tuple(range(len(training_groups))))
    model_digest = incidence_marking_digest(model)
    events.append("fit-frozen")

    seed = _seed_crop(CONFIRMATION_CENTER)
    proposals = _bounded_proposals(
        connection, prototypes, seed, CONFIRMATION_CENTER)
    minimum_distance = _minimum_distance(seed.positions)
    descriptors = candidate_incidence_descriptors(
        proposals, distance_scale=HIDDEN_UNIT,
        neighborhood_reach=NEIGHBORHOOD_REACH,
        distance_bin_width=DISTANCE_BIN_WIDTH,
        maximum_neighbors=MAXIMUM_NEIGHBORS,
        occupied_positions=seed.positions,
        occupied_species=seed.species)
    rows = []
    for point in sorted(proposals.votes):
        if any(math.dist(point, occupied) < minimum_distance - 1e-8
               for occupied in seed.positions):
            continue
        rows.append(_Candidate(
            CONFIRMATION_CENTER, point,
            _dominant_source_color(proposals, point), descriptors[point],
            False, minimum_distance))
    rows = tuple(rows)
    candidate_digest = hashlib.sha256(repr(tuple(
        (row.group, row.point, row.color, row.minimum_distance)
        for row in rows)).encode()).hexdigest()
    descriptor_digest = hashlib.sha256(repr(tuple(
        (row.group, row.descriptor) for row in rows)).encode()).hexdigest()
    events.append("candidate-graph-frozen")

    detailed = tuple((score_incidence_descriptor(model, row.descriptor), row)
                     for row in rows)
    channel = tuple((score_incidence_descriptor_by_channel(
        model, row.descriptor), row) for row in rows)
    detailed_band = _top_band_size(detailed)
    channel_band = _top_band_size(channel)
    selected_view = "channel" if channel_band > detailed_band else "detailed"
    selected = _ranked_antichain(
        channel if selected_view == "channel" else detailed,
        ACTIONS_PER_NUCLEUS)
    selected_digest = hashlib.sha256(repr((
        PROTOCOL_DIGEST, model_digest, candidate_digest, descriptor_digest,
        detailed_band, channel_band, selected_view,
        tuple((row.point, row.color) for row in selected))).encode()).hexdigest()
    events.append("selection-frozen")

    target_open_count = 0
    if events[-1] != "selection-frozen" or not selected_digest:
        raise AssertionError("target cannot open before selection freeze")
    target = _open_target(CONFIRMATION_CENTER)
    target_open_count += 1
    events.append("target-opened")
    truth = {_key(point): color for point, color in zip(
        target.positions, target.species)}
    correct = sum(truth.get(_key(row.point)) == row.color for row in selected)
    false = len(selected) - correct
    events.append("scored")

    minimum_separation = min(math.dist(CONFIRMATION_CENTER, center)
                             for center in COMPLETED_TRAINING_CENTERS)
    required_separation = 2. * EVALUATION_TARGET_RADIUS
    disjoint = minimum_separation > required_separation
    passed = bool(
        len(selected) == ACTIONS_PER_NUCLEUS and correct == len(selected) and
        not false and disjoint and target_open_count == 1 and
        tuple(events) == ("fit-frozen", "candidate-graph-frozen",
                          "selection-frozen", "target-opened", "scored"))
    return SymmetryOrbitChannelConfirmation(
        FROZEN_DEVELOPMENT_COMMIT, PROTOCOL_DIGEST,
        COMPLETED_TRAINING_CENTERS, CONFIRMATION_CENTER,
        NEIGHBORHOOD_REACH, DISTANCE_BIN_WIDTH, MAXIMUM_NEIGHBORS,
        ACTIONS_PER_NUCLEUS, model_digest, candidate_digest,
        descriptor_digest, detailed_band, channel_band, selected_view,
        selected_digest, len(selected), correct, false,
        correct / len(selected) if selected else 0., minimum_separation,
        required_separation, disjoint, len(seed.positions),
        len(target.positions), tuple(events), target_open_count, True, False,
        passed, False,
        ("symmetry-orbit channel rule confirms on the reserved IQC nucleus"
         if passed else
         "symmetry-orbit channel rule fails on the reserved IQC nucleus"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
