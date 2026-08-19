#!/usr/bin/env python3
"""Build the preregistered seed-only second IQC frontier receipt."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import zlib
from pathlib import Path

from materials_gcts_iqc_complete_frontier_confirmation_candidates import (
    DEFAULT_FIXTURE as FIRST_CANDIDATE_FIXTURE, _crop_code, _seed,
    validate_candidate_receipt as validate_first_candidate_receipt)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    freeze_self_fed_candidates, normalize_actions)
from materials_gcts_iqc_self_fed_frontier_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST, FIRST_BLOCK_RECEIPT_DIGEST,
    FIRST_BLOCK_RESULT_DIGEST, INHERITED_ACTION_DIGEST,
    INHERITED_FUSION_STABLE_INDEX, ORACLE_LIFT_BOUND, SECOND_BLOCK_RADIUS,
    SOURCE_COMMIT, audit)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_self_fed_frontier_candidates_v1.json"


def _digest(payload):
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _terminal_actions(receipt):
    raw = zlib.decompress(base64.b64decode(
        receipt["terminal_actions_zlib_base64"], validate=True))
    if hashlib.sha256(raw).hexdigest() != receipt["terminal_actions_sha256"]:
        raise AssertionError("first-block terminal payload drift")
    return json.loads(raw)


def build_candidate_receipt():
    protocol = audit()
    if protocol.manifest_digest != EXPECTED_MANIFEST_DIGEST:
        raise AssertionError("self-fed protocol digest drift")
    first = validate_first_candidate_receipt(json.loads(
        FIRST_CANDIDATE_FIXTURE.read_text()))
    if first["receipt_digest"] != FIRST_BLOCK_RECEIPT_DIGEST:
        raise AssertionError("first-block receipt digest drift")
    first_result = ROOT / \
        "fixtures/iqc_complete_frontier_confirmation_result_v1.json"
    if hashlib.sha256(first_result.read_bytes()).hexdigest() != \
            FIRST_BLOCK_RESULT_DIGEST:
        raise AssertionError("first-block result fixture drift")
    terminals = _terminal_actions(first)
    if first["fusion_order"][0] != INHERITED_FUSION_STABLE_INDEX:
        raise AssertionError("inherited fusion selection drift")
    inherited = normalize_actions(terminals[INHERITED_FUSION_STABLE_INDEX])
    if hashlib.sha256(repr(inherited).encode()).hexdigest() != \
            INHERITED_ACTION_DIGEST:
        raise AssertionError("inherited action digest drift")

    seed = _seed(ORACLE_LIFT_BOUND)
    seed_check = _seed(ORACLE_LIFT_BOUND + 1)
    stable = _crop_code(seed) == _crop_code(seed_check)
    if not stable:
        raise AssertionError("self-fed seed changes at lift bound + 1")
    execution = freeze_self_fed_candidates(
        center=CONFIRMATION_CENTER,
        seed_positions=seed.positions,
        seed_species=seed.species,
        inherited_actions=inherited,
        public_radius=SECOND_BLOCK_RADIUS)
    terminal_bytes = json.dumps(
        execution.terminal_actions, separators=(",", ":")).encode()
    compressed = base64.b64encode(
        zlib.compress(terminal_bytes, level=9)).decode()
    payload = {
        "schema_version": 1,
        "source_commit": SOURCE_COMMIT,
        "protocol_digest": protocol.manifest_digest,
        "first_block_receipt_digest": first["receipt_digest"],
        "center": CONFIRMATION_CENTER,
        "original_seed_atoms": execution.original_seed_atoms,
        "seed_bound_plus_one_stable": stable,
        "inherited_fusion_stable_index": INHERITED_FUSION_STABLE_INDEX,
        "inherited_actions": execution.inherited_actions,
        "inherited_action_digest": INHERITED_ACTION_DIGEST,
        "inherited_state_atoms": execution.inherited_state_atoms,
        "inherited_state_digest": execution.inherited_state_digest,
        "public_radius": SECOND_BLOCK_RADIUS,
        "action_reach_schedule": execution.action_reach_schedule,
        "candidate_counts_by_depth": execution.candidate_counts_by_depth,
        "terminal_count": execution.terminal_count,
        "terminal_actions_zlib_base64": compressed,
        "terminal_actions_sha256": hashlib.sha256(terminal_bytes).hexdigest(),
        "scalar_order": execution.scalar_order,
        "fusion_order": execution.fusion_order,
        "portfolio_indices": execution.portfolio_indices,
        "candidate_digest": execution.candidate_digest,
        "portfolio_digest": execution.portfolio_digest,
        "execution_digest": execution.execution_digest,
        "target_open_count": 0,
        "target_used": execution.target_used,
    }
    return {**payload, "receipt_digest": _digest(payload)}


def validate_candidate_receipt(payload):
    body = dict(payload)
    digest = body.pop("receipt_digest")
    try:
        raw = zlib.decompress(base64.b64decode(
            body["terminal_actions_zlib_base64"], validate=True))
        actions = json.loads(raw)
    except Exception as error:
        raise AssertionError("invalid self-fed terminal payload") from error
    if (_digest(body) != digest
            or body["schema_version"] != 1
            or body["protocol_digest"] != EXPECTED_MANIFEST_DIGEST
            or body["first_block_receipt_digest"] != FIRST_BLOCK_RECEIPT_DIGEST
            or tuple(body["center"]) != CONFIRMATION_CENTER
            or body["inherited_fusion_stable_index"] !=
               INHERITED_FUSION_STABLE_INDEX
            or body["inherited_action_digest"] != INHERITED_ACTION_DIGEST
            or body["public_radius"] != SECOND_BLOCK_RADIUS
            or tuple(body["action_reach_schedule"]) != (8, 8, 8)
            or body["terminal_count"] != len(actions)
            or hashlib.sha256(raw).hexdigest() !=
               body["terminal_actions_sha256"]
            or len(body["scalar_order"]) != body["terminal_count"]
            or len(body["fusion_order"]) != body["terminal_count"]
            or len(body["portfolio_indices"]) > 18
            or body["target_open_count"] != 0 or body["target_used"]
            or not body["seed_bound_plus_one_stable"]):
        raise AssertionError("self-fed candidate receipt drift")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    receipt = build_candidate_receipt()
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
