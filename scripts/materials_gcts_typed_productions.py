#!/usr/bin/env python3
"""Finite typed transform productions learned from colored point sets.

This is the common recursive layer between geometric rule discovery and
growth.  A production says that one typed parent is covered by typed children
at discrete local addresses.  Its ``section_mark`` is a bounded connection
label, not an energy or physical potential.  Once productions are induced,
the same counter rewrite evaluates crystals and substitution quasicrystals;
no family branch remains in the recursive executor.

The current observation adapters cover translation quotients and finite
substitution products.  Icosahedral internal-space inflation is deliberately
reported as unsupported until its continuous section can be compiled into a
finite typed graph.
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable, Tuple

from materials_gcts_fibonacci_3d import Substitution, generate
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_parametric_recursive import (
    ParametricRecursiveRule, discover_rule)


@dataclass(frozen=True, order=True)
class TypedChild:
    child_type: str
    address: Tuple[int, ...]
    section_mark: Tuple[str, ...]


@dataclass(frozen=True)
class TypedProduction:
    parent_type: str
    children: Tuple[TypedChild, ...]
    evidence_occurrences: int


@dataclass(frozen=True)
class TypedTransformProgram:
    type_names: Tuple[str, ...]
    atomic_weights: Tuple[int, ...]
    productions: Tuple[TypedProduction, ...]
    root_counts: Tuple[int, ...]
    deterministic: bool
    observation_kind: str
    selection_reason: str
    family_label_used: bool
    physical_potential_used: bool


def _boundary_section(address: Tuple[int, ...], extents: Tuple[int, ...]
                      ) -> Tuple[str, ...]:
    marks = []
    for axis, (index, extent) in enumerate(zip(address, extents)):
        if index == 0:
            marks.append(f"{axis}-")
        if index == extent - 1:
            marks.append(f"{axis}+")
    return tuple(marks)


def _validated_program(
    types: Iterable[str], weights: dict[str, int],
    productions: Iterable[TypedProduction], root: Counter[str],
    observation_kind: str, reason: str,
) -> TypedTransformProgram:
    names = tuple(sorted(types))
    ordered = tuple(sorted(productions, key=lambda item: item.parent_type))
    if len({item.parent_type for item in ordered}) != len(ordered):
        raise ValueError("conflicting productions for one parent type")
    production_types = {item.parent_type for item in ordered}
    if production_types != set(names):
        raise ValueError("every admitted type must have exactly one production")
    for production in ordered:
        if not production.children or production.evidence_occurrences < 1:
            raise ValueError("a production needs children and observed evidence")
        if any(child.child_type not in production_types
               for child in production.children):
            raise ValueError("production refers to an unknown child type")
        if len({child.address for child in production.children}) != len(
                production.children):
            raise ValueError("child addresses must be unique within a parent")
    if any(root[name] < 0 or weights[name] < 1 for name in names):
        raise ValueError("root counts and atomic weights must be nonnegative")
    return TypedTransformProgram(
        names, tuple(weights[name] for name in names), ordered,
        tuple(root[name] for name in names), True, observation_kind, reason,
        False, False)


def _translation_observation(
    configuration: AtomicConfiguration, rule: ParametricRecursiveRule,
) -> TypedTransformProgram | None:
    if (rule.translation_basis is None or not rule.translation_motif or
            rule.substitution_images is not None):
        return None
    motif_atoms = len(rule.translation_motif)
    if len(configuration.positions) % motif_atoms:
        return None
    cells = len(configuration.positions) // motif_atoms
    children = tuple(
        TypedChild("cell", address, _boundary_section(address, (2, 2, 2)))
        for address in itertools.product(range(2), repeat=3))
    return _validated_program(
        ("cell",), {"cell": motif_atoms},
        (TypedProduction("cell", children, max(2, cells)),),
        Counter({"cell": cells}), "translation residue observations",
        "one recurring quotient type and eight learned local addresses")


def _product_substitution_observation(
    configuration: AtomicConfiguration, rule: ParametricRecursiveRule,
) -> TypedTransformProgram | None:
    if (rule.substitution_images is None or rule.input_side is None or
            rule.translation_basis is not None):
        return None
    image_a, image_b, seed = rule.substitution_images
    substitution = Substitution(image_a, image_b, seed)
    alphabet = tuple(sorted(set(image_a + image_b)))
    if not alphabet or any(not substitution.image(symbol) for symbol in alphabet):
        return None
    type_names = tuple("".join(symbols)
                       for symbols in itertools.product(alphabet, repeat=3))
    word = generate(substitution, rule.input_side)
    root = Counter("".join(symbols)
                   for symbols in itertools.product(word, repeat=3))
    productions = []
    evidence = Counter(word)
    for parent in type_names:
        images = tuple(substitution.image(symbol) for symbol in parent)
        extents = tuple(len(image) for image in images)
        children = []
        for address in itertools.product(*(range(extent)
                                           for extent in extents)):
            child_type = "".join(images[axis][address[axis]]
                                 for axis in range(3))
            children.append(TypedChild(
                child_type, tuple(address),
                _boundary_section(tuple(address), extents)))
        occurrences = min(evidence[symbol] for symbol in parent)
        productions.append(TypedProduction(
            parent, tuple(children), max(1, occurrences)))
    return _validated_program(
        type_names, {name: 1 for name in type_names}, productions, root,
        "bounded gap-word observations",
        "Cartesian products of two learned gap-cluster productions")


def induce_typed_transform_program(
    configuration: AtomicConfiguration,
    rule: ParametricRecursiveRule | None = None,
) -> TypedTransformProgram:
    """Compile geometric evidence without consulting ``rule.family``."""
    learned = discover_rule(configuration) if rule is None else rule
    if not learned.deterministic:
        return TypedTransformProgram(
            (), (), (), (), False, "none", learned.reason,
            False, False)
    candidates = tuple(candidate for candidate in (
        _translation_observation(configuration, learned),
        _product_substitution_observation(configuration, learned),
    ) if candidate is not None)
    if len(candidates) != 1:
        return TypedTransformProgram(
            (), (), (), (), False, "none",
            ("no unambiguous finite typed production adapter" if not candidates
             else "ambiguous finite typed production evidence"),
            False, False)
    return candidates[0]


def expand_type_counts(program: TypedTransformProgram, actions: int
                       ) -> Tuple[int, ...]:
    if actions < 0:
        raise ValueError("actions must be nonnegative")
    if not program.deterministic:
        raise ValueError("cannot expand a rejected typed program")
    counts = Counter(dict(zip(program.type_names, program.root_counts)))
    productions = {item.parent_type: item for item in program.productions}
    for _ in range(actions):
        grown: Counter[str] = Counter()
        for parent, count in counts.items():
            for child in productions[parent].children:
                grown[child.child_type] += count
        counts = grown
    return tuple(counts[name] for name in program.type_names)


def symbolic_atom_count(program: TypedTransformProgram, actions: int) -> int:
    counts = expand_type_counts(program, actions)
    return sum(count * weight for count, weight in zip(
        counts, program.atomic_weights))


def actions_to_at_least(program: TypedTransformProgram,
                        target_atoms: int = 1_000_000) -> Tuple[int, int]:
    for actions in range(32):
        count = symbolic_atom_count(program, actions)
        if count >= target_atoms:
            return actions, count
    raise RuntimeError("typed program did not reach the requested size")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    from materials_gcts_fibonacci_3d import make_input
    from materials_gcts_generic import benchmark_systems
    samples = (
        next(item for item in benchmark_systems()
             if item.name == "NaCl-rocksalt"),
        make_input(9),
    )
    result = tuple(induce_typed_transform_program(item) for item in samples)
    print(json.dumps(tuple(asdict(item) for item in result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
