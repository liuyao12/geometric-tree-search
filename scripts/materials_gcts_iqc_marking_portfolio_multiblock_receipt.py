#!/usr/bin/env python3
"""Preserve the consumed three-block two-mark IQC portfolio receipt."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


FIXTURE = Path(__file__).resolve().parent / \
    "fixtures/iqc_stage_local_marking_portfolio_multiblock_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "6eb344e704f6d83655a8e24d37ed300b7286d6b93af53b1df2a6e38e0e4edcd9"


@dataclass(frozen=True)
class IQCMarkingPortfolioMultiblockReceipt:
    schema_version: int
    center: tuple[float, float, float]
    seed_atoms: int
    target_atoms: int
    blocks: int
    beam_width: int
    marking_names: tuple[str, ...]
    physical_expansions: int
    expansion_candidate_counts: tuple[int, ...]
    level_candidate_counts: tuple[int, ...]
    level_unique_state_counts: tuple[int, ...]
    level_retained_state_counts: tuple[int, ...]
    pretarget_execution_digest: str
    terminal_correct_sites: tuple[int, ...]
    terminal_wrong_sites: tuple[int, ...]
    terminal_exact: tuple[bool, ...]
    exact_terminal_supply: int
    first_block_exact_connection_head_preserved: bool
    target_used_during_tree_construction: bool
    target_opened_after_complete_tree_froze: bool
    consumed_target_diagnostic_only: bool
    winner_selected: bool
    autonomous_growth_claimed: bool
    stationary_or_exponential_claimed: bool
    honest_status: str


def load_receipt(path=FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("multi-block portfolio receipt byte drift")
    row = json.loads(raw)
    result = IQCMarkingPortfolioMultiblockReceipt(
        int(row["schema_version"]), tuple(map(float, row["center"])),
        int(row["seed_atoms"]), int(row["target_atoms"]), int(row["blocks"]),
        int(row["beam_width"]), tuple(map(str, row["marking_names"])),
        int(row["physical_expansions"]),
        tuple(map(int, row["expansion_candidate_counts"])),
        tuple(map(int, row["level_candidate_counts"])),
        tuple(map(int, row["level_unique_state_counts"])),
        tuple(map(int, row["level_retained_state_counts"])),
        str(row["pretarget_execution_digest"]),
        tuple(map(int, row["terminal_correct_sites"])),
        tuple(map(int, row["terminal_wrong_sites"])),
        tuple(map(bool, row["terminal_exact"])),
        int(row["exact_terminal_supply"]),
        bool(row["first_block_exact_connection_head_preserved"]),
        bool(row["target_used_during_tree_construction"]),
        bool(row["target_opened_after_complete_tree_froze"]),
        bool(row["consumed_target_diagnostic_only"]),
        bool(row["winner_selected"]), bool(row["autonomous_growth_claimed"]),
        bool(row["stationary_or_exponential_claimed"]),
        str(row["honest_status"]))
    if (result.schema_version != 1 or result.blocks != 3 or
            result.beam_width != 2 or result.physical_expansions != 5 or
            result.expansion_candidate_counts != (8, 8, 8, 8, 8) or
            result.level_retained_state_counts != (2, 2, 2) or
            result.target_used_during_tree_construction or
            not result.target_opened_after_complete_tree_froze or
            not result.consumed_target_diagnostic_only or result.winner_selected or
            result.autonomous_growth_claimed or
            result.stationary_or_exponential_claimed):
        raise AssertionError("invalid multi-block portfolio receipt")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = load_receipt()
    print(json.dumps(result.__dict__, indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
