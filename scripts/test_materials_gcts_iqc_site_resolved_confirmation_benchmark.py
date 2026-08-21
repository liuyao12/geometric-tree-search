#!/usr/bin/env python3
"""Regression for the consumed one-shot site-resolved IQC confirmation."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import re

from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_site_resolved_confirmation_preregistration import (
    EXPECTED_MANIFEST_DIGEST,
)


ROOT = Path(__file__).resolve().parent
RECEIPT = ROOT / "fixtures" / "iqc_site_resolved_confirmation_v1.json.gz"
BENCHMARK = ROOT / "materials_gcts_iqc_site_resolved_confirmation_benchmark.py"


def test_consumed_confirmation_receipt_is_immutable_and_honestly_red():
    with gzip.open(RECEIPT, "rt", encoding="utf-8") as handle:
        row = json.load(handle)
    result_digest = row.pop("result_digest")
    source = BENCHMARK.read_text(encoding="utf-8")
    frozen = re.search(
        r'EXPECTED_RESULT_DIGEST\s*=\s*\\?\s*\n?\s*"([0-9a-f]{64})"',
        source)
    assert frozen is not None
    assert _digest(row) == result_digest == frozen.group(1)
    assert row["protocol_digest"] == EXPECTED_MANIFEST_DIGEST
    assert row["fresh_confirmation_consumed"] is True
    assert row["target_factory_calls"] == 1
    assert row["target_opened_after_all_wave_rankings"] is True
    assert row["target_used_for_fit_candidates_ranking_or_execution"] is False
    assert row["oracle_bound_plus_one_stable"] is True
    assert row["candidate_geometry_changed"] is False
    assert row["branches_spliced_or_sites_moved"] is False
    assert row["self_fed_depth"] == 3
    assert row["selected_exact_sites"] == 2
    assert row["required_exact_sites"] == 9
    assert row["confirmation_gate_passed"] is False
    assert row["autonomous_finite_growth_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False

    scores = row["posthoc_wave_scores"]
    assert [item["exact_candidate_supply"] for item in scores] == [0, 1, 1]
    assert [item["selected_exact"] for item in scores] == [False, False, False]
    assert [item["selected_correct_sites"] for item in scores] == [0, 2, 0]
    assert all(not wave["target_used"] for wave in row["wave_frozen_receipts"])


if __name__ == "__main__":
    test_consumed_confirmation_receipt_is_immutable_and_honestly_red()
    print("consumed site-resolved IQC confirmation receipt: passed")
