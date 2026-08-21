#!/usr/bin/env python3
"""One-shot spatial confirmation of frozen stage-local rollout value."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_frozen_stage_local_margin_marking import (
    load_default_model as load_prefix_model)
from materials_gcts_iqc_frozen_stage_local_rollout_value import (
    load_default_model as load_rollout_model)
from materials_gcts_iqc_obligation_expanded_dataset import _digest, _site_key
from materials_gcts_iqc_stage_local_rollout_confirmation_preregistration import (
    EXPECTED_MANIFEST_DIGEST, audit as preregistration_audit)
from materials_gcts_iqc_stage_local_rollout_runtime import (
    execute_stage_local_rollout_search)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_RECEIPT = ROOT / \
    "fixtures/iqc_stage_local_rollout_confirmation_v1.json.gz"
EXPECTED_RECEIPT_SHA256 = \
    "2d321f383357318ba47b65435f90306ec9fb105053a6b292dc73797b2cd9dd37"
EXPECTED_RESULT_DIGEST = \
    "0f77561c20750e9647c267bee4bca5208d0a055b14962d5cfa6d5b6019257a1d"


class _SingleUseTargetGate:
    def __init__(self, center, radius):
        self._center = tuple(center)
        self._radius = float(radius)
        self._execution_digest = None
        self.open_count = 0

    def freeze_execution(self, digest):
        if self._execution_digest is not None or self.open_count:
            raise RuntimeError("confirmation execution already frozen")
        self._execution_digest = str(digest)

    def open(self):
        if self._execution_digest is None or self.open_count:
            raise RuntimeError("confirmation target ordering violation")
        self.open_count += 1
        return oracle_crop_fast(self._center, self._radius)[0]


def _execute_blocks(protocol, runtime, prefix_model, rollout_model, *, marked):
    seed, _ = oracle_crop_fast(
        protocol.confirmation_center, protocol.seed_radius)
    positions, species = tuple(seed.positions), tuple(seed.species)
    blocks = []
    for block in range(1, protocol.self_fed_blocks + 1):
        result = execute_stage_local_rollout_search(
            runtime, prefix_model, rollout_model,
            center=protocol.confirmation_center,
            seed_positions=positions, seed_species=species,
            public_radius=protocol.target_radius)
        selected_index = result.selected_index if marked else 0
        selected = result.candidates[selected_index]
        state = selected.state
        if len(state.positions) != len(positions) + protocol.sites_per_block:
            raise AssertionError("one confirmation block must emit three sites")
        blocks.append({
            "block": block, "seed_atoms": len(positions),
            "candidate_counts_by_depth": result.candidate_counts_by_depth,
            "retained_counts_by_depth": result.retained_counts_by_depth,
            "candidate_digest": result.candidate_digest,
            "candidate_action_keys": tuple(row.action_key
                                            for row in result.candidates),
            "candidate_scores": tuple(row.rollout_score
                                       for row in result.candidates),
            "candidate_trace_digests": tuple(row.trace_digest
                                              for row in result.candidates),
            "candidate_transition_digests": tuple(
                row.transition_digest for row in result.candidates),
            "selected_index": selected_index,
            "selected_actions": selected.action_key,
            "selected_state_digest": _digest({
                "positions": state.positions, "species": state.species,
                "actions": state.actions}),
            "target_api_present": result.target_api_present,
            "target_used": result.target_used,
        })
        positions, species = tuple(state.positions), tuple(state.species)
    return {
        "arm": "rollout-value" if marked else "stable-prefix-control",
        "initial_seed_atoms": len(seed.positions), "blocks": tuple(blocks),
        "final_positions": positions, "final_species": species,
        "target_api_present": False, "target_used": False,
    }


def _score_trace(trace, truth):
    seen, blocks = set(), []
    for row in trace["blocks"]:
        flags = tuple(truth.get(_site_key(point)) == str(color)
                      for point, color in row["selected_actions"])
        sites = tuple((_site_key(point), str(color))
                      for point, color in row["selected_actions"])
        duplicate = any(site in seen for site in sites)
        seen.update(sites)
        blocks.append({
            "block": row["block"], "site_correct": flags,
            "correct_sites": sum(flags), "wrong_sites": len(flags) - sum(flags),
            "exact_action": all(flags), "duplicate_selected_site": duplicate,
        })
    return {
        "blocks": tuple(blocks),
        "correct_sites": sum(row["correct_sites"] for row in blocks),
        "wrong_sites": sum(row["wrong_sites"] for row in blocks),
        "exact_blocks": sum(row["exact_action"] for row in blocks),
        "unique_selected_sites": len(seen),
    }


def evaluate():
    protocol = preregistration_audit()
    if protocol.manifest_digest != EXPECTED_MANIFEST_DIGEST or \
            not protocol.source_hashes_verified:
        raise AssertionError("confirmation protocol/source drift")
    prefix_model, rollout_model = load_prefix_model(), load_rollout_model()
    if prefix_model.model_digest != protocol.prefix_model_digest or \
            rollout_model.model_digest != protocol.rollout_model_digest:
        raise AssertionError("confirmation model drift")
    runtime = load_default_runtime()
    marked = _execute_blocks(
        protocol, runtime, prefix_model, rollout_model, marked=True)
    baseline = _execute_blocks(
        protocol, runtime, prefix_model, rollout_model, marked=False)
    if marked["blocks"][0]["candidate_digest"] != \
            baseline["blocks"][0]["candidate_digest"] or \
            marked["blocks"][0]["candidate_action_keys"] != \
            baseline["blocks"][0]["candidate_action_keys"]:
        raise AssertionError("matched first-block candidate work drift")
    execution_body = {
        "protocol_digest": protocol.manifest_digest,
        "prefix_model_digest": prefix_model.model_digest,
        "rollout_model_digest": rollout_model.model_digest,
        "marked": marked, "baseline": baseline,
    }
    execution_digest = _digest(execution_body)
    gate = _SingleUseTargetGate(
        protocol.confirmation_center, protocol.target_radius)
    gate.freeze_execution(execution_digest)
    target = gate.open()
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    marked_score = _score_trace(marked, truth)
    baseline_score = _score_trace(baseline, truth)
    first_marked = marked_score["blocks"][0]
    first_baseline = baseline_score["blocks"][0]
    body = {
        "schema_version": 1, "protocol": asdict(protocol),
        "protocol_digest": protocol.manifest_digest,
        "prefix_model_digest": prefix_model.model_digest,
        "rollout_model_digest": rollout_model.model_digest,
        "confirmation_center": protocol.confirmation_center,
        "seed_atoms": marked["initial_seed_atoms"],
        "target_atoms": len(target.positions),
        "execution_digest_before_target": execution_digest,
        "marked_trace": marked, "baseline_trace": baseline,
        "marked_score": marked_score, "baseline_score": baseline_score,
        "identical_first_block_candidate_work": True,
        "target_open_count": gate.open_count,
        "target_opened_after_all_traces_froze": True,
        "target_used_for_candidate_ranking_or_execution": False,
        "candidate_geometry_changed_after_target": False,
        "fresh_confirmation_consumed": True,
        "generic_stage_local_rollout_value_tested": True,
        "stationary_or_exponential_claimed": False,
    }
    body["first_block_transfer_gate_passed"] = bool(
        gate.open_count == 1 and first_marked["exact_action"] and
        first_marked["wrong_sites"] == 0 and
        first_marked["correct_sites"] >= first_baseline["correct_sites"] and
        not first_marked["duplicate_selected_site"])
    body["sustained_three_block_gate_passed"] = bool(
        body["first_block_transfer_gate_passed"] and
        marked_score["exact_blocks"] == protocol.self_fed_blocks and
        marked_score["correct_sites"] ==
            protocol.self_fed_blocks * protocol.sites_per_block and
        marked_score["wrong_sites"] == 0 and
        marked_score["unique_selected_sites"] ==
            protocol.self_fed_blocks * protocol.sites_per_block and
        all(not row["duplicate_selected_site"]
            for row in marked_score["blocks"]))
    body["autonomous_finite_continuation_claimed"] = bool(
        body["sustained_three_block_gate_passed"])
    return {**body, "result_digest": _digest(body)}


def load_receipt(path=DEFAULT_RECEIPT):
    raw = Path(path).read_bytes()
    if EXPECTED_RECEIPT_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_RECEIPT_SHA256:
        raise AssertionError("confirmation receipt byte drift")
    row = json.loads(gzip.decompress(raw))
    body = dict(row)
    digest = body.pop("result_digest")
    if _digest(body) != digest or \
            (EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST):
        raise AssertionError("confirmation result drift")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write and DEFAULT_RECEIPT.exists():
        raise RuntimeError("confirmation receipt already exists")
    row = evaluate()
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_RECEIPT.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text if args.json else (
        "stage-local rollout confirmation passes" if
        row["first_block_transfer_gate_passed"] else
        "stage-local rollout confirmation remains red"), end="")


if __name__ == "__main__":
    main()
