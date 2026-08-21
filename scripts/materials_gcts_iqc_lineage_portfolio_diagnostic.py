#!/usr/bin/env python3
"""Consumed-target diagnosis of lineage-balanced IQC marking supply.

The candidate tree is built completely from the frozen prefix and rollout
models before the already-consumed confirmation target is reconstructed.  It
uses a predeclared 2→4→8 parent×marking schedule: every retained parent keeps
one connection head and one rollout head when the physical states differ.
This is a candidate-supply audit, never a fresh confirmation or value claim.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_frozen_stage_local_margin_marking import (
    load_default_model as load_prefix_model)
from materials_gcts_iqc_frozen_stage_local_rollout_value import (
    load_default_model as load_rollout_model)
from materials_gcts_iqc_obligation_expanded_dataset import _digest, _site_key
from materials_gcts_iqc_stage_local_marking_portfolio import (
    execute_iqc_stage_local_marking_portfolio)
from materials_gcts_iqc_stage_local_rollout_confirmation_preregistration import (
    audit as preregistration_audit)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


BEAM_SCHEDULE = (2, 4, 8)
ALLOCATION = "parent-marking-round-robin"


@dataclass(frozen=True)
class IQCLineagePortfolioDiagnostic:
    center: tuple[float, float, float]
    seed_atoms: int
    target_atoms: int
    beam_schedule: tuple[int, ...]
    allocation: str
    physical_expansions: int
    expansion_candidate_counts: tuple[int, ...]
    level_candidate_counts: tuple[int, ...]
    level_unique_state_counts: tuple[int, ...]
    level_retained_state_counts: tuple[int, ...]
    terminal_correct_sites: tuple[int, ...]
    terminal_wrong_sites: tuple[int, ...]
    terminal_exact: tuple[bool, ...]
    exact_terminal_supply: int
    pretarget_execution_digest: str
    target_opened_after_tree_froze: bool
    target_used_during_tree: bool
    consumed_target_diagnostic_only: bool
    autonomous_growth_claimed: bool
    stationary_or_exponential_claimed: bool
    honest_status: str


def evaluate() -> IQCLineagePortfolioDiagnostic:
    protocol = preregistration_audit()
    seed, _ = oracle_crop_fast(
        protocol.confirmation_center, protocol.seed_radius)
    result = execute_iqc_stage_local_marking_portfolio(
        load_default_runtime(), load_prefix_model(), load_rollout_model(),
        center=protocol.confirmation_center,
        seed_positions=seed.positions, seed_species=seed.species,
        public_radius=protocol.target_radius, blocks=3, beam_width=8,
        beam_schedule=BEAM_SCHEDULE, allocation=ALLOCATION)
    if result.target_api_present or result.target_used or \
            result.tree.target_api_present or result.tree.target_used:
        raise AssertionError("target-tainted lineage portfolio")
    execution_body = {
        "center": result.center,
        "seed_atoms": result.seed_atoms,
        "schedule": result.beam_schedule,
        "allocation": result.allocation,
        "levels": tuple((level.candidate_digest,
                         level.retained_action_paths,
                         level.retained_state_keys)
                        for level in result.tree.levels),
        "terminal_states": tuple(node.state_key for node in result.tree.retained),
    }
    execution_digest = _digest(execution_body)

    # This target was consumed by the frozen rollout confirmation.  It is
    # reconstructed only after every candidate, score, and retained state is
    # immutable, and is used solely to label the diagnostic tree.
    target, _ = oracle_crop_fast(
        protocol.confirmation_center, protocol.target_radius)
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    correct, wrong, exact = [], [], []
    for node in result.tree.retained:
        additions = tuple(zip(node.state.positions[len(seed.positions):],
                              node.state.species[len(seed.species):]))
        if len(additions) != 9:
            raise AssertionError("three blocks must add nine colored sites")
        count = sum(truth.get(_site_key(point)) == str(color)
                    for point, color in additions)
        correct.append(count)
        wrong.append(len(additions) - count)
        exact.append(count == len(additions))
    supply = sum(exact)
    status = ("lineage-balanced tree contains an exact three-block terminal"
              if supply else
              "lineage-balanced widening still has no exact terminal")
    return IQCLineagePortfolioDiagnostic(
        tuple(map(float, result.center)), len(seed.positions),
        len(target.positions), BEAM_SCHEDULE, ALLOCATION,
        len(result.expansion_candidate_counts),
        result.expansion_candidate_counts,
        tuple(level.candidate_count for level in result.tree.levels),
        tuple(level.unique_state_count for level in result.tree.levels),
        tuple(len(level.retained_state_keys) for level in result.tree.levels),
        tuple(correct), tuple(wrong), tuple(exact), supply, execution_digest,
        True, False, True, False, False, status)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
