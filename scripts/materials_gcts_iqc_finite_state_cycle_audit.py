#!/usr/bin/env python3
"""Necessary-evidence audit for finite-state cycles in the current IQC hierarchy."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_iqc_max5_transfer_claim_audit import evaluate as max5_audit


@dataclass(frozen=True)
class IQCFiniteStateCycleAudit:
    positive_train_levels: int
    positive_heldout_reencoding_levels: int
    minimum_levels_for_two_state_two_traversal_cycle: int
    observed_adjacent_transitions: int
    train_exact_production_records_adapted: int
    train_adjacent_exact_state_intersections: tuple[int, ...]
    train_three_level_exact_state_intersections: tuple[int, ...]
    child_arity_histograms_by_level: tuple[tuple[tuple[int, int], ...], ...]
    enough_levels_to_learn_nontrivial_cycle: bool
    heldout_scale_independently_observed: bool
    finite_state_cycle_recurrence: bool
    stationary_gate_weakened: bool
    heldout_reencoding: bool
    autonomous_growth: bool
    target_used_to_select_cycle: bool
    shuffled_transition_control_pass_required: bool
    chemistry_population_port_control_pass_required: bool
    conclusion: str


def evaluate() -> IQCFiniteStateCycleAudit:
    current = max5_audit()
    levels = len(current.selected_types_by_level)
    minimum = 5  # Derived as 2*p+1 for the smallest nontrivial p=2 cycle.
    enough = levels >= minimum
    # The heldout hierarchy is frozen exact re-encoding.  It tests whether
    # train states deploy, but does not independently learn a new geometric
    # scale and therefore cannot confirm a substitution cycle.
    heldout_independent_scale = False
    recurrent = False
    conclusion = (
        "red: the current IQC recurrent core has four positive train and "
        "heldout-reencoding levels, but a nontrivial two-state cycle needs "
        "five consecutive levels to witness both directed transitions twice; "
        "furthermore heldout levels replay frozen prototypes and do not "
        "independently observe hierarchy scale")
    return IQCFiniteStateCycleAudit(
        levels, len(current.exact_raw_support_size_histograms_by_level),
        minimum, max(0, levels - 1), current.strict_adapted_records,
        current.common_normalized_production_keys_by_adjacent_levels,
        current.common_normalized_production_keys_by_three_levels,
        current.child_arity_histograms_by_level, enough,
        heldout_independent_scale, recurrent, False, True, False, False,
        True, True, conclusion)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
