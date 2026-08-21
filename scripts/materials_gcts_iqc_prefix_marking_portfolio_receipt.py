#!/usr/bin/env python3
"""Validate the consumed IQC prefix-portfolio failure boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FIXTURE = Path(__file__).resolve().parent / \
    "fixtures/iqc_prefix_marking_portfolio_diagnostic_v1.json"
EXPECTED_SHA256 = \
    "8babdfc8db3e9bcb482355d0629c582126b897634de6d57b1612920381e4be6d"


def load_receipt(path=FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise AssertionError("IQC prefix-portfolio fixture drift")
    row = json.loads(raw)
    lineage = row["lineage_portfolio"]
    raw_reach = row["raw_prefix_reach"]
    rank = row["complete_bounded_block2_rank_audit"]
    portfolio = row["channel_diverse_prefix_portfolio"]
    if (row["schema_version"] != 1 or
            not row["consumed_target_diagnostic_only"] or
            row["target_used_during_candidate_generation"] or
            lineage["exact_terminal_supply"] != 0 or
            lineage["beam_schedule"] != [2, 4, 8] or
            not raw_reach["target_guided_exact_three_block_path_supplied"] or
            not raw_reach["target_used_to_prune_prefixes"] or
            raw_reach["first_correct_exposed_port_rank_after_exact_two_site_prefix"] != 14 or
            rank["best_learned_section_exact_rank_by_depth"] != [1, 1, 19] or
            portfolio["block2_exact_candidates"] != 0 or
            portfolio["exact_three_block_path_supplied"] or
            not row["candidate_geometry_repaired"] or
            row["transferable_value_repaired"] or
            row["autonomous_growth_claimed"] or
            row["stationary_or_exponential_claimed"]):
        raise AssertionError("dishonest IQC prefix-portfolio receipt")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    row = load_receipt()
    print(json.dumps(row, indent=2, sort_keys=True)
          if arguments.json else row["honest_status"])


if __name__ == "__main__":
    main()
