#!/usr/bin/env python3
"""31-shuffle causal audit of incoming-port context on dense NaCl growth."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
import json
import math
from statistics import median

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_dense_nacl_context_marking import (
    connection_traces, fit_causal_connection_marking, guarded_trace_split,
    rank_key, shuffle_trace_labels)
from materials_gcts_dense_nacl_marking_benchmark import MatchedWork
from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_derivation import (
    _compile_productions, _site_key, execute_macro_derivation,
    score_macro_derivation)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, canonical_relative_pose, matmul, matvec, transpose)
from materials_gcts_periodic_growth import replicate
from materials_gcts_port_graph_macros import mine_port_graph_macros


@dataclass(frozen=True)
class IncomingContextEquivarianceAudit:
    training_atoms: int
    seed_atoms: int
    frozen_candidate_actions: int
    maximum_interaction_order: int
    training_traces: int
    validation_traces: int
    guarded_occurrence_domains_disjoint: bool
    validation_top_one: float
    live_exact_context_coverage: float
    matched_correct_novel_atoms: int
    marked: MatchedWork
    unmarked: MatchedWork
    shuffled_median_proposals: float
    shuffled_median_wrong_plus_backtracks: float
    shuffled_best_wrong_plus_backtracks: int
    shuffled_runs: int
    empirical_work_p_value: float
    identical_frozen_candidates: bool
    target_global_frame_radius_unused_by_marking: bool
    grammar_and_marking_fit_on_independent_train_cloud: bool
    evaluation_outer_shell_used_during_fit_or_ranking: bool
    equivariance_or_in_sample_diagnostic_only: bool
    causal_gate_passed: bool
    integrated_as_default_policy: bool


def _curve(derivation, target_keys):
    proposed = correct = 0
    result = []
    for index, step in enumerate(derivation.steps, 1):
        emitted = step.certificate.emitted_sites
        proposed += len(emitted)
        correct += sum(key in target_keys for key in emitted)
        result.append((index, proposed, correct))
    return tuple(result)


def _top_one(marking, traces):
    correct = 0
    for trace in traces:
        actions = marking.marginal.get(trace.parent_type, {})
        candidates = set(actions)
        candidates.add(trace.chosen_outgoing_port)
        chosen = min(candidates, key=lambda action: rank_key(
            marking, trace.parent_type, trace.incoming_ports, action,
            0, 0, trace.center_occurrence))
        correct += chosen == trace.chosen_outgoing_port
    return correct / len(traces)


def _frozen_seed_atomic_program(source, species, positions):
    """Enumerate source-frozen atomic supports/ports on seed atoms only."""
    frozen = enumerate_frozen_port_occurrences(
        source, species, positions, select_greedy_cover=False)
    occurrence = {item.occurrence_id: item for item in frozen.occurrences}
    support = dict(frozen.occurrence_supports)
    prototype = {item.type_id: item for item in source.prototypes}
    frozen_keys = {(item.parent_type, item.child_type,
                    item.symmetry_orbit_key) for item in source.atlas.ports}
    relations = []
    for parent in frozen.occurrences:
        for child in frozen.occurrences:
            if parent.occurrence_id == child.occurrence_id:
                continue
            if len(set(support[parent.occurrence_id]).intersection(
                    support[child.occurrence_id])) < source.minimum_shared_atoms:
                continue
            inverse = transpose(parent.rotation)
            relative_rotation = matmul(inverse, child.rotation)
            delta = tuple(child.translation[axis] - parent.translation[axis]
                          for axis in range(3))
            relative_translation = matvec(inverse, delta)
            try:
                _, _, key = canonical_relative_pose(
                    prototype[parent.type_id], prototype[child.type_id],
                    relative_rotation, relative_translation, .03)
            except ValueError:
                continue
            frozen_key = parent.type_id, child.type_id, key
            if frozen_key in frozen_keys:
                relations.append((parent.occurrence_id, child.occurrence_id,
                                  parent.type_id, child.type_id, key))
    atlas = replace(source.atlas, relation_classes=tuple(relations),
                    witnessed_relations=len(relations))
    return replace(source, occurrences=frozen.occurrences,
                   occurrence_supports=frozen.occurrence_supports,
                   atlas=atlas)


def evaluate(*, shuffled_runs: int = 31) -> IncomingContextEquivarianceAudit:
    if shuffled_runs < 3:
        raise ValueError("at least three shuffled controls are required")
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    evaluation_rotation = ((0., -1., 0.), (1., 0., 0.), (0., 0., 1.))
    evaluation_shift = (17.25, -8.5, 4.75)
    evaluation_positions = tuple(tuple(
        matvec(evaluation_rotation, point)[axis] + evaluation_shift[axis]
        for axis in range(3)) for point in nacl.positions)
    atomic = compile_irregular_port_program(nacl.species, nacl.positions)
    admitted = mine_port_graph_macros(atomic, maximum_nodes=2)
    dense = match_dense_macro_types(atomic, admitted.macro_types)
    promoted = promote_macro_types(atomic, dense.dense_macro_types)
    traces = connection_traces(promoted, maximum_interaction_order=2)
    training, validation = guarded_trace_split(traces)
    marking = fit_causal_connection_marking(
        training, validation_count=len(validation),
        guarded_domains_disjoint=True)
    shuffled_markings = tuple(fit_causal_connection_marking(
        shuffle_trace_labels(training, seed=2718 + run),
        validation_count=len(validation), guarded_domains_disjoint=True)
                              for run in range(shuffled_runs))

    center = tuple(sum(point[axis] for point in evaluation_positions) /
                   len(evaluation_positions) for axis in range(3))
    radii = tuple(math.dist(point, center) for point in evaluation_positions)
    cutoff = median(radii)
    inner = {index for index, radius in enumerate(radii) if radius <= cutoff}
    supports = dict(promoted.occurrence_supports)
    source_seeds = tuple(item for item in promoted.occurrences
                         if set(supports[item.occurrence_id]) <= inner)
    seeds = tuple(ClusterOccurrence(
        item.occurrence_id, item.type_id,
        matmul(evaluation_rotation, item.rotation),
        tuple(matvec(evaluation_rotation, item.translation)[axis] +
              evaluation_shift[axis] for axis in range(3)))
                  for item in source_seeds)
    seed_sites = tuple((nacl.species[index], evaluation_positions[index])
                       for index in sorted(inner))
    target_keys = {_site_key((species, point), .03)
                   for species, point in zip(nacl.species,
                                             evaluation_positions)}
    productions = _compile_productions(promoted)
    production_by_key = {
        (item.parent_type, item.child_type, item.symmetry_orbit_key):
        item.production_id for item in productions}
    # Enumerate only train-frozen port keys among already placed evaluation
    # seed occurrences. No outer occurrence or outer atom is consulted.
    prototype = {item.type_id: item for item in promoted.prototypes}
    frozen_keys = set(production_by_key)
    incoming = defaultdict(list)
    for parent_index, parent in enumerate(seeds):
        for child_index, child in enumerate(seeds):
            if parent_index == child_index:
                continue
            shared = set(supports[parent.occurrence_id]).intersection(
                supports[child.occurrence_id])
            if len(shared) < promoted.minimum_shared_atoms:
                continue
            inverse = transpose(parent.rotation)
            relative_rotation = matmul(inverse, child.rotation)
            delta = tuple(child.translation[axis] - parent.translation[axis]
                          for axis in range(3))
            relative_translation = matvec(inverse, delta)
            try:
                _, _, key = canonical_relative_pose(
                    prototype[parent.type_id], prototype[child.type_id],
                    relative_rotation, relative_translation, .03)
            except ValueError:
                continue
            frozen = parent.type_id, child.type_id, key
            if frozen in frozen_keys:
                incoming[child_index].append(production_by_key[frozen])
    node_context = {index: tuple(sorted(incoming[index])[:2])
                    for index in range(len(seeds))}

    def make_ranker(fitted):
        def rank(parent, action, child, orbit, overlap, emitted):
            parent_type = productions[action].parent_type
            return rank_key(fitted, parent_type,
                            node_context.get(parent, ()), action,
                            overlap, emitted, parent)
        return rank

    arms = [("unmarked", None), ("marked", make_ranker(marking))]
    arms.extend((f"shuffle-{run}", make_ranker(fitted))
                for run, fitted in enumerate(shuffled_markings))
    maximum = []
    for name, ranker in arms:
        derivation = execute_macro_derivation(
            promoted, seeds, explicit_seed_sites=seed_sites,
            maximum_levels=1, maximum_new_nodes_per_level=64, ranker=ranker)
        maximum.append((name, ranker, derivation,
                        _curve(derivation, target_keys)))
    candidate_counts = {item.attempted_candidates
                        for _, _, item, _ in maximum}
    matched = min(curve[-1][2] for _, _, _, curve in maximum if curve)
    results = []
    for name, ranker, _, curve in maximum:
        placements = next(item[0] for item in curve if item[2] >= matched)
        replay = execute_macro_derivation(
            promoted, seeds, explicit_seed_sites=seed_sites,
            maximum_levels=1, maximum_new_nodes_per_level=placements,
            ranker=ranker)
        score = score_macro_derivation(
            replay, nacl.species, evaluation_positions)
        wrong_placements = sum(any(key not in target_keys
                                   for key in step.certificate.emitted_sites)
                               for step in replay.steps)
        results.append(MatchedWork(
            name, placements, placements + replay.rejected_batch_conflicts,
            score.proposed_novel_atoms, score.correct_novel_atoms,
            wrong_placements,
            score.proposed_novel_atoms - score.correct_novel_atoms,
            replay.rejected_batch_conflicts, replay.attempted_candidates,
            score.precision, score.heldout_recall))
    by_name = {item.arm: item for item in results}
    marked, unmarked = by_name["marked"], by_name["unmarked"]
    shuffled = tuple(by_name[f"shuffle-{run}"]
                     for run in range(shuffled_runs))
    marked_work = marked.wrong_placements + marked.geometric_backtracks
    shuffled_work = tuple(item.wrong_placements + item.geometric_backtracks
                          for item in shuffled)
    empirical_p = ((1 + sum(value <= marked_work
                             for value in shuffled_work)) /
                   (shuffled_runs + 1))
    live_contexts = tuple(node_context.values())
    exact_coverage = (
        sum((seed.type_id, context) in marking.exact
            for seed, context in zip(seeds, live_contexts)) /
        max(1, len(live_contexts)))
    diagnostic_ranking_gain = (len(candidate_counts) == 1 and
            marked.proposals < unmarked.proposals and
            marked.proposals < median(item.proposals for item in shuffled) and
            marked_work < median(shuffled_work) and empirical_p <= .05 and
            marked.precision > unmarked.precision)
    # A rigid copy has exact correspondence with every fitted source atom.
    # Even a ranking gain here cannot satisfy the independent causal gate.
    gate = False
    return IncomingContextEquivarianceAudit(
        len(nacl.positions), len(seed_sites), next(iter(candidate_counts)), 2,
        len(training), len(validation), True, _top_one(marking, validation),
        exact_coverage, matched, marked, unmarked,
        median(item.proposals for item in shuffled), median(shuffled_work),
        min(shuffled_work), shuffled_runs, empirical_p,
        len(candidate_counts) == 1, True, False, True, True, gate, False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--shuffles", type=int, default=31)
    args = parser.parse_args()
    result = evaluate(shuffled_runs=args.shuffles)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
