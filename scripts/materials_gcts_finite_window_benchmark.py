#!/usr/bin/env python3
"""Finite-window stability gate for generic recursive GCTS discovery."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Tuple

import materials_gcts_blind_continuation as blind
from materials_gcts_2d_generic_atlas import (
    _score, layered_hexagonal_configuration)
from materials_gcts_fibonacci_3d import make_input
from materials_gcts_generic import AtomicConfiguration, supercell
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_recursive_program import (
    discover_recursive_program_candidates, explicit_apply,
    select_recursive_program_candidate)
from materials_gcts_typed_productions import induce_typed_transform_program


@dataclass(frozen=True)
class WindowCase:
    system: str
    crop: str
    observed_atoms: int
    selected_program: str
    parameter_signature: Tuple[object, ...]
    candidate_programs: Tuple[str, ...]
    selected_score: float
    grown_atoms: int
    exact_clean_continuation: bool


@dataclass(frozen=True)
class FamilyWindowResult:
    family: str
    cases: Tuple[WindowCase, ...]
    atom_range: Tuple[int, int]
    selected_program_stable: bool
    learned_parameter_signature_stable: bool
    all_clean_continuations_exact: bool


@dataclass(frozen=True)
class FiniteWindowBenchmark:
    families: Tuple[FamilyWindowResult, ...]
    window_cases: int
    crop_geometries: Tuple[str, ...]
    all_programs_stable: bool
    all_parameters_stable: bool
    all_continuations_exact: bool
    benchmark_passed: bool


def _sites(configuration: AtomicConfiguration) -> set[tuple]:
    return {(blind._site_key(point), chemical)
            for point, chemical in zip(configuration.positions,
                                       configuration.species)}


def _nacl(repeats: int) -> AtomicConfiguration:
    fcc = ((0, 0, 0), (0, .5, .5), (.5, 0, .5), (.5, .5, 0))
    basis = []
    for point in fcc:
        basis.extend(((point, "Na"),
                      (((point[0] + .5) % 1, point[1], point[2]), "Cl")))
    generated = supercell(
        f"NaCl-window-{repeats}", basis, (repeats,) * 3, (5.64,) * 3,
        "finite cubic crop; cell metadata removed before learning")
    return AtomicConfiguration(generated.name, generated.positions,
                               generated.species)


def _gram_signature(vectors) -> Tuple[float, ...]:
    return tuple(round(sum(left[axis] * right[axis] for axis in range(3)), 5)
                 for left_index, left in enumerate(vectors)
                 for right in vectors[left_index:])


def _signature(configuration: AtomicConfiguration, program) -> Tuple[object, ...]:
    payload = program._payload
    if program.family == "translation_quotient":
        return (len(payload.translation_motif),
                _gram_signature(payload.translation_basis))
    if program.family == "substitution_product":
        return (payload.substitution_images,
                tuple(item[:3] + (item[3],)
                      for item in payload.substitution_decoration),
                tuple(round(value, 6)
                      for value in payload.substitution_gap_lengths))
    if program.family == "internal_section_inflation":
        typed = induce_typed_transform_program(configuration, payload)
        predicate = typed.section_productions[0].predicate
        return (round(predicate.algebraic_unit, 8),
                round(predicate.window_radius, 8),
                tuple(round(value, 8)
                      for value in predicate.chemical_threshold_fractions))
    atlas = payload
    components = tuple(sorted(
        (len(component.motif), component.motif_isometry_class,
         _gram_signature(component.translations))
        for component in atlas.components))
    return (atlas.motif_isometry_classes, atlas.pose_states, components)


def _case(configuration: AtomicConfiguration, crop: str,
          expected: AtomicConfiguration, planar: bool = False) -> WindowCase:
    candidates = discover_recursive_program_candidates(configuration)
    selected = select_recursive_program_candidate(candidates)
    grown = explicit_apply(configuration, selected.program, 1)
    exact = (_score(grown, expected) == (1.0, 1.0, 1.0)
             if planar else _sites(grown) == _sites(expected))
    return WindowCase(
        configuration.name, crop, len(configuration.positions),
        selected.program.family,
        _signature(configuration, selected.program),
        tuple(candidate.program.family for candidate in candidates),
        selected.selection_score, len(grown.positions), exact)


def _family(name: str, cases: Tuple[WindowCase, ...]) -> FamilyWindowResult:
    programs = {case.selected_program for case in cases}
    signatures = {case.parameter_signature for case in cases}
    return FamilyWindowResult(
        name, cases,
        (min(case.observed_atoms for case in cases),
         max(case.observed_atoms for case in cases)),
        len(programs) == 1, len(signatures) == 1,
        all(case.exact_clean_continuation for case in cases))


def evaluate() -> FiniteWindowBenchmark:
    crystal_cases = []
    for repeats in (2, 3, 4):
        seed = _nacl(repeats)
        crystal_cases.append(_case(seed, f"cubic {repeats}^3 cells",
                                   _nacl(2 * repeats)))

    iqc_cases = []
    for radius, bound in ((7.5, 3), (9.0, 3), (11.0, 4)):
        seed, _ = oracle_patch(bound, radius)
        # The learned parent radius is the smallest containing integer radius.
        target_radius = math.ceil(radius - 1e-9) * (
            1.0 + math.sqrt(5.0)) / 2.0
        target, _ = oracle_patch(bound + 3, target_radius)
        iqc_cases.append(_case(seed, f"spherical R={radius:g}", target))

    substitution_cases = []
    for side, next_side in ((6, 10), (9, 15), (12, 20)):
        substitution_cases.append(_case(
            make_input(side), f"Cartesian {side}^3 sites",
            make_input(next_side)))

    planar_cases = []
    basis = ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N"))
    angles = (0.0, math.pi / 6)
    for radius in (14.0, 18.0, 22.0):
        seed = layered_hexagonal_configuration(
            f"hBN-window-{radius:g}", radius, basis, angles,
            global_rotation=True)
        candidates = discover_recursive_program_candidates(seed)
        selected = select_recursive_program_candidate(candidates)
        target = layered_hexagonal_configuration(
            f"hBN-window-target-{radius:g}",
            selected.program.observation_radius * 2, basis, angles,
            global_rotation=True)
        planar_cases.append(_case(
            seed, f"two circular disks R={radius:g}", target, True))

    families = (
        _family("periodic crystal", tuple(crystal_cases)),
        _family("icosahedral model set", tuple(iqc_cases)),
        _family("substitution quasicrystal", tuple(substitution_cases)),
        _family("twisted planar bilayer", tuple(planar_cases)),
    )
    stable_programs = all(item.selected_program_stable for item in families)
    stable_parameters = all(item.learned_parameter_signature_stable
                            for item in families)
    exact = all(item.all_clean_continuations_exact for item in families)
    return FiniteWindowBenchmark(
        families, sum(len(item.cases) for item in families),
        ("cubic", "spherical", "Cartesian product", "circular bilayer"),
        stable_programs, stable_parameters, exact,
        stable_programs and stable_parameters and exact)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
