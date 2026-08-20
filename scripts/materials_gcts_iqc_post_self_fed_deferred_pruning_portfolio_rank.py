#!/usr/bin/env python3
"""Consumed-target rank audit for the exact deferred-pruning IQC branch.

The earlier diagnostic identifies one exact first-block state at fused rank
eight.  This audit replays that already-consumed development state, enumerates
its complete second-block tree without a target, and freezes the full orders
of the existing base, topology, utility, and topology/yield portfolio values.
Only afterward is the consumed target reconstructed to report the ranks of
the exact actions.  It is a beam-design diagnostic, never a confirmation.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_child_frontier_graph_value import (
    ChildFrontierGraphExample, ChildFrontierGraphUtilityExample,
    fit_child_frontier_graph_utility_value, fit_child_frontier_graph_value,
    score_child_frontier_graph_utility_value,
    score_child_frontier_graph_value)
from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, percentile_ranks,
    select_equivariant_port_fusion)
from materials_gcts_iqc_frozen_fusion_artifact import (
    canonical_json, fusion_value_from_payload)
from materials_gcts_iqc_post_self_fed_child_graph_value import (
    SPEC as CHILD_SPEC, _load_examples as _load_graph_examples)
from materials_gcts_iqc_post_self_fed_deferred_pruning_diagnostic import (
    _key, load_default_result as load_deferred_result)
from materials_gcts_iqc_post_self_fed_fusion_value import (
    load_default_result as load_base_result)
from materials_gcts_iqc_post_self_fed_marking_portfolio import (
    load_default_result as load_portfolio_result)
from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    _colored_digest, _replay_first_terminal, _second_block_candidates)
from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS, SEED_RADIUS)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_terminal_dataset import OUTER_ORACLE_LIFT_BOUND
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_deferred_pruning_portfolio_rank_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "a4a7807e26633b52c3d7b7e3ad5631da25249574acdb9a036bcd0f687eea043e"
EXPECTED_RESULT_DIGEST = \
    "7669647664e941c4bf1b8f2df900904c14a89b8edfb6c72e7e97e52f0a8cda78"


def _orders(rows):
    base = load_base_result()
    base_model = fusion_value_from_payload(base["final_model_payload"])
    portfolio = load_portfolio_result()
    graph_rows, _graph_data = _load_graph_examples()
    topology = fit_child_frontier_graph_value(tuple(
        ChildFrontierGraphExample(row.group, row.graph, row.exact)
        for row in graph_rows), CHILD_SPEC)
    utility = fit_child_frontier_graph_utility_value(tuple(
        ChildFrontierGraphUtilityExample(
            row.group, row.graph, row.correct_sites)
        for row in graph_rows), CHILD_SPEC)
    if (topology.model_digest != portfolio["final_topology_model_digest"]
            or utility.model_digest !=
            portfolio["final_utility_model_digest"]
            or base_model.model_digest != portfolio["base_fusion_model_digest"]):
        raise AssertionError("frozen portfolio model drift")
    base_candidates = tuple(EquivariantPortFusionCandidate(
        row["features"], row["colors"], row["partial_graph"],
        row["stable_index"]) for row in rows)
    base_scores = select_equivariant_port_fusion(
        base_model, base_candidates).fused_scores
    topology_scores = tuple(score_child_frontier_graph_value(
        topology, row["child_graph"]) for row in rows)
    utility_scores = tuple(score_child_frontier_graph_utility_value(
        utility, row["child_graph"]) for row in rows)
    base_percentile = percentile_ranks(base_scores)
    utility_percentile = percentile_ranks(utility_scores)
    yield_scores = tuple(left + right for left, right in
                         zip(base_percentile, utility_percentile))

    def order(scores):
        return tuple(rows[index]["stable_index"] for index in sorted(
            range(len(rows)), key=lambda index: (
                -scores[index], rows[index]["stable_index"])))
    return {
        "base": order(base_scores),
        "typed_child_topology": order(topology_scores),
        "ordinal_utility": order(utility_scores),
        "local_section_ordinal_yield": order(yield_scores),
    }


def build_exact_second_frontier():
    """Rebuild the consumed exact branch without constructing its target."""
    deferred = load_deferred_result()
    exact_sources = tuple(row for row in deferred["scored_sources"]
                          if row["first_exact"])
    if len(exact_sources) != 1:
        raise AssertionError("expected one consumed exact first-block source")
    exact_source = exact_sources[0]
    receipt_source = deferred["receipt"]["second_sources"][
        exact_source["first_rank"] - 1]
    if receipt_source["first_stable_index"] != \
            exact_source["first_stable_index"]:
        raise AssertionError("deferred source identity drift")

    seed_physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SEED_RADIUS)
    seed_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND, seed_physical)
    seed = _crop(seed_oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-deferred-rank-consumed-seed")
    from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
    runtime = load_default_runtime()
    seed_source = SimpleNamespace(
        group=CONFIRMATION_CENTER, seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species))
    first_actions = tuple((tuple(point), str(color))
                          for point, color in receipt_source["first_actions"])
    first_state = _replay_first_terminal(
        seed_source, runtime, first_actions)
    second_source = SimpleNamespace(
        group=CONFIRMATION_CENTER,
        seed_positions=tuple(first_state.positions),
        seed_species=tuple(first_state.species))
    states, counts = _complete_states_at_radius(
        second_source, runtime, SECOND_BLOCK_RADIUS)
    from materials_gcts_iqc_frozen_fusion_runtime import action_key
    states = tuple(sorted(states, key=lambda state: action_key(state.actions)))
    rows, _retained, candidate_digest, model_digests = \
        _second_block_candidates(second_source, states, runtime)
    return {
        "deferred": deferred,
        "exact_source": exact_source,
        "receipt_source": receipt_source,
        "seed": seed,
        "runtime": runtime,
        "second_source": second_source,
        "states": states,
        "counts": tuple(counts),
        "rows": rows,
        "candidate_digest": candidate_digest,
        "model_digests": model_digests,
    }


def evaluate():
    rebuilt = build_exact_second_frontier()
    exact_source = rebuilt["exact_source"]
    seed = rebuilt["seed"]
    rows = rebuilt["rows"]
    counts = rebuilt["counts"]
    candidate_digest = rebuilt["candidate_digest"]
    model_digests = rebuilt["model_digests"]
    orders = _orders(rows)
    receipt = {
        "schema_version": 1,
        "consumed_first_rank": exact_source["first_rank"],
        "consumed_first_stable_index": exact_source["first_stable_index"],
        "seed_digest": _colored_digest(seed.positions, seed.species),
        "second_candidate_counts": tuple(counts),
        "second_candidate_count": len(rows),
        "second_candidate_digest": candidate_digest,
        "orders": orders,
        "model_digests": model_digests,
        "target_open_count_before_receipt": 0,
        "target_used": False,
    }
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()

    physical = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    target = _crop(oracle, CONFIRMATION_CENTER, SECOND_BLOCK_RADIUS,
                   "IQC-deferred-rank-consumed-target")
    truth = {_key(point): str(color) for point, color in
             zip(target.positions, target.species)}
    exact_stable_indices = tuple(row["stable_index"] for row in rows
                                 if all(truth.get(_key(point)) == color
                                        for point, color in
                                        row["state"].actions))
    rank_by_marking = {
        name: tuple(order.index(stable) + 1
                    for stable in exact_stable_indices)
        for name, order in orders.items()}
    union_rank = {
        stable: min(rank_by_marking["typed_child_topology"][index],
                    rank_by_marking["local_section_ordinal_yield"][index])
        for index, stable in enumerate(exact_stable_indices)}
    minimum_per_marking_depth = min(union_rank.values())
    body = {
        "schema_version": 1,
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "target_open_count": 1,
        "target_atoms": len(target.positions),
        "exact_second_stable_indices": exact_stable_indices,
        "exact_ranks_by_marking": rank_by_marking,
        "exact_union_ranks": tuple(tuple(item) for item in
                                   sorted(union_rank.items())),
        "minimum_per_marking_depth_for_exact_supply":
            minimum_per_marking_depth,
        "maximum_portfolio_actions_at_minimum_depth":
            2 * minimum_per_marking_depth,
        "current_top_one_per_marking_retains_exact":
            minimum_per_marking_depth <= 1,
        "candidate_geometry_unchanged": True,
        "target_used_for_ordering": False,
        "consumed_target_diagnostic_only": True,
        "fresh_confirmation_claimed": False,
        "autonomous_commit_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["receipt"]["target_used"]
            or body["receipt"]["target_open_count_before_receipt"] != 0
            or hashlib.sha256(canonical_json(body["receipt"])).hexdigest()
            != body["receipt_digest"]
            or body["target_open_count"] != 1
            or not body["candidate_geometry_unchanged"]
            or body["target_used_for_ordering"]
            or not body["consumed_target_diagnostic_only"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_commit_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("deferred portfolio-rank diagnostic drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("deferred portfolio-rank result digest drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("deferred portfolio-rank fixture byte drift")
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
