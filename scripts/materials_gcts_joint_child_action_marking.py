#!/usr/bin/env python3
"""ID-free joint marking for immutable three-site child actions.

Unlike the earlier minimum-over-site channel, this representation keeps the
three proposed sites together.  It concatenates invariant local sections in a
species/fingerprint canonical order, colored pair-distance summaries inside
the child and parent, all colored child-to-parent cross distances, and the
four already-frozen legacy scores.  It contains no candidate id, coordinate
frame, global origin, lattice address, family label, or target value.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

from materials_gcts_local_section_child_marking import (
    FrozenLocalSectionSchema, feature_names as site_feature_names,
    local_section_features)


FORMAT = "materials-gcts-joint-child-action-marking-v1"
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_joint_child_action_marking_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "4c8c3c6ee41e1277e59934c11c4e531a498edb0fa24fa1f876c3ba11998023df")
EXPECTED_MODEL_DIGEST = (
    "99e459ee26914377f4e6525dd4bfbb50822e22de6f5d43d1eb4ae5e76ce136f7")
EXPECTED_ARTIFACT_DIGEST = (
    "98b32b6944ddb0516d5e6e22aed72019b6b2cb7f2f5d8de70d83de1e9c08f2c2")
PAIR_STAT_NAMES = ("count", "minimum", "mean", "maximum")


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


@dataclass(frozen=True)
class FrozenJointChildActionMarking:
    site_schema: FrozenLocalSectionSchema
    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    intercept: float
    ridge_lambda: float
    positive_weight: float
    child_top_k: int
    model_digest: str
    target_used_for_fitting: bool
    target_used_for_scoring: bool = False


def _branch_value(branch, name):
    return branch[name] if isinstance(branch, dict) else getattr(branch, name)


def _action_key(action, decimals):
    point, color = action
    return tuple(round(float(value), decimals) for value in point), str(color)


def _stats(values):
    values = tuple(values)
    if not values:
        return 0., 0., 0., 0.
    return (float(len(values)), min(values), sum(values) / len(values),
            max(values))


def _species_pairs(species):
    return tuple((species[first], species[second])
                 for first in range(len(species))
                 for second in range(first, len(species)))


def _internal_pair_summary(actions, species):
    rows = []
    for first_species, second_species in _species_pairs(species):
        distances = []
        for first, (point, color) in enumerate(actions):
            for second in range(first + 1, len(actions)):
                other_point, other_color = actions[second]
                if tuple(sorted((color, other_color))) != tuple(sorted(
                        (first_species, second_species))):
                    continue
                distances.append(math.dist(point, other_point))
        rows.extend(_stats(distances))
    return tuple(rows)


def _cross_pair_summary(children, parents, species):
    rows = []
    for child_species in species:
        for parent_species in species:
            rows.extend(_stats(math.dist(child_point, parent_point)
                               for child_point, child_color in children
                               for parent_point, parent_color in parents
                               if child_color == child_species and
                               parent_color == parent_species))
    return tuple(rows)


def joint_feature_names(schema: FrozenLocalSectionSchema):
    names = []
    site_names = site_feature_names(schema)
    for slot in range(3):
        names.extend(f"child-site-{slot}:{name}" for name in site_names)
    names.extend(f"child-composition:{color}" for color in schema.species)
    names.extend(f"parent-composition:{color}" for color in schema.species)
    for prefix in ("child-internal", "parent-internal"):
        for first, second in _species_pairs(schema.species):
            names.extend(f"{prefix}:{first}-{second}:{stat}"
                         for stat in PAIR_STAT_NAMES)
    for child in schema.species:
        for parent in schema.species:
            names.extend(f"child-parent:{child}-{parent}:{stat}"
                         for stat in PAIR_STAT_NAMES)
    names.extend(f"legacy-score:{name}"
                 for name in schema.source_channel_names)
    return tuple(names)


def joint_child_action_features(*, seed_positions, seed_species, branch,
                                schema: FrozenLocalSectionSchema):
    """Return one SE(3)-invariant vector for each immutable child index."""
    local = local_section_features(
        seed_positions=seed_positions, seed_species=seed_species,
        branch=branch, schema=schema)
    parents = tuple((tuple(map(float, point)), str(color))
                    for point, color in _branch_value(branch, "first_actions"))
    child_rows = tuple(_branch_value(branch, "second_actions"))
    channel_rows = tuple(_branch_value(branch, "second_channel_scores"))
    if (len(parents) != 3 or len(child_rows) != len(channel_rows) or
            any(len(row) != len(schema.source_channel_names)
                for row in channel_rows)):
        raise ValueError("invalid joint child-action portfolio")
    expected = joint_feature_names(schema)
    output = []
    for child_index, raw_actions in enumerate(child_rows):
        actions = tuple((tuple(map(float, point)), str(color))
                        for point, color in raw_actions)
        if len(actions) != 3:
            raise ValueError("joint child marking requires three-site actions")
        site_rows = sorted((color, local[_action_key(
            (point, color), schema.site_key_decimals)])
                           for point, color in actions)
        values = []
        for _color, row in site_rows:
            values.extend(row)
        values.extend(sum(color == species for _point, color in actions)
                      for species in schema.species)
        values.extend(sum(color == species for _point, color in parents)
                      for species in schema.species)
        values.extend(_internal_pair_summary(actions, schema.species))
        values.extend(_internal_pair_summary(parents, schema.species))
        values.extend(_cross_pair_summary(actions, parents, schema.species))
        values.extend(map(float, channel_rows[child_index]))
        if (len(values) != len(expected) or
                any(not math.isfinite(value) for value in values)):
            raise AssertionError("joint child-action feature schema drift")
        output.append(tuple(values))
    return tuple(output)


def score_joint_vector(model: FrozenJointChildActionMarking, values):
    values = tuple(map(float, values))
    if len(values) != len(model.feature_names):
        raise ValueError("joint child-action feature length drift")
    return model.intercept + sum(
        weight * ((value - mean) / scale)
        for value, mean, scale, weight in zip(
            values, model.means, model.scales, model.weights))


def rank_joint_children(*, model, seed_positions, seed_species, branch):
    features = joint_child_action_features(
        seed_positions=seed_positions, seed_species=seed_species,
        branch=branch, schema=model.site_schema)
    rows = tuple((index, score_joint_vector(model, values))
                 for index, values in enumerate(features))
    return tuple(sorted(rows, key=lambda row: (-row[1], row[0])))


def select_joint_child_ids(*, model, seed_positions, seed_species, branch):
    ranked = rank_joint_children(
        model=model, seed_positions=seed_positions,
        seed_species=seed_species, branch=branch)
    return tuple(child for child, _score in ranked[:min(
        model.child_top_k, len(ranked))])


def model_payload(model):
    return {
        "site_schema": {
            "species": model.site_schema.species,
            "reach": model.site_schema.reach,
            "radial_bin_width": model.site_schema.radial_bin_width,
            "nearest_per_species": model.site_schema.nearest_per_species,
            "source_channel_names":
                model.site_schema.source_channel_names,
            "site_key_decimals": model.site_schema.site_key_decimals,
        },
        "feature_names": model.feature_names,
        "means": model.means,
        "scales": model.scales,
        "weights": model.weights,
        "intercept": model.intercept,
        "ridge_lambda": model.ridge_lambda,
        "positive_weight": model.positive_weight,
        "child_top_k": model.child_top_k,
        "target_used_for_fitting": model.target_used_for_fitting,
        "target_used_for_scoring": model.target_used_for_scoring,
    }


def compute_model_digest(model):
    return hashlib.sha256(canonical_json(model_payload(model))).hexdigest()


def model_from_artifact(artifact):
    if artifact.get("format") != FORMAT:
        raise ValueError("unknown joint child-action artifact")
    data = artifact["model"]
    schema_data = data["site_schema"]
    schema = FrozenLocalSectionSchema(
        tuple(schema_data["species"]), schema_data["reach"],
        schema_data["radial_bin_width"],
        schema_data["nearest_per_species"],
        tuple(schema_data["source_channel_names"]),
        schema_data["site_key_decimals"])
    model = FrozenJointChildActionMarking(
        schema, tuple(data["feature_names"]), tuple(data["means"]),
        tuple(data["scales"]), tuple(data["weights"]), data["intercept"],
        data["ridge_lambda"], data["positive_weight"], data["child_top_k"],
        artifact["model_digest"], data["target_used_for_fitting"],
        data["target_used_for_scoring"])
    if (model.feature_names != joint_feature_names(schema) or
            len(model.means) != len(model.feature_names) or
            len(model.scales) != len(model.feature_names) or
            len(model.weights) != len(model.feature_names) or
            any(scale <= 0 or not math.isfinite(scale)
                for scale in model.scales) or
            compute_model_digest(model) != model.model_digest):
        raise AssertionError("joint child-action model drift")
    return model


def load_default_marking(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("joint child-action fixture drift")
    artifact = json.loads(gzip.decompress(raw))
    computed = hashlib.sha256(canonical_json({
        key: value for key, value in artifact.items()
        if key != "artifact_digest"})).hexdigest()
    if (computed != artifact.get("artifact_digest") or
            (EXPECTED_ARTIFACT_DIGEST and
             computed != EXPECTED_ARTIFACT_DIGEST)):
        raise AssertionError("joint child-action audit digest drift")
    model = model_from_artifact(artifact)
    if EXPECTED_MODEL_DIGEST and model.model_digest != EXPECTED_MODEL_DIGEST:
        raise AssertionError("joint child-action model digest drift")
    return model, artifact


__all__ = [
    "FrozenJointChildActionMarking", "compute_model_digest",
    "joint_child_action_features", "joint_feature_names",
    "load_default_marking", "model_payload", "rank_joint_children",
    "score_joint_vector", "select_joint_child_ids"]
