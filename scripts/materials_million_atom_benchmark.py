#!/usr/bin/env python3
"""Scalable, auditable controls for hundred-to-million atom growth.

This benchmark deliberately separates three quantities that are easy to
conflate in a large-scale demonstration:

* ``represented_atoms`` is the number of atoms addressed by a compact grammar;
* ``materialized_atoms`` is the number of Cartesian records actually allocated;
* ``audit_atoms`` is the bounded configuration used for structural statistics.

The crystal and Fibonacci-product controls have exact compact continuations.
The amorphous control is intentionally harder: its current learned continuation
is only a counter-based, jittered-cell stochastic surrogate fitted to density,
nearest-neighbour scale and composition.  Poor fidelity is a useful negative
result, not hidden by the benchmark.

The GCTS-marking ablation measures how species markings change the recurring
local-cluster vocabulary.  It does not currently alter the scalable generator,
and the JSON says so explicitly.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import statistics
import sys
import time
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from materials_pointset_benchmarks import amorphous_hard_core_point_set
from materials_pointset_clusters import learn_cluster_candidates
from materials_structure_classifier import evaluate_structure

Vector = Tuple[float, float, float]
Atom = Tuple[Vector, str]
SymbolWord = Tuple[str, ...]


@dataclass(frozen=True)
class Substitution:
    image_a: SymbolWord
    image_b: SymbolWord
    seed: str

    def image(self, symbol: str) -> SymbolWord:
        return self.image_a if symbol == "A" else self.image_b


HIDDEN_FIBONACCI = Substitution(("A", "B"), ("A",), "A")
HIDDEN_LONG_GAP = (1.0 + math.sqrt(5.0)) / 2.0


def _apply_substitution(
    word: Sequence[str], substitution: Substitution,
) -> SymbolWord:
    return tuple(
        symbol for source in word for symbol in substitution.image(source))


def _generate(substitution: Substitution, length: int) -> SymbolWord:
    word = (substitution.seed,)
    for _ in range(64):
        if len(word) >= length:
            return word[:length]
        grown = _apply_substitution(word, substitution)
        if grown == word:
            break
        word = grown
    return word[:length]


def _coordinates_from_word(
    word: Sequence[str], short_gap: float, long_gap: float,
) -> Tuple[float, ...]:
    coordinates = [0.0]
    for symbol in word:
        coordinates.append(
            coordinates[-1] + (long_gap if symbol == "A" else short_gap))
    return tuple(coordinates)


def _infer_axes(positions: Sequence[Vector]) -> Tuple[Tuple[float, ...], ...]:
    return tuple(
        tuple(sorted({round(point[axis], 10) for point in positions}))
        for axis in range(3))


def _gap_word(axis: Sequence[float]) -> Tuple[Tuple[float, float], SymbolWord]:
    gaps = [axis[index + 1] - axis[index] for index in range(len(axis) - 1)]
    distinct: List[float] = []
    for gap in sorted(gaps):
        if not distinct or abs(gap - distinct[-1]) > 1e-7:
            distinct.append(gap)
    if len(distinct) != 2:
        raise ValueError(f"expected two inferred gap clusters, found {distinct}")
    short, long = distinct
    word = tuple(
        "A" if abs(gap - long) < abs(gap - short) else "B"
        for gap in gaps)
    return (short, long), word


def _candidate_words(maximum_image_length: int = 3) -> Tuple[SymbolWord, ...]:
    return tuple(
        word
        for length in range(1, maximum_image_length + 1)
        for word in itertools.product(("A", "B"), repeat=length))


def _infer_substitution(observed: Sequence[str]) -> Tuple[Substitution, int]:
    consistent = []
    candidates = _candidate_words()
    for image_a in candidates:
        for image_b in candidates:
            for seed in ("A", "B"):
                substitution = Substitution(image_a, image_b, seed)
                if _generate(substitution, len(observed)) != tuple(observed):
                    continue
                if len(_generate(substitution, len(observed) + 1)) <= len(observed):
                    continue
                consistent.append(substitution)
    if not consistent:
        raise ValueError("no bounded substitution explains the observed axes")
    selected = min(
        consistent,
        key=lambda rule: (
            len(rule.image_a) + len(rule.image_b),
            rule.image_a,
            rule.image_b,
            rule.seed,
        ))
    return selected, len(consistent)


def _fibonacci_training(atom_goal: int) -> Tuple[Tuple[Vector, ...], Tuple[str, ...]]:
    """Hidden oracle used only to create the learner's Cartesian input."""
    dimensions = _dimensions(atom_goal)
    word = _generate(HIDDEN_FIBONACCI, max(dimensions))
    coordinates = _coordinates_from_word(
        word[:max(dimensions) - 1], 1.0, HIDDEN_LONG_GAP)
    positions = []
    species = []
    for index in range(atom_goal):
        x, y, z = _linear_site(index, dimensions)
        positions.append((coordinates[x], coordinates[y], coordinates[z]))
        parity = sum(word[index] == "B" for index in (x, y, z)) % 2
        species.append("A" if parity == 0 else "B")
    return tuple(positions), tuple(species)


