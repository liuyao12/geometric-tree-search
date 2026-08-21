#!/usr/bin/env python3
"""Low-capacity relational contradiction rule for wide IQC rollback."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
from dataclasses import replace
from pathlib import Path

from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_relational_port_discharge_dataset import (
    DEFAULT_FIXTURE as DATASET_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_DATASET_DIGEST,
    load_default_dataset)
from materials_gcts_iqc_wide_typed_port_discharge_rollback import Candidate


HORIZONS = (1, 2, 4, 8, 16)
METRICS = (
    "no_reverse", "no_forward", "no_touch_source",
    "forward_lost", "reverse_lost", "touch_source_lost",
    "forward_after", "reverse_after", "touch_source_after",
    "selected_pair_reverse", "selected_pair_forward",
    "selected_pair_touch",
)
DIRECTIONS = ("maximize", "minimize")
SPECS = tuple((metric, horizon, direction)
              for horizon in HORIZONS for metric in METRICS
              for direction in DIRECTIONS)
SHUFFLES = 31
SHUFFLE_SEED = 20260820
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_relational_port_rule_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "71bbd626e9d463d29943b9d4f53b01e14e2b00e14419c7dc85ec0ba3aabaacc7"
EXPECTED_AUDIT_DIGEST = \
    "3c067ae87a86c8e7af8303b57b25bb1163bb2d79656c257cc85566c95ee340f6"


def _load_rows():
    dataset = load_default_dataset(DATASET_FIXTURE)
    if dataset["dataset_digest"] != EXPECTED_DATASET_DIGEST:
        raise AssertionError("relational dataset drift")
    rows = tuple(Candidate(
        int(group["group"]), int(row["stable_index"]), row["trace"],
        tuple(row["typed_transitions"]), bool(row["exact"]),
        int(row["correct_sites"]))
        for group in dataset["groups"] for row in group["rows"])
    return rows, dataset


def _raw_score(row, metric, horizon):
    transitions = row.typed_transitions[:horizon]
    selected = tuple(item for transition in transitions
                     for item in transition["selected_role_transitions"])
    pairs = tuple(item for transition in transitions
                  for item in transition["selected_pair_relations"])
    if metric == "no_reverse":
        return sum(item["contradiction_flags"]["no_reverse_after"]
                   for item in selected)
    if metric == "no_forward":
        return sum(item["contradiction_flags"]["no_forward_after"]
                   for item in selected)
    if metric == "no_touch_source":
        return sum(item["contradiction_flags"]["no_touch_source_after"]
                   for item in selected)
    relation = ("forward" if metric.startswith("forward_") else
                "reverse" if metric.startswith("reverse_") else
                "touch_source")
    if metric.endswith("_lost"):
        return sum(item["relation_counts"][relation]["lost"]
                   for item in selected)
    if metric.endswith("_after"):
        return sum(item["relation_counts"][relation]["after"]
                   for item in selected)
    if metric == "selected_pair_reverse":
        return sum(item["reverse"] for item in pairs)
    if metric == "selected_pair_forward":
        return sum(item["forward"] for item in pairs)
    if metric == "selected_pair_touch":
        return sum(item["touch_source"] or item["touch_parent"]
                   for item in pairs)
    raise AssertionError("unknown relational metric")


def _score(row, spec):
    metric, horizon, direction = spec
    value = _raw_score(row, metric, horizon)
    return value if direction == "maximize" else -value


def _cache(rows):
    return {(row.group, row.stable_index, spec): _score(row, spec)
            for row in rows for spec in SPECS}


def _select(rows, spec, cache):
    return min(rows, key=lambda row: (
        -cache[row.group, row.stable_index, spec], row.stable_index))


def _objective(rows, spec, cache):
    selected = tuple(_select(tuple(
        row for row in rows if row.group == group), spec, cache)
        for group in sorted({row.group for row in rows}))
    return sum(row.exact for row in selected), \
        sum(row.correct_sites for row in selected)


def _fit(rows, cache):
    return max(SPECS, key=lambda spec: (
        *_objective(rows, spec, cache), -spec[1], -SPECS.index(spec)))


def _nested(rows, cache):
    folds = []
    for heldout in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        spec = _fit(training, cache)
        selected = _select(held, spec, cache)
        folds.append({
            "heldout_group": heldout,
            "selected_metric": spec[0],
            "selected_horizon": spec[1],
            "selected_direction": spec[2],
            "terminal_supply": any(row.exact for row in held),
            "selected_stable_index": selected.stable_index,
            "selected_exact": selected.exact,
            "selected_correct_sites": selected.correct_sites,
            "selected_score": cache[
                selected.group, selected.stable_index, spec],
        })
    return tuple(folds)


def _summary(folds):
    return (sum(row["selected_exact"] for row in folds
                if row["terminal_supply"]),
            sum(row["selected_correct_sites"] for row in folds))


def _shuffle(rows, index):
    rng = random.Random(f"{SHUFFLE_SEED}:relational-rule:{index}")
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
    cache = _cache(rows)
    folds = _nested(rows, cache)
    exact, sites = _summary(folds)
    final_spec = _fit(rows, cache)
    null = tuple(_summary(_nested(_shuffle(rows, index), cache))[0]
                 for index in range(SHUFFLES))
    p = (1 + sum(value >= exact for value in null)) / (SHUFFLES + 1)
    body = {
        "schema_version": 1,
        "relational_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["development_groups"],
        "retained_candidates": len(rows),
        "spec_count": len(SPECS),
        "metrics": METRICS,
        "horizons": HORIZONS,
        "directions": DIRECTIONS,
        "folds": folds,
        "nested_selected_exact_supplied_groups": exact,
        "nested_selected_correct_sites": sites,
        "development_selected_metric": final_spec[0],
        "development_selected_horizon": final_spec[1],
        "development_selected_direction": final_spec[2],
        "shuffle_count": SHUFFLES,
        "shuffle_seed": SHUFFLE_SEED,
        "fully_nested_shuffle_exact_counts": null,
        "shuffle_upper_tail_p": p,
        "development_gate_passed": exact >= 9 and sites >= 27,
        "causal_superiority_gate_passed": (
            exact >= 9 and sites >= 27 and p <= .05),
        "failure_detector_validated_target_free": (
            exact >= 9 and sites >= 27 and p <= .05),
        "full_background_roles_used_only_for_relations": True,
        "background_role_identities_not_features": True,
        "candidate_geometry_unchanged": True,
        "whole_nucleus_outer_selection": True,
        "every_null_refit_in_every_outer_fold": True,
        "target_used_for_fit_or_selection": False,
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
            or body["relational_dataset_digest"] != EXPECTED_DATASET_DIGEST
            or body["retained_candidates"] != 120
            or body["spec_count"] != len(SPECS)
            or tuple(body["metrics"]) != METRICS
            or tuple(body["horizons"]) != HORIZONS
            or not body["full_background_roles_used_only_for_relations"]
            or not body["background_role_identities_not_features"]
            or not body["candidate_geometry_unchanged"]
            or not body["whole_nucleus_outer_selection"]
            or not body["every_null_refit_in_every_outer_fold"]
            or body["target_used_for_fit_or_selection"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("relational port rule drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("relational port rule audit drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("relational port rule fixture byte drift")
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
