#!/usr/bin/env python3
"""Leakage-resistant nested-crop benchmark for colored point-set growth.

The harness is deliberately independent of a material family and of the
learner's internal representation.  It gives the fitter only the innermost
crop, freezes the resulting artifact, and gives the grower only that same
crop plus a public radial boundary.  The two outer crops are used exclusively
by the scorer after inference.

This does not attempt to sandbox hostile Python callbacks.  It does make the
intended information boundary explicit, testable, and difficult to violate by
accident: neither callback accepts a held-out configuration, and mutation of
the serialized learned artifact is detected.
"""

from __future__ import annotations

import hashlib
import itertools
import math
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from materials_gcts_generic import AtomicConfiguration
from materials_gcts_recursive_connections import point_key

Point = tuple[float, float, float]
ColoredSite = tuple[Point, str]
Program = TypeVar("Program")


@dataclass(frozen=True)
class NestedCropSplit:
    """Three fixed, cumulative radial crops from one immutable oracle."""

    training: AtomicConfiguration
    validation: AtomicConfiguration
    test: AtomicConfiguration
    origin: Point
    radii: tuple[float, float, float]
    fixture_sha256: str


@dataclass(frozen=True)
class ProgramAudit:
    """Train-only facts reported by a generic cluster/GCTS learner."""

    fitted_atoms: int
    covered_training_sites: int
    cluster_types: int
    gap_cluster_types: int
    marking_states: int
    hierarchy_depth: int
    learned_from_seed_only: bool
    family_label_used: bool
    physical_potential_used: bool


@dataclass(frozen=True)
class FittedProgram(Generic[Program]):
    program: Program
    audit: ProgramAudit


@dataclass(frozen=True)
class GrowthTrace:
    """Inference output and work counters; sites may include known seed sites."""

    emitted_sites: frozenset[ColoredSite]
    proposed_actions: int
    accepted_actions: int
    rejected_actions: int
    hierarchy_depth_used: int


@dataclass(frozen=True)
class AnnulusScore:
    truth_sites: int
    predicted_sites: int
    geometry_matches: int
    colored_matches: int
    geometry_precision: float
    geometry_recall: float
    colored_precision: float
    colored_recall: float
    matched_species_accuracy: float


@dataclass(frozen=True)
class TransferThresholds:
    minimum_training_cover_fraction: float = 1.0
    minimum_validation_precision: float = .99
    minimum_validation_recall: float = .90
    minimum_test_precision: float = .99
    minimum_test_recall: float = .90
    minimum_species_accuracy: float = .99
    minimum_hierarchy_depth: int = 3
    minimum_marking_proposal_reduction: float = 10.0
    minimum_marking_failed_proposal_reduction: float = 10.0
    minimum_marking_recall_retention: float = .99
    matching_tolerance: float = .15


@dataclass(frozen=True)
class NestedTransferReport:
    fixture_sha256: str
    training_atoms: int
    validation_atoms: int
    test_atoms: int
    frozen_program_sha256: str
    frozen_program_bytes: int
    training_cover_fraction: float
    known_region_conflicts: int
    out_of_bounds_predictions: int
    validation: AnnulusScore
    test: AnnulusScore
    marked_proposed_actions: int
    unmarked_proposed_actions: int
    marking_proposal_reduction: float
    marked_rejected_actions: int
    unmarked_rejected_actions: int
    marking_failed_proposal_reduction: float
    marking_recall_retention: float
    program_immutable_during_scoring: bool
    provenance_gate_passed: bool
    cover_gate_passed: bool
    transfer_gate_passed: bool
    hierarchy_gate_passed: bool
    marking_ablation_gate_passed: bool
    benchmark_passed: bool


Fit = Callable[[AtomicConfiguration], FittedProgram[Program]]
Grow = Callable[[Program, AtomicConfiguration, Point, float, bool], GrowthTrace]
Serialize = Callable[[Program], bytes]


def _sites(configuration: AtomicConfiguration) -> frozenset[ColoredSite]:
    return frozenset(zip(map(point_key, configuration.positions),
                         configuration.species))


