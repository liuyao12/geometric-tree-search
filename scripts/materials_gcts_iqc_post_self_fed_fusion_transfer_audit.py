#!/usr/bin/env python3
"""Reused-target audit of the frozen post-self-feed IQC terminal value.

The model and a width-16 retention policy are selected entirely from the ten
already-consumed development nuclei.  This module then reconstructs the
previously published second-block candidate receipt, freezes a new ordering,
and only afterwards regenerates that *already consumed* target for scoring.
It is a transfer diagnostic, not a fresh one-shot confirmation.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, select_equivariant_port_fusion)
from materials_gcts_iqc_complete_frontier_confirmation_candidates import (
    _seed)
from materials_gcts_iqc_extended_development_preregistration import (
    TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_artifact import (
    canonical_json, fusion_value_from_payload)
from materials_gcts_iqc_frozen_fusion_runtime import (
    _local_section, _partial, action_key, branch_features,
    load_default_runtime)
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_post_self_fed_fusion_value import (
    load_default_result as load_development_result)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_self_fed_frontier_candidates import (
    DEFAULT_FIXTURE as CANDIDATE_FIXTURE,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_CANDIDATE_SHA256,
    EXPECTED_RECEIPT_DIGEST, validate_candidate_receipt)
from materials_gcts_iqc_self_fed_frontier_confirmation import (
    _crop_code, _open_target_pair)
from materials_gcts_iqc_self_fed_frontier_preregistration import (
    CONFIRMATION_CENTER, ORACLE_LIFT_BOUND, SECOND_BLOCK_RADIUS)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    terminal_successor_features)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_post_self_fed_fusion_transfer_audit_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "f017efc27934daa2bcb9fd3d502dd5814c73ca8bb23ea5eb02d30807539ebf08"
EXPECTED_AUDIT_DIGEST = \
    "39a1aa518dd6c4db0e00e4d8b59c60364a7117123e5495889abc895966b31bf5"
BEAM_WIDTH = 16


@dataclass(frozen=True)
class PostSelfFedFusionTransferAudit:
    development_audit_digest: str
    development_gate_passed: bool
    development_supplied_groups: int
    development_top_one_exact_groups: int
    development_beam_supplied_groups: int
    candidate_receipt_digest: str
    candidate_count: int
    exact_candidate_count: int
    selected_stable_index: int
    selected_exact: bool
    selected_correct_sites: int
    first_exact_rank: int | None
    beam_width: int
    beam_supplies_exact: bool
    exact_candidates_in_beam: int
    candidate_order_digest: str
    candidate_geometry_unchanged: bool
    candidates_frozen_before_target: bool
    target_bound_plus_one_stable: bool
    target_open_count: int
    target_used_for_fit_features_or_ranking: bool
    consumed_target_reused: bool
    fresh_confirmation_claimed: bool
    fresh_confirmation_authorized: bool
    stationary_or_exponential_claimed: bool
    honest_status: str
    audit_digest: str = ""


def _candidate_receipt():
    raw = CANDIDATE_FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_CANDIDATE_SHA256:
        raise AssertionError("self-fed candidate fixture byte drift")
    row = validate_candidate_receipt(json.loads(raw))
    if row["receipt_digest"] != EXPECTED_RECEIPT_DIGEST:
        raise AssertionError("self-fed candidate receipt drift")
    return row


def _receipt_actions(receipt):
    raw = zlib.decompress(base64.b64decode(
        receipt["terminal_actions_zlib_base64"], validate=True))
    if hashlib.sha256(raw).hexdigest() != receipt["terminal_actions_sha256"]:
        raise AssertionError("self-fed terminal payload drift")
    return tuple(tuple((tuple(map(float, point)), str(color))
                       for point, color in terminal)
                 for terminal in json.loads(raw))


def _freeze_candidate_order(model, receipt):
    runtime = load_default_runtime()
    seed = _seed(ORACLE_LIFT_BOUND)
    first_source = SimpleNamespace(
        group=CONFIRMATION_CENTER, seed_positions=seed.positions,
        seed_species=seed.species)
    first_states, first_counts = _complete_states_at_radius(
        first_source, runtime, TARGET_RADIUS)
    inherited_key = action_key(tuple(
        (tuple(map(float, point)), str(color))
        for point, color in receipt["inherited_actions"]))
    inherited = tuple(state for state in first_states
                      if action_key(state.actions) == inherited_key)
    if first_counts != (8, 37, 128) or len(inherited) != 1:
        raise AssertionError("inherited self-fed state did not replay")
    second_source = SimpleNamespace(
        group=CONFIRMATION_CENTER,
        seed_positions=inherited[0].positions,
        seed_species=inherited[0].species)
    states, second_counts = _complete_states_at_radius(
        second_source, runtime, SECOND_BLOCK_RADIUS)
    states = tuple(sorted(states, key=lambda state: repr(
        action_key(state.actions))))
    actions = tuple(action_key(state.actions) for state in states)
    if second_counts != (8, 37, 128) or actions != _receipt_actions(receipt):
        raise AssertionError("second self-fed candidate geometry drift")
    candidates = []
    for stable_index, state in enumerate(states):
        partial, graph = _partial(
            second_source, state, runtime["grouped_vocabulary"])
        features = tuple(branch_features(state)) + _local_section(state) + \
            partial + terminal_successor_features(
                state, runtime["state_model"], CONFIRMATION_CENTER,
                SECOND_BLOCK_RADIUS)
        candidates.append(EquivariantPortFusionCandidate(
            features, tuple(color for _point, color in state.actions),
            graph, stable_index))
    selection = select_equivariant_port_fusion(model, candidates)
    order = tuple(sorted(range(len(states)), key=lambda index: (
        -selection.fused_scores[index], index)))
    payload = tuple((candidate.scalar_features, candidate.action_colors,
                     candidate.graph.canonical_digest, candidate.tie_key)
                    for candidate in candidates), order
    digest = hashlib.sha256(repr(payload).encode()).hexdigest()
    return states, order, selection.stable_index, digest


def evaluate():
    development = load_development_result()
    model = fusion_value_from_payload(development["final_model_payload"])
    supplied_ranks = tuple(fold["first_exact_rank"]
                           for fold in development["folds"]
                           if fold["terminal_supply"])
    development_beam_supply = sum(
        rank is not None and rank <= BEAM_WIDTH for rank in supplied_ranks)
    receipt = _candidate_receipt()
    states, order, selected, frozen_digest = _freeze_candidate_order(
        model, receipt)
    immutable = repr((tuple(action_key(state.actions) for state in states),
                      order, selected, frozen_digest))

    target, target_check = _open_target_pair()
    stable = _crop_code(target) == _crop_code(target_check)
    truth = {_key(point): str(color) for point, color in
             zip(target.positions, target.species)}
    exact = tuple(all(truth.get(_key(point)) == color
                      for point, color in state.actions)
                  for state in states)
    correct = tuple(sum(truth.get(_key(point)) == color
                        for point, color in state.actions)
                    for state in states)
    if immutable != repr((tuple(action_key(state.actions) for state in states),
                          order, selected, frozen_digest)):
        raise AssertionError("candidate order changed after target")
    first_exact = next((rank for rank, index in enumerate(order, 1)
                        if exact[index]), None)
    body = asdict(PostSelfFedFusionTransferAudit(
        development["audit_digest"], development["development_gate_passed"],
        development["supplied_groups"],
        development["nested_selected_exact_groups"],
        development_beam_supply, receipt["receipt_digest"], len(states),
        sum(exact), selected, exact[selected], correct[selected], first_exact,
        BEAM_WIDTH, any(exact[index] for index in order[:BEAM_WIDTH]),
        sum(exact[index] for index in order[:BEAM_WIDTH]), frozen_digest,
        True, True, stable, 1, False, True, False, False, False,
        "reused target tests a development-selected beam; fresh gate remains red"))
    body.pop("audit_digest")
    return PostSelfFedFusionTransferAudit(
        **body, audit_digest=hashlib.sha256(canonical_json(body)).hexdigest())


def validate_result(row):
    body = dict(row)
    digest = body.pop("audit_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["development_gate_passed"]
            or body["development_beam_supplied_groups"] != 9
            or body["candidate_receipt_digest"] != EXPECTED_RECEIPT_DIGEST
            or body["candidate_count"] != 128
            or body["beam_width"] != BEAM_WIDTH
            or not body["candidate_geometry_unchanged"]
            or not body["candidates_frozen_before_target"]
            or body["target_used_for_fit_features_or_ranking"]
            or not body["consumed_target_reused"]
            or body["fresh_confirmation_claimed"]
            or body["fresh_confirmation_authorized"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("post-self-fed fusion transfer audit drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("post-self-fed transfer result drift")
    return row


def load_default_result():
    raw = DEFAULT_FIXTURE.read_bytes()
    if (EXPECTED_FIXTURE_SHA256
            and hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("post-self-fed transfer fixture byte drift")
    return validate_result(json.loads(raw))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    text = json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
