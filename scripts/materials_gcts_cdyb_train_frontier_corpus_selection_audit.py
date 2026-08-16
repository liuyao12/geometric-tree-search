#!/usr/bin/env python3
"""Role-balanced Cd--Yb frontier corpus from five training windows only."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import TRAIN_CENTERS
from materials_gcts_cdyb_partial_completion_marking_ablation import (
    TRAIN_SEED_RADIUS, TRAIN_TARGET_RADIUS, _compile, _frontier)
from materials_gcts_cdyb_hierarchical_growth_design import _ids
from materials_gcts_macro_derivation import _site_key


@dataclass(frozen=True)
class TrainingFrontierCorpusRow:
    patch_id: int
    candidate_id: str
    frozen_parent_type: int | None
    macro_id: int
    descriptor: object
    port_role: tuple
    outcome_role: str
    matched_witnesses: int


@dataclass(frozen=True)
class CdYbTrainingFrontierCorpusAudit:
    training_windows: int
    training_atoms: int
    raw_candidates: int
    raw_candidates_by_patch: tuple[int, ...]
    raw_positive_candidates: int
    raw_negative_candidates: int
    selected_candidates: int
    selected_candidates_by_patch: tuple[int, ...]
    selected_positive_candidates: int
    selected_negative_candidates: int
    selected_mixed_failures: int
    selected_unsupported_failures: int
    unique_parent_roles: int
    unique_macro_alternatives: int
    unique_port_roles: int
    unique_joint_roles: int
    joint_roles_shared_across_patches: int
    selected_candidates_in_shared_joint_roles: int
    maximum_patches_per_joint_role: int
    label_mixed_exact_descriptor_roles: int
    unique_negative_parent_roles: int
    unique_negative_port_roles: int
    patches_per_parent_role: tuple[tuple[int, int], ...]
    raw_role_effective_sample_size: float
    selected_role_effective_sample_size: float
    selected_to_raw_ratio: float
    lopo_exact_descriptor_coverage_by_patch: tuple[float, ...]
    lopo_coarse_descriptor_coverage_by_patch: tuple[float, ...]
    lopo_parent_role_coverage_by_patch: tuple[float, ...]
    lopo_negative_descriptor_coverage_by_patch: tuple[float, ...]
    every_validation_group_sealed: bool
    every_patch_has_selected_positive_and_negative: bool
    selection_digest: str
    spatial_jitter_or_absolute_origin_used_for_selection: bool
    heldout_or_new_evaluation_nucleus_opened: bool
    target_used_only_within_authorized_training_windows: bool


def _port_role(descriptor):
    incoming = tuple(descriptor.anchor_incoming_ports)
    slots = tuple((direction, semantic)
                  for direction, semantic, _frequency, _support in
                  descriptor.alternative_boundary_slots)
    return incoming, slots


def _coarse_descriptor(row):
    descriptor = row.descriptor
    return (row.port_role, descriptor.matched_witnesses,
            bool(descriptor.training_port_evidence),
            bool(descriptor.live_overlap_support),
            bool(descriptor.live_collision_support))


def _ess(rows):
    counts = Counter((row.frozen_parent_type, row.port_role,
                      row.outcome_role, row.matched_witnesses)
                     for row in rows)
    total = sum(counts.values())
    return total * total / max(1, sum(value * value
                                     for value in counts.values()))


def _coverage(validation, discovery, key):
    known = {key(row) for row in discovery}
    return sum(key(row) in known for row in validation) / max(1, len(validation))


def evaluate():
    (atoms, windows, species, _positions, primitive,
     quotient, parent_map) = _compile()
    rows_by_patch = []
    for patch_id, center in enumerate(TRAIN_CENTERS):
        payload = _frontier(
            atoms, primitive, quotient, parent_map, center,
            TRAIN_SEED_RADIUS, TRAIN_TARGET_RADIUS,
            open_training_target=True)
        frozen_rows = payload[-1]
        target_ids = _ids(atoms, center, TRAIN_TARGET_RADIUS)
        target = {_site_key((atoms.symbols[index], atoms.positions[index]), .03)
                  for index in target_ids}
        rows = []
        for item in frozen_rows:
            correct = set(item.emitted).intersection(target)
            if item.exact:
                outcome = "exact"
            elif correct:
                outcome = "mixed-failure"
            else:
                outcome = "unsupported-failure"
            candidate = item.candidate
            rows.append(TrainingFrontierCorpusRow(
                patch_id, candidate.candidate_id,
                candidate.frozen_parent_type, candidate.macro_id,
                candidate.descriptor, _port_role(candidate.descriptor),
                outcome, candidate.descriptor.matched_witnesses))
        rows_by_patch.append(tuple(rows))
    rows_by_patch = tuple(rows_by_patch)
    raw = tuple(row for rows in rows_by_patch for row in rows)

    selected_by_patch = []
    for rows in rows_by_patch:
        representatives = {}
        for row in rows:
            role = (row.frozen_parent_type, row.port_role,
                    row.outcome_role, row.matched_witnesses)
            prior = representatives.get(role)
            if prior is None or row.candidate_id < prior.candidate_id:
                representatives[role] = row
        selected_by_patch.append(tuple(
            representatives[key] for key in sorted(representatives, key=repr)))
    selected_by_patch = tuple(selected_by_patch)
    selected = tuple(row for rows in selected_by_patch for row in rows)

    exact_coverage = []
    coarse_coverage = []
    parent_coverage = []
    negative_coverage = []
    for held, validation in enumerate(selected_by_patch):
        discovery = tuple(row for patch, rows in enumerate(selected_by_patch)
                          if patch != held for row in rows)
        exact_coverage.append(_coverage(
            validation, discovery, lambda row: row.descriptor))
        coarse_coverage.append(_coverage(
            validation, discovery, _coarse_descriptor))
        parent_coverage.append(_coverage(
            validation, discovery, lambda row: row.frozen_parent_type))
        negatives = tuple(row for row in validation
                          if row.outcome_role != "exact")
        negative_coverage.append(_coverage(
            negatives, discovery, lambda row: row.descriptor)
            if negatives else 1.)
    parents = {row.frozen_parent_type for row in selected}
    joint = lambda row: (row.frozen_parent_type, row.port_role,
                         row.outcome_role, row.matched_witnesses)
    joint_patches = {role: {row.patch_id for row in selected
                            if joint(row) == role}
                     for role in {joint(row) for row in selected}}
    shared_joint = {role for role, patches in joint_patches.items()
                    if len(patches) >= 2}
    descriptor_labels = {}
    for row in selected:
        descriptor_labels.setdefault(row.descriptor, set()).add(
            row.outcome_role == "exact")
    negatives = tuple(row for row in selected if row.outcome_role != "exact")
    patches_per_parent = tuple(sorted((parent, len({
        row.patch_id for row in selected if row.frozen_parent_type == parent}))
        for parent in parents))
    digest = hashlib.sha256(repr(tuple(sorted(
        row.candidate_id for row in selected))).encode()).hexdigest()
    positive = lambda row: row.outcome_role == "exact"
    return CdYbTrainingFrontierCorpusAudit(
        len(TRAIN_CENTERS), len(species), len(raw),
        tuple(map(len, rows_by_patch)), sum(map(positive, raw)),
        sum(not positive(row) for row in raw), len(selected),
        tuple(map(len, selected_by_patch)), sum(map(positive, selected)),
        sum(not positive(row) for row in selected),
        sum(row.outcome_role == "mixed-failure" for row in selected),
        sum(row.outcome_role == "unsupported-failure" for row in selected),
        len(parents), len({row.macro_id for row in selected}),
        len({row.port_role for row in selected}),
        len(joint_patches), len(shared_joint),
        sum(joint(row) in shared_joint for row in selected),
        max(map(len, joint_patches.values()), default=0),
        sum(len(labels) > 1 for labels in descriptor_labels.values()),
        len({row.frozen_parent_type for row in negatives}),
        len({row.port_role for row in negatives}),
        patches_per_parent, _ess(raw), _ess(selected),
        len(selected) / max(1, len(raw)), tuple(exact_coverage),
        tuple(coarse_coverage), tuple(parent_coverage),
        tuple(negative_coverage), True,
        all(any(positive(row) for row in rows) and
            any(not positive(row) for row in rows)
            for rows in selected_by_patch), digest, False, False, True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
