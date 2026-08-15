#!/usr/bin/env python3
"""Explicit million-site certificates for learned crystal and IQC programs."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import struct
import time
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable, Tuple

from materials_gcts_generic import benchmark_systems
from materials_gcts_fibonacci_3d import (
    HIDDEN_FIBONACCI, Substitution, apply_substitution,
    coordinates_from_gaps, generate, make_input, species_at)
from materials_gcts_geometry_vm import compile_metric_overlap_from_seed
from materials_gcts_icosahedral_modelset import (
    HIDDEN_SPECIES_THRESHOLDS, HIDDEN_UNIT, HIDDEN_WINDOW, hidden_species,
    oracle_patch)
from materials_gcts_propagated_marking import (
    emit_marked_macro_sites, fit_propagated_marking)
from materials_gcts_recursive_program import discover_recursive_program


Site = Tuple[Tuple[float, float, float], str]


@dataclass(frozen=True)
class MillionEmissionCurve:
    system: str
    learned_family: str
    seed_atoms: int
    macro_actions: int
    sites_emitted: int
    observed_growth: float
    minimum_growth_per_action: float
    explicit_site_insertions: int
    site_insertions_per_macro_action: float
    emission_seconds: float
    species_counts: Tuple[Tuple[str, int], ...]
    coordinate_digest: str
    independent_oracle_digest: str | None
    exact_certificate: bool
    positions_retained: bool


@dataclass(frozen=True)
class MillionEmissionBenchmark:
    crystal: MillionEmissionCurve
    quasicrystal: MillionEmissionCurve
    fibonacci_quasicrystal: MillionEmissionCurve
    both_explicitly_exceed_one_million: bool
    both_exact: bool
    all_three_explicitly_exceed_one_million: bool
    all_three_exact: bool
    physical_potential_used: bool
    heldout_sites_used_for_learning: bool
    quasicrystal_gcts_marking_compiled: bool
    coordinate_lift_used_during_emission: bool
    benchmark_passed: bool


def _digest(sites: Iterable[Site]):
    # Addition modulo 2^256 makes the certificate independent of emission
    # order, so a structurally independent oracle need not mimic the learner's
    # traversal. Each site still contributes a cryptographic 256-bit digest.
    digest_sum = 0
    counts = Counter()
    total = 0
    for point, chemical in sites:
        total += 1
        counts[chemical] += 1
        site_digest = hashlib.sha256()
        site_digest.update(chemical.encode("ascii"))
        site_digest.update(struct.pack(">3q", *(round(value / 1e-5)
                                               for value in point)))
        digest_sum = (digest_sum + int.from_bytes(
            site_digest.digest(), "big")) % (1 << 256)
    return total, tuple(sorted(counts.items())), f"{digest_sum:064x}"


def _crystal_sites(configuration, rule, actions):
    if (rule.translation_basis is None or
            rule.translation_index_minimum is None or
            rule.translation_index_maximum is None):
        raise ValueError("incomplete learned translation quotient")
    initial_extents = tuple(
        rule.translation_index_maximum[axis] -
        rule.translation_index_minimum[axis] + 1 for axis in range(3))
    extents = tuple(value * 2 ** actions for value in initial_extents)
    basis = rule.translation_basis
    for cell in itertools.product(*(range(value) for value in extents)):
        for chemical, fx, fy, fz in rule.translation_motif:
            fractional = (cell[0] + fx, cell[1] + fy, cell[2] + fz)
            point = tuple(sum(fractional[axis] * basis[axis][coordinate]
                              for axis in range(3))
                          for coordinate in range(3))
            yield point, chemical


def _hidden_iqc_sites(radius):
    """Independent Cartesian oracle using only the sealed model constants."""
    unit = HIDDEN_UNIT
    conjugate = -1.0 / unit
    denominator = unit - conjugate
    bound_a = math.ceil(
        (unit * HIDDEN_WINDOW + abs(conjugate) * radius) / denominator + 1e-9)
    bound_b = math.ceil((radius + HIDDEN_WINDOW) / denominator + 1e-9)
    coordinate_pairs = []
    for a in range(-bound_a, bound_a + 1):
        for b in range(-bound_b, bound_b + 1):
            physical = a + b * unit
            internal = a + b * conjugate
            if (abs(physical) <= radius + 1e-10 and
                    abs(internal) <= HIDDEN_WINDOW + 1e-10):
                coordinate_pairs.append((a, b, physical, internal))
    radius_squared = radius * radius
    window_squared = HIDDEN_WINDOW * HIDDEN_WINDOW
    for xa, xb, x, xi in coordinate_pairs:
        for ya, yb, y, yi in coordinate_pairs:
            if x * x + y * y > radius_squared + 1e-10:
                continue
            if xi * xi + yi * yi > window_squared + 1e-10:
                continue
            if (xa - yb) % 2:
                continue
            for za, zb, z, zi in coordinate_pairs:
                if ((ya - zb) % 2 or (za - xb) % 2 or
                        x * x + y * y + z * z > radius_squared + 1e-10 or
                        xi * xi + yi * yi + zi * zi >
                        window_squared + 1e-10):
                    continue
                internal_radius = math.sqrt(xi * xi + yi * yi + zi * zi)
                yield (x, y, z), hidden_species(internal_radius)


def _hidden_nacl_sites(cells, lattice_constant):
    """Independent half-grid rocksalt oracle, without the learned motif."""
    for i, j, k in itertools.product(range(2 * cells), repeat=3):
        chemical = "Na" if (i + j + k) % 2 == 0 else "Cl"
        yield ((i * lattice_constant / 2,
                j * lattice_constant / 2,
                k * lattice_constant / 2), chemical)


def _fibonacci_sites(rule, actions):
    image_a, image_b, seed = rule.substitution_images
    substitution = Substitution(image_a, image_b, seed)
    word = generate(substitution, rule.input_side)
    for _ in range(actions):
        word = apply_substitution(word, substitution)
    short, long = rule.substitution_gap_lengths
    coordinates = [0.0]
    for symbol in word[:-1]:
        coordinates.append(coordinates[-1] +
                           (long if symbol == "A" else short))
    decoration = {item[:3]: item[3]
                  for item in rule.substitution_decoration}
    inverse = tuple(tuple(rule.to_canonical[column][row]
                          for column in range(3)) for row in range(3))
    minimum = rule.canonical_minimum
    for i, j, k in itertools.product(range(len(word)), repeat=3):
        canonical = (coordinates[i] + minimum[0],
                     coordinates[j] + minimum[1],
                     coordinates[k] + minimum[2])
        point = tuple(sum(inverse[row][column] * canonical[column]
                          for column in range(3)) + rule.origin[row]
                      for row in range(3))
        yield point, decoration[(word[i], word[j], word[k])]


def _hidden_fibonacci_sites(side):
    word = generate(HIDDEN_FIBONACCI, side)
    coordinates = coordinates_from_gaps(word[:side - 1])
    for i, j, k in itertools.product(range(side), repeat=3):
        yield ((coordinates[i], coordinates[j], coordinates[k]),
               "A" if species_at(word, i, j, k) == 0 else "B")


def _curve(system, family, seed_atoms, actions,
           seconds, result, oracle_digest=None):
    total, species, digest = result
    growth = total / seed_atoms
    return MillionEmissionCurve(
        system, family, seed_atoms, actions, total, growth,
        growth ** (1.0 / actions), total - seed_atoms,
        (total - seed_atoms) / actions, seconds, species,
        digest, oracle_digest, oracle_digest is None or digest == oracle_digest,
        False)


def evaluate():
    crystal = next(item for item in benchmark_systems()
                   if item.name == "NaCl-rocksalt")
    crystal_program = discover_recursive_program(crystal)
    crystal_actions = 5
    started = time.perf_counter()
    crystal_result = _digest(_crystal_sites(
        crystal, crystal_program._payload, crystal_actions))
    crystal_seconds = time.perf_counter() - started
    crystal_cells = 3 * 2 ** crystal_actions
    hidden_crystal = _digest(_hidden_nacl_sites(
        crystal_cells, crystal_program._payload.translation_basis[0][0]))
    crystal_curve = _curve(
        crystal.name, crystal_program.family, len(crystal.positions),
        crystal_actions, crystal_seconds, crystal_result, hidden_crystal[2])

    iqc, _ = oracle_patch(3, 9.0)
    iqc_program = discover_recursive_program(iqc)
    iqc_instruction = compile_metric_overlap_from_seed(iqc)
    iqc_marking = fit_propagated_marking(iqc_instruction, iqc)
    iqc_actions = 6
    radius = 9.0 * iqc_program._payload.scale ** iqc_actions
    started = time.perf_counter()
    iqc_result = _digest(emit_marked_macro_sites(
        iqc_instruction, iqc_marking, radius))
    iqc_seconds = time.perf_counter() - started
    _, hidden_species_counts, hidden_digest = _digest(
        _hidden_iqc_sites(radius))
    if hidden_species_counts != iqc_result[1]:
        hidden_digest = "species-count-mismatch:" + hidden_digest
    iqc_curve = _curve(
        iqc.name, "carried_mark_address_macro", len(iqc.positions), iqc_actions,
        iqc_seconds, iqc_result, hidden_digest)

    fibonacci = make_input(9)
    fibonacci_program = discover_recursive_program(fibonacci)
    fibonacci_actions = 5
    started = time.perf_counter()
    fibonacci_result = _digest(_fibonacci_sites(
        fibonacci_program._payload, fibonacci_actions))
    fibonacci_seconds = time.perf_counter() - started
    fibonacci_side = round(fibonacci_result[0] ** (1.0 / 3.0))
    hidden_fibonacci = _digest(_hidden_fibonacci_sites(fibonacci_side))
    fibonacci_curve = _curve(
        fibonacci.name, fibonacci_program.family, len(fibonacci.positions),
        fibonacci_actions, fibonacci_seconds, fibonacci_result,
        hidden_fibonacci[2])
    million = min(crystal_curve.sites_emitted,
                  iqc_curve.sites_emitted) >= 1_000_000
    exact = crystal_curve.exact_certificate and iqc_curve.exact_certificate
    all_million = min(crystal_curve.sites_emitted, iqc_curve.sites_emitted,
                      fibonacci_curve.sites_emitted) >= 1_000_000
    all_exact = exact and fibonacci_curve.exact_certificate
    return MillionEmissionBenchmark(
        crystal_curve, iqc_curve, fibonacci_curve, million, exact,
        all_million, all_exact, False, False, True, False,
        all_million and all_exact)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
