#!/usr/bin/env python3
"""Candidate-level IQC gate for an ID-free local incidence marking.

The nine completed nuclei are the only scored configurations opened here.
For each held-out nucleus the marking is fit on the other eight.  A common
threshold is then calibrated from complete out-of-fold score levels; the
reserved confirmation nucleus is neither imported nor constructed.
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
    IncidenceTokenExample, candidate_incidence_descriptors,
    fit_incidence_token_marking, score_incidence_descriptor)
from materials_gcts_iqc_continuous_section_confirmation import (
    COMPLETED_TRAINING_CENTERS)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_recursive_connections import (
    learn_recursive_connection_marking, local_cluster_types)


MINIMUM_TOKEN_SUPPORT = 4
MINIMUM_TOKEN_GROUPS = 2
TOKEN_SHRINKAGE = .5
MINIMUM_ACTION_PRECISION = .95
REQUIRED_SELECTED_ACTIONS = 2 * len(COMPLETED_TRAINING_CENTERS)
REQUIRED_EXACT_GROUPS = len(COMPLETED_TRAINING_CENTERS)


@dataclass(frozen=True)
class _Candidate:
    group: tuple[float, float, float]
    point: tuple[float, float, float]
    color: str
    descriptor: object
    successful: bool
    minimum_distance: float


@dataclass(frozen=True)
class _CandidateSource:
    group: tuple[float, float, float]
    proposals: object
    seed_positions: tuple[tuple[float, float, float], ...]
    seed_species: tuple[str, ...]
    truth: dict[tuple[float, float, float], str]
    minimum_distance: float


@dataclass(frozen=True)
class CandidateIncidencePreflight:
    training_centers: tuple[tuple[float, float, float], ...]
    candidate_graph_digest: str
    candidates_by_group: tuple[int, ...]
    positives_by_group: tuple[int, ...]
    total_candidates: int
    positive_candidates: int
    minimum_token_support: int
    minimum_token_groups: int
    token_shrinkage: float
    fold_model_digests: tuple[str, ...]
    out_of_fold_logloss: float
    mean_seen_token_fraction: float
    mean_weighted_token_fraction: float
    calibrated_threshold: float
    threshold_selected_candidates: int
    threshold_correct_candidates: int
    threshold_precision: float
    antichain_selected_by_group: tuple[int, ...]
    antichain_correct_by_group: tuple[int, ...]
    antichain_selected_candidates: int
    antichain_correct_candidates: int
    antichain_false_candidates: int
    antichain_precision: float
    exact_groups: int
    reserved_confirmation_center_imported_or_accessed: bool
    preflight_passed: bool
    honest_status: str


def _minimum_distance(positions):
    return min(math.dist(left, right)
               for index, left in enumerate(positions)
               for right in positions[index + 1:])


def _key(point):
    return tuple(round(value, 6) for value in point)


def _build_candidate_fixture():
    origin_seed, _ = oracle_patch(3, 9.)
    origin_target, _ = oracle_patch(4, EVALUATION_TARGET_RADIUS)
    prototypes = local_cluster_types(
        origin_seed.positions, origin_seed.species, CLUSTER_EDGES)
    connection = learn_recursive_connection_marking(
        origin_seed.positions, prototypes, origin_target.positions,
        HIDDEN_UNIT, minimum_purity=.5,
        target_colors=origin_target.species)
    seeds = (origin_seed,) + tuple(
        _seed_crop(center) for center in COMPLETED_TRAINING_CENTERS[1:])
    targets = (origin_target,) + tuple(
        _open_target(center) for center in COMPLETED_TRAINING_CENTERS[1:])
    sources = []
    for center, seed, target in zip(
            COMPLETED_TRAINING_CENTERS, seeds, targets):
        proposals = _bounded_proposals(connection, prototypes, seed, center)
        truth = {_key(point): color for point, color in zip(
            target.positions, target.species)}
        minimum = _minimum_distance(seed.positions)
        sources.append(_CandidateSource(
            center, proposals, tuple(seed.positions), tuple(seed.species),
            truth, minimum))
    return prototypes, connection, tuple(sources)


def _build_candidate_sources():
    return _build_candidate_fixture()[2]


def _candidate_groups_for_geometry(
        sources, *, neighborhood_reach: float = 3.,
        distance_bin_width: float = .5, maximum_neighbors: int = 8,
        joint_role_geometry: bool = False,
        message_passing_rounds: int = 0,
        message_distance_divisor: int = 1,
        message_role_mode: str = "exact",
        message_encoding: str = "exact"):
    groups = []
    for source in sources:
        descriptors = candidate_incidence_descriptors(
            source.proposals, distance_scale=HIDDEN_UNIT,
            neighborhood_reach=neighborhood_reach,
            distance_bin_width=distance_bin_width,
            maximum_neighbors=maximum_neighbors,
            joint_role_geometry=joint_role_geometry,
            message_passing_rounds=message_passing_rounds,
            message_distance_divisor=message_distance_divisor,
            message_role_mode=message_role_mode,
            message_encoding=message_encoding,
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
        groups.append(tuple(rows))
    return tuple(groups)


def _build_candidate_groups(*, neighborhood_reach: float = 3.,
                            distance_bin_width: float = .5,
                            maximum_neighbors: int = 8):
    return _candidate_groups_for_geometry(
        _build_candidate_sources(), neighborhood_reach=neighborhood_reach,
        distance_bin_width=distance_bin_width,
        maximum_neighbors=maximum_neighbors)


def _threshold(scores):
    """Choose a complete score level with >=95% OOF precision."""
    best = None
    ordered = sorted(scores, key=lambda row: -row[0])
    selected = correct = 0
    cursor = 0
    while cursor < len(ordered):
        threshold = ordered[cursor][0]
        end = cursor
        while (end < len(ordered) and
               abs(ordered[end][0] - threshold) <= 1e-15):
            correct += int(ordered[end][1].successful)
            selected += 1
            end += 1
        precision = correct / selected
        if precision < MINIMUM_ACTION_PRECISION:
            cursor = end
            continue
        objective = (correct, selected, threshold)
        if best is None or objective > best[0]:
            best = (objective, threshold, selected, correct, precision)
        cursor = end
    return (math.inf, 0, 0, 0.) if best is None else best[1:]


def _antichain(rows, threshold):
    accepted = []
    for score, row in sorted(rows, key=lambda item: (
            -item[0], item[1].point, item[1].color)):
        if score < threshold - 1e-15:
            continue
        if any(math.dist(row.point, prior.point) < row.minimum_distance - 1e-8
               for prior in accepted):
            continue
        accepted.append(row)
    return tuple(accepted)


def evaluate():
    groups = _build_candidate_groups()
    graph_digest = hashlib.sha256(repr(tuple(
        (row.group, row.point, row.color, row.descriptor, row.successful)
        for group in groups for row in group)).encode()).hexdigest()
    scored_groups = []
    fold_digests = []
    seen_fractions = []
    weighted_fractions = []
    for heldout_index, heldout in enumerate(groups):
        examples = tuple(IncidenceTokenExample(
            row.group, row.descriptor, row.successful)
            for index, group in enumerate(groups) if index != heldout_index
            for row in group)
        marking = fit_incidence_token_marking(
            examples, minimum_support=MINIMUM_TOKEN_SUPPORT,
            minimum_groups=MINIMUM_TOKEN_GROUPS,
            shrinkage=TOKEN_SHRINKAGE)
        fold_digests.append(hashlib.sha256(
            repr(marking).encode()).hexdigest())
        scored = tuple((score_incidence_descriptor(
            marking, row.descriptor), row) for row in heldout)
        scored_groups.append(scored)
        for _score, row in scored:
            token_count = max(1, len(row.descriptor.tokens))
            seen_fractions.append(sum(
                token in marking.token_evidence
                for token in row.descriptor.tokens) / token_count)
            weighted_fractions.append(sum(
                token in marking.token_weights
                for token in row.descriptor.tokens) / token_count)
    scores = tuple(item for group in scored_groups for item in group)
    threshold, threshold_selected, threshold_correct, threshold_precision = \
        _threshold(scores)
    selected = tuple(_antichain(group, threshold)
                     for group in scored_groups)
    selected_counts = tuple(map(len, selected))
    correct_counts = tuple(sum(row.successful for row in group)
                           for group in selected)
    selected_total = sum(selected_counts)
    correct_total = sum(correct_counts)
    exact_groups = sum(bool(selected_counts[index]) and
                       selected_counts[index] == correct_counts[index]
                       for index in range(len(selected)))
    precision = correct_total / selected_total if selected_total else 0.
    logloss = -sum(
        math.log(max(1e-15, score if row.successful else 1. - score))
        for score, row in scores) / len(scores)
    passed = bool(
        selected_total >= REQUIRED_SELECTED_ACTIONS and
        precision >= MINIMUM_ACTION_PRECISION and
        exact_groups >= REQUIRED_EXACT_GROUPS)
    return CandidateIncidencePreflight(
        COMPLETED_TRAINING_CENTERS, graph_digest,
        tuple(map(len, groups)),
        tuple(sum(row.successful for row in group) for group in groups),
        sum(map(len, groups)),
        sum(row.successful for group in groups for row in group),
        MINIMUM_TOKEN_SUPPORT, MINIMUM_TOKEN_GROUPS, TOKEN_SHRINKAGE,
        tuple(fold_digests), logloss,
        sum(seen_fractions) / len(seen_fractions),
        sum(weighted_fractions) / len(weighted_fractions), threshold,
        threshold_selected, threshold_correct, threshold_precision,
        selected_counts, correct_counts, selected_total, correct_total,
        selected_total - correct_total, precision, exact_groups, False,
        passed,
        ("candidate-level incidence marking passes the nine-nucleus gate"
         if passed else
         "candidate-level incidence marking is precise but does not yet "
         "cover every nucleus"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
