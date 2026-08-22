#!/usr/bin/env python3
"""Frozen fair schedule for expensive IQC third-frontier prefix expansion.

The schedule never changes candidate geometry.  For each of the eight retained
first-block parents it expands a small joint-action tier, followed by a base
marking fallback tier.  The per-parent quota prevents a high-scoring parent
from consuming the whole compute budget and is therefore an antichain-aware
tree-search policy rather than a global greedy beam.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from materials_gcts_joint_child_action_marking import (
    load_default_marking, rank_joint_children)


FORMAT = "materials-gcts-joint-prefix-schedule-v1"
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_joint_prefix_schedule_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = (
    "d0fc14e912c268923a2a55b6cb0a6a9f8181805bd0596f718599c8e699cb0195")
EXPECTED_ARTIFACT_DIGEST = (
    "4e5c57d6a2ad15a374f9f973869f693e84a63c4e38cba829907054b74d895fe7")
BASE_CHANNEL_INDEX = 0


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


@dataclass(frozen=True)
class FrozenJointPrefixSchedule:
    parent_width: int
    joint_top_k: int
    base_top_k: int
    base_channel_index: int
    maximum_prefixes: int
    artifact_digest: str
    target_used_for_selection: bool
    target_used_for_execution: bool = False


def _branch_value(branch, name):
    return branch[name] if isinstance(branch, dict) else getattr(branch, name)


def schedule_prefixes(*, schedule, seed_positions, seed_species, branches):
    """Freeze selected and deferred child prefixes for every parent.

    The return value exposes the entire immutable queue digest, while only the
    selected prefix rows are authorized for third-frontier expansion.
    """
    model, marking_artifact = load_default_marking()
    branches = tuple(sorted(branches, key=lambda row: int(
        _branch_value(row, "first_rank"))))
    if len(branches) != schedule.parent_width:
        raise ValueError("joint prefix schedule parent-width drift")
    selected_rows = []
    deferred_rows = []
    tier_counts = {"joint": 0, "base-fallback": 0}
    complete_queue = []
    for branch in branches:
        parent = int(_branch_value(branch, "first_rank"))
        actions = tuple(_branch_value(branch, "second_actions"))
        channel_scores = tuple(_branch_value(
            branch, "second_channel_scores"))
        if len(actions) != len(channel_scores):
            raise ValueError("child action/score count drift")
        joint = rank_joint_children(
            model=model, seed_positions=seed_positions,
            seed_species=seed_species, branch=branch)
        joint_rank = {child: rank for rank, (child, _score)
                      in enumerate(joint, 1)}
        joint_score = dict(joint)
        base = tuple(sorted(range(len(actions)), key=lambda child: (
            -float(channel_scores[child][schedule.base_channel_index]),
            child)))
        base_rank = {child: rank for rank, child in enumerate(base, 1)}
        selected = []
        sources = {}
        for child, _score in joint[:schedule.joint_top_k]:
            selected.append(child)
            sources.setdefault(child, []).append("joint")
        for child in base[:schedule.base_top_k]:
            if child not in selected:
                selected.append(child)
            sources.setdefault(child, []).append("base-fallback")
        selected_set = set(selected)
        # A deterministic complete queue makes the unexpanded search space
        # auditable without evaluating any deferred third-frontier subtree.
        all_children = tuple(sorted(range(len(actions)), key=lambda child: (
            0 if child in selected_set else 1,
            selected.index(child) if child in selected_set else
            min(joint_rank[child], base_rank[child]),
            joint_rank[child], base_rank[child], child)))
        for child in all_children:
            row = (
                parent, int(child), tuple(sources.get(child, ("deferred",))),
                int(joint_rank[child]), float(joint_score[child]),
                int(base_rank[child]),
                float(channel_scores[child][schedule.base_channel_index]))
            complete_queue.append(row)
            if child in selected_set:
                selected_rows.append(row)
                for source in sources[child]:
                    tier_counts[source] += 1
            else:
                deferred_rows.append(row)
    if (len(selected_rows) > schedule.maximum_prefixes or
            any(row[1] < 0 for row in selected_rows) or
            schedule.target_used_for_execution or model.target_used_for_scoring):
        raise AssertionError("invalid target-free prefix schedule")
    queue_digest = hashlib.sha256(repr(tuple(complete_queue)).encode()).hexdigest()
    selected_digest = hashlib.sha256(repr(tuple(selected_rows)).encode()).hexdigest()
    return {
        "model": model,
        "marking_artifact": marking_artifact,
        "selected_rows": tuple(selected_rows),
        "deferred_rows": tuple(deferred_rows),
        "complete_queue_digest": queue_digest,
        "selected_prefix_digest": selected_digest,
        "tier_counts": tuple(sorted(tier_counts.items())),
    }


def load_default_schedule(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("joint prefix schedule fixture byte drift")
    artifact = json.loads(gzip.decompress(raw))
    if artifact.get("format") != FORMAT:
        raise ValueError("unknown joint prefix schedule artifact")
    computed = hashlib.sha256(canonical_json({
        key: value for key, value in artifact.items()
        if key != "artifact_digest"})).hexdigest()
    if (computed != artifact.get("artifact_digest") or
            (EXPECTED_ARTIFACT_DIGEST and
             computed != EXPECTED_ARTIFACT_DIGEST)):
        raise AssertionError("joint prefix schedule artifact drift")
    data = artifact["schedule"]
    schedule = FrozenJointPrefixSchedule(
        int(data["parent_width"]), int(data["joint_top_k"]),
        int(data["base_top_k"]), int(data["base_channel_index"]),
        int(data["maximum_prefixes"]), computed,
        bool(data["target_used_for_selection"]),
        bool(data["target_used_for_execution"]))
    if (min(schedule.parent_width, schedule.joint_top_k,
            schedule.base_top_k) < 1 or
            schedule.maximum_prefixes != schedule.parent_width * (
                schedule.joint_top_k + schedule.base_top_k) or
            not schedule.target_used_for_selection or
            schedule.target_used_for_execution):
        raise AssertionError("invalid frozen joint prefix schedule")
    return schedule, artifact


__all__ = [
    "FrozenJointPrefixSchedule", "load_default_schedule",
    "schedule_prefixes"]
