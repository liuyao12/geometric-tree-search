#!/usr/bin/env python3
"""Consumed-target supply audit for the prefix marking portfolio.

Candidate construction and both marking orders are target-free.  The consumed
target is then used to choose an exact candidate when one exists so the next
self-fed block can be diagnosed.  This is not an autonomous selector result.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_frozen_stage_local_margin_marking import (
    load_default_model as load_prefix_model)
from materials_gcts_iqc_obligation_expanded_dataset import _site_key
from materials_gcts_iqc_prefix_marking_portfolio import (
    PREFIX_PORTFOLIO_BUDGET, build_stage_local_prefix_portfolio_tree)
from materials_gcts_iqc_stage_local_rollout_confirmation_preregistration import (
    audit as preregistration_audit)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


@dataclass(frozen=True)
class PrefixPortfolioBlock:
    block: int
    candidate_counts_by_depth: tuple[int, ...]
    retained_counts_by_depth: tuple[int, ...]
    terminal_candidates: int
    exact_candidates: int
    best_correct_sites: int
    selected_correct_sites: int
    selected_exact: bool


@dataclass(frozen=True)
class PrefixPortfolioConsumedDiagnostic:
    center: tuple[float, float, float]
    seed_atoms: int
    target_atoms: int
    retained_budget: tuple[int, ...]
    blocks: tuple[PrefixPortfolioBlock, ...]
    exact_three_block_path_supplied: bool
    first_supply_failure_block: int | None
    candidate_generation_target_free: bool
    target_used_for_posthoc_branch_choice: bool
    consumed_target_diagnostic_only: bool
    autonomous_growth_claimed: bool
    honest_status: str


def evaluate(candidate_reach=None, retained_budget=None,
             allocation="parent-marking-round-robin"):
    protocol = preregistration_audit()
    seed, _ = oracle_crop_fast(
        protocol.confirmation_center, protocol.seed_radius)
    target, _ = oracle_crop_fast(
        protocol.confirmation_center, protocol.target_radius)
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    runtime, prefix = load_default_runtime(), load_prefix_model()
    reach = (tuple(map(int, candidate_reach))
             if candidate_reach is not None else tuple(prefix.candidate_reach))
    budget = (tuple(map(int, retained_budget))
              if retained_budget is not None else PREFIX_PORTFOLIO_BUDGET)
    frontier = ((tuple(seed.positions), tuple(seed.species)),)
    blocks = []
    first_failure = None
    for block in range(1, protocol.self_fed_blocks + 1):
        depth_counts, retained_counts = [0, 0, 0], [0, 0, 0]
        candidates, scores = [], []
        exact_states = {}
        for positions, species in frontier:
            _source, tree = build_stage_local_prefix_portfolio_tree(
                runtime, prefix, center=protocol.confirmation_center,
                seed_positions=positions, seed_species=species,
                public_radius=protocol.target_radius, candidate_reach=reach,
                retained_budget=budget, allocation=allocation)
            if tree.target_api_present or tree.target_used:
                raise AssertionError("target leaked into prefix portfolio")
            for index, level in enumerate(tree.levels):
                depth_counts[index] += level.candidate_count
                retained_counts[index] += len(level.retained_state_keys)
            for node in tree.retained:
                candidate = node.state
                additions = candidate.positions[len(positions):]
                colors = candidate.species[len(species):]
                score = sum(truth.get(_site_key(point)) == str(color)
                            for point, color in zip(additions, colors))
                candidates.append(candidate)
                scores.append(score)
                if score == 3:
                    exact_states[node.state_key] = (
                        tuple(candidate.positions), tuple(candidate.species))
        supplied = bool(exact_states)
        best = max(scores)
        blocks.append(PrefixPortfolioBlock(
            block, tuple(depth_counts), tuple(retained_counts), len(candidates),
            len(exact_states), best, best, supplied))
        if not supplied:
            first_failure = block
            break
        frontier = tuple(exact_states[key] for key in sorted(exact_states))
    complete = len(blocks) == protocol.self_fed_blocks and \
        all(row.selected_exact for row in blocks)
    return PrefixPortfolioConsumedDiagnostic(
        tuple(map(float, protocol.confirmation_center)), len(seed.positions),
        len(target.positions), budget, tuple(blocks),
        complete, first_failure, True, True, True, False,
        ("prefix marking portfolio supplies an exact three-block path"
         if complete else
         f"prefix marking portfolio first loses supply at block {first_failure}"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--candidate-reach", nargs=3, type=int)
    parser.add_argument("--retained-budget", nargs=3, type=int)
    parser.add_argument(
        "--allocation", choices=("parent-marking-round-robin",
                                  "global-marking-round-robin"),
        default="parent-marking-round-robin")
    arguments = parser.parse_args()
    result = evaluate(arguments.candidate_reach, arguments.retained_budget,
                      arguments.allocation)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
