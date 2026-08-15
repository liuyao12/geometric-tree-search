#!/usr/bin/env python3
"""Mine recurring exact action submacros from the clean IQC train corpus.

Only the five internal R5/R7 training traces are consumed.  Correctness labels
were used upstream to construct those exact traces, but no heldout atom or
label is available here.  Numeric cluster/production ids are resolved to
colored prototype geometry and overlap chemistry before canonicalization.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from typing import Any, Sequence

from materials_gcts_macro_stationary_adapter import prototype_semantics
from materials_gcts_oriented_overlap_ports import (
    ClusterPrototype, IDENTITY, matmul, matvec, transpose)


@dataclass(frozen=True)
class ActionSubmacroOccurrence:
    patch_id: int
    node_ids: tuple[int, ...]
    atom_count: int
    render_conflict_free: bool
    atom_support: tuple[tuple[str, tuple[int, ...]], ...]


@dataclass(frozen=True)
class ActionSubmacroType:
    type_id: int
    normalized_key: str
    node_count: int
    edge_count: int
    occurrences: tuple[ActionSubmacroOccurrence, ...]
    independent_patch_support: int
    mdl_saving: int
    atom_count: int
    maximum_occurrence_atom_overlap_fraction: float
    promotable: bool


@dataclass(frozen=True)
class IQCActionSubmacroRecurrenceAudit:
    patches: int
    exact_input_actions: int
    candidate_occurrences: int
    exact_semantic_classes: int
    recurrent_classes: int
    admitted_types: tuple[ActionSubmacroType, ...]
    admitted_by_node_count: tuple[tuple[int, int], ...]
    promotable_types: int
    maximum_independent_patch_support: int
    types_with_three_independent_patches: int
    maximum_admitted_occurrence_atom_overlap_fraction: float
    heldout_used: bool
    family_phi_cell_used: bool
    raw_type_or_production_id_used_as_semantics: bool
    train_labels_used_only_for_trace_construction: bool
    semantic_extension_available: bool
    corpus_digest: str


def _species(value: Any) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}:{value!r}"


def _quantized(values, tolerance):
    return tuple(round(value / tolerance) for value in values)


def _matrix_key(matrix, tolerance):
    return _quantized(tuple(value for row in matrix for value in row),
                      tolerance)


def _subtract(left, right):
    return tuple(left[axis] - right[axis] for axis in range(3))


def _corpus_scale(prototypes) -> float:
    positive = []
    for prototype in prototypes:
        for index, (_, left) in enumerate(prototype.sites):
            positive.extend(math.dist(left, right)
                            for _, right in prototype.sites[index + 1:]
                            if math.dist(left, right) > 1e-9)
    if not positive:
        raise ValueError("semantic prototypes contain no separated sites")
    return min(positive)


def _connected_subsets(nodes, edges, maximum_nodes):
    adjacency = {node: set() for node in nodes}
    for parent, child in edges:
        adjacency[parent].add(child)
        adjacency[child].add(parent)
    current = {frozenset((node,)) for node in nodes}
    answer = []
    for size in range(2, maximum_nodes + 1):
        expanded = set()
        for subset in current:
            frontier = set().union(*(adjacency[node] for node in subset))
            for node in frontier - subset:
                candidate = subset | {node}
                if len(candidate) == size:
                    expanded.add(candidate)
        answer.extend(expanded)
        current = expanded
    return tuple(sorted(answer, key=lambda item: (
        len(item), tuple(sorted(item)))))


def _tied_orders(records):
    ordered = sorted(range(len(records)), key=lambda index: records[index])
    groups = []
    for _, group in itertools.groupby(ordered, key=lambda index: records[index]):
        groups.append(tuple(group))
    for choices in itertools.product(*(itertools.permutations(group)
                                       for group in groups)):
        yield tuple(index for group in choices for index in group)


def _canonical_submacro(nodes, edges, prototype_by_type, semantics,
                        production_by_id, scale, tolerance):
    local_nodes = tuple(nodes)
    node_index = {item.node_id: index for index, item in enumerate(local_nodes)}
    alternatives = []
    for anchor_index, anchor in enumerate(local_nodes):
        anchor_prototype = prototype_by_type[anchor.cluster_type]
        for anchor_gauge in anchor_prototype.proper_symmetries:
            frame = matmul(anchor.rotation, anchor_gauge)
            inverse = transpose(frame)
            records = []
            for item in local_nodes:
                semantic = semantics[item.cluster_type]
                translated = matvec(inverse, _subtract(
                    item.local_translation, anchor.local_translation))
                rotations = tuple(_matrix_key(matmul(
                    inverse, matmul(item.rotation, symmetry)), tolerance)
                                  for symmetry in
                                  prototype_by_type[item.cluster_type].proper_symmetries)
                records.append((
                    semantic.chemistry_key, semantic.chirality_key,
                    semantic.chemical_population,
                    _quantized(tuple(value / scale for value in translated),
                               tolerance), min(rotations)))
            for order in _tied_orders(records):
                remap = {old: new for new, old in enumerate(order)}
                port_records = []
                for edge in edges:
                    production = production_by_id[edge.production_id]
                    overlap = tuple(sorted(_species(value)
                                           for value in
                                           production.overlap_species))
                    port_records.append((
                        remap[node_index[edge.parent_node]],
                        remap[node_index[edge.child_node]],
                        ("colored-oriented-overlap", overlap)))
                code = (tuple(records[index] for index in order),
                        tuple(sorted(port_records, key=repr)))
                alternatives.append(code)
    code = min(alternatives, key=repr)
    payload = json.dumps(code, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def _render_atom_support(nodes, prototype_by_type, center, tolerance):
    sites = {}
    for node in nodes:
        prototype = prototype_by_type[node.cluster_type]
        for species, local in prototype.sites:
            rotated = matvec(node.rotation, local)
            point = tuple(center[axis] + rotated[axis] +
                          node.local_translation[axis]
                          for axis in range(3))
            key = _quantized(point, tolerance)
            label = _species(species)
            if key in sites and sites[key] != label:
                return (), False
            sites[key] = label
    return tuple(sorted((label, key) for key, label in sites.items())), True


def _support_overlap(left, right):
    left = frozenset(left)
    right = frozenset(right)
    denominator = min(len(left), len(right))
    return 1. if denominator == 0 else len(left & right) / denominator


def _independent_occurrences(occurrences, maximum_overlap=.1):
    """Conservatively select distinct-patch, nearly atom-disjoint copies."""
    ordered = tuple(sorted(occurrences, key=lambda item: (
        item.patch_id, item.node_ids)))
    alternatives = []
    for start in range(len(ordered)):
        chosen = [ordered[start]]
        used_patches = {ordered[start].patch_id}
        for item in ordered:
            if item.patch_id in used_patches:
                continue
            if all(_support_overlap(item.atom_support, old.atom_support) <=
                   maximum_overlap for old in chosen):
                chosen.append(item)
                used_patches.add(item.patch_id)
        alternatives.append(tuple(chosen))
    return max(alternatives, key=lambda values: (
        len(values), tuple((item.patch_id, item.node_ids) for item in values)),
               default=())


def evaluate(corpus=None, *, minimum_nodes: int = 2,
             maximum_nodes: int = 5, tolerance: float = 1e-5,
             minimum_independent_patches: int = 2):
    """Return exact recurring semantic types and promotion readiness."""
    if corpus is None:
        from materials_gcts_iqc_clean_training_action_corpus import (
            build_clean_training_action_corpus)
        corpus = build_clean_training_action_corpus()
    if not 2 <= minimum_nodes <= maximum_nodes <= 5:
        raise ValueError("submacro node range must lie within 2--5")
    if minimum_independent_patches < 2:
        raise ValueError("recurrence needs at least two independent patches")
    if not getattr(corpus, "semantic_descriptors_train_only", False):
        raise ValueError("clean corpus lacks train-only semantic descriptors")

    prototype_by_type = {item.cluster_type: ClusterPrototype(
        item.cluster_type, item.sites, item.proper_symmetries)
                         for item in corpus.prototypes}
    semantics = {type_id: prototype_semantics(prototype, tolerance=tolerance)
                 for type_id, prototype in prototype_by_type.items()}
    production_by_id = {item.production_id: item
                        for item in corpus.productions}
    scale = _corpus_scale(tuple(prototype_by_type.values()))
    classes = {}
    candidates = 0
    for patch in corpus.patches:
        nodes = {item.node_id: item for item in patch.nodes}
        edge_pairs = tuple((item.parent_node, item.child_node)
                           for item in patch.edges)
        for subset in _connected_subsets(nodes, edge_pairs, maximum_nodes):
            if len(subset) < minimum_nodes:
                continue
            selected_nodes = tuple(nodes[index] for index in sorted(subset))
            selected_edges = tuple(item for item in patch.edges
                                   if item.parent_node in subset and
                                   item.child_node in subset)
            if len(selected_edges) != len(selected_nodes) - 1:
                continue
            candidates += 1
            key = _canonical_submacro(
                selected_nodes, selected_edges, prototype_by_type, semantics,
                production_by_id, scale, tolerance)
            atom_support, conflict_free = _render_atom_support(
                selected_nodes, prototype_by_type, patch.center, tolerance)
            classes.setdefault(key, []).append(ActionSubmacroOccurrence(
                patch.patch_id, tuple(sorted(subset)), len(atom_support),
                conflict_free, atom_support))

    admitted = []
    recurrent = 0
    for key, occurrences in sorted(classes.items()):
        independent = _independent_occurrences(occurrences)
        patch_support = len(independent)
        if patch_support >= minimum_independent_patches:
            recurrent += 1
        node_count = len(occurrences[0].node_ids)
        edge_count = node_count - 1
        # Token accounting is fixed before looking at recurrence: one token
        # per primitive node/edge, one dictionary copy, one reference/copy.
        primitive = len(independent) * (node_count + edge_count)
        dictionary = node_count + edge_count
        references = len(independent)
        saving = primitive - dictionary - references
        atom_counts = {item.atom_count for item in independent}
        overlaps = tuple(_support_overlap(left.atom_support,
                                          right.atom_support)
                         for index, left in enumerate(independent)
                         for right in independent[index + 1:])
        maximum_overlap = max(overlaps, default=0.)
        promotable = (patch_support >= minimum_independent_patches and
                      saving > 0 and len(atom_counts) == 1 and
                      maximum_overlap <= .1 and
                      all(item.render_conflict_free for item in independent))
        if patch_support < minimum_independent_patches or saving <= 0:
            continue
        admitted.append(ActionSubmacroType(
            len(admitted), key, node_count, edge_count, tuple(independent),
            patch_support, saving,
            next(iter(atom_counts)) if len(atom_counts) == 1 else 0,
            maximum_overlap, promotable))
    by_size = tuple((size, sum(item.node_count == size for item in admitted))
                    for size in range(minimum_nodes, maximum_nodes + 1))
    return IQCActionSubmacroRecurrenceAudit(
        len(corpus.patches), corpus.total_exact_actions, candidates,
        len(classes), recurrent, tuple(admitted), by_size,
        sum(item.promotable for item in admitted),
        max((item.independent_patch_support for item in admitted), default=0),
        sum(item.independent_patch_support >= 3 for item in admitted),
        max((item.maximum_occurrence_atom_overlap_fraction
             for item in admitted), default=0.),
        bool(corpus.heldout_patch_atoms_or_labels_used), False, False,
        bool(corpus.known_training_labels_used_for_exact_trace_selection),
        True, corpus.corpus_digest)


if __name__ == "__main__":
    import dataclasses
    result = evaluate()
    summary = dataclasses.asdict(result)
    summary["admitted_types"] = len(result.admitted_types)
    print(json.dumps(summary, indent=2, sort_keys=True))
