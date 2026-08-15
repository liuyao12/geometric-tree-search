#!/usr/bin/env python3
"""Generic whole-placement consensus waves over a frozen frontier grammar."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Sequence

from materials_gcts_frozen_frontier_replay import (
    FrontierCandidate, FrontierSeed, FrozenFrontierProgram, PortKey,
    RadialBoundary, Site, _SpatialSiteIndex, _placed_sites, _pose_key,
    _site_key, enumerate_frontier)
from materials_gcts_oriented_overlap_ports import ClusterOccurrence, Matrix, Vector


@dataclass(frozen=True)
class ConsensusCandidate:
    candidate_id: str
    parent_occurrence: int
    production_id: int
    child_type: int
    emitted_site_keys: tuple[tuple[str, int, int, int], ...]
    minimum_site_support: int
    normalized_support: float
    accepted: bool
    rejection: str | None


@dataclass(frozen=True)
class ConsensusWave:
    wave: int
    candidates: tuple[ConsensusCandidate, ...]
    candidate_count: int
    maximum_minimum_site_support: int
    qualified_candidates: int
    accepted_candidates: int
    rejected_below_threshold: int
    rejected_wave_limit: int
    rejected_pair_conflicts: int
    rejected_redundant: int
    pairwise_compatible_antichain: bool
    sites_before: int
    sites_after: int


@dataclass(frozen=True)
class SymbolicConsensusNode:
    node_id: int
    cluster_type: int
    rotation: Matrix
    translation: Vector
    wave: int
    parent_occurrence: int | None
    production_id: int | None
    candidate_id: str | None
    normalized_support: float


@dataclass(frozen=True)
class BatchFrontierResult:
    threshold_ratio: float
    initial_sites: tuple[Site, ...]
    sites: tuple[Site, ...]
    placed_occurrences: tuple[ClusterOccurrence, ...]
    symbolic_nodes: tuple[SymbolicConsensusNode, ...]
    waves: tuple[ConsensusWave, ...]
    accepted_candidate_ids: tuple[str, ...]
    target_used: bool


def _candidate_id(
    candidate: FrontierCandidate, tolerance: float,
) -> str:
    occurrence = ClusterOccurrence(
        -1, candidate.child_type, candidate.rotation, candidate.translation)
    payload = repr(_pose_key(occurrence, tolerance)).encode()
    return hashlib.sha256(payload).hexdigest()[:24]


def run_batch_frontier_search(
    program: FrozenFrontierProgram,
    seed_occurrences: Sequence[ClusterOccurrence] | FrontierSeed, *,
    threshold_ratio: float,
    maximum_waves: int = 1,
    maximum_accepted_per_wave: int | None = None,
    boundary: RadialBoundary | None = None,
) -> BatchFrontierResult:
    """Repeat target-free frozen enumeration and compatible batch commits."""
    if (not math.isfinite(threshold_ratio) or threshold_ratio < 0 or
            threshold_ratio > 1):
        raise ValueError("threshold ratio must be finite and in [0, 1]")
    if maximum_waves < 0:
        raise ValueError("maximum waves cannot be negative")
    if (maximum_accepted_per_wave is not None and
            maximum_accepted_per_wave < 1):
        raise ValueError("per-wave acceptance limit must be positive")
    seed = (seed_occurrences if isinstance(seed_occurrences, FrontierSeed)
            else FrontierSeed(tuple(seed_occurrences)))
    if not seed.occurrences:
        raise ValueError("at least one seed occurrence is required")
    placed = [ClusterOccurrence(
        index, occurrence.type_id, occurrence.rotation,
        occurrence.translation)
        for index, occurrence in enumerate(seed.occurrences)]
    initial_sites = _placed_sites(
        program, placed, seed.explicit_gap_sites)
    occupied_by_key = {
        _site_key(site, program.overlap_tolerance): site
        for site in initial_sites}
    occupied_index = _SpatialSiteIndex(
        initial_sites, program.exclusion_distance)
    existing_poses = {_pose_key(item, program.overlap_tolerance)
                      for item in placed}
    orbit_cache = {}
    incoming_ports: dict[int, PortKey] = {}
    nodes = [SymbolicConsensusNode(
        occurrence.occurrence_id, occurrence.type_id,
        occurrence.rotation, occurrence.translation, 0, None, None, None, 1.0)
        for occurrence in placed]
    waves = []
    accepted_ids = []
    for wave_index in range(1, maximum_waves + 1):
        frozen = enumerate_frontier(
            program, placed, explicit_gap_sites=seed.explicit_gap_sites,
            boundary=boundary, incoming_ports=incoming_ports,
            _occupied_index=occupied_index,
            _existing_poses=existing_poses, _orbit_cache=orbit_cache)
        if not frozen.candidates:
            waves.append(ConsensusWave(
                wave_index, (), 0, 0, 0, 0, 0, 0, 0, 0, True,
                len(occupied_by_key), len(occupied_by_key)))
            break
        identified = tuple((_candidate_id(
            candidate, program.overlap_tolerance), candidate)
            for candidate in frozen.candidates)
        if len({item[0] for item in identified}) != len(identified):
            raise AssertionError("candidate-id digest collision")
        site_support = {}
        for candidate_id, candidate in identified:
            for site in {_site_key(item, program.overlap_tolerance)
                         for item in candidate.novel_sites}:
                site_support.setdefault(site, set()).add(candidate_id)
        minimum_support = {
            candidate_id: min(len(site_support[_site_key(
                site, program.overlap_tolerance)])
                for site in candidate.novel_sites)
            for candidate_id, candidate in identified}
        wave_maximum = max(minimum_support.values())
        normalized = {candidate_id: support / wave_maximum
                      for candidate_id, support in minimum_support.items()}
        ranked = sorted(identified, key=lambda item: (
            -normalized[item[0]], -minimum_support[item[0]], item[0]))
        accepted_this_wave = []
        accepted_sites = list(occupied_by_key.values())
        batch_index = _SpatialSiteIndex(
            accepted_sites, program.exclusion_distance)
        decisions = {}
        below = wave_limit = pair_conflicts = redundant = 0
        for candidate_id, candidate in ranked:
            ratio = normalized[candidate_id]
            if ratio + 1e-15 < threshold_ratio:
                below += 1
                decisions[candidate_id] = (False, "below-threshold")
                continue
            if (maximum_accepted_per_wave is not None and
                    len(accepted_this_wave) >= maximum_accepted_per_wave):
                wave_limit += 1
                decisions[candidate_id] = (False, "wave-limit")
                continue
            _, novel, conflict = batch_index.classify(
                candidate.rendered_sites, program.overlap_tolerance,
                program.exclusion_distance)
            if conflict or not novel:
                if conflict:
                    pair_conflicts += 1
                    decisions[candidate_id] = (False, "pair-conflict")
                else:
                    redundant += 1
                    decisions[candidate_id] = (False, "redundant")
                continue
            accepted_this_wave.append((
                candidate_id, candidate, novel, ratio))
            accepted_sites.extend(novel)
            batch_index.extend(novel)
            decisions[candidate_id] = (True, None)
        before = len(occupied_by_key)
        for candidate_id, candidate, novel, ratio in accepted_this_wave:
            occurrence = ClusterOccurrence(
                len(placed), candidate.child_type,
                candidate.rotation, candidate.translation)
            placed.append(occurrence)
            existing_poses.add(_pose_key(
                occurrence, program.overlap_tolerance))
            new_sites = []
            for site in novel:
                key = _site_key(site, program.overlap_tolerance)
                if key not in occupied_by_key:
                    occupied_by_key[key] = site
                    new_sites.append(site)
            occupied_index.extend(new_sites)
            incoming_ports[occurrence.occurrence_id] = candidate.outgoing_port
            nodes.append(SymbolicConsensusNode(
                occurrence.occurrence_id, occurrence.type_id,
                occurrence.rotation, occurrence.translation, wave_index,
                candidate.parent_occurrence, candidate.production_id,
                candidate_id, ratio))
            accepted_ids.append(candidate_id)
        records = tuple(ConsensusCandidate(
            candidate_id, candidate.parent_occurrence,
            candidate.production_id, candidate.child_type,
            tuple(sorted({_site_key(site, program.overlap_tolerance)
                          for site in candidate.novel_sites})),
            minimum_support[candidate_id], normalized[candidate_id],
            decisions[candidate_id][0], decisions[candidate_id][1])
            for candidate_id, candidate in identified)
        waves.append(ConsensusWave(
            wave_index, records, len(records), wave_maximum,
            sum(normalized[item[0]] + 1e-15 >= threshold_ratio
                for item in identified), len(accepted_this_wave), below,
            wave_limit, pair_conflicts, redundant, True, before,
            len(occupied_by_key)))
        if not accepted_this_wave:
            break
    sites = tuple(occupied_by_key[key] for key in sorted(occupied_by_key))
    return BatchFrontierResult(
        threshold_ratio, initial_sites, sites, tuple(placed), tuple(nodes),
        tuple(waves), tuple(accepted_ids), False)
