#!/usr/bin/env python3
"""Target-blind second-block execution for the confirmed IQC frontier.

The first block is reconstructed from the original colored seed and the
already frozen, pre-target action key.  Its completed configuration becomes
the *only* seed for a new complete ``8 -> 8 -> 8`` block under a caller-supplied
public radius.  No target, truth, oracle, or scorer is accepted by this API.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color, _subset_proposals, _without_known_sites)
from materials_gcts_iqc_complete_frontier_confirmation_execution import (
    ACTION_REACH_SCHEDULE, _freeze_receipt)
from materials_gcts_iqc_complete_terminal_frontier_audit import (
    CompleteTerminalNucleus)
from materials_gcts_iqc_extended_development_preregistration import (
    TARGET_RADIUS as FIRST_BLOCK_RADIUS)
from materials_gcts_iqc_frozen_fusion_runtime import (
    BEAM_SPECS, FusionSearchState, FrozenFusionTerminal, _child,
    _local_section, _partial, _scalar_only_model, action_key,
    branch_features, load_default_runtime)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import CLUSTER_EDGES
from materials_gcts_pose_port_state_marking import score_pose_port_state
from materials_gcts_recursive_connections import (
    local_cluster_types, propose_with_recursive_marking)
from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, select_equivariant_port_fusion)


@dataclass(frozen=True)
class FrozenSelfFedCompleteFrontier:
    center: tuple[float, float, float]
    original_seed_atoms: int
    inherited_actions: tuple
    inherited_state_atoms: int
    public_radius: float
    action_reach_schedule: tuple[int, ...]
    candidate_counts_by_depth: tuple[int, ...]
    terminal_count: int
    terminal_actions: tuple[tuple, ...]
    scalar_order: tuple[int, ...]
    fusion_order: tuple[int, ...]
    portfolio_indices: tuple[int, ...]
    candidate_digest: str
    portfolio_digest: str
    inherited_state_digest: str
    execution_digest: str
    target_used: bool = False


def normalize_actions(actions):
    return tuple((tuple(map(float, point)), str(color))
                 for point, color in actions)


def _bounded_at_radius(connection, source, types, radius):
    if not math.isfinite(radius) or radius <= 0.:
        raise ValueError("public radius must be finite and positive")
    proposals = propose_with_recursive_marking(
        connection, source.seed_positions, types, HIDDEN_UNIT)
    proposals = _without_known_sites(proposals, source.seed_positions)
    return _subset_proposals(proposals, (
        point for point in proposals.votes
        if math.dist(point, source.group) <= radius + 1e-8))


def _complete_states_at_radius(
        source, runtime, radius, *, use_caches=True, telemetry=None):
    connection = runtime["connection"]
    state_model = runtime["state_model"]
    initial_types = local_cluster_types(
        source.seed_positions, source.seed_species, CLUSTER_EDGES)
    frontier = _bounded_at_radius(
        connection, source, initial_types, radius)
    states = (FusionSearchState(
        tuple(source.seed_positions), tuple(source.seed_species), frontier,
        (), (), (), 0., ()),)
    geometry_cache = {} if use_caches else None
    cluster_type_cache = {(): initial_types} if use_caches else None
    prototype_mapping_cache = {} if use_caches else None
    cache_hits = cache_misses = 0
    counts = []
    for reach, _spec in zip(ACTION_REACH_SCHEDULE, BEAM_SPECS):
        children = {}
        for state in states:
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
                -score_pose_port_state(state_model, descriptors[point]),
                -state.proposals.votes[point], point)))[:reach]
            for point in ordered:
                geometry_key = action_key(
                    state.actions + ((tuple(point), str(
                        _dominant_source_color(state.proposals, point))),))
                if geometry_cache is not None and geometry_key in geometry_cache:
                    cache_hits += 1
                else:
                    cache_misses += 1
                candidate = _child(
                    source, connection, state_model, state, point,
                    descriptors[point], radius,
                    geometry_cache=geometry_cache,
                    cluster_type_cache=cluster_type_cache,
                    prototype_mapping_cache=prototype_mapping_cache)
                key = action_key(candidate.actions)
                prior = children.get(key)
                if prior is None or (candidate.cumulative, candidate.actions) > \
                        (prior.cumulative, prior.actions):
                    children[key] = candidate
        states = tuple(sorted(children.values(),
                              key=lambda row: action_key(row.actions)))
        counts.append(len(states))
    if telemetry is not None:
        telemetry.update({
            "geometry_cache_hits": cache_hits,
            "geometry_cache_misses": cache_misses,
            "prototype_mapping_cache_entries":
                (0 if prototype_mapping_cache is None else
                 sum(len(rows) for rows in
                     prototype_mapping_cache.values())),
        })
    return states, tuple(counts)


def _freeze_at_radius(runtime, center, seed, radius):
    source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species))
    states, counts = _complete_states_at_radius(source, runtime, radius)
    terminals = []
    for state in states:
        partial, graph = _partial(
            source, state, runtime["grouped_vocabulary"])
        terminals.append(FrozenFusionTerminal(
            action_key(state.actions),
            tuple(branch_features(state)) + _local_section(state) + partial,
            tuple(color for _point, color in state.actions), graph,
            action_key(state.actions)))
    terminals = tuple(sorted(terminals, key=lambda row: repr(row.tie_key)))
    candidates = tuple(EquivariantPortFusionCandidate(
        row.scalar_features, row.action_colors, row.graph, row.tie_key)
        for row in terminals)
    fusion = select_equivariant_port_fusion(
        runtime["fusion_model"], candidates)
    scalar = select_equivariant_port_fusion(
        _scalar_only_model(runtime["fusion_model"]), candidates)
    scalar_order = tuple(sorted(range(len(terminals)), key=lambda index: (
        -scalar.fused_scores[index], repr(terminals[index].tie_key))))
    fusion_order = tuple(sorted(range(len(terminals)), key=lambda index: (
        -fusion.fused_scores[index], repr(terminals[index].tie_key))))
    digest = hashlib.sha256(repr(tuple(
        (row.actions, row.scalar_features, row.action_colors,
         row.graph.canonical_digest) for row in terminals)).encode()).hexdigest()
    return CompleteTerminalNucleus(
        tuple(center), len(seed.positions), counts, counts, terminals,
        scalar_order, fusion_order, digest)


def freeze_self_fed_candidates(*, center, seed_positions, seed_species,
                               inherited_actions, public_radius):
    """Reconstruct one frozen first-block branch, then enumerate block two."""
    if len(seed_positions) != len(seed_species) or not seed_positions:
        raise ValueError("seed positions/species must be nonempty and aligned")
    inherited_actions = normalize_actions(inherited_actions)
    if len(inherited_actions) != len(ACTION_REACH_SCHEDULE):
        raise ValueError("inherited branch must contain exactly three actions")
    center = tuple(map(float, center))
    runtime = load_default_runtime()
    original = SimpleNamespace(
        group=center,
        seed_positions=tuple(tuple(map(float, point))
                             for point in seed_positions),
        seed_species=tuple(map(str, seed_species)))
    first_states, _counts = _complete_states_at_radius(
        original, runtime, FIRST_BLOCK_RADIUS)
    inherited_key = action_key(inherited_actions)
    matches = tuple(state for state in first_states
                    if action_key(state.actions) == inherited_key)
    if len(matches) != 1:
        raise AssertionError("frozen inherited branch did not replay uniquely")
    inherited = matches[0]
    inherited_digest = hashlib.sha256(repr((
        inherited_key, inherited.positions, inherited.species)).encode()).hexdigest()
    grown_seed = SimpleNamespace(
        positions=inherited.positions, species=inherited.species)
    nucleus = _freeze_at_radius(
        runtime, center, grown_seed, float(public_radius))
    receipt = _freeze_receipt(nucleus)
    payload = (
        center, len(original.seed_positions), inherited_key,
        len(inherited.positions), float(public_radius),
        receipt.candidate_counts_by_depth, receipt.terminal_actions,
        receipt.scalar_order, receipt.fusion_order, receipt.portfolio_indices,
        receipt.candidate_digest, receipt.portfolio_digest, inherited_digest)
    execution_digest = hashlib.sha256(repr(payload).encode()).hexdigest()
    return FrozenSelfFedCompleteFrontier(
        center, len(original.seed_positions), inherited_key,
        len(inherited.positions), float(public_radius), ACTION_REACH_SCHEDULE,
        receipt.candidate_counts_by_depth, receipt.terminal_count,
        receipt.terminal_actions, receipt.scalar_order, receipt.fusion_order,
        receipt.portfolio_indices, receipt.candidate_digest,
        receipt.portfolio_digest, inherited_digest, execution_digest)


__all__ = [
    "FrozenSelfFedCompleteFrontier", "freeze_self_fed_candidates",
    "normalize_actions"]
