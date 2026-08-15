#!/usr/bin/env python3
"""Mine recurring exact connected submacros inside committed action macros."""

from __future__ import annotations

import hashlib
import itertools
import math
from collections import Counter, defaultdict
from dataclasses import dataclass

from materials_gcts_action_macro_promotion import ActionMacroType
from materials_gcts_frozen_frontier_replay import (
    FrozenFrontierProgram, Site, _add, _site_key)
from materials_gcts_oriented_overlap_ports import (
    Matrix, Vector, canonical_relative_pose, matmul, matvec, transpose)


@dataclass(frozen=True)
class ActionMacroCorpusEntry:
    patch_id: str
    macro: ActionMacroType


@dataclass(frozen=True)
class SubmacroChild:
    node: int
    source_node_id: int
    cluster_type: int
    rotation: Matrix
    translation: Vector


@dataclass(frozen=True)
class SubmacroEdge:
    source: int
    target: int
    connection_kind: str
    port_key: tuple[str, ...]
    overlap_chemistry: tuple[str, ...]


@dataclass(frozen=True)
class SubmacroBoundarySlot:
    node: int
    direction: str
    outside_type: int
    port_key: tuple[str, ...]
    occurrence_support: int


@dataclass(frozen=True)
class SubmacroOccurrence:
    patch_id: str
    action_macro_id: int
    wave: int
    source_node_ids: tuple[int, ...]
    atom_site_keys: tuple[tuple[str, int, int, int], ...]
    canonical_key: str


@dataclass(frozen=True)
class ActionSubmacroType:
    submacro_id: int
    node_types: tuple[int, ...]
    child_placements: tuple[SubmacroChild, ...]
    edges: tuple[SubmacroEdge, ...]
    atom_union: tuple[Site, ...]
    boundary_slots: tuple[SubmacroBoundarySlot, ...]
    occurrences: tuple[SubmacroOccurrence, ...]
    dense_occurrences: tuple[SubmacroOccurrence, ...]
    primitive_tokens_per_occurrence: int
    dictionary_tokens: int
    reference_tokens: int
    mdl_saving: int
    maximum_occurrence_atom_overlap_fraction: float
    exact_induced_graph_verified: bool
    proper_se3_colored_union_verified: bool


@dataclass(frozen=True)
class ActionSubmacroMiningResult:
    source_patches: int
    source_action_macros: int
    connected_induced_candidates: int
    exact_canonical_classes: int
    rejected_insufficient_disjoint_evidence: int
    rejected_nonpositive_mdl: int
    submacro_types: tuple[ActionSubmacroType, ...]
    target_used: bool


@dataclass(frozen=True)
class _Candidate:
    patch_id: str
    macro: ActionMacroType
    local_nodes: tuple[int, ...]
    canonical_key: str
    union_local: tuple[Site, ...]
    world_site_keys: tuple[tuple[str, int, int, int], ...]
    graph_code: tuple


def _subtract(left: Vector, right: Vector) -> Vector:
    return tuple(left[index] - right[index]
                 for index in range(3))  # type: ignore[return-value]


def _prototype(program, type_id):
    return next(item for item in program.prototypes if item.type_id == type_id)


def _render_child(program, child) -> tuple[Site, ...]:
    prototype = _prototype(program, child.cluster_type)
    return tuple((species, _add(
        matvec(child.rotation, point), child.translation))
        for species, point in prototype.sites)


def _union(program, macro, nodes, tolerance):
    local = {}
    species_at = {}
    world_keys = set()
    for node in nodes:
        child = macro.children[node]
        for species, point in _render_child(program, child):
            coordinate = tuple(round(value / tolerance) for value in point)
            if coordinate in species_at and species_at[coordinate] != species:
                raise ValueError("submacro contains an unlike-colored collision")
            species_at[coordinate] = species
            local.setdefault(coordinate, (species, point))
            world = _add(matvec(macro.world_rotation, point),
                         macro.world_translation)
            world_keys.add(_site_key((species, world), tolerance))
    return tuple(local[key] for key in sorted(local)), tuple(sorted(world_keys))


def _colored_union_code(union, tolerance):
    population = tuple(sorted(Counter(site[0] for site in union).items(),
                              key=repr))
    distances = tuple(sorted((
        repr(left[0]), repr(right[0]),
        round(math.dist(left[1], right[1]) / tolerance))
        for index, left in enumerate(union)
        for right in union[index + 1:]))
    return population, distances


