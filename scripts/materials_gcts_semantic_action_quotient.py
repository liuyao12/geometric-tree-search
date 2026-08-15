#!/usr/bin/env python3
"""MDL-selected approximate quotient for exact action terminals.

The quotient may pool a coarse connection grammar, but never merges exact
colored proper-SE(3) terminals.  Every deployment retains its exact key and
emitted colored sites.  Consequently this module cannot certify stationary
recursion; it only prepares a larger, explicitly approximate vocabulary for a
subsequent exact replay and three-level stationarity audit.
"""

from __future__ import annotations

import hashlib
import itertools
import math
from dataclasses import dataclass
from typing import Sequence

from materials_gcts_oriented_overlap_ports import matmul, matvec, transpose


@dataclass(frozen=True)
class ExactActionTerminal:
    patch_id: str
    exact_key: str
    topology_key: tuple
    chemistry_roles: tuple[str, ...]
    normalized_distances: tuple[float, ...]
    emitted_site_keys: tuple[tuple, ...]
    exact_children: tuple[tuple, ...] = ()
    outgoing_ports: tuple[tuple, ...] = ()


@dataclass(frozen=True)
class SemanticDescriptor:
    name: str
    chemistry_resolution: str
    distance_bin_width: float | None
    complexity_tokens: int


@dataclass(frozen=True)
class SemanticGrammarType:
    grammar_key: str
    deployments: tuple[ExactActionTerminal, ...]
    exact_alternatives: tuple[str, ...]
    independent_patches: int
    mdl_saving: int
    exact_replay_payload_complete: bool


@dataclass(frozen=True)
class DescriptorScore:
    descriptor: SemanticDescriptor
    discovery_grammar_types: int
    validation_deployments_covered: int
    validation_mdl_saving: int
    shuffled_control_mdl_saving: int
    perturbation_control_mdl_saving: int
    external_negative_control_mdl_saving: int | None
    guarded: bool


@dataclass(frozen=True)
class SemanticActionQuotient:
    selected_descriptor: SemanticDescriptor | None
    descriptor_scores: tuple[DescriptorScore, ...]
    grammar_types: tuple[SemanticGrammarType, ...]
    types_with_required_deployments: int
    required_deployments: int
    exact_terminals_preserved: bool
    approximate_grammar_called_exact: bool
    strict_stationarity_claimed: bool
    reason: str


DEFAULT_DESCRIPTORS = (
    SemanticDescriptor("exact-roles-fine-geometry", "exact", .25, 6),
    SemanticDescriptor("coarse-roles-medium-geometry", "coarse", .5, 4),
    SemanticDescriptor("terminal-chemistry-medium-geometry", "terminal", .5, 3),
    SemanticDescriptor("terminal-chemistry-coarse-geometry", "terminal", 1., 2),
    SemanticDescriptor("topology-only", "terminal", None, 1),
)