def validate_nested_crops(split: NestedCropSplit, tolerance: float = 1e-6) -> None:
    """Reject malformed or non-nested fixtures before a learner is called."""
    if (len(split.fixture_sha256) != 64 or any(
            character not in "0123456789abcdef"
            for character in split.fixture_sha256.lower())):
        raise ValueError("fixture_sha256 must pin the normalized oracle bytes")
    if not 0 < split.radii[0] < split.radii[1] < split.radii[2]:
        raise ValueError("crop radii must be positive and strictly increasing")
    configurations = (split.training, split.validation, split.test)
    site_sets = tuple(_sites(configuration) for configuration in configurations)
    if not site_sets[0] < site_sets[1] < site_sets[2]:
        raise ValueError("fixed crops must be strict cumulative colored-site sets")
    # A nested split is a partition by radius, not merely three overlapping
    # samples.  This catches an easy source of optimistic transfer scores:
    # selectively omitting difficult inner sites from the smaller crops.
    for sites, radius in zip(site_sets[:2], split.radii[:2]):
        restriction = frozenset(
            site for site in site_sets[2]
            if math.dist(site[0], split.origin) <= radius + tolerance)
        if sites != restriction:
            raise ValueError("inner crops must equal radial restrictions of test")
    for configuration, radius in zip(configurations, split.radii):
        if any(math.dist(point, split.origin) > radius + tolerance
               for point in configuration.positions):
            raise ValueError("crop contains a site outside its declared radius")
        if configuration.periodic:
            raise ValueError("transfer crops must be explicit, non-periodic sites")


def _annulus(sites: frozenset[ColoredSite], origin: Point,
             inner: float, outer: float) -> frozenset[ColoredSite]:
    return frozenset((point, species) for point, species in sites
                     if inner < math.dist(point, origin) <= outer)


def _greedy_matches(predicted: frozenset[ColoredSite],
                    truth: frozenset[ColoredSite], tolerance: float,
                    require_species: bool) -> tuple[int, int]:
    """Return unique geometric matches and species-correct matched pairs."""
    if tolerance < 0:
        raise ValueError("matching tolerance must be nonnegative")
    if tolerance == 0:
        if require_species:
            count = len(predicted & truth)
            return count, count
        predicted_points = {point: species for point, species in predicted}
        truth_points = {point: species for point, species in truth}
        common = predicted_points.keys() & truth_points.keys()
        return len(common), sum(predicted_points[p] == truth_points[p]
                                for p in common)
    inverse = 1.0 / tolerance
    grid: dict[tuple[int, int, int], list[tuple[Point, str]]] = {}
    for point, species in truth:
        cell = tuple(math.floor(value * inverse) for value in point)
        grid.setdefault(cell, []).append((point, species))
    candidates = []
    ordered_predictions = tuple(sorted(predicted))
    for predicted_index, (point, species) in enumerate(ordered_predictions):
        cell = tuple(math.floor(value * inverse) for value in point)
        for offset in itertools.product((-1, 0, 1), repeat=3):
            for target in grid.get(tuple(cell[axis] + offset[axis]
                                         for axis in range(3)), ()):
                target_point, target_species = target
                if require_species and species != target_species:
                    continue
                distance = math.dist(point, target_point)
                if distance <= tolerance:
                    candidates.append((distance, predicted_index, target))
    used_predictions = set()
    used_targets = set()
    species_correct = 0
    for _, predicted_index, target in sorted(candidates):
        target_key = target
        if predicted_index in used_predictions or target_key in used_targets:
            continue
        used_predictions.add(predicted_index)
        used_targets.add(target_key)
        species_correct += ordered_predictions[predicted_index][1] == target[1]
    return len(used_predictions), species_correct


def score_annulus(predicted: frozenset[ColoredSite],
                  truth: frozenset[ColoredSite], tolerance: float) -> AnnulusScore:
    geometry_matches, species_correct = _greedy_matches(
        predicted, truth, tolerance, False)
    colored_matches, _ = _greedy_matches(predicted, truth, tolerance, True)
    return AnnulusScore(
        len(truth), len(predicted), geometry_matches, colored_matches,
        geometry_matches / max(1, len(predicted)),
        geometry_matches / max(1, len(truth)),
        colored_matches / max(1, len(predicted)),
        colored_matches / max(1, len(truth)),
        species_correct / max(1, geometry_matches))


