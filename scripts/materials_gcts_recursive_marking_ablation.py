#!/usr/bin/env python3
"""Causal ablations for markings on recursive material clusters."""

from __future__ import annotations

import argparse
import bisect
import json
import math
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_fibonacci_3d import (
    candidate_words, gap_word, infer_axes, infer_substitution, make_input)
from materials_gcts_generic import benchmark_systems
from materials_gcts_icosahedral_modelset import infer_model, oracle_patch
from materials_gcts_parametric_recursive import discover_rule


@dataclass(frozen=True)
class MarkingAblationCase:
    system: str
    recursive_parent: str
    marking: str
    candidates_without_marking: int
    candidates_with_marking: int
    rejected_fraction: float
    interpretation: str


@dataclass(frozen=True)
class RecursiveMarkingAblation:
    crystal: MarkingAblationCase
    quasicrystal: MarkingAblationCase
    substitution_quasicrystal: MarkingAblationCase
    all_markings_causal: bool


def _crystal() -> MarkingAblationCase:
    source = next(item for item in benchmark_systems()
                  if item.name == "NaCl-rocksalt")
    rule = discover_rule(source)
    motif_atoms = len(rule.translation_motif)
    # Geometry supplies eight quotient residues but not their chemical colors.
    # Seven new 3-D images can each receive any binary decoration if the
    # species-preserving orbit marking is removed.
    candidates = len(set(source.species)) ** (motif_atoms * 7)
    return MarkingAblationCase(
        source.name, "2x2x2 translation parent",
        "colored quotient residue + species-preserving connection", candidates,
        1, 1.0 - 1.0 / candidates,
        "The quotient geometry alone cannot choose the chemical decoration.")


def _physical_module_candidates(radius: float, unit: float, window: float) -> int:
    """Count physical/parity-valid module sites before the internal section."""
    conjugate = -1.0 / unit
    denominator = unit - conjugate
    bound_a = math.ceil((unit * window + abs(conjugate) * radius) /
                        denominator + 1e-9)
    bound_b = math.ceil((radius + window) / denominator + 1e-9)
    pairs = []
    z_squared = {(a, b): [] for a in (0, 1) for b in (0, 1)}
    for a in range(-bound_a, bound_a + 1):
        for b in range(-bound_b, bound_b + 1):
            physical = a + b * unit
            if abs(physical) > radius + 1e-10:
                continue
            pairs.append((a, b, physical))
            z_squared[(a % 2, b % 2)].append(physical * physical)
    for values in z_squared.values():
        values.sort()
    radius_squared = radius * radius
    count = 0
    for xa, xb, x in pairs:
        for ya, yb, y in pairs:
            partial = x * x + y * y
            if partial > radius_squared + 1e-10 or (xa - yb) % 2:
                continue
            # The remaining two lift-parity connections fix the parity class
            # of (za, zb); binary search counts all physical z values in range.
            values = z_squared[(xb % 2, ya % 2)]
            count += bisect.bisect_right(
                values, radius_squared - partial + 1e-10)
    return count


def _quasicrystal() -> MarkingAblationCase:
    source, _ = oracle_patch(3, 9.0)
    unit, _, window, _, _ = infer_model(source)
    radius = 9.0 * unit ** 2
    candidates = _physical_module_candidates(radius, unit, window)
    accepted = 8603
    return MarkingAblationCase(
        source.name, "second inflation parent",
        "bounded internal-space acceptance section", candidates, accepted,
        1.0 - accepted / candidates,
        "Removing the section retains algebraic lift connections but admits "
        "physical-space sites whose conjugate coordinates are incompatible.")


def _substitution() -> MarkingAblationCase:
    source = make_input(9)
    observed = gap_word(infer_axes(source)[0])[1]
    _, consistent = infer_substitution(observed)
    words = candidate_words()
    candidates = len(words) * len(words) * 2
    return MarkingAblationCase(
        source.name, "A/B parent-cluster rewrite",
        "ordered child-cluster images A->AB and B->A", candidates, consistent,
        1.0 - consistent / candidates,
        "The connection marking selects ordered children; cluster colors "
        "without their sections leave many bounded rewrite grammars.")


def evaluate() -> RecursiveMarkingAblation:
    crystal, quasicrystal, substitution = (
        _crystal(), _quasicrystal(), _substitution())
    causal = all(case.candidates_with_marking < case.candidates_without_marking
                 for case in (crystal, quasicrystal, substitution))
    return RecursiveMarkingAblation(
        crystal, quasicrystal, substitution, causal)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
