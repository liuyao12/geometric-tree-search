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
    ParametricRecursiveRule, apply_rule_actions, discover_rule)


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


def _try_planar(configuration: AtomicConfiguration) -> RecursiveProgram | None:
    ratio = _planarity_ratio(configuration)
    # Multiple separated sheets have nonzero thickness.  The exact atlas
    # replay below is the authoritative gate; this loose ratio only avoids an
    # expensive planar fit for isotropic 3-D clouds.
    if ratio >= .25:
        return None
    try:
        atlas = learn_planar_atlas(configuration)
    except (AssertionError, RuntimeError, ValueError, ZeroDivisionError):
        return None
    if (not atlas.components or atlas.seed_atoms_covered != len(configuration.positions)
            or any(len(component.translations) != 2 for component in atlas.components)):
        return None
    radius = _planar_radius(configuration, atlas) + 1e-7
    replay = grow(atlas, radius)
    precision, recall, chemistry = _score(replay, configuration)
    if min(precision, recall, chemistry) < .999:
        return None
    primitive = sum(len(component.motif) for component in atlas.components)
    seed_level = max(0, math.ceil(math.log(
        max(1.0, len(configuration.positions) / primitive), 4.0)))
    supports = tuple(primitive * 4 ** level for level in range(3))
    return RecursiveProgram(
        "planar_pose_address", True, 2, 4, primitive,
        len(atlas.components), 4.0,
        "component pose + two learned translation ports", supports,
        len(configuration.positions), primitive * 4 ** seed_level,
        seed_level, radius,
        f"covariance planarity ratio {ratio:.6g}; exact atlas replay", False,
        False, False, atlas)


def discover_recursive_program(configuration: AtomicConfiguration) -> RecursiveProgram:
    planar = _try_planar(configuration)
    if planar is not None:
        return planar
    rule = discover_rule(configuration)
    if not rule.deterministic:
        return RecursiveProgram(
            "none", False, 3, 0, 0, 0, 1.0, rule.marking,
            rule.hierarchy_supports, len(configuration.positions),
            len(configuration.positions), 0, 0.0, rule.reason,
            False, False, False, rule)
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


def actions_to_at_least(configuration: AtomicConfiguration,
                        program: RecursiveProgram,
                        target_atoms: int = 1_000_000) -> tuple[int, int]:
    for actions in range(24):
        count = symbolic_count(configuration, program, actions)
        if count >= target_atoms:
            return actions, count
    raise RuntimeError("recursive program did not reach target within 24 actions")