def _connected(subset, edges):
    adjacency = {node: set() for node in subset}
    for edge in edges:
        if edge.source in adjacency and edge.target in adjacency:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)
    reached = {subset[0]}
    pending = [subset[0]]
    while pending:
        current = pending.pop()
        for neighbor in adjacency[current] - reached:
            reached.add(neighbor)
            pending.append(neighbor)
    return len(reached) == len(subset)


def _pair_pose_keys(program, macro, tolerance):
    result = {}
    for left_index, left in enumerate(macro.children):
        for right_index, right in enumerate(macro.children):
            if left_index == right_index:
                continue
            inverse = transpose(left.rotation)
            relative_rotation = matmul(inverse, right.rotation)
            relative_translation = matvec(
                inverse, _subtract(right.translation, left.translation))
            _, _, key = canonical_relative_pose(
                _prototype(program, left.cluster_type),
                _prototype(program, right.cluster_type),
                relative_rotation, relative_translation, tolerance)
            result[left_index, right_index] = key
    return result


def _canonical_graph_code(program, macro, subset, pair_keys):
    edge_labels = defaultdict(list)
    for edge in macro.edges:
        if edge.source in subset and edge.target in subset:
            edge_labels[edge.source, edge.target].append((
                edge.connection_kind, edge.port_key,
                tuple(sorted(key[0]
                             for key in edge.exact_overlap_site_keys))))
    alternatives = []
    for order in itertools.permutations(subset):
        node_code = tuple(macro.children[node].cluster_type for node in order)
        pose_code = tuple(pair_keys[left, right]
                          for left in order for right in order
                          if left != right)
        directed_edges = tuple(
            tuple(sorted(edge_labels.get((left, right), ()), key=repr))
            for left in order for right in order if left != right)
        alternatives.append((node_code, directed_edges, pose_code))
    return min(alternatives, key=repr)


def _representative(program, candidate, tolerance):
    macro = candidate.macro
    nodes = candidate.local_nodes
    root = macro.children[nodes[0]]
    inverse = transpose(root.rotation)
    children = tuple(SubmacroChild(
        local, macro.children[node].node_id,
        macro.children[node].cluster_type,
        matmul(inverse, macro.children[node].rotation),
        matvec(inverse, _subtract(
            macro.children[node].translation, root.translation)))
        for local, node in enumerate(nodes))
    node_to_local = {node: local for local, node in enumerate(nodes)}
    edges = tuple(SubmacroEdge(
        node_to_local[edge.source], node_to_local[edge.target],
        edge.connection_kind, edge.port_key,
        tuple(sorted(key[0] for key in edge.exact_overlap_site_keys)))
        for edge in macro.edges
        if edge.source in node_to_local and edge.target in node_to_local)
    boundaries = []
    for edge in macro.edges:
        inside_source = edge.source in node_to_local
        inside_target = edge.target in node_to_local
        if inside_source == inside_target:
            continue
        inside = edge.source if inside_source else edge.target
        outside = edge.target if inside_source else edge.source
        boundaries.append(SubmacroBoundarySlot(
            node_to_local[inside],
            "outgoing" if inside_source else "incoming",
            macro.children[outside].cluster_type, edge.port_key, 1))
    production_by_id = {item.production_id: item
                        for item in program.productions}
    for slot in macro.boundary_slots:
        if slot.child not in node_to_local:
            continue
        production = production_by_id[slot.production_id]
        boundaries.append(SubmacroBoundarySlot(
            node_to_local[slot.child], "incoming", production.parent_type,
            slot.port_key, 1))
    atom_union = tuple((species, matvec(inverse, _subtract(
        point, root.translation))) for species, point in candidate.union_local)
    return children, edges, atom_union, tuple(sorted(
        boundaries, key=lambda item: (item.node, item.direction,
                                      item.outside_type, item.port_key)))