def evaluate_nested_transfer(
        split: NestedCropSplit, fit: Fit[Program], grow: Grow[Program],
        serialize: Serialize[Program],
        thresholds: TransferThresholds = TransferThresholds(),
        ) -> NestedTransferReport:
    """Fit once on the inner crop, then score two unseen radial annuli.

    ``grow`` is called twice with identical seed evidence and boundary: once
    with the marking and once as its ablation.  It never receives either
    held-out configuration.  The same serialized program must survive both
    calls unchanged.
    """
    validate_nested_crops(split)
    fitted = fit(split.training)
    audit = fitted.audit
    if audit.fitted_atoms != len(split.training.positions):
        raise ValueError("learner audit does not match the supplied seed")
    frozen = serialize(fitted.program)
    if not isinstance(frozen, bytes) or not frozen:
        raise ValueError("serialize must return nonempty immutable bytes")
    digest = hashlib.sha256(frozen).hexdigest()
    marked = grow(fitted.program, split.training, split.origin,
                  split.radii[2], True)
    digest_after_marked = hashlib.sha256(serialize(fitted.program)).hexdigest()
    unmarked = grow(fitted.program, split.training, split.origin,
                    split.radii[2], False)
    for trace in (marked, unmarked):
        if min(trace.proposed_actions, trace.accepted_actions,
               trace.rejected_actions, trace.hierarchy_depth_used) < 0:
            raise ValueError("growth work counters must be nonnegative")
        if trace.accepted_actions + trace.rejected_actions != trace.proposed_actions:
            raise ValueError("growth proposals must partition into accept/reject")
    digest_after_unmarked = hashlib.sha256(serialize(fitted.program)).hexdigest()
    immutable = digest == digest_after_marked == digest_after_unmarked

    seed_sites = _sites(split.training)
    predicted = marked.emitted_sites - seed_sites
    known_region_conflicts = sum(
        math.dist(point, split.origin) <= split.radii[0]
        for point, _ in predicted)
    out_of_bounds = sum(
        math.dist(point, split.origin) > split.radii[2]
        for point, _ in predicted)
    validation_prediction = _annulus(
        predicted, split.origin, split.radii[0], split.radii[1])
    test_prediction = _annulus(
        predicted, split.origin, split.radii[1], split.radii[2])
    validation_truth = _annulus(
        _sites(split.validation), split.origin,
        split.radii[0], split.radii[1])
    test_truth = _annulus(
        _sites(split.test), split.origin, split.radii[1], split.radii[2])
    validation = score_annulus(
        validation_prediction, validation_truth, thresholds.matching_tolerance)
    test = score_annulus(
        test_prediction, test_truth, thresholds.matching_tolerance)

    cover = audit.covered_training_sites / max(1, audit.fitted_atoms)
    reduction = (unmarked.proposed_actions /
                 max(1, marked.proposed_actions))
    failed_reduction = (unmarked.rejected_actions /
                        max(1, marked.rejected_actions))
    unmarked_sites = unmarked.emitted_sites - seed_sites
    unmarked_test = score_annulus(
        _annulus(unmarked_sites, split.origin,
                 split.radii[1], split.radii[2]),
        test_truth, thresholds.matching_tolerance)
    recall_retention = (test.colored_recall /
                        max(1e-12, unmarked_test.colored_recall))
    provenance_gate = (
        audit.learned_from_seed_only and not audit.family_label_used and
        not audit.physical_potential_used and immutable)
    cover_gate = (cover >= thresholds.minimum_training_cover_fraction and
                  audit.cluster_types + audit.gap_cluster_types > 0)
    transfer_gate = (
        known_region_conflicts == 0 and out_of_bounds == 0 and
        validation.colored_precision >= thresholds.minimum_validation_precision and
        validation.colored_recall >= thresholds.minimum_validation_recall and
        test.colored_precision >= thresholds.minimum_test_precision and
        test.colored_recall >= thresholds.minimum_test_recall and
        min(validation.matched_species_accuracy,
            test.matched_species_accuracy) >= thresholds.minimum_species_accuracy)
    hierarchy_gate = (
        audit.hierarchy_depth >= thresholds.minimum_hierarchy_depth and
        marked.hierarchy_depth_used >= thresholds.minimum_hierarchy_depth)
    ablation_gate = (
        reduction >= thresholds.minimum_marking_proposal_reduction and
        failed_reduction >=
        thresholds.minimum_marking_failed_proposal_reduction and
        recall_retention >= thresholds.minimum_marking_recall_retention)
    passed = (provenance_gate and cover_gate and transfer_gate and
              hierarchy_gate and ablation_gate)
    return NestedTransferReport(
        split.fixture_sha256, len(split.training.positions),
        len(split.validation.positions), len(split.test.positions), digest,
        len(frozen), cover, known_region_conflicts, out_of_bounds,
        validation, test, marked.proposed_actions,
        unmarked.proposed_actions, reduction, marked.rejected_actions,
        unmarked.rejected_actions, failed_reduction, recall_retention, immutable,
        provenance_gate, cover_gate, transfer_gate, hierarchy_gate,
        ablation_gate, passed)