def terminals_from_action_corpus(program, entries, *, minimum_nodes=2,
                                 maximum_nodes=5):
    """Adapt exact committed action graphs to quotient terminals.

    This adapter consumes only frozen prototypes and committed train traces.
    The exact terminal key remains the existing colored-union/pose key.
    """
    from materials_gcts_action_submacro_mining import (
        _canonical_graph_code, _colored_union_code, _connected,
        _pair_pose_keys, _union)
    from materials_gcts_macro_stationary_adapter import prototype_semantics
    prototypes = {item.type_id: item for item in program.prototypes}
    semantics = {key: prototype_semantics(value, tolerance=1e-5)
                 for key, value in prototypes.items()}
    positive = tuple(math.dist(left, right)
                     for prototype in prototypes.values()
                     for index, (_, left) in enumerate(prototype.sites)
                     for _, right in prototype.sites[index + 1:]
                     if math.dist(left, right) > 1e-8)
    scale = min(positive)
    terminals = []
    for entry in entries:
        macro = entry.macro
        pair_keys = _pair_pose_keys(program, macro, program.overlap_tolerance)
        upper = min(maximum_nodes, len(macro.children))
        for size in range(minimum_nodes, upper + 1):
            for subset in itertools.combinations(range(len(macro.children)),
                                                 size):
                if not _connected(subset, macro.edges):
                    continue
                union, world_keys = _union(
                    program, macro, subset, program.overlap_tolerance)
                exact_graph = _canonical_graph_code(
                    program, macro, subset, pair_keys)
                exact_key = hashlib.sha256(repr((
                    exact_graph, _colored_union_code(
                        union, program.overlap_tolerance))).encode()).hexdigest()
                alternatives = []
                for order in itertools.permutations(subset):
                    remap = {old: new for new, old in enumerate(order)}
                    topology = tuple(sorted((
                        remap[edge.source], remap[edge.target],
                        edge.connection_kind,
                        tuple(sorted(key[0]
                                     for key in edge.exact_overlap_site_keys)))
                        for edge in macro.edges
                        if edge.source in remap and edge.target in remap))
                    roles = []
                    for node in order:
                        semantic = semantics[
                            macro.children[node].cluster_type]
                        species_family = ",".join(sorted(
                            value.split("*")[0]
                            for value in semantic.chemistry_key))
                        roles.append(
                            species_family + "|" + repr((
                                semantic.chemistry_key,
                                semantic.chirality_key)))
                    distances = tuple(
                        math.dist(macro.children[left].translation,
                                  macro.children[right].translation) / scale
                        for left_index, left in enumerate(order)
                        for right in order[left_index + 1:])
                    root = macro.children[order[0]]
                    inverse = transpose(root.rotation)
                    children = tuple((
                        macro.children[node].cluster_type,
                        matmul(inverse, macro.children[node].rotation),
                        matvec(inverse, tuple(
                            macro.children[node].translation[axis] -
                            root.translation[axis] for axis in range(3))))
                                     for node in order)
                    alternatives.append((topology, tuple(roles), distances,
                                         children))
                topology, roles, distances, children = min(
                    alternatives, key=repr)
                terminals.append(ExactActionTerminal(
                    entry.patch_id, exact_key, topology, roles, distances,
                    tuple(world_keys), children, topology))
    return tuple(terminals)


def _role(role: str, resolution: str) -> str:
    if resolution == "exact":
        return role
    if resolution == "coarse":
        # The prefix is a train-provided role family; exact chemistry remains
        # in the terminal and is never synthesized from this coarse label.
        return role.split("|", 1)[0]
    if resolution == "terminal":
        return "exact-chemistry-in-terminal"
    raise ValueError("unknown chemistry resolution")


def _key(item: ExactActionTerminal, descriptor: SemanticDescriptor,
         *, amorphous: bool = False) -> str:
    roles = tuple(_role(value, descriptor.chemistry_resolution)
                  for value in item.chemistry_roles)
    if descriptor.distance_bin_width is None:
        distances = ()
    else:
        width = descriptor.distance_bin_width
        jitter_seed = int(hashlib.sha256(
            item.exact_key.encode()).hexdigest()[:12], 16)
        binned = []
        for index, value in enumerate(item.normalized_distances):
            jitter = ((((jitter_seed >> (index % 24)) % 17) - 8) *
                      .19 * width) if amorphous else 0.
            binned.append(round((value + jitter) / width))
        distances = tuple(binned)
    payload = item.topology_key, roles, distances
    return hashlib.sha256(repr(payload).encode()).hexdigest()


def _mdl(groups, descriptor, patches):
    covered = saving = 0
    for values in groups.values():
        selected = {item.patch_id: item for item in values
                    if item.patch_id in patches}
        count = len(selected)
        if count < 2:
            continue
        # Shared topology/role tokens are dictionary-coded once; exact pose,
        # chemistry and emitted sites remain residual terminals per copy.
        structural = 2 + len(values[0].chemistry_roles)
        gain = count * structural - structural - count - \
            descriptor.complexity_tokens
        if gain > 0:
            covered += count
            saving += gain
    return covered, saving


