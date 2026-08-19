#!/usr/bin/env python3
"""Whole-nucleus rollback audit for frozen target-free port-discharge traces."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_post_self_fed_port_discharge_dataset import (
    DEFAULT_FIXTURE as TRACE_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_TRACE_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_TRACE_SHA256,
    ROLLOUT_HORIZON, load_fixture_json, validate_dataset)


METRICS = (
    "frontier_vote_mass", "frontier_count", "cumulative_selected_votes",
    "cumulative_log_probability", "integrated_frontier_vote_mass",
)
HORIZONS = (0, 1, 2, 4, 8, 12, 16)
RULE_GRID = tuple((metric, horizon)
                  for horizon in HORIZONS for metric in METRICS)
SHUFFLES = 31
SHUFFLE_SEED = 20260819
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_port_discharge_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "606d59239bf1822d3df0af931430b553f0329f533c312f3dbddff9e60e1255bc"
EXPECTED_AUDIT_DIGEST = \
    "5a7993de25847975207e2a921fa7795e990275e8dba3a7e2966bf0d9ee35b798"


@dataclass(frozen=True)
class Candidate:
    group: int
    stable_index: int
    trace: dict
    exact: bool
    correct_sites: int


@dataclass(frozen=True)
class HeldoutFold:
    heldout_group: int
    selected_metric: str
    selected_horizon: int
    terminal_supply: bool
    selected_stable_index: int
    selected_exact: bool
    selected_correct_sites: int
    selected_score: float


def _score(trace, spec):
    metric, horizon = spec
    steps = tuple(trace["steps"])
    if not steps:
        return 0.
    used = steps[:min(horizon, len(steps))]
    if horizon == 0:
        frontier_count = steps[0]["frontier_count_before"]
        frontier_mass = steps[0]["frontier_vote_mass_before"]
    else:
        frontier_count = used[-1]["frontier_count_after"]
        frontier_mass = used[-1]["frontier_vote_mass_after"]
    if metric == "frontier_vote_mass":
        return float(frontier_mass)
    if metric == "frontier_count":
        return float(frontier_count)
    if metric == "cumulative_selected_votes":
        return float(sum(step["selected_votes"] for step in used))
    if metric == "cumulative_log_probability":
        return float(sum(math.log(max(
            float(step["selected_probability"]), 1e-15)) for step in used))
    if metric == "integrated_frontier_vote_mass":
        return float(steps[0]["frontier_vote_mass_before"] + sum(
            step["frontier_vote_mass_after"] for step in used))
    raise AssertionError("unknown discharge metric")


def _select(rows, spec):
    return min(rows, key=lambda row: (
        -_score(row.trace, spec), row.stable_index))


def _training_objective(rows, spec):
    groups = sorted({row.group for row in rows})
    selected = tuple(_select(tuple(row for row in rows if row.group == group),
                             spec) for group in groups)
    supplied = {group for group in groups if any(
        row.exact for row in rows if row.group == group)}
    return (
        sum(row.exact for row in selected if row.group in supplied),
        sum(row.correct_sites for row in selected),
    )


def _fit(rows):
    # Scientific performance chooses the rule; equal rules prefer the shorter
    # rollout and then the declared low-cardinality metric order.
    metric_order = {metric: index for index, metric in enumerate(METRICS)}
    return max(RULE_GRID, key=lambda spec: (
        *_training_objective(rows, spec), -spec[1], -metric_order[spec[0]]))


def _load_rows():
    raw, payload = load_fixture_json(TRACE_FIXTURE)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_TRACE_SHA256:
        raise AssertionError("port-discharge fixture byte drift")
    dataset = validate_dataset(payload)
    if dataset["dataset_digest"] != EXPECTED_TRACE_DIGEST:
        raise AssertionError("port-discharge dataset drift")
    rows = tuple(Candidate(
        int(group["group"]), int(row["stable_index"]), row["trace"],
        bool(row["exact"]), int(row["correct_sites"]))
        for group in dataset["groups"] for row in group["rows"])
    return rows, dataset


def _shuffled_score(rows, spec, rng):
    shuffled = []
    for group in sorted({row.group for row in rows}):
        group_rows = tuple(row for row in rows if row.group == group)
        labels = [(row.exact, row.correct_sites) for row in group_rows]
        rng.shuffle(labels)
        shuffled.extend(Candidate(
            row.group, row.stable_index, row.trace, exact, correct)
            for row, (exact, correct) in zip(group_rows, labels))
    supplied = {group for group in {row.group for row in shuffled} if any(
        row.exact for row in shuffled if row.group == group)}
    selected = tuple(_select(tuple(
        row for row in shuffled if row.group == group), spec)
        for group in sorted(supplied))
    return sum(row.exact for row in selected)


def evaluate():
    rows, dataset = _load_rows()
    groups = tuple(range(dataset["development_groups"]))
    folds = []
    for heldout in groups:
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        spec = _fit(training)
        selected = _select(held, spec)
        folds.append(HeldoutFold(
            heldout, spec[0], spec[1], any(row.exact for row in held),
            selected.stable_index, selected.exact, selected.correct_sites,
            _score(selected.trace, spec)))
    final_spec = _fit(rows)
    final_selected = tuple(_select(tuple(
        row for row in rows if row.group == group), final_spec)
        for group in groups)
    supplied = {group for group in groups if any(
        row.exact for row in rows if row.group == group)}
    development_exact = sum(row.exact for row in final_selected
                            if row.group in supplied)
    development_sites = sum(row.correct_sites for row in final_selected)
    nested_exact = sum(fold.selected_exact for fold in folds
                       if fold.terminal_supply)
    nested_sites = sum(fold.selected_correct_sites for fold in folds)
    rng = random.Random(SHUFFLE_SEED)
    null_exact = tuple(_shuffled_score(rows, final_spec, rng)
                       for _index in range(SHUFFLES))
    shuffle_p = (1 + sum(score >= development_exact
                         for score in null_exact)) / (SHUFFLES + 1)
    body = {
        "schema_version": 1,
        "port_discharge_dataset_digest": dataset["dataset_digest"],
        "development_groups": len(groups),
        "retained_candidates": len(rows),
        "rule_metrics": METRICS,
        "rule_horizons": HORIZONS,
        "folds": [asdict(fold) for fold in folds],
        "nested_supplied_groups": sum(fold.terminal_supply for fold in folds),
        "nested_selected_exact_groups": nested_exact,
        "nested_selected_correct_sites": nested_sites,
        "development_selected_metric": final_spec[0],
        "development_selected_horizon": final_spec[1],
        "development_selected_exact_supplied_groups": development_exact,
        "development_selected_correct_sites": development_sites,
        "fixed_point_traces": sum(row.trace["fixed_point_reached"]
                                  for row in rows),
        "hard_exhaustion_certificate_available": any(
            row.trace["fixed_point_reached"] for row in rows),
        "shuffle_count": SHUFFLES,
        "shuffle_seed": SHUFFLE_SEED,
        "shuffle_exact_group_counts": null_exact,
        "shuffle_exact_upper_tail_p": shuffle_p,
        "nested_transfer_gate_passed": (
            nested_exact == len(supplied) and nested_sites >= 27),
        "causal_superiority_gate_passed": shuffle_p <= .05,
        "autonomous_commit_gate_passed": (
            nested_exact == len(supplied) and nested_sites >= 27
            and shuffle_p <= .05),
        "failure_detector_validated_target_free": False,
        "candidate_geometry_unchanged": True,
        "same_bounded_rollout_per_candidate": True,
        "whole_nucleus_outer_selection": True,
        "target_used_for_rollout_fit_or_selection": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "audit_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("audit_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or body["port_discharge_dataset_digest"] != EXPECTED_TRACE_DIGEST
            or body["development_groups"] != 10
            or body["retained_candidates"] != 19
            or tuple(body["rule_metrics"]) != METRICS
            or tuple(body["rule_horizons"]) != HORIZONS
            or not body["candidate_geometry_unchanged"]
            or not body["same_bounded_rollout_per_candidate"]
            or not body["whole_nucleus_outer_selection"]
            or body["target_used_for_rollout_fit_or_selection"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("post-self-fed port-discharge value drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("post-self-fed port-discharge audit drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("post-self-fed port-discharge value fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
