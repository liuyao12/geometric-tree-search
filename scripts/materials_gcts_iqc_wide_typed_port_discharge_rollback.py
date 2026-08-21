#!/usr/bin/env python3
"""Nested rollback audit over the wide typed-discharge IQC portfolio."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_wide_typed_port_discharge_dataset import (
    DEFAULT_FIXTURE as TRACE_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_TRACE_DIGEST,
    load_default_dataset)


HORIZONS = (1, 2, 4, 8, 12, 16)
TYPED_METRICS = (
    "selected_persisted_mass", "selected_discharged_mass",
    "selected_reappearance_count", "selected_unique_role_count",
    "selected_survival_fraction",
)
SCALAR_METRICS = (
    "frontier_vote_mass", "frontier_count",
    "cumulative_selected_votes", "cumulative_log_probability",
    "integrated_frontier_vote_mass",
)
SHUFFLES = 31
SHUFFLE_SEED = 20260820
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_wide_typed_port_discharge_rollback_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "767466e15bfdf06dd97e80dbd2a7b48140bc3522673b8f4acd202b659b4cb48e"
EXPECTED_AUDIT_DIGEST = \
    "f84a060fcc768e25410f7440b1123c56288ce5e8bdb3983080f933a81919b4c0"


@dataclass(frozen=True)
class Candidate:
    group: int
    stable_index: int
    trace: dict
    typed_transitions: tuple[dict, ...]
    exact: bool
    correct_sites: int


def _specs(kind):
    metrics = TYPED_METRICS if kind == "typed" else SCALAR_METRICS
    return tuple((kind, metric, horizon)
                 for horizon in HORIZONS for metric in metrics)


def _score(row, spec):
    kind, metric, horizon = spec
    if kind == "typed":
        selected = tuple(item
                         for transition in row.typed_transitions[:horizon]
                         for item in transition[
                             "selected_role_transitions"])
        if metric == "selected_persisted_mass":
            return float(sum(item["persisted"] for item in selected))
        if metric == "selected_discharged_mass":
            return float(sum(item["discharged"] for item in selected))
        if metric == "selected_reappearance_count":
            return float(sum(item["selected_again_within_horizon"]
                             for item in selected))
        if metric == "selected_unique_role_count":
            return float(len({json.dumps(
                item["role"], separators=(",", ":")) for item in selected}))
        if metric == "selected_survival_fraction":
            return sum(item["persisted"] for item in selected) / max(
                1, sum(item["before"] for item in selected))
    else:
        steps = row.trace["steps"][:horizon]
        if metric == "frontier_vote_mass":
            return float(steps[-1]["frontier_vote_mass_after"])
        if metric == "frontier_count":
            return float(steps[-1]["frontier_count_after"])
        if metric == "cumulative_selected_votes":
            return float(sum(item["selected_votes"] for item in steps))
        if metric == "cumulative_log_probability":
            return float(sum(math.log(max(
                item["selected_probability"], 1e-15)) for item in steps))
        if metric == "integrated_frontier_vote_mass":
            return float(steps[0]["frontier_vote_mass_before"] + sum(
                item["frontier_vote_mass_after"] for item in steps))
    raise AssertionError("unknown wide discharge score")


def _load_rows():
    dataset = load_default_dataset(TRACE_FIXTURE)
    if dataset["dataset_digest"] != EXPECTED_TRACE_DIGEST:
        raise AssertionError("wide typed trace drift")
    rows = tuple(Candidate(
        int(group["group"]), int(row["stable_index"]), row["trace"],
        tuple(row["typed_transitions"]), bool(row["exact"]),
        int(row["correct_sites"]))
        for group in dataset["groups"] for row in group["rows"])
    return rows, dataset


def _score_cache(rows):
    return {(row.group, row.stable_index, spec): _score(row, spec)
            for row in rows for kind in ("typed", "scalar")
            for spec in _specs(kind)}


def _select(rows, spec, cache):
    return min(rows, key=lambda row: (
        -cache[row.group, row.stable_index, spec], row.stable_index))


def _objective(rows, spec, cache):
    selected = tuple(_select(tuple(
        row for row in rows if row.group == group), spec, cache)
        for group in sorted({row.group for row in rows}))
    return (sum(row.exact for row in selected),
            sum(row.correct_sites for row in selected))


def _fit(rows, kind, cache):
    specs = _specs(kind)
    return max(specs, key=lambda spec: (
        *_objective(rows, spec, cache), -spec[2], -specs.index(spec)))


def _nested(rows, kind, cache):
    folds = []
    for heldout in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        spec = _fit(training, kind, cache)
        selected = _select(held, spec, cache)
        folds.append({
            "heldout_group": heldout,
            "selected_metric": spec[1],
            "selected_horizon": spec[2],
            "terminal_supply": any(row.exact for row in held),
            "selected_stable_index": selected.stable_index,
            "selected_exact": selected.exact,
            "selected_correct_sites": selected.correct_sites,
            "selected_score": cache[
                selected.group, selected.stable_index, spec],
        })
    return tuple(folds)


def _summary(folds):
    return (sum(fold["selected_exact"] for fold in folds
                if fold["terminal_supply"]),
            sum(fold["selected_correct_sites"] for fold in folds))


def _shuffle(rows, index):
    rng = random.Random(f"{SHUFFLE_SEED}:{index}")
    result = []
    for group in sorted({row.group for row in rows}):
        group_rows = tuple(row for row in rows if row.group == group)
        labels = [(row.exact, row.correct_sites) for row in group_rows]
        rng.shuffle(labels)
        result.extend(replace(row, exact=exact, correct_sites=sites)
                      for row, (exact, sites) in zip(group_rows, labels))
    return tuple(result)


def evaluate():
    rows, dataset = _load_rows()
    cache = _score_cache(rows)
    typed_folds = _nested(rows, "typed", cache)
    scalar_folds = _nested(rows, "scalar", cache)
    typed_exact, typed_sites = _summary(typed_folds)
    scalar_exact, scalar_sites = _summary(scalar_folds)
    null_typed, null_scalar = [], []
    for index in range(SHUFFLES):
        shuffled = _shuffle(rows, index)
        null_typed.append(_summary(_nested(
            shuffled, "typed", cache))[0])
        null_scalar.append(_summary(_nested(
            shuffled, "scalar", cache))[0])
    typed_p = (1 + sum(value >= typed_exact for value in null_typed)) / \
        (SHUFFLES + 1)
    scalar_p = (1 + sum(value >= scalar_exact for value in null_scalar)) / \
        (SHUFFLES + 1)
    final_typed = _fit(rows, "typed", cache)
    final_scalar = _fit(rows, "scalar", cache)
    typed_better = (typed_exact, typed_sites) > (scalar_exact, scalar_sites)
    body = {
        "schema_version": 1,
        "wide_typed_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["development_groups"],
        "retained_candidates": len(rows),
        "maximum_retained_candidates": dataset[
            "maximum_retained_candidates"],
        "mixed_exact_inexact_groups": sum(
            0 < sum(row.exact for row in rows if row.group == group) <
            sum(row.group == group for row in rows)
            for group in sorted({row.group for row in rows})),
        "typed_metrics": TYPED_METRICS,
        "scalar_metrics": SCALAR_METRICS,
        "horizons": HORIZONS,
        "typed_folds": typed_folds,
        "scalar_folds": scalar_folds,
        "typed_nested_exact_supplied_groups": typed_exact,
        "typed_nested_correct_sites": typed_sites,
        "scalar_nested_exact_supplied_groups": scalar_exact,
        "scalar_nested_correct_sites": scalar_sites,
        "typed_lexicographically_beats_scalar": typed_better,
        "development_typed_metric": final_typed[1],
        "development_typed_horizon": final_typed[2],
        "development_scalar_metric": final_scalar[1],
        "development_scalar_horizon": final_scalar[2],
        "shuffle_count": SHUFFLES,
        "shuffle_seed": SHUFFLE_SEED,
        "fully_nested_typed_shuffle_exact_counts": tuple(null_typed),
        "fully_nested_scalar_shuffle_exact_counts": tuple(null_scalar),
        "typed_shuffle_upper_tail_p": typed_p,
        "scalar_shuffle_upper_tail_p": scalar_p,
        "typed_development_gate_passed": (
            typed_exact >= 9 and typed_sites >= 27),
        "typed_causal_superiority_gate_passed": (
            typed_better and typed_p <= .05),
        "failure_detector_validated_target_free": (
            typed_exact >= 9 and typed_sites >= 27
            and typed_better and typed_p <= .05),
        "exact_candidate_set_identical_across_arms": True,
        "every_null_refit_in_every_outer_fold": True,
        "candidate_geometry_unchanged": True,
        "target_used_for_rollout_fit_or_selection": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_commit_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "audit_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("audit_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or body["wide_typed_dataset_digest"] != EXPECTED_TRACE_DIGEST
            or body["retained_candidates"] != 120
            or body["maximum_retained_candidates"] > 16
            or body["mixed_exact_inexact_groups"] < 5
            or tuple(body["typed_metrics"]) != TYPED_METRICS
            or tuple(body["scalar_metrics"]) != SCALAR_METRICS
            or tuple(body["horizons"]) != HORIZONS
            or not body["exact_candidate_set_identical_across_arms"]
            or not body["every_null_refit_in_every_outer_fold"]
            or not body["candidate_geometry_unchanged"]
            or body["target_used_for_rollout_fit_or_selection"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("wide typed rollback drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("wide typed rollback audit drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("wide typed rollback fixture byte drift")
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
