#!/usr/bin/env python3
"""Overlap-CSP reconstruction with geometry-first decoration alternatives."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass

from materials_gcts_geometry_decoration_vocabulary_benchmark import (
    POSE_TOLERANCE, _decorations, _site_permutation)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_oriented_overlap_ports import matvec
from materials_gcts_recurrent_macro_execution_benchmark import (
    compile_disjoint_iqc_execution_fixture)


@dataclass(frozen=True)
class DecorationCoverSolverAudit:
    training_atoms: int
    evaluation_atoms: int
    seed_atoms_with_known_species: int
    outer_atoms_species_hidden_from_solver: int
    geometry_types: int
    train_decoration_alternatives: int
    frozen_candidate_occurrences: int
    retained_geometry_covered_atoms: int
    initial_decoration_states: int
    seed_inconsistent_states_removed: int
    seed_rejected_occurrences: int
    propagation_rounds: int
    propagation_states_removed: int
    optional_occurrences_rejected_by_constraints: int
    uniquely_inferred_outer_atoms: int
    correct_inferred_outer_atoms: int
    wrong_inferred_outer_atoms: int
    inferred_precision: float
    inferred_outer_recall: float
    ambiguous_outer_atoms: int
    geometry_uncovered_outer_atoms: int
    outer_species_used_by_solver: bool
    target_positions_used_for_reencoding: bool
    autonomous_growth_claimed: bool
    overlap_constraints_improve_seed_only: bool
    benchmark_passed: bool
    limitation: str


def _add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def _local_atoms(prototype, occurrence, support, positions):
    available = set(support)
    result = []
    for _dummy, local in prototype.sites:
        world = _add(matvec(occurrence.rotation, local),
                     occurrence.translation)
        distance, atom = min((math.dist(world, positions[index]), index)
                             for index in available)
        if distance > POSE_TOLERANCE:
            raise AssertionError("geometry occurrence does not render support")
        available.remove(atom)
        result.append(atom)
    return tuple(result)


def _domain(prototype, local_atoms, alternatives):
    points = tuple(point for _dummy, point in prototype.sites)
    assignments = set()
    for decoration in alternatives:
        for symmetry in prototype.proper_symmetries:
            permutation = _site_permutation(
                points, symmetry, POSE_TOLERANCE)
            placed = [None] * len(decoration)
            for source, target in enumerate(permutation):
                placed[target] = decoration[source]
            assignments.add(tuple(placed))
    return tuple(sorted(assignments))


def _solve(positions, seed_species, occurrences, supports, prototypes,
           alternatives):
    """Propagate forced decorations through an optional overlap cover.

    Occurrences are proposals, not mandatory constraints.  A proposal becomes
    informative only after it overlaps an already labelled atom.  If its
    remaining train-observed decorations unanimously label another atom, that
    label is a forced move.  Conflicting proposals do not get to vote: the atom
    remains unresolved until every currently forced proposal agrees.

    No outer species argument exists; constraints see geometry only.
    """
    domains = {}
    local_atoms = {}
    initial = seed_removed = seed_rejected = 0
    for occurrence in occurrences:
        atoms = _local_atoms(
            prototypes[occurrence.type_id], occurrence,
            supports[occurrence.occurrence_id], positions)
        domain = _domain(prototypes[occurrence.type_id], atoms,
                         alternatives[occurrence.type_id])
        initial += len(domain)
        filtered = tuple(assignment for assignment in domain
                         if all(atom not in seed_species or
                                assignment[index] == seed_species[atom]
                                for index, atom in enumerate(atoms)))
        seed_removed += len(domain) - len(filtered)
        if not filtered:
            seed_rejected += 1
            continue
        domains[occurrence.occurrence_id] = list(filtered)
        local_atoms[occurrence.occurrence_id] = atoms
    known = dict(seed_species)
    rounds = removed = emptied = 0
    while True:
        rounds += 1
        changed = 0
        dropped = []
        for occurrence_id, domain in tuple(domains.items()):
            atoms = local_atoms[occurrence_id]
            kept = [assignment for assignment in domain
                    if all(atom not in known or
                           assignment[index] == known[atom]
                           for index, atom in enumerate(atoms))]
            changed += len(domain) - len(kept)
            if kept:
                domains[occurrence_id] = kept
            else:
                dropped.append(occurrence_id)
        for occurrence_id in dropped:
            domains.pop(occurrence_id)
            local_atoms.pop(occurrence_id)
        emptied += len(dropped)
        removed += changed

        proposals = defaultdict(list)
        for occurrence_id, domain in domains.items():
            atoms = local_atoms[occurrence_id]
            # This is a connection rule: an isolated occurrence cannot invent
            # a decoration merely because one alternative is globally common.
            if not any(atom in known for atom in atoms):
                continue
            for local_index, atom in enumerate(atoms):
                if atom in known:
                    continue
                possible = {assignment[local_index] for assignment in domain}
                if len(possible) == 1:
                    proposals[atom].append(next(iter(possible)))
        forced = {
            atom: labels[0]
            for atom, labels in proposals.items()
            if len(set(labels)) == 1
        }
        if not forced:
            break
        known.update(forced)

    membership = defaultdict(list)
    for occurrence_id, atoms in local_atoms.items():
        for local_index, atom in enumerate(atoms):
            membership[atom].append((occurrence_id, local_index))
    inferred = {atom: species for atom, species in known.items()
                if atom not in seed_species}
    return (domains, inferred, initial, seed_removed, seed_rejected, rounds,
            removed, emptied, membership)


def evaluate():
    fixture, open_target = compile_disjoint_iqc_execution_fixture()
    train_species = tuple(species for species, _point in fixture.training_sites)
    train_positions = tuple(point for _species, point in fixture.training_sites)
    geometry = compile_irregular_port_program(
        tuple("*" for _ in train_positions), train_positions)
    train_decorations = _decorations(
        geometry, train_species, train_positions, geometry.occurrences,
        geometry.occurrence_supports)
    alternatives = defaultdict(set)
    for type_id, decoration in train_decorations:
        alternatives[type_id].add(decoration)
    alternatives = {key: tuple(sorted(value))
                    for key, value in alternatives.items()}

    # Positions are supplied for this reconstruction test. Only the inner
    # radius-seven species labels cross into the solver payload.
    target = open_target()
    seed_species = {
        index: repr(target.species[index])
        for index, point in enumerate(target.positions)
        if math.dist(point, fixture.boundary.origin) <= 7. + 1e-10}
    enumeration = enumerate_frozen_port_occurrences(
        geometry, tuple("*" for _ in target.positions), target.positions)
    supports = dict(enumeration.occurrence_supports)
    prototypes = {item.type_id: item for item in geometry.prototypes}
    (domains, inferred, initial, seed_removed, seed_rejected, rounds, removed,
     emptied, membership) = \
        _solve(target.positions, seed_species, enumeration.occurrences,
               supports, prototypes, alternatives)

    outer = set(range(len(target.positions))) - set(seed_species)
    inferred_outer = {atom: species for atom, species in inferred.items()
                      if atom in outer}
    correct = sum(species == repr(target.species[atom])
                  for atom, species in inferred_outer.items())
    wrong = len(inferred_outer) - correct
    covered = set(membership)
    ambiguous = len((outer & covered) - set(inferred_outer))
    uncovered = len(outer - covered)
    precision = correct / max(1, len(inferred_outer))
    recall = correct / max(1, len(outer))
    improves = bool(inferred_outer) and precision > 0.
    gate = precision >= .99 and recall >= .9
    return DecorationCoverSolverAudit(
        len(train_positions), len(target.positions), len(seed_species),
        len(outer), len(geometry.prototypes),
        sum(map(len, alternatives.values())), len(enumeration.occurrences),
        len(covered), initial, seed_removed, seed_rejected, rounds, removed,
        emptied,
        len(inferred_outer), correct, wrong, precision, recall, ambiguous,
        uncovered, False, True, False, improves, gate,
        "This is a species reconstruction/covering gate on supplied heldout "
        "positions, not autonomous coordinate growth. Every decoration is "
        "train-observed and every inference follows seed labels plus exact "
        "cluster-overlap equality. A growth claim additionally needs the "
        "geometry frontier to be emitted target-blind.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
