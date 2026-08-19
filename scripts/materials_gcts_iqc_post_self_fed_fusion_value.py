#!/usr/bin/env python3
"""Fit a grouped GCTS terminal value on complete post-self-feed IQC blocks."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import itertools
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, EquivariantPortFusionExample,
    EquivariantPortFusionSpec, fit_grouped_equivariant_port_fusion,
    select_equivariant_port_fusion, _fit_graph, _graph_cache_key)
from materials_gcts_iqc_frozen_fusion_artifact import (
    canonical_json, fusion_value_from_payload, fusion_value_payload)
from materials_gcts_iqc_frozen_fusion_runtime import (
    BRANCH_NAMES, COLORS, FEATURE_NAMES as FUSION_FEATURE_NAMES)
from materials_gcts_learned_equivariant_port_value import (
    LearnedEquivariantPortSpec)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE as DATASET_FIXTURE, EXPECTED_DATASET_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_DATASET_SHA256, FEATURE_NAMES,
    SUCCESSOR_FEATURE_NAMES, graph_from_json, load_fixture_json,
    validate_dataset)
from materials_gcts_portfolio_terminal_value import TerminalRepresentation


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_fusion_value_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "c272bbd109c45a51ff90b18b98c54aaa80488525905c843f3ac375d9f63ef6e4"
EXPECTED_AUDIT_DIGEST = \
    "6b9b089a2323255d28036ca74cabbc74547cf443713aea0168fa5cd1ea2e09e0"
EXPECTED_MODEL_DIGEST = \
    "02c233923095b9118d36a85185ad0d07817f97aadc40ed9caece2009140e4e2e"
MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS = 8
MINIMUM_SELECTED_CORRECT_SITES = 27
SPEC = EquivariantPortFusionSpec(
    graph=LearnedEquivariantPortSpec(
        interaction_order=3, support_type_weight=.25, ridge=10.,
        minimum_feature_groups=2, steps=100, learning_rate=.16,
        objective="pairwise-aggregated"),
    neighbors=(1, 3, 5, 9, 15),
    graph_rank_weights=(0., .25, .5, 1., 2.))
_GRAPH_WORKER_ROWS = ()


@dataclass(frozen=True)
class HeldoutSelfFedFusionFold:
    heldout_group: int
    terminal_supply: bool
    exact_terminals: int
    selected_representation: str
    selected_neighbors: int
    selected_graph_rank_weight: float
    selected_stable_index: int
    selected_exact: bool
    selected_correct_sites: int
    top_band_size: int
    top_band_all_exact: bool
    first_exact_rank: int | None


def _representations():
    fusion_count = len(FUSION_FEATURE_NAMES)
    successor = tuple(range(fusion_count, len(FEATURE_NAMES)))
    incidence = tuple(range(fusion_count - 4, fusion_count))
    branch = tuple(range(len(BRANCH_NAMES)))
    return (
        TerminalRepresentation("incidence", incidence),
        TerminalRepresentation("successor", successor),
        TerminalRepresentation("incidence+successor", incidence + successor),
        TerminalRepresentation("branch+successor", branch + successor),
    )


def _load_rows():
    raw, payload = load_fixture_json(DATASET_FIXTURE)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_DATASET_SHA256:
        raise AssertionError("post-self-feed dataset byte drift")
    data = validate_dataset(payload)
    if data["dataset_digest"] != EXPECTED_DATASET_DIGEST:
        raise AssertionError("post-self-feed dataset digest drift")
    rows = []
    metadata = {}
    for group in data["groups"]:
        for row in group["rows"]:
            graph = graph_from_json(row["graph"])
            example = EquivariantPortFusionExample(
                int(row["group"]), tuple(map(float, row["features"])),
                tuple(map(str, row["action_colors"])), graph,
                bool(row["exact"]))
            rows.append(example)
            metadata[(int(row["group"]), int(row["stable_index"]))] = (
                int(row["correct_sites"]), bool(row["exact"]))
    return tuple(rows), metadata, data


def _candidate(example, stable_index):
    return EquivariantPortFusionCandidate(
        example.scalar_features, example.action_colors, example.graph,
        int(stable_index))


def _init_graph_worker(rows):
    global _GRAPH_WORKER_ROWS
    _GRAPH_WORKER_ROWS = rows


def _fit_graph_subset(groups):
    selected = tuple(row for row in _GRAPH_WORKER_ROWS
                     if row.group in groups)
    return (_graph_cache_key(selected, SPEC.graph),
            _fit_graph(selected, SPEC.graph, None))


def _prewarm_graph_cache(rows, groups, workers):
    group_set = tuple(groups)
    subsets = [tuple(group for group in group_set if group not in excluded)
               for excluded in itertools.combinations(group_set, 2)]
    subsets.extend(tuple(group for group in group_set if group != heldout)
                   for heldout in group_set)
    subsets.append(group_set)
    if workers == 1:
        _init_graph_worker(rows)
        fitted = tuple(map(_fit_graph_subset, subsets))
    else:
        context = multiprocessing.get_context("fork")
        with ProcessPoolExecutor(
                max_workers=workers, mp_context=context,
                initializer=_init_graph_worker, initargs=(rows,)) as pool:
            fitted = tuple(pool.map(_fit_graph_subset, subsets))
    return dict(fitted)


def evaluate(*, workers=1):
    rows, metadata, data = _load_rows()
    groups = tuple(range(data["development_groups"]))
    representations = _representations()
    graph_cache = _prewarm_graph_cache(rows, groups, workers)
    folds = []
    for heldout in groups:
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        model, inner = fit_grouped_equivariant_port_fusion(
            training, feature_names=FEATURE_NAMES, color_keys=COLORS,
            representations=representations, spec=SPEC,
            graph_model_cache=graph_cache)
        candidates = tuple(_candidate(row, index)
                           for index, row in enumerate(held))
        selection = select_equivariant_port_fusion(model, candidates)
        exact = tuple(row.successful for row in held)
        order = tuple(sorted(range(len(held)), key=lambda index: (
            -selection.fused_scores[index], index)))
        first_exact = next((rank for rank, index in enumerate(order, 1)
                            if exact[index]), None)
        stable = selection.stable_index
        correct, selected_exact = metadata[(heldout, stable)]
        folds.append(HeldoutSelfFedFusionFold(
            heldout, any(exact), sum(exact), inner.selected_representation,
            inner.selected_neighbors, inner.selected_graph_rank_weight,
            stable, selected_exact, correct, len(selection.top_indices),
            all(exact[index] for index in selection.top_indices), first_exact))

    model, audit = fit_grouped_equivariant_port_fusion(
        rows, feature_names=FEATURE_NAMES, color_keys=COLORS,
        representations=representations, spec=SPEC,
        graph_model_cache=graph_cache)
    model_payload = fusion_value_payload(model)
    restored = fusion_value_from_payload(model_payload)
    if restored.model_digest != model.model_digest:
        raise AssertionError("post-self-feed model serialization drift")
    nested_selected_exact = sum(fold.selected_exact for fold in folds)
    nested_selected_correct = sum(
        fold.selected_correct_sites for fold in folds)
    body = {
        "schema_version": 1,
        "dataset_digest": data["dataset_digest"],
        "development_groups": len(groups),
        "terminal_examples": len(rows),
        "exact_examples": sum(row.successful for row in rows),
        "supplied_groups": sum(fold.terminal_supply for fold in folds),
        "nested_selected_exact_groups": nested_selected_exact,
        "nested_selected_correct_sites": nested_selected_correct,
        "nested_top_band_all_exact_groups": sum(
            fold.top_band_all_exact for fold in folds),
        "nested_first_exact_rank_sum": sum(
            fold.first_exact_rank or 0 for fold in folds),
        "folds": [asdict(fold) for fold in folds],
        "final_selected_representation": audit.selected_representation,
        "final_selected_neighbors": audit.selected_neighbors,
        "final_graph_rank_weight": audit.selected_graph_rank_weight,
        "final_model_digest": model.model_digest,
        "final_model_payload": model_payload,
        "unique_cached_graph_fits": len(graph_cache),
        "graph_fit_workers": workers,
        "minimum_selected_exact_supplied_groups":
            MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS,
        "minimum_selected_correct_sites": MINIMUM_SELECTED_CORRECT_SITES,
        "development_gate_passed": (
            nested_selected_exact >= MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS
            and nested_selected_correct >= MINIMUM_SELECTED_CORRECT_SITES),
        "candidate_geometry_unchanged": True,
        "target_used_for_candidate_or_features": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    digest = hashlib.sha256(canonical_json(body)).hexdigest()
    return {**body, "audit_digest": digest}


def validate_result(row):
    body = dict(row)
    digest = body.pop("audit_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or body["dataset_digest"] != EXPECTED_DATASET_DIGEST
            or body["development_groups"] != 10
            or body["terminal_examples"] != 1278
            or body["exact_examples"] != 142
            or body["minimum_selected_exact_supplied_groups"] !=
               MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS
            or body["minimum_selected_correct_sites"] !=
               MINIMUM_SELECTED_CORRECT_SITES
            or body["development_gate_passed"] != (
                body["nested_selected_exact_groups"] >=
                MINIMUM_SELECTED_EXACT_SUPPLIED_GROUPS
                and body["nested_selected_correct_sites"] >=
                MINIMUM_SELECTED_CORRECT_SITES)
            or body["target_used_for_candidate_or_features"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("post-self-feed fusion audit drift")
    restored = fusion_value_from_payload(body["final_model_payload"])
    if restored.model_digest != body["final_model_digest"]:
        raise AssertionError("invalid frozen post-self-feed fusion model")
    if (EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST
            or EXPECTED_MODEL_DIGEST and body["final_model_digest"] !=
               EXPECTED_MODEL_DIGEST):
        raise AssertionError("post-self-feed result fixture drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("post-self-feed result fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.workers <= 0:
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
