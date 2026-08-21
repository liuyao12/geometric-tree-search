#!/usr/bin/env python3
"""Build target-free connection rollouts for the stage-local IQC portfolio.

Each heldout nucleus' ``4 -> 8 -> 8`` shortlist is produced by models whose
receipts exclude that nucleus.  Workers receive only its colored R9 seed and
eight frozen action keys, reconstruct each terminal under a valid action
permutation, and roll its connection frontier for sixteen steps.  Labels from
the already-consumed development fixture are joined only after every rollout
receipt freezes.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import os
import pickle
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, action_key, load_default_runtime)
from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_obligation_expanded_preregistration import (
    DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_stage_local_prefix_dataset import (
    _seed_frontier, load_default_dataset as load_prefix_dataset)
from materials_gcts_iqc_stage_local_prefix_marking_audit import (
    _flatten, _freeze_receipts, _real_labels)
from materials_gcts_iqc_stage_local_site_selector_audit import _shortlist
from materials_gcts_iqc_wide_typed_port_discharge_dataset import _rollout
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_stage_local_rollout_development_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "1e10cba6af91c8d180fd8af28dc4f911cf8025e1a51dbece2116415d9f0c9e1d"
EXPECTED_DATASET_DIGEST = \
    "def1a139ea74b4492cd1c5610bd970a0061b8f2132f05b47fa2d2e976ec5a720"


def _reconstruct(source, runtime, actions):
    frontier = _seed_frontier(runtime, source, TARGET_RADIUS)
    for permutation in itertools.permutations(actions):
        state = FusionSearchState(
            source.seed_positions, source.seed_species, frontier,
            (), (), (), 0., ())
        valid = True
        for point, color in permutation:
            if point not in state.proposals.votes:
                valid = False
                break
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            state = _child(
                source, runtime["connection"], runtime["state_model"],
                state, point, descriptors[point], TARGET_RADIUS)
            if state.actions[-1][1] != color:
                valid = False
                break
        if valid and action_key(state.actions) == action_key(actions):
            return state, tuple(permutation)
    raise AssertionError("no valid order reconstructs stage-local terminal")


def _geometry_group(payload):
    group, center, seed_positions, seed_species, candidate_actions = payload
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=tuple(map(float, center)),
        seed_positions=tuple(tuple(map(float, point))
                             for point in seed_positions),
        seed_species=tuple(map(str, seed_species)))
    rows = []
    for index, actions in enumerate(candidate_actions):
        actions = tuple((tuple(map(float, point)), str(color))
                        for point, color in actions)
        state, order = _reconstruct(source, runtime, actions)
        trace, transitions = _rollout(
            source, state, runtime, relational=True)
        if trace["target_used"] or len(transitions) > 16:
            raise AssertionError("invalid target-free stage-local rollout")
        rows.append({
            "candidate_index": index, "action_key": action_key(actions),
            "reconstruction_order": order,
            "trace": trace, "transitions": tuple(transitions),
            "trace_digest": _digest(trace),
            "transition_digest": _digest(tuple(transitions)),
        })
    body = {
        "group": int(group), "center": tuple(map(float, center)),
        "seed_atoms": len(source.seed_positions), "rows": tuple(rows),
        "target_received_by_worker": False,
        "target_used_for_reconstruction_or_rollout": False,
    }
    return {**body, "geometry_digest_before_label_join": _digest(body)}


def _build_geometry(payloads, workers):
    if workers <= 1:
        return tuple(_geometry_group(payload) for payload in payloads)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", "")
    results = [None] * len(payloads)
    with tempfile.TemporaryDirectory(prefix="gcts-stage-local-rollout-") as tmp:
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
                    f"stage-local rollout worker {index} failed\n{output}{error}")
            results[index] = pickle.loads(output_path.read_bytes())
    return tuple(results)


def build_dataset(*, workers=1):
    source = load_prefix_dataset()
    rows = _flatten(source)
    receipts, _records, receipt_digest = _freeze_receipts(rows)
    shortlist = _shortlist(rows, _real_labels(rows), receipts)
    by_group = {group: tuple(
        row for row in shortlist if row["group"] == group)
                for group in range(source["consumed_development_groups"])}
    seeds = tuple(oracle_crop_fast(center, SEED_RADIUS)[0]
                  for center in DEVELOPMENT_CENTERS)
    payloads = tuple((
        group, center, seed.positions, seed.species,
        tuple(row["action_key_frozen"] for row in by_group[group]))
        for group, (center, seed) in enumerate(zip(DEVELOPMENT_CENTERS, seeds)))
    geometry = _build_geometry(payloads, workers)
    geometry_digest = _digest(tuple(
        row["geometry_digest_before_label_join"] for row in geometry))

    groups = []
    for frozen in geometry:
        source_rows = by_group[frozen["group"]]
        labelled = []
        for row, labels in zip(frozen["rows"], source_rows):
            if action_key(row["action_key"]) != \
                    action_key(labels["action_key_frozen"]):
                raise AssertionError("stage-local rollout label join drift")
            labelled.append({
                **row, "site_correct": tuple(labels["site_correct"]),
                "correct_sites": int(labels["correct_sites"]),
                "exact": bool(labels["viable_prefix"]),
            })
        groups.append({
            **frozen, "rows": tuple(labelled),
            "labels_joined_after_all_rollouts_froze": True,
        })
    body = {
        "schema_version": 1,
        "source_dataset_digest": source["dataset_digest"],
        "development_groups": len(groups),
        "candidate_count": sum(len(group["rows"]) for group in groups),
        "candidate_count_per_group": 8,
        "prefix_receipt_digest": receipt_digest,
        "geometry_digest_before_any_label_join": geometry_digest,
        "groups": tuple(groups),
        "all_labels_joined_after_all_rollouts_froze": True,
        "targets_used_for_candidate_reconstruction_or_rollout": False,
        "confirmation_data_imported_or_used": False,
        "consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "dataset_digest": _digest(body)}


def validate_dataset(row):
    body = dict(row)
    digest = body.pop("dataset_digest")
    if _digest(body) != digest or body["development_groups"] != 20 or \
            body["candidate_count"] != 160 or \
            not body["all_labels_joined_after_all_rollouts_froze"] or \
            body["targets_used_for_candidate_reconstruction_or_rollout"] or \
            body["confirmation_data_imported_or_used"] or \
            body["fresh_confirmation_claimed"] or \
            body["autonomous_growth_claimed"] or \
            body["stationary_or_exponential_claimed"]:
        raise AssertionError("stage-local rollout dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("unexpected stage-local rollout dataset")
    return row


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("stage-local rollout fixture byte drift")
    return validate_dataset(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int,
                        default=max(1, min(4, os.cpu_count() or 1)))
    parser.add_argument("--group-pickle", nargs=2)
    args = parser.parse_args()
    if args.group_pickle:
        input_path, output_path = map(Path, args.group_pickle)
        output_path.write_bytes(pickle.dumps(
            _geometry_group(pickle.loads(input_path.read_bytes()))))
        return
    if args.write and DEFAULT_FIXTURE.exists():
        raise RuntimeError("stage-local rollout fixture already exists")
    row = build_dataset(workers=max(1, args.workers))
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
