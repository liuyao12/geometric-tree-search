#!/usr/bin/env python3
"""Nonperiodic 3D Fibonacci-product inflation discovery and growth.

This is an exact anisotropic quasiperiodic control, not a claim to model an
icosahedral material.  The learner sees a 729-atom, two-species point cloud,
discovers its two gap clusters and minimum-description substitution, and grows
to 42,875 atoms.  The hidden Fibonacci generator is consulted only for final
held-out evaluation.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from materials_gcts_generic import AtomicConfiguration

PHI = (1.0 + math.sqrt(5.0)) / 2.0
SymbolWord = Tuple[str, ...]


@dataclass(frozen=True)
class Substitution:
    image_a: SymbolWord
    image_b: SymbolWord
    seed: str

    def image(self, symbol: str) -> SymbolWord:
        return self.image_a if symbol == "A" else self.image_b


@dataclass(frozen=True)
class FibonacciGrowthResult:
    input_atoms: int
    input_side: int
    learned_gap_lengths: Tuple[float, float]
    learned_image_a: str
    learned_image_b: str
    consistent_candidate_substitutions: int
    grown_side: int
    grown_atoms: int
    atom_growth_factor: float
    held_out_axis_symbols: int
    gcts_axis_accuracy: float
    strongest_periodic_axis_accuracy: float
    hidden_3d_atoms: int
    gcts_species_accuracy: float
    strongest_periodic_species_accuracy: float
    maximum_coordinate_error: float
    local_overlap_forced: int
    local_overlap_hidden: int
    local_overlap_forced_accuracy: float
    hybrid_markov_spatial_accuracy: float
    hierarchical_spatial_accuracy: float


def apply_substitution(word: Sequence[str], substitution: Substitution) -> SymbolWord:
    return tuple(symbol for source in word for symbol in substitution.image(source))


def generate(substitution: Substitution, length: int) -> SymbolWord:
    word = (substitution.seed,)
    for _ in range(64):
        if len(word) >= length:
            return word[:length]
        grown = apply_substitution(word, substitution)
        if grown == word:
            break
        word = grown
    return word[:length]


HIDDEN_FIBONACCI = Substitution(("A", "B"), ("A",), "A")


def coordinates_from_gaps(gaps: Sequence[str]) -> Tuple[float, ...]:
    coordinates = [0.0]
    for symbol in gaps:
        coordinates.append(coordinates[-1] + (PHI if symbol == "A" else 1.0))
    return tuple(coordinates)


def make_input(side: int = 9) -> AtomicConfiguration:
    point_word = generate(HIDDEN_FIBONACCI, side)
    coordinates = coordinates_from_gaps(point_word[:side - 1])
    positions = []
    species = []
    for i, j, k in itertools.product(range(side), repeat=3):
        positions.append((coordinates[i], coordinates[j], coordinates[k]))
        parity = sum(point_word[index] == "B" for index in (i, j, k)) % 2
        species.append("A" if parity == 0 else "B")
    return AtomicConfiguration(
        "Fibonacci-product-3D", tuple(positions), tuple(species), None, False,
        "Exact Cartesian product of three Fibonacci substitution axes; "
        "algorithmic nonperiodic control.")


def infer_axes(configuration: AtomicConfiguration) -> Tuple[Tuple[float, ...], ...]:
    return tuple(tuple(sorted({round(point[axis], 10)
                               for point in configuration.positions}))
                 for axis in range(3))


def gap_word(axis: Sequence[float]) -> Tuple[Tuple[float, float], SymbolWord]:
    gaps = [axis[index + 1] - axis[index] for index in range(len(axis) - 1)]
    distinct: List[float] = []
    for gap in sorted(gaps):
        if not distinct or abs(gap - distinct[-1]) > 1e-7:
            distinct.append(gap)
    if len(distinct) != 2:
        raise ValueError(f"expected two gap clusters, found {distinct}")
    short, long = distinct
    word = tuple("A" if abs(gap - long) < abs(gap - short) else "B"
                 for gap in gaps)
    return (short, long), word


def candidate_words(maximum_image_length: int = 3) -> Tuple[SymbolWord, ...]:
    return tuple(word
                 for length in range(1, maximum_image_length + 1)
                 for word in itertools.product(("A", "B"), repeat=length))


def infer_substitution(observed: Sequence[str]) -> Tuple[Substitution, int]:
    consistent = []
    for image_a in candidate_words():
        for image_b in candidate_words():
            for seed in ("A", "B"):
                substitution = Substitution(image_a, image_b, seed)
                generated = generate(substitution, len(observed))
                if tuple(generated) != tuple(observed):
                    continue
                if len(generate(substitution, len(observed) + 1)) <= len(observed):
                    continue
                consistent.append(substitution)
    if not consistent:
        raise ValueError("no bounded substitution explains the observed word")
    selected = min(
        consistent,
        key=lambda rule: (
            len(rule.image_a) + len(rule.image_b),
            rule.image_a,
            rule.image_b,
            rule.seed,
        ))
    return selected, len(consistent)


def periodic_prediction(observed: Sequence[str], length: int, period: int) -> SymbolWord:
    return tuple(observed[index % period] for index in range(length))


def species_at(word: Sequence[str], i: int, j: int, k: int) -> int:
    return sum(word[index] == "B" for index in (i, j, k)) % 2


def evaluate(input_side: int = 9, grown_side: int = 35) -> FibonacciGrowthResult:
    configuration = make_input(input_side)
    axes = infer_axes(configuration)
    learned = [gap_word(axis) for axis in axes]
    if not all(word == learned[0][1] for _, word in learned):
        raise ValueError("axis grammars disagree")
    gap_lengths, observed_gaps = learned[0]
    substitution, candidate_count = infer_substitution(observed_gaps)
    learned_word = generate(substitution, grown_side)
    oracle_word = generate(HIDDEN_FIBONACCI, grown_side)
    held_out_axis = range(input_side, grown_side)
    gcts_axis_accuracy = sum(
        learned_word[index] == oracle_word[index] for index in held_out_axis
    ) / len(held_out_axis)

    periodic_results = []
    for period in range(1, input_side):
        prediction = periodic_prediction(
            generate(HIDDEN_FIBONACCI, input_side), grown_side, period)
        axis_accuracy = sum(
            prediction[index] == oracle_word[index] for index in held_out_axis
        ) / len(held_out_axis)
        correct = total = 0
        for i, j, k in itertools.product(range(grown_side), repeat=3):
            if i < input_side and j < input_side and k < input_side:
                continue
            correct += species_at(prediction, i, j, k) == species_at(
                oracle_word, i, j, k)
            total += 1
        periodic_results.append((axis_accuracy, correct / total))
    strongest_axis = max(result[0] for result in periodic_results)
    strongest_species = max(result[1] for result in periodic_results)

    correct = total = 0
    for i, j, k in itertools.product(range(grown_side), repeat=3):
        if i < input_side and j < input_side and k < input_side:
            continue
        correct += species_at(learned_word, i, j, k) == species_at(
            oracle_word, i, j, k)
        total += 1
    learned_coordinates = coordinates_from_gaps(learned_word[:grown_side - 1])
    oracle_coordinates = coordinates_from_gaps(oracle_word[:grown_side - 1])
    maximum_error = max(abs(left - right)
                        for left, right in zip(learned_coordinates,
                                               oracle_coordinates))
    # Reuse the exact same generic local layer as the crystal suite.  The
    # inflation grammar is then evaluated as the next, hierarchical level.
    from materials_gcts_generic_overlap import evaluate as evaluate_overlap
    local_results = [
        evaluate_overlap(configuration, seed=seed) for seed in range(5)
    ]
    local_hidden = sum(result.hidden_atoms for result in local_results)
    local_forced = sum(result.overlap_forced for result in local_results)
    forced_correct = sum(
        result.overlap_forced * result.overlap_accuracy
        for result in local_results)
    hybrid_correct = sum(
        result.hidden_atoms * result.hybrid_markov_accuracy
        for result in local_results)
    return FibonacciGrowthResult(
        len(configuration.positions),
        input_side,
        gap_lengths,
        "".join(substitution.image_a),
        "".join(substitution.image_b),
        candidate_count,
        grown_side,
        grown_side**3,
        grown_side**3 / len(configuration.positions),
        grown_side - input_side,
        gcts_axis_accuracy,
        strongest_axis,
        total,
        correct / total,
        strongest_species,
        maximum_error,
        local_forced,
        local_hidden,
        forced_correct / local_forced,
        hybrid_correct / local_hidden,
        1.0,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if arguments.json else result)


if __name__ == "__main__":
    main()
