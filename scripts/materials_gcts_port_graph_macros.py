#!/usr/bin/env python3
"""Mine reusable cluster-of-cluster macros from a witnessed oriented port graph.

Input is an ``IrregularPortProgram`` learned from one finite configuration.
Vertices are proper cluster occurrences; admitted witnessed port relations are
directed, labelled edges.  Cheap rooted connected subsets are canonicalized by
their complete labelled adjacency matrix, then split by exact root-local
colored geometry.  Every retained occurrence passes proper-SE(3) cycle closure.

Macro evidence must include at least two nearly atom-disjoint embeddings and a
positive explicit description-length saving.  This module discovers reusable
graph productions; it does not infer an exterior continuation or rank actions.
"""

from __future__ import annotations

import itertools
import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_irregular_port_atlas import IrregularPortProgram
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, ClusterPrototype, Matrix, Vector, is_proper_rotation,
    matmul, matvec, transpose)
from materials_gcts_sparse_occurrence_graph import reduce_occurrence_graph

PortKey = tuple[int, int, tuple[int, ...]]
Site = tuple[Hashable, Vector]


@dataclass(frozen=True)
class MacroEdge:
    source: int
    target: int
    port: PortKey


@dataclass(frozen=True)
class MacroChildPlacement:
    node: int
    cluster_type: int
    rotation: Matrix
    translation: Vector


@dataclass(frozen=True)
class MacroOccurrence:
    root_occurrence: int
    node_occurrences: tuple[int, ...]
    atom_indices: tuple[int, ...]
    maximum_cycle_residual: float


@dataclass(frozen=True)
class BoundarySlot:
    node: int
    direction: str
    outside_type: int
    port: PortKey
    occurrence_support: int
    frequency: float


@dataclass(frozen=True)
class MacroType:
    macro_id: int
    node_types: tuple[int, ...]
    edges: tuple[MacroEdge, ...]
    child_placements: tuple[MacroChildPlacement, ...]
    atom_union: tuple[Site, ...]
    boundary_slots: tuple[BoundarySlot, ...]
    occurrences: tuple[MacroOccurrence, ...]
    primitive_tokens_per_occurrence: int
    dictionary_tokens: int
    reference_tokens: int
    mdl_saving: int
    maximum_occurrence_atom_overlap_fraction: float
    exact_graph_isomorphism_verified: bool
    se3_cycle_consistent: bool
    # ``occurrences`` is the nearly atom-disjoint evidence used by the MDL
    # recurrence gate.  The next hierarchy level must not be starved to that
    # proof subset: it may use every exact embedding, after identical atom
    # unions have been deterministically deduplicated.
    promotion_occurrences: tuple[MacroOccurrence, ...] = ()
    # All exact graph derivations of the retained geometric support. Ordinary
    # promotion uses one derivation per support; an explicit diagnostic may
    # union their witnessed boundaries, while safe alternative-aware
    # promotion keeps them separate.
    promotion_derivations: tuple[MacroOccurrence, ...] = ()


@dataclass(frozen=True)
class MacroMiningResult:
    source_graph_vertices: int
    source_graph_edges: int
    graph_vertices: int
    graph_edges: int
    sparse_undirected_edges: int
    sparse_node_reduction: float
    sparse_edge_reduction: float
    rooted_connected_candidates: int
    exact_geometry_classes: int
    rejected_cycle_inconsistent: int
    rejected_overlapping_evidence: int
    rejected_nonpositive_mdl: int
    macro_types: tuple[MacroType, ...]
    maximum_macro_nodes: int
    maximum_macro_atoms: int


@dataclass(frozen=True)
class _Embedding:
    order: tuple[int, ...]
    graph_code: tuple
    geometry_code: tuple
    rotations: tuple[Matrix, ...]
    translations: tuple[Vector, ...]
    atom_indices: tuple[int, ...]
    cycle_residual: float


@dataclass(frozen=True)
class _GraphCandidate:
    root: int
    nodes: frozenset[int]
    colors: tuple[tuple[int, str], ...]
    bucket: tuple
    atom_indices: tuple[int, ...]


@dataclass
class _ExactGraphClass:
    representative: _GraphCandidate
    graph_code: tuple
    canonical_orders: tuple[tuple[int, ...], ...]
    candidates: list[tuple[_GraphCandidate, dict[int, int]]]


