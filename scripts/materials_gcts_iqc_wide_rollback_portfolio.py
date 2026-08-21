#!/usr/bin/env python3
"""Preflight a wider target-free IQC rollback portfolio.

The previous two-marking portfolio retained one terminal per marking.  This
audit keeps the two learned orderings and exact candidate geometry unchanged,
then measures fixed widths up to the historical 16-state rollback bound.  The
selected policy is eight candidates per marking (at most sixteen after union),
chosen before typed-discharge fitting so that several independent nuclei
contain both exact and inexact retained alternatives.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_bounded_marking_portfolio import (
    MarkingOrder, bounded_marking_portfolio)
from materials_gcts_child_frontier_graph_value import (
    ChildFrontierGraphExample, ChildFrontierGraphUtilityExample,
    fit_child_frontier_graph_utility_value, fit_child_frontier_graph_value,
    score_child_frontier_graph_utility_value,
    score_child_frontier_graph_value)
from materials_gcts_equivariant_port_fusion_value import percentile_ranks
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
import materials_gcts_iqc_post_self_fed_marking_portfolio as narrow


WIDTHS = (1, 2, 3, 4, 6, 8)
SELECTED_CANDIDATES_PER_MARKING = 8
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_wide_rollback_portfolio_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "adcb33c5d1f7d6f3738763053db8f9159c1df9d3d4733bbbd34a79f0e0996819"
EXPECTED_AUDIT_DIGEST = \
    "a2e377b6c1e795923afb9742e4175df3c27e3fa5b59f983ce321a000e47e1baa"


@dataclass(frozen=True)
class RankedFold:
    heldout_group: int
    candidate_count: int
    candidate_universe_digest: str
    topology_order: tuple[int, ...]
    yield_order: tuple[int, ...]
    labels: tuple[tuple[int, bool, int], ...]
    topology_model_digest: str
    utility_model_digest: str


def _rank_fold(heldout):
    aligned, _base_data, graph_data = narrow._load_aligned()
    baseline = narrow.load_base_result()
    variants = {row.name: row for row in narrow._representations()}
    training = tuple(row for row in aligned if int(row[1].group) != heldout)
    held = tuple(row for row in aligned if int(row[1].group) == heldout)
    base_training = tuple(row[1] for row in training)
    base_held = tuple(row[1] for row in held)
    graph_training = tuple(row[2] for row in training)
    graph_held = tuple(row[2] for row in held)
    source_fold = next(row for row in baseline["folds"]
                       if int(row["heldout_group"]) == heldout)
    scalar = narrow._fit_scalar(
        base_training, variants[source_fold["selected_representation"]],
        int(source_fold["selected_neighbors"]), narrow.FEATURE_NAMES,
        narrow.COLORS, narrow.BASE_SPEC.beta_prior)
    port = narrow._fit_graph(base_training, narrow.BASE_SPEC.graph, None)
    candidates = tuple(narrow._candidate(row, stable)
                       for (stable, _base, _graph), row in zip(
                           held, base_held))
    _scalar, _port, base_scores = narrow._scores(
        scalar, port, float(source_fold["selected_graph_rank_weight"]),
        candidates)
    base_rank = percentile_ranks(base_scores)
    topology = fit_child_frontier_graph_value(tuple(
        ChildFrontierGraphExample(row.group, row.graph, row.exact)
        for row in graph_training), narrow.CHILD_SPEC)
    utility = fit_child_frontier_graph_utility_value(tuple(
        ChildFrontierGraphUtilityExample(
            row.group, row.graph, row.correct_sites)
        for row in graph_training), narrow.CHILD_SPEC)
    topology_rank = percentile_ranks(tuple(
        score_child_frontier_graph_value(topology, row.graph)
        for row in graph_held))
    utility_rank = percentile_ranks(tuple(
        score_child_frontier_graph_utility_value(utility, row.graph)
        for row in graph_held))
    stable = tuple(int(row[0]) for row in held)
    topology_order = tuple(stable[index] for index in sorted(
        range(len(held)), key=lambda index: (
            -topology_rank[index], stable[index])))
    yield_order = tuple(stable[index] for index in sorted(
        range(len(held)), key=lambda index: (
            -(base_rank[index] + utility_rank[index]), stable[index])))
    universe = bounded_marking_portfolio((
        MarkingOrder(narrow.MARKING_IDS[0], topology_order),
        MarkingOrder(narrow.MARKING_IDS[1], yield_order)),
        candidates_per_marking=SELECTED_CANDIDATES_PER_MARKING)
    labels = tuple((int(row.stable_index), bool(row.exact),
                    int(row.correct_sites)) for row in graph_held)
    return RankedFold(
        heldout, len(held), universe.candidate_universe_digest,
        topology_order, yield_order, labels,
        topology.model_digest, utility.model_digest)


def _parallel_folds(workers):
    assignments = tuple(tuple(range(worker, 10, workers))
                        for worker in range(workers))
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", "")
    processes = tuple(subprocess.Popen(
        [sys.executable, "-B", str(Path(__file__).resolve()),
         "--fold-only", ",".join(map(str, assignment))],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=environment) for assignment in assignments if assignment)
    folds = {}
    for process in processes:
        output, error = process.communicate()
        if process.returncode:
            raise RuntimeError(f"wide portfolio fold failed: {error.strip()}")
        for row in json.loads(output):
            folds[int(row["heldout_group"])] = RankedFold(**row)
    if set(folds) != set(range(10)):
        raise AssertionError("wide portfolio fold accounting drift")
    return tuple(folds[index] for index in range(10))


def _portfolio(fold, width):
    return bounded_marking_portfolio((
        MarkingOrder(narrow.MARKING_IDS[0], fold.topology_order),
        MarkingOrder(narrow.MARKING_IDS[1], fold.yield_order)),
        candidates_per_marking=width)


def _width_summary(folds, width):
    retained_total = supplied = exact_supply = mixed = best_sites = 0
    minimum = None
    maximum = 0
    exact_random_selector_probability = 1.
    rows = []
    for fold in folds:
        portfolio = _portfolio(fold, width)
        labels = {stable: (exact, sites)
                  for stable, exact, sites in fold.labels}
        retained = tuple(map(int, portfolio.retained_candidate_ids))
        retained_labels = tuple(labels[stable] for stable in retained)
        all_exact = sum(exact for _stable, exact, _sites in fold.labels)
        exact = sum(value for value, _sites in retained_labels)
        has_supply = all_exact > 0
        is_mixed = 0 < exact < len(retained)
        retained_total += len(retained)
        supplied += has_supply
        exact_supply += bool(exact)
        mixed += is_mixed
        best_sites += max(sites for _exact, sites in retained_labels)
        minimum = len(retained) if minimum is None else min(
            minimum, len(retained))
        maximum = max(maximum, len(retained))
        if is_mixed:
            exact_random_selector_probability *= exact / len(retained)
        rows.append({
            "heldout_group": fold.heldout_group,
            "retained_stable_indices": retained,
            "retained_candidates": len(retained),
            "retained_exact_candidates": exact,
            "mixed_exact_inexact": is_mixed,
            "portfolio_contains_exact": bool(exact),
            "portfolio_best_correct_sites": max(
                sites for _exact, sites in retained_labels),
        })
    return {
        "candidates_per_marking": width,
        "folds": rows,
        "total_retained_candidates": retained_total,
        "minimum_retained_candidates": minimum,
        "maximum_retained_candidates": maximum,
        "supplied_groups": supplied,
        "portfolio_exact_supplied_groups": exact_supply,
        "mixed_exact_inexact_groups": mixed,
        "portfolio_best_correct_sites": best_sites,
        "conditional_random_selector_exact_probability":
            exact_random_selector_probability,
    }


def evaluate(*, workers=1):
    folds = (tuple(_rank_fold(group) for group in range(10))
             if workers == 1 else _parallel_folds(min(workers, 10)))
    widths = tuple(_width_summary(folds, width) for width in WIDTHS)
    selected = next(row for row in widths
                    if row["candidates_per_marking"] ==
                    SELECTED_CANDIDATES_PER_MARKING)
    aligned, base_data, graph_data = narrow._load_aligned()
    body = {
        "schema_version": 1,
        "base_dataset_digest": base_data["dataset_digest"],
        "child_graph_dataset_digest": graph_data["dataset_digest"],
        "source_narrow_portfolio_audit_digest":
            narrow.load_default_result()["audit_digest"],
        "development_groups": len(folds),
        "terminal_examples": len(aligned),
        "marking_ids": narrow.MARKING_IDS,
        "widths": widths,
        "selected_candidates_per_marking":
            SELECTED_CANDIDATES_PER_MARKING,
        "selected_folds": selected["folds"],
        "selected_total_retained_candidates":
            selected["total_retained_candidates"],
        "selected_maximum_retained_candidates":
            selected["maximum_retained_candidates"],
        "selected_exact_supplied_groups":
            selected["portfolio_exact_supplied_groups"],
        "selected_mixed_exact_inexact_groups":
            selected["mixed_exact_inexact_groups"],
        "selected_best_correct_sites":
            selected["portfolio_best_correct_sites"],
        "selected_conditional_random_selector_exact_probability":
            selected["conditional_random_selector_exact_probability"],
        "ranked_fold_digests": tuple((
            fold.heldout_group, fold.candidate_universe_digest,
            fold.topology_model_digest, fold.utility_model_digest)
            for fold in folds),
        "historical_maximum_rollback_width": 16,
        "restores_historical_width_without_exceeding_it":
            selected["maximum_retained_candidates"] <= 16,
        "wider_portfolio_preflight_passed": (
            selected["portfolio_exact_supplied_groups"] == 9
            and selected["mixed_exact_inexact_groups"] >= 5
            and selected["conditional_random_selector_exact_probability"]
            <= .01
            and selected["maximum_retained_candidates"] <= 16),
        "typed_discharge_rollouts_constructed": False,
        "candidate_geometry_unchanged": True,
        "outer_fold_rankers_exclude_ranked_nucleus": True,
        "target_used_for_ranking_or_portfolio": False,
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
            or body["development_groups"] != 10
            or body["terminal_examples"] != 1278
            or tuple(body["marking_ids"]) != narrow.MARKING_IDS
            or tuple(item["candidates_per_marking"]
                     for item in body["widths"]) != WIDTHS
            or body["selected_candidates_per_marking"] != 8
            or not body["restores_historical_width_without_exceeding_it"]
            or not body["wider_portfolio_preflight_passed"]
            or body["typed_discharge_rollouts_constructed"]
            or not body["candidate_geometry_unchanged"]
            or not body["outer_fold_rankers_exclude_ranked_nucleus"]
            or body["target_used_for_ranking_or_portfolio"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("wide rollback portfolio drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("wide rollback audit digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("wide portfolio fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--fold-only", default="")
    args = parser.parse_args()
    if args.fold_only:
        groups = tuple(map(int, args.fold_only.split(",")))
        print(json.dumps(tuple(asdict(_rank_fold(group)) for group in groups)))
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
