#!/usr/bin/env python3
"""Nested IQC rollback over the frozen two-marking portfolio.

The topology/yield portfolio supplies at most two immutable terminal states.
This audit asks whether the separately learned parent→child incidence value can
rank those states without target access.  No candidate, action, or geometry is
added by this module.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_parent_child_port_incidence_value import (
    Example, _fit, _load_examples,
    load_default_result as load_incidence_value)
from materials_gcts_iqc_post_self_fed_marking_portfolio import (
    load_default_result as load_portfolio)
from materials_gcts_learned_equivariant_port_value import (
    score_learned_equivariant_port_value)


SHUFFLES = 31
SHUFFLE_SEED = 20260820
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_incidence_ranked_rollback_portfolio_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "64ad7ee1c84edc31489d9e4c0045935d04643d760027b61e3e835e64afeb1049"
EXPECTED_AUDIT_DIGEST = \
    "d79f428fd88219f58df938577c88a810afa1f95c7f2054dedd4cf14d465bd0f4"


def _rank(model, rows_by_key, group, stable_indices, cache):
    order = tuple(sorted(map(int, stable_indices), key=lambda stable: (
        -score_learned_equivariant_port_value(
            model, rows_by_key[(group, stable)].graph,
            embedding_cache=cache), stable)))
    return order, rows_by_key[(group, order[0])]


def _shuffle_labels(rows, shuffle):
    rng = random.Random(f"{SHUFFLE_SEED}:{shuffle}")
    shuffled = []
    for group in sorted({row.group for row in rows}):
        group_rows = tuple(row for row in rows if row.group == group)
        labels = [row.exact for row in group_rows]
        rng.shuffle(labels)
        shuffled.extend(Example(
            row.group, row.stable_index, row.graph, label,
            row.correct_sites) for row, label in zip(group_rows, labels))
    return tuple(shuffled)


def _nested_shuffle_score(payload, cache=None):
    shuffle, rows, folds = payload
    shuffled = _shuffle_labels(rows, shuffle)
    by_key = {(row.group, row.stable_index): row for row in rows}
    cache = {} if cache is None else cache
    selected = []
    for source_fold in folds:
        group = int(source_fold["heldout_group"])
        model = _fit(tuple(row for row in shuffled if row.group != group),
                     cache)
        _order, row = _rank(
            model, by_key, group,
            source_fold["retained_stable_indices"], cache)
        selected.append(row)
    return sum(row.exact for row in selected)


def _null_scores_for_indices(indices):
    rows, _dataset = _load_examples()
    folds = load_portfolio()["folds"]
    cache = {}
    return tuple(_nested_shuffle_score((index, rows, folds), cache)
                 for index in indices)


def _parallel_null_scores(workers):
    assignments = tuple(tuple(range(worker, SHUFFLES, workers))
                        for worker in range(workers))
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", "")
    processes = tuple(subprocess.Popen(
        [sys.executable, "-B", str(Path(__file__).resolve()),
         "--null-only", ",".join(map(str, assignment))],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=environment) for assignment in assignments if assignment)
    indexed = {}
    for process in processes:
        output, error = process.communicate()
        if process.returncode:
            raise RuntimeError(
                f"nested null subprocess failed: {error.strip()}")
        for index, score in json.loads(output):
            indexed[int(index)] = int(score)
    if set(indexed) != set(range(SHUFFLES)):
        raise AssertionError("nested null subprocess accounting drift")
    return [indexed[index] for index in range(SHUFFLES)]


def evaluate(*, workers=1):
    rows, dataset = _load_examples()
    portfolio = load_portfolio()
    by_key = {(row.group, row.stable_index): row for row in rows}
    cache = {}
    folds = []
    for source_fold in portfolio["folds"]:
        group = int(source_fold["heldout_group"])
        model = _fit(tuple(row for row in rows if row.group != group), cache)
        retained = tuple(map(int, source_fold["retained_stable_indices"]))
        order, selected = _rank(model, by_key, group, retained, cache)
        folds.append({
            "heldout_group": group,
            "terminal_supply": bool(source_fold["terminal_supply"]),
            "retained_stable_indices": retained,
            "incidence_order": order,
            "selected_stable_index": selected.stable_index,
            "selected_exact": selected.exact,
            "selected_correct_sites": selected.correct_sites,
            "portfolio_contains_exact": bool(
                source_fold["portfolio_contains_exact"]),
            "model_digest": model.model_digest,
        })
    selected_exact = sum(row["selected_exact"] for row in folds)
    selected_correct = sum(row["selected_correct_sites"] for row in folds)
    if workers == 1:
        null_exact = list(_null_scores_for_indices(range(SHUFFLES)))
    else:
        null_exact = _parallel_null_scores(min(workers, SHUFFLES))
    shuffle_p = (1 + sum(value >= selected_exact for value in null_exact)) \
        / (SHUFFLES + 1)
    confirmation = load_incidence_value()["confirmation"]
    exact_confirmation_rank = min(
        confirmation["exact_path_ranks"], default=None)
    body = {
        "schema_version": 1,
        "incidence_dataset_digest": dataset["dataset_digest"],
        "portfolio_audit_digest": portfolio["audit_digest"],
        "development_groups": dataset["development_groups"],
        "supplied_groups": portfolio["supplied_groups"],
        "retained_candidates": portfolio["total_retained_candidates"],
        "maximum_retained_candidates": portfolio["maximum_retained_candidates"],
        "folds": folds,
        "selected_exact_supplied_groups": selected_exact,
        "selected_correct_sites": selected_correct,
        "minimum_exact_groups": 9,
        "minimum_correct_sites": 28,
        "development_gate_passed": selected_exact >= 9 and selected_correct >= 28,
        "shuffle_exact_counts": tuple(null_exact),
        "shuffle_p": shuffle_p,
        "causal_shuffle_gate_passed": shuffle_p <= .05,
        "outer_models_exclude_heldout_nucleus": True,
        "null_models_exclude_heldout_nucleus": True,
        "null_labels_shuffled_within_nucleus": True,
        "consumed_confirmation_candidate_count": confirmation[
            "candidate_count"],
        "consumed_confirmation_selected_first_rank": confirmation[
            "selected_first_rank"],
        "consumed_confirmation_exact_path_rank": exact_confirmation_rank,
        "consumed_confirmation_top_two_contains_exact": (
            exact_confirmation_rank is not None
            and exact_confirmation_rank <= 2),
        "consumed_confirmation_selected_exact": confirmation[
            "selected_end_to_end_exact"],
        "failure_detector_validated_target_free": False,
        "candidate_geometry_unchanged": True,
        "candidate_supply_frozen_before_incidence_ranking": True,
        "target_used_for_fit_ranking_or_portfolio": False,
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
            or body["development_groups"] != 10
            or body["supplied_groups"] != 9
            or body["retained_candidates"] != 19
            or body["maximum_retained_candidates"] != 2
            or not body["development_gate_passed"]
            or body["causal_shuffle_gate_passed"]
            or not body["outer_models_exclude_heldout_nucleus"]
            or not body["null_models_exclude_heldout_nucleus"]
            or not body["null_labels_shuffled_within_nucleus"]
            or body["consumed_confirmation_candidate_count"] != 8
            or not body["consumed_confirmation_top_two_contains_exact"]
            or body["consumed_confirmation_selected_exact"]
            or body["failure_detector_validated_target_free"]
            or not body["candidate_geometry_unchanged"]
            or not body["candidate_supply_frozen_before_incidence_ranking"]
            or body["target_used_for_fit_ranking_or_portfolio"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("incidence-ranked rollback portfolio drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("incidence-ranked rollback result drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("incidence-ranked rollback fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--null-only", default="")
    args = parser.parse_args()
    if args.null_only:
        indices = tuple(map(int, args.null_only.split(",")))
        print(json.dumps(tuple(zip(
            indices, _null_scores_for_indices(indices)))))
        return
    row = evaluate(workers=max(1, args.workers))
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
