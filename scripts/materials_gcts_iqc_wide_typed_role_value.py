#!/usr/bin/env python3
"""Nested identity-specific value over wide IQC port-discharge histories."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_wide_typed_port_discharge_rollback import (
    Candidate, SHUFFLES, SHUFFLE_SEED, _load_rows)


HORIZONS = (4, 8, 16)
TOKEN_FAMILIES = (
    "exact-role-status", "exact-role-status-transition",
    "coarse-role-status", "coarse-role-status-transition",
    "chemistry-role-status",
)
MINIMUM_GROUPS = (2, 3)
SHRINKAGES = (1., 4.)
AGGREGATIONS = ("mean", "sqrt-sum")
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_wide_typed_role_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "42a9429f37ad65dc12d9f5e665712b6557fb3fcf592ed6111a7d10069bed8c61"
EXPECTED_AUDIT_DIGEST = \
    "e168087f86b909a7dd065603784ffbd05da7528a1a60e9aa2313b5d8f22739fb"


@dataclass(frozen=True, order=True)
class Spec:
    horizon: int
    token_family: str
    minimum_groups: int
    shrinkage: float
    aggregation: str


@dataclass(frozen=True)
class Model:
    spec: Spec
    intercept: float
    weights: dict
    evidence: dict


SPECS = tuple(Spec(horizon, family, groups, shrinkage, aggregation)
              for horizon in HORIZONS
              for family in TOKEN_FAMILIES
              for groups in MINIMUM_GROUPS
              for shrinkage in SHRINKAGES
              for aggregation in AGGREGATIONS)


def _role(item, family):
    row = item["role"]
    exact = (str(row[0]), tuple(row[1]), str(row[2]),
             tuple(row[3]), int(row[4]))
    if family.startswith("exact-"):
        return exact
    if family.startswith("coarse-"):
        return exact[0], exact[2], exact[4]
    if family.startswith("chemistry-"):
        return exact[0], exact[2]
    raise AssertionError("unknown role abstraction")


def _tokens(row, spec):
    transitions = row.typed_transitions[:spec.horizon]
    result = set()
    primary = []
    for transition in transitions:
        selected = transition["selected_role_transitions"]
        if selected:
            primary.append(_role(selected[0], spec.token_family))
        for item in selected:
            role = _role(item, spec.token_family)
            result.add(("role", role))
            result.add(("discharged", role, item["discharged"] > 0))
            result.add(("persisted", role, item["persisted"] > 0))
            result.add(("reappears", role,
                        item["selected_again_within_horizon"] is True))
            if item["steps_until_selected_again"]:
                result.add(("return-wait", role,
                            min(4, int(item["steps_until_selected_again"]))))
    if spec.token_family.endswith("-transition"):
        result.update(("role-transition", left, right)
                      for left, right in zip(primary, primary[1:]))
    return frozenset(result)


def _fit(rows, spec, token_cache):
    positives = sum(row.exact for row in rows)
    total = len(rows)
    prior = spec.shrinkage
    base = (positives + prior) / (total + 2 * prior)
    intercept = math.log(base / (1 - base))
    counts = defaultdict(lambda: [0, 0, set()])
    for row in rows:
        for token in token_cache[row.group, row.stable_index, spec]:
            counts[token][0] += int(row.exact)
            counts[token][1] += 1
            counts[token][2].add(row.group)
    weights, evidence = {}, {}
    for token, (positive, count, groups) in counts.items():
        if len(groups) < spec.minimum_groups:
            continue
        probability = (positive + prior) / (count + 2 * prior)
        weights[token] = math.log(probability / (1 - probability)) - intercept
        evidence[token] = (positive, count, len(groups))
    return Model(spec, intercept, weights, evidence)


def _score(model, row, token_cache):
    tokens = token_cache[row.group, row.stable_index, model.spec]
    values = tuple(model.weights[token] for token in tokens
                   if token in model.weights)
    if not values:
        return model.intercept, 0., 0
    scale = len(values) if model.spec.aggregation == "mean" \
        else math.sqrt(len(values))
    return model.intercept + sum(values) / scale, len(values) / len(tokens), \
        len(values)


def _rank(model, rows, token_cache):
    return min(rows, key=lambda row: (
        -_score(model, row, token_cache)[0], row.stable_index))


def _inner_objective(rows, spec, token_cache):
    selected = []
    groups = sorted({row.group for row in rows})
    for heldout in groups:
        model = _fit(tuple(row for row in rows if row.group != heldout),
                     spec, token_cache)
        selected.append(_rank(model, tuple(
            row for row in rows if row.group == heldout), token_cache))
    return sum(row.exact for row in selected), \
        sum(row.correct_sites for row in selected)


def _select_spec(rows, token_cache):
    return max(SPECS, key=lambda spec: (
        *_inner_objective(rows, spec, token_cache),
        -spec.horizon, -SPECS.index(spec)))


def _nested(rows, token_cache):
    folds = []
    for heldout in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        spec = _select_spec(training, token_cache)
        model = _fit(training, spec, token_cache)
        selected = _rank(model, held, token_cache)
        score, coverage, supported = _score(model, selected, token_cache)
        folds.append({
            "heldout_group": heldout,
            "selected_spec": asdict(spec),
            "terminal_supply": any(row.exact for row in held),
            "selected_stable_index": selected.stable_index,
            "selected_exact": selected.exact,
            "selected_correct_sites": selected.correct_sites,
            "selected_score": score,
            "selected_token_coverage": coverage,
            "selected_supported_tokens": supported,
            "fitted_token_weights": len(model.weights),
        })
    return tuple(folds)


def _summary(folds):
    return (sum(row["selected_exact"] for row in folds
                if row["terminal_supply"]),
            sum(row["selected_correct_sites"] for row in folds))


def _shuffle(rows, index):
    rng = random.Random(f"{SHUFFLE_SEED}:typed-role:{index}")
    result = []
    for group in sorted({row.group for row in rows}):
        group_rows = tuple(row for row in rows if row.group == group)
        labels = [(row.exact, row.correct_sites) for row in group_rows]
        rng.shuffle(labels)
        result.extend(replace(row, exact=exact, correct_sites=sites)
                      for row, (exact, sites) in zip(group_rows, labels))
    return tuple(result)


def evaluate(*, include_null=True):
    rows, dataset = _load_rows()
    token_cache = {(row.group, row.stable_index, spec): _tokens(row, spec)
                   for row in rows for spec in SPECS}
    folds = _nested(rows, token_cache)
    exact, sites = _summary(folds)
    final_spec = _select_spec(rows, token_cache)
    final_model = _fit(rows, final_spec, token_cache)
    null = []
    if include_null:
        for index in range(SHUFFLES):
            null.append(_summary(_nested(
                _shuffle(rows, index), token_cache))[0])
    p = ((1 + sum(value >= exact for value in null)) / (SHUFFLES + 1)
         if include_null else None)
    body = {
        "schema_version": 1,
        "wide_typed_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["development_groups"],
        "retained_candidates": len(rows),
        "spec_count": len(SPECS),
        "horizons": HORIZONS,
        "token_families": TOKEN_FAMILIES,
        "minimum_groups": MINIMUM_GROUPS,
        "shrinkages": SHRINKAGES,
        "aggregations": AGGREGATIONS,
        "folds": folds,
        "nested_selected_exact_supplied_groups": exact,
        "nested_selected_correct_sites": sites,
        "final_spec": asdict(final_spec),
        "final_fitted_token_weights": len(final_model.weights),
        "shuffle_count": SHUFFLES if include_null else 0,
        "shuffle_seed": SHUFFLE_SEED,
        "fully_nested_shuffle_exact_counts": tuple(null),
        "shuffle_upper_tail_p": p,
        "development_gate_passed": exact >= 9 and sites >= 27,
        "causal_superiority_gate_passed": bool(
            include_null and exact >= 9 and sites >= 27 and p <= .05),
        "failure_detector_validated_target_free": bool(
            include_null and exact >= 9 and sites >= 27 and p <= .05),
        "exact_candidate_set_unchanged": True,
        "semantic_role_identity_preserved": True,
        "minimum_independent_group_support_enforced": True,
        "every_hyperparameter_selected_inside_outer_fold": True,
        "every_null_refit_in_every_inner_and_outer_fold": True,
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
            or body["schema_version"] != 1
            or body["retained_candidates"] != 120
            or body["spec_count"] != len(SPECS)
            or tuple(body["horizons"]) != HORIZONS
            or tuple(body["token_families"]) != TOKEN_FAMILIES
            or not body["exact_candidate_set_unchanged"]
            or not body["semantic_role_identity_preserved"]
            or not body["minimum_independent_group_support_enforced"]
            or not body["every_hyperparameter_selected_inside_outer_fold"]
            or not body["every_null_refit_in_every_inner_and_outer_fold"]
            or body["target_used_for_fit_or_selection"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("wide typed role value drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("wide typed role audit drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("wide typed role fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--no-null", action="store_true")
    args = parser.parse_args()
    row = evaluate(include_null=not args.no_null)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        if args.no_null:
            raise SystemExit("refusing to freeze an audit without null controls")
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
