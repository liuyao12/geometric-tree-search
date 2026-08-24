#!/usr/bin/env python3
"""Pinned minimal two-fallback full-width IQC development gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from materials_gcts_iqc_hybrid_fullwidth_consumed_benchmark import evaluate
from materials_gcts_iqc_parent_balanced_confirmation_preregistration import \
    canonical_json


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_minimal_hybrid_fullwidth_consumed_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "bb9f67bffd2144a6c30e469f95514bdde5742251d59a97116c0253be00e6205c"
EXPECTED_RESULT_DIGEST = \
    "c43e774cda1e7ccaaa8d475bcc8cba8fbaff581b61996fb9bc80e767954fb719"


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            digest != EXPECTED_RESULT_DIGEST or
            row["candidate_selection_target_used"] or
            not row["target_opened_after_complete_receipt_freeze"] or
            not row["receipt_unchanged_after_target"] or
            row["selected_prefixes"] != 10 or
            row["joint_prefixes"] != 8 or
            row["fallback_prefixes"] != 2 or
            row["maximum_fallbacks"] != 2 or
            row["raw_joint_exact_lineages"] != 3 or
            row["raw_fallback_exact_lineages"] != 3 or
            row["selected_exact_nine_action_lineages"] != 6 or
            row["exact_complete_twelve_action_paths"] < 1 or
            row["best_complete_correct_actions"] != 12 or
            not row["runtime_gate_passed"] or
            row["fresh_confirmation_claimed"] or
            row["autonomous_or_exponential_growth_claimed"]):
        raise AssertionError("minimal hybrid full-width gate drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("minimal hybrid fixture drift")
    return validate_result(json.loads(raw))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    row = evaluate(maximum_fallbacks=2) if args.live \
        else load_default_result()
    print(json.dumps(row, indent=2, sort_keys=True))