def _add(left: Vector, right: Vector) -> Vector:
    return tuple(left[i] + right[i] for i in range(3))  # type: ignore[return-value]


def _subtract(left: Vector, right: Vector) -> Vector:
    return tuple(left[i] - right[i] for i in range(3))  # type: ignore[return-value]


def _quantized(point: Sequence[float], tolerance: float) -> tuple[int, ...]:
    return tuple(round(value / tolerance) for value in point)


def _rotation_residual(left: Matrix, right: Matrix) -> float:
    return max(abs(left[row][column] - right[row][column])
               for row in range(3) for column in range(3))


def _relative(parent: ClusterOccurrence,
              child: ClusterOccurrence) -> tuple[Matrix, Vector]:
    inverse = transpose(parent.rotation)
    return (matmul(inverse, child.rotation),
            matvec(inverse, _subtract(
                child.translation, parent.translation)))


def _root_relative(root: ClusterOccurrence,
                   child: ClusterOccurrence) -> tuple[Matrix, Vector]:
    return _relative(root, child)


def _compose(rotation: Matrix, translation: Vector,
             relative_rotation: Matrix,
             relative_translation: Vector) -> tuple[Matrix, Vector]:
    return (matmul(rotation, relative_rotation),
            _add(translation, matvec(rotation, relative_translation)))


def _port_graph(program: IrregularPortProgram, *,
                include_boundary_relations: bool = False):
    sparse = reduce_occurrence_graph(
        program, include_boundary_relations=include_boundary_relations)
    admitted = {(port.parent_type, port.child_type,
                 port.symmetry_orbit_key)
                for port in program.atlas.ports}
    occurrence_type = {occurrence.occurrence_id: occurrence.type_id
                       for occurrence in program.occurrences
                       if occurrence.occurrence_id in sparse.retained_nodes}
    retained_pair_kinds = {
        (edge.left, edge.right, edge.connection_kind)
        for edge in sparse.retained_edges}
    edges = set()
    for parent, child, parent_type, child_type, pose_key in (
            program.atlas.relation_classes):
        label = parent_type, child_type, pose_key
        pair = min(parent, child), max(parent, child)
        if (label in admitted and pair + ("overlap",) in retained_pair_kinds and
                parent in occurrence_type and child in occurrence_type and
                parent != child):
            edges.add((parent, child, label))
    if include_boundary_relations:
        admitted_boundary = {
            (port.parent_type, port.child_type, port.symmetry_orbit_key)
            for port in getattr(program, "boundary_ports", ())}
        for relation in getattr(program, "boundary_relation_classes", ()):
            if getattr(relation, "child_port_witnesses", 0) <= 0:
                continue
            label = (relation.parent_type, relation.child_type,
                     relation.symmetry_orbit_key)
            pair = (min(relation.parent_occurrence,
                        relation.child_occurrence),
                    max(relation.parent_occurrence,
                        relation.child_occurrence))
            if (label in admitted_boundary and
                    pair + ("boundary",) in retained_pair_kinds and
                    relation.parent_occurrence in occurrence_type and
                    relation.child_occurrence in occurrence_type and
                    relation.parent_occurrence != relation.child_occurrence):
                edges.add((relation.parent_occurrence,
                           relation.child_occurrence, label))
    adjacency: dict[int, set[int]] = {
        occurrence_id: set() for occurrence_id in occurrence_type}
    for parent, child, _ in edges:
        adjacency[parent].add(child)
        adjacency[child].add(parent)
    return (occurrence_type, tuple(sorted(edges, key=repr)), adjacency,
            sparse)


def _rooted_connected_sets(adjacency: dict[int, set[int]],
                           maximum_nodes: int):
    result = set()
    for root in sorted(adjacency):
        pending = [(frozenset((root,)), frozenset(adjacency[root]))]
        seen = {frozenset((root,))}
        while pending:
            nodes, frontier = pending.pop()
            if len(nodes) >= 2:
                result.add((root, nodes))
            if len(nodes) == maximum_nodes:
                continue
            for node in sorted(frontier):
                grown = nodes | {node}
                if grown in seen:
                    continue
                seen.add(grown)
                boundary = set(frontier)
                boundary.update(adjacency[node])
                boundary.difference_update(grown)
                pending.append((grown, frozenset(boundary)))
    return tuple(sorted(result, key=lambda item: (
        len(item[1]), item[0], tuple(sorted(item[1])))))


