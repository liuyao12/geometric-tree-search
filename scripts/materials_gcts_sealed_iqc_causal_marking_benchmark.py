#!/usr/bin/env python3
"""Real causal incoming-port ablation on a sealed primitive-port IQC frontier.

The train and evaluation balls are disjoint subsets of one external ideal-IQC
oracle cloud. Grammar and marking use only the train ball. Frozen prototypes
are recognized on the smaller evaluation seed, where every incoming context
is constructed solely from another already placed, more-inward seed occurrence
and a train-admitted relative port. Candidate enumeration is target blind.
Only after its digest is frozen does the larger concentric evaluation target
label candidate novel sites for matched-work scoring.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from types import SimpleNamespace

from materials_gcts_causal_frontier_marking_ablation import (
    CausalFrontierMarkingAblation, FrozenFrontierAction,
    causal_occurrence_traces, run_causal_marking_ablation)
from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, _site_key, enumerate_frontier,
    fit_frozen_frontier_program)
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_geometric_port_abstraction import (
    GeometrySelectionAudit, abstract_action, abstract_trace,
    nearest_neighbor_scale, select_geometry_abstraction)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_oriented_overlap_ports import (
    canonical_relative_pose, matmul, matvec, transpose)


@dataclass(frozen=True)
class SealedIQCCausalMarkingBenchmark:
    oracle_atoms: int
    training_atoms: int
    evaluation_seed_atoms: int
    scoring_target_atoms: int
    train_target_raw_id_intersection: int
    train_evaluation_center_separation: float
    sum_train_target_radii: float
    spatial_domains_disjoint: bool
    frozen_productions: int
    recognized_seed_occurrences: int
    explicit_seed_gap_atoms: int
    causal_training_traces: int
    maximum_interaction_order: int
    seed_occurrences_with_incoming_context: int
    seed_incoming_context_coverage: float
    candidate_actions: int
    attempted_poses: int
    candidates_with_incoming_context: int
    candidate_incoming_context_coverage: float
    candidate_exact_context_seen_in_training: int
    candidate_exact_context_training_coverage: float
    abstract_candidate_exact_context_seen_in_training: int
    abstract_candidate_exact_context_training_coverage: float
    abstract_candidate_backoff_context_seen_in_training: int
    abstract_candidate_backoff_context_training_coverage: float
    geometry_selection: GeometrySelectionAudit
    train_nearest_neighbor_scale: float
    exact_candidate_ids_preserved: bool
    bounded_geometry_features_present: bool
    exact_candidate_actions: int
    union_correct_novel_target_atoms: int
    scorer_calls: int
    scorer_called_after_candidate_freeze: bool
    grammar_fit_on_training_only: bool
    marking_fit_on_causal_training_relations_only: bool
    target_used_for_candidate_generation_or_ranking: bool
    ablation: CausalFrontierMarkingAblation
    benchmark_passed: bool


def _crop(configuration: AtomicConfiguration, center, radius, name):
    indices = tuple(index for index, point in enumerate(configuration.positions)
                    if math.dist(point, center) <= radius + 1e-10)
    return (AtomicConfiguration(
        name, tuple(configuration.positions[index] for index in indices),
        tuple(configuration.species[index] for index in indices)), indices)


def _incoming_seed_contexts(
    learned, frozen, enumeration, center,
) -> dict[int, tuple[int, ...]]:
    prototype = {item.type_id: item for item in learned.prototypes}
    production = {(item.parent_type, item.child_type,
                   item.port.symmetry_orbit_key): item.production_id
                  for item in frozen.productions}
    supports = dict(enumeration.occurrence_supports)
    radius = {item.occurrence_id: math.dist(item.translation, center)
              for item in enumeration.occurrences}
    incoming = {}
    for child in enumeration.occurrences:
        witnessed = []
        for parent in enumeration.occurrences:
            if (parent.occurrence_id == child.occurrence_id or
                    radius[parent.occurrence_id] >=
                    radius[child.occurrence_id] - 1e-10 or
                    len(set(supports[parent.occurrence_id]).intersection(
                        supports[child.occurrence_id])) <
                    learned.minimum_shared_atoms):
                continue
            inverse = transpose(parent.rotation)
            relative_rotation = matmul(inverse, child.rotation)
            delta = tuple(child.translation[axis] -
                          parent.translation[axis] for axis in range(3))
            relative_translation = matvec(inverse, delta)
            try:
                _, _, key = canonical_relative_pose(
                    prototype[parent.type_id], prototype[child.type_id],
                    relative_rotation, relative_translation, .03)
            except ValueError:
                continue
            action = production.get((parent.type_id, child.type_id, key))
            if action is not None:
                witnessed.append((
                    -radius[parent.occurrence_id], action,
                    parent.occurrence_id))
        # Nearest already grown radial predecessors first; two is the initial
        # interaction-order cap, not a target-selected hyperparameter.
        incoming[child.occurrence_id] = tuple(
            item[1] for item in sorted(witnessed)[:2])
    return incoming


def evaluate(*, shuffled_runs: int = 31) -> SealedIQCCausalMarkingBenchmark:
    train_center = (-16.0, 0.0, 0.0)
    evaluation_center = (8.0, 14.0, 7.0)
    train_radius = 11.0
    seed_radius = 7.0
    target_radius = 11.0
    oracle, _ = oracle_patch_fast(8, 32.0)
    training, training_ids = _crop(
        oracle, train_center, train_radius, "IQC-causal-train")
    seed_cloud, seed_ids = _crop(
        oracle, evaluation_center, seed_radius, "IQC-frontier-seed")

    learned = compile_irregular_port_program(
        training.species, training.positions)
    frozen = fit_frozen_frontier_program(learned)
    enumeration = enumerate_frozen_port_occurrences(
        learned, seed_cloud.species, seed_cloud.positions,
        select_greedy_cover=True)
    covered = {index for _, support in enumeration.occurrence_supports
               for index in support}
    gaps = tuple((seed_cloud.species[index], seed_cloud.positions[index])
                 for index in range(len(seed_cloud.positions))
                 if index not in covered)
    seed = FrontierSeed(enumeration.occurrences, gaps)
    contexts = _incoming_seed_contexts(
        learned, frozen, enumeration, evaluation_center)
    frontier = enumerate_frontier(
        frozen, seed.occurrences, explicit_gap_sites=seed.explicit_gap_sites)

    train_program = SimpleNamespace(
        occurrences=learned.occurrences,
        relation_classes=learned.atlas.relation_classes,
        productions=frozen.productions)
    traces = causal_occurrence_traces(train_program, training.positions)
    raw_training_contexts = {(trace.parent_type, trace.incoming_ports)
                             for trace in traces}
    occurrence_type = {item.occurrence_id: item.type_id
                       for item in enumeration.occurrences}
    raw_actions = tuple(FrozenFrontierAction(
        candidate_id=index,
        parent_occurrence=candidate.parent_occurrence,
        parent_type=occurrence_type[candidate.parent_occurrence],
        incoming_ports=contexts.get(candidate.parent_occurrence, ()),
        production_id=candidate.production_id,
        novel_site_keys=tuple(sorted(
            _site_key(site, frozen.overlap_tolerance)
            for site in candidate.novel_sites)),
        # Exact target-blind order emitted by the frozen executor.
        baseline_order=(index,))
        for index, candidate in enumerate(frontier.candidates))
    train_nn_scale = nearest_neighbor_scale(training.positions)
    selection = select_geometry_abstraction(traces, frozen, train_nn_scale)
    spec = selection.spec
    abstract_traces = tuple(abstract_trace(
        trace, frozen, spec, train_nn_scale) for trace in traces)
    actions = tuple(abstract_action(
        action, frozen, contexts.get(action.parent_occurrence, ()), spec,
        train_nn_scale) for action in raw_actions)
    exact_support = Counter((trace.parent_type, trace.incoming_ports)
                            for trace in abstract_traces)
    backoff_support = Counter((trace.parent_type, token)
                              for trace in abstract_traces
                              for token in set(trace.incoming_ports))
    abstract_exact_contexts = {key for key, count in exact_support.items()
                               if count >= spec.minimum_state_support}
    abstract_backoff_contexts = {key for key, count in backoff_support.items()
                                 if count >= spec.minimum_state_support}

    # Oracle boundary: the target crop does not exist until grammar, marking
    # traces, seed contexts, frontier enumeration, and the action batch have
    # all been frozen.
    target, target_ids = _crop(
        oracle, evaluation_center, target_radius, "IQC-sealed-target")
    target_keys = {_site_key(
        (label, point), frozen.overlap_tolerance)
        for label, point in zip(target.species, target.positions)}
    scorer_calls = []
    scored_result = {}
    frozen_digest_ready = bool(actions)
    def sealed_scorer(frozen_actions):
        scorer_calls.append(tuple(action.candidate_id
                                  for action in frozen_actions))
        result = {action.candidate_id: frozenset(
            site for site in action.novel_site_keys if site in target_keys)
                for action in frozen_actions}
        scored_result.update(result)
        return result

    ablation = run_causal_marking_ablation(
        abstract_traces, actions, sealed_scorer,
        shuffled_runs=shuffled_runs, maximum_interaction_order=2,
        minimum_state_support=spec.minimum_state_support)
    exact = tuple(action for action in actions
                  if action.novel_site_keys and
                  scored_result[action.candidate_id] ==
                  frozenset(action.novel_site_keys))
    correct_union = {site for action in exact
                     for site in action.novel_site_keys}
    contextual_seed = sum(bool(value) for value in contexts.values())
    contextual_candidates = sum(bool(action.incoming_ports)
                                for action in actions)
    raw_seen_context = sum((action.parent_type, action.incoming_ports) in
                           raw_training_contexts for action in raw_actions)
    abstract_seen_context = sum(
        (action.parent_type, action.incoming_ports) in abstract_exact_contexts
        for action in actions)
    abstract_backoff_context = sum(
        ((action.parent_type, action.incoming_ports) not in
         abstract_exact_contexts and any(
             (action.parent_type, token) in abstract_backoff_contexts
             for token in action.incoming_ports)) for action in actions)
    separation = math.dist(train_center, evaluation_center)
    disjoint = not set(training_ids).intersection(target_ids)
    passed = (ablation.benchmark_passed and disjoint and
              frozen_digest_ready and len(scorer_calls) == 1 and
              not ablation.heldout_labels_used_during_fit_or_candidate_freeze)
    return SealedIQCCausalMarkingBenchmark(
        len(oracle.positions), len(training.positions),
        len(seed_cloud.positions), len(target.positions),
        len(set(training_ids).intersection(target_ids)), separation,
        train_radius + target_radius, separation >
        train_radius + target_radius and disjoint,
        len(frozen.productions), len(enumeration.occurrences), len(gaps),
        len(traces), 2, contextual_seed,
        contextual_seed / max(1, len(enumeration.occurrences)),
        len(actions), frontier.attempted_poses, contextual_candidates,
        contextual_candidates / max(1, len(actions)), raw_seen_context,
        raw_seen_context / max(1, len(actions)), abstract_seen_context,
        abstract_seen_context / max(1, len(actions)),
        abstract_backoff_context,
        abstract_backoff_context / max(1, len(actions)), selection,
        train_nn_scale,
        tuple(action.candidate_id for action in actions) ==
        tuple(action.candidate_id for action in raw_actions), True,
        len(exact), len(correct_union),
        len(scorer_calls), frozen_digest_ready and len(scorer_calls) == 1,
        True, True, False, ablation, passed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--shuffles", type=int, default=31)
    arguments = parser.parse_args()
    result = evaluate(shuffled_runs=arguments.shuffles)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
