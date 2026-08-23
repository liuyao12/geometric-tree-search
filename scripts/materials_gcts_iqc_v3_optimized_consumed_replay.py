#!/usr/bin/env python3
"""Target-free full V3 replay after generic frontier/section cache work."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_fresh_parent_balanced_execution_v3 import \
    freeze_fresh_parent_balanced_execution_v3
from materials_gcts_iqc_parent_balanced_confirmation_preregistration import (
    FIRST_RADIUS, FOURTH_RADIUS, SECOND_RADIUS, SEED_RADIUS, THIRD_RADIUS)
from materials_gcts_iqc_parent_balanced_v3_consumed_benchmark import (
    CONSUMED_CENTER, RUNTIME_LIMIT_SECONDS, WORKERS, load_default_result)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_v3_optimized_consumed_replay_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "d96fb75a0d8830682f953b00ecd19c3670f2a05e408ddac5ffba42da4efcc8d6"


def validate_result(result):
    if (result["schema_version"] != 1 or result["target_used"] or
            not result["all_frozen_outputs_identical"] or
            not all(result["parity"].values()) or
            result["raw_nine_action_lineages"] != 1102 or
            result["selected_nine_action_lineages"] != 64 or
            result["fourth_candidates"] != 512 or
            result["runtime_limit_seconds"] != 600. or
            not result["runtime_gate_passed"] or
            result["total_execution_seconds"] >
            result["runtime_limit_seconds"] or
            result["speedup"] < 4. or
            result["old_total_execution_seconds"] /
            result["total_execution_seconds"] != result["speedup"]):
        raise AssertionError("optimized consumed V3 result drift")
    return result


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("optimized consumed V3 fixture byte drift")
    return validate_result(json.loads(raw))


def evaluate():
    old = load_default_result()["receipt"]
    seed, _lifts = oracle_crop_fast(CONSUMED_CENTER, SEED_RADIUS)
    execution = freeze_fresh_parent_balanced_execution_v3(
        center=CONSUMED_CENTER, seed_positions=seed.positions,
        seed_species=seed.species, first_radius=FIRST_RADIUS,
        second_radius=SECOND_RADIUS, third_radius=THIRD_RADIUS,
        fourth_radius=FOURTH_RADIUS, workers=WORKERS)
    stage_seconds = dict(execution.stage_seconds)
    total = sum(stage_seconds.values())
    parity = {
        "second_branch_receipt":
            execution.second_branch_receipt_digest ==
            old["second_branch_receipt_digest"],
        "scheduled_prefix":
            execution.scheduled_prefix_digest ==
            old["scheduled_prefix_digest"],
        "lineage_model": execution.lineage_model_digest ==
            old["lineage_model_digest"],
        "raw_lineage": execution.raw_nine_action_lineage_digest ==
            old["raw_nine_action_lineage_digest"],
        "selected_indices": list(execution.selected_nine_action_lineage_indices)
            == old["selected_nine_action_lineage_indices"],
        "candidate": execution.candidate_digest == old["candidate_digest"],
        "deterministic_receipt": execution.deterministic_receipt_digest ==
            old["deterministic_receipt_digest"],
    }
    result = {
        "schema_version": 1,
        "seed_atoms": len(seed.positions),
        "raw_nine_action_lineages":
            len(execution.raw_nine_action_lineages),
        "selected_nine_action_lineages":
            len(execution.selected_nine_action_lineage_indices),
        "fourth_candidates": len(execution.candidates),
        "parity": parity,
        "all_frozen_outputs_identical": all(parity.values()),
        "stage_seconds": execution.stage_seconds,
        "total_execution_seconds": total,
        "runtime_limit_seconds": RUNTIME_LIMIT_SECONDS,
        "runtime_gate_passed": total <= RUNTIME_LIMIT_SECONDS,
        "old_total_execution_seconds":
            sum(seconds for _name, seconds in old["stage_seconds"]),
        "speedup": sum(seconds for _name, seconds in
                       old["stage_seconds"]) / total,
        "target_used": execution.target_used,
    }
    if (result["target_used"] or not result["all_frozen_outputs_identical"] or
            result["raw_nine_action_lineages"] != 1102 or
            result["selected_nine_action_lineages"] != 64 or
            result["fourth_candidates"] != 512):
        raise AssertionError("optimized consumed V3 replay drift")
    return validate_result(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live", action="store_true",
        help="rerun the several-minute target-free construction")
    args = parser.parse_args()
    print(json.dumps(evaluate() if args.live else load_default_result(),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