def mine_action_submacros(
    program: FrozenFrontierProgram,
    action_macros: tuple[ActionMacroType | ActionMacroCorpusEntry, ...], *,
    minimum_nodes: int = 2, maximum_nodes: int = 5,
    geometry_tolerance: float | None = None,
    maximum_evidence_overlap_fraction: float = .1,
) -> ActionSubmacroMiningResult:
    """Mine recurring connected induced subgraphs without target labels."""
    if minimum_nodes < 2 or maximum_nodes < minimum_nodes:
        raise ValueError("submacro node bounds are invalid")
    tolerance = (program.overlap_tolerance if geometry_tolerance is None
                 else geometry_tolerance)
    if tolerance <= 0 or not 0 <= maximum_evidence_overlap_fraction < 1:
        raise ValueError("invalid geometry or evidence-overlap tolerance")
    corpus = tuple(
        item if isinstance(item, ActionMacroCorpusEntry) else
        ActionMacroCorpusEntry("default", item)
        for item in action_macros)
    if any(not item.patch_id for item in corpus):
        raise ValueError("every action macro corpus entry needs a patch id")
    candidates = []
    for corpus_entry in corpus:
        macro = corpus_entry.macro
        pair_keys = _pair_pose_keys(program, macro, tolerance)
        upper = min(maximum_nodes, len(macro.children))
        for size in range(minimum_nodes, upper + 1):
            for subset in itertools.combinations(range(len(macro.children)),
                                                 size):
                if not _connected(subset, macro.edges):
                    continue
                union, world_keys = _union(program, macro, subset, tolerance)
                graph_code = _canonical_graph_code(
                    program, macro, subset, pair_keys)
                code = graph_code, _colored_union_code(union, tolerance)
                key = hashlib.sha256(repr(code).encode()).hexdigest()
                candidates.append(_Candidate(
                    corpus_entry.patch_id, macro, subset, key, union,
                    world_keys, graph_code))
    grouped = defaultdict(list)
    for candidate in candidates:
        grouped[candidate.canonical_key].append(candidate)
    retained = []
    rejected_disjoint = rejected_mdl = 0
    for key in sorted(grouped):
        dense = sorted(grouped[key], key=lambda item: (
            item.patch_id, item.macro.wave, item.macro.macro_id,
            item.local_nodes))
        proof = []
        maximum_overlap = 0.0
        for candidate in dense:
            node_ids = {candidate.macro.children[node].node_id
                        for node in candidate.local_nodes}
            atom_keys = set(candidate.world_site_keys)
            compatible = True
            candidate_maximum = 0.0
            for prior in proof:
                if candidate.patch_id != prior.patch_id:
                    # Patch IDs are the corpus namespace and carry the
                    # caller's disjoint-patch contract. Bare node IDs and
                    # coordinate SiteKeys are never compared across patches.
                    continue
                prior_nodes = {prior.macro.children[node].node_id
                               for node in prior.local_nodes}
                prior_atoms = set(prior.world_site_keys)
                fraction = (len(atom_keys.intersection(prior_atoms)) /
                            max(1, min(len(atom_keys), len(prior_atoms))))
                candidate_maximum = max(candidate_maximum, fraction)
                if (node_ids.intersection(prior_nodes) or fraction >
                        maximum_evidence_overlap_fraction):
                    compatible = False
                    break
            if compatible:
                proof.append(candidate)
                maximum_overlap = max(maximum_overlap, candidate_maximum)
        if len(proof) < 2:
            rejected_disjoint += 1
            continue
        representative = proof[0]
        children, edges, atom_union, boundaries = _representative(
            program, representative, tolerance)
        primitive = len(children) + len(edges) + len(atom_union)
        dictionary = primitive + len(boundaries)
        references = len(proof)
        saving = len(proof) * primitive - dictionary - references
        if saving <= 0:
            rejected_mdl += 1
            continue
        def occurrence(item):
            return SubmacroOccurrence(
                item.patch_id, item.macro.macro_id, item.macro.wave,
                tuple(item.macro.children[node].node_id
                      for node in item.local_nodes),
                item.world_site_keys, item.canonical_key)
        retained.append(ActionSubmacroType(
            len(retained), tuple(child.cluster_type for child in children),
            children, edges, atom_union, boundaries,
            tuple(occurrence(item) for item in proof),
            tuple(occurrence(item) for item in dense),
            primitive, dictionary, references, saving, maximum_overlap,
            True, True))
    return ActionSubmacroMiningResult(
        len({item.patch_id for item in corpus}), len(action_macros),
        len(candidates), len(grouped),
        rejected_disjoint, rejected_mdl, tuple(retained), False)
