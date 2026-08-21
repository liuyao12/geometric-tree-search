#!/usr/bin/env python3
"""Build the preregistered disjoint IQC obligation development corpus.

Workers receive only colored R9 seeds.  They freeze complete candidate trees,
dual-ranker portfolios, and sixteen-step relational obligation trajectories.
Only after every group's geometry digest exists does the parent construct the
R14.56 development targets and join labels.  This is consumed development
evidence, not a confirmation.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import pickle
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

from materials_gcts_dual_rank_terminal_portfolio import (
    select_dual_rank_terminal_portfolio)
from materials_gcts_iqc_frozen_fusion_runtime import (
    action_key, load_default_runtime)
from materials_gcts_iqc_obligation_expanded_preregistration import (
    CANDIDATES_PER_BASE_RANKER, DEVELOPMENT_CENTERS,
    EXPECTED_MANIFEST_DIGEST, MAXIMUM_FROZEN_CANDIDATES,
    ORACLE_LIFT_BOUND, ROLLOUT_HORIZON, ROLLOUT_RADIUS, SEED_RADIUS,
    TARGET_RADIUS, audit as preregistration_audit)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius, _freeze_at_radius)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_iqc_wide_typed_port_discharge_dataset import _rollout
from materials_gcts_icosahedral_modelset import oracle_patch_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_obligation_expanded_development_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "a6bbb9209f36cbccd2e6f6b0ce64a2fb620e348e894703f8e6a1e4e9baf30806"
EXPECTED_DATASET_DIGEST = \
    "5450f477d3968007bcf5a722f9380645dffd972ddd71691af8a9796cfd30e1df"


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _site_key(point):
    return tuple(round(float(value), 6) for value in point)


def _geometry_group(payload):
    group, center, seed_positions, seed_species = payload
    runtime = load_default_runtime()
    seed = SimpleNamespace(
        positions=tuple(tuple(map(float, point)) for point in seed_positions),
        species=tuple(map(str, seed_species)))
    source = SimpleNamespace(
        group=tuple(center), seed_positions=seed.positions,
        seed_species=seed.species)
    nucleus = _freeze_at_radius(runtime, tuple(center), seed, TARGET_RADIUS)
    states, counts = _complete_states_at_radius(
        source, runtime, TARGET_RADIUS)
    states_by_action = {action_key(row.actions): row for row in states}
    if tuple(counts) != tuple(nucleus.candidate_counts_by_depth) or \
            len(states_by_action) != len(nucleus.terminals):
        raise AssertionError(f"group {group} candidate accounting drift")
    candidate_ids = tuple(row.actions for row in nucleus.terminals)
    portfolio = select_dual_rank_terminal_portfolio(
        candidate_ids, nucleus.scalar_order, nucleus.fusion_order,
        per_channel_budget=CANDIDATES_PER_BASE_RANKER)
    retained = tuple(portfolio.selected_candidate_ids)
    if len(retained) > MAXIMUM_FROZEN_CANDIDATES:
        raise AssertionError("expanded portfolio exceeds frozen bound")
    rows = []
    for actions in retained:
        state = states_by_action[tuple(actions)]
        trace, transitions = _rollout(
            source, state, runtime, relational=True)
        if len(transitions) > ROLLOUT_HORIZON or trace["target_used"]:
            raise AssertionError("invalid target-free obligation rollout")
        rows.append({
            "action_key": tuple(actions),
            "trace": trace,
            "transitions": tuple(transitions),
            "trace_digest": _digest(trace),
            "transition_digest": _digest(tuple(transitions)),
        })
    rows = tuple(sorted(rows, key=lambda row: repr(row["action_key"])))
    body = {
        "group": int(group),
        "center": tuple(map(float, center)),
        "seed_atoms": len(seed.positions),
        "candidate_counts_by_depth": tuple(counts),
        "complete_terminal_count": len(states),
        "retained_candidates": len(rows),
        "candidate_digest": nucleus.candidate_digest,
        "portfolio_digest": portfolio.selection_digest,
        "rows": rows,
        "target_received_by_worker": False,
        "target_used_for_candidate_or_rollout": False,
    }
    return {**body, "geometry_digest_before_label_join": _digest(body)}


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
    with tempfile.TemporaryDirectory(prefix="gcts-expanded-obligation-") as tmp:
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
                    f"expanded obligation worker {index} failed\n"
                    f"{output}{error}")
            results[index] = pickle.loads(output_path.read_bytes())
    return tuple(results)


def build_dataset(*, workers=1):
    protocol = preregistration_audit()
    if protocol.manifest_digest != EXPECTED_MANIFEST_DIGEST or \
            not protocol.rollout_domains_disjoint:
        raise AssertionError("expanded obligation preregistration drift")

    seed_physical_radius = math.ceil(max(math.dist(
        (0., 0., 0.), center) for center in DEVELOPMENT_CENTERS) +
        SEED_RADIUS)
    seed_oracle, _ = oracle_patch_fast(
        ORACLE_LIFT_BOUND, seed_physical_radius)
    seeds = tuple(_crop(seed_oracle, center, SEED_RADIUS,
                        f"obligation-expanded-seed-{group}")
                  for group, center in enumerate(DEVELOPMENT_CENTERS))
    if any(not seed.positions for seed in seeds):
        raise AssertionError("expanded development contains an empty seed")

    # Only R9 seed tuples cross the worker boundary.  This tuple and digest
    # freeze for all twenty nuclei before either outer oracle below exists.
    geometry = _build_geometry(seeds, workers)
    geometry_digest = _digest(tuple(
        row["geometry_digest_before_label_join"] for row in geometry))

    target_physical_radius = math.ceil(max(math.dist(
        (0., 0., 0.), center) for center in DEVELOPMENT_CENTERS) +
        TARGET_RADIUS)
    oracle, _ = oracle_patch_fast(
        ORACLE_LIFT_BOUND, target_physical_radius)
    check, _ = oracle_patch_fast(
        ORACLE_LIFT_BOUND + 1, target_physical_radius)
    stable = True
    groups = []
    for group, (center, seed, frozen) in enumerate(zip(
            DEVELOPMENT_CENTERS, seeds, geometry)):
        seed_check = _crop(check, center, SEED_RADIUS,
                           f"obligation-expanded-seed-check-{group}")
        target = _crop(oracle, center, TARGET_RADIUS,
                       f"obligation-expanded-target-{group}")
        target_check = _crop(check, center, TARGET_RADIUS,
                             f"obligation-expanded-target-check-{group}")
        stable = stable and (
            tuple(seed.positions), tuple(seed.species)) == (
                tuple(seed_check.positions), tuple(seed_check.species)) and (
            tuple(target.positions), tuple(target.species)) == (
                tuple(target_check.positions), tuple(target_check.species))
        truth = {_site_key(point): str(color) for point, color in zip(
            target.positions, target.species)}
        labelled = []
        for row in frozen["rows"]:
            correct = sum(truth.get(_site_key(point)) == str(color)
                          for point, color in row["action_key"])
            labelled.append({
                **row, "exact": correct == len(row["action_key"]),
                "correct_sites": correct,
            })
        groups.append({
            **frozen,
            "target_atoms": len(target.positions),
            "rows": tuple(labelled),
            "labels_joined_after_all_geometry_froze": True,
        })
    if not stable:
        raise AssertionError("expanded obligation crop changes at bound + 1")

    body = {
        "schema_version": 1,
        "source_preregistration_digest": protocol.manifest_digest,
        "development_groups": len(groups),
        "rollout_domain_radius": ROLLOUT_RADIUS,
        "rollout_horizon": ROLLOUT_HORIZON,
        "required_center_separation": protocol.required_center_separation,
        "minimum_batch_center_separation":
            protocol.minimum_batch_center_separation,
        "minimum_consumed_center_separation":
            protocol.minimum_consumed_center_separation,
        "raw_rollout_domains_disjoint": protocol.rollout_domains_disjoint,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "oracle_bound_plus_one_stable": stable,
        "geometry_digest_before_any_target_construction": geometry_digest,
        "groups": tuple(groups),
        "candidate_geometry_changed": False,
        "all_targets_constructed_after_all_geometry_froze": True,
        "targets_used_for_fit_or_candidate_generation": False,
        "labels_joined_only_for_consumed_development": True,
        "failed_or_label_trivial_nuclei_retained": True,
        "fresh_confirmation_claimed": False,
    }
    return {**body, "dataset_digest": _digest(body)}


def validate_dataset(row):
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (_digest(body) != digest
            or body["development_groups"] != len(DEVELOPMENT_CENTERS)
            or not body["raw_rollout_domains_disjoint"]
            or not body["oracle_bound_plus_one_stable"]
            or not body["all_targets_constructed_after_all_geometry_froze"]
            or body["targets_used_for_fit_or_candidate_generation"]
            or body["candidate_geometry_changed"]
            or body["fresh_confirmation_claimed"]
            or any(group["target_received_by_worker"] or
                   group["target_used_for_candidate_or_rollout"] or
                   not group["labels_joined_after_all_geometry_froze"]
                   for group in body["groups"])):
        raise AssertionError("expanded obligation dataset drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("unexpected expanded obligation dataset digest")
    return row


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("expanded obligation fixture byte drift")
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
        raise RuntimeError("expanded obligation fixture already exists")
    row = build_dataset(workers=max(1, args.workers))
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