def _dimensions(minimum_atoms: int) -> Tuple[int, int, int]:
    side = max(1, math.ceil(minimum_atoms ** (1.0 / 3.0) - 1e-12))
    depth = math.ceil(minimum_atoms / (side * side))
    return side, side, depth


def _linear_site(index: int, dimensions: Tuple[int, int, int]) -> Tuple[int, int, int]:
    nx, ny, _ = dimensions
    plane = nx * ny
    z, remainder = divmod(index, plane)
    y, x = divmod(remainder, nx)
    return x, y, z


def _distance(left: Sequence[float], right: Sequence[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def _splitmix64(value: int) -> int:
    value = (value + 0x9E3779B97F4A7C15) & ((1 << 64) - 1)
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & ((1 << 64) - 1)
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & ((1 << 64) - 1)
    return value ^ (value >> 31)


def _uniform01(index: int, channel: int, seed: int) -> float:
    bits = _splitmix64(index ^ (channel * 0xD1B54A32D192ED03) ^ seed)
    return (bits >> 11) * (1.0 / (1 << 53))


class CompactModel:
    family: str
    grammar: Mapping[str, object]

    def atom(self, index: int, dimensions: Tuple[int, int, int]) -> Atom:
        raise NotImplementedError


@lru_cache(maxsize=32)
def _fibonacci_axis(
    substitution: Substitution,
    length: int,
    short_gap: float,
    long_gap: float,
) -> Tuple[SymbolWord, Tuple[float, ...]]:
    word = _generate(substitution, length)
    coordinates = _coordinates_from_word(
        word[:length - 1], short_gap, long_gap)
    return word, coordinates


@dataclass(frozen=True)
class CrystalModel(CompactModel):
    spacing: float
    even_species: str
    odd_species: str
    family: str = "crystal"

    @property
    def grammar(self) -> Mapping[str, object]:
        return {
            "kind": "translation_octree",
            "spacing": self.spacing,
            "species_rule": "integer-coordinate parity",
            "parameters": 3,
        }

    def atom(self, index: int, dimensions: Tuple[int, int, int]) -> Atom:
        x, y, z = _linear_site(index, dimensions)
        species = self.even_species if (x + y + z) % 2 == 0 else self.odd_species
        return ((x * self.spacing, y * self.spacing, z * self.spacing), species)


@dataclass(frozen=True)
class FibonacciModel(CompactModel):
    substitution: Substitution
    short_gap: float
    long_gap: float
    decoration: Tuple[Tuple[Tuple[str, str, str], str], ...]
    fallback_species: str
    consistent_substitutions: int
    family: str = "quasicrystal_model_set"

    @property
    def grammar(self) -> Mapping[str, object]:
        return {
            "kind": "fibonacci_product_substitution",
            "image_a": "".join(self.substitution.image_a),
            "image_b": "".join(self.substitution.image_b),
            "seed": self.substitution.seed,
            "gap_lengths": [self.short_gap, self.long_gap],
            "consistent_bounded_substitutions": self.consistent_substitutions,
            "species_decoration": {
                "".join(symbols): chemical
                for symbols, chemical in self.decoration
            },
            "species_decoration_source": "learned from Cartesian-axis indices and observed species",
            "parameters": 5 + len(self.decoration),
        }

    def atom(self, index: int, dimensions: Tuple[int, int, int]) -> Atom:
        x, y, z = _linear_site(index, dimensions)
        maximum = max(dimensions)
        word, coordinates = _fibonacci_axis(
            self.substitution, maximum, self.short_gap, self.long_gap)
        chemical = dict(self.decoration).get(
            (word[x], word[y], word[z]), self.fallback_species)
        return ((coordinates[x], coordinates[y], coordinates[z]), chemical)


@dataclass(frozen=True)
class AmorphousModel(CompactModel):
    spacing: float
    jitter_fraction: float
    palette: Tuple[str, ...]
    cumulative_weights: Tuple[float, ...]
    seed: int
    family: str = "amorphous_stochastic"

    @property
    def grammar(self) -> Mapping[str, object]:
        previous = 0.0
        probabilities = {}
        for chemical, cumulative in zip(self.palette, self.cumulative_weights):
            probabilities[chemical] = cumulative - previous
            previous = cumulative
        return {
            "kind": "counter_based_jittered_cell_surrogate",
            "spacing": self.spacing,
            "jitter_fraction": self.jitter_fraction,
            "species_probabilities": probabilities,
            "parameters": 3 + 2 * len(self.palette),
            "known_limitation": "cell scaffold can create artificial medium-range order",
        }

    def atom(self, index: int, dimensions: Tuple[int, int, int]) -> Atom:
        site = _linear_site(index, dimensions)
        amplitude = self.spacing * self.jitter_fraction
        position = tuple(
            self.spacing * site[axis]
            + amplitude * (2.0 * _uniform01(index, axis, self.seed) - 1.0)
            for axis in range(3)
        )
        draw = _uniform01(index, 7, self.seed)
        species = next(
            label for label, threshold in zip(self.palette, self.cumulative_weights)
            if draw <= threshold
        )
        return position, species  # type: ignore[return-value]


def _crystal_training(atom_goal: int) -> Tuple[Tuple[Vector, ...], Tuple[str, ...]]:
    dimensions = _dimensions(atom_goal)
    model = CrystalModel(2.82, "Na", "Cl")
    atoms = tuple(model.atom(index, dimensions) for index in range(atom_goal))
    return tuple(atom[0] for atom in atoms), tuple(atom[1] for atom in atoms)


def _nearest_distances(positions: Sequence[Vector]) -> Tuple[float, ...]:
    return tuple(
        min(_distance(point, other) for j, other in enumerate(positions) if i != j)
        for i, point in enumerate(positions)
    )


def _fit_crystal(positions: Sequence[Vector], species: Sequence[str]) -> CrystalModel:
    spacing = statistics.median(_nearest_distances(positions))
    return CrystalModel(spacing, species[0], next(
        (value for value in species if value != species[0]), species[0]))


def _fit_fibonacci(positions: Sequence[Vector], species: Sequence[str]) -> FibonacciModel:
    """Infer gaps, substitution, and color decoration from a plain point set."""
    axes = _infer_axes(positions)
    learned = [_gap_word(axis) for axis in axes]
    observed = max((item[1] for item in learned), key=len)
    if not all(item[1] == observed[:len(item[1])] for item in learned):
        raise ValueError("independently inferred Fibonacci axes disagree")
    gap_values = tuple(sorted({round(value, 10)
                               for gaps, _ in learned for value in gaps}))
    if len(gap_values) != 2:
        raise ValueError("independently inferred Fibonacci gap scales disagree")
    substitution, consistent_count = _infer_substitution(observed)
    side = max(map(len, axes))
    point_word = _generate(substitution, side)
    coordinate_indices = tuple({value: index for index, value in enumerate(axis)}
                               for axis in axes)
    decoration_counts: Dict[Tuple[str, str, str], Counter[str]] = {}
    for point, chemical in zip(positions, species):
        indices = tuple(
            coordinate_indices[axis][round(point[axis], 10)]
            for axis in range(3))
        symbols = tuple(point_word[index] for index in indices)
        decoration_counts.setdefault(symbols, Counter())[chemical] += 1
    decoration = tuple(sorted(
        (symbols, counts.most_common(1)[0][0])
        for symbols, counts in decoration_counts.items()))
    fallback = Counter(species).most_common(1)[0][0]
    return FibonacciModel(
        substitution, gap_values[0], gap_values[1], decoration, fallback,
        consistent_count)


def _fit_amorphous(positions: Sequence[Vector], species: Sequence[str], seed: int) -> AmorphousModel:
    center = tuple(sum(point[axis] for point in positions) / len(positions) for axis in range(3))
    radius = max(_distance(point, center) for point in positions)
    density = len(positions) / ((4.0 / 3.0) * math.pi * radius ** 3)
    spacing = density ** (-1.0 / 3.0)
    nearest = _nearest_distances(positions)
    coefficient = statistics.pstdev(nearest) / statistics.mean(nearest)
    jitter_fraction = min(0.30, max(0.05, coefficient))
    counts = Counter(species)
    palette = tuple(sorted(counts))
    cumulative = []
    running = 0.0
    for chemical in palette:
        running += counts[chemical] / len(species)
        cumulative.append(running)
    cumulative[-1] = 1.0
    return AmorphousModel(spacing, jitter_fraction, palette, tuple(cumulative), seed)


def _cluster_ablation(positions: Sequence[Vector], species: Sequence[str]) -> Mapping[str, object]:
    rows = {}
    for name, labels in (("marked", species), ("unmarked", ("X",) * len(species))):
        started = time.perf_counter()
        learned = learn_cluster_candidates(
            labels, positions, neighbor_count=6,
            descriptor_tolerance=1e-5, minimum_occurrences=2)
        recurring_centers = {item.center_index for item in learned.occurrences}
        rows[name] = {
            "recurring_cluster_types": len(learned.cluster_types),
            "recurring_occurrences": len(learned.occurrences),
            "recurring_center_fraction": len(recurring_centers) / len(positions),
            "seconds": time.perf_counter() - started,
        }
    return {
        "domain": "bounded six-neighbour cluster signature",
        "affects_growth_in_this_benchmark": False,
        "reason": "current scalable generators are ablated before GCTS marking is coupled to their move policy",
        "conditions": rows,
        "marked_minus_unmarked_types": (
            rows["marked"]["recurring_cluster_types"]
            - rows["unmarked"]["recurring_cluster_types"]),
    }


def _structural_summary(atoms: Sequence[Atom], bins: int = 20) -> Mapping[str, object]:
    positions = tuple(item[0] for item in atoms)
    species = tuple(item[1] for item in atoms)
    nearest = _nearest_distances(positions)
    nearest_scale = statistics.median(nearest)
    cutoff = 1.35 * nearest_scale
    maximum_radius = 3.0 * nearest_scale
    pair_counts: Counter[str] = Counter()
    histograms: Dict[str, List[int]] = {}
    coordination = []
    for left, point in enumerate(positions):
        neighbors = 0
        for right, other in enumerate(positions):
            if left == right:
                continue
            distance = _distance(point, other)
            if distance <= cutoff:
                neighbors += 1
            if right <= left or distance >= maximum_radius:
                continue
            key = "-".join(sorted((species[left], species[right])))
            bucket = min(bins - 1, int(distance / maximum_radius * bins))
            histograms.setdefault(key, [0] * bins)[bucket] += 1
            pair_counts[key] += 1
        coordination.append(neighbors)
    normalized = {
        key: [value / pair_counts[key] for value in values]
        for key, values in sorted(histograms.items())
    }
    coordination_histogram = Counter(coordination)
    return {
        "atoms": len(atoms),
        "nearest_distance_median": nearest_scale,
        "coordination_cutoff": cutoff,
        "coordination_mean": statistics.mean(coordination),
        "coordination_histogram": {
            str(key): value / len(coordination)
            for key, value in sorted(coordination_histogram.items())
        },
        "partial_rdf_probability": normalized,
        "rdf_note": "species-pair distance probability inside 3x median-nearest radius; not density-normalized g(r)",
    }


def _fidelity(reference: Mapping[str, object], generated: Mapping[str, object]) -> Mapping[str, float]:
    left = reference["partial_rdf_probability"]
    right = generated["partial_rdf_probability"]
    keys = set(left) | set(right)
    rdf_l1 = 0.0
    for key in keys:
        a = left.get(key, [0.0] * 20)
        b = right.get(key, [0.0] * 20)
        rdf_l1 += sum(abs(x - y) for x, y in zip(a, b))
    return {
        "partial_rdf_l1": rdf_l1,
        "coordination_mean_absolute_error": abs(
            float(reference["coordination_mean"])
            - float(generated["coordination_mean"])),
        "nearest_distance_relative_error": abs(
            float(reference["nearest_distance_median"])
            - float(generated["nearest_distance_median"]))
            / float(reference["nearest_distance_median"]),
    }


def _classification_summary(atoms: Sequence[Atom]) -> Mapping[str, object]:
    evaluation = evaluate_structure(
        tuple(atom[0] for atom in atoms),
        tuple(atom[1] for atom in atoms),
    )
    return {
        "category": evaluation.category,
        "confidence": evaluation.confidence,
        "translation_periodicity": evaluation.translation_periodicity,
        "translation_closure": evaluation.translation_closure,
        "local_environment_recurrence": evaluation.local_environment_recurrence,
        "radial_shell_contrast": evaluation.radial_shell_contrast,
        "ordinary_space_group_status": evaluation.space_group.status,
        "reasons": evaluation.reasons,
        "note": "finite audit crop; ordinary space groups require a separately fitted periodic cell",
    }


def _deep_size(value: object, seen: set[int] | None = None) -> int:
    seen = set() if seen is None else seen
    identifier = id(value)
    if identifier in seen:
        return 0
    seen.add(identifier)
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        return size + sum(_deep_size(k, seen) + _deep_size(v, seen) for k, v in value.items())
    if isinstance(value, (tuple, list, set, frozenset)):
        return size + sum(_deep_size(item, seen) for item in value)
    return size


def _materialize(model: CompactModel, count: int) -> Tuple[Atom, ...]:
    dimensions = _dimensions(count)
    return tuple(model.atom(index, dimensions) for index in range(count))


def _hierarchy_levels(training_atoms: int, represented_atoms: int) -> int:
    if represented_atoms <= training_atoms:
        return 0
    return math.ceil(math.log(represented_atoms / training_atoms, 8.0))


def _run_family(
    family: str,
    training: Tuple[Tuple[Vector, ...], Tuple[str, ...]],
    fit,
    represented_atoms: int,
    audit_atoms: int,
    materialization: str,
) -> Mapping[str, object]:
    positions, species = training
    learning_started = time.perf_counter()
    model = fit(positions, species)
    learning_seconds = time.perf_counter() - learning_started
    marking = _cluster_ablation(positions, species)

    compile_started = time.perf_counter()
    dimensions = _dimensions(represented_atoms)
    implicit = {
        "dimensions": dimensions,
        "capacity_atoms": math.prod(dimensions),
        "represented_atoms": represented_atoms,
        "hierarchy_levels_at_branching_8": _hierarchy_levels(len(positions), represented_atoms),
        "grammar": model.grammar,
    }
    compile_seconds = time.perf_counter() - compile_started

    if materialization == "full":
        materialized_count = represented_atoms
    elif materialization == "audit":
        materialized_count = audit_atoms
    else:
        materialized_count = 0
    explicit_started = time.perf_counter()
    materialized = _materialize(model, materialized_count) if materialized_count else ()
    explicit_seconds = time.perf_counter() - explicit_started

    audit_count = min(audit_atoms, represented_atoms)
    generated_audit = (_materialize(model, audit_count)
                       if materialized_count != audit_count else materialized)
    reference_atoms = tuple(zip(positions, species))
    reference_summary = _structural_summary(reference_atoms)
    generated_summary = _structural_summary(generated_audit)
    measured_bytes = _deep_size(materialized) if materialized else 0
    bytes_per_atom = measured_bytes / materialized_count if materialized_count else None
    atoms_per_second = (
        materialized_count / explicit_seconds
        if materialized_count and explicit_seconds > 0 else None)
    return {
        "family": family,
        "training_atoms": len(positions),
        "learning_seconds": learning_seconds,
        "marking_ablation": marking,
        "implicit": {
            **implicit,
            "compile_seconds": compile_seconds,
            "python_size_bytes": _deep_size(implicit),
            "warning": "represented atoms are addressable but are not force-evaluated MD atoms",
        },
        "explicit": {
            "mode": materialization,
            "materialized_atoms": materialized_count,
            "seconds": explicit_seconds,
            "measured_atoms_per_second": atoms_per_second,
            "linear_projected_seconds_for_represented_atoms": (
                represented_atoms / atoms_per_second if atoms_per_second else None),
            "measured_python_bytes": measured_bytes,
            "measured_python_bytes_per_atom": bytes_per_atom,
            "projected_python_bytes_for_represented_atoms": (
                bytes_per_atom * represented_atoms if bytes_per_atom else None),
            "packed_lower_bound_bytes_for_represented_atoms": represented_atoms * 25,
        },
        "structural_fidelity": {
            "reference": reference_summary,
            "generated_audit": generated_summary,
            "errors": _fidelity(reference_summary, generated_summary),
        },
        "posthoc_order_classification": _classification_summary(generated_audit),
    }


def benchmark(
    represented_atoms: int = 1_048_576,
    training_atoms: int = 512,
    audit_atoms: int = 512,
    materialization: str = "audit",
    seed: int = 20260805,
) -> Mapping[str, object]:
    if not 256 <= training_atoms <= 1024:
        raise ValueError("training_atoms must be in [256, 1024]")
    if represented_atoms < training_atoms:
        raise ValueError("represented_atoms must not be smaller than training_atoms")
    if audit_atoms < 32:
        raise ValueError("audit_atoms must be at least 32")
    if materialization not in {"none", "audit", "full"}:
        raise ValueError("invalid materialization mode")

    crystal = _crystal_training(training_atoms)
    quasi = _fibonacci_training(training_atoms)
    amorphous_radius = 5.5 * (training_atoms / 300.0) ** (1.0 / 3.0)
    amorphous_sample = amorphous_hard_core_point_set(
        atom_count=training_atoms, radius=amorphous_radius, seed=seed % (1 << 31))
    amorphous = amorphous_sample.positions, amorphous_sample.species

    started = time.perf_counter()
    systems = (
        _run_family("crystal", crystal, _fit_crystal, represented_atoms,
                    audit_atoms, materialization),
        _run_family("quasicrystal_model_set", quasi, _fit_fibonacci,
                    represented_atoms, audit_atoms, materialization),
        _run_family("amorphous_stochastic", amorphous,
                    lambda p, s: _fit_amorphous(p, s, seed + 1),
                    represented_atoms, audit_atoms, materialization),
    )
    return {
        "benchmark": "hundreds_to_million_colored_point_growth",
        "schema_version": 1,
        "represented_atoms": represented_atoms,
        "requested_training_atoms": training_atoms,
        "audit_atoms": audit_atoms,
        "materialization": materialization,
        "total_wall_seconds": time.perf_counter() - started,
        "systems": systems,
        "interpretation": {
            "claim_supported": "compact structural continuation and bounded structural audit",
            "claim_not_yet_supported": "replacement of million-atom MD trajectories, forces, kinetics, or thermodynamics",
            "next_required_baseline": "held-out million-atom MD configurations and force/energy relaxation audit",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--represented-atoms", type=int, default=1_048_576)
    parser.add_argument("--training-atoms", type=int, default=512)
    parser.add_argument("--audit-atoms", type=int, default=512)
    parser.add_argument("--materialize", choices=("none", "audit", "full"), default="audit")
    parser.add_argument("--seed", type=int, default=20260805)
    parser.add_argument("--output", help="write JSON to this path instead of stdout")
    arguments = parser.parse_args()
    result = benchmark(
        represented_atoms=arguments.represented_atoms,
        training_atoms=arguments.training_atoms,
        audit_atoms=arguments.audit_atoms,
        materialization=arguments.materialize,
        seed=arguments.seed,
    )
    payload = json.dumps(result, indent=2, sort_keys=True)
    if arguments.output:
        with open(arguments.output, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
    else:
        print(payload)


if __name__ == "__main__":
    main()
