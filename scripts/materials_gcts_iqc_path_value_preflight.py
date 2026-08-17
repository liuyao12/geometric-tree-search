#!/usr/bin/env python3
"""Target-free third-frontier value section for exact IQC port paths.

The input graph and its labels come from the nine completed nuclei.  A fixed
raw child-score shortlist is constructed without labels and contains exact
two-step paths in every nucleus.  Each path is executed one more step without
committing it; the resulting local outgoing-port section is fit and evaluated
by leaving out whole nuclei.  The reserved confirmation nucleus is not
imported or constructed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample,
    fit_incidence_token_marking, score_incidence_descriptor)
from materials_gcts_iqc_candidate_port_search_preflight import (
    _build_pairs)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_port_incidence_search import (
    port_incidence_patterns, port_incidence_state)


SHORTLIST_PER_NUCLEUS = 512
MINIMUM_TOKEN_SUPPORT = 4
MINIMUM_TOKEN_GROUPS = 2
TOKEN_SHRINKAGE = .5


@dataclass(frozen=True)
class _PathRow:
    group: tuple[float, float, float]
    pair: object
    descriptor: CandidateIncidenceDescriptor


@dataclass(frozen=True)
class IQCPathValuePreflight:
    training_centers: tuple[tuple[float, float, float], ...]
    shortlist_per_nucleus: int
    shortlist_candidates_by_group: tuple[int, ...]
    shortlist_positive_by_group: tuple[int, ...]
    terminal_outgoing_minimum_by_group: tuple[int, ...]
    terminal_outgoing_maximum_by_group: tuple[int, ...]
    terminal_descriptor_digest: str
    fold_model_digests: tuple[str, ...]
    selected_path_ids: tuple[str, ...]
    selected_correct_by_group: tuple[bool, ...]
    selected_correct_paths: int
    selected_false_paths: int
    selected_precision: float
    reserved_confirmation_center_imported_or_accessed: bool
    preflight_passed: bool
    honest_status: str


def _bucket(value):
    return 0 if value <= 0 else min(16, int(math.log2(value)) + 1)


def _compatible(positions, point, minimum):
    return not any(math.dist(point, occupied) < minimum - 1e-8
                   for occupied in positions)


def _terminal_descriptor(context, pair, root_cache):
    root_point = pair.root.payload["point"]
    root_color = pair.root.payload["color"]
    cached = root_cache.get(root_point)
    if cached is None:
        cached = advance_frontier_configuration(
            context.connection, context.proposals,
            context.seed_positions, context.seed_species,
            (root_point,), (root_color,), CLUSTER_EDGES,
            context.center, EVALUATION_TARGET_RADIUS)
        root_cache[root_point] = cached
    positions, colors, future = cached
    child_point = pair.child.payload["point"]
    child_color = pair.child.payload["color"]
    terminal_positions, terminal_colors, terminal = \
        advance_frontier_configuration(
            context.connection, future, positions, colors,
            (child_point,), (child_color,), CLUSTER_EDGES,
            context.center, EVALUATION_TARGET_RADIUS)
    new_parent = len(terminal_positions) - 1
    outgoing = tuple(sorted(
        point for point in terminal.votes
        if new_parent in terminal.parent_votes.get(point, {}) and
        _compatible(terminal_positions, point, context.minimum_distance)))
    votes = tuple(terminal.votes[point] for point in outgoing)
    parent_mass = tuple(sum(
        terminal.parent_votes.get(point, {}).values()) for point in outgoing)
    state = port_incidence_state(
        terminal, outgoing, maximum_roles=8, minimum_multiplicity=1)
    patterns = port_incidence_patterns(
        terminal, outgoing, maximum_order=2,
        maximum_patterns=32, roles_per_site=4) if outgoing else ()
    distance_bins = Counter(round(
        math.dist(child_point, point) / (HIDDEN_UNIT * .5))
        for point in outgoing)
    tokens = {
        ("terminal-frontier-count", _bucket(len(terminal.votes))),
        ("outgoing-count", _bucket(len(outgoing))),
        ("outgoing-vote-mass", _bucket(sum(votes))),
        ("outgoing-max-vote", _bucket(max(votes, default=0))),
        ("outgoing-parent-mass", _bucket(sum(parent_mass))),
        ("outgoing-max-parent-mass", _bucket(max(parent_mass, default=0))),
        ("outgoing-source-colors", tuple(sorted({
            color for point in outgoing
            for color in terminal.color_votes.get(point, {})}))),
        ("outgoing-predicted-colors", tuple(sorted({
            color for point in outgoing
            for color in terminal.target_color_votes.get(point, {})}))),
    }
    tokens.update(("distance-bin", distance, _bucket(count))
                  for distance, count in distance_bins.items())
    tokens.update(("outgoing-role", role) for role, _count in state.roles)
    tokens.update(("outgoing-coarse-role", role.parent_color,
                   role.source_color, role.separation_bin)
                  for role, _count in state.roles)
    tokens.update(("outgoing-pattern", pattern) for pattern in patterns)
    # Retain only the coarse chemistry of the incoming transition; the full
    # path identity and coordinates remain search data, never marking fields.
    tokens.add(("path-colors", str(root_color), str(child_color)))
    return CandidateIncidenceDescriptor(tuple(sorted(tokens, key=repr))), \
        len(outgoing)


def _build_rows():
    groups, _root_counts, _root_positive, contexts = _build_pairs()
    result = []
    outgoing_counts = []
    for group, context in zip(groups, contexts):
        shortlist = tuple(sorted(
            group, key=lambda pair: (
                -pair.raw_child_score, repr(pair.root.action_id)))
            [:SHORTLIST_PER_NUCLEUS])
        cache = {}
        rows = []
        counts = []
        for pair in shortlist:
            descriptor, outgoing = _terminal_descriptor(
                context, pair, cache)
            rows.append(_PathRow(pair.group, pair, descriptor))
            counts.append(outgoing)
        result.append(tuple(rows))
        outgoing_counts.append(tuple(counts))
    return tuple(result), tuple(outgoing_counts)


def evaluate():
    groups, outgoing = _build_rows()
    digest = hashlib.sha256(repr(tuple(
        (row.group, row.pair.root.action_id, row.descriptor)
        for group in groups for row in group)).encode()).hexdigest()
    selected = []
    model_digests = []
    for heldout_index, heldout in enumerate(groups):
        examples = tuple(IncidenceTokenExample(
            row.group, row.descriptor, row.pair.successful)
            for index, group in enumerate(groups) if index != heldout_index
            for row in group)
        marking = fit_incidence_token_marking(
            examples, minimum_support=MINIMUM_TOKEN_SUPPORT,
            minimum_groups=MINIMUM_TOKEN_GROUPS,
            shrinkage=TOKEN_SHRINKAGE)
        model_digests.append(hashlib.sha256(
            repr(marking).encode()).hexdigest())
        ranked = sorted(heldout, key=lambda row: (
            -score_incidence_descriptor(marking, row.descriptor),
            repr(row.pair.root.action_id)))
        selected.append(ranked[0])
    correct = tuple(bool(row.pair.successful) for row in selected)
    correct_count = sum(correct)
    passed = correct_count == len(groups)
    return IQCPathValuePreflight(
        tuple(group[0].group for group in groups), SHORTLIST_PER_NUCLEUS,
        tuple(map(len, groups)),
        tuple(sum(row.pair.successful for row in group) for group in groups),
        tuple(min(counts) for counts in outgoing),
        tuple(max(counts) for counts in outgoing), digest,
        tuple(model_digests),
        tuple(str(row.pair.root.action_id) for row in selected), correct,
        correct_count, len(groups) - correct_count,
        correct_count / len(groups), False, passed,
        ("third-frontier path value passes every known IQC nucleus"
         if passed else
         "third-frontier path value remains below the all-nucleus gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
