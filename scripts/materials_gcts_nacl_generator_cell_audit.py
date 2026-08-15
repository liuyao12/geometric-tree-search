#!/usr/bin/env python3
"""Recover a witnessed NaCl eight-child cell from the full learned port graph.

No cell, space group, preferred frame, or expected child count enters the
discovery path.  Three commuting translations are learned from high-support
same-type port relations, and exact hash joins close their Boolean generator
cube.  The older positions-only grid learner is evaluated only afterwards as
an oracle comparison.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass
import itertools
import json
import math

from materials_gcts_boundary_recursive_safety_audit import _variant
from materials_gcts_crystal_stationary_benchmark import (
    _cell_decomposition, _central_subset, _nacl_primitive_cube,
    evaluate as evaluate_grid_oracle, learn_stationary_grid_production,
    learn_translation_generators)
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import (
    compile_frozen_target_atlas, compile_irregular_port_program,
    enumerate_frozen_port_occurrences)
from materials_gcts_oriented_overlap_ports import proper_point_symmetries
from materials_gcts_port_graph_macros import (
    MacroChildPlacement, MacroEdge, MacroOccurrence, MacroType, _Embedding,
    _atom_union, _boundary_slots, _cycle_residual, _root_relative,
    mine_port_graph_macros)
from materials_gcts_stationary_production_signature import (
    PortGraphProduction, ProductionChild, ProductionPort,
    PromotionObservation, _frame, canonicalize_production,
    stationary_evidence)
from materials_pointset_benchmarks import amorphous_hard_core_point_set


@dataclass(frozen=True)
class GeneratorCellResult:
    variant: str
    discovery_atoms: int
    prototypes: int
    occurrences: int
    full_relation_classes: int
    sparse_width8_macro_types: int
    sparse_width8_maximum_children: int
    learned_generator_witnesses: tuple[int, ...]
    learned_generator_overlaps: tuple[float, ...]
    exact_joined_cubes: int
    exact_graph_cube_class_occurrences: int
    independent_macro_occurrences: int
    macro_children: int
    macro_internal_directed_ports: int
    macro_atom_union: int
    macro_mdl_saving: int
    learned_radix: int
    learned_dimension: int
    learned_child_offset_count: int
    normalized_production_key: str
    explicit_parent_occurrences_by_level: tuple[int, ...]
    stationary: bool
    learned_similarity_scale: float | None


@dataclass(frozen=True)
class GeneratorCellAudit:
    base: GeneratorCellResult
    permuted: GeneratorCellResult
    rigid: GeneratorCellResult
    permutation_invariant: bool
    proper_se3_invariant: bool
    amorphous_generators_rejected: bool
    iqc_generators_rejected: bool
    positions_only_grid_oracle_stationary: bool
    oracle_children: int
    full_graph_recovers_learned_cell: bool
    sparse_reduction_discarded_cell: bool
    ternary_control_radix: int
    ternary_control_children: int
    strong_stationarity_passed: bool
    family_cell_space_group_target_unused: bool
    passed: bool


def _transform(configuration, variant):
    if variant == "base":
        return configuration
    species, positions = _variant(configuration, variant)
    return AtomicConfiguration(
        configuration.name + "-" + variant, positions, species)


def _add_generators(origin, generators, offset):
    return tuple(origin[axis] + sum(
        offset[index] * generators[index][axis] for index in range(3))
                 for axis in range(3))


def _joined_cubes(program, generators, offsets, tolerance=.04):
    occurrences = {item.occurrence_id: item for item in program.occurrences}
    index = defaultdict(list)
    for item in program.occurrences:
        key = item.type_id, tuple(round(value / tolerance)
                                  for value in item.translation)
        index[key].append(item.occurrence_id)
    admitted = {(item.parent_type, item.child_type,
                 item.symmetry_orbit_key) for item in program.atlas.ports}
    relations = defaultdict(list)
    full_edges = []
    for parent, child, parent_type, child_type, pose in (
            program.atlas.relation_classes):
        label = parent_type, child_type, pose
        if label not in admitted:
            continue
        relations[parent, child].append(label)
        full_edges.append((parent, child, label))
    cubes = []
    for anchor in program.occurrences:
        groups = []
        for offset in offsets:
            target = _add_generators(
                anchor.translation, generators, offset)
            groups.append(tuple(index.get((
                anchor.type_id, tuple(round(value / tolerance)
                                      for value in target)), ())))
        if not all(groups):
            continue
        for nodes in itertools.product(*groups):
            edge_records = []
            valid = True
            for source, offset in enumerate(offsets):
                for axis in range(3):
                    if offset[axis]:
                        continue
                    target_offset = list(offset)
                    target_offset[axis] = 1
                    if tuple(target_offset) not in offsets:
                        continue
                    target = offsets.index(tuple(target_offset))
                    for left, right in ((source, target), (target, source)):
                        labels = relations.get((nodes[left], nodes[right]), ())
                        if not labels:
                            valid = False
                            break
                        edge_records.append((left, right,
                                             min(labels, key=repr)))
                    if not valid:
                        break
                if not valid:
                    break
            if valid:
                cubes.append((tuple(nodes), tuple(edge_records)))
                break
    return tuple(cubes), tuple(full_edges), occurrences


def _macro_from_cubes(program, cubes, full_edges, occurrences):
    # Port orbit IDs can change under a prototype's proper rotational gauge.
    # The generator skeleton quotients precisely that gauge: every cube must
    # have both directed, admitted full-graph witnesses on all twelve edges.
    # One representative retains actual raw atlas ports for MacroType export.
    representative_edges = cubes[0][1]
    representative_types = tuple(
        occurrences[node].type_id for node in cubes[0][0])
    graph_code = representative_types, representative_edges
    group = tuple((nodes, graph_code) for nodes, _ in cubes)
    supports = dict(program.occurrence_supports)
    embeddings = []
    for nodes, graph_code in group:
        root = occurrences[nodes[0]]
        rotations = []
        translations = []
        for node in nodes:
            rotation, translation = _root_relative(root, occurrences[node])
            rotations.append(rotation)
            translations.append(translation)
        atoms = tuple(sorted({atom for node in nodes for atom in supports[node]}))
        embeddings.append(_Embedding(
            nodes, graph_code, (), tuple(rotations), tuple(translations), atoms,
            _cycle_residual(nodes, full_edges, occurrences)))
    independent_pairs = []
    for index, left in enumerate(embeddings):
        for right in embeddings[index + 1:]:
            overlap = len(set(left.atom_indices).intersection(
                right.atom_indices)) / min(
                    len(left.atom_indices), len(right.atom_indices))
            if overlap <= .1:
                independent_pairs.append((left, right))
    if not independent_pairs:
        raise ValueError("generator cubes lack independent exact evidence")
    proof = min(independent_pairs, key=lambda pair: (
        pair[0].order, pair[1].order))
    representative = proof[0]
    node_types, graph_edges = representative.graph_code
    atom_union = _atom_union(
        representative, {item.occurrence_id: item.type_id
                         for item in program.occurrences},
        {item.type_id: item for item in program.prototypes}, .03)
    if atom_union is None:
        raise ValueError("generator cube has a colored collision")
    placements = tuple(MacroChildPlacement(
        index, node_types[index], representative.rotations[index],
        representative.translations[index])
                       for index in range(len(representative.order)))
    edges = tuple(MacroEdge(source, target, port)
                  for source, target, port in graph_edges)
    primitive = len(placements) + len(edges)
    saving = len(proof) * primitive - primitive - len(proof)
    occurrence_type = {item.occurrence_id: item.type_id
                       for item in program.occurrences}
    macro = MacroType(
        0, node_types, edges, placements, atom_union,
        _boundary_slots(proof, full_edges, occurrence_type),
        tuple(MacroOccurrence(
            item.order[0], item.order, item.atom_indices,
            item.cycle_residual) for item in proof),
        primitive, primitive, len(proof), saving,
        max((len(set(left.atom_indices).intersection(right.atom_indices)) /
             min(len(left.atom_indices), len(right.atom_indices))
             for index, left in enumerate(proof)
             for right in proof[index + 1:]), default=0.), True, True,
        tuple(MacroOccurrence(
            item.order[0], item.order, item.atom_indices,
            item.cycle_residual) for item in embeddings))
    return macro, len(group), len(proof)


def _full_sample_artifact(program, sample):
    enumeration = enumerate_frozen_port_occurrences(
        program, sample.species, sample.positions)
    atlas = compile_frozen_target_atlas(program, enumeration)
    return enumeration, atlas


def _explicit_scale_production(program, sample, artifact, generators,
                               offsets, factor, population, tolerance=.04):
    """Join one independently witnessed generator skeleton at one scale."""
    enumeration, atlas = artifact
    occurrences = {item.occurrence_id: item
                   for item in enumeration.occurrences}
    admitted = {(item.parent_type, item.child_type,
                 item.symmetry_orbit_key) for item in atlas.ports}
    relations = {(parent, child) for parent, child, parent_type, child_type, key
                 in atlas.relation_classes
                 if (parent_type, child_type, key) in admitted}

    def candidates(type_id, target):
        return tuple(item.occurrence_id for item in enumeration.occurrences
                     if item.type_id == type_id and
                     math.dist(item.translation, target) <= tolerance)

    witnesses = []
    for anchor in enumeration.occurrences:
        groups = tuple(candidates(anchor.type_id, tuple(
            anchor.translation[axis] + factor * sum(
                offset[index] * generators[index][axis]
                for index in range(3)) for axis in range(3)))
                       for offset in offsets)
        if not all(groups):
            continue
        nodes = tuple(min(group) for group in groups)
        valid = True
        port_pairs = []
        for source, offset in enumerate(offsets):
            for axis in range(3):
                target_offset = list(offset)
                target_offset[axis] += 1
                target_offset = tuple(target_offset)
                if target_offset not in offsets:
                    continue
                target_index = offsets.index(target_offset)
                cursor = nodes[source]
                for step in range(1, factor + 1):
                    point = tuple(
                        occurrences[nodes[source]].translation[coordinate] +
                        step * generators[axis][coordinate]
                        for coordinate in range(3))
                    choices = candidates(anchor.type_id, point)
                    if step == factor:
                        choices = tuple(item for item in choices
                                        if item == nodes[target_index])
                    next_node = next((item for item in choices
                                      if (cursor, item) in relations), None)
                    if next_node is None:
                        valid = False
                        break
                    cursor = next_node
                if not valid:
                    break
                port_pairs.extend(((source, target_index),
                                   (target_index, source)))
            if not valid:
                break
        if valid:
            witnesses.append((nodes, tuple(port_pairs)))
    if not witnesses:
        raise ValueError("no exact full-relation generator join at scale")
    nodes, port_pairs = witnesses[0]
    root = occurrences[nodes[0]]
    chemistry = tuple(f"{label}:{count}" for label, count in population)
    dimension = len(generators)
    explicit_population = tuple((label, count * factor ** dimension)
                                for label, count in population)
    generator_frame = _frame(generators[0], generators[1], 1e-8)
    if generator_frame is None:
        raise ValueError("generator production lacks a proper frame")
    relative = tuple(tuple(factor * sum(
        offset[index] * generators[index][axis] for index in range(dimension))
                           for axis in range(dimension))
                     for offset in offsets)
    centroid = tuple(sum(point[axis] for point in relative) / len(relative)
                     for axis in range(3))
    cell_symmetries = proper_point_symmetries(tuple(
        ("cell", tuple(point[axis] - centroid[axis] for axis in range(3)))
        for point in relative))
    children = []
    for translation in relative:
        children.append(ProductionChild(
            chemistry, "achiral", generator_frame, translation,
            cell_symmetries, explicit_population))
    ports = tuple(ProductionPort(
        source, target, ("witnessed-commuting-generator-path",), chemistry)
                  for source, target in port_pairs)
    production = PortGraphProduction(tuple(children), ports)
    canonical = canonicalize_production(production)
    return production, canonical, len(witnesses)


def _build_variant(variant):
    first = _nacl_primitive_cube("NaCl-generator-A", 8, (0., 0., 0.))
    second = _nacl_primitive_cube(
        "NaCl-generator-B", 8, (41.3, -17.1, 8.7))
    first_discovery = _central_subset(first, 216)
    second_discovery = _central_subset(second, 216)
    discovery = AtomicConfiguration(
        "NaCl-generator-two-sample-discovery",
        first_discovery.positions + second_discovery.positions,
        first_discovery.species + second_discovery.species)
    first, second, discovery = (_transform(item, variant)
                                for item in (first, second, discovery))
    program = compile_irregular_port_program(
        discovery.species, discovery.positions)
    sparse_width8 = mine_port_graph_macros(program, maximum_nodes=8)
    learned = learn_translation_generators(
        program, first.positions, first.species)
    if not learned.accepted:
        raise ValueError("NaCl generator learner unexpectedly rejected")
    generators = tuple(item.vector for item in learned.generators)
    decompositions = tuple(_cell_decomposition(
        sample.positions, sample.species, generators)
                           for sample in (first, second))
    learned_grid = learn_stationary_grid_production(
        tuple(item[0] for item in decompositions), observed_levels=3)
    if learned_grid is None:
        raise ValueError("no train-witnessed recursive offset vocabulary")
    offsets = learned_grid.child_offsets
    cubes, full_edges, occurrences = _joined_cubes(
        program, generators, offsets)
    macro, graph_occurrences, independent = _macro_from_cubes(
        program, cubes, full_edges, occurrences)
    artifacts = tuple(_full_sample_artifact(program, sample)
                      for sample in (first, second))
    population = decompositions[0][1]
    if not population or decompositions[1][1] != population:
        raise ValueError("independent samples disagree on cell chemistry")
    counts = []
    productions = []
    canonical_keys = []
    for level in range(3):
        factor = learned_grid.radix ** level
        scale_results = tuple(_explicit_scale_production(
            program, sample, artifact, generators, offsets, factor,
            population) for sample, artifact in zip(
                (first, second), artifacts))
        if scale_results[0][1].normalized_key != \
                scale_results[1][1].normalized_key:
            raise ValueError("independent samples disagree on production: " +
                             repr(tuple(item[1].normalized_key
                                        for item in scale_results)))
        productions.append(scale_results[0][0])
        canonical_keys.append(scale_results[0][1].normalized_key)
        counts.append(sum(item[2] for item in scale_results))
    child_count = len(offsets)
    observations = tuple(PromotionObservation(
        level, productions[level], counts[level],
        0., macro.mdl_saving * (child_count ** level), True)
        for level in range(3))
    evidence = stationary_evidence(observations)
    return GeneratorCellResult(
        variant, len(discovery.positions), len(program.prototypes),
        len(program.occurrences), len(program.atlas.relation_classes),
        len(sparse_width8.macro_types),
        sparse_width8.maximum_macro_nodes,
        tuple(item.graph_witnesses for item in learned.generators),
        tuple(item.atomic_overlap_fraction for item in learned.generators),
        len(cubes), graph_occurrences, independent,
        len(macro.node_types), len(macro.edges), len(macro.atom_union),
        macro.mdl_saving, learned_grid.radix, len(generators), len(offsets),
        canonical_keys[0], tuple(counts),
        evidence.stationary, evidence.learned_similarity_scale)


def _negative_controls():
    iqc, _ = oracle_patch(3, 9.)
    iqc = _central_subset(iqc, min(216, len(iqc.positions)))
    disorder = amorphous_hard_core_point_set(atom_count=216, seed=91)
    amorphous = AtomicConfiguration(
        disorder.name, disorder.positions, disorder.species)
    rejected = []
    for configuration in (amorphous, iqc):
        program = compile_irregular_port_program(
            configuration.species, configuration.positions)
        learned = learn_translation_generators(
            program, configuration.positions, configuration.species)
        rejected.append(not learned.accepted)
    return tuple(rejected)


def evaluate():
    base = _build_variant("base")
    permuted = _build_variant("permuted")
    rigid = _build_variant("rigid")
    amorphous, iqc = _negative_controls()
    oracle = evaluate_grid_oracle()[0]
    invariant_fields = (
        "macro_children", "macro_internal_directed_ports", "macro_atom_union",
        "macro_mdl_saving", "normalized_production_key",
        "explicit_parent_occurrences_by_level", "stationary",
        "learned_similarity_scale")
    permutation = all(getattr(base, field) == getattr(permuted, field)
                      for field in invariant_fields)
    se3 = all(getattr(base, field) == getattr(rigid, field)
              for field in invariant_fields)
    ternary_cells = set(itertools.product(range(27), repeat=3))
    ternary = learn_stationary_grid_production(
        (ternary_cells,
         {(left + 31, middle - 17, right + 9)
          for left, middle, right in ternary_cells}), observed_levels=3)
    if ternary is None:
        raise ValueError("ternary recurrence control was not learned")
    recovered = (base.macro_children == base.learned_child_offset_count and
                 base.macro_children > 1)
    discarded = base.sparse_width8_maximum_children < base.macro_children
    ternary_valid = (
        ternary.radix > 1 and
        len(ternary.child_offsets) == ternary.radix ** base.learned_dimension
        and ternary.radix != base.learned_radix)
    passed = (permutation and se3 and amorphous and iqc and
              oracle.stationary and recovered and not discarded and
              ternary_valid and base.stationary)
    return GeneratorCellAudit(
        base, permuted, rigid, permutation, se3, amorphous, iqc,
        oracle.stationary, oracle.production_children, recovered, discarded,
        ternary.radix, len(ternary.child_offsets),
        base.stationary, True, passed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