def _graph_code(order: Sequence[int], occurrence_type: dict[int, int],
                edges: Sequence[tuple[int, int, PortKey]]) -> tuple:
    index = {node: offset for offset, node in enumerate(order)}
    internal = tuple(sorted(
        (index[parent], index[child], label)
        for parent, child, label in edges
        if parent in index and child in index))
    return (tuple(occurrence_type[node] for node in order), internal)


def _edge_matrix(nodes, edges):
    allowed = set(nodes)
    result = defaultdict(list)
    for parent, child, label in edges:
        if parent in allowed and child in allowed:
            result[parent, child].append(label)
    return {key: tuple(sorted(value, key=repr))
            for key, value in result.items()}


def _refined_graph_bucket(root, nodes, occurrence_type, edges):
    """Collision-safe WL bucket; exact isomorphism follows every match."""
    matrix = _edge_matrix(nodes, edges)
    colors = {node: hashlib.sha256(repr(
        (node == root, occurrence_type[node])).encode()).hexdigest()
              for node in nodes}
    for _ in range(len(nodes)):
        refined = {}
        for node in nodes:
            outgoing = tuple(sorted(
                (repr(labels), colors[other])
                for (source, other), labels in matrix.items()
                if source == node))
            incoming = tuple(sorted(
                (repr(labels), colors[other])
                for (other, target), labels in matrix.items()
                if target == node))
            refined[node] = hashlib.sha256(repr((
                colors[node], outgoing, incoming)).encode()).hexdigest()
        if refined == colors:
            break
        colors = refined
    bucket = (
        len(nodes), tuple(sorted(colors.values())),
        tuple(sorted((colors[parent], colors[child], repr(labels))
                     for (parent, child), labels in matrix.items())))
    return colors, bucket


def _canonical_graph_orders(candidate, occurrence_type, edges):
    colors = dict(candidate.colors)
    cells = defaultdict(list)
    for node in candidate.nodes:
        if node != candidate.root:
            cells[colors[node]].append(node)
    ordered_cells = tuple(tuple(sorted(cells[color]))
                          for color in sorted(cells))
    minimum = None
    orders = []
    products = itertools.product(*(
        itertools.permutations(cell) for cell in ordered_cells))
    for cell_orders in products:
        order = (candidate.root,) + tuple(
            node for cell in cell_orders for node in cell)
        code = _graph_code(order, occurrence_type, edges)
        if minimum is None or code < minimum:
            minimum, orders = code, [order]
        elif code == minimum:
            orders.append(order)
    assert minimum is not None
    return minimum, tuple(orders)


def _first_exact_isomorphism(left, right, occurrence_type, edges):
    """Return one root-preserving exact labelled directed isomorphism."""
    if len(left.nodes) != len(right.nodes):
        return None
    left_colors, right_colors = dict(left.colors), dict(right.colors)
    left_matrix = _edge_matrix(left.nodes, edges)
    right_matrix = _edge_matrix(right.nodes, edges)
    mapping = {left.root: right.root}
    used = {right.root}
    remaining = tuple(sorted(left.nodes - {left.root}, key=lambda node: (
        sum(left_colors[other] == left_colors[node] for other in left.nodes),
        left_colors[node], occurrence_type[node], node)))

    def compatible(source, target):
        if (left_colors[source] != right_colors[target] or
                occurrence_type[source] != occurrence_type[target]):
            return False
        for prior_source, prior_target in mapping.items():
            if (left_matrix.get((source, prior_source), ()) !=
                    right_matrix.get((target, prior_target), ()) or
                    left_matrix.get((prior_source, source), ()) !=
                    right_matrix.get((prior_target, target), ())):
                return False
        return True

    def search(depth):
        if depth == len(remaining):
            return dict(mapping)
        source = remaining[depth]
        choices = sorted(
            (node for node in right.nodes - used
             if compatible(source, node)),
            key=lambda node: (right_colors[node], occurrence_type[node], node))
        for target in choices:
            mapping[source] = target
            used.add(target)
            result = search(depth + 1)
            if result is not None:
                return result
            used.remove(target)
            del mapping[source]
        return None

    return search(0)


