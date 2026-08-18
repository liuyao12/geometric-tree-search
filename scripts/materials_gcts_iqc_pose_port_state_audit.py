#!/usr/bin/env python3
"""Select a finite pose-port quotient and audit conditional IQC transfer.

The eight evaluation configurations reuse the already-open development set.
A truth-selected two-action prefix constructs each conditional frontier, but
the quotient, thresholds, and finite state table are fitted only from the ten
training nuclei.  This is a branch-selection gate, not autonomous growth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import _dominant_source_color
from materials_gcts_incidence_token_marking import (
    IncidenceTokenExample, candidate_incidence_descriptors,
    fit_incidence_token_marking)
from materials_gcts_iqc_expanded_development_baseline import _expanded_fixture
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_order_independent_frontier_audit import (
    MAXIMUM_EXACT_TRAINING_ACTIONS, TRAINING_WAVES)
from materials_gcts_iqc_recurrent_path_selector_audit import (
    TRAINING_GROUPS, _all_paths, _program)
from materials_gcts_iqc_recurrent_prototype_connection_audit import _bounded
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_persistent_frontier_beam import advance_frontier_configuration
from materials_gcts_pose_port_state_marking import (
    DEFAULT_POSE_PORT_CHANNELS, fit_pose_port_state_marking,
    fit_pose_port_states_from_token_marking, pose_port_state_code,
    pose_port_state_marking_digest, score_pose_port_state)
from materials_gcts_recursive_connections import local_cluster_types


# Frozen upstream by the cluster-pose atlas audit.  Marking learning may
# quotient these pose states, but must not refit the geometry discretization.
UPSTREAM_ANGULAR_BIN_WIDTH = .125
STATE_WIDTHS = (.125, .25, .5, 1.)
TOKEN_SETTINGS = ((4, 2), (8, 3), (16, 3))
TOKEN_SHRINKAGE = .5
MINIMUM_STATE_SUPPORT = 8
MINIMUM_STATE_GROUPS = 2
UNQUOTIENTED_RANKS = (3, 4, 3, 3, 1, 1, 1, 1)


@dataclass(frozen=True)
class PosePortStateSelection:
    state_bin_width: float
    minimum_token_support: int
    minimum_token_groups: int
    eligible_training_stages: int
    selected_exact_stages: int
    first_exact_rank_sum: int
    selected_state_supported_stages: int


@dataclass(frozen=True)
class IQCPosePortStateAudit:
    training_groups: int
    validation_groups: int
    training_waves: int
    training_candidates: int
    training_exact_actions: int
    upstream_angular_bin_width: float
    pose_atlas_refit_during_marking: bool
    state_widths: tuple[float, ...]
    token_settings: tuple[tuple[int, int], ...]
    channel_families: tuple[tuple[str, ...], ...]
    selection_audits: tuple[PosePortStateSelection, ...]
    selected_angular_bin_width: float
    selected_state_bin_width: float
    selected_token_setting: tuple[int, int]
    selected_training_exact_stages: int
    eligible_training_stages: int
    frozen_recurrent_states: int
    frozen_state_marking_digest: str
    validation_frontier_candidates: tuple[int, ...]
    validation_exact_actions: tuple[int, ...]
    validation_supported_top_states: tuple[bool, ...]
    state_first_exact_ranks: tuple[int, ...]
    state_top1_exact_by_group: tuple[bool, ...]
    state_top1_exact_groups: int
    state_required_beam_width: int
    unquotiented_first_exact_ranks: tuple[int, ...]
    unquotiented_top1_exact_groups: int
    finite_pose_port_quotient_improves_selection: bool
    conditional_top1_gate_passed: bool
    exact_candidate_geometry_changed: bool
    proper_rotation_quotiented: bool
    raw_rotation_count_used_as_channel_count: bool
    heldout_truth_used_to_select_quotient: bool
    validation_truth_used_to_construct_conditional_prefix: bool
    autonomous_growth_claimed: bool
    candidate_digest: str
    honest_status: str


def _descriptors(positions, species, proposals, angular_width):
    return candidate_incidence_descriptors(
        proposals, distance_scale=HIDDEN_UNIT, neighborhood_reach=3.,
        distance_bin_width=.25, maximum_neighbors=8,
        joint_role_geometry=True, oriented_port_geometry=True,
        angular_bin_width=angular_width,
        occupied_positions=positions, occupied_species=species)


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
    corpora = []
    for source in sources[:TRAINING_GROUPS]:
        positions = tuple(source.seed_positions)
        species = tuple(source.seed_species)
        proposals = _bounded(connection, source, local_cluster_types(
            positions, species, CLUSTER_EDGES))
        stages = []
        for _wave in range(TRAINING_WAVES):
            labels = {point: _exact(source, proposals, point)
                      for point in proposals.votes}
            descriptors = _descriptors(
                positions, species, proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            points = tuple(sorted(proposals.votes))
            stages.append(tuple(
                (descriptors[point], labels[point]) for point in points))
            exact = tuple(sorted(
                (point for point in proposals.votes if labels[point]),
                key=lambda point: (-proposals.votes[point], point))[
                    :MAXIMUM_EXACT_TRAINING_ACTIONS])
            if not exact:
                break
            positions, species, proposals = _advance(
                source, connection, positions, species, proposals, exact)
        corpora.append(tuple(stages))
    return tuple(corpora)


def _examples(corpora, excluded=()):
    excluded = frozenset(excluded)
    return tuple(IncidenceTokenExample(group, descriptor, label)
        for group, stages in enumerate(corpora) if group not in excluded
        for stage in stages for descriptor, label in stage)


def _selection(corpora):
    audits = []
    fold_examples = tuple(_examples(corpora, (heldout,))
                          for heldout in range(len(corpora)))
    for support, groups in TOKEN_SETTINGS:
        token_markings = tuple(fit_incidence_token_marking(
            rows, minimum_support=support, minimum_groups=groups,
            shrinkage=TOKEN_SHRINKAGE) for rows in fold_examples)
        for state_width in STATE_WIDTHS:
            models = tuple(fit_pose_port_states_from_token_marking(
                rows, token_marking, state_bin_width=state_width,
                minimum_state_support=MINIMUM_STATE_SUPPORT,
                minimum_state_groups=MINIMUM_STATE_GROUPS)
                for rows, token_marking in zip(
                    fold_examples, token_markings))
            selected = rank_sum = eligible = supported = 0
            for heldout, stages in enumerate(corpora):
                model = models[heldout]
                for stage in stages:
                    if not any(label for _descriptor, label in stage):
                        continue
                    eligible += 1
                    ordered = sorted(stage, key=lambda row: (
                        -score_pose_port_state(model, row[0]),
                        repr(row[0].tokens)))
                    selected += int(ordered[0][1])
                    rank_sum += next(
                        rank for rank, row in enumerate(ordered, 1)
                        if row[1])
                    state = pose_port_state_code(
                        model.token_marking, ordered[0][0],
                        state_bin_width=model.state_bin_width,
                        channel_families=model.channel_families)
                    supported += int(state in model.state_probabilities)
            audits.append(PosePortStateSelection(
                state_width, support, groups, eligible,
                selected, rank_sum, supported))
    chosen = max(audits, key=lambda row: (
        row.selected_exact_stages, -row.first_exact_rank_sum,
        row.selected_state_supported_stages, -row.state_bin_width,
        row.minimum_token_groups,
        -row.minimum_token_support))
    return tuple(audits), chosen


def evaluate() -> IQCPosePortStateAudit:
    sources, _counts, _origin = _expanded_fixture()
    prototypes, connection = _program(sources)
    paths = _all_paths(sources, prototypes, connection)
    path_labels = tuple(tuple(
        source.truth.get(_key(row[2])) == row[3] and
        source.truth.get(_key(row[4])) == row[5]
        for row in rows) for source, rows in zip(sources, paths))
    training = _training_corpora(sources, connection)
    audits, selected = _selection(training)
    model = fit_pose_port_state_marking(
        _examples(training),
        minimum_token_support=selected.minimum_token_support,
        minimum_token_groups=selected.minimum_token_groups,
        token_shrinkage=TOKEN_SHRINKAGE,
        state_bin_width=selected.state_bin_width,
        minimum_state_support=MINIMUM_STATE_SUPPORT,
        minimum_state_groups=MINIMUM_STATE_GROUPS)

    frontier_counts = []
    exact_counts = []
    supported = []
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
            positions, species, proposals, UPSTREAM_ANGULAR_BIN_WIDTH)
        ordered = tuple(sorted(proposals.votes, key=lambda point: (
            -score_pose_port_state(model, descriptors[point]),
            -proposals.votes[point], point)))
        rank = next(rank for rank, point in enumerate(ordered, 1)
                    if _exact(source, proposals, point))
        state = pose_port_state_code(
            model.token_marking, descriptors[ordered[0]],
            state_bin_width=model.state_bin_width,
            channel_families=model.channel_families)
        frontier_counts.append(len(proposals.votes))
        exact_counts.append(sum(_exact(source, proposals, point)
                                for point in proposals.votes))
        supported.append(state in model.state_probabilities)
        ranks.append(rank)
        top1.append(rank == 1)
        digest_rows.append(tuple((point, descriptors[point])
                                 for point in sorted(proposals.votes)))

    improved = (sum(top1) > 4 and max(ranks) <= max(UNQUOTIENTED_RANKS))
    gate = improved and all(top1)
    training_candidates = sum(
        len(stage) for stages in training for stage in stages)
    training_exact = sum(
        label for stages in training for stage in stages
        for _descriptor, label in stage)
    return IQCPosePortStateAudit(
        TRAINING_GROUPS, len(sources) - TRAINING_GROUPS, TRAINING_WAVES,
        training_candidates, training_exact, UPSTREAM_ANGULAR_BIN_WIDTH,
        False, STATE_WIDTHS, TOKEN_SETTINGS, DEFAULT_POSE_PORT_CHANNELS,
        audits, UPSTREAM_ANGULAR_BIN_WIDTH, selected.state_bin_width,
        (selected.minimum_token_support, selected.minimum_token_groups),
        selected.selected_exact_stages, selected.eligible_training_stages,
        len(model.state_probabilities), pose_port_state_marking_digest(model),
        tuple(frontier_counts), tuple(exact_counts), tuple(supported),
        tuple(ranks), tuple(top1), sum(top1), max(ranks),
        UNQUOTIENTED_RANKS, 4, improved, gate, False, True, False, False,
        True, False, hashlib.sha256(repr(tuple(digest_rows)).encode()).hexdigest(),
        ("finite recurrent pose-port quotient selects every conditional "
         "heldout continuation" if gate else
         "finite pose-port quotient does not yet pass conditional top-one"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
