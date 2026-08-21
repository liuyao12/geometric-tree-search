#!/usr/bin/env python3
"""One-shot sealed confirmation of the IQC port-obligation automaton."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_dual_rank_terminal_portfolio import (
    select_dual_rank_terminal_portfolio)
from materials_gcts_iqc_port_obligation_automaton_audit import (
    SPEC, _labelled, _rows)
from materials_gcts_iqc_port_obligation_confirmation_preregistration import (
    ACTION_REACH_SCHEDULE, CANDIDATES_PER_BASE_RANKER,
    CONFIRMATION_CENTER, EXPECTED_AUTOMATON_AUDIT_DIGEST,
    EXPECTED_AUTOMATON_MODEL_DIGEST, EXPECTED_MANIFEST_DIGEST,
    EXPECTED_TRAINING_DATASET_DIGEST, EXPECTED_TRAINING_GEOMETRY_DIGEST,
    MAXIMUM_FROZEN_CANDIDATES, ORACLE_LIFT_BOUND, ROLLOUT_HORIZON,
    ROLLOUT_RADIUS, SEED_RADIUS, SUCCESS_GATE, TARGET_OPEN_LIMIT,
    TARGET_RADIUS, validate_preregistration)
from materials_gcts_iqc_relational_port_discharge_dataset import (
    relational_transition)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius, _freeze_at_radius)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_iqc_wide_typed_port_discharge_dataset import _rollout
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_iqc_frozen_fusion_runtime import (
    action_key, load_default_runtime)
from materials_gcts_port_obligation_automaton import (
    fit_port_obligation_automaton, score_port_obligation_trajectory)


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixtures/iqc_port_obligation_confirmation_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "35d8eaf1e3d0fb55bc69133ee9cecf03e5bba551907bc4ce69bc492530e1e524"
EXPECTED_RESULT_DIGEST = \
    "8258ee6a60326fd0723de0f8d74b6f8ee59dcb0bbc60eeb51792874385012f77"


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _site_key(point):
    return tuple(round(float(value), 6) for value in point)


@dataclass(frozen=True)
class FrozenCandidateTrajectory:
    action_key: tuple
    automaton_score: float
    recognized_state_fraction: float
    rollout_steps: int
    fixed_point_reached: bool
    trace_digest: str
    transition_digest: str


@dataclass(frozen=True)
class FrozenConfirmationExecution:
    seed_atoms: int
    candidate_counts_by_depth: tuple[int, ...]
    complete_terminal_count: int
    retained_candidates: int
    retained_action_keys: tuple
    candidate_digest: str
    portfolio_digest: str
    trajectories: tuple[FrozenCandidateTrajectory, ...]
    ranked_action_keys: tuple
    selected_action_key: tuple
    selected_rollout_steps: int
    model_digest: str
    target_free_receipt_digest: str
    target_used: bool = False


class OneShotOrderGuard:
    def __init__(self):
        self.events = []
        self.target_open_count = 0

    def record(self, event):
        if self.target_open_count:
            raise AssertionError("target-free execution attempted after target open")
        self.events.append(str(event))

    def open_target(self, factory):
        if self.target_open_count or not self.events or \
                self.events[-1] != "execution-frozen":
            raise AssertionError("target opened outside the frozen event order")
        self.target_open_count += 1
        self.events.append("target-opened")
        return factory()

    def scored(self):
        if self.target_open_count != 1 or self.events[-1] != "target-opened":
            raise AssertionError("score called outside the one-shot order")
        self.events.append("scored")


def _fit_frozen_automaton():
    dataset, geometry, labels, geometry_digest = _rows()
    if dataset["dataset_digest"] != EXPECTED_TRAINING_DATASET_DIGEST or \
            geometry_digest != EXPECTED_TRAINING_GEOMETRY_DIGEST:
        raise AssertionError("obligation training corpus drift")
    model = fit_port_obligation_automaton(
        _labelled(geometry, labels), SPEC)
    if model.model_digest != EXPECTED_AUTOMATON_MODEL_DIGEST:
        raise AssertionError("obligation automaton drift")
    return model


def _seed_crop():
    physical = math.ceil(math.dist((0., 0., 0.), CONFIRMATION_CENTER)
                         + SEED_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical)
    return _crop(oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "obligation-confirmation-seed")


def _target_factory():
    physical = math.ceil(math.dist((0., 0., 0.), CONFIRMATION_CENTER)
                         + TARGET_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical)
    check, _ = oracle_patch_fast(ORACLE_LIFT_BOUND + 1, physical)
    target = _crop(oracle, CONFIRMATION_CENTER, TARGET_RADIUS,
                   "obligation-confirmation-target")
    target_check = _crop(check, CONFIRMATION_CENTER, TARGET_RADIUS,
                         "obligation-confirmation-target-check")
    stable = (tuple(target.positions), tuple(target.species)) == (
        tuple(target_check.positions), tuple(target_check.species))
    return target, stable


def prepare_target_blind_execution(guard=None):
    guard = guard or OneShotOrderGuard()
    protocol = validate_preregistration()
    if protocol.manifest_digest != EXPECTED_MANIFEST_DIGEST or \
            protocol.expected_automaton_audit_digest != \
            EXPECTED_AUTOMATON_AUDIT_DIGEST:
        raise AssertionError("confirmation preregistration drift")
    guard.record("protocol-verified")
    model = _fit_frozen_automaton()
    guard.record("model-frozen")
    seed = _seed_crop()
    if not seed.positions:
        raise AssertionError("confirmation seed is empty")
    guard.record("seed-frozen")
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=CONFIRMATION_CENTER,
        seed_positions=tuple(seed.positions), seed_species=tuple(seed.species))
    nucleus = _freeze_at_radius(
        runtime, CONFIRMATION_CENTER, seed, TARGET_RADIUS)
    states, counts = _complete_states_at_radius(source, runtime, TARGET_RADIUS)
    states_by_action = {action_key(row.actions): row for row in states}
    if tuple(counts) != tuple(nucleus.candidate_counts_by_depth) or \
            len(states_by_action) != len(nucleus.terminals):
        raise AssertionError("complete terminal/state accounting drift")
    candidate_ids = tuple(row.actions for row in nucleus.terminals)
    portfolio = select_dual_rank_terminal_portfolio(
        candidate_ids, nucleus.scalar_order, nucleus.fusion_order,
        per_channel_budget=CANDIDATES_PER_BASE_RANKER)
    retained = tuple(portfolio.selected_candidate_ids)
    if not retained or len(retained) > MAXIMUM_FROZEN_CANDIDATES:
        raise AssertionError("frozen candidate portfolio bound failed")
    guard.record("candidates-frozen")
    trajectories = []
    for actions in retained:
        state = states_by_action[tuple(actions)]
        trace, transitions = _rollout(
            source, state, runtime, relational=True)
        score, coverage = score_port_obligation_trajectory(
            model, tuple(transitions))
        trajectories.append(FrozenCandidateTrajectory(
            tuple(actions), score, coverage,
            int(trace["accepted_children"]), bool(trace["fixed_point_reached"]),
            _digest(trace), _digest(tuple(transitions))))
    trajectories = tuple(sorted(trajectories, key=lambda row: repr(
        row.action_key)))
    ranked = tuple(sorted(trajectories, key=lambda row: (
        -row.automaton_score, repr(row.action_key))))
    body = {
        "seed_atoms": len(seed.positions),
        "candidate_counts_by_depth": tuple(counts),
        "complete_terminal_count": len(states),
        "retained_candidates": len(retained),
        "retained_action_keys": tuple(retained),
        "candidate_digest": nucleus.candidate_digest,
        "portfolio_digest": portfolio.selection_digest,
        "trajectories": tuple(asdict(row) for row in trajectories),
        "ranked_action_keys": tuple(row.action_key for row in ranked),
        "selected_action_key": ranked[0].action_key,
        "selected_rollout_steps": ranked[0].rollout_steps,
        "model_digest": model.model_digest,
        "target_used": False,
    }
    execution = FrozenConfirmationExecution(
        body["seed_atoms"], body["candidate_counts_by_depth"],
        body["complete_terminal_count"], body["retained_candidates"],
        body["retained_action_keys"], body["candidate_digest"],
        body["portfolio_digest"], trajectories, body["ranked_action_keys"],
        body["selected_action_key"], body["selected_rollout_steps"],
        body["model_digest"], _digest(body), False)
    guard.record("execution-frozen")
    return execution, guard


def execute_confirmation_once():
    frozen, guard = prepare_target_blind_execution()
    immutable_digest = frozen.target_free_receipt_digest
    target, stable = guard.open_target(_target_factory)
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    exact, correct = [], []
    for actions in frozen.ranked_action_keys:
        hits = sum(truth.get(_site_key(point)) == str(color)
                   for point, color in actions)
        correct.append(hits)
        exact.append(hits == len(actions))
    guard.scored()
    if frozen.target_free_receipt_digest != immutable_digest:
        raise AssertionError("target-free receipt changed after target open")
    selected_correct = correct[0]
    selected_sites = len(frozen.selected_action_key)
    selected_false = selected_sites - selected_correct
    first_exact_rank = next((index for index, value in enumerate(exact, 1)
                             if value), None)
    body = {
        "schema_version": 1,
        "preregistration_digest": EXPECTED_MANIFEST_DIGEST,
        "confirmation_center": CONFIRMATION_CENTER,
        "seed_radius": SEED_RADIUS,
        "target_radius": TARGET_RADIUS,
        "rollout_radius": ROLLOUT_RADIUS,
        "rollout_horizon": ROLLOUT_HORIZON,
        "seed_atoms": frozen.seed_atoms,
        "target_atoms": len(target.positions),
        "candidate_counts_by_depth": frozen.candidate_counts_by_depth,
        "complete_terminal_count": frozen.complete_terminal_count,
        "retained_candidates": frozen.retained_candidates,
        "candidate_digest": frozen.candidate_digest,
        "portfolio_digest": frozen.portfolio_digest,
        "target_free_receipt_digest": frozen.target_free_receipt_digest,
        "model_digest": frozen.model_digest,
        "ranked_action_keys": frozen.ranked_action_keys,
        "ranked_scores": tuple(row.automaton_score for row in sorted(
            frozen.trajectories, key=lambda row: (
                -row.automaton_score, repr(row.action_key)))),
        "ranked_recognized_state_fractions": tuple(
            row.recognized_state_fraction for row in sorted(
                frozen.trajectories, key=lambda row: (
                    -row.automaton_score, repr(row.action_key)))),
        "exact_candidates": sum(exact),
        "candidate_portfolio_contains_exact": any(exact),
        "first_exact_rank": first_exact_rank,
        "selected_action_key": frozen.selected_action_key,
        "selected_action_exact": exact[0],
        "selected_action_correct_sites": selected_correct,
        "selected_action_false_sites": selected_false,
        "selected_rollout_steps": frozen.selected_rollout_steps,
        "oracle_bound_plus_one_stable": stable,
        "target_open_count": guard.target_open_count,
        "event_order": tuple(guard.events),
        "target_materialized_after_execution": True,
        "target_used_for_fit_candidates_trajectory_or_rank": False,
        "raw_training_rollout_domains_disjoint": True,
        "candidate_geometry_changed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["confirmation_gate_passed"] = bool(
        stable and guard.target_open_count == TARGET_OPEN_LIMIT and
        body["candidate_portfolio_contains_exact"] ==
        SUCCESS_GATE["candidate_portfolio_contains_exact"] and
        selected_correct == SUCCESS_GATE["selected_action_exact_sites"] and
        selected_false == SUCCESS_GATE["selected_action_false_sites"] and
        frozen.selected_rollout_steps ==
        SUCCESS_GATE["selected_rollout_steps"])
    return {**body, "result_digest": _digest(body)}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (_digest(body) != digest
            or body["preregistration_digest"] != EXPECTED_MANIFEST_DIGEST
            or body["model_digest"] != EXPECTED_AUTOMATON_MODEL_DIGEST
            or body["retained_candidates"] > MAXIMUM_FROZEN_CANDIDATES
            or body["target_open_count"] != 1
            or body["event_order"] != [
                "protocol-verified", "model-frozen", "seed-frozen",
                "candidates-frozen", "execution-frozen", "target-opened",
                "scored"]
            or body["target_used_for_fit_candidates_trajectory_or_rank"]
            or body["candidate_geometry_changed"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]
            or (EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST)):
        raise AssertionError("port-obligation confirmation result drift")
    return row


def load_default_result():
    raw = FIXTURE.read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("port-obligation confirmation fixture drift")
    return validate_result(json.loads(raw))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-once", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.execute_once:
        if args.write and FIXTURE.exists():
            raise RuntimeError("one-shot confirmation fixture already exists")
        report = execute_confirmation_once()
        text = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.write:
            FIXTURE.parent.mkdir(parents=True, exist_ok=True)
            FIXTURE.write_text(text)
        print(text, end="")
    else:
        print(json.dumps(load_default_result(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
