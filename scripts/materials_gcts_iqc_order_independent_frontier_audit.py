#!/usr/bin/env python3
"""Audit an order-independent post-commit IQC frontier marking.

This is deliberately a conditional continuation audit, not an autonomous
growth claim: a known-exact two-action prefix is used to create each heldout
configuration, and heldout truth is opened only to score the frozen frontier.
The marking itself is fitted solely on causal self-fed traces from the ten
training nuclei.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass

from materials_gcts_cluster_prototype_compatibility import (
    fit_prototype_compatibility_context, score_prototype_insertions)
from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_incidence_token_marking import (
    FrozenIncidenceTokenMarking, IncidenceTokenExample, TokenEvidence,
    candidate_incidence_descriptors,
    fit_incidence_token_marking, incidence_marking_digest,
    score_incidence_descriptor)
from materials_gcts_iqc_expanded_development_baseline import _expanded_fixture
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_recurrent_path_selector_audit import (
    TRAINING_GROUPS, _all_paths, _program)
from materials_gcts_iqc_recurrent_prototype_connection_audit import _bounded
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_recursive_connections import local_cluster_types
from materials_gcts_successor_state_marking import successor_outgoing_points


TRAINING_WAVES = 3
MAXIMUM_EXACT_TRAINING_ACTIONS = 64
MARKING_GRID = ((4, 2, .5), (8, 3, .5), (16, 3, 1.), (24, 5, 1.))


@dataclass(frozen=True)
class PostCommitMarkingSelection:
    minimum_support: int
    minimum_groups: int
    shrinkage: float
    eligible_training_stages: int
    selected_exact_stages: int
    first_exact_rank_sum: int


@dataclass(frozen=True)
class IQCOrderIndependentFrontierAudit:
    training_groups: int
    validation_groups: int
    training_waves: int
    training_candidates: int
    training_exact_actions: int
    training_wave_candidates: tuple[tuple[int, ...], ...]
    training_wave_exact_actions: tuple[tuple[int, ...], ...]
    marking_grid: tuple[tuple[int, int, float], ...]
    marking_audits: tuple[PostCommitMarkingSelection, ...]
    selected_marking: tuple[int, int, float]
    frozen_marking_tokens: int
    frozen_marking_digest: str
    validation_frontier_candidates: tuple[int, ...]
    validation_global_exact_actions: tuple[int, ...]
    validation_last_inserted_exact_actions: tuple[int, ...]
    compatibility_first_exact_ranks: tuple[int, ...]
    marked_first_exact_ranks: tuple[int, ...]
    marked_top1_exact_by_group: tuple[bool, ...]
    marked_top1_exact_groups: int
    required_configuration_beam_width: int
    all_global_frontiers_have_exact_action: bool
    width_four_conditional_supply_gate_passed: bool
    top1_selection_gate_passed: bool
    order_independent_frontier_materially_required: bool
    training_truth_used_only_for_causal_trace_labels: bool
    validation_truth_used_to_construct_conditional_prefix: bool
    heldout_truth_used_to_fit_marking: bool
    autonomous_growth_claimed: bool
    candidate_digest: str
    honest_status: str


def _descriptors(positions, species, proposals):
    return candidate_incidence_descriptors(
        proposals, distance_scale=HIDDEN_UNIT, neighborhood_reach=3.,
        distance_bin_width=.25, maximum_neighbors=8,
        occupied_positions=positions, occupied_species=species)


def _is_exact(source, proposals, point):
    return (source.truth.get(_key(point)) ==
            _dominant_source_color(proposals, point))


def _advance(source, connection, positions, species, proposals, points):
    points = tuple(points)
    colors = tuple(_dominant_source_color(proposals, point)
                   for point in points)
    return advance_frontier_configuration(
        connection, proposals, positions, species, points, colors,
        CLUSTER_EDGES, source.group, EVALUATION_TARGET_RADIUS)


def _training_corpus(sources, connection):
    groups = []
    candidate_counts = []
    exact_counts = []
    for source in sources[:TRAINING_GROUPS]:
        positions = tuple(source.seed_positions)
        species = tuple(source.seed_species)
        proposals = _bounded(connection, source, local_cluster_types(
            positions, species, CLUSTER_EDGES))
        stages = []
        group_candidates = []
        group_exact = []
        for _wave in range(TRAINING_WAVES):
            descriptors = _descriptors(positions, species, proposals)
            rows = tuple((descriptors[point],
                          _is_exact(source, proposals, point))
                         for point in proposals.votes)
            stages.append(rows)
            exact = tuple(sorted(
                (point for point in proposals.votes
                 if _is_exact(source, proposals, point)),
                key=lambda point: (-proposals.votes[point], point))[
                    :MAXIMUM_EXACT_TRAINING_ACTIONS])
            group_candidates.append(len(rows))
            group_exact.append(len(exact))
            if not exact:
                break
            positions, species, proposals = _advance(
                source, connection, positions, species, proposals, exact)
        groups.append(tuple(stages))
        candidate_counts.append(tuple(group_candidates))
        exact_counts.append(tuple(group_exact))
    return tuple(groups), tuple(candidate_counts), tuple(exact_counts)


def _fit(groups, excluded, setting):
    support, independent_groups, shrinkage = setting
    examples = tuple(IncidenceTokenExample(group, descriptor, label)
        for group, stages in enumerate(groups) if group not in excluded
        for stage in stages for descriptor, label in stage)
    return fit_incidence_token_marking(
        examples, minimum_support=support,
        minimum_groups=independent_groups, shrinkage=shrinkage)


def _group_token_statistics(groups):
    statistics = []
    for stages in groups:
        examples = 0
        positive = 0
        counts = defaultdict(lambda: [0, 0])
        for stage in stages:
            for descriptor, label in stage:
                examples += 1
                positive += int(label)
                for token in set(descriptor.tokens):
                    counts[token][0] += int(label)
                    counts[token][1] += 1
        statistics.append((examples, positive, dict(counts)))
    return tuple(statistics)


def _fit_from_statistics(statistics, heldout, setting):
    """Exact count-equivalent LOPO fit without rescanning every descriptor."""
    support, minimum_groups, shrinkage = setting
    examples = sum(row[0] for index, row in enumerate(statistics)
                   if index != heldout)
    positive = sum(row[1] for index, row in enumerate(statistics)
                   if index != heldout)
    prior = (positive + 1.) / (examples + 2.)
    intercept = math.log(prior / (1. - prior))
    pooled = defaultdict(lambda: [0, 0, 0])
    for index, (_examples, _positive, counts) in enumerate(statistics):
        if index == heldout:
            continue
        for token, (pos, total) in counts.items():
            pooled[token][0] += pos
            pooled[token][1] += total
            pooled[token][2] += 1
    evidence = {token: TokenEvidence(pos, total, groups)
                for token, (pos, total, groups) in pooled.items()}
    weights = {}
    for token, row in evidence.items():
        if row.total < support or row.independent_groups < minimum_groups:
            continue
        probability = (row.positive + 1.) / (row.total + 2.)
        logit = math.log(probability / (1. - probability))
        weights[token] = max(-4., min(4., shrinkage * (
            logit - intercept)))
    return FrozenIncidenceTokenMarking(
        intercept, weights, evidence, support, minimum_groups, shrinkage)


def _select_marking(groups):
    statistics = _group_token_statistics(groups)
    audits = []
    for setting in MARKING_GRID:
        selected = 0
        rank_sum = 0
        eligible = 0
        for heldout, stages in enumerate(groups):
            marking = _fit_from_statistics(statistics, heldout, setting)
            for stage in stages:
                if not any(label for _descriptor, label in stage):
                    continue
                eligible += 1
                ordered = sorted(stage, key=lambda row: (
                    -score_incidence_descriptor(marking, row[0]),
                    repr(row[0].tokens)))
                selected += bool(ordered[0][1])
                rank_sum += next(rank for rank, row in enumerate(ordered, 1)
                                 if row[1])
        audits.append(PostCommitMarkingSelection(
            *setting, eligible, selected, rank_sum))
    chosen = max(audits, key=lambda row: (
        row.selected_exact_stages, -row.first_exact_rank_sum,
        row.minimum_groups, row.minimum_support, -row.shrinkage))
    setting = (chosen.minimum_support, chosen.minimum_groups,
               chosen.shrinkage)
    return tuple(audits), setting, _fit(groups, frozenset(), setting)


def evaluate() -> IQCOrderIndependentFrontierAudit:
    sources, _counts, _origin = _expanded_fixture()
    prototypes, connection = _program(sources)
    paths = _all_paths(sources, prototypes, connection)
    labels = tuple(tuple(
        source.truth.get(_key(row[2])) == row[3] and
        source.truth.get(_key(row[4])) == row[5]
        for row in rows) for source, rows in zip(sources, paths))
    corpus, wave_candidates, wave_exact = _training_corpus(
        sources, connection)
    audits, setting, marking = _select_marking(corpus)

    frontier_counts = []
    global_exact_counts = []
    dependent_exact_counts = []
    compatibility_ranks = []
    marked_ranks = []
    top1 = []
    digest_rows = []
    for source, group_paths, group_labels in zip(
            sources[TRAINING_GROUPS:], paths[TRAINING_GROUPS:],
            labels[TRAINING_GROUPS:]):
        exact_index = group_labels.index(True)
        row = group_paths[exact_index]
        positions = tuple(source.seed_positions)
        species = tuple(source.seed_species)
        proposals = _bounded(connection, source, local_cluster_types(
            positions, species, CLUSTER_EDGES))
        positions, species, proposals = _advance(
            source, connection, positions, species, proposals, (row[2],))
        positions, species, proposals = _advance(
            source, connection, positions, species, proposals, (row[4],))

        last = len(positions) - 1
        dependent = successor_outgoing_points(
            proposals, new_parent_index=last,
            occupied_positions=positions,
            minimum_distance=source.minimum_distance)
        dependent_exact_counts.append(sum(
            _is_exact(source, proposals, point) for point in dependent))

        descriptors = _descriptors(positions, species, proposals)
        context = fit_prototype_compatibility_context(
            positions, species, CLUSTER_EDGES, prototypes)
        compatibility = {}
        for point in proposals.votes:
            color = _dominant_source_color(proposals, point)
            compatibility[point] = score_prototype_insertions(
                context, (point,), (color,))
        compatibility_order = tuple(sorted(proposals.votes, key=lambda point: (
            compatibility[point].total_residual_delta,
            compatibility[point].inserted_residuals[0],
            -proposals.votes[point], point)))
        marked_order = tuple(sorted(proposals.votes, key=lambda point: (
            -score_incidence_descriptor(marking, descriptors[point]),
            -proposals.votes[point], point)))
        exact_count = sum(_is_exact(source, proposals, point)
                          for point in proposals.votes)
        frontier_counts.append(len(proposals.votes))
        global_exact_counts.append(exact_count)
        compatibility_ranks.append(next(
            rank for rank, point in enumerate(compatibility_order, 1)
            if _is_exact(source, proposals, point)))
        marked_ranks.append(next(
            rank for rank, point in enumerate(marked_order, 1)
            if _is_exact(source, proposals, point)))
        top1.append(_is_exact(source, proposals, marked_order[0]))
        digest_rows.append(tuple((point, descriptors[point])
                                 for point in sorted(proposals.votes)))

    all_supply = all(count > 0 for count in global_exact_counts)
    beam_width = max(marked_ranks)
    conditional = all_supply and beam_width <= 4
    selection = conditional and all(top1)
    order_required = any(global_count > 0 and dependent_count == 0
                         for global_count, dependent_count in zip(
                             global_exact_counts, dependent_exact_counts))
    return IQCOrderIndependentFrontierAudit(
        TRAINING_GROUPS, len(sources) - TRAINING_GROUPS, TRAINING_WAVES,
        sum(sum(row) for row in wave_candidates),
        sum(label for stages in corpus for stage in stages
            for _descriptor, label in stage), wave_candidates, wave_exact,
        MARKING_GRID, audits, setting, len(marking.token_weights),
        incidence_marking_digest(marking), tuple(frontier_counts),
        tuple(global_exact_counts), tuple(dependent_exact_counts),
        tuple(compatibility_ranks), tuple(marked_ranks), tuple(top1),
        sum(top1), beam_width, all_supply, conditional, selection,
        order_required, True, True, False, False,
        hashlib.sha256(repr(tuple(digest_rows)).encode()).hexdigest(),
        ("width-four order-independent supply is complete, but the marking "
         "does not yet select every continuation" if conditional else
         "order-independent conditional continuation supply is incomplete"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