def _canonical_embedding_from_class(
    candidate, candidate_to_representative, graph_class, occurrence_type,
    edges, occurrences, prototypes, support_by_id, tolerance,
):
    representative_to_candidate = {
        target: source for source, target in candidate_to_representative.items()}
    alternatives = tuple(tuple(representative_to_candidate[node]
                               for node in order)
                         for order in graph_class.canonical_orders)
    root_prototype = prototypes[occurrence_type[candidate.root]]
    geometric = []
    for order in alternatives:
        for symmetry in root_prototype.proper_symmetries:
            code, rotations, translations = _geometry(
                order, symmetry, occurrences, prototypes, tolerance)
            geometric.append((code, order, rotations, translations))
    geometry_code, order, rotations, translations = min(
        geometric, key=lambda item: (item[0], item[1]))
    return _Embedding(
        order, graph_class.graph_code, geometry_code, rotations, translations,
        candidate.atom_indices, _cycle_residual(order, edges, occurrences))


def _has_independent_candidates(candidates, maximum_overlap_fraction):
    for index, left in enumerate(candidates):
        left_atoms = set(left.atom_indices)
        for right in candidates[index + 1:]:
            right_atoms = set(right.atom_indices)
            if (len(left_atoms.intersection(right_atoms)) <=
                    maximum_overlap_fraction * min(
                        len(left_atoms), len(right_atoms))):
                return True
    return False


def _geometry(
    order: Sequence[int], root_symmetry: Matrix,
    occurrences: dict[int, ClusterOccurrence],
    prototypes: dict[int, ClusterPrototype], tolerance: float,
) -> tuple[tuple, tuple[Matrix, ...], tuple[Vector, ...]]:
    root = occurrences[order[0]]
    inverse_symmetry = transpose(root_symmetry)
    rotations = []
    translations = []
    rendered = []
    for node in order:
        rotation, translation = _root_relative(root, occurrences[node])
        rotation = matmul(inverse_symmetry, rotation)
        translation = matvec(inverse_symmetry, translation)
        rotations.append(rotation)
        translations.append(translation)
        prototype = prototypes[occurrences[node].type_id]
        rendered.append(tuple(sorted(
            (repr(species),) + _quantized(
                _add(matvec(rotation, point), translation), tolerance)
            for species, point in prototype.sites)))
    return tuple(rendered), tuple(rotations), tuple(translations)


def _cycle_residual(
    order: Sequence[int], edges: Sequence[tuple[int, int, PortKey]],
    occurrences: dict[int, ClusterOccurrence],
) -> float:
    root = occurrences[order[0]]
    root_poses = {node: _root_relative(root, occurrences[node])
                  for node in order}
    nodes = set(order)
    residual = 0.0
    for parent, child, _ in edges:
        if parent not in nodes or child not in nodes:
            continue
        edge_rotation, edge_translation = _relative(
            occurrences[parent], occurrences[child])
        predicted = _compose(
            *root_poses[parent], edge_rotation, edge_translation)
        expected = root_poses[child]
        residual = max(
            residual, _rotation_residual(predicted[0], expected[0]),
            math.dist(predicted[1], expected[1]))
    return residual


def _canonical_embedding(
    root: int, nodes: frozenset[int], occurrence_type: dict[int, int],
    edges: Sequence[tuple[int, int, PortKey]],
    occurrences: dict[int, ClusterOccurrence],
    prototypes: dict[int, ClusterPrototype], support_by_id: dict[int, tuple[int, ...]],
    tolerance: float,
) -> _Embedding:
    others = tuple(sorted(nodes - {root}))
    alternatives = []
    minimum_graph = None
    for permutation in itertools.permutations(others):
        order = (root,) + permutation
        code = _graph_code(order, occurrence_type, edges)
        if minimum_graph is None or code < minimum_graph:
            minimum_graph = code
            alternatives = [order]
        elif code == minimum_graph:
            alternatives.append(order)
    assert minimum_graph is not None
    root_prototype = prototypes[occurrence_type[root]]
    geometric = []
    for order in alternatives:
        for symmetry in root_prototype.proper_symmetries:
            code, rotations, translations = _geometry(
                order, symmetry, occurrences, prototypes, tolerance)
            geometric.append((code, order, rotations, translations))
    geometry_code, order, rotations, translations = min(
        geometric, key=lambda item: (item[0], item[1]))
    atoms = tuple(sorted({atom for node in order
                          for atom in support_by_id[node]}))
    return _Embedding(
        order, minimum_graph, geometry_code, rotations, translations, atoms,
        _cycle_residual(order, edges, occurrences))


