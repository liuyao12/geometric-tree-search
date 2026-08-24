#!/usr/bin/env python3
"""Stage-local value for closure-conditioned parent→child port incidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_geometric_port_abstraction import nearest_neighbor_scale
from materials_gcts_iqc_commuting_child_action_marking_fit import (
    CASES, POSITION_TOLERANCE)
from materials_gcts_iqc_commuting_child_supply_benchmark import \
    load_default_result as load_consumed_labels
from materials_gcts_iqc_commuting_closure_model_artifact import \
    load_default_marking as load_parent_marking
from materials_gcts_iqc_commuting_parent_execution import \
    freeze_commuting_second_frontier
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_hybrid_confirmation_preregistration_v4 import (
    CONFIRMATION_CENTER, FIRST_RADIUS, SECOND_RADIUS, SEED_RADIUS)
from materials_gcts_iqc_three_block_channel_execution import \
    _replay_action_set
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_learned_equivariant_port_value import (
    LearnedEquivariantPortExample, LearnedEquivariantPortSpec,
    fit_learned_equivariant_port_value,
    score_learned_equivariant_port_value)
from materials_gcts_parent_child_port_incidence_transition import (
    combine_port_incidence_transition_blocks,
    port_incidence_transition_block)


SPEC = LearnedEquivariantPortSpec(
    interaction_order=3, support_type_weight=0., ridge=10.,
    minimum_feature_groups=2, steps=100, learning_rate=.16,
    objective="pairwise-aggregated")
TOP_K = 16
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_commuting_child_incidence_ablation_v1.json"
EXPECTED_ABLATION_DIGEST = \
    "99707ab0616045938c447d1bfa9263d1126d92cbc13c08d44d29a325b7987fc1"


def _graphs_for_execution(seed, center, execution, runtime, scale):
    grouped = runtime["grouped_vocabulary"]
    source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species))
    graphs = []
    branches = []
    for branch in execution.second_branches:
        parent_state, _orders = _replay_action_set(
            source, runtime, branch.first_actions, execution.radii[0])
        parent = port_incidence_transition_block(
            grouped.vocabulary, grouped.training_group_support,
            source.seed_positions, source.seed_species,
            tuple(point for point, _color in branch.first_actions),
            tuple(color for _point, color in branch.first_actions), "parent")
        start = len(graphs)
        for actions in branch.second_actions:
            child = port_incidence_transition_block(
                grouped.vocabulary, grouped.training_group_support,
                tuple(parent_state.positions), tuple(parent_state.species),
                tuple(point for point, _color in actions),
                tuple(color for _point, color in actions), "child")
            graphs.append(combine_port_incidence_transition_blocks(
                parent, child, distance_scale=scale))
        branches.append({
            "parent": int(branch.first_rank),
            "first_actions": branch.first_actions,
            "second_actions": branch.second_actions,
            "indices": tuple(range(start, len(graphs))),
        })
    return tuple(graphs), tuple(branches)


def _freeze_development(*, workers=4):
    parent_model, parent_artifact = load_parent_marking()
    runtime = load_default_runtime()
    frozen = []
    # All executions and the train-derived length scale freeze first.
    for group, (name, relative, center) in enumerate(CASES):
        source_raw = open(__file__.rsplit("/", 1)[0] + "/" + relative,
                          "rb").read()
        receipt = json.loads(__import__("gzip").decompress(source_raw))["receipt"]
        seed, _ = oracle_crop_fast(center, 9.)
        execution = freeze_commuting_second_frontier(
            center=center, seed_positions=seed.positions,
            seed_species=seed.species, first_radius=receipt["radii"][0],
            second_radius=receipt["radii"][1], marking_model=parent_model,
            workers=workers)
        frozen.append((group, name, center, receipt, seed, execution))
    scale = sum(nearest_neighbor_scale(row[4].positions)
                for row in frozen) / len(frozen)
    geometry = []
    for group, name, center, receipt, seed, execution in frozen:
        graphs, branches = _graphs_for_execution(
            seed, center, execution, runtime, scale)
        geometry.append((group, name, center, receipt, seed, execution,
                         graphs, branches))
    geometry_digest = hashlib.sha256(canonical_json(tuple(
        (group, execution.execution_digest,
         tuple(graph.canonical_digest for graph in graphs))
        for group, _name, _center, _receipt, _seed, execution, graphs,
        _branches in geometry))).hexdigest()

    # Only now are consumed development labels joined.
    examples = []
    branch_records = []
    for (group, _name, center, receipt, _seed, _execution, graphs,
         branches) in geometry:
        target, _ = oracle_crop_fast(center, receipt["radii"][1])
        truth = colored_position_index(
            target.positions, target.species, tolerance=POSITION_TOLERANCE)
        group_example_start = len(examples)
        for branch in branches:
            first_exact = all(colored_action_labels(
                branch["first_actions"], truth,
                tolerance=POSITION_TOLERANCE))
            labels = tuple(bool(first_exact and all(colored_action_labels(
                actions, truth, tolerance=POSITION_TOLERANCE)))
                for actions in branch["second_actions"])
            for index, label in zip(branch["indices"], labels):
                examples.append(LearnedEquivariantPortExample(
                    group, graphs[index], label))
            branch_records.append({
                "group": group, "parent": branch["parent"],
                "indices": tuple(group_example_start + index
                                 for index in branch["indices"]),
                "labels": labels,
            })
    return (tuple(examples), tuple(branch_records), scale, geometry_digest,
            parent_model, parent_artifact)


def _rank(model, examples, branches, cache):
    scores = tuple(score_learned_equivariant_port_value(
        model, row.graph, embedding_cache=cache) for row in examples)
    supplied = total = 0
    ranks = []
    for branch in branches:
        exact = {index for index, label in enumerate(branch["labels"])
                 if label}
        if not exact:
            continue
        total += 1
        order = tuple(sorted(range(len(branch["indices"])), key=lambda i: (
            -scores[branch["indices"][i]], i)))
        rank = min(order.index(index) + 1 for index in exact)
        supplied += rank <= TOP_K
        ranks.append((branch["group"], branch["parent"], rank))
    return supplied, total, tuple(ranks), scores


def evaluate(*, workers=4, interaction_order=3):
    if interaction_order not in (2, 3):
        raise ValueError("interaction order must be two or three")
    spec = replace(SPEC, interaction_order=interaction_order)
    examples, branches, scale, geometry_digest, parent_model, parent_artifact = \
        _freeze_development(workers=workers)
    cache = {}
    folds = []
    for heldout in range(4):
        training = tuple(row for row in examples if row.group != heldout)
        held = tuple(row for row in examples if row.group == heldout)
        held_branches = []
        offset = 0
        source_indices = [index for index, row in enumerate(examples)
                          if row.group == heldout]
        remap = {source: index for index, source in enumerate(source_indices)}
        for branch in branches:
            if branch["group"] == heldout:
                held_branches.append({**branch, "indices": tuple(
                    remap[index] for index in branch["indices"])})
        model = fit_learned_equivariant_port_value(
            training, spec, embedding_cache=cache)
        supplied, total, ranks, _scores = _rank(
            model, held, tuple(held_branches), cache)
        folds.append({
            "heldout_group": heldout,
            "exact_branches_supplied": supplied,
            "exact_branches": total,
            "exact_ranks": ranks,
        })
    final_model = fit_learned_equivariant_port_value(
        examples, spec, embedding_cache=cache)

    # Freeze the fifth consumed geometry and its scores before label receipt.
    seed, _ = oracle_crop_fast(CONFIRMATION_CENTER, SEED_RADIUS)
    execution = freeze_commuting_second_frontier(
        center=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_RADIUS,
        second_radius=SECOND_RADIUS, marking_model=parent_model,
        workers=workers)
    consumed_graphs, consumed_branches = _graphs_for_execution(
        seed, CONFIRMATION_CENTER, execution, load_default_runtime(), scale)
    consumed_examples = tuple(LearnedEquivariantPortExample(
        "consumed-unlabeled", graph, False) for graph in consumed_graphs)
    consumed_scores = tuple(score_learned_equivariant_port_value(
        final_model, row.graph, embedding_cache=cache)
        for row in consumed_examples)
    consumed_receipt_digest = hashlib.sha256(canonical_json((
        execution.execution_digest,
        tuple(graph.canonical_digest for graph in consumed_graphs),
        consumed_scores, final_model.model_digest))).hexdigest()
    labels = load_consumed_labels()
    exact_pairs = {tuple(row) for row in labels["exact_six_action_pairs"]}
    consumed_ranks = []
    for branch in consumed_branches:
        order = tuple(sorted(range(len(branch["indices"])), key=lambda i: (
            -consumed_scores[branch["indices"][i]], i)))
        for parent, child in sorted(exact_pairs):
            if parent == branch["parent"]:
                consumed_ranks.append((parent, child,
                                       order.index(child) + 1))
    body = {
        "schema_version": 1,
        "spec": asdict(spec),
        "top_k": TOP_K,
        "development_examples": len(examples),
        "development_positive_examples": sum(row.successful
                                               for row in examples),
        "development_geometry_digest": geometry_digest,
        "development_folds": folds,
        "development_exact_branches_supplied": sum(
            row["exact_branches_supplied"] for row in folds),
        "development_exact_branches": sum(row["exact_branches"]
                                           for row in folds),
        "train_length_scale": scale,
        "final_model_digest": final_model.model_digest,
        "final_model_features": len(final_model.feature_keys),
        "consumed_candidates": len(consumed_graphs),
        "consumed_unique_graphs": len({graph.canonical_digest
                                       for graph in consumed_graphs}),
        "consumed_exact_ranks": consumed_ranks,
        "consumed_exact_supplied": sum(rank <= TOP_K
                                       for _parent, _child, rank
                                       in consumed_ranks),
        "consumed_receipt_digest": consumed_receipt_digest,
        "candidate_generation_target_used": False,
        "consumed_labels_opened_after_scores": True,
        "diagnostic_uses_consumed_development_labels": True,
        "fresh_confirmation_claimed": False,
        "autonomous_or_exponential_growth_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def _validate_order(row, interaction_order):
    body = dict(row)
    digest = body.pop("result_digest")
    ranks = tuple(tuple(entry) for entry in body["consumed_exact_ranks"])
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["spec"]["interaction_order"] != interaction_order
            or body["top_k"] != TOP_K
            or body["development_examples"] != 3994
            or body["development_positive_examples"] != 95
            or body["development_exact_branches"] != 14
            or body["consumed_candidates"] != 1220
            or body["consumed_unique_graphs"] != 1063
            or len(ranks) != 2
            or body["consumed_exact_supplied"] != 0
            or body["candidate_generation_target_used"]
            or not body["consumed_labels_opened_after_scores"]
            or not body["diagnostic_uses_consumed_development_labels"]
            or body["fresh_confirmation_claimed"]
            or body["autonomous_or_exponential_growth_claimed"]):
        raise AssertionError(
            f"commuting child incidence order-{interaction_order} drift")
    return row


def validate_ablation(row):
    body = dict(row)
    digest = body.pop("ablation_digest")
    orders = body["orders"]
    order2 = _validate_order(orders["2"], 2)
    order3 = _validate_order(orders["3"], 3)
    order2_ranks = sorted(entry[2] for entry in
                          order2["consumed_exact_ranks"])
    order3_ranks = sorted(entry[2] for entry in
                          order3["consumed_exact_ranks"])
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or order2["development_geometry_digest"] !=
            order3["development_geometry_digest"]
            or order2["development_exact_branches_supplied"] != 12
            or order3["development_exact_branches_supplied"] != 9
            or order2_ranks != [69, 71]
            or order3_ranks != [78, 80]
            or body["top_k_gate_passed"]):
        raise AssertionError("commuting child incidence ablation drift")
    if EXPECTED_ABLATION_DIGEST and digest != EXPECTED_ABLATION_DIGEST:
        raise AssertionError("commuting child incidence digest drift")
    return row


def load_default_ablation():
    return validate_ablation(json.loads(DEFAULT_FIXTURE.read_text()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--interaction-order", type=int, choices=(2, 3),
                        default=3)
    args = parser.parse_args()
    print(json.dumps(evaluate(workers=args.workers,
                              interaction_order=args.interaction_order), indent=2,
                     sort_keys=True))
