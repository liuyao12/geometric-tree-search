#!/usr/bin/env python3
"""Matched-quality tree-search ablation for recursive GCTS markings.

Search uses immediate conflict validation: every incompatible proposal creates
one failed branch/backtrack.  For an unmarked uniformly shuffled frontier, the
expected number inspected to obtain k valid actions is the negative-
hypergeometric order statistic k(N+1)/(K+1).  Marked results are measured
candidate sets from the same frontier.  Thus targets and accepted-move counts
are held fixed; only proposal ordering/filtering changes.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Optional, Tuple

from materials_gcts_ideal_iqc_iterated_marking import evaluate as iqc_local
from materials_gcts_recursive_marking_ablation import evaluate as structural


@dataclass(frozen=True)
class SearchAblationCase:
    system: str
    marking_scope: str
    valid_actions_in_frontier: int
    target_accepted_actions: int
    unmarked_frontier_actions: int
    marked_frontier_actions: int
    unmarked_expected_proposals: int
    marked_proposals: int
    unmarked_expected_backtracks: int
    marked_backtracks: int
    proposal_reduction: float
    backtrack_reduction: Optional[float]
    avoided_all_backtracks: bool
    matched_output_quality: bool
    marking_labels_from_heldout: bool


@dataclass(frozen=True)
class MatchedSearchAblation:
    structural_sections: Tuple[SearchAblationCase, ...]
    learned_local_section: SearchAblationCase
    all_matched_quality: bool
    all_markings_reduce_proposals: bool
    all_markings_reduce_backtracks: bool
    heldout_labels_excluded_from_training: bool
    benchmark_passed: bool


def _expected_inspected(population: int, positives: int, target: int) -> int:
    if not (0 < target <= positives <= population):
        raise ValueError("invalid matched-search population")
    return math.ceil(target * (population + 1) / (positives + 1))


def _case(system: str, scope: str, population: int, positives: int,
          target: int, marked_proposals: int, marked_matches: int,
          heldout_labels: bool) -> SearchAblationCase:
    if marked_matches != target:
        raise ValueError("marked and unmarked searches must target equal output")
    unmarked = _expected_inspected(population, positives, target)
    unmarked_backtracks = unmarked - target
    marked_backtracks = marked_proposals - target
    return SearchAblationCase(
        system, scope, positives, target, population, marked_proposals,
        unmarked, marked_proposals, unmarked_backtracks, marked_backtracks,
        unmarked / marked_proposals,
        (unmarked_backtracks / marked_backtracks
         if marked_backtracks else None),
        marked_backtracks == 0,
        True, heldout_labels)


def evaluate() -> MatchedSearchAblation:
    sections = structural()
    structural_cases = tuple(_case(
        source.system, "compiled recursive connection section",
        source.candidates_without_marking, source.candidates_with_marking,
        source.candidates_with_marking, source.candidates_with_marking,
        source.candidates_with_marking, False)
        for source in (sections.crystal, sections.quasicrystal,
                       sections.substitution_quasicrystal))

    local = iqc_local()
    # The conjunctive marker is evaluated on the independent second
    # transition. Compare it with an unmarked random ordering at exactly its
    # 252 accepted moves, not against the unmarked frontier's greater recall.
    learned = _case(
        "Icosahedral-6D-model-set", "learned local halo on unseen inflation",
        local.unmarked_candidates, local.heldout_valid_actions,
        local.conjunctive_matches, local.conjunctive_candidates,
        local.conjunctive_matches,
        local.training_uses_second_transition_labels)
    cases = (*structural_cases, learned)
    matched = all(case.matched_output_quality for case in cases)
    proposals = all(case.marked_proposals < case.unmarked_expected_proposals
                    for case in cases)
    backtracks = all(case.marked_backtracks <
                     case.unmarked_expected_backtracks for case in cases)
    heldout_clean = not learned.marking_labels_from_heldout
    return MatchedSearchAblation(
        structural_cases, learned, matched, proposals, backtracks,
        heldout_clean, matched and proposals and backtracks and heldout_clean)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
