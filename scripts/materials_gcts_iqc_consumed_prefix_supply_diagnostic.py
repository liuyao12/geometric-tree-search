#!/usr/bin/env python3
"""Exhaust exact-prefix supply on the consumed IQC confirmation.

Unlike the autonomous executor, this diagnostic opens the consumed target and
uses it after each atomic action to retain only exact prefixes.  It therefore
cannot be a search result.  It isolates whether the frozen 12→4→8 proposal
reach contains any exact three-site block before the learned depth marking
prunes the prefix tree to 4→8→8 states.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from types import SimpleNamespace

from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, action_key)
from materials_gcts_iqc_frozen_stage_local_margin_marking import (
    load_default_model as load_prefix_model)
from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_obligation_expanded_dataset import _site_key
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_stage_local_prefix_dataset import _seed_frontier
from materials_gcts_iqc_stage_local_rollout_confirmation_preregistration import (
    audit as preregistration_audit)
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_pose_port_state_marking import score_pose_port_state


@dataclass(frozen=True)
class PrefixSupplyBlock:
    block: int
    candidate_counts: tuple[int, ...]
    exact_prefix_counts: tuple[int, ...]
    exact_block_supplied: bool


@dataclass(frozen=True)
class ConsumedPrefixSupplyDiagnostic:
    center: tuple[float, float, float]
    seed_atoms: int
    target_atoms: int
    candidate_reach: tuple[int, ...]
    autonomous_retained_budget: tuple[int, ...]
    blocks: tuple[PrefixSupplyBlock, ...]
    exact_three_block_path_in_raw_reach: bool
    first_raw_supply_failure_block: int | None
    target_used_to_prune_prefixes: bool
    consumed_target_diagnostic_only: bool
    autonomous_growth_claimed: bool
    honest_status: str


def _exact_prefix_trace(runtime, *, center, positions, species, public_radius,
                        reach, truth):
    source = SimpleNamespace(
        group=tuple(map(float, center)),
        seed_positions=tuple(tuple(map(float, point)) for point in positions),
        seed_species=tuple(map(str, species)))
    frontier = _seed_frontier(runtime, source, public_radius)
    states = (FusionSearchState(
        source.seed_positions, source.seed_species, frontier,
        (), (), (), 0., ()),)
    counts, exact_counts, exact_states = [], [], []
    for local_reach in reach:
        children = {}
        for state in states:
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
                -score_pose_port_state(
                    runtime["state_model"], descriptors[point]),
                -state.proposals.votes[point], point)))[:local_reach]
            for point in ordered:
                candidate = _child(
                    source, runtime["connection"], runtime["state_model"],
                    state, point, descriptors[point], public_radius)
                key = action_key(candidate.actions)
                prior = children.get(key)
                if prior is None or (candidate.cumulative, candidate.actions) > \
                        (prior.cumulative, prior.actions):
                    children[key] = candidate
        stage = tuple(children.values())
        exact = tuple(state for state in stage if all(
            truth.get(_site_key(point)) == str(color)
            for point, color in zip(
                state.positions[len(positions):],
                state.species[len(species):])))
        counts.append(len(stage))
        exact_counts.append(len(exact))
        exact_states.append(exact)
        states = exact
        if not states:
            counts.extend(0 for _ in range(len(reach) - len(counts)))
            exact_counts.extend(0 for _ in range(
                len(reach) - len(exact_counts)))
            break
    return tuple(counts), tuple(exact_counts), tuple(exact_states)


def _exact_prefixes(runtime, *, center, positions, species, public_radius,
                    reach, truth):
    counts, exact_counts, trace = _exact_prefix_trace(
        runtime, center=center, positions=positions, species=species,
        public_radius=public_radius, reach=reach, truth=truth)
    states = trace[-1] if len(trace) == len(reach) else ()
    states = tuple(sorted(states, key=lambda row: repr(action_key(row.actions))))
    return counts, exact_counts, states


def evaluate(candidate_reach=None):
    protocol = preregistration_audit()
    model = load_prefix_model()
    runtime = load_default_runtime()
    seed, _ = oracle_crop_fast(
        protocol.confirmation_center, protocol.seed_radius)
    target, _ = oracle_crop_fast(
        protocol.confirmation_center, protocol.target_radius)
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    reach = (tuple(map(int, candidate_reach)) if candidate_reach is not None
             else tuple(model.candidate_reach))
    if len(reach) != 3 or any(value < 1 for value in reach):
        raise ValueError("candidate reach must contain three positive widths")
    positions, species = tuple(seed.positions), tuple(seed.species)
    blocks = []
    first_failure = None
    for block in range(1, protocol.self_fed_blocks + 1):
        counts, exact_counts, exact = _exact_prefixes(
            runtime, center=protocol.confirmation_center,
            positions=positions, species=species,
            public_radius=protocol.target_radius,
            reach=reach, truth=truth)
        supplied = bool(exact)
        blocks.append(PrefixSupplyBlock(
            block, counts, exact_counts, supplied))
        if not supplied:
            first_failure = block
            break
        state = exact[0]
        positions, species = tuple(state.positions), tuple(state.species)
    complete = len(blocks) == protocol.self_fed_blocks and \
        all(block.exact_block_supplied for block in blocks)
    return ConsumedPrefixSupplyDiagnostic(
        tuple(map(float, protocol.confirmation_center)), len(seed.positions),
        len(target.positions), reach,
        tuple(model.retained_prefix_budget), tuple(blocks), complete,
        first_failure, True, True, False,
        ("raw frozen reach contains an exact three-block path"
         if complete else
         f"raw proposal reach first loses exact supply at block {first_failure}"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--candidate-reach", nargs=3, type=int)
    arguments = parser.parse_args()
    result = evaluate(arguments.candidate_reach)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
