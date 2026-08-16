#!/usr/bin/env python3
"""Frozen target-free ranking policies for partial completion execution."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Optional, Sequence, Union

from materials_gcts_partial_completion_marking import (
    CompletionRanking, FrozenCompletionCandidate, FrozenCompletionMarking,
    RankedCompletion, rank_completion_candidates)


CONTINUOUS_FEATURE_NAMES = (
    "matched_child_fraction", "log_emitted_atoms", "log_macro_atoms",
    "species_entropy", "macro_radial_rms_nn", "macro_radial_cv",
    "log_port_evidence", "log_boundary_slots", "mean_boundary_frequency",
    "log_incoming_port_kinds")


@dataclass(frozen=True)
class FrozenLinearCompletionPolicy:
    """An immutable standardized linear marking fitted before execution."""

    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    intercept: float
    target_used: bool = False


@dataclass(frozen=True)
class FrozenMacroFrequencyPolicy:
    """Train-frozen exact-type frequency baseline (not a semantic marking)."""

    scores: tuple[tuple[int, float], ...]
    marginal_score: float
    training_samples: int
    target_used: bool = False


CompletionExecutionPolicy = Optional[Union[
    FrozenCompletionMarking, FrozenLinearCompletionPolicy,
    FrozenMacroFrequencyPolicy]]


def adapt_continuous_completion_marking(model) -> FrozenLinearCompletionPolicy:
    """Copy the public frozen continuous model into the generic executor type."""
    if getattr(model, "target_used", True):
        raise ValueError("target-tainted continuous completion marking is forbidden")
    names = tuple(model.feature_names)
    if names != CONTINUOUS_FEATURE_NAMES:
        raise ValueError("continuous completion feature schema is not executable")
    vectors = tuple(tuple(map(float, getattr(model, field))) for field in
                    ("means", "scales", "weights"))
    if any(len(vector) != len(names) for vector in vectors):
        raise ValueError("continuous completion model has inconsistent dimensions")
    if any(scale <= 0 or not math.isfinite(scale) for scale in vectors[1]):
        raise ValueError("continuous completion model has invalid scales")
    values = (*vectors[0], *vectors[1], *vectors[2], float(model.intercept))
    if any(not math.isfinite(value) for value in values):
        raise ValueError("continuous completion model is not finite")
    return FrozenLinearCompletionPolicy(
        names, vectors[0], vectors[1], vectors[2], float(model.intercept), False)


def completion_continuous_features(candidate, completion, macro,
                                   minimum_distance):
    """ID/coordinate-free features used by the frozen continuous marking."""
    if minimum_distance <= 0 or not math.isfinite(minimum_distance):
        raise ValueError("a positive frozen minimum distance is required")
    sites = tuple(macro.atom_union)
    if not sites or not macro.child_placements:
        raise ValueError("completion macro must have atoms and children")
    species = {}
    for label, _point in sites:
        key = repr(label)
        species[key] = species.get(key, 0) + 1
    total = sum(species.values())
    entropy = -sum((value / total) * math.log(value / total)
                   for value in species.values() if value)
    centroid = tuple(sum(point[axis] for _, point in sites) / len(sites)
                     for axis in range(3))
    radii = tuple(math.dist(point, centroid) / minimum_distance
                  for _, point in sites)
    mean_radius = sum(radii) / len(radii)
    rms = math.sqrt(sum(value * value for value in radii) / len(radii))
    deviation = math.sqrt(sum((value - mean_radius) ** 2 for value in radii) /
                          len(radii))
    emitted_atoms = sum(len(child.sites) for child in completion.missing_children)
    slots = candidate.descriptor.alternative_boundary_slots
    return (
        len(completion.matched_nodes) / len(macro.child_placements),
        math.log1p(emitted_atoms), math.log1p(len(sites)), entropy,
        rms, deviation / max(mean_radius, 1e-12),
        math.log1p(candidate.descriptor.training_port_evidence),
        math.log1p(len(slots)),
        sum(item[2] / 10 for item in slots) / max(1, len(slots)),
        math.log1p(len(candidate.descriptor.anchor_incoming_ports)))


def _sigmoid(value):
    if value >= 0:
        inverse = math.exp(-min(value, 50.))
        return 1 / (1 + inverse)
    exponential = math.exp(max(value, -50.))
    return exponential / (1 + exponential)


def rank_execution_candidates(
    candidates: Sequence[FrozenCompletionCandidate], completion_by_id,
    macro_by_id, minimum_distance: float, policy: CompletionExecutionPolicy,
) -> CompletionRanking:
    """Rank one already-frozen candidate batch without changing membership."""
    candidates = tuple(candidates)
    if isinstance(policy, (FrozenCompletionMarking, type(None))):
        return rank_completion_candidates(candidates, policy)
    if policy.target_used:
        raise ValueError("target-tainted completion execution policy is forbidden")
    if len({item.candidate_id for item in candidates}) != len(candidates):
        raise ValueError("frozen completion candidate IDs must be unique")
    if isinstance(policy, FrozenLinearCompletionPolicy):
        if policy.feature_names != CONTINUOUS_FEATURE_NAMES:
            raise ValueError("linear completion policy feature schema mismatch")
        def score(item):
            features = completion_continuous_features(
                item, completion_by_id[item.candidate_id],
                macro_by_id[item.macro_id], minimum_distance)
            standardized = tuple((value - mean) / scale
                                 for value, mean, scale in zip(
                                     features, policy.means, policy.scales))
            return _sigmoid(policy.intercept + sum(
                weight * value for weight, value in
                zip(policy.weights, standardized)))
    elif isinstance(policy, FrozenMacroFrequencyPolicy):
        frequency = dict(policy.scores)
        def score(item):
            return frequency.get(item.macro_id, policy.marginal_score)
    else:
        raise TypeError("unsupported frozen completion execution policy")
    digest = hashlib.sha256(repr(tuple(sorted(
        item.candidate_id for item in candidates))).encode()).hexdigest()
    ordered = tuple(sorted(candidates, key=lambda item: (
        -score(item), item.stable_key)))
    ranked = tuple(RankedCompletion(item, score(item), index + 1)
                   for index, item in enumerate(ordered))
    return CompletionRanking(digest, ranked, True, False)
