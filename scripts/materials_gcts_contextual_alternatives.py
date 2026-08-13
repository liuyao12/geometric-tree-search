#!/usr/bin/env python3
"""Frozen occurrence split for context-marked cover-production alternatives.

This benchmark asks a narrow causal question before attempting another growth
claim: can the bounded halo marking select among multiple cluster-of-cluster
right-hand sides better than one modal production per parent type?

Cluster discovery runs once on the finite point cloud.  Production selection
then uses a deterministic 2:1 train/held-out split of occurrences, ordered by
distance from the observation centroid.  The held-out right-hand sides are
never used to choose a rule.  This is an occurrence holdout, not yet the
stronger unseen-window benchmark.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import DefaultDict, Hashable, Sequence, Tuple

from materials_gcts_cover_grammar import _cover_signature, _is_recurring
from materials_recursive_gcts import learn_recursive_hierarchy


@dataclass(frozen=True)
class ContextAlternativeCase:
    system: str
    atoms: int
    training_occurrences: int
    heldout_occurrences: int
    parent_types: int
    learned_context_rules: int
    learned_rhs_alternatives: int
    context_rules_per_training_occurrence: float
    known_context_fraction: float
    single_modal_accuracy: float
    marked_context_accuracy: float
    shuffled_context_accuracy: float
    original_halo_accuracy: float
    oracle_seen_alternative_fraction: float
    marking_gain_over_modal: float
    marking_gain_over_shuffled: float
    finite_vocabulary: bool
    benchmark_passed: bool


@dataclass(frozen=True)
class ContextAlternativeBenchmark:
    crystal: ContextAlternativeCase
    quasicrystal: ContextAlternativeCase
    both_markings_causal: bool
    both_finite_vocabularies: bool
    benchmark_passed: bool


def _centroid(positions):
    return tuple(sum(point[axis] for point in positions) / len(positions)
                 for axis in range(3))


def _split_indices(centers, positions):
    origin = _centroid(positions)
    ranked = sorted(range(len(centers)), key=lambda offset: (
        math.dist(positions[centers[offset]], origin), centers[offset]))
    heldout = frozenset(ranked[2::3])
    return tuple(index for index in range(len(centers))
                 if index not in heldout), tuple(sorted(heldout))


def _mode(values):
    return Counter(values).most_common(1)[0][0]


def _quantize(value, width):
    return int(math.floor(value / width + .5001))


def _port_context(parent_center, parent_support, child_models,
                  positions, scale):
    """Bounded section of child ports around one parent cluster.

    The section is independent of the greedy cover decision.  It records each
    lower-level cluster whose centre lies in the parent, including candidates
    that protrude through its boundary.  This is precisely the local
    connection information a marking may expose to the tree search.
    """
    parent = frozenset(parent_support)
    center = positions[parent_center]
    width = max(1e-9, .20 * scale)
    ports = []
    for child in child_models:
        for child_center, child_support in zip(
                child.occurrence_centers, child.occurrence_supports):
            if child_center not in parent:
                continue
            support = frozenset(child_support)
            ports.append((
                child.type_id,
                _quantize(math.dist(center, positions[child_center]), width),
                len(support.intersection(parent)),
                len(support.difference(parent))))
    return tuple(sorted(ports))


def _case(configuration) -> ContextAlternativeCase:
    hierarchy, dictionaries = learn_recursive_hierarchy(
        configuration.name, configuration.positions, configuration.species,
        maximum_levels=4, first_descriptor_bin_scale=.02,
        first_angle_bin=.03, macro_distance_bin_scale=.20,
        macro_angle_bin=.08)
    training = []
    heldout = []
    parent_types = 0
    for level_index in range(1, len(dictionaries)):
        children = tuple(model for model in dictionaries[level_index - 1]
                         if _is_recurring(model, 2, 3))
        for parent in dictionaries[level_index]:
            if not _is_recurring(parent, 2, 3):
                continue
            train_indices, test_indices = _split_indices(
                parent.occurrence_centers, configuration.positions)
            if not train_indices or not test_indices:
                continue
            parent_types += 1
            rows = []
            for index, support in enumerate(parent.occurrence_supports):
                rhs = _cover_signature(
                    support, children, configuration.species)[0]
                port_context = _port_context(
                    parent.occurrence_centers[index], support, children,
                    configuration.positions, hierarchy.nearest_neighbor_scale)
                rows.append((parent.level, parent.type_id, port_context,
                             parent.occurrence_markings[index], rhs))
            training.extend(rows[index] for index in train_indices)
            heldout.extend(rows[index] for index in test_indices)

    modal_by_type = {}
    context_votes: DefaultDict[tuple, Counter] = defaultdict(Counter)
    alternatives: DefaultDict[tuple, set] = defaultdict(set)
    halo_votes: DefaultDict[tuple, Counter] = defaultdict(Counter)
    for level, type_id, marking, halo, rhs in training:
        key = level, type_id
        alternatives[key].add(rhs)
        context_votes[(level, type_id, marking)][rhs] += 1
        halo_votes[(level, type_id, halo)][rhs] += 1
    for key in alternatives:
        modal_by_type[key] = _mode(
            [rhs for level, type_id, _, _, rhs in training
             if (level, type_id) == key])
    context_rule = {key: votes.most_common(1)[0][0]
                    for key, votes in context_votes.items()}
    halo_rule = {key: votes.most_common(1)[0][0]
                 for key, votes in halo_votes.items()}

    # The shuffled control preserves the number and marginal frequencies of
    # marking values but breaks their association with right-hand sides.
    shuffled_rule = {}
    contexts_by_type: DefaultDict[tuple, list] = defaultdict(list)
    for context in context_rule:
        contexts_by_type[context[:2]].append(context)
    for contexts in contexts_by_type.values():
        contexts.sort(key=repr)
        shifted = contexts[1:] + contexts[:1]
        for index, context in enumerate(contexts):
            shuffled_rule[context] = context_rule[shifted[index]]

    modal_correct = marked_correct = shuffled_correct = halo_correct = known = seen = 0
    for level, type_id, marking, halo, rhs in heldout:
        type_key = level, type_id
        modal_correct += modal_by_type[type_key] == rhs
        context_key = level, type_id, marking
        if context_key in context_rule:
            known += 1
            marked_correct += context_rule[context_key] == rhs
            shuffled_correct += shuffled_rule[context_key] == rhs
        halo_correct += halo_rule.get(
            (level, type_id, halo), modal_by_type[type_key]) == rhs
        seen += rhs in alternatives[type_key]
    count = len(heldout)
    modal_accuracy = modal_correct / count if count else 0.0
    marked_accuracy = marked_correct / count if count else 0.0
    shuffled_accuracy = shuffled_correct / count if count else 0.0
    halo_accuracy = halo_correct / count if count else 0.0
    vocabulary = sum(len(values) for values in alternatives.values())
    finite = (len(context_rule) <= len(training) / 2 and
              vocabulary <= len(training) / 2)
    passed = (count > 0 and marked_accuracy >= .90 and finite and
              marked_accuracy >= modal_accuracy + .10 and
              marked_accuracy >= shuffled_accuracy + .10)
    return ContextAlternativeCase(
        configuration.name, len(configuration.positions), len(training), count,
        parent_types, len(context_rule), vocabulary,
        len(context_rule) / len(training), known / count,
        modal_accuracy, marked_accuracy, shuffled_accuracy, halo_accuracy,
        seen / count,
        marked_accuracy - modal_accuracy,
        marked_accuracy - shuffled_accuracy, finite, passed)


def evaluate() -> ContextAlternativeBenchmark:
    from materials_gcts_generic import benchmark_systems
    from materials_gcts_icosahedral_modelset import oracle_patch

    crystal = next(item for item in benchmark_systems()
                   if item.name == "NaCl-rocksalt")
    quasicrystal, _ = oracle_patch(3, 9.0)
    cases = _case(crystal), _case(quasicrystal)
    causal = all(case.marked_context_accuracy > case.single_modal_accuracy and
                 case.marked_context_accuracy > case.shuffled_context_accuracy
                 for case in cases)
    finite = all(case.finite_vocabulary for case in cases)
    return ContextAlternativeBenchmark(
        *cases, causal, finite,
        causal and finite and all(case.benchmark_passed for case in cases))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
