#!/usr/bin/env python3
"""Freeze target-free obligation trajectories for the consumed IQC confirmation.

The original one-shot fixture intentionally retained only trajectory digests.
This companion rebuilds the same seed, exact candidates, portfolio, and
rollouts, verifies the already-published target-free receipt byte-for-byte,
and stores the identity-free relational transitions needed to audit a new
marking representation.  It never constructs or imports a confirmation
target and contains no correctness labels.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_dual_rank_terminal_portfolio import (
    select_dual_rank_terminal_portfolio)
from materials_gcts_iqc_port_obligation_automaton_audit import SPEC
from materials_gcts_iqc_port_obligation_confirmation import (
    FrozenCandidateTrajectory, _fit_frozen_automaton, _seed_crop)
from materials_gcts_iqc_port_obligation_confirmation_preregistration import (
    CANDIDATES_PER_BASE_RANKER, CONFIRMATION_CENTER,
    MAXIMUM_FROZEN_CANDIDATES, TARGET_RADIUS, validate_preregistration)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius, _freeze_at_radius)
from materials_gcts_iqc_wide_typed_port_discharge_dataset import _rollout
from materials_gcts_iqc_frozen_fusion_runtime import (
    action_key, load_default_runtime)
from materials_gcts_port_obligation_automaton import (
    score_port_obligation_trajectory)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_port_obligation_confirmation_trajectories_v1.json.gz"

# These values were frozen before this companion existed.  They are copied
# from the target-free receipt embedded in the consumed confirmation result;
# no target geometry or target-derived label is needed to verify them.
EXPECTED_TARGET_FREE_RECEIPT_DIGEST = \
    "bae0f2e72420c8f7d6e1e89dcbc75342882a9da4fdb2e64fdb88ec7e40124983"
EXPECTED_CANDIDATE_DIGEST = \
    "027494baec61cb8a1cedf7aef41be52fd49893a1b1067ab9a89a6937e1766628"
EXPECTED_PORTFOLIO_DIGEST = \
    "253bb322163ccb35e884ed7525588b81c31dd007964fa73dd31f865339a58bc2"
EXPECTED_FIXTURE_SHA256 = \
    "f0df9cd365000afd96ca6b4513cbf0e0da42cb9e354e65374186faa90101b290"
EXPECTED_DATASET_DIGEST = \
    "0b6b2e793c34ff997ca3406ab29cb40ec9aedb428f0dd64576969b1e921101c4"


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def build_dataset():
    protocol = validate_preregistration()
    model = _fit_frozen_automaton()
    seed = _seed_crop()
    if not seed.positions:
        raise AssertionError("confirmation seed is empty")
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=CONFIRMATION_CENTER,
        seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species),
    )
    nucleus = _freeze_at_radius(
        runtime, CONFIRMATION_CENTER, seed, TARGET_RADIUS)
    states, counts = _complete_states_at_radius(
        source, runtime, TARGET_RADIUS)
    states_by_action = {action_key(row.actions): row for row in states}
    if tuple(counts) != tuple(nucleus.candidate_counts_by_depth) or \
            len(states_by_action) != len(nucleus.terminals):
        raise AssertionError("complete terminal/state accounting drift")
    portfolio = select_dual_rank_terminal_portfolio(
        tuple(row.actions for row in nucleus.terminals),
        nucleus.scalar_order,
        nucleus.fusion_order,
        per_channel_budget=CANDIDATES_PER_BASE_RANKER,
    )
    retained = tuple(portfolio.selected_candidate_ids)
    if not retained or len(retained) > MAXIMUM_FROZEN_CANDIDATES:
        raise AssertionError("frozen candidate portfolio bound failed")

    geometry_rows = []
    receipt_rows = []
    for actions in retained:
        state = states_by_action[tuple(actions)]
        trace, transitions = _rollout(
            source, state, runtime, relational=True)
        transitions = tuple(transitions)
        score, coverage = score_port_obligation_trajectory(
            model, transitions)
        receipt = FrozenCandidateTrajectory(
            tuple(actions), score, coverage,
            int(trace["accepted_children"]),
            bool(trace["fixed_point_reached"]),
            _digest(trace), _digest(transitions),
        )
        receipt_rows.append(receipt)
        geometry_rows.append({
            "action_key": tuple(actions),
            "trace": trace,
            "transitions": transitions,
            "trace_digest": receipt.trace_digest,
            "transition_digest": receipt.transition_digest,
        })
    receipt_rows = tuple(sorted(
        receipt_rows, key=lambda row: repr(row.action_key)))
    geometry_rows = tuple(sorted(
        geometry_rows, key=lambda row: repr(row["action_key"])))
    ranked = tuple(sorted(receipt_rows, key=lambda row: (
        -row.automaton_score, repr(row.action_key))))
    receipt_body = {
        "seed_atoms": len(seed.positions),
        "candidate_counts_by_depth": tuple(counts),
        "complete_terminal_count": len(states),
        "retained_candidates": len(retained),
        "retained_action_keys": tuple(retained),
        "candidate_digest": nucleus.candidate_digest,
        "portfolio_digest": portfolio.selection_digest,
        "trajectories": tuple(asdict(row) for row in receipt_rows),
        "ranked_action_keys": tuple(row.action_key for row in ranked),
        "selected_action_key": ranked[0].action_key,
        "selected_rollout_steps": ranked[0].rollout_steps,
        "model_digest": model.model_digest,
        "target_used": False,
    }
    receipt_digest = _digest(receipt_body)
    if (receipt_digest != EXPECTED_TARGET_FREE_RECEIPT_DIGEST
            or nucleus.candidate_digest != EXPECTED_CANDIDATE_DIGEST
            or portfolio.selection_digest != EXPECTED_PORTFOLIO_DIGEST):
        raise AssertionError("published target-free confirmation receipt drift")

    body = {
        "schema_version": 1,
        "source_preregistration_digest": protocol.manifest_digest,
        "source_target_free_receipt_digest": receipt_digest,
        "source_candidate_digest": nucleus.candidate_digest,
        "source_portfolio_digest": portfolio.selection_digest,
        "automaton_spec": asdict(SPEC),
        "confirmation_center": CONFIRMATION_CENTER,
        "seed_atoms": len(seed.positions),
        "candidate_counts_by_depth": tuple(counts),
        "complete_terminal_count": len(states),
        "retained_candidates": len(geometry_rows),
        "geometry_rows": geometry_rows,
        "geometry_rows_digest": _digest(geometry_rows),
        "target_imported_or_constructed": False,
        "target_labels_serialized": False,
        "candidate_geometry_changed": False,
        "published_target_free_receipt_reproduced": True,
    }
    return {**body, "dataset_digest": _digest(body)}


def validate_dataset(row):
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (_digest(body) != digest
            or body["source_target_free_receipt_digest"] !=
            EXPECTED_TARGET_FREE_RECEIPT_DIGEST
            or body["source_candidate_digest"] != EXPECTED_CANDIDATE_DIGEST
            or body["source_portfolio_digest"] != EXPECTED_PORTFOLIO_DIGEST
            or body["retained_candidates"] != 13
            or body["target_imported_or_constructed"]
            or body["target_labels_serialized"]
            or body["candidate_geometry_changed"]
            or not body["published_target_free_receipt_reproduced"]):
        raise AssertionError("confirmation trajectory companion drift")
    if EXPECTED_DATASET_DIGEST and digest != EXPECTED_DATASET_DIGEST:
        raise AssertionError("confirmation trajectory dataset digest drift")
    return row


def load_default_dataset(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("confirmation trajectory fixture byte drift")
    return validate_dataset(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write and DEFAULT_FIXTURE.exists():
        raise RuntimeError("target-free trajectory fixture already exists")
    row = build_dataset()
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
