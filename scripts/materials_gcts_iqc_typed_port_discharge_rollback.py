#!/usr/bin/env python3
"""Whole-nucleus rollback audit for typed GCTS obligation discharge.

Only the retained candidate trajectories are ranked.  Exact candidate
geometry is unchanged.  Hyperparameters are selected without the heldout
nucleus, and every null assignment is refit independently in every outer
fold.  Because only three nuclei have nonidentical label tuples, the complete
eight-assignment randomization distribution is enumerated rather than sampled.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_typed_port_discharge_dataset import (
    DEFAULT_FIXTURE as TRACE_FIXTURE,
    EXPECTED_DATASET_DIGEST as EXPECTED_TRACE_DIGEST,
    load_default_dataset)


METRICS = (
    "selected_persisted_mass",
    "selected_discharged_mass",
    "selected_reappearance_count",
    "selected_unique_role_count",
    "selected_survival_fraction",
)
HORIZONS = (1, 2, 4, 8, 16)
RULE_GRID = tuple((metric, horizon)
                  for horizon in HORIZONS for metric in METRICS)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_typed_port_discharge_rollback_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "8af585b6340fe827da26e0b23ef29b900e840079ddff0fa8fafe3979013c06c7"
EXPECTED_AUDIT_DIGEST = \
    "d8635477bbda01561fb9ecb273397fbec78c0a64ff6ae4c37cb58183768bc570"


@dataclass(frozen=True)
class Candidate:
    group: int
    stable_index: int
    typed_transitions: tuple[dict, ...]
    exact: bool
    correct_sites: int


def _selected_rows(candidate, horizon):
    return tuple(item for transition in candidate.typed_transitions[:horizon]
                 for item in transition["selected_role_transitions"])


def _score(candidate, spec):
    metric, horizon = spec
    rows = _selected_rows(candidate, horizon)
    if metric == "selected_persisted_mass":
        return float(sum(row["persisted"] for row in rows))
    if metric == "selected_discharged_mass":
        return float(sum(row["discharged"] for row in rows))
    if metric == "selected_reappearance_count":
        return float(sum(row["selected_again_within_horizon"] for row in rows))
    if metric == "selected_unique_role_count":
        return float(len({json.dumps(row["role"], separators=(",", ":"))
                          for row in rows}))
    if metric == "selected_survival_fraction":
        return sum(row["persisted"] for row in rows) / max(
            1, sum(row["before"] for row in rows))
    raise AssertionError("unknown typed-discharge metric")


def _select(rows, spec):
    return min(rows, key=lambda row: (
        -_score(row, spec), row.stable_index))


def _objective(rows, spec):
    groups = sorted({row.group for row in rows})
    selected = tuple(_select(tuple(row for row in rows if row.group == group),
                             spec) for group in groups)
    return (sum(row.exact for row in selected),
            sum(row.correct_sites for row in selected))


def _fit(rows):
    metric_order = {name: index for index, name in enumerate(METRICS)}
    return max(RULE_GRID, key=lambda spec: (
        *_objective(rows, spec), -spec[1], -metric_order[spec[0]]))


def _rows(dataset):
    return tuple(Candidate(
        int(group["group"]), int(row["stable_index"]),
        tuple(row["typed_transitions"]), bool(row["exact"]),
        int(row["correct_sites"]))
        for group in dataset["groups"] for row in group["rows"])


def _nested(rows):
    result = []
    for heldout in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        spec = _fit(training)
        selected = _select(held, spec)
        result.append({
            "heldout_group": heldout,
            "selected_metric": spec[0],
            "selected_horizon": spec[1],
            "terminal_supply": any(row.exact for row in held),
            "selected_stable_index": selected.stable_index,
            "selected_exact": selected.exact,
            "selected_correct_sites": selected.correct_sites,
            "selected_score": _score(selected, spec),
        })
    return tuple(result)


def _label_assignments(rows):
    """Enumerate every distinct within-nucleus label-pair permutation."""
    changing = tuple(group for group in sorted({row.group for row in rows})
                     if len({(row.exact, row.correct_sites) for row in rows
                             if row.group == group}) > 1)
    assignments = []
    for bits in itertools.product((0, 1), repeat=len(changing)):
        copied = [Candidate(**asdict(row)) for row in rows]
        for group, swap in zip(changing, bits):
            if not swap:
                continue
            group_rows = [row for row in copied if row.group == group]
            if len(group_rows) != 2:
                raise AssertionError("audit expects binary retained supply")
            left, right = group_rows
            left_index, right_index = copied.index(left), copied.index(right)
            copied[left_index] = Candidate(
                left.group, left.stable_index, left.typed_transitions,
                right.exact, right.correct_sites)
            copied[right_index] = Candidate(
                right.group, right.stable_index, right.typed_transitions,
                left.exact, left.correct_sites)
        assignments.append((bits, tuple(copied)))
    return changing, tuple(assignments)


def evaluate():
    dataset = load_default_dataset(TRACE_FIXTURE)
    if dataset["dataset_digest"] != EXPECTED_TRACE_DIGEST:
        raise AssertionError("typed trace dataset drift")
    rows = _rows(dataset)
    folds = _nested(rows)
    supplied = sum(fold["terminal_supply"] for fold in folds)
    nested_exact = sum(fold["selected_exact"] for fold in folds
                       if fold["terminal_supply"])
    nested_sites = sum(fold["selected_correct_sites"] for fold in folds)
    final_spec = _fit(rows)
    final_selected = tuple(_select(tuple(
        row for row in rows if row.group == group), final_spec)
        for group in sorted({row.group for row in rows}))
    changing, assignments = _label_assignments(rows)
    null_scores = []
    for bits, shuffled in assignments:
        shuffled_folds = _nested(shuffled)
        null_scores.append({
            "swap_bits": bits,
            "nested_exact_supplied_groups": sum(
                fold["selected_exact"] for fold in shuffled_folds
                if fold["terminal_supply"]),
        })
    exact_p = sum(row["nested_exact_supplied_groups"] >= nested_exact
                  for row in null_scores) / len(null_scores)
    selected_role_rows = tuple(item for row in rows
                               for transition in row.typed_transitions
                               for item in transition[
                                   "selected_role_transitions"])
    body = {
        "schema_version": 1,
        "typed_discharge_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["development_groups"],
        "retained_candidates": len(rows),
        "semantic_selected_role_identities": len({json.dumps(
            row["role"], separators=(",", ":"))
            for row in selected_role_rows}),
        "typed_transitions": sum(len(row.typed_transitions) for row in rows),
        "selected_role_transitions": len(selected_role_rows),
        "rule_metrics": METRICS,
        "rule_horizons": HORIZONS,
        "folds": folds,
        "nested_supplied_groups": supplied,
        "nested_selected_exact_groups": nested_exact,
        "nested_selected_correct_sites": nested_sites,
        "development_selected_metric": final_spec[0],
        "development_selected_horizon": final_spec[1],
        "development_selected_exact_groups": sum(
            row.exact for row in final_selected),
        "development_selected_correct_sites": sum(
            row.correct_sites for row in final_selected),
        "nonidentical_label_tuple_groups": changing,
        "exhaustive_within_nucleus_assignments": len(assignments),
        "fully_nested_null_scores": null_scores,
        "exact_randomization_upper_tail_p": exact_p,
        "minimum_attainable_exact_randomization_p": 1 / len({
            tuple(row.exact for row in assignment)
            for _bits, assignment in assignments}),
        "nested_transfer_gate_passed": (
            nested_exact == supplied and nested_sites >= 27),
        "causal_superiority_gate_passed": exact_p <= .05,
        "failure_detector_validated_target_free": (
            nested_exact == supplied and nested_sites >= 27
            and exact_p <= .05),
        "selected_role_cohort_untruncated": True,
        "background_role_mass_used_for_ranking": False,
        "candidate_geometry_unchanged": True,
        "whole_nucleus_outer_selection": True,
        "every_null_refit_in_every_outer_fold": True,
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
            or body["typed_discharge_dataset_digest"] != EXPECTED_TRACE_DIGEST
            or body["retained_candidates"] != 19
            or not body["selected_role_cohort_untruncated"]
            or body["background_role_mass_used_for_ranking"]
            or not body["candidate_geometry_unchanged"]
            or not body["whole_nucleus_outer_selection"]
            or not body["every_null_refit_in_every_outer_fold"]
            or body["target_used_for_rollout_fit_or_selection"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("typed port-discharge rollback drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("typed port-discharge audit digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("typed rollback fixture byte drift")
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
