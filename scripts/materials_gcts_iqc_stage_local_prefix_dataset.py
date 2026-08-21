#!/usr/bin/env python3
"""Build a consumed-development corpus for stage-local IQC marking.

The repaired ``12 -> 4 -> 8`` tree is enumerated from each colored R9 seed.
Every prefix receives only target-free branch, local-section, and frontier
features.  All twenty geometry receipts freeze before local R14.56 targets are
constructed and joined.  This is consumed development evidence, not a fresh
confirmation.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import math
import os
import pickle
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import (
    _subset_proposals, _without_known_sites)
from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, _local_section, action_key, branch_features,
    load_default_runtime)
from materials_gcts_iqc_obligation_expanded_dataset import _digest, _site_key
from materials_gcts_iqc_obligation_expanded_preregistration import (
    DEVELOPMENT_CENTERS, EXPECTED_MANIFEST_DIGEST, SEED_RADIUS, TARGET_RADIUS,
    audit as source_preregistration_audit)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_post_self_fed_port_discharge_dataset import (
    _frontier_summary)
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import CLUSTER_EDGES
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_pose_port_state_marking import score_pose_port_state
from materials_gcts_recursive_connections import (
    local_cluster_types, propose_with_recursive_marking)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_stage_local_prefix_development_v1.json.gz"
SCHEDULE = (12, 4, 8)
EXPECTED_FIXTURE_SHA256 = \
    "e708ab541fb2db8404145afdb58aa20612a31e3915140a5d7ff40cba496a914f"
EXPECTED_DATASET_DIGEST = \
    "5bab03312f0c2fd52e746bb7a2218097a7d65aaed4eb77bbf23a858646bfc961"


def _seed_frontier(runtime, source, radius=TARGET_RADIUS):
    """Enumerate only from the supplied seed inside the public outer ball."""
    proposals = propose_with_recursive_marking(
        runtime["connection"], source.seed_positions,
        local_cluster_types(
            source.seed_positions, source.seed_species, CLUSTER_EDGES),
        HIDDEN_UNIT)
    proposals = _without_known_sites(proposals, source.seed_positions)
    return _subset_proposals(proposals, (
        point for point in proposals.votes
        if math.dist(point, source.group) <= radius + 1e-8))


def _parent_keys(actions):
    if len(actions) <= 1:
        return ((),)
    return tuple(sorted((action_key(subset)
                         for subset in itertools.combinations(
                             actions, len(actions) - 1)), key=repr))


def _geometry_group(payload):
    group, center, seed_positions, seed_species = payload
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=tuple(map(float, center)),
        seed_positions=tuple(tuple(map(float, point))
                             for point in seed_positions),
        seed_species=tuple(map(str, seed_species)))
    frontier = _seed_frontier(runtime, source)
    states = (FusionSearchState(
        source.seed_positions, source.seed_species, frontier,
        (), (), (), 0., ()),)
    counts, stages = [], []
    for depth, reach in enumerate(SCHEDULE, start=1):
        children, attempts = {}, 0
        for state in states:
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
                -score_pose_port_state(
                    runtime["state_model"], descriptors[point]),
                -state.proposals.votes[point], point)))[:reach]
            attempts += len(ordered)
            for point in ordered:
                candidate = _child(
                    source, runtime["connection"], runtime["state_model"],
                    state, point, descriptors[point], TARGET_RADIUS)
                key = action_key(candidate.actions)
                prior = children.get(key)
                if prior is None or (candidate.cumulative, candidate.actions) > \
                        (prior.cumulative, prior.actions):
                    children[key] = candidate
        states = tuple(sorted(children.values(),
                              key=lambda row: action_key(row.actions)))
        counts.append(len(states))
        rows = []
        for state in states:
            summary = _frontier_summary(state.proposals)
            features = tuple(branch_features(state)) + \
                tuple(_local_section(state)) + tuple(map(float, summary))
            rows.append({
                "depth": depth,
                "action_key": action_key(state.actions),
                "parent_keys": _parent_keys(state.actions),
                "features": features,
                "feature_digest": hashlib.sha256(
                    repr(features).encode()).hexdigest(),
            })
        stages.append({
            "depth": depth, "reach": reach, "proposal_checks": attempts,
            "rows": tuple(rows),
        })
    body = {
        "group": int(group), "center": tuple(map(float, center)),
        "seed_atoms": len(source.seed_positions),
        "candidate_counts_by_depth": tuple(counts),
        "stages": tuple(stages),
        "target_received_by_worker": False,
        "target_used_for_features_or_tree": False,
    }
    return {**body, "geometry_digest_before_target": _digest(body)}


def _build_geometry(seeds, workers):
    payloads = tuple((group, center, seed.positions, seed.species)
                     for group, (center, seed) in enumerate(zip(
                         DEVELOPMENT_CENTERS, seeds)))
    if workers <= 1:
        return tuple(_geometry_group(payload) for payload in payloads)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", "")
    results = [None] * len(payloads)
    with tempfile.TemporaryDirectory(prefix="gcts-stage-local-prefix-") as tmp:
        directory = Path(tmp)
        active, launched = [], 0
        while launched < len(payloads) or active:
            while launched < len(payloads) and len(active) < workers:
                input_path = directory / f"input-{launched}.pickle"
                output_path = directory / f"output-{launched}.pickle"
                input_path.write_bytes(pickle.dumps(payloads[launched]))
                process = subprocess.Popen(
                    [sys.executable, "-B", str(Path(__file__).resolve()),
                     "--group-pickle", str(input_path), str(output_path)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, env=environment)
                active.append((launched, process, output_path))
                launched += 1
            index, process, output_path = active.pop(0)
            output, error = process.communicate()
            if process.returncode:
                raise RuntimeError(
                    f"stage-local worker {index} failed\n{output}{error}")
            results[index] = pickle.loads(output_path.read_bytes())
    return tuple(results)


def build_dataset(*, workers=1):
    protocol = source_preregistration_audit()
    if protocol.manifest_digest != EXPECTED_MANIFEST_DIGEST:
        raise AssertionError("source development preregistration drift")
    seeds = tuple(oracle_crop_fast(center, SEED_RADIUS)[0]
                  for center in DEVELOPMENT_CENTERS)
    if any(not seed.positions for seed in seeds):
        raise AssertionError("empty stage-local seed")
    geometry = _build_geometry(seeds, workers)
    geometry_digest = _digest(tuple(
        row["geometry_digest_before_target"] for row in geometry))

    groups = []
    for frozen, center in zip(geometry, DEVELOPMENT_CENTERS):
        target, _ = oracle_crop_fast(center, TARGET_RADIUS)
        truth = {_site_key(point): str(color) for point, color in zip(
            target.positions, target.species)}
        stages = []
        for stage in frozen["stages"]:
            rows = []
            for row in stage["rows"]:
                correct = tuple(
                    truth.get(_site_key(point)) == str(color)
                    for point, color in row["action_key"])
                rows.append({
                    **row, "site_correct": correct,
                    "correct_sites": sum(correct),
                    "viable_prefix": all(correct),
                })
            stages.append({**stage, "rows": tuple(rows)})
        groups.append({
            **frozen, "target_atoms": len(target.positions),
            "stages": tuple(stages),
            "labels_joined_after_all_geometry_froze": True,
        })
    body = {
        "schema_version": 1,
        "source_preregistration_digest": protocol.manifest_digest,
        "consumed_development_groups": len(groups),
        "schedule": SCHEDULE,
        "geometry_digest_before_any_target": geometry_digest,
        "groups": tuple(groups),
        "targets_used_for_features_tree_or_branch_choice": False,
        "all_labels_joined_after_all_geometry_froze": True,
        "candidate_geometry_changed": False,
        "fresh_confirmation_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "dataset_digest": _digest(body)}


def validate_dataset(row):
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (_digest(body) != digest or body["schedule"] != list(SCHEDULE) or
            body["consumed_development_groups"] != len(DEVELOPMENT_CENTERS) or
            body["targets_used_for_features_tree_or_branch_choice"] or
            not body["all_labels_joined_after_all_geometry_froze"] or
            body["candidate_geometry_changed"] or
            body["fresh_confirmation_claimed"] or
            body["autonomous_growth_claimed"] or
            body["stationary_or_exponential_claimed"] or any(
                group["target_received_by_worker"] or
                group["target_used_for_features_or_tree"] or
                not group["labels_joined_after_all_geometry_froze"]
                for group in body["groups"])):
        raise AssertionError("stage-local prefix dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("unexpected stage-local dataset digest")
    return row


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("stage-local fixture byte drift")
    return validate_dataset(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int,
                        default=max(1, min(4, os.cpu_count() or 1)))
    parser.add_argument("--group-pickle", nargs=2,
                        metavar=("INPUT", "OUTPUT"))
    args = parser.parse_args()
    if args.group_pickle:
        input_path, output_path = map(Path, args.group_pickle)
        output_path.write_bytes(pickle.dumps(
            _geometry_group(pickle.loads(input_path.read_bytes()))))
        return
    if args.write and DEFAULT_FIXTURE.exists():
        raise RuntimeError("stage-local fixture already exists")
    row = build_dataset(workers=max(1, args.workers))
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
