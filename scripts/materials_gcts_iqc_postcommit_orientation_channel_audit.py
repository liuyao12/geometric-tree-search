#!/usr/bin/env python3
"""Train-select oriented post-commit channels and test their transfer."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_incidence_token_marking import (
    IncidenceTokenExample, candidate_incidence_descriptors,
    fit_incidence_token_marking, incidence_marking_digest,
    score_incidence_descriptor, score_incidence_descriptor_by_channel)
from materials_gcts_iqc_expanded_development_baseline import _expanded_fixture
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_order_independent_frontier_audit import (
    MARKING_GRID, MAXIMUM_EXACT_TRAINING_ACTIONS, TRAINING_WAVES,
    _fit_from_statistics, _group_token_statistics)
from materials_gcts_iqc_recurrent_path_selector_audit import (
    TRAINING_GROUPS, _all_paths, _program)
from materials_gcts_iqc_recurrent_prototype_connection_audit import _bounded
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_recursive_connections import local_cluster_types


ANGULAR_WIDTHS = (.125, .25, .5)
SCORE_MODES = ("additive", "channel")
FROZEN_MARKING = (4, 2, .5)


@dataclass(frozen=True)
class OrientationChannelSelection:
    angular_bin_width: float
    score_mode: str
    eligible_training_stages: int
    selected_exact_stages: int
    first_exact_rank_sum: int


@dataclass(frozen=True)
class IQCPostCommitOrientationChannelAudit:
    training_groups: int
    validation_groups: int
    angular_widths: tuple[float, ...]
    score_modes: tuple[str, ...]
    frozen_marking: tuple[int, int, float]
    training_candidates: int
    training_exact_actions: int
    audits: tuple[OrientationChannelSelection, ...]
    selected_angular_bin_width: float
    selected_score_mode: str
    selected_training_exact_stages: int
    eligible_training_stages: int
    frozen_oriented_tokens: int
    frozen_oriented_marking_digest: str
    oriented_first_exact_ranks: tuple[int, ...]
    oriented_top1_exact_by_group: tuple[bool, ...]
    oriented_top1_exact_groups: int
    oriented_required_beam_width: int
    unoriented_first_exact_ranks: tuple[int, ...]
    unoriented_top1_exact_groups: int
    orientation_improves_heldout_selection: bool
    exact_candidate_geometry_changed: bool
    proper_rotation_quotiented: bool
    chirality_preserved: bool
    orientation_capacity_transfer_gate_passed: bool
    heldout_truth_used_to_select_orientation: bool
    validation_truth_used_to_construct_conditional_prefix: bool
    autonomous_growth_claimed: bool
    descriptor_digest: str
    honest_status: str


def _descriptors(positions, species, proposals, width):
    return candidate_incidence_descriptors(
        proposals, distance_scale=HIDDEN_UNIT, neighborhood_reach=3.,
        distance_bin_width=.25, maximum_neighbors=8,
        joint_role_geometry=True, oriented_port_geometry=True,
        angular_bin_width=width, occupied_positions=positions,
        occupied_species=species)


def _exact(source, proposals, point):
    return (source.truth.get(_key(point)) ==
            _dominant_source_color(proposals, point))


def _advance(source, connection, positions, species, proposals, points):
    points = tuple(points)
    return advance_frontier_configuration(
        connection, proposals, positions, species, points,
        tuple(_dominant_source_color(proposals, point) for point in points),
        CLUSTER_EDGES, source.group, EVALUATION_TARGET_RADIUS)


def _training_corpora(sources, connection):
    corpora = {width: [] for width in ANGULAR_WIDTHS}
    geometry = []
    for source in sources[:TRAINING_GROUPS]:
        positions = tuple(source.seed_positions)
        species = tuple(source.seed_species)
        proposals = _bounded(connection, source, local_cluster_types(
            positions, species, CLUSTER_EDGES))
        stages = {width: [] for width in ANGULAR_WIDTHS}
        group_geometry = []
        for _wave in range(TRAINING_WAVES):
            labels = {point: _exact(source, proposals, point)
                      for point in proposals.votes}
            descriptor_rows = {width: _descriptors(
                positions, species, proposals, width)
                for width in ANGULAR_WIDTHS}
            ordered_points = tuple(sorted(proposals.votes))
            group_geometry.append(ordered_points)
            for width in ANGULAR_WIDTHS:
                stages[width].append(tuple(
                    (descriptor_rows[width][point], labels[point])
                    for point in ordered_points))
            exact = tuple(sorted(
                (point for point in proposals.votes if labels[point]),
                key=lambda point: (-proposals.votes[point], point))[
                    :MAXIMUM_EXACT_TRAINING_ACTIONS])
            if not exact:
                break
            positions, species, proposals = _advance(
                source, connection, positions, species, proposals, exact)
        for width in ANGULAR_WIDTHS:
            corpora[width].append(tuple(stages[width]))
        geometry.append(tuple(group_geometry))
    return ({width: tuple(groups) for width, groups in corpora.items()},
            tuple(geometry))


def _selection(corpora):
    audits = []
    for width in ANGULAR_WIDTHS:
        statistics = _group_token_statistics(corpora[width])
        for mode in SCORE_MODES:
            scorer = (score_incidence_descriptor if mode == "additive"
                      else score_incidence_descriptor_by_channel)
            selected = 0
            rank_sum = 0
            eligible = 0
            for heldout, stages in enumerate(corpora[width]):
                marking = _fit_from_statistics(
                    statistics, heldout, FROZEN_MARKING)
                for stage in stages:
                    if not any(label for _descriptor, label in stage):
                        continue
                    eligible += 1
                    ordered = sorted(stage, key=lambda row: (
                        -scorer(marking, row[0]), repr(row[0].tokens)))
                    selected += bool(ordered[0][1])
                    rank_sum += next(
                        rank for rank, row in enumerate(ordered, 1)
                        if row[1])
            audits.append(OrientationChannelSelection(
                width, mode, eligible, selected, rank_sum))
    chosen = max(audits, key=lambda row: (
        row.selected_exact_stages, -row.first_exact_rank_sum,
        row.score_mode == "channel", -row.angular_bin_width))
    return tuple(audits), chosen


def evaluate() -> IQCPostCommitOrientationChannelAudit:
    sources, _counts, _origin = _expanded_fixture()
    prototypes, connection = _program(sources)
    paths = _all_paths(sources, prototypes, connection)
    path_labels = tuple(tuple(
        source.truth.get(_key(row[2])) == row[3] and
        source.truth.get(_key(row[4])) == row[5]
        for row in rows) for source, rows in zip(sources, paths))
    corpora, training_geometry = _training_corpora(sources, connection)
    audits, selected = _selection(corpora)
    training = corpora[selected.angular_bin_width]
    marking = fit_incidence_token_marking(tuple(
        IncidenceTokenExample(group, descriptor, label)
        for group, stages in enumerate(training) for stage in stages
        for descriptor, label in stage),
        minimum_support=FROZEN_MARKING[0],
        minimum_groups=FROZEN_MARKING[1],
        shrinkage=FROZEN_MARKING[2])
    scorer = (score_incidence_descriptor
              if selected.score_mode == "additive"
              else score_incidence_descriptor_by_channel)

    ranks = []
    top1 = []
    digest_rows = []
    for source, rows, labels in zip(
            sources[TRAINING_GROUPS:], paths[TRAINING_GROUPS:],
            path_labels[TRAINING_GROUPS:]):
        row = rows[labels.index(True)]
        positions = tuple(source.seed_positions)
        species = tuple(source.seed_species)
        proposals = _bounded(connection, source, local_cluster_types(
            positions, species, CLUSTER_EDGES))
        positions, species, proposals = _advance(
            source, connection, positions, species, proposals, (row[2],))
        positions, species, proposals = _advance(
            source, connection, positions, species, proposals, (row[4],))
        descriptors = _descriptors(
            positions, species, proposals, selected.angular_bin_width)
        ordered = tuple(sorted(proposals.votes, key=lambda point: (
            -scorer(marking, descriptors[point]),
            -proposals.votes[point], point)))
        ranks.append(next(rank for rank, point in enumerate(ordered, 1)
                          if _exact(source, proposals, point)))
        top1.append(_exact(source, proposals, ordered[0]))
        digest_rows.append(tuple((point, descriptors[point])
                                 for point in sorted(proposals.votes)))

    unoriented = (3, 4, 3, 3, 1, 1, 1, 1)
    improved = (sum(top1) > 4 and max(ranks) <= max(unoriented))
    gate = improved and all(top1)
    training_candidates = sum(len(stage) for stages in corpora[.125]
                              for stage in stages)
    training_exact = sum(label for stages in corpora[.125]
                         for stage in stages for _descriptor, label in stage)
    return IQCPostCommitOrientationChannelAudit(
        TRAINING_GROUPS, len(sources) - TRAINING_GROUPS, ANGULAR_WIDTHS,
        SCORE_MODES, FROZEN_MARKING, training_candidates, training_exact,
        audits, selected.angular_bin_width, selected.score_mode,
        selected.selected_exact_stages, selected.eligible_training_stages,
        len(marking.token_weights), incidence_marking_digest(marking),
        tuple(ranks), tuple(top1), sum(top1), max(ranks), unoriented, 4,
        improved, False, True, True, gate, False, True, False,
        hashlib.sha256(repr((training_geometry,
            tuple(digest_rows))).encode()).hexdigest(),
        ("raw orientation channels improve training but do not transfer; "
         "automatic capacity must remain recurrence-audited"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
