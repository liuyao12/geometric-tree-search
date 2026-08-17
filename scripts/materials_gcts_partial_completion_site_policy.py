#!/usr/bin/env python3
"""Generic frozen local-site marking for partial completion sections."""

from __future__ import annotations

import math
from dataclasses import dataclass

from materials_gcts_oriented_overlap_ports import matmul, matvec


SITE_SECTION_FEATURE_NAMES = (
    "same_species_fraction", "rhs_radial_distance_nn",
    "nearest_seed_distance_nn", "nearest_witness_distance_nn",
    "nearest_emitted_distance_nn", "rhs_local_neighbors",
    "child_site_multiplicity", "matched_child_fraction",
    "missing_children", "log_port_evidence")
SITE_SECTION_AGGREGATIONS = ("minimum", "lower-quartile", "mean")


@dataclass(frozen=True)
class FrozenLocalSiteSectionPolicy:
    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    intercept: float
    aggregation: str
    site_acceptance_threshold: float
    target_used: bool = False
    candidate_id_or_global_coordinate_feature_used: bool = False


@dataclass(frozen=True)
class ScoredCompletionSection:
    section_id: str
    site_scores: tuple[tuple[tuple, float], ...]
    aggregate_score: float


def adapt_frozen_site_section(model) -> FrozenLocalSiteSectionPolicy:
    """Copy a fitted structural model without importing its material module."""
    if (getattr(model, "target_used", True) or
            getattr(model, "candidate_id_or_global_coordinate_feature_used",
                    True)):
        raise ValueError("site section must be target/ID/global-coordinate free")
    names = tuple(model.feature_names)
    if names != SITE_SECTION_FEATURE_NAMES:
        raise ValueError("site section feature schema is not executable")
    vectors = tuple(tuple(map(float, getattr(model, field))) for field in
                    ("means", "scales", "weights"))
    if any(len(vector) != len(names) for vector in vectors):
        raise ValueError("site section has inconsistent dimensions")
    if any(scale <= 0 or not math.isfinite(scale) for scale in vectors[1]):
        raise ValueError("site section has invalid standardization scales")
    aggregation = model.whole_action_aggregation
    if aggregation not in SITE_SECTION_AGGREGATIONS:
        raise ValueError("site section has unknown frozen aggregation")
    threshold = float(model.site_acceptance_threshold)
    if not 0 <= threshold <= 1 or not math.isfinite(threshold):
        raise ValueError("site section has invalid frozen site threshold")
    values = (*vectors[0], *vectors[1], *vectors[2], float(model.intercept))
    if any(not math.isfinite(value) for value in values):
        raise ValueError("site section contains nonfinite parameters")
    return FrozenLocalSiteSectionPolicy(
        names, vectors[0], vectors[1], vectors[2], float(model.intercept),
        aggregation, threshold, False, False)


def _add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def _site_key(site, tolerance):
    return (repr(site[0]),) + tuple(round(value / tolerance)
                                    for value in site[1])


def _render(prototype, rotation, translation):
    return tuple((species, _add(matvec(rotation, point), translation))
                 for species, point in prototype.sites)


def _distance(point, sites, scale):
    return min((math.dist(point, other) / scale for _species, other in sites),
               default=20.)


