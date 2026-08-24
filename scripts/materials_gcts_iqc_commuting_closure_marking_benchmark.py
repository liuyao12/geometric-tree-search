#!/usr/bin/env python3
"""Grouped development audit of a commuting-frontier marking channel."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_colored_position_scorer import (
    colored_action_labels, colored_position_index)
from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, EquivariantPortFusionExample)
from materials_gcts_iqc_commuting_closure_marking import (
    fit_commuting_closure_marking, select_commuting_closure_marking)
from materials_gcts_iqc_commuting_frontier_closure import \
    complete_first_frontier_with_commuting_closure
from materials_gcts_iqc_frozen_fusion_runtime import action_key, \
    load_default_runtime
from materials_gcts_iqc_hybrid_confirmation_preregistration_v4 import (
    CONFIRMATION_CENTER, FIRST_RADIUS, SEED_RADIUS)
from materials_gcts_iqc_hybrid_confirmation_v4 import \
    load_default_result as load_v4_result
from materials_gcts_iqc_joint_child_action_marking_fit import CASES
from materials_gcts_iqc_parent_balanced_confirmation_preregistration import \
    canonical_json
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_commuting_closure_marking_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "f25b164e15d4abadd878c4c07bd100d5cec6fb406cf96e1e11e5f4bf78f0421e"
EXPECTED_RESULT_DIGEST = \
    "e0c1162f4486f75155ffdebd2c26742682132f3704cf32b94739652ffeb135f1"
BEAM_WIDTH = 8


def _freeze_candidates(center, first_radius):
    seed, _ = oracle_crop_fast(center, SEED_RADIUS)
    runtime = load_default_runtime()
    frontier = complete_first_frontier_with_commuting_closure(
        center=center, seed_positions=seed.positions,
        seed_species=seed.species, radius=first_radius, runtime=runtime,
        action_count=3, initial_action_width=8,
        maximum_action_universe=8)
    closure_keys = {action_key(state.actions)
                    for state in frontier.closure.states}
    indices = tuple(index for index, state in enumerate(frontier.states)
                    if action_key(state.actions) in closure_keys)
    candidates = tuple(frontier.candidates[index] for index in indices)
    actions = tuple(action_key(frontier.states[index].actions)
                    for index in indices)
    if (frontier.target_used or frontier.closure.target_used or
            len(candidates) != 56 or len(set(actions)) != len(actions)):
        raise AssertionError("commuting candidate freeze drift")
    digest = hashlib.sha256(canonical_json(actions)).hexdigest()
    return runtime, frontier, candidates, actions, digest


def _labels(actions, positions, species):
    truth = colored_position_index(positions, species, tolerance=1e-5)
    return tuple(all(colored_action_labels(
        row, truth, tolerance=1e-5)) for row in actions)


def _examples(group, candidates, labels):
    return tuple(EquivariantPortFusionExample(
        group, row.scalar_features, row.action_colors, row.graph,
        bool(success)) for row, success in zip(candidates, labels))


def _rank(model, frontier, candidates):
    selection = select_commuting_closure_marking(
        model, frontier, width=len(candidates))
    local = {global_index: local_index for local_index, global_index in
             enumerate(selection.candidate_indices)}
    return tuple(local[index] for index in selection.ranked_candidate_indices)


def fit_default_model():
    """Fit only from the four already-consumed development nuclei."""
    frozen = []
    source_hashes = []
    # Every development candidate set is frozen before its already-consumed
    # target is reopened for labels.
    for name, relative, center in CASES:
        source_raw = (ROOT / relative).read_bytes()
        receipt = json.loads(gzip.decompress(source_raw))["receipt"]
        runtime, frontier, candidates, actions, digest = \
            _freeze_candidates(center, receipt["radii"][0])
        target, _ = oracle_crop_fast(center, receipt["radii"][0])
        labels = _labels(actions, target.positions, target.species)
        frozen.append((name, candidates, actions, labels, digest, frontier))
        source_hashes.append(hashlib.sha256(source_raw).hexdigest())
    examples = tuple(row for name, candidates, _actions, labels, _digest,
                     _frontier in frozen
                     for row in _examples(name, candidates, labels))
    runtime = load_default_runtime()
    model, audit = fit_commuting_closure_marking(
        examples, feature_names=runtime["fusion_model"].feature_names,
        color_keys=runtime["fusion_model"].color_keys)
    return model, audit, tuple(frozen), examples, tuple(source_hashes)


def evaluate():
    model, audit, frozen, examples, source_hashes = fit_default_model()
    runtime = load_default_runtime()
    fold_rows = []
    for (held_name, held_candidates, _held_actions, held_labels, digest,
         held_frontier) in frozen:
        training = tuple(row for row in examples if row.group != held_name)
        model, audit = fit_commuting_closure_marking(
            training, feature_names=runtime["fusion_model"].feature_names,
            color_keys=runtime["fusion_model"].color_keys)
        order = _rank(model, held_frontier, held_candidates)
        exact_indices = tuple(index for index, value
                              in enumerate(held_labels) if value)
        fold_rows.append({
            "heldout": held_name,
            "candidate_digest": digest,
            "exact_candidates": len(exact_indices),
            "top8_exact": sum(held_labels[index] for index in
                              order[:BEAM_WIDTH]),
            "first_exact_rank": min((order.index(index) + 1
                                     for index in exact_indices),
                                    default=0),
            "selected_representation": audit.selected_representation,
            "selected_neighbors": audit.selected_neighbors,
            "selected_graph_rank_weight":
                audit.selected_graph_rank_weight,
            "model_digest": model.model_digest,
        })
    # Freeze the candidate set for the now-consumed V4 nucleus before loading
    # its posthoc target labels from the immutable result fixture.
    _runtime, fresh_frontier, fresh_candidates, fresh_actions, fresh_digest = \
        _freeze_candidates(CONFIRMATION_CENTER, FIRST_RADIUS)
    fresh_result = load_v4_result()
    fresh_labels = _labels(
        fresh_actions,
        tuple(tuple(point) for point, _species
              in fresh_result["target_sites"]),
        tuple(species for _point, species in fresh_result["target_sites"]))
    fresh_order = _rank(model, fresh_frontier, fresh_candidates)
    fresh_exact = tuple(index for index, value
                        in enumerate(fresh_labels) if value)
    body = {
        "schema_version": 1,
        "development_groups": len(frozen),
        "development_examples": len(examples),
        "development_positive_examples": sum(row.successful
                                               for row in examples),
        "source_fixture_sha256": source_hashes,
        "folds": fold_rows,
        "folds_with_exact_top8": sum(row["top8_exact"] > 0
                                     for row in fold_rows),
        "development_gate_passed": all(
            row["top8_exact"] > 0 for row in fold_rows),
        "selected_representation": audit.selected_representation,
        "selected_neighbors": audit.selected_neighbors,
        "selected_graph_rank_weight": audit.selected_graph_rank_weight,
        "model_digest": model.model_digest,
        "fresh_candidate_digest": fresh_digest,
        "fresh_candidates": len(fresh_candidates),
        "fresh_exact_candidates": len(fresh_exact),
        "fresh_top8_exact": sum(fresh_labels[index]
                                for index in fresh_order[:BEAM_WIDTH]),
        "fresh_first_exact_rank": min((fresh_order.index(index) + 1
                                       for index in fresh_exact), default=0),
        "consumed_fresh_diagnostic_supplied": any(
            fresh_labels[index] for index in fresh_order[:BEAM_WIDTH]),
        "fresh_candidate_geometry_unchanged": True,
        "candidate_generation_target_used": False,
        "fresh_target_opened_only_after_candidate_freeze": True,
        "consumed_development_and_diagnostic_only": True,
        "future_confirmation_claimed": False,
        "autonomous_or_exponential_growth_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row, *, pin=True):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            row["candidate_generation_target_used"] or
            not row["fresh_target_opened_only_after_candidate_freeze"] or
            not row["consumed_development_and_diagnostic_only"] or
            row["future_confirmation_claimed"] or
            row["autonomous_or_exponential_growth_claimed"] or
            row["development_groups"] != 4 or
            row["development_examples"] != 224 or
            not row["development_gate_passed"] or
            row["fresh_candidates"] != 56 or
            row["fresh_exact_candidates"] < 1 or
            not row["consumed_fresh_diagnostic_supplied"]):
        raise AssertionError("commuting closure marking audit drift")
    if pin and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("commuting closure marking result drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("commuting closure marking fixture drift")
    return validate_result(json.loads(raw))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    row = validate_result(evaluate(), pin=False) if args.live \
        else load_default_result()
    print(json.dumps(row, indent=2, sort_keys=True))
