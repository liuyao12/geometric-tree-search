#!/usr/bin/env python3
"""Generic overlap-CSP regrowth on atomic point clouds.

Neighborhood factors are learned from visible atoms and transferred between
geometrically isomorphic supports.  The implementation uses no lattice labels,
unit-cell indices, or material-specific rules.  It is an exact, finite-support
GCTS layer over the generic representation in ``materials_gcts_generic``.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import DefaultDict, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Set, Tuple

from materials_gcts_generic import (
    AtomicConfiguration,
    benchmark_systems,
    displacement,
    iid_alloy_control,
    dot,
    norm,
    perturb,
)

Pattern = Tuple[str, ...]
DistanceMatrix = Tuple[Tuple[float, ...], ...]


@dataclass(frozen=True)
class Factor:
    support: Tuple[int, ...]
    allowed: Tuple[Pattern, ...]


@dataclass(frozen=True)
class OverlapResult:
    system: str
    split_seed: int
    nominal_neighbors: int
    atoms: int
    hidden_atoms: int
    geometry_classes: int
    learned_patterns: int
    overlap_forced: int
    overlap_accuracy: float
    geometry_baseline_forced: int
    geometry_baseline_accuracy: float
    geometry_map_accuracy: float
    pairwise_markov_accuracy: float
    hybrid_markov_accuracy: float
    majority_accuracy: float
    compact_grammar: bool
    true_assignment_admitted: bool
    consistent: bool


def nearest_shell_supports(
    configuration: AtomicConfiguration,
    shell_band: float = 1.05,
    nominal_neighbors: int = 3,
) -> Tuple[Tuple[int, ...], ...]:
    supports = []
    for center in range(len(configuration.positions)):
        neighbors = []
        for other in range(len(configuration.positions)):
            if other == center:
                continue
            distance = norm(displacement(configuration, center, other))
            if distance > 1e-10:
                neighbors.append((distance, other))
        neighbors.sort()
        nominal = min(nominal_neighbors, len(neighbors))
        cutoff = neighbors[nominal - 1][0] * shell_band
        shell = tuple(other for distance, other in neighbors if distance <= cutoff)
        supports.append((center,) + shell)
    return tuple(supports)


def distance_matrix(
    configuration: AtomicConfiguration,
    support: Sequence[int],
) -> DistanceMatrix:
    vectors = [(0.0, 0.0, 0.0)] + [
        displacement(configuration, support[0], atom) for atom in support[1:]
    ]
    nearest = min(norm(vector) for vector in vectors[1:]) if len(vectors) > 1 else 1.0
    return tuple(tuple(norm(tuple(a - b for a, b in zip(left, right))) / nearest
                       for right in vectors)
                 for left in vectors)


def geometry_key(matrix: DistanceMatrix) -> Tuple[Tuple[float, Tuple[float, ...]], ...]:
    """Rounded reporting key; factor learning uses tolerant isomorphism."""
    rows = [(round(matrix[index][0], 2),
             tuple(round(value, 2) for value in sorted(matrix[index])))
            for index in range(len(matrix))]
    return tuple(sorted(rows))


def isomorphisms(
    source: DistanceMatrix,
    target: DistanceMatrix,
    cap: int = 512,
    tolerance: float = 6e-2,
) -> Tuple[Tuple[int, ...], ...]:
    """All distance-graph isomorphisms mapping the anchor 0 to anchor 0."""
    if len(source) != len(target):
        return ()
    size = len(source)
    def rows_close(left: Sequence[float], right: Sequence[float]) -> bool:
        return len(left) == len(right) and all(
            abs(a - b) <= tolerance for a, b in zip(sorted(left), sorted(right)))

    candidates = []
    for index in range(size):
        choices = [
            other for other in range(size)
            if abs(source[index][0] - target[other][0]) <= tolerance
            and rows_close(source[index], target[other])
        ]
        if index == 0:
            choices = [0] if 0 in choices else []
        elif 0 in choices:
            choices.remove(0)
        candidates.append(tuple(choices))
    if any(not choices for choices in candidates):
        return ()
    mapping = [-1] * size
    used: Set[int] = set()
    results: List[Tuple[int, ...]] = []

    def search() -> None:
        if len(results) >= cap:
            return
        unresolved = [index for index, value in enumerate(mapping) if value < 0]
        if not unresolved:
            results.append(tuple(mapping))
            return
        source_index = min(
            unresolved,
            key=lambda index: sum(
                candidate not in used and all(
                    mapping[assigned] < 0 or
                    abs(source[index][assigned] -
                        target[candidate][mapping[assigned]]) <= tolerance
                    for assigned in range(size))
                for candidate in candidates[index]))
        valid = [
            candidate for candidate in candidates[source_index]
            if candidate not in used and all(
                mapping[assigned] < 0 or
                abs(source[source_index][assigned] -
                    target[candidate][mapping[assigned]]) <= tolerance
                for assigned in range(size))
        ]
        for candidate in valid:
            mapping[source_index] = candidate
            used.add(candidate)
            search()
            used.remove(candidate)
            mapping[source_index] = -1

    search()
    return tuple(results)


def geometry_class_labels(
    matrices: Sequence[DistanceMatrix],
) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """Cluster supports by tolerance-controlled geometric isomorphism."""
    representatives: List[int] = []
    labels: List[int] = []
    for index, matrix in enumerate(matrices):
        label = None
        for candidate, representative in enumerate(representatives):
            if isomorphisms(matrix, matrices[representative], cap=1):
                label = candidate
                break
        if label is None:
            label = len(representatives)
            representatives.append(index)
        labels.append(label)
    return tuple(labels), tuple(representatives)


def hidden_spatial_block(
    configuration: AtomicConfiguration,
    count: int,
    seed: int = 0,
) -> Set[int]:
    """Choose a compact periodic block, independent of atom species."""
    rng = random.Random(seed)
    bounds = tuple((min(point[axis] for point in configuration.positions),
                    max(point[axis] for point in configuration.positions))
                   for axis in range(3))
    center = tuple(low + (.15 + .70 * rng.random()) * (high - low)
                   for low, high in bounds)
    distances = []
    for index, point in enumerate(configuration.positions):
        # For a compact benchmark split, Euclidean distance to the cell center
        # is sufficient; species never enters the selection.
        distance = math.sqrt(sum((point[axis] - center[axis]) ** 2
                                 for axis in range(3)))
        distances.append((distance, index))
    return {index for _, index in sorted(distances)[:count]}


def learn_factors(
    configuration: AtomicConfiguration,
    hidden: Set[int],
    nominal_neighbors: int = 3,
) -> Tuple[Tuple[Factor, ...], Dict[Tuple, Counter], int]:
    supports = nearest_shell_supports(configuration,
                                      nominal_neighbors=nominal_neighbors)
    matrices = tuple(distance_matrix(configuration, support) for support in supports)
    keys, representative_indices = geometry_class_labels(matrices)
    references = {key: index for key, index in enumerate(representative_indices)}
    catalogs: DefaultDict[int, Set[Pattern]] = defaultdict(set)
    central_species: DefaultDict[int, Counter] = defaultdict(Counter)

    for anchor, (support, key) in enumerate(zip(supports, keys)):
        if anchor not in hidden:
            central_species[key][configuration.species[anchor]] += 1
        if hidden.isdisjoint(support):
            reference = references[key]
            mappings = isomorphisms(matrices[anchor], matrices[reference], cap=1)
            if not mappings:
                continue
            mapping = mappings[0]
            assignment = [""] * len(support)
            for source_index, target_index in enumerate(mapping):
                assignment[target_index] = configuration.species[support[source_index]]
            catalogs[key].add(tuple(assignment))

    factors: List[Factor] = []
    for anchor, (support, key) in enumerate(zip(supports, keys)):
        if key not in catalogs:
            continue
        reference = references[key]
        mappings = isomorphisms(matrices[reference], matrices[anchor])
        allowed: Set[Pattern] = set()
        for reference_pattern in catalogs[key]:
            for mapping in mappings:
                assignment = [""] * len(support)
                for source_index, target_index in enumerate(mapping):
                    assignment[target_index] = reference_pattern[source_index]
                allowed.add(tuple(assignment))
        if allowed:
            factors.append(Factor(support, tuple(sorted(allowed))))
    return tuple(factors), dict(central_species), sum(map(len, catalogs.values()))


def propagate(
    factors: Sequence[Factor],
    domains: MutableMapping[int, Set[str]],
) -> bool:
    changed = True
    while changed:
        changed = False
        for factor in factors:
            allowed = [
                pattern for pattern in factor.allowed
                if all(pattern[index] in domains[atom]
                       for index, atom in enumerate(factor.support))
            ]
            if not allowed:
                return False
            for index, atom in enumerate(factor.support):
                supported = {pattern[index] for pattern in allowed}
                narrowed = domains[atom] & supported
                if not narrowed:
                    return False
                if narrowed != domains[atom]:
                    domains[atom] = narrowed
                    changed = True
    return True


def pairwise_markov_predictions(
    configuration: AtomicConfiguration,
    hidden: Set[int],
    supports: Sequence[Sequence[int]],
    iterations: int = 40,
    geometry_labels: Optional[Sequence[int]] = None,
    geometry_species: Optional[Mapping[int, Counter]] = None,
) -> Dict[int, str]:
    """Mean-field baseline with pair statistics learned only from visible edges."""
    names = sorted(set(configuration.species))
    visible_counts = Counter(configuration.species[index]
                             for index in range(len(configuration.species))
                             if index not in hidden)
    directed = Counter()
    for support in supports:
        center = support[0]
        if center in hidden:
            continue
        for neighbor in support[1:]:
            if neighbor not in hidden:
                directed[(configuration.species[center],
                          configuration.species[neighbor])] += 1
    transition: Dict[Tuple[str, str], float] = {}
    for source in names:
        denominator = sum(directed[(source, target)] for target in names) + .5 * len(names)
        for target in names:
            transition[(source, target)] = (
                directed[(source, target)] + .5) / denominator
    beliefs: Dict[int, Dict[str, float]] = {}
    total_visible = sum(visible_counts.values())
    for index, chemical in enumerate(configuration.species):
        if index in hidden:
            local = (geometry_species or {}).get(
                geometry_labels[index] if geometry_labels is not None else -1,
                Counter())
            local_total = sum(local.values())
            beliefs[index] = {
                name: ((local[name] + .5) / (local_total + .5 * len(names))
                       if local_total else
                       (visible_counts[name] + .5) /
                       (total_visible + .5 * len(names))) for name in names
            }
        else:
            beliefs[index] = {name: float(name == chemical) for name in names}
    adjacency = {support[0]: tuple(support[1:]) for support in supports}
    for _ in range(iterations):
        updated = {}
        maximum_change = 0.0
        for index in hidden:
            scores = {}
            for candidate in names:
                local = (geometry_species or {}).get(
                    geometry_labels[index] if geometry_labels is not None else -1,
                    Counter())
                local_total = sum(local.values())
                prior = ((local[candidate] + .5) /
                         (local_total + .5 * len(names)) if local_total else
                         (visible_counts[candidate] + .5) /
                         (total_visible + .5 * len(names)))
                score = math.log(prior)
                for neighbor in adjacency[index]:
                    probability = sum(
                        beliefs[neighbor][other] * transition[(candidate, other)]
                        for other in names)
                    score += math.log(max(probability, 1e-15))
                scores[candidate] = score
            peak = max(scores.values())
            weights = {name: math.exp(value - peak) for name, value in scores.items()}
            normalizer = sum(weights.values())
            updated[index] = {name: value / normalizer
                              for name, value in weights.items()}
            maximum_change = max(maximum_change, max(
                abs(updated[index][name] - beliefs[index][name]) for name in names))
        beliefs.update(updated)
        if maximum_change < 1e-9:
            break
    return {
        index: max(names, key=lambda name: (beliefs[index][name], name))
        for index in hidden
    }


def evaluate(
    configuration: AtomicConfiguration,
    hidden_count: Optional[int] = None,
    seed: int = 0,
    nominal_neighbors: int = 3,
) -> OverlapResult:
    count = hidden_count or max(4, round(len(configuration.positions) * .04))
    hidden = hidden_spatial_block(configuration, count, seed)
    factors, central_species, learned_patterns = learn_factors(
        configuration, hidden, nominal_neighbors)
    chemical_species = set(configuration.species)
    domains: Dict[int, Set[str]] = {
        index: (set(chemical_species) if index in hidden else {species})
        for index, species in enumerate(configuration.species)
    }
    consistent = propagate(factors, domains)
    forced = [index for index in hidden if consistent and len(domains[index]) == 1]
    overlap_correct = sum(next(iter(domains[index])) == configuration.species[index]
                          for index in forced)

    supports = nearest_shell_supports(configuration,
                                      nominal_neighbors=nominal_neighbors)
    matrices = tuple(distance_matrix(configuration, support) for support in supports)
    keys, _ = geometry_class_labels(matrices)
    baseline_forced = [
        index for index in hidden if len(central_species.get(keys[index], {})) == 1
    ]
    baseline_correct = sum(
        next(iter(central_species[keys[index]])) == configuration.species[index]
        for index in baseline_forced)
    geometry_predictions = {
        key: counts.most_common(1)[0][0] for key, counts in central_species.items()
    }
    geometry_map_accuracy = sum(
        geometry_predictions.get(keys[index]) == configuration.species[index]
        for index in hidden) / len(hidden)
    pairwise_predictions = pairwise_markov_predictions(
        configuration, hidden, supports)
    pairwise_accuracy = sum(
        pairwise_predictions[index] == configuration.species[index]
        for index in hidden) / len(hidden)
    hybrid_predictions = pairwise_markov_predictions(
        configuration, hidden, supports,
        geometry_labels=keys, geometry_species=central_species)
    hybrid_accuracy = sum(
        hybrid_predictions[index] == configuration.species[index]
        for index in hidden) / len(hidden)
    visible_counts = Counter(species for index, species in enumerate(configuration.species)
                             if index not in hidden)
    majority = visible_counts.most_common(1)[0][0]
    majority_accuracy = sum(configuration.species[index] == majority
                            for index in hidden) / len(hidden)
    true_admitted = all(any(
        all(pattern[position] == configuration.species[atom]
            for position, atom in enumerate(factor.support))
        for pattern in factor.allowed) for factor in factors)
    return OverlapResult(
        configuration.name,
        seed,
        nominal_neighbors,
        len(configuration.positions),
        len(hidden),
        len(set(keys)),
        learned_patterns,
        len(forced),
        overlap_correct / len(forced) if forced else 0.0,
        len(baseline_forced),
        baseline_correct / len(baseline_forced) if baseline_forced else 0.0,
        geometry_map_accuracy,
        pairwise_accuracy,
        hybrid_accuracy,
        majority_accuracy,
        learned_patterns <= max(12, round(len(configuration.positions) * .20)),
        true_admitted,
        consistent,
    )


def run_suite(
    seeds: Iterable[int] = range(5),
    nominal_neighbors: int = 3,
) -> Tuple[OverlapResult, ...]:
    return tuple(evaluate(configuration, seed=seed,
                          nominal_neighbors=nominal_neighbors)
                 for configuration in benchmark_systems() for seed in seeds)


def run_null_control(seeds: Iterable[int] = range(5)) -> Tuple[OverlapResult, ...]:
    configuration = iid_alloy_control()
    return tuple(evaluate(configuration, seed=seed) for seed in seeds)


def run_perturbed_suite(
    seeds: Iterable[int] = range(5),
    relative_sigma: float = .005,
) -> Tuple[OverlapResult, ...]:
    results = []
    for configuration in benchmark_systems():
        nearest = min(norm(displacement(configuration, 0, other))
                      for other in range(1, len(configuration.positions)))
        for seed in seeds:
            noisy = perturb(configuration, nearest * relative_sigma, 1000 + seed)
            results.append(evaluate(noisy, seed=seed))
    return tuple(results)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    results = run_suite()
    if arguments.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            print(result)


if __name__ == "__main__":
    main()
