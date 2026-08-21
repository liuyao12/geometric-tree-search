#!/usr/bin/env python3
"""Fast receipt checks for posthoc consumed-confirmation diagnostics."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from materials_gcts_iqc_obligation_expanded_dataset import _digest


ROOT = Path(__file__).resolve().parent
SUPPLY = ROOT / "fixtures" / \
    "iqc_site_resolved_confirmation_full_tree_supply_v1.json.gz"
REACH = ROOT / "fixtures" / \
    "iqc_site_resolved_confirmation_reach_v1.json.gz"


def _load(path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        row = json.load(handle)
    digest = row.pop("result_digest")
    assert _digest(row) == digest
    return row, digest


def test_full_old_tree_has_no_exact_terminal_at_any_portfolio_width():
    row, digest = _load(SUPPLY)
    assert digest == \
        "1b3091f26963a9e5a174b553d9effcdbdcdd8c955ae276f31c7bc5eef4d68f5f"
    assert row["consumed_confirmation_diagnostic"] is True
    assert row["fresh_confirmation_claimed"] is False
    assert row["candidate_counts_by_depth"] == [8, 40, 157]
    assert row["exact_candidate_count"] == 0
    assert row["minimum_dual_rank_budget_for_exact_supply"] is None
    assert all(item["exact_candidates"] == 0
               for item in row["portfolio_width_audit"])
    assert row["target_used_for_candidate_rollout_or_ranking"] is False
    assert row["policy_integrated"] is False


def test_wider_root_narrower_middle_restores_supply_but_not_value():
    row, digest = _load(REACH)
    assert digest == \
        "d4536b62e1e309ceb4ec49cde089ca41abb45b5538c09f0486785dfa3efbd03d"
    results = {tuple(item["schedule"]): item
               for item in row["schedule_results"]}
    old = results[(8, 8, 8)]
    repaired = results[(12, 4, 8)]
    assert old["exact_terminal_count"] == 0
    assert old["proposal_checks"] == 392
    assert repaired["exact_terminal_count"] == 1
    assert repaired["proposal_checks"] == 356
    assert repaired["candidate_counts_by_depth"] == [12, 37, 166]
    assert repaired["exact_terminal_ranks"] == [{
        "terminal_index": 68, "scalar_rank": 114, "fusion_rank": 107}]
    assert repaired["minimum_dual_rank_budget_for_exact_supply"] == 107
    assert results[(24, 4, 8)]["exact_terminal_count"] == 4
    assert row["target_used_for_proposal_generation"] is False
    assert row["policy_integrated"] is False
    assert row["autonomous_growth_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_full_old_tree_has_no_exact_terminal_at_any_portfolio_width()
    test_wider_root_narrower_middle_restores_supply_but_not_value()
    print("consumed IQC confirmation diagnostics: passed")
