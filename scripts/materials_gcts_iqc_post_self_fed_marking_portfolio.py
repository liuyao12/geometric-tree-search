#!/usr/bin/env python3
"""Nested two-marking rollback portfolio for post-self-fed IQC terminals."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_bounded_marking_portfolio import (
    MarkingOrder, bounded_marking_portfolio)
from materials_gcts_child_frontier_graph_value import (
    ChildFrontierGraphExample, ChildFrontierGraphUtilityExample,
    fit_child_frontier_graph_utility_value, fit_child_frontier_graph_value,
    score_child_frontier_graph_utility_value,
    score_child_frontier_graph_value)
from materials_gcts_equivariant_port_fusion_value import (
    _fit_graph, _fit_scalar, _scores, percentile_ranks)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import COLORS
from materials_gcts_iqc_post_self_fed_child_graph_value import (
    SPEC as CHILD_SPEC, _load_examples as _load_graph_examples)
from materials_gcts_iqc_post_self_fed_fusion_value import (
    SPEC as BASE_SPEC, _candidate, _load_rows as _load_base_rows,
    _representations, load_default_result as load_base_result)
from materials_gcts_iqc_self_fed_terminal_dataset import FEATURE_NAMES


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_marking_portfolio_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "6f7e1d9d5fa765930cce3b1f2cb7529a571bb0f5df2341e60610dae44570ceb6"
EXPECTED_AUDIT_DIGEST = \
    "61a346528b114f5dbc13108427175fa1c5d0ecea3d3774b2780cb93e3a1872cd"
MARKING_IDS = ("typed-child-topology", "local-section+ordinal-yield")


@dataclass(frozen=True)
class HeldoutPortfolioFold:
    heldout_group: int
    terminal_supply: bool
    exact_terminals: int
    candidate_count: int
    candidate_universe_digest: str
    topology_stable_index: int
    topology_exact: bool
    topology_correct_sites: int
    yield_stable_index: int
    yield_exact: bool
    yield_correct_sites: int
    retained_stable_indices: tuple[int, ...]
    retained_candidates: int
    portfolio_contains_exact: bool
    portfolio_exact_candidates: int
    portfolio_best_correct_sites: int
    posthoc_first_exact_attempt: int | None
    base_fold_model_capacity: tuple[str, int, float]
    child_topology_model_digest: str
    child_utility_model_digest: str


def _load_aligned():
    base_rows, metadata, base_data = _load_base_rows()
    graph_rows, graph_data = _load_graph_examples()
    graph_by_key = {(row.group, row.stable_index): row for row in graph_rows}
    aligned = []
    offsets = {group: 0 for group in range(graph_data["development_groups"])}
    for base in base_rows:
        stable = offsets[int(base.group)]
        offsets[int(base.group)] += 1
        graph = graph_by_key[(int(base.group), stable)]
        correct, exact = metadata[(int(base.group), stable)]
        # Both fixture builders independently replay and validate action
        # colors against the same source terminal digest.  The cross-fixture
        # join therefore needs only the stable row and copied labels.
        if (bool(base.successful) != graph.exact or exact != graph.exact
                or int(correct) != graph.correct_sites):
            raise AssertionError("base/child graph label drift")
        aligned.append((stable, base, graph))
    if any(count == 0 for count in offsets.values()):
        raise AssertionError("empty post-self-fed group")
    return tuple(aligned), base_data, graph_data


def _evaluate_fold(heldout):
    aligned, _base_data, _graph_data = _load_aligned()
    baseline = load_base_result()
    variants = {row.name: row for row in _representations()}
    training = tuple(row for row in aligned if int(row[1].group) != heldout)
    held = tuple(row for row in aligned if int(row[1].group) == heldout)
    base_training = tuple(row[1] for row in training)
    base_held = tuple(row[1] for row in held)
    graph_training = tuple(row[2] for row in training)
    graph_held = tuple(row[2] for row in held)
    fold = next(row for row in baseline["folds"]
                if int(row["heldout_group"]) == heldout)
    scalar = _fit_scalar(
        base_training, variants[fold["selected_representation"]],
        int(fold["selected_neighbors"]), FEATURE_NAMES, COLORS,
        BASE_SPEC.beta_prior)
    port = _fit_graph(base_training, BASE_SPEC.graph, None)
    candidates = tuple(_candidate(row, stable)
                       for (stable, _base, _graph), row in zip(
                           held, base_held))
    _scalar_rank, _port_rank, base_scores = _scores(
        scalar, port, float(fold["selected_graph_rank_weight"]), candidates)
    base_rank = percentile_ranks(base_scores)
    topology = fit_child_frontier_graph_value(tuple(
        ChildFrontierGraphExample(row.group, row.graph, row.exact)
        for row in graph_training), CHILD_SPEC)
    utility = fit_child_frontier_graph_utility_value(tuple(
        ChildFrontierGraphUtilityExample(
            row.group, row.graph, row.correct_sites)
        for row in graph_training), CHILD_SPEC)
    topology_rank = percentile_ranks(tuple(
        score_child_frontier_graph_value(topology, row.graph)
        for row in graph_held))
    utility_rank = percentile_ranks(tuple(
        score_child_frontier_graph_utility_value(utility, row.graph)
        for row in graph_held))
    stable_ids = tuple(row[0] for row in held)
    topology_order = tuple(stable_ids[index] for index in sorted(
        range(len(held)), key=lambda index: (
            -topology_rank[index], stable_ids[index])))
    yield_order = tuple(stable_ids[index] for index in sorted(
        range(len(held)), key=lambda index: (
            -(base_rank[index] + utility_rank[index]), stable_ids[index])))
    portfolio = bounded_marking_portfolio((
        MarkingOrder(MARKING_IDS[0], topology_order),
        MarkingOrder(MARKING_IDS[1], yield_order)),
        candidates_per_marking=1)
    by_stable = {row.stable_index: row for row in graph_held}
    retained = tuple(by_stable[int(index)]
                     for index in portfolio.retained_candidate_ids)
    first_exact = next((index for index, row in enumerate(retained, 1)
                        if row.exact), None)
    top = by_stable[topology_order[0]]
    productive = by_stable[yield_order[0]]
    return HeldoutPortfolioFold(
        heldout, any(row.exact for row in graph_held),
        sum(row.exact for row in graph_held), len(graph_held),
        portfolio.candidate_universe_digest, top.stable_index, top.exact,
        top.correct_sites, productive.stable_index, productive.exact,
        productive.correct_sites, tuple(map(int,
            portfolio.retained_candidate_ids)), len(retained),
        any(row.exact for row in retained), sum(row.exact for row in retained),
        max(row.correct_sites for row in retained), first_exact,
        (str(fold["selected_representation"]),
         int(fold["selected_neighbors"]),
         float(fold["selected_graph_rank_weight"])),
        topology.model_digest, utility.model_digest)


def evaluate(*, workers=1):
    aligned, base_data, graph_data = _load_aligned()
    groups = tuple(range(graph_data["development_groups"]))
    if workers == 1:
        folds = tuple(map(_evaluate_fold, groups))
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            folds = tuple(pool.map(_evaluate_fold, groups))
    all_graph = tuple(row[2] for row in aligned)
    topology = fit_child_frontier_graph_value(tuple(
        ChildFrontierGraphExample(row.group, row.graph, row.exact)
        for row in all_graph), CHILD_SPEC)
    utility = fit_child_frontier_graph_utility_value(tuple(
        ChildFrontierGraphUtilityExample(
            row.group, row.graph, row.correct_sites) for row in all_graph),
        CHILD_SPEC)
    baseline = load_base_result()
    final_payload = (
        baseline["final_model_digest"], topology.model_digest,
        utility.model_digest, MARKING_IDS, 1)
    supplied = sum(fold.terminal_supply for fold in folds)
    exact_supply = sum(fold.portfolio_contains_exact for fold in folds
                       if fold.terminal_supply)
    best_sites = sum(fold.portfolio_best_correct_sites for fold in folds)
    body = {
        "schema_version": 1,
        "base_dataset_digest": base_data["dataset_digest"],
        "child_graph_dataset_digest": graph_data["dataset_digest"],
        "development_groups": len(groups),
        "terminal_examples": len(aligned),
        "marking_ids": MARKING_IDS,
        "candidates_per_marking": 1,
        "folds": [asdict(fold) for fold in folds],
        "supplied_groups": supplied,
        "topology_exact_top_one_groups": sum(
            fold.topology_exact for fold in folds),
        "topology_correct_sites": sum(
            fold.topology_correct_sites for fold in folds),
        "yield_exact_top_one_groups": sum(fold.yield_exact for fold in folds),
        "yield_correct_sites": sum(fold.yield_correct_sites for fold in folds),
        "portfolio_exact_supplied_groups": exact_supply,
        "portfolio_best_correct_sites": best_sites,
        "maximum_retained_candidates": max(
            fold.retained_candidates for fold in folds),
        "total_retained_candidates": sum(
            fold.retained_candidates for fold in folds),
        "maximum_posthoc_attempt_to_exact": max(
            fold.posthoc_first_exact_attempt or 0 for fold in folds),
        "previous_rollback_width": 16,
        "bounded_rollback_supply_gate_passed": (
            supplied == 9 and exact_supply == supplied
            and max(fold.retained_candidates for fold in folds) <= 2
            and best_sites >= 27),
        "autonomous_commit_gate_passed": False,
        "failure_detector_validated_target_free": False,
        "final_topology_model_digest": topology.model_digest,
        "final_utility_model_digest": utility.model_digest,
        "base_fusion_model_digest": baseline["final_model_digest"],
        "final_portfolio_model_digest": hashlib.sha256(
            repr(final_payload).encode()).hexdigest(),
        "candidate_geometry_unchanged": True,
        "identical_candidate_universe_per_marking": True,
        "outer_fold_models_exclude_heldout_nucleus": True,
        "target_used_for_fit_ranking_or_portfolio": False,
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
            or body["development_groups"] != 10
            or body["terminal_examples"] != 1278
            or tuple(body["marking_ids"]) != MARKING_IDS
            or body["candidates_per_marking"] != 1
            or not body["candidate_geometry_unchanged"]
            or not body["identical_candidate_universe_per_marking"]
            or not body["outer_fold_models_exclude_heldout_nucleus"]
            or body["target_used_for_fit_ranking_or_portfolio"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("post-self-fed marking portfolio drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("post-self-fed marking portfolio audit drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("post-self-fed marking portfolio fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.workers < 1:
        raise SystemExit("--workers must be positive")
    row = evaluate(workers=args.workers)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
