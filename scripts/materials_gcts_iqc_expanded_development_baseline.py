#!/usr/bin/env python3
"""Open the preregistered IQC development batch and audit the frozen quotient."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_incidence_token_marking import score_incidence_descriptor
from materials_gcts_iqc_expanded_development_preregistration import (
    EXPANDED_DEVELOPMENT_CENTERS, audit as preregistration_audit)
from materials_gcts_iqc_incidence_geometry_selection import (
    _ranked_antichain, _statistics)
from materials_gcts_iqc_incidence_token_preflight import (
    _CandidateSource, _build_candidate_fixture,
    _candidate_groups_for_geometry, _key, _minimum_distance)
from materials_gcts_iqc_joint_incidence_graph_preflight import (
    JointFitSpec, _fit)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_orbit_disagreement_preflight import (
    CONSUMED_CONFIRMATION_CENTER)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    EVALUATION_SEED_RADIUS, EVALUATION_TARGET_RADIUS, _crop, _open_target,
    _seed_crop)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)
from materials_gcts_icosahedral_modelset import oracle_patch_fast


EXPECTED_PREREGISTRATION_DIGEST = \
    "c21e3fa12d2b2670af48974e5fd3856383c3518887fe28669abcd4e9a6464d43"
FROZEN_QUOTIENT = (4, "coarse", "incidence")
FROZEN_FIT = JointFitSpec(4, 2, .5)
EXPANDED_ORACLE_LIFT_BOUND = 24


@dataclass(frozen=True)
class ExpandedDevelopmentBaseline:
    preregistration_digest: str
    prior_groups: int
    expanded_groups: int
    total_groups: int
    expanded_oracle_lift_bound: int
    expanded_oracle_bound_plus_one_stable: bool
    expanded_seed_atoms: tuple[int, ...]
    expanded_target_atoms: tuple[int, ...]
    candidates_by_group: tuple[int, ...]
    positives_by_group: tuple[int, ...]
    candidate_graph_digest: str
    descriptor_digest: str
    frozen_quotient: tuple[int, str, str]
    frozen_fit: JointFitSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    expanded_targets_materialized_after_preregistration_commit: bool
    reserved_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def _source(center, prototypes, connection, seed, target):
    proposals = _bounded_proposals(connection, prototypes, seed, center)
    return _CandidateSource(
        center, proposals, tuple(seed.positions), tuple(seed.species),
        {_key(point): color for point, color in zip(
            target.positions, target.species)},
        _minimum_distance(seed.positions))


def _expanded_groups():
    protocol = preregistration_audit()
    if protocol.manifest_digest != EXPECTED_PREREGISTRATION_DIGEST:
        raise AssertionError("expanded-development protocol drift")
    prototypes, connection, original_sources = _build_candidate_fixture()
    consumed = _source(
        CONSUMED_CONFIRMATION_CENTER, prototypes, connection,
        _seed_crop(CONSUMED_CONFIRMATION_CENTER),
        _open_target(CONSUMED_CONFIRMATION_CENTER))
    physical_radius = math.ceil(max(math.dist((0., 0., 0.), center)
        for center in EXPANDED_DEVELOPMENT_CENTERS) +
        EVALUATION_TARGET_RADIUS)
    oracle, _ = oracle_patch_fast(EXPANDED_ORACLE_LIFT_BOUND, physical_radius)
    check, _ = oracle_patch_fast(
        EXPANDED_ORACLE_LIFT_BOUND + 1, physical_radius)
    crops = tuple((
        _crop(oracle, center, EVALUATION_SEED_RADIUS,
              "IQC-expanded-development-seed"),
        _crop(oracle, center, EVALUATION_TARGET_RADIUS,
              "IQC-expanded-development-target"))
        for center in EXPANDED_DEVELOPMENT_CENTERS)
    check_counts = tuple((
        len(_crop(check, center, EVALUATION_SEED_RADIUS, "check-seed").positions),
        len(_crop(check, center, EVALUATION_TARGET_RADIUS,
                  "check-target").positions))
        for center in EXPANDED_DEVELOPMENT_CENTERS)
    crop_counts = tuple((len(seed.positions), len(target.positions))
                        for seed, target in crops)
    if crop_counts != check_counts:
        raise AssertionError("expanded oracle crop changes at bound plus one")
    expanded = tuple(_source(center, prototypes, connection, seed, target)
                     for center, (seed, target) in zip(
                         EXPANDED_DEVELOPMENT_CENTERS, crops))
    sources = original_sources + (consumed,) + expanded
    return _candidate_groups_for_geometry(
        sources, neighborhood_reach=3., distance_bin_width=.25,
        maximum_neighbors=8, joint_role_geometry=True,
        message_passing_rounds=1,
        message_distance_divisor=FROZEN_QUOTIENT[0],
        message_role_mode=FROZEN_QUOTIENT[1],
        message_encoding=FROZEN_QUOTIENT[2]), crop_counts


def evaluate() -> ExpandedDevelopmentBaseline:
    groups, crop_counts = _expanded_groups()
    statistics = _statistics(groups)
    selected = []
    for heldout_index, rows in enumerate(groups):
        model = _fit(statistics, tuple(
            index for index in range(len(groups))
            if index != heldout_index), FROZEN_FIT)
        selected.append(_ranked_antichain(tuple(
            (score_incidence_descriptor(model, row.descriptor), row)
            for row in rows), ACTIONS_PER_NUCLEUS))
    correct_by_group = tuple(sum(row.successful for row in rows)
                             for rows in selected)
    selected_total = sum(map(len, selected))
    correct_total = sum(correct_by_group)
    passed = selected_total == 2 * len(groups) and \
        correct_total == selected_total
    graph_digest = hashlib.sha256(repr(tuple(
        (row.group, row.point, row.color, row.minimum_distance)
        for group in groups for row in group)).encode()).hexdigest()
    descriptor_digest = hashlib.sha256(repr(tuple(
        (row.group, row.descriptor)
        for group in groups for row in group)).encode()).hexdigest()
    return ExpandedDevelopmentBaseline(
        EXPECTED_PREREGISTRATION_DIGEST, 10, len(EXPANDED_DEVELOPMENT_CENTERS),
        len(groups), EXPANDED_ORACLE_LIFT_BOUND, True,
        tuple(row[0] for row in crop_counts),
        tuple(row[1] for row in crop_counts),
        tuple(map(len, groups)), tuple(sum(
            row.successful for row in group) for group in groups),
        graph_digest, descriptor_digest, FROZEN_QUOTIENT, FROZEN_FIT,
        correct_by_group, selected_total, correct_total,
        selected_total - correct_total,
        correct_total / selected_total if selected_total else 0.,
        sum(value == ACTIONS_PER_NUCLEUS for value in correct_by_group),
        True, False, passed,
        "frozen finite quotient passes expanded development" if passed else
        "frozen finite quotient remains below expanded development gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
