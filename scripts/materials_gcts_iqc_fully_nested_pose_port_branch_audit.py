#!/usr/bin/env python3
"""Fully nested IQC audit for channel-conditioned branch geometry."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from materials_gcts_on_policy_branch_aggregation import (
    branch_examples_digest, fit_group_sealed_on_policy_values)
from materials_gcts_pose_port_branch_features import (
    pose_port_branch_feature_names)
from materials_gcts_recurrent_branch_value import RecurrentBranchExample, _fit
from materials_gcts_recurrent_branch_value_heads import DepthBranchExample


FIXTURE = (Path(__file__).parent /
           "fixtures/iqc_fully_nested_pose_port_branch.json")


@dataclass(frozen=True)
class IQCFullyNestedPosePortBranchReport:
    groups: int
    folds: int
    broad_examples: int
    on_policy_examples: int
    positive_broad_examples: int
    positive_on_policy_examples: int
    conflicting_descriptor_groups: int
    feature_count: int
    pose_port_channels_per_action: int
    maximum_actions: int
    base_selected_exact: int
    base_terminal_supply: int
    colored_geometry_selected_exact: int
    colored_geometry_terminal_supply: int
    pose_port_only_selected_exact: int
    pose_port_only_terminal_supply: int
    coupled_selected_exact: int
    coupled_terminal_supply: int
    aggregated_selected_exact: int
    aggregated_terminal_supply: int
    aggregated_selected_correct_moves: int
    raw_pose_port_channels_improve_base: bool
    colored_geometry_improves_base: bool
    coupled_representation_improves_base: bool
    on_policy_aggregation_improves_coupled_model: bool
    broad_upstream_pose_port_fully_nested: bool
    on_policy_upstream_pose_port_fully_nested: bool
    scientific_gate_passed: bool
    fresh_confirmation_authorized: bool
    corpus_digest: str
    closed_loop_candidate_digest: str
    target_used: bool


def _rows(raw) -> tuple[DepthBranchExample, ...]:
    return tuple(DepthBranchExample(
        int(row["group"]), int(row["depth"]), tuple(row["features"]),
        tuple(row["action_colors"]), bool(row["successful"])) for row in raw)


def _heads_digest(rows, names, indices, neighbors_by_depth, colors):
    heads = []
    for depth, neighbors in neighbors_by_depth:
        stage = tuple(RecurrentBranchExample(
            row.group, tuple(row.features[index] for index in indices),
            row.action_colors, row.successful)
            for row in rows if row.depth == depth)
        heads.append((depth, _fit(
            stage, tuple(names[index] for index in indices), colors,
            neighbors, .5)))
    return hashlib.sha256(repr(tuple(heads)).encode()).hexdigest()


def evaluate(path: Path = FIXTURE) -> IQCFullyNestedPosePortBranchReport:
    data = json.loads(path.read_text())
    if data["format"] != "iqc-fully-nested-pose-port-branch-v1":
        raise AssertionError("unexpected fully nested branch fixture")
    names = tuple(data["feature_names"])
    colors = tuple(data["color_keys"])
    expected_names = pose_port_branch_feature_names(
        names[:10], colors, maximum_actions=3, channel_count=5)
    if names != expected_names:
        raise AssertionError("pose-port branch feature schema changed")
    variants = {
        "base": tuple(range(10)),
        "base_colored_geometry": tuple(range(16)),
        "base_pose_port_channels": tuple(range(10)) + tuple(range(16, 31)),
        "all": tuple(range(31)),
    }
    neighbors = tuple(tuple(row) for row in data["neighbors_by_depth"])
    digest_parts = []
    broad_count = policy_count = broad_positive = policy_positive = conflicts = 0
    for fold in data["folds"]:
        broad = _rows(fold["broad_examples"])
        policy = _rows(fold["on_policy_examples"])
        broad_digest = branch_examples_digest(broad)
        policy_digest = branch_examples_digest(policy)
        if (broad_digest != fold["broad_digest"] or
                policy_digest != fold["on_policy_digest"]):
            raise AssertionError("fully nested branch corpus changed")
        digest_parts.append((broad_digest, policy_digest))
        for name, indices in variants.items():
            if _heads_digest(broad, names, indices, neighbors, colors) != \
                    fold["initial_model_digests"][name]:
                raise AssertionError("initial feature ablation changed")
        _model, audit = fit_group_sealed_on_policy_values(
            broad, policy, heldout_groups=tuple(fold["heldout_groups"]),
            feature_names=names, color_keys=colors,
            neighbors_by_depth=neighbors, beta_prior=float(data["beta_prior"]))
        if (audit.model_digest != fold["aggregated_all_model_digest"] or
                audit.training_example_digest !=
                fold["aggregated_training_digest"] or
                audit.merged_examples != fold["aggregated_merged_examples"] or
                audit.conflicting_descriptor_groups !=
                fold["aggregated_conflicting_descriptors"] or
                audit.heldout_seen_during_fit or audit.target_used):
            raise AssertionError("fully nested aggregation changed")
        broad_count += len(broad)
        policy_count += len(policy)
        broad_positive += sum(row.successful for row in broad)
        policy_positive += sum(row.successful for row in policy)
        conflicts += audit.conflicting_descriptor_groups
    corpus_digest = hashlib.sha256(
        repr(tuple(digest_parts)).encode()).hexdigest()
    if corpus_digest != data["corpus_digest"]:
        raise AssertionError("fully nested combined corpus changed")

    ablation = data["feature_ablations"]
    closed = data["closed_loop"]
    initial = closed["initial"]
    aggregated = closed["aggregated"]
    groups = int(initial["groups"])
    gate = data["scientific_gate"]
    supply_ok = (aggregated["terminal_supply"] / groups >=
                 gate["minimum_terminal_supply_fraction"])
    selection_ok = (aggregated["selected_exact"] / groups >=
                    gate["minimum_selected_exact_fraction"])
    aggregation_improves = (aggregated["selected_exact"] >
                            initial["selected_exact"])
    combined_gate = (supply_ok and selection_ok and
                     (aggregation_improves or not
                      gate["require_aggregation_improvement"]))
    return IQCFullyNestedPosePortBranchReport(
        groups=groups,
        folds=len(data["folds"]),
        broad_examples=broad_count,
        on_policy_examples=policy_count,
        positive_broad_examples=broad_positive,
        positive_on_policy_examples=policy_positive,
        conflicting_descriptor_groups=conflicts,
        feature_count=len(names),
        pose_port_channels_per_action=5,
        maximum_actions=3,
        base_selected_exact=ablation["base"]["selected_exact"],
        base_terminal_supply=ablation["base"]["terminal_supply"],
        colored_geometry_selected_exact=
            ablation["base_colored_geometry"]["selected_exact"],
        colored_geometry_terminal_supply=
            ablation["base_colored_geometry"]["terminal_supply"],
        pose_port_only_selected_exact=
            ablation["base_pose_port_channels"]["selected_exact"],
        pose_port_only_terminal_supply=
            ablation["base_pose_port_channels"]["terminal_supply"],
        coupled_selected_exact=ablation["all"]["selected_exact"],
        coupled_terminal_supply=ablation["all"]["terminal_supply"],
        aggregated_selected_exact=aggregated["selected_exact"],
        aggregated_terminal_supply=aggregated["terminal_supply"],
        aggregated_selected_correct_moves=aggregated["selected_correct"],
        raw_pose_port_channels_improve_base=(
            ablation["base_pose_port_channels"]["selected_exact"] >
            ablation["base"]["selected_exact"]),
        colored_geometry_improves_base=(
            ablation["base_colored_geometry"]["selected_exact"] >
            ablation["base"]["selected_exact"]),
        coupled_representation_improves_base=(
            ablation["all"]["selected_exact"] >
            ablation["base"]["selected_exact"]),
        on_policy_aggregation_improves_coupled_model=aggregation_improves,
        broad_upstream_pose_port_fully_nested=bool(
            data["broad_upstream_pose_port_fully_nested"]),
        on_policy_upstream_pose_port_fully_nested=bool(
            data["on_policy_upstream_pose_port_fully_nested"]),
        scientific_gate_passed=combined_gate,
        fresh_confirmation_authorized=combined_gate,
        corpus_digest=corpus_digest,
        closed_loop_candidate_digest=closed["candidate_digest"],
        target_used=bool(data["target_used"]))


if __name__ == "__main__":
    print(evaluate())
