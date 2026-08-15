#!/usr/bin/env python3
"""Clean supervised action graphs mined solely inside one IQC train crop."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from materials_gcts_batch_frontier_search import _candidate_id
from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, RadialBoundary, _SpatialSiteIndex, _placed_sites, _pose_key,
    _site_key, enumerate_frontier, fit_frozen_frontier_program)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_iqc_action_graph_corpus import (
    CorpusActionNode, CorpusPortEdge)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_oriented_overlap_ports import ClusterOccurrence
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop


TRAINING_CENTER = (-16., 0., 0.)
LOCAL_SEED_CENTERS = (
    (-16., 0., 0.), (-13.5, 1.5, 1.5), (-18.5, -1.5, 1.5),
    (-14.5, -2.5, -1.5), (-17.5, 2.5, -1.5))


@dataclass(frozen=True)
class CleanTrainingPatchGraph:
    patch_id: int
    center: tuple[float, float, float]
    nodes: tuple[CorpusActionNode, ...]
    edges: tuple[CorpusPortEdge, ...]
    accepted_per_wave: tuple[int, ...]
    seed_atoms: int
    public_domain_atoms: int
    seed_occurrences: int
    exact_actions: int
    unique_emitted_train_atoms: int


@dataclass(frozen=True)
class CleanCorpusPrototype:
    """Train-learned colored support needed to render promoted submacros."""

    cluster_type: int
    sites: tuple
    proper_symmetries: tuple


@dataclass(frozen=True)
class CleanCorpusProduction:
    """Semantic oriented port; raw production ids are not recurrence keys."""

    production_id: int
    parent_type: int
    child_type: int
    relative_rotation: tuple
    relative_translation: tuple[float, float, float]
    overlap_species: tuple
    symmetry_orbit_key: tuple[int, ...]


@dataclass(frozen=True)
class CleanTrainingActionCorpus:
    patches: tuple[CleanTrainingPatchGraph, ...]
    training_atoms: int
    frozen_prototypes: int
    frozen_productions: int
    seed_radius: float
    public_boundary_radius: float
    maximum_waves: int
    maximum_accepted_per_wave: int
    total_nodes: int
    total_exact_actions: int
    distinct_cluster_types: int
    distinct_production_types: int
    unique_train_atoms_emitted_across_patches: int
    train_atom_emission_coverage: float
    corpus_digest: str
    known_training_labels_used_for_exact_trace_selection: bool
    heldout_patch_atoms_or_labels_used: bool
    target_correctness_labels_stored: bool
    prototypes: tuple[CleanCorpusPrototype, ...]
    productions: tuple[CleanCorpusProduction, ...]
    semantic_descriptors_train_only: bool


def _execute_clean_patch(frozen, enumeration, gaps, center, target_keys,
                         *, maximum_waves=5, maximum_per_wave=40):
    seed = FrontierSeed(enumeration.occurrences, gaps)
    placed = [ClusterOccurrence(index, item.type_id, item.rotation,
                                item.translation)
              for index, item in enumerate(seed.occurrences)]
    occupied = list(_placed_sites(frozen, placed, gaps))
    occupied_index = _SpatialSiteIndex(occupied, frozen.exclusion_distance)
    existing_poses = {_pose_key(item, frozen.overlap_tolerance)
                      for item in placed}
    incoming = {}
    orbit_cache = {}
    nodes = [CorpusActionNode(
        item.occurrence_id, item.type_id, item.rotation,
        tuple(item.translation[axis] - center[axis] for axis in range(3)),
        0, 1.) for item in placed]
    edges = []
    emitted_keys = set()
    accepted_per_wave = []
    production = {item.production_id: item for item in frozen.productions}
    for wave in range(1, maximum_waves + 1):
        frontier = enumerate_frontier(
            frozen, placed, explicit_gap_sites=gaps,
            boundary=RadialBoundary(center, 7.), incoming_ports=incoming,
            _occupied_index=occupied_index, _existing_poses=existing_poses,
            _orbit_cache=orbit_cache)
        exact = tuple(candidate for candidate in frontier.candidates
                      if all(_site_key(site, frozen.overlap_tolerance)
                             in target_keys for site in
                             candidate.rendered_sites))
        exact = sorted(exact, key=lambda item: (
            -item.overlap_atoms,
            -production[item.production_id].training_observations,
            _candidate_id(item, frozen.overlap_tolerance)))
        batch_index = _SpatialSiteIndex(occupied, frozen.exclusion_distance)
        accepted = []
        for candidate in exact:
            if len(accepted) >= maximum_per_wave:
                break
            _, novel, conflict = batch_index.classify(
                candidate.rendered_sites, frozen.overlap_tolerance,
                frozen.exclusion_distance)
            if conflict or not novel:
                continue
            accepted.append((candidate, novel))
            batch_index.extend(novel)
        accepted_per_wave.append(len(accepted))
        if not accepted:
            break
        for candidate, novel in accepted:
            occurrence = ClusterOccurrence(
                len(placed), candidate.child_type,
                candidate.rotation, candidate.translation)
            placed.append(occurrence)
            existing_poses.add(_pose_key(occurrence,
                                         frozen.overlap_tolerance))
            occupied.extend(novel)
            occupied_index.extend(novel)
            incoming[occurrence.occurrence_id] = candidate.outgoing_port
            rule = production[candidate.production_id]
            nodes.append(CorpusActionNode(
                occurrence.occurrence_id, occurrence.type_id,
                occurrence.rotation,
                tuple(occurrence.translation[axis] - center[axis]
                      for axis in range(3)), wave, 1.))
            edges.append(CorpusPortEdge(
                candidate.parent_occurrence, occurrence.occurrence_id,
                candidate.production_id, rule.parent_type, rule.child_type,
                rule.port.symmetry_orbit_key))
            emitted_keys.update(_site_key(site, frozen.overlap_tolerance)
                                for site in novel)
    return tuple(nodes), tuple(edges), tuple(accepted_per_wave), emitted_keys


def _build():
    oracle, _discarded = oracle_patch_fast(9, 34.)
    training, training_ids = _crop(
        oracle, TRAINING_CENTER, 11., "IQC-clean-action-train")
    learned = compile_irregular_port_program(
        training.species, training.positions)
    frozen = fit_frozen_frontier_program(learned)
    target_keys = {_site_key(site, frozen.overlap_tolerance)
                   for site in zip(training.species, training.positions)}
    patches = []
    emitted_union = set()
    domain_ids = []
    seed_ids = []
    for patch_id, center in enumerate(LOCAL_SEED_CENTERS):
        seed_cloud, raw_seed_ids = _crop(
            oracle, center, 5., f"IQC-clean-seed-{patch_id}")
        public, raw_public_ids = _crop(
            oracle, center, 7., f"IQC-clean-public-{patch_id}")
        if not set(raw_public_ids).issubset(training_ids):
            raise AssertionError("local public domain escapes training crop")
        enumeration = enumerate_frozen_port_occurrences(
            learned, seed_cloud.species, seed_cloud.positions,
            select_greedy_cover=True)
        covered = {index for _, support in enumeration.occurrence_supports
                   for index in support}
        gaps = tuple((seed_cloud.species[index], seed_cloud.positions[index])
                     for index in range(len(seed_cloud.positions))
                     if index not in covered)
        nodes, edges, waves, emitted = _execute_clean_patch(
            frozen, enumeration, gaps, center, target_keys)
        emitted_union.update(emitted)
        patches.append(CleanTrainingPatchGraph(
            patch_id, center, nodes, edges, waves, len(seed_cloud.positions),
            len(public.positions), len(enumeration.occurrences), len(edges),
            len(emitted)))
        domain_ids.append(tuple(raw_public_ids))
        seed_ids.append(tuple(raw_seed_ids))
    payload = tuple((item.patch_id, item.nodes, item.edges,
                     item.accepted_per_wave) for item in patches)
    corpus = CleanTrainingActionCorpus(
        tuple(patches), len(training.positions), len(frozen.prototypes),
        len(frozen.productions), 5., 7., 5, 40,
        sum(len(item.nodes) for item in patches),
        sum(len(item.edges) for item in patches),
        len({node.cluster_type for item in patches for node in item.nodes}),
        len({edge.production_id for item in patches for edge in item.edges}),
        len(emitted_union), len(emitted_union) / len(training.positions),
        hashlib.sha256(repr(payload).encode()).hexdigest(), True, False, False,
        tuple(CleanCorpusPrototype(
            item.type_id, item.sites, item.proper_symmetries)
              for item in frozen.prototypes),
        tuple(CleanCorpusProduction(
            item.production_id, item.parent_type, item.child_type,
            item.port.relative_rotation, item.port.relative_translation,
            item.port.overlap_species, item.port.symmetry_orbit_key)
              for item in frozen.productions), True)
    return corpus, tuple(seed_ids), tuple(domain_ids), tuple(training_ids)


def build_clean_training_action_corpus():
    """Public deterministic clean corpus API for submacro mining."""
    corpus, _, _, _ = _build()
    return corpus


def clean_submacro_edge_records(corpus):
    return tuple((patch.patch_id, edge.parent_node, edge.child_node,
                  edge.parent_type, edge.child_type,
                  edge.symmetry_orbit_key)
                 for patch in corpus.patches for edge in patch.edges)