def completion_site_feature_context(program, macro, completion, candidate,
                                    seed_sites, pose_tolerance=.03):
    """Freeze the whole-candidate geometry used by every section site."""
    if getattr(program, "target_used", False) or completion.target_used:
        raise ValueError("site features require target-free frozen geometry")
    scale = getattr(program, "minimum_distance", 0.)
    if scale <= 0 or not math.isfinite(scale):
        raise ValueError("site features need a positive frozen length scale")
    prototypes = {item.type_id: item for item in program.prototypes}
    rendered = []
    for placement in macro.child_placements:
        rotation = matmul(completion.macro_rotation, placement.rotation)
        shifted = matvec(completion.macro_rotation, placement.translation)
        translation = _add(completion.macro_translation, shifted)
        rendered.append((placement.node, _render(
            prototypes[placement.cluster_type], rotation, translation)))
    seed_sites = tuple((species, tuple(map(float, point)))
                       for species, point in seed_sites)
    seed_keys = {_site_key(site, pose_tolerance) for site in seed_sites}
    full_by_key = {_site_key(site, pose_tolerance): site
                   for _node, sites in rendered for site in sites}
    full_sites = tuple(full_by_key[key] for key in sorted(full_by_key))
    matched = set(completion.matched_nodes)
    witness_sites = tuple(site for node, sites in rendered
                          if node in matched for site in sites)
    emitted_by_key = {
        _site_key(site, pose_tolerance): site
        for child in completion.missing_children for site in child.sites
        if _site_key(site, pose_tolerance) not in seed_keys}
    emitted_sites = tuple(emitted_by_key[key]
                          for key in sorted(emitted_by_key))
    multiplicity = {}
    for _node, sites in rendered:
        for site in sites:
            key = _site_key(site, pose_tolerance)
            multiplicity[key] = multiplicity.get(key, 0) + 1
    centroid = tuple(sum(point[axis] for _species, point in full_sites) /
                     len(full_sites) for axis in range(3))
    species_counts = {}
    for species, _point in full_sites:
        species_counts[species] = species_counts.get(species, 0) + 1
    return {
        "scale": scale, "seed_sites": seed_sites,
        "witness_sites": witness_sites, "full_sites": full_sites,
        "emitted_sites": emitted_sites, "multiplicity": multiplicity,
        "centroid": centroid, "species_counts": species_counts,
        "matched_fraction": (len(completion.matched_nodes) /
                             len(macro.child_placements)),
        "missing_children": len(completion.missing_children),
        "port_evidence": candidate.descriptor.training_port_evidence,
        "pose_tolerance": pose_tolerance}


def completion_site_features(site, context):
    """The exact ten local, distance-based, proper-SE(3)-invariant features."""
    species, point = site
    full_sites = context["full_sites"]
    emitted_sites = context["emitted_sites"]
    tolerance = context["pose_tolerance"]
    key = _site_key(site, tolerance)
    other_emitted = tuple(other for other in emitted_sites
                          if _site_key(other, tolerance) != key)
    scale = context["scale"]
    return (
        context["species_counts"].get(species, 0) / len(full_sites),
        math.dist(point, context["centroid"]) / scale,
        _distance(point, context["seed_sites"], scale),
        _distance(point, context["witness_sites"], scale),
        _distance(point, other_emitted, scale),
        float(sum(0 < math.dist(point, other) <= 1.6 * scale
                  for _label, other in full_sites)),
        float(context["multiplicity"].get(key, 1)),
        context["matched_fraction"],
        float(context["missing_children"]),
        math.log1p(context["port_evidence"]))


def _sigmoid(value):
    value = max(-50., min(50., value))
    return 1 / (1 + math.exp(-value))


def score_site_features(policy: FrozenLocalSiteSectionPolicy, features):
    if policy.target_used or policy.candidate_id_or_global_coordinate_feature_used:
        raise ValueError("tainted site section policy is forbidden")
    if len(features) != len(policy.feature_names):
        raise ValueError("site feature dimension does not match frozen policy")
    return _sigmoid(policy.intercept + sum(
        weight * (value - mean) / scale
        for weight, value, mean, scale in zip(
            policy.weights, features, policy.means, policy.scales)))


def _aggregate(values, kind):
    values = sorted(values)
    if not values:
        raise ValueError("a section must contain at least one emitted site")
    if kind == "minimum":
        return values[0]
    if kind == "lower-quartile":
        return values[(len(values) - 1) // 4]
    if kind == "mean":
        return sum(values) / len(values)
    raise ValueError("unknown site aggregation")


def score_completion_sections(policy, sections, program, macro, completion,
                              candidate, seed_sites, pose_tolerance=.03):
    """Score fixed section IDs; never add, remove, or repartition candidates."""
    context = completion_site_feature_context(
        program, macro, completion, candidate, seed_sites, pose_tolerance)
    emitted_keys = {_site_key(site, pose_tolerance)
                    for site in context["emitted_sites"]}
    result = []
    for section in sections:
        rows = []
        for site in section.sites:
            key = _site_key(site, pose_tolerance)
            if key not in emitted_keys:
                continue
            features = completion_site_features(site, context)
            rows.append((key, score_site_features(policy, features)))
        rows = tuple(sorted(rows, key=repr))
        if rows:
            result.append(ScoredCompletionSection(
                section.section_id, rows,
                _aggregate(tuple(score for _key, score in rows),
                           policy.aggregation)))
    return tuple(result)
