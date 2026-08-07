#!/usr/bin/env python3
"""Iterate safe latent-filtered recursive GCTS batches on the IQC control."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Dict, Sequence, Tuple

import materials_gcts_blind_continuation as blind
import materials_gcts_dag_blind_frontier as frontier
import materials_gcts_transform_dag as dag

Vector = Tuple[float, float, float]


@dataclass(frozen=True)
class IteratedDagWave:
    wave: int
    state_atoms_before: int
    level1_hypotheses: int
    level2_hypotheses: int
    parent_candidates: int
    score_strata_tried: int
    top_actions: int
    accepted_actions: int
    added_atoms: int
    correct_added_atoms: int
    precision: float
    cumulative_hidden_recall: float


@dataclass(frozen=True)
class IteratedDagGrowthResult:
    training_atoms: int
    initial_state_atoms: int
    hidden_atoms: int
    waves: Tuple[IteratedDagWave, ...]
    final_atoms: int
    final_correct_atoms: int
    final_precision: float
    final_hidden_recall: float
    stalled: bool


def _wave(
    state: Dict[Tuple[int, int, int], blind.AtomState],
    training,
    training_model,
    levels: Sequence[Sequence[dag.DagNode]],
    refinement: blind.LearnedGrammar,
    marking_nodes: Sequence[dag.DagNode],
    exterior_ports: Sequence[Sequence[frontier.ExteriorPort]],
    module_marking: frontier.ModuleMarking,
    confinement_radius: float,
) -> Tuple[Dict[Tuple[int, int, int], blind.AtomState], Dict[str, int]]:
    positions = tuple(atom.position for atom in state.values())
    species = tuple(atom.species for atom in state.values())
    _, oriented_levels, _ = frontier._match_state_levels(
        training.positions, training.species, training_model,
        positions, species)
    partial_level1 = frontier._partial_level1_hypotheses(
        levels[0], positions, species, training_model[0][0])
    level1 = frontier._beam_hypotheses(
        tuple(oriented_levels[0]) + partial_level1,
        maximum_per_center=4, maximum_total=500,
        frontier_first=True)
    level2 = frontier._beam_hypotheses(
        frontier._lift_hypotheses(
            levels[1], level1, minimum_matches=1),
        maximum_per_center=4, maximum_total=500,
        frontier_first=True)
    candidates = frontier._parent_candidates(levels[2], level2)
    candidates = frontier._rescore_with_overlap_marking(
        candidates, marking_nodes, level2)
    candidates = frontier._rescore_with_exterior_marking(
        candidates, exterior_ports, level2)
    current = frozenset(
        (key, atom.species) for key, atom in state.items())
    expansions = {
        node.type_id: dag.expand_node(levels, 3, node.type_id)
        for node in levels[2]}
    proposed = []
    for candidate in candidates:
        transformed = {
            (blind._site_key(point), chemical): point
            for chemical, offset in expansions[candidate.parent_type]
            for point in (dag._add(
                candidate.translation,
                dag._matvec(candidate.rotation, offset)),)
            if dag._norm(point) <= confinement_radius + 1e-5}
        new = {site: point for site, point in transformed.items()
               if site not in current}
        if new:
            proposed.append((candidate, new))
    if not proposed:
        return {}, {
            "level1": len(level1), "level2": len(level2),
            "candidates": len(candidates), "top": 0, "accepted": 0}
    expansion_cache: Dict[int, Tuple[Tuple[str, Vector], ...]] = {}
    ranking = sorted({
        (candidate.child_matches, round(candidate.exterior_score, 12))
        for candidate, _ in proposed}, reverse=True)
    actions = []
    strata_tried = 0
    for internal_score, exterior_score in ranking:
        strata_tried += 1
        for candidate, new in proposed:
            if (candidate.child_matches != internal_score or
                    round(candidate.exterior_score, 12) != exterior_score):
                continue
            marked = frontier._mark_new_sites(new, state, refinement)
            if not marked:
                continue
            lookahead, supported, _ = frontier._exterior_lookahead_score(
                candidate, exterior_ports[candidate.parent_type], levels,
                current, marked, confinement_radius, expansion_cache)
            if lookahead > 0:
                marked = supported
            marked = frontier._apply_module_marking(
                marked, module_marking)
            marked = frozenset(
                site for site in marked if site not in current)
            if marked:
                actions.append((lookahead, len(new), marked))
        if actions:
            break
    if not actions:
        return {}, {
            "level1": len(level1), "level2": len(level2),
            "candidates": len(candidates), "strata": strata_tried,
            "top": 0, "accepted": 0}
    best_lookahead = max(action[0] for action in actions)
    actions = [action for action in actions
               if abs(action[0] - best_lookahead) < 1e-9]
    additions: Dict[Tuple[int, int, int], blind.AtomState] = {}
    accepted = 0
    for _, _, marked in sorted(
            actions, key=lambda action: len(action[2]), reverse=True):
        pending = []
        conflict = False
        for key, chemical in marked:
            if key in additions:
                if additions[key].species != chemical:
                    conflict = True
                    break
                continue
            point = tuple(value * 1e-5 for value in key)
            if not blind._compatible_with_additions(
                    point, chemical, additions, refinement):
                conflict = True
                break
            pending.append((key, blind.AtomState(chemical, -1, point)))
        if conflict or not pending:
            continue
        additions.update(pending)
        accepted += 1
    return additions, {
        "level1": len(level1), "level2": len(level2),
        "candidates": len(candidates), "strata": strata_tried,
        "top": len(actions),
        "accepted": accepted}


def evaluate(maximum_waves: int = 6) -> IteratedDagGrowthResult:
    from materials_gcts_icosahedral_modelset import oracle_patch

    training, _ = oracle_patch(3, 9.0)
    oracle, _ = oracle_patch(4, 15.0)
    state, refinement = frontier._three_wave_state(training, oracle)
    initial_atoms = len(state)
    training_model = dag._learn_levels(
        training.positions, training.species, 3, 2.2)
    _, levels = dag.build_transform_dag(
        training.name, training.positions, training.species,
        prelearned=training_model)
    learned_levels = training_model[1]
    labels = training_model[2]
    child_rotations = dag._occurrence_rotations(
        2, learned_levels[1], labels[0], training.positions)
    parent_rotations = dag._occurrence_rotations(
        3, learned_levels[2], labels[1], training.positions)
    marking_nodes = frontier._overlap_marking_nodes(
        training.positions, training_model, child_rotations)
    exterior_ports = frontier._exterior_marking_ports(
        training.positions, training_model,
        child_rotations=child_rotations,
        parent_rotations=parent_rotations)
    module_marking = frontier._learn_module_marking(training)
    oracle_set = {(blind._site_key(point), chemical)
                  for point, chemical in zip(
                      oracle.positions, oracle.species)}
    hidden = len(oracle.positions) - len(training.positions)
    waves = []
    for wave_index in range(1, maximum_waves + 1):
        before = len(state)
        additions, counts = _wave(
            state, training, training_model, levels, refinement,
            marking_nodes, exterior_ports, module_marking, 15.0)
        if not additions:
            break
        correct_additions = sum(
            (key, atom.species) in oracle_set
            for key, atom in additions.items())
        state.update(additions)
        correct_total = sum(
            (key, atom.species) in oracle_set
            for key, atom in state.items())
        waves.append(IteratedDagWave(
            wave_index, before, counts["level1"], counts["level2"],
            counts["candidates"], counts["strata"], counts["top"],
            counts["accepted"],
            len(additions), correct_additions,
            correct_additions / len(additions),
            (correct_total - len(training.positions)) / hidden))
    correct = sum((key, atom.species) in oracle_set
                  for key, atom in state.items())
    return IteratedDagGrowthResult(
        len(training.positions), initial_atoms, hidden, tuple(waves),
        len(state), correct, correct / len(state),
        (correct - len(training.positions)) / hidden,
        len(waves) < maximum_waves)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--waves", type=int, default=6)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.waves)
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
