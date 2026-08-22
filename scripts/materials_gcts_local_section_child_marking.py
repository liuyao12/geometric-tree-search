#!/usr/bin/env python3
"""ID-free local-section marking for finite child-action portfolios.

The marking scores only already-frozen actions.  Features contain proposed
species, radial histograms and nearest distances to the already placed seed
and parent actions, action recurrence across the frozen child set, and summary
statistics from pre-existing marking channels.  No target, family label,
global origin, lattice coordinate, candidate id, or hidden lift is a feature.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path


FORMAT = "materials-gcts-local-section-child-marking-v1"
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_local_section_child_marking_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "ed9791c608c98bd0d3ae9239f56ff00955323f336a016c51fcec99ebd0cc8361")
EXPECTED_MODEL_DIGEST = (
    "9b28158d2a1b6eb7edde39bd80e3ef885d04c6e0770b4905bc93f8e8cc24d714")
EXPECTED_ARTIFACT_DIGEST = (
    "9f8f3a73155b79b36d7b299a1f0db11ad082f5460569805fc8f6385770f15146")


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


@dataclass(frozen=True)
class FrozenLocalSectionSchema:
    species: tuple[str, ...]
    reach: float
    radial_bin_width: float
    nearest_per_species: int
    source_channel_names: tuple[str, ...]
    site_key_decimals: int = 6


@dataclass(frozen=True)
class FrozenLocalSectionChildMarking:
    schema: FrozenLocalSectionSchema
    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    intercept: float
    ridge_lambda: float
    child_top_k: int
    aggregation: str
    model_digest: str
    target_used_for_fitting: bool
    target_used_for_scoring: bool = False


def feature_names(schema: FrozenLocalSectionSchema) -> tuple[str, ...]:
    bins = round(schema.reach / schema.radial_bin_width)
    names = [f"proposed-species:{species}" for species in schema.species]
    for species in schema.species:
        names.extend(f"occupied-{species}:radial-bin-{index}"
                     for index in range(bins))
        names.extend(f"occupied-{species}:nearest-{index}"
                     for index in range(schema.nearest_per_species))
    names.append("frozen-child-state-occurrence-fraction")
    for channel in schema.source_channel_names:
        names.extend((f"source-{channel}:mean", f"source-{channel}:max",
                      f"source-{channel}:min"))
    return tuple(names)


def _branch_value(branch, name):
    return branch[name] if isinstance(branch, dict) else getattr(branch, name)


def _action_key(action, decimals):
    point, color = action
    return tuple(round(float(value), decimals) for value in point), str(color)


def local_section_features(*, seed_positions, seed_species, branch,
                           schema: FrozenLocalSectionSchema):
    """Return one invariant feature vector per unique proposed colored site."""
    seed_positions = tuple(tuple(map(float, point))
                           for point in seed_positions)
    seed_species = tuple(map(str, seed_species))
    if len(seed_positions) != len(seed_species) or not seed_positions:
        raise ValueError("invalid occupied seed")
    first_actions = tuple(_branch_value(branch, "first_actions"))
    child_actions = tuple(_branch_value(branch, "second_actions"))
    channel_scores = tuple(_branch_value(
        branch, "second_channel_scores"))
    if (not child_actions or len(child_actions) != len(channel_scores) or
            any(len(row) != len(schema.source_channel_names)
                for row in channel_scores)):
        raise ValueError("invalid frozen child portfolio")
    occurrences = {}
    action_payload = {}
    for state_index, actions in enumerate(child_actions):
        for action in actions:
            key = _action_key(action, schema.site_key_decimals)
            occurrences.setdefault(key, []).append(state_index)
            action_payload.setdefault(key, (tuple(map(float, action[0])),
                                            str(action[1])))
    occupied = tuple(zip(seed_positions, seed_species)) + tuple(
        (tuple(map(float, point)), str(color))
        for point, color in first_actions)
    bins = round(schema.reach / schema.radial_bin_width)
    if (bins < 1 or
            abs(bins * schema.radial_bin_width - schema.reach) > 1e-9):
        raise ValueError("reach must be an integer number of radial bins")
    result = {}
    for key in sorted(occurrences):
        point, color = action_payload[key]
        values = [float(color == species) for species in schema.species]
        for species in schema.species:
            histogram = [0.] * bins
            distances = []
            for occupied_point, occupied_species in occupied:
                if occupied_species != species:
                    continue
                distance = math.dist(point, occupied_point)
                if distance < schema.reach:
                    index = min(bins - 1, int(
                        distance / schema.radial_bin_width))
                    histogram[index] += 1.
                distances.append(distance)
            distances.sort()
            values.extend(histogram)
            values.extend((distances + [schema.reach] *
                           schema.nearest_per_species)[
                               :schema.nearest_per_species])
        states = occurrences[key]
        values.append(len(states) / len(child_actions))
        for channel in range(len(schema.source_channel_names)):
            scores = [float(channel_scores[index][channel])
                      for index in states]
            values.extend((sum(scores) / len(scores), max(scores),
                           min(scores)))
        if any(not math.isfinite(value) for value in values):
            raise ValueError("nonfinite local-section feature")
        result[key] = tuple(values)
    expected = feature_names(schema)
    if any(len(values) != len(expected) for values in result.values()):
        raise AssertionError("local-section feature schema drift")
    return result


def score_feature_vector(model: FrozenLocalSectionChildMarking, values):
    values = tuple(map(float, values))
    if len(values) != len(model.feature_names):
        raise ValueError("local-section feature length drift")
    logit = model.intercept + sum(
        weight * ((value - mean) / scale)
        for value, mean, scale, weight in zip(
            values, model.means, model.scales, model.weights))
    logit = max(-30., min(30., logit))
    return 1. / (1. + math.exp(-logit))


def rank_child_states(*, model: FrozenLocalSectionChildMarking,
                      seed_positions, seed_species, branch):
    """Rank the immutable child ids; this function cannot authorize geometry."""
    features = local_section_features(
        seed_positions=seed_positions, seed_species=seed_species,
        branch=branch, schema=model.schema)
    actions = tuple(_branch_value(branch, "second_actions"))
    scores = {key: score_feature_vector(model, vector)
              for key, vector in features.items()}
    rows = []
    for child_id, state_actions in enumerate(actions):
        site_scores = tuple(scores[_action_key(
            action, model.schema.site_key_decimals)]
            for action in state_actions)
        if model.aggregation == "minimum":
            score = min(site_scores)
        elif model.aggregation == "mean":
            score = sum(site_scores) / len(site_scores)
        else:
            raise ValueError("unsupported child marking aggregation")
        rows.append((child_id, score, site_scores))
    return tuple(sorted(rows, key=lambda row: (-row[1], row[0])))


def select_child_ids(*, model: FrozenLocalSectionChildMarking,
                     seed_positions, seed_species, branch):
    ranked = rank_child_states(
        model=model, seed_positions=seed_positions,
        seed_species=seed_species, branch=branch)
    return tuple(row[0] for row in ranked[:min(model.child_top_k,
                                                len(ranked))])


def model_payload(model: FrozenLocalSectionChildMarking):
    return {
        "schema": {
            "species": model.schema.species,
            "reach": model.schema.reach,
            "radial_bin_width": model.schema.radial_bin_width,
            "nearest_per_species": model.schema.nearest_per_species,
            "source_channel_names": model.schema.source_channel_names,
            "site_key_decimals": model.schema.site_key_decimals,
        },
        "feature_names": model.feature_names,
        "means": model.means,
        "scales": model.scales,
        "weights": model.weights,
        "intercept": model.intercept,
        "ridge_lambda": model.ridge_lambda,
        "child_top_k": model.child_top_k,
        "aggregation": model.aggregation,
        "target_used_for_fitting": model.target_used_for_fitting,
        "target_used_for_scoring": model.target_used_for_scoring,
    }


def compute_model_digest(model):
    return hashlib.sha256(canonical_json(model_payload(model))).hexdigest()


def model_from_artifact(artifact):
    if artifact.get("format") != FORMAT:
        raise ValueError("unknown local-section marking artifact")
    data = artifact["model"]
    schema = FrozenLocalSectionSchema(
        tuple(data["schema"]["species"]), data["schema"]["reach"],
        data["schema"]["radial_bin_width"],
        data["schema"]["nearest_per_species"],
        tuple(data["schema"]["source_channel_names"]),
        data["schema"]["site_key_decimals"])
    model = FrozenLocalSectionChildMarking(
        schema, tuple(data["feature_names"]), tuple(data["means"]),
        tuple(data["scales"]), tuple(data["weights"]), data["intercept"],
        data["ridge_lambda"], data["child_top_k"], data["aggregation"],
        artifact["model_digest"], data["target_used_for_fitting"],
        data["target_used_for_scoring"])
    if (model.feature_names != feature_names(schema) or
            len(model.means) != len(model.feature_names) or
            len(model.scales) != len(model.feature_names) or
            len(model.weights) != len(model.feature_names) or
            any(scale <= 0 or not math.isfinite(scale)
                for scale in model.scales) or
            compute_model_digest(model) != model.model_digest):
        raise AssertionError("local-section marking artifact drift")
    return model


def load_default_marking(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("local-section marking fixture drift")
    artifact = json.loads(gzip.decompress(raw))
    computed_artifact_digest = hashlib.sha256(canonical_json({
        key: value for key, value in artifact.items()
        if key != "artifact_digest"
    })).hexdigest()
    if (artifact.get("artifact_digest") != computed_artifact_digest or
            (EXPECTED_ARTIFACT_DIGEST and
             computed_artifact_digest != EXPECTED_ARTIFACT_DIGEST)):
        raise AssertionError("local-section marking audit digest drift")
    model = model_from_artifact(artifact)
    if EXPECTED_MODEL_DIGEST and model.model_digest != EXPECTED_MODEL_DIGEST:
        raise AssertionError("local-section marking model digest drift")
    return model, artifact


__all__ = [
    "FrozenLocalSectionChildMarking", "FrozenLocalSectionSchema",
    "compute_model_digest", "feature_names", "load_default_marking",
    "local_section_features", "model_payload", "rank_child_states",
    "score_feature_vector", "select_child_ids"]
