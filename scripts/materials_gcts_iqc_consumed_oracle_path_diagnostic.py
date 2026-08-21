#!/usr/bin/env python3
"""Locate candidate-supply failure on the consumed IQC confirmation.

This intentionally uses the already-consumed target to choose a branch after
each candidate batch.  It is a diagnostic oracle, not GCTS execution, and can
never pass an autonomous or confirmation gate.  Its only purpose is to tell
whether the frozen target-free candidate generator contains a three-block
exact path when beam/value pruning is removed from the decision.
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
from materials_gcts_iqc_obligation_expanded_dataset import _site_key
from materials_gcts_iqc_stage_local_rollout_confirmation_preregistration import (
    audit as preregistration_audit)
from materials_gcts_iqc_stage_local_rollout_runtime import (
    execute_stage_local_rollout_search)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


@dataclass(frozen=True)
class ConsumedOraclePathBlock:
    block: int
    candidate_count: int
    exact_candidate_count: int
    best_correct_sites: int
    selected_index: int
    selected_correct_sites: int
    selected_exact: bool


@dataclass(frozen=True)
class ConsumedOraclePathDiagnostic:
    center: tuple[float, float, float]
    seed_atoms: int
    target_atoms: int
    blocks: tuple[ConsumedOraclePathBlock, ...]
    exact_three_block_path_supplied: bool
    first_supply_failure_block: int | None
    target_used_for_branch_choice: bool
    consumed_target_diagnostic_only: bool
    autonomous_growth_claimed: bool
    honest_status: str


def evaluate():
    protocol = preregistration_audit()
    seed, _ = oracle_crop_fast(
        protocol.confirmation_center, protocol.seed_radius)
    target, _ = oracle_crop_fast(
        protocol.confirmation_center, protocol.target_radius)
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    runtime, prefix, rollout = (
        load_default_runtime(), load_prefix_model(), load_rollout_model())
    positions, species = tuple(seed.positions), tuple(seed.species)
    rows = []
    for block in range(1, protocol.self_fed_blocks + 1):
        result = execute_stage_local_rollout_search(
            runtime, prefix, rollout, center=protocol.confirmation_center,
            seed_positions=positions, seed_species=species,
            public_radius=protocol.target_radius)
        if result.target_api_present or result.target_used:
            raise AssertionError("target leaked into candidate generation")
        counts = []
        for candidate in result.candidates:
            additions = candidate.state.positions[len(positions):]
            colors = candidate.state.species[len(species):]
            counts.append(sum(truth.get(_site_key(point)) == str(color)
                              for point, color in zip(additions, colors)))
        exact = tuple(index for index, count in enumerate(counts)
                      if count == 3)
        selected = min(range(len(counts)), key=lambda index: (
            -counts[index], repr(result.candidates[index].action_key)))
        rows.append(ConsumedOraclePathBlock(
            block, len(counts), len(exact), max(counts), selected,
            counts[selected], counts[selected] == 3))
        state = result.candidates[selected].state
        positions, species = tuple(state.positions), tuple(state.species)
    first = next((row.block for row in rows if not row.selected_exact), None)
    supplied = first is None
    return ConsumedOraclePathDiagnostic(
        tuple(map(float, protocol.confirmation_center)), len(seed.positions),
        len(target.positions), tuple(rows), supplied, first, True, True, False,
        ("complete frozen candidate generator supplies an exact path"
         if supplied else f"candidate supply first fails at block {first}"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
