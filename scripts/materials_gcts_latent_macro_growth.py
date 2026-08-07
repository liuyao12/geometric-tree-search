#!/usr/bin/env python3
"""Latent-directed level-3 DAG covering for the IQC benchmark."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Dict, Tuple

import materials_gcts_blind_continuation as blind
import materials_gcts_dag_blind_frontier as frontier
import materials_gcts_transform_dag as dag
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_icosahedral_modelset import (
    infer_model, learned_species, lift_point, project, star_vectors,
    vector_norm)

Vector = Tuple[float, float, float]


@dataclass(frozen=True)
class LatentMacroGrowthResult:
    training_atoms: int
    initial_state_atoms: int
    latent_target_atoms: int
    oracle_atoms: int
    latent_target_precision: float
    latent_target_recall: float
    mapped_level1_centers: int
    mapped_level2_centers: int
    mapped_level3_centers: int
    level3_actions: int
    accepted_macro_actions: int
    largest_action_gain: int
    covered_new_atoms: int
    covered_new_correct: int
    covered_precision: float
    hidden_recall: float
    uncovered_latent_atoms: int


def _radial_signature(
    center: int, labels, positions, neighbors,
) -> Tuple[str, Tuple[Tuple[str, int], ...]]:
    return (repr(labels[center]), tuple(sorted(
        (repr(labels[index]), round(dag._norm(dag._subtract(
            positions[index], positions[center])) / 1e-5))
        for index in neighbors if index != center)))


def _spatial_neighbors(positions, radius: float):
    cell_size = radius
    buckets = defaultdict(list)
    for index, point in enumerate(positions):
        buckets[blind._cell_key(point, cell_size)].append(index)
    result = []
    for point in positions:
        center = blind._cell_key(point, cell_size)
        neighbors = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for index in buckets.get((
                            center[0] + dx, center[1] + dy,
                            center[2] + dz), ()):
                        if dag._norm(dag._subtract(
                                positions[index], point)) <= radius + 1e-6:
                            neighbors.append(index)
        result.append(tuple(neighbors))
    return tuple(result)


def _radial_hierarchy_labels(
    training, target, training_model,
) -> Tuple[Tuple[Tuple[int, ...], ...], Tuple[int, ...]]:
    radii, training_levels, training_labels = training_model
    mapped_levels = []
    counts = []
    for level, radius in enumerate(radii):
        # Classify every spatial scale directly from the colored atoms.  Using
        # the previous predicted label as the sole input makes one unknown
        # boundary corona cascade into unknown labels at every coarser level.
        # The learned type IDs still come from the recursive hierarchy; this
        # descriptor is only its robust, boundary-tolerant lookup key.
        training_input = training.species
        training_neighbors = _spatial_neighbors(
            training.positions, radius)
        signature_types = defaultdict(set)
        for cluster_type in training_levels[level].cluster_types:
            center = cluster_type.representative_center
            signature_types[_radial_signature(
                center, training_input, training.positions,
                training_neighbors[center])].add(cluster_type.type_id)
        target_neighbors = _spatial_neighbors(target.positions, radius)
        mapped = []
        for center in range(len(target.positions)):
            types = signature_types.get(_radial_signature(
                center, target.species, target.positions,
                target_neighbors[center]), ())
            mapped.append(next(iter(types)) if len(types) == 1 else -1)
        mapped_levels.append(tuple(mapped))
        counts.append(sum(value >= 0 for value in mapped))
    return tuple(mapped_levels), tuple(counts)


def _module_hierarchy_labels(training, target, training_model):
    """Evaluate learned cluster labels as sections of internal space.

    This is the quasicrystal analogue of a crystal's unit-cell coordinate.
    The six-dimensional lift is learned from the training cloud, and a target
    center inherits the label of the closest sampled marking section.  No
    held-out/oracle labels enter this lookup.
    """
    unit, lifted, _, _, residual = infer_model(training)
    if residual > 1e-5:
        raise ValueError("module hierarchy requires an active module marking")
    internal_vectors = star_vectors(-1.0 / unit)
    training_internal = []
    for point in training.positions:
        lift, lift_residual = lift_point(point, unit)
        if lift_residual > 1e-5 or lift not in lifted:
            raise ValueError("could not lift a training center")
        training_internal.append(project(lift, internal_vectors))
    target_internal = []
    for point in target.positions:
        lift, lift_residual = lift_point(point, unit)
        if lift_residual > 1e-5:
            raise ValueError("could not lift a latent center")
        target_internal.append(project(lift, internal_vectors))
    mapped_levels = []
    for labels in training_model[2]:
        mapped = []
        for coordinate in target_internal:
            nearest = min(range(len(training_internal)), key=lambda index:
                          dag._norm(dag._subtract(
                              coordinate, training_internal[index])))
            mapped.append(labels[nearest])
        mapped_levels.append(tuple(mapped))
    return tuple(mapped_levels), tuple(len(target.positions)
                                      for _ in mapped_levels)


def _module_type_rankings(training, target, training_model, level: int):
    """Rank learned parent sections by internal-space marking distance."""
    unit, lifted, _, _, residual = infer_model(training)
    if residual > 1e-5:
        raise ValueError("module rankings require an active module marking")
    internal_vectors = star_vectors(-1.0 / unit)
    labels = training_model[2][level - 1]
    samples = defaultdict(list)
    for point, type_id in zip(training.positions, labels):
        lift, lift_residual = lift_point(point, unit)
        if lift_residual > 1e-5 or lift not in lifted:
            raise ValueError("could not lift a training marking sample")
        samples[type_id].append(project(lift, internal_vectors))
    rankings = []
    for point in target.positions:
        lift, lift_residual = lift_point(point, unit)
        if lift_residual > 1e-5:
            raise ValueError("could not lift a latent marking sample")
        coordinate = project(lift, internal_vectors)
        rankings.append(tuple(sorted(samples, key=lambda type_id: min(
            dag._norm(dag._subtract(coordinate, sample))
            for sample in samples[type_id]))))
    return tuple(rankings)


def _latent_atoms(
    training: AtomicConfiguration,
    physical_radius: float,
    maximum_residual: float = 1e-5,
):
    robust = maximum_residual > 1e-5
    unit, lifted, window, thresholds, residual = infer_model(
        training,
        coefficient_bound=8 if robust else 16,
        complexity_penalty=1e-3 if robust else 1e-4)
    if residual > maximum_residual:
        raise ValueError("training cloud has no active low-residual module")
    conjugate = -1.0 / unit
    internal_vectors = star_vectors(conjugate)
    radii_by_species: Dict[str, list[float]] = {}
    for lift, chemical in lifted.items():
        radii_by_species.setdefault(chemical, []).append(
            vector_norm(project(lift, internal_vectors)))
    ordered_species = tuple(sorted(
        radii_by_species,
        key=lambda chemical: (
            sum(radii_by_species[chemical]) /
            len(radii_by_species[chemical]))))
    # Write every Cartesian coordinate as a + b*unit.  Its algebraic
    # conjugate a + b*conjugate is the matching internal coordinate.  This
    # reduces a brute-force six-dimensional coefficient box to three products
    # of a compact one-coordinate section, with the lift parity constraints
    # enforced before projection.
    denominator = unit - conjugate
    bound_a = math.ceil((unit * window + abs(conjugate) * physical_radius) /
                        denominator + 1e-9)
    bound_b = math.ceil((physical_radius + window) / denominator + 1e-9)
    coordinate_pairs = []
    for a in range(-bound_a, bound_a + 1):
        for b in range(-bound_b, bound_b + 1):
            physical = a + b * unit
            internal = a + b * conjugate
            if (abs(physical) <= physical_radius + 1e-10 and
                    abs(internal) <= window + 1e-10):
                coordinate_pairs.append((a, b, physical, internal))
    radius_squared = physical_radius * physical_radius
    window_squared = window * window
    for xa, xb, x, x_internal in coordinate_pairs:
        for ya, yb, y, y_internal in coordinate_pairs:
            if x * x + y * y > radius_squared + 1e-10:
                continue
            if x_internal * x_internal + y_internal * y_internal > (
                    window_squared + 1e-10):
                continue
            if (xa - yb) % 2:
                continue
            for za, zb, z, z_internal in coordinate_pairs:
                if ((ya - zb) % 2 or (za - xb) % 2 or
                        x * x + y * y + z * z > radius_squared + 1e-10 or
                        x_internal * x_internal +
                        y_internal * y_internal +
                        z_internal * z_internal > window_squared + 1e-10):
                    continue
                physical = (x, y, z)
                internal_radius = math.sqrt(
                    x_internal * x_internal +
                    y_internal * y_internal +
                    z_internal * z_internal)
                chemical = learned_species(
                    internal_radius, ordered_species, thresholds)
                yield physical, chemical


def _latent_patch(
    training: AtomicConfiguration,
    physical_radius: float,
    maximum_residual: float = 1e-5,
) -> AtomicConfiguration:
    atoms = {}
    for physical, chemical in _latent_atoms(
            training, physical_radius, maximum_residual):
        atoms[(blind._site_key(physical), chemical)] = physical
    return AtomicConfiguration(
        "learned-latent-IQC", tuple(atoms.values()),
        tuple(site[1] for site in atoms), None, False,
        "Generated only from the module inferred from the training cloud.")


def _latent_atom_count(
    training: AtomicConfiguration,
    physical_radius: float,
    maximum_residual: float = 1e-5,
) -> int:
    return sum(1 for _ in _latent_atoms(
        training, physical_radius, maximum_residual))


def evaluate() -> LatentMacroGrowthResult:
    from materials_gcts_icosahedral_modelset import oracle_patch

    training, _ = oracle_patch(3, 9.0)
    oracle, _ = oracle_patch(4, 15.0)
    latent = _latent_patch(training, 15.0)
    state, _ = frontier._three_wave_state(training, oracle)
    training_model = dag._learn_levels(
        training.positions, training.species, 3, 2.2)
    _, levels = dag.build_transform_dag(
        training.name, training.positions, training.species,
        prelearned=training_model)
    mapped_levels, mapped_counts = _module_hierarchy_labels(
        training, latent, training_model)

    latent_set = {(blind._site_key(point), chemical)
                  for point, chemical in zip(
                      latent.positions, latent.species)}
    oracle_set = {(blind._site_key(point), chemical)
                  for point, chemical in zip(
                      oracle.positions, oracle.species)}
    current = {(key, atom.species) for key, atom in state.items()}
    candidate_sets = []
    expansion_cache = {
        node.type_id: dag.expand_node(levels, 3, node.type_id)
        for node in levels[2]}
    radii, learned_levels, training_labels = training_model
    rotations = dag._occurrence_rotations(
        3, learned_levels[2], training_labels[1], training.positions)
    orientation_atlas = defaultdict(dict)
    for cluster_type in learned_levels[2].cluster_types:
        for occurrence in cluster_type.occurrences:
            rotation = rotations[(cluster_type.type_id,
                                  occurrence.center_index)]
            orientation_atlas[cluster_type.type_id][
                frontier._rotation_key(rotation)] = rotation
    type_rankings = _module_type_rankings(
        training, latent, training_model, 3)
    oriented_expansions = defaultdict(list)
    for type_id, orientations in orientation_atlas.items():
        for rotation in orientations.values():
            expansion = tuple(sorted(
                ((chemical, dag._matvec(rotation, offset))
                 for chemical, offset in expansion_cache[type_id]),
                key=lambda item: dag._norm(item[1]), reverse=True))
            oriented_expansions[type_id].append(expansion)
    unique_candidates = set()
    for center_index, ranking in enumerate(type_rankings):
        center = latent.positions[center_index]
        # A marking section is a proposal ranking, not an irreversible class.
        # Keep the full ranking in this diagnostic.  Prefix-width ablations
        # quantify how aggressively the learned marking may safely prune it.
        for type_id in ranking:
            for expansion in oriented_expansions[type_id]:
                sites = []
                valid = True
                for chemical, offset in expansion:
                    point = dag._add(center, offset)
                    if dag._norm(point) > 15.0 + 1e-5:
                        continue
                    site = (blind._site_key(point), chemical)
                    if site not in latent_set:
                        valid = False
                        break
                    sites.append(site)
                if valid and sites:
                    unique_candidates.add(frozenset(sites))
    candidate_sets.extend(unique_candidates)

    covered = set(current & latent_set)
    accepted = 0
    largest_gain = 0
    remaining = list(candidate_sets)
    while remaining:
        best = max(remaining, key=lambda sites: len(sites - covered))
        gain = len(best - covered)
        if gain <= 0:
            break
        covered.update(best)
        accepted += 1
        largest_gain = max(largest_gain, gain)
        remaining.remove(best)
    covered_new = covered - current
    hidden = len(oracle_set) - len(training.positions)
    latent_correct = len(latent_set & oracle_set)
    return LatentMacroGrowthResult(
        len(training.positions), len(state), len(latent_set), len(oracle_set),
        latent_correct / len(latent_set),
        latent_correct / len(oracle_set),
        mapped_counts[0], mapped_counts[1], mapped_counts[2],
        len(candidate_sets), accepted, largest_gain,
        len(covered_new), len(covered_new & oracle_set),
        len(covered_new & oracle_set) / max(1, len(covered_new)),
        (len((covered & oracle_set)) - len(training.positions)) / hidden,
        len(latent_set - covered))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