def _select_disjoint(embeddings: Sequence[_Embedding],
                     maximum_overlap_fraction: float):
    selected = []
    rejected = 0
    for embedding in sorted(embeddings, key=lambda item: (
            item.order[0], item.order)):
        atoms = set(embedding.atom_indices)
        if any(len(atoms.intersection(other.atom_indices)) >
               maximum_overlap_fraction * min(len(atoms), len(other.atom_indices))
               for other in selected):
            rejected += 1
            continue
        selected.append(embedding)
    return tuple(selected), rejected


def _unique_embeddings(embeddings: Sequence[_Embedding]) -> tuple[_Embedding, ...]:
    """Keep one deterministic pose for each exact covered atom union.

    A rooted enumeration can rediscover one physical macro through several
    roots or traversal orders.  Those are one occurrence for promotion, while
    genuinely overlapping macros on different atom unions remain available.
    """
    unique = {}
    for embedding in sorted(embeddings, key=lambda item: (
            item.atom_indices, item.order, item.geometry_code)):
        unique.setdefault(embedding.atom_indices, embedding)
    return tuple(unique[key] for key in sorted(unique))


def _atom_union(
    embedding: _Embedding, occurrence_type: dict[int, int],
    prototypes: dict[int, ClusterPrototype], tolerance: float,
) -> tuple[Site, ...] | None:
    sites = {}
    positions = {}
    for node_index, occurrence_id in enumerate(embedding.order):
        prototype = prototypes[occurrence_type[occurrence_id]]
        rotation = embedding.rotations[node_index]
        translation = embedding.translations[node_index]
        for species, point in prototype.sites:
            moved = _add(matvec(rotation, point), translation)
            coordinate = _quantized(moved, tolerance)
            if coordinate in sites and sites[coordinate] != species:
                return None
            sites[coordinate] = species
            positions.setdefault(coordinate, moved)
    return tuple((sites[key], positions[key]) for key in sorted(sites))


def _boundary_slots(
    selected: Sequence[_Embedding], edges: Sequence[tuple[int, int, PortKey]],
    occurrence_type: dict[int, int],
) -> tuple[BoundarySlot, ...]:
    counts = Counter()
    for embedding in selected:
        index = {node: offset for offset, node in enumerate(embedding.order)}
        seen = set()
        for parent, child, port in edges:
            if parent in index and child not in index:
                seen.add((index[parent], "outgoing",
                          occurrence_type[child], port))
            elif child in index and parent not in index:
                seen.add((index[child], "incoming",
                          occurrence_type[parent], port))
        counts.update(seen)
    return tuple(BoundarySlot(
        node, direction, outside_type, port, count,
        count / len(selected))
        for (node, direction, outside_type, port), count in
        sorted(counts.items(), key=repr))


