#!/usr/bin/env python3
"""Validate the immutable one-shot supply-confirmation receipt without rerun."""

import hashlib
import json
from pathlib import Path


RECEIPT = Path(__file__).resolve().parent / \
    "fixtures/materials_gcts_iqc_recurrent_supply_confirmation.json"
EXPECTED_DIGEST = \
    "63a4a3eeb05c15250aa567cf470fab3b721d08338b29e688c32a701dc0e0a11a"


def main():
    report = json.loads(RECEIPT.read_text())
    digest = hashlib.sha256(json.dumps(
        report, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == EXPECTED_DIGEST
    assert report["candidate_graph_frozen_before_target"]
    assert report["target_open_count"] == 1
    assert not report["target_used_for_fit_or_candidate_generation"]
    assert report["correct_root_candidates"] == 38
    assert report["exact_root_child_paths"] == 4
    assert report["supply_gate_passed"]
    assert not report["autonomous_selection_claimed"]
    assert not report["stationary_or_exponential_certificate"]
    print("recurrent IQC supply confirmation receipt passed")


if __name__ == "__main__":
    main()