def select_semantic_action_quotient(
        terminals: Sequence[ExactActionTerminal], *,
        descriptors: Sequence[SemanticDescriptor] = DEFAULT_DESCRIPTORS,
        required_deployments: int = 16,
        external_negative_terminals: Sequence[ExactActionTerminal] | None = None,
) -> SemanticActionQuotient:
    """Select resolution on spatial train folds with two negative controls."""
    if required_deployments < 2:
        raise ValueError("recursive evidence needs multiple deployments")
    patches = tuple(sorted({item.patch_id for item in terminals}))
    discovery = frozenset(patch for index, patch in enumerate(patches)
                          if index % 3 != 2)
    validation = frozenset(patches) - discovery
    scores = []
    viable = []
    for descriptor in descriptors:
        groups = {}
        perturbation_groups = {}
        shuffled_groups = {}
        for item in terminals:
            groups.setdefault(_key(item, descriptor), []).append(item)
            perturbation_groups.setdefault(
                _key(item, descriptor, amorphous=True), []).append(item)
            # Degree/topology-preserving incidence control: rotate semantic
            # roles and distance terminals within each exact action.
            offset = (0 if len(item.chemistry_roles) < 2 else 1 +
                      int(hashlib.sha256(item.exact_key.encode()).hexdigest()[
                          12:20], 16) % (len(item.chemistry_roles) - 1))
            distance_offset = (0 if len(item.normalized_distances) < 2 else 1 +
                               int(hashlib.sha256(
                                   item.exact_key.encode()).hexdigest()[20:28],
                                   16) %
                               (len(item.normalized_distances) - 1))
            shuffled = ExactActionTerminal(
                item.patch_id, item.exact_key, item.topology_key,
                item.chemistry_roles[offset:] + item.chemistry_roles[:offset],
                item.normalized_distances[distance_offset:] +
                item.normalized_distances[:distance_offset],
                item.emitted_site_keys, item.exact_children,
                item.outgoing_ports)
            shuffled_groups.setdefault(_key(shuffled, descriptor), []).append(
                shuffled)
        discovery_types = sum(
            len({item.patch_id for item in values if item.patch_id in discovery})
            >= 2 for values in groups.values())
        covered, saving = _mdl(groups, descriptor, validation)
        _, shuffled_saving = _mdl(shuffled_groups, descriptor, validation)
        _, perturbation_saving = _mdl(
            perturbation_groups, descriptor, validation)
        external_saving = None
        if external_negative_terminals is not None:
            external_groups = {}
            for item in external_negative_terminals:
                external_groups.setdefault(_key(item, descriptor), []).append(
                    item)
            negative_patches = frozenset(
                item.patch_id for item in external_negative_terminals)
            _, external_saving = _mdl(
                external_groups, descriptor, negative_patches)
        guarded = (saving > 0 and saving > shuffled_saving and
                   saving > perturbation_saving and
                   (external_saving is None or saving > external_saving))
        score = DescriptorScore(
            descriptor, discovery_types, covered, saving,
            shuffled_saving, perturbation_saving, external_saving, guarded)
        scores.append(score)
        if guarded:
            viable.append(score)
    if not viable:
        return SemanticActionQuotient(
            None, tuple(scores), (), 0, required_deployments, True, False,
            False, "no descriptor beats topology-preserving shuffled and "
                   "deterministic geometry-perturbation controls on train-only "
                   "validation folds")
    selected = max(viable, key=lambda item: (
        item.validation_mdl_saving, -item.descriptor.complexity_tokens,
        item.descriptor.name)).descriptor
    grouped = {}
    for item in terminals:
        grouped.setdefault(_key(item, selected), []).append(item)
    grammar = []
    for key, values in sorted(grouped.items()):
        by_patch = {item.patch_id: item for item in values}
        count = len(by_patch)
        structural = 2 + len(values[0].chemistry_roles)
        saving = count * structural - structural - count - \
            selected.complexity_tokens
        if count < 2 or saving <= 0:
            continue
        deployments = tuple(by_patch[key] for key in sorted(by_patch))
        grammar.append(SemanticGrammarType(
            key, deployments,
            tuple(sorted({item.exact_key for item in deployments})),
            count, saving,
            all(bool(item.exact_key) and bool(item.emitted_site_keys)
                and bool(item.exact_children) for item in deployments)))
    return SemanticActionQuotient(
        selected, tuple(scores), tuple(grammar),
        sum(item.independent_patches >= required_deployments
            for item in grammar), required_deployments,
        all(item.exact_replay_payload_complete for item in grammar),
        False, False, "")


@dataclass(frozen=True)
class QuotientProductionRecord:
    semantic_parent_type: str
    terminal: ExactActionTerminal


def production_records(quotient: SemanticActionQuotient):
    """Flatten selected grammar types for ``compile_from_semantic_quotient``."""
    return tuple(QuotientProductionRecord(item.grammar_key, terminal)
                 for item in quotient.grammar_types
                 for terminal in item.deployments)


def adapt_quotient_production(record, prototypes):
    """Compile one stored exact terminal to the execution grammar API."""
    from materials_gcts_semantic_production_grammar import (
        ExactChildPlacement, make_production_alternative)
    children = tuple(ExactChildPlacement(*item)
                     for item in record.terminal.exact_children)
    return make_production_alternative(
        record.semantic_parent_type, children, prototypes,
        outgoing_ports=record.terminal.outgoing_ports)
