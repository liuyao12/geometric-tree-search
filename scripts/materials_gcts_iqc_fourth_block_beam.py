#!/usr/bin/env python3
"""Freeze a parent-balanced fourth-block IQC beam without held-out targets."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from materials_gcts_iqc_bounded_lineage_graph_value import SPEC
from materials_gcts_iqc_bounded_lineage_value import (
    _candidate_rows, _correct, _truth_index)
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_partial_port_graph_lineage_value import (
    PartialPortGraphLineageExample, fit_partial_port_graph_lineage_value,
    score_partial_port_graph_lineage_value)


PARENT_WIDTH = 8


@dataclass(frozen=True)
class FrozenFourthBlockBeamCandidate:
    stable_index: int
    parent_id: int
    score: float
    actions: tuple[tuple, ...]
    graph_digests: tuple[str, ...]


@dataclass(frozen=True)
class FrozenFourthBlockBeam:
    heldout_group: int
    nucleus: str
    center: tuple[float, float, float]
    seed_radius: float
    replay_radii: tuple[float, ...]
    next_radius: float
    parent_width: int
    parents: int
    complete_candidates: int
    retained_candidates: int
    candidate_digest: str
    retained_digest: str
    training_groups: tuple[int, ...]
    training_examples: int
    training_positive_examples: int
    model_digest: str
    candidates: tuple[FrozenFourthBlockBeamCandidate, ...]
    heldout_target_opened: bool = False
    target_used_for_ranking: bool = False


def parent_balanced_beam(scores, parents, tie_keys, width=PARENT_WIDTH):
    scores = tuple(map(float, scores))
    parents = tuple(map(int, parents))
    tie_keys = tuple(tie_keys)
    if (not scores or len(scores) != len(parents) or
            len(scores) != len(tie_keys) or width < 1):
        raise ValueError("invalid parent-balanced beam inputs")
    retained = []
    for parent in sorted(set(parents)):
        order = sorted((index for index, value in enumerate(parents)
                        if value == parent), key=lambda index: (
                            -scores[index], repr(tie_keys[index])))
        retained.extend(order[:min(width, len(order))])
    return tuple(sorted(retained, key=lambda index: (
        parents[index], -scores[index], repr(tie_keys[index]))))


def freeze_fourth_block_beam(
        heldout_group: int, *, parent_width: int = PARENT_WIDTH,
        candidate_loader=_candidate_rows, target_loader=oracle_crop_fast,
        ) -> FrozenFourthBlockBeam:
    groups, _completion = candidate_loader()
    groups = tuple(sorted(groups, key=lambda row: row["group"]))
    if heldout_group not in {row["group"] for row in groups}:
        raise ValueError("unknown held-out nucleus")
    training_examples = []
    training_groups = []
    for row in groups:
        if row["group"] == heldout_group:
            continue
        # Only non-held targets are permitted to produce development labels.
        target, _ = target_loader(row["center"], row["radii"][2])
        truth = _truth_index(target.positions, target.species)
        training_groups.append(row["group"])
        for parent, _features, _colors, actions, graphs, _temporal in row["rows"]:
            successful = all(_correct(point, color, truth)
                             for point, color in actions)
            training_examples.append(PartialPortGraphLineageExample(
                row["group"], parent, graphs, successful))
    model = fit_partial_port_graph_lineage_value(
        tuple(training_examples), SPEC, embedding_cache={})
    held = next(row for row in groups if row["group"] == heldout_group)
    rows = held["rows"]
    scores = tuple(score_partial_port_graph_lineage_value(
        model, row[4]) for row in rows)
    parents = tuple(row[0] for row in rows)
    tie_keys = tuple(row[3] for row in rows)
    retained = parent_balanced_beam(
        scores, parents, tie_keys, parent_width)
    parent_set = tuple(sorted(set(parents)))
    if len(parent_set) != 8 or any(
            sum(parents[index] == parent for index in retained) != parent_width
            for parent in parent_set):
        raise AssertionError("parent-balanced beam lost a complete parent")
    candidates = tuple(FrozenFourthBlockBeamCandidate(
        stable_index, int(rows[stable_index][0]), float(scores[stable_index]),
        tuple(rows[stable_index][3]),
        tuple(graph.canonical_digest for graph in rows[stable_index][4]))
        for stable_index in retained)
    candidate_digest = hashlib.sha256(repr(tuple(
        row[3] for row in rows)).encode()).hexdigest()
    retained_digest = hashlib.sha256(repr(tuple(
        (row.stable_index, row.parent_id, row.actions, row.graph_digests)
        for row in candidates)).encode()).hexdigest()
    next_radius = float(held["radii"][-1] + held["radii"][1] -
                        held["radii"][0])
    return FrozenFourthBlockBeam(
        heldout_group, held["name"], tuple(held["center"]), 9.,
        tuple(held["radii"]), next_radius, parent_width, len(parent_set),
        len(rows), len(candidates), candidate_digest, retained_digest,
        tuple(training_groups), len(training_examples),
        sum(row.successful for row in training_examples), model.model_digest,
        candidates)


__all__ = [
    "FrozenFourthBlockBeam", "FrozenFourthBlockBeamCandidate",
    "PARENT_WIDTH", "freeze_fourth_block_beam", "parent_balanced_beam"]
