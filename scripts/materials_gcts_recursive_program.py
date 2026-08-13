#!/usr/bin/env python3
"""One family-blind recursive GCTS program interface for 2D and 3D inputs.

The existing learners deliberately use different internal representations:
translation quotients, internal-space sections, substitution words, and
planar pose/address atlases.  This module does not erase those distinctions.
It gives them one auditable contract and selects among them from positions and
species alone, without a crystal/quasicrystal/2D label.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Tuple

from materials_gcts_2d_generic_atlas import (
    GenericPlanarAtlas, _score, grow, learn_planar_atlas)
from materials_gcts_2d_recursive_macro import expand_level
from materials_gcts_fibonacci_3d import Substitution, apply_substitution, generate
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_latent_macro_growth import _latent_atom_count
from materials_gcts_parametric_recursive import (
    ParametricRecursiveRule, apply_rule_actions, discover_rule,
    discover_rule_candidates)


@dataclass(frozen=True)
class RecursiveProgram:
    family: str
    deterministic: bool
    intrinsic_dimension: int
    child_references_per_macro: int
    primitive_cluster_atoms: int
    pose_states: int
    growth_base: float
    marking: str
    hierarchy_supports: Tuple[int, ...]
    observed_atoms: int
    base_symbolic_atoms: int
    seed_equivalent_level: int
    observation_radius: float
    selection_reason: str
    family_label_used: bool
    heldout_atoms_used: bool
    physical_potential_used: bool
    _payload: Any = field(repr=False, compare=False)


@dataclass(frozen=True)
class RecursiveProgramCandidate:
    program: RecursiveProgram
    normalized_residual: float
    description_entries: int
    seed_replay_exact: bool
    seed_mismatch_fraction: float
    selection_score: float
    evidence_kind: str


@dataclass(frozen=True)
class RepresentedCount:
    atoms: int
    exact: bool
    method: str


def _covariance_eigenvalues(configuration: AtomicConfiguration) -> tuple[float, float, float]:
    center = tuple(sum(point[axis] for point in configuration.positions) /
                   len(configuration.positions) for axis in range(3))
    matrix = [[0.0] * 3 for _ in range(3)]
    for point in configuration.positions:
        delta = [point[axis] - center[axis] for axis in range(3)]
        for row in range(3):
            for column in range(3):
                matrix[row][column] += delta[row] * delta[column]
    for row in range(3):
        for column in range(3):
            matrix[row][column] /= len(configuration.positions)
    # Jacobi rotations are ample for a real symmetric 3x3 covariance matrix.
    for _ in range(24):
        row, column = max(((0, 1), (0, 2), (1, 2)),
                          key=lambda pair: abs(matrix[pair[0]][pair[1]]))
        if abs(matrix[row][column]) < 1e-12:
            break
        angle = .5 * math.atan2(2 * matrix[row][column],
                                matrix[column][column] - matrix[row][row])
        cosine, sine = math.cos(angle), math.sin(angle)
        for index in range(3):
            left, right = matrix[index][row], matrix[index][column]
            matrix[index][row] = cosine * left - sine * right
            matrix[index][column] = sine * left + cosine * right
        for index in range(3):
            upper, lower = matrix[row][index], matrix[column][index]
            matrix[row][index] = cosine * upper - sine * lower
            matrix[column][index] = sine * upper + cosine * lower
    return tuple(sorted(matrix[index][index] for index in range(3)))  # type: ignore[return-value]


def _planarity_ratio(configuration: AtomicConfiguration) -> float:
    eigenvalues = _covariance_eigenvalues(configuration)
    return eigenvalues[0] / max(eigenvalues[-1], 1e-12)


def _planar_radius(configuration: AtomicConfiguration,
                   atlas: GenericPlanarAtlas) -> float:
    radius = 0.0
    for point in configuration.positions:
        best = math.inf
        for component in atlas.components:
            delta = tuple(point[axis] - atlas.observation_center[axis]
                          for axis in range(3))
            normal = sum(delta[axis] * component.normal[axis]
                         for axis in range(3))
            planar = tuple(delta[axis] - normal * component.normal[axis]
                           for axis in range(3))
            best = min(best, math.sqrt(sum(value * value
                                            for value in planar)))
        radius = max(radius, best)
    return radius


def _try_planar(
    configuration: AtomicConfiguration,
) -> tuple[RecursiveProgram, bool, float] | None:
    ratio = _planarity_ratio(configuration)
    # Multiple separated sheets have nonzero thickness.  The exact atlas
    # replay below is the authoritative gate; this loose ratio only avoids an
    # expensive planar fit for isotropic 3-D clouds.
    if ratio >= .25:
        return None
    learned = None
    for fit_tolerance in (2e-5, .02, .045):
        try:
            # The address envelope is centred on the observed finite sample,
            # not the ambient coordinate origin. Inferring this point is
            # necessary for translation-equivariant imported data.
            observation_center = tuple(
                sum(point[axis] for point in configuration.positions) /
                len(configuration.positions) for axis in range(3))
            candidate = learn_planar_atlas(
                configuration, observation_center=observation_center,
                tolerance=fit_tolerance)
            if (candidate.components and candidate.seed_atoms_covered ==
                    len(configuration.positions) and all(
                        len(component.translations) == 2
                        for component in candidate.components)):
                learned = candidate
                break
        except (AssertionError, RuntimeError, ValueError, ZeroDivisionError):
            continue
    if learned is None:
        return None
    atlas = learned
    radius = _planar_radius(configuration, atlas) + 1e-7
    replay = grow(atlas, radius)
    precision, recall, chemistry = _score(replay, configuration)
    exact = min(precision, recall, chemistry) >= .999
    mismatch = 1.0 - min(precision, recall, chemistry)
    replay_description = "exact atlas replay"
    if not exact:
        from materials_gcts_2d_robustness import _registered_score
        precision, recall, chemistry, rms = _registered_score(
            replay, configuration, tolerance=.16)
        mismatch = 1.0 - min(precision, recall, chemistry)
        if (min(precision, recall) < .94 or chemistry < .999 or rms > .08):
            return None
        replay_description = (
            f"robust registered replay P={precision:.4f}, R={recall:.4f}, "
            f"RMS={rms:.4g}")
    primitive = sum(len(component.motif) for component in atlas.components)
    seed_level = max(0, math.ceil(math.log(
        max(1.0, len(configuration.positions) / primitive), 4.0)))
    supports = tuple(primitive * 4 ** level for level in range(3))
    program = RecursiveProgram(
        "planar_pose_address", True, 2, 4, primitive,
        len(atlas.components), 4.0,
        "component pose + two learned translation ports", supports,
        len(configuration.positions), primitive * 4 ** seed_level,
        seed_level, radius,
        f"covariance planarity ratio {ratio:.6g}; {replay_description}", False,
        False, False, atlas)
    return program, exact, mismatch


def _program_from_rule(configuration: AtomicConfiguration,
                       rule: ParametricRecursiveRule) -> RecursiveProgram:
    primitive = (len(rule.translation_motif)
                 if rule.family == "translation_quotient"
                 else max(1, rule.hierarchy_supports[0]))
    children = (8 if rule.family == "translation_quotient" else
                2 if rule.family == "substitution_product" else 1)
    return RecursiveProgram(
        rule.family, True, 3, children, primitive, 1,
        8.0 if rule.family == "translation_quotient" else
        (1 + math.sqrt(5)) ** 3 / 8 if rule.family == "internal_section_inflation"
        else 4.23606797749979,
        rule.marking, rule.hierarchy_supports, len(configuration.positions),
        len(configuration.positions), 0, rule.input_radius or 0.0,
        rule.reason, False, False, False, rule)


def discover_recursive_program_candidates(
    configuration: AtomicConfiguration,
) -> Tuple[RecursiveProgramCandidate, ...]:
    """Evaluate planar and 3-D hypotheses before choosing either one."""
    candidates = []
    planar_fit = _try_planar(configuration)
    if planar_fit is not None:
        planar, exact, mismatch = planar_fit
        atlas: GenericPlanarAtlas = planar._payload
        complexity = (sum(len(component.motif) + 2
                          for component in atlas.components) +
                      len(atlas.components))
        score = mismatch + complexity / len(configuration.positions)
        candidates.append(RecursiveProgramCandidate(
            planar, mismatch, complexity, exact, mismatch, score,
            "exact planar seed replay"))
    for candidate in discover_rule_candidates(configuration):
        candidates.append(RecursiveProgramCandidate(
            _program_from_rule(configuration, candidate.rule),
            candidate.normalized_residual,
            candidate.description_entries,
            candidate.seed_replay_exact,
            candidate.seed_mismatch_fraction,
            candidate.selection_score,
            "3-D geometric hypothesis"))
    return tuple(sorted(candidates, key=lambda candidate: (
        candidate.selection_score, candidate.description_entries,
        candidate.program.marking)))


def select_recursive_program_candidate(
    candidates: Tuple[RecursiveProgramCandidate, ...],
) -> RecursiveProgramCandidate:
    if not candidates:
        raise ValueError("no admitted recursive program candidate")
    return min(candidates, key=lambda candidate: (
        candidate.selection_score, candidate.description_entries,
        candidate.program.marking))


def discover_recursive_program(configuration: AtomicConfiguration) -> RecursiveProgram:
    candidates = discover_recursive_program_candidates(configuration)
    if candidates:
        return select_recursive_program_candidate(candidates).program
    rule = discover_rule(configuration)
    return RecursiveProgram(
        "none", False, 3, 0, 0, 0, 1.0, rule.marking,
        rule.hierarchy_supports, len(configuration.positions),
        len(configuration.positions), 0, 0.0, rule.reason,
        False, False, False, rule)


def explicit_apply(configuration: AtomicConfiguration,
                   program: RecursiveProgram, actions: int
                   ) -> AtomicConfiguration:
    if actions < 0:
        raise ValueError("actions must be nonnegative")
    if not program.deterministic:
        raise ValueError("cannot apply a rejected recursive program")
    if program.family == "planar_pose_address":
        atlas: GenericPlanarAtlas = program._payload
        radius = program.observation_radius * 2 ** actions
        level = program.seed_equivalent_level + actions + 1
        return expand_level(atlas, level, radius)
    return apply_rule_actions(
        configuration, program._payload, actions)  # type: ignore[arg-type]


def symbolic_count(configuration: AtomicConfiguration,
                   program: RecursiveProgram, actions: int) -> int:
    if actions < 0:
        raise ValueError("actions must be nonnegative")
    if not program.deterministic:
        return len(configuration.positions)
    if program.family == "planar_pose_address":
        return program.base_symbolic_atoms * 4 ** actions
    if program.family == "translation_quotient":
        return len(configuration.positions) * 8 ** actions
    rule: ParametricRecursiveRule = program._payload
    if program.family == "substitution_product":
        if rule.substitution_images is None or rule.input_side is None:
            raise ValueError("substitution program is incomplete")
        first, second, seed = rule.substitution_images
        substitution = Substitution(first, second, seed)
        word = generate(substitution, rule.input_side)
        for _ in range(actions):
            word = apply_substitution(word, substitution)
        return len(word) ** 3
    if program.family == "internal_section_inflation":
        if rule.input_radius is None:
            raise ValueError("internal-section program is incomplete")
        return (len(configuration.positions) if actions == 0 else
                _latent_atom_count(configuration,
                                   rule.input_radius * rule.scale ** actions))
    raise ValueError(f"unsupported recursive program {program.family}")


def _determinant(matrix: list[list[float]]) -> float:
    work = [row[:] for row in matrix]
    determinant = 1.0
    for column in range(len(work)):
        pivot = max(range(column, len(work)),
                    key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) < 1e-15:
            return 0.0
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            determinant *= -1.0
        value = work[column][column]
        determinant *= value
        for row in range(column + 1, len(work)):
            factor = work[row][column] / value
            for index in range(column, len(work)):
                work[row][index] -= factor * work[column][index]
    return determinant


def fast_represented_count(
    configuration: AtomicConfiguration, program: RecursiveProgram,
    actions: int,
) -> RepresentedCount:
    """Count a compact representation without enumerating its atom sites.

    Finite production graphs have exact incidence counts. A continuous model
    set has an exact compact radius/section representation, but its fast count
    is the cut-and-project density estimate; exact finite-window counting still
    requires site enumeration and remains available through ``symbolic_count``.
    """
    if actions < 0:
        raise ValueError("actions must be nonnegative")
    if program.family != "internal_section_inflation":
        return RepresentedCount(
            symbolic_count(configuration, program, actions), True,
            "finite production incidence")
    if actions == 0:
        return RepresentedCount(len(configuration.positions), True,
                                "observed root")
    from materials_gcts_icosahedral_modelset import star_vectors
    rule: ParametricRecursiveRule = program._payload
    if (rule.origin is None or rule.to_canonical is None or
            rule.input_radius is None):
        raise ValueError("internal-section program is incomplete")
    if rule.section_window_radius is None:
        raise ValueError("internal-section program lacks its learned window")
    unit, window = rule.scale, rule.section_window_radius
    physical, internal = star_vectors(unit), star_vectors(-1.0 / unit)
    columns = tuple(left + right for left, right in zip(physical, internal))
    matrix = [[columns[column][row] for column in range(6)]
              for row in range(6)]
    covolume = abs(_determinant(matrix))
    radius = rule.input_radius * rule.scale ** actions
    ball = lambda value: 4.0 * math.pi * value ** 3 / 3.0
    estimate = round(ball(radius) * ball(window) / covolume)
    return RepresentedCount(
        estimate, False,
        "learned physical/internal volumes divided by rank-6 covolume")


def fast_actions_to_at_least(
    configuration: AtomicConfiguration, program: RecursiveProgram,
    target_atoms: int = 1_000_000,
) -> tuple[int, RepresentedCount]:
    for actions in range(24):
        count = fast_represented_count(configuration, program, actions)
        if count.atoms >= target_atoms:
            return actions, count
    raise RuntimeError("recursive program did not reach target within 24 actions")


def actions_to_at_least(configuration: AtomicConfiguration,
                        program: RecursiveProgram,
                        target_atoms: int = 1_000_000) -> tuple[int, int]:
    for actions in range(24):
        count = symbolic_count(configuration, program, actions)
        if count >= target_atoms:
            return actions, count
    raise RuntimeError("recursive program did not reach target within 24 actions")
