#!/usr/bin/env python3
"""Target-free multi-patch action-graph corpus for recurrence mining.

Corpus records contain only local symbolic cluster poses and frozen port graph
edges.  No target sites, correctness labels, family metadata, or oracle lifts
are serialised.  A separate audit may score already-frozen executions.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from materials_gcts_batch_frontier_search import run_batch_frontier_search
from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, RadialBoundary, fit_frozen_frontier_program)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop


TRAINING_CENTER = (-16., 0., 0.)
PATCH_CENTERS = (
    (8., -12., -12.), (8., -12., 12.), (16., 8., -4.),
    (-4., 20., 0.), (0., 8., -20.), (0., 8., 20.))


@dataclass(frozen=True)
class CorpusActionNode:
    node_id: int
    cluster_type: int
    rotation: tuple[tuple[float, float, float], ...]
    local_translation: tuple[float, float, float]
    wave: int
    normalized_support: float


@dataclass(frozen=True)
class CorpusPortEdge:
    parent_node: int
    child_node: int
    production_id: int
    parent_type: int
    child_type: int
    symmetry_orbit_key: tuple[int, ...]


@dataclass(frozen=True)
class ActionGraphPatch:
    patch_id: int
    nodes: tuple[CorpusActionNode, ...]
    edges: tuple[CorpusPortEdge, ...]
    accepted_per_wave: tuple[int, ...]
    seed_nodes: int
    action_nodes: int
    production_types: int


@dataclass(frozen=True)
class IQCActionGraphCorpus:
    patches: tuple[ActionGraphPatch, ...]
    training_atoms: int
    frozen_prototypes: int
    frozen_productions: int
    threshold_ratio: float
    maximum_waves: int
    maximum_accepted_per_wave: int
    public_boundary_radius: float
    total_nodes: int
    total_actions: int
    distinct_cluster_types: int
    distinct_production_types: int
    corpus_digest: str
    target_labels_stored: bool
    target_used_during_execution: bool
    family_phi_cell_stored: bool


def _patch_record(patch_id, center, result, frozen):
    nodes = tuple(CorpusActionNode(
        item.node_id, item.cluster_type, item.rotation,
        tuple(item.translation[axis] - center[axis] for axis in range(3)),
        item.wave, item.normalized_support) for item in result.symbolic_nodes)
    production = {item.production_id: item for item in frozen.productions}
    edges = []
    for item in result.symbolic_nodes:
        if item.parent_occurrence is None or item.production_id is None:
            continue
        rule = production[item.production_id]
        edges.append(CorpusPortEdge(
            item.parent_occurrence, item.node_id, item.production_id,
            rule.parent_type, rule.child_type,
            rule.port.symmetry_orbit_key))
    edges = tuple(edges)
    return ActionGraphPatch(
        patch_id, nodes, edges,
        tuple(wave.accepted_candidates for wave in result.waves),
        sum(item.wave == 0 for item in nodes), len(edges),
        len({item.production_id for item in edges}))


def _build_with_executions():
    oracle, _discarded_oracle_metadata = oracle_patch_fast(9, 34.)
    training, _ = _crop(
        oracle, TRAINING_CENTER, 11., "IQC-corpus-train")
    learned = compile_irregular_port_program(
        training.species, training.positions)
    frozen = fit_frozen_frontier_program(learned)
    patches = []
    executions = []
    for patch_id, center in enumerate(PATCH_CENTERS):
        seed_cloud, _ = _crop(
            oracle, center, 7., f"IQC-corpus-seed-{patch_id}")
        enumeration = enumerate_frozen_port_occurrences(
            learned, seed_cloud.species, seed_cloud.positions,
            select_greedy_cover=True)
        covered = {index for _, support in enumeration.occurrence_supports
                   for index in support}
        gaps = tuple((seed_cloud.species[index], seed_cloud.positions[index])
                     for index in range(len(seed_cloud.positions))
                     if index not in covered)
        seed = FrontierSeed(enumeration.occurrences, gaps)
        result = run_batch_frontier_search(
            frozen, seed, threshold_ratio=15 / 21, maximum_waves=5,
            maximum_accepted_per_wave=40,
            boundary=RadialBoundary(center, 11.))
        patches.append(_patch_record(patch_id, center, result, frozen))
        executions.append(result)
    payload = tuple((patch.patch_id, patch.nodes, patch.edges,
                     patch.accepted_per_wave) for patch in patches)
    digest = hashlib.sha256(repr(payload).encode()).hexdigest()
    corpus = IQCActionGraphCorpus(
        tuple(patches), len(training.positions), len(frozen.prototypes),
        len(frozen.productions), 15 / 21, 5, 40, 11.,
        sum(len(item.nodes) for item in patches),
        sum(item.action_nodes for item in patches),
        len({node.cluster_type for patch in patches for node in patch.nodes}),
        len({edge.production_id for patch in patches for edge in patch.edges}),
        digest, False, any(item.target_used for item in executions), False)
    return corpus, tuple(executions), oracle


def build_action_graph_corpus() -> IQCActionGraphCorpus:
    """Deterministic target-free API consumed by future submacro miners."""
    corpus, _, _ = _build_with_executions()
    return corpus


def submacro_edge_records(corpus: IQCActionGraphCorpus):
    """Stable flattened local production graph, with no score labels."""
    return tuple((patch.patch_id, edge.parent_node, edge.child_node,
                  edge.parent_type, edge.child_type,
                  edge.symmetry_orbit_key)
                 for patch in corpus.patches for edge in patch.edges)