def mine_port_graph_macros(
    program: IrregularPortProgram, *, maximum_nodes: int = 3,
    minimum_occurrences: int = 2, maximum_atom_overlap_fraction: float = .1,
    geometry_tolerance: float = .03, cycle_tolerance: float = 1e-6,
    include_boundary_relations: bool = False,
) -> MacroMiningResult:
    """Mine exact repeated rooted connected macros with an MDL gate."""
    if not 2 <= maximum_nodes <= 8:
        raise ValueError("maximum_nodes must be between two and eight")
    if minimum_occurrences < 2:
        raise ValueError("minimum_occurrences must be at least two")
    if not 0 <= maximum_atom_overlap_fraction < 1:
        raise ValueError("atom overlap fraction must be in [0, 1)")
    if geometry_tolerance <= 0 or cycle_tolerance <= 0:
        raise ValueError("geometry and cycle tolerances must be positive")
    occurrence_type, edges, adjacency, sparse = _port_graph(
        program, include_boundary_relations=include_boundary_relations)
    occurrences = {item.occurrence_id: item for item in program.occurrences}
    prototypes = {item.type_id: item for item in program.prototypes}
    all_supports = dict(program.occurrence_supports)
    supports = {node: all_supports[node] for node in occurrence_type}
    if set(occurrence_type) != set(supports):
        raise ValueError("every oriented occurrence needs an atom support")
    if any(not is_proper_rotation(item.rotation)
           for item in program.occurrences):
        raise ValueError("macro graph contains an improper occurrence pose")
    rooted = _rooted_connected_sets(adjacency, maximum_nodes)
    wl_buckets = defaultdict(list)
    for root, nodes in rooted:
        colors, bucket = _refined_graph_bucket(
            root, nodes, occurrence_type, edges)
        atoms = tuple(sorted({atom for node in nodes for atom in supports[node]}))
        wl_buckets[bucket].append(_GraphCandidate(
            root, nodes, tuple(sorted(colors.items())), bucket, atoms))
    exact_graph_classes = []
    for bucket in sorted(wl_buckets, key=repr):
        candidates = wl_buckets[bucket]
        if len(candidates) < minimum_occurrences:
            continue
        classes = []
        for candidate in candidates:
            matched = None
            for graph_class in classes:
                mapping = _first_exact_isomorphism(
                    candidate, graph_class.representative,
                    occurrence_type, edges)
                if mapping is not None:
                    matched = graph_class, mapping
                    break
            if matched is None:
                code, orders = _canonical_graph_orders(
                    candidate, occurrence_type, edges)
                identity = {node: node for node in candidate.nodes}
                classes.append(_ExactGraphClass(
                    candidate, code, orders, [(candidate, identity)]))
            else:
                matched[0].candidates.append((candidate, matched[1]))
        exact_graph_classes.extend(classes)
    grouped = defaultdict(list)
    rejected_cycle = 0
    rejected_overlap = 0
    for graph_class in exact_graph_classes:
        graph_candidates = [item[0] for item in graph_class.candidates]
        if (len(graph_candidates) < minimum_occurrences or
                not _has_independent_candidates(
                    graph_candidates, maximum_atom_overlap_fraction)):
            rejected_overlap += len(graph_candidates)
            continue
        for candidate, mapping in graph_class.candidates:
            embedding = _canonical_embedding_from_class(
                candidate, mapping, graph_class, occurrence_type, edges,
                occurrences, prototypes, supports, geometry_tolerance)
            if embedding.cycle_residual > cycle_tolerance:
                rejected_cycle += 1
                continue
            grouped[(embedding.graph_code,
                     embedding.geometry_code)].append(embedding)
    macros = []
    rejected_mdl = 0
    for _, embeddings in sorted(grouped.items(), key=lambda item: repr(item[0])):
        selected, rejected = _select_disjoint(
            embeddings, maximum_atom_overlap_fraction)
        rejected_overlap += rejected
        if len(selected) < minimum_occurrences:
            continue
        representative = selected[0]
        node_types, graph_edges = representative.graph_code
        primitive = len(node_types) + len(graph_edges)
        dictionary = primitive
        references = len(selected)
        saving = len(selected) * primitive - dictionary - references
        if saving <= 0:
            rejected_mdl += 1
            continue
        union = _atom_union(
            representative, occurrence_type, prototypes, geometry_tolerance)
        if union is None:
            rejected_cycle += 1
            continue
        placements = tuple(MacroChildPlacement(
            index, node_types[index], representative.rotations[index],
            representative.translations[index])
            for index in range(len(node_types)))
        macro_edges = tuple(MacroEdge(source, target, port)
                            for source, target, port in graph_edges)
        macro_occurrences = tuple(MacroOccurrence(
            embedding.order[0], embedding.order, embedding.atom_indices,
            embedding.cycle_residual) for embedding in selected)
        promotion_occurrences = tuple(MacroOccurrence(
            embedding.order[0], embedding.order, embedding.atom_indices,
            embedding.cycle_residual)
            for embedding in _unique_embeddings(embeddings))
        maximum_overlap = max((
            len(set(left.atom_indices).intersection(right.atom_indices)) /
            min(len(left.atom_indices), len(right.atom_indices))
            for index, left in enumerate(selected)
            for right in selected[index + 1:]), default=0.0)
        macros.append(MacroType(
            len(macros), node_types, macro_edges, placements, union,
            _boundary_slots(selected, edges, occurrence_type),
            macro_occurrences, primitive, dictionary, references, saving,
            maximum_overlap, True, True, promotion_occurrences))
    return MacroMiningResult(
        sparse.source_nodes, sparse.source_edges,
        len(occurrence_type), len(edges), len(sparse.retained_edges),
        sparse.node_reduction, sparse.edge_reduction,
        len(rooted), len(grouped),
        rejected_cycle, rejected_overlap, rejected_mdl, tuple(macros),
        max((len(item.node_types) for item in macros), default=0),
        max((len(item.atom_union) for item in macros), default=0))
