#!/usr/bin/env python3
"""Explicit JSON artifact for the frozen IQC terminal-fusion runtime.

The original development experiment used process-local pickle checkpoints.
This module migrates the selected policy into inert, schema-checked data.  No
Python object code, atom coordinates, held-out labels, or target sites are
stored in the runtime artifact.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Mapping

from materials_gcts_equivariant_port_fusion_value import (
    FrozenEquivariantPortFusionValue)
from materials_gcts_grouped_irregular_vocabulary import (
    GroupedIrregularVocabulary)
from materials_gcts_irregular_supports import (
    FrozenSupportPrototype, FrozenSupportVocabulary)
from materials_gcts_learned_equivariant_port_value import (
    FrozenLearnedEquivariantPortValue, LearnedEquivariantPortSpec)
from materials_gcts_portfolio_terminal_value import (
    FrozenPortfolioTerminalValue, TerminalRepresentation)
from materials_gcts_pose_port_state_serialization import (
    pose_port_state_marking_from_payload, pose_port_state_marking_payload)
from materials_gcts_recurrent_branch_value import FrozenRecurrentBranchValue
from materials_gcts_recursive_connections import (
    LocalClusterType, RecursiveConnectionMarking, RecursiveConnectionState,
    StateEvidence)


FORMAT = "gcts-iqc-frozen-terminal-fusion-v1"


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def payload_digest(value: Mapping[str, Any]) -> str:
    body = dict(value)
    body.pop("artifact_digest", None)
    return hashlib.sha256(canonical_json(body)).hexdigest()


def _tree(value: Any):
    if isinstance(value, tuple):
        return {"tuple": [_tree(item) for item in value]}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"unsupported frozen value {type(value)!r}")


def _untree(value: Any):
    if isinstance(value, dict) and set(value) == {"tuple"}:
        return tuple(_untree(item) for item in value["tuple"])
    if isinstance(value, dict) or isinstance(value, list):
        raise ValueError("untyped container in frozen value")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise ValueError("invalid frozen scalar")


def branch_value_payload(model: FrozenRecurrentBranchValue) -> dict[str, Any]:
    return {
        "feature_names": list(model.feature_names),
        "color_keys": list(model.color_keys),
        "means": list(model.means),
        "scales": list(model.scales),
        "normalized_examples": [[list(row), label]
                                for row, label in model.normalized_examples],
        "neighbors": model.neighbors,
        "beta_prior": model.beta_prior,
        "target_used": model.target_used,
    }


def branch_value_from_payload(payload: Mapping[str, Any]):
    model = FrozenRecurrentBranchValue(
        tuple(map(str, payload["feature_names"])),
        tuple(map(str, payload["color_keys"])),
        tuple(map(float, payload["means"])),
        tuple(map(float, payload["scales"])),
        tuple((tuple(map(float, row)), bool(label))
              for row, label in payload["normalized_examples"]),
        int(payload["neighbors"]), float(payload["beta_prior"]),
        bool(payload.get("target_used", False)))
    if (not model.feature_names or len(model.means) != len(model.scales)
            or any(len(row) != len(model.means)
                   for row, _label in model.normalized_examples)
            or model.target_used):
        raise ValueError("invalid frozen branch-value payload")
    return model


def connection_payload(model: RecursiveConnectionMarking) -> dict[str, Any]:
    prototypes = tuple(sorted(model.prototypes))
    prototype_index = {prototype: index
                       for index, prototype in enumerate(prototypes)}

    def state(row):
        return [prototype_index[row.parent_type],
                prototype_index[row.source_type],
                row.normalized_separation_bin]

    return {
        "scale": model.scale,
        "separation_bin_width": model.separation_bin_width,
        "prototypes": [[row.color_key, list(row.cumulative_neighbor_counts)]
                       for row in prototypes],
        "evidence": [[state(key), value.positive, value.total]
                     for key, value in sorted(model.evidence.items())],
        "accepted_states": [state(row)
                            for row in sorted(model.accepted_states)],
        "minimum_positive_support": model.minimum_positive_support,
        "minimum_purity": model.minimum_purity,
        "target_color_evidence": [[state(key), sorted(value.items())]
                                  for key, value in sorted(
                                      model.target_color_evidence.items())],
    }


def connection_from_payload(payload: Mapping[str, Any]):
    prototypes = tuple(LocalClusterType(
        str(color), tuple(map(int, counts)))
        for color, counts in payload["prototypes"])

    def state(row):
        parent, source, separation = map(int, row)
        if not 0 <= parent < len(prototypes) or not 0 <= source < len(prototypes):
            raise ValueError("connection prototype index out of range")
        return RecursiveConnectionState(
            prototypes[parent], prototypes[source], separation)

    evidence = {state(row): StateEvidence(int(positive), int(total))
                for row, positive, total in payload["evidence"]}
    accepted = frozenset(state(row) for row in payload["accepted_states"])
    colors = {state(row): Counter({str(color): int(count)
                                   for color, count in counts})
              for row, counts in payload["target_color_evidence"]}
    model = RecursiveConnectionMarking(
        float(payload["scale"]), float(payload["separation_bin_width"]),
        prototypes, evidence, accepted,
        int(payload["minimum_positive_support"]),
        float(payload["minimum_purity"]), colors)
    if not model.accepted_states or not model.prototypes:
        raise ValueError("empty frozen recursive connection")
    return model


def grouped_vocabulary_payload(model: GroupedIrregularVocabulary):
    vocabulary = model.vocabulary
    return {
        "prototypes": [{
            "type_id": row.type_id,
            "hierarchy_level": row.hierarchy_level,
            "species": [_tree(value) for value in row.species],
            "quantized_distances": [list(values)
                                    for values in row.quantized_distances],
            "signature": _tree(row.signature),
        } for row in vocabulary.prototypes],
        "distance_tolerance": vocabulary.distance_tolerance,
        "minimum_neighbors": vocabulary.minimum_neighbors,
        "maximum_neighbors": vocabulary.maximum_neighbors,
        "shell_gap": vocabulary.shell_gap,
        "maximum_merged_size": vocabulary.maximum_merged_size,
        "training_group_support": list(model.training_group_support),
        "fitted_group_count": model.fitted_group_count,
        "input_prototype_count": model.input_prototype_count,
        "recurrent_prototype_count": model.recurrent_prototype_count,
        "repeated_coverage_by_group": list(model.repeated_coverage_by_group),
        "lattice_coordinates_used": model.lattice_coordinates_used,
        "target_used": model.target_used,
    }


def grouped_vocabulary_from_payload(payload: Mapping[str, Any]):
    prototypes = tuple(FrozenSupportPrototype(
        int(row["type_id"]), int(row["hierarchy_level"]),
        tuple(_untree(value) for value in row["species"]),
        tuple(tuple(map(int, values))
              for values in row["quantized_distances"]),
        _untree(row["signature"])) for row in payload["prototypes"])
    vocabulary = FrozenSupportVocabulary(
        prototypes, float(payload["distance_tolerance"]),
        int(payload["minimum_neighbors"]),
        int(payload["maximum_neighbors"]), float(payload["shell_gap"]),
        int(payload["maximum_merged_size"]))
    model = GroupedIrregularVocabulary(
        vocabulary, tuple(map(int, payload["training_group_support"])),
        int(payload["fitted_group_count"]),
        int(payload["input_prototype_count"]),
        int(payload["recurrent_prototype_count"]),
        tuple(map(float, payload["repeated_coverage_by_group"])),
        bool(payload.get("lattice_coordinates_used", False)),
        bool(payload.get("target_used", False)))
    if (model.target_used or len(model.training_group_support) !=
            len(model.vocabulary.prototypes)):
        raise ValueError("invalid grouped vocabulary payload")
    return model


def graph_value_payload(model: FrozenLearnedEquivariantPortValue):
    return {
        "spec": {
            "interaction_order": model.spec.interaction_order,
            "support_type_weight": model.spec.support_type_weight,
            "ridge": model.spec.ridge,
            "minimum_feature_groups": model.spec.minimum_feature_groups,
            "steps": model.spec.steps,
            "learning_rate": model.spec.learning_rate,
            "objective": model.spec.objective,
        },
        "feature_keys": [_tree(value) for value in model.feature_keys],
        "scales": list(model.scales),
        "weights": list(model.weights),
        "intercept": model.intercept,
        "training_groups": model.training_groups,
        "training_examples": model.training_examples,
        "positive_examples": model.positive_examples,
        "model_digest": model.model_digest,
        "target_used": model.target_used,
    }


def graph_value_from_payload(payload: Mapping[str, Any]):
    row = payload["spec"]
    spec = LearnedEquivariantPortSpec(
        int(row["interaction_order"]), float(row["support_type_weight"]),
        float(row["ridge"]), int(row["minimum_feature_groups"]),
        int(row["steps"]), float(row["learning_rate"]), str(row["objective"]))
    model = FrozenLearnedEquivariantPortValue(
        spec, tuple(_untree(value) for value in payload["feature_keys"]),
        tuple(map(float, payload["scales"])),
        tuple(map(float, payload["weights"])), float(payload["intercept"]),
        int(payload["training_groups"]), int(payload["training_examples"]),
        int(payload["positive_examples"]), str(payload["model_digest"]),
        bool(payload.get("target_used", False)))
    if (model.target_used or len(model.feature_keys) != len(model.scales)
            or len(model.scales) != len(model.weights)):
        raise ValueError("invalid frozen graph-value payload")
    return model


def fusion_value_payload(model: FrozenEquivariantPortFusionValue):
    return {
        "scalar": {
            "representation": {
                "name": model.scalar.representation.name,
                "feature_indices": list(
                    model.scalar.representation.feature_indices),
            },
            "value": branch_value_payload(model.scalar.value),
        },
        "graph": graph_value_payload(model.graph),
        "graph_rank_weight": model.graph_rank_weight,
        "feature_names": list(model.feature_names),
        "color_keys": list(model.color_keys),
        "training_groups": model.training_groups,
        "model_digest": model.model_digest,
        "target_used": model.target_used,
    }


def fusion_value_from_payload(payload: Mapping[str, Any]):
    scalar = payload["scalar"]
    representation = scalar["representation"]
    model = FrozenEquivariantPortFusionValue(
        FrozenPortfolioTerminalValue(
            TerminalRepresentation(
                str(representation["name"]),
                tuple(map(int, representation["feature_indices"]))),
            branch_value_from_payload(scalar["value"])),
        graph_value_from_payload(payload["graph"]),
        float(payload["graph_rank_weight"]),
        tuple(map(str, payload["feature_names"])),
        tuple(map(str, payload["color_keys"])),
        int(payload["training_groups"]), str(payload["model_digest"]),
        bool(payload.get("target_used", False)))
    if model.target_used:
        raise ValueError("target-tainted frozen fusion model")
    return model


def runtime_payload(*, source_commit, connection, grouped_vocabulary,
                    state_model, branch_models, fusion_model, provenance):
    payload = {
        "format": FORMAT,
        "source_commit": str(source_commit),
        "connection": connection_payload(connection),
        "grouped_vocabulary": grouped_vocabulary_payload(grouped_vocabulary),
        "state_model": pose_port_state_marking_payload(state_model),
        "branch_models": [{
            "variant": str(name),
            "heads": [branch_value_payload(head) for head in heads],
        } for name, heads in sorted(branch_models.items())],
        "fusion_model": fusion_value_payload(fusion_model),
        "provenance": provenance,
        "target_used": False,
    }
    payload["artifact_digest"] = payload_digest(payload)
    return payload


def runtime_from_payload(payload: Mapping[str, Any]):
    if (payload.get("format") != FORMAT
            or payload.get("target_used") is not False
            or payload.get("artifact_digest") != payload_digest(payload)):
        raise ValueError("invalid or mutated frozen fusion artifact")
    branches = {str(row["variant"]): tuple(
        branch_value_from_payload(head) for head in row["heads"])
        for row in payload["branch_models"]}
    if len(branches) != len(payload["branch_models"]):
        raise ValueError("duplicate frozen branch variant")
    return {
        "source_commit": str(payload["source_commit"]),
        "connection": connection_from_payload(payload["connection"]),
        "grouped_vocabulary": grouped_vocabulary_from_payload(
            payload["grouped_vocabulary"]),
        "state_model": pose_port_state_marking_from_payload(
            payload["state_model"]),
        "branch_models": branches,
        "fusion_model": fusion_value_from_payload(payload["fusion_model"]),
        "provenance": payload["provenance"],
        "artifact_digest": str(payload["artifact_digest"]),
    }
