#!/usr/bin/env python3
"""Target-blind self-fed execution of a frozen recurrent macro program."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_macro_derivation import (
    FrozenMacroProduction, OverlapInclusionCertificate, Site, SiteKey,
    SymbolicMacroNode, _Candidate, _SpatialSiteIndex, _add, _certificate,
    _classify, _compile_productions, _pose_key, _production_ports, _render,
    _site_key, _unique_sites)
from materials_gcts_macro_promotion import PromotedMacroProgram
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, Matrix, Vector, expand_port_orbit,
    is_proper_rotation, matmul, matvec)


@dataclass(frozen=True)
class ExecutionBoundary:
    origin: Vector
    outer_radius: float


@dataclass(frozen=True)
class FrozenExecutionPolicy:
    strategy: str = "overlap-first"
    minimum_consensus_ratio: float = 0.
    maximum_incoming_context: int = 2
    marking_scores: tuple[
        tuple[tuple[int, int, tuple[int, ...]], float], ...] = ()


@dataclass(frozen=True)
class RecurrentCandidateTrace:
    wave: int
    phase: str
    candidate_id: str
    parent_node: int
    production_id: int
    production_kind: str
    child_type: int
    overlap_atoms: int
    emitted_atoms: int
    decision: str
    marking_context: tuple[int, ...] = ()
    marking_score: float = 0.


@dataclass(frozen=True)
class AcceptedMacroPlacement:
    wave: int
    candidate_id: str
    node: SymbolicMacroNode
    certificate: OverlapInclusionCertificate


@dataclass(frozen=True)
class EligibleMacroCandidate:
    wave: int
    candidate_id: str
    parent_node: int
    parent_type: int
    production_id: int
    production_kind: str
    child_type: int
    marking_context: tuple[int, ...]
    marking_score: float
    overlap_atoms: int
    emitted_site_keys: tuple[SiteKey, ...]


@dataclass(frozen=True)
class RecurrentMacroWave:
    wave: int
    frontier_nodes: int
    eligible_candidates: int
    accepted_placements: int
    emitted_atoms: int
    atoms_after: int
    candidate_digest: str


@dataclass(frozen=True)
class RecurrentMacroExecution:
    policy: FrozenExecutionPolicy
    frozen_productions: tuple[FrozenMacroProduction, ...]
    seed_occurrences: int
    seed_sites: tuple[Site, ...]
    nodes: tuple[SymbolicMacroNode, ...]
    accepted: tuple[AcceptedMacroPlacement, ...]
    eligible_candidates: tuple[EligibleMacroCandidate, ...]
    waves: tuple[RecurrentMacroWave, ...]
    trace: tuple[RecurrentCandidateTrace, ...]
    sites: tuple[Site, ...]
    attempted_port_poses: int
    rejected_duplicate_poses: int
    rejected_outside_boundary: int
    rejected_colored_collisions: int
    rejected_insufficient_overlap: int
    rejected_commit_conflicts: int
    deferred_by_wave_cap: int
    rejection_trace_complete: bool
    exhausted: bool
    longest_parent_child_depth: int
    reachable_fixed_point: bool
    stopped_by_wave_limit: bool
    self_fed: bool
    exact_certificates: bool
    target_used_for_proposals_or_ranking: bool


@dataclass(frozen=True)
class RecurrentMacroScore:
    target_atoms: int
    target_atoms_outside_seed: int
    proposed_novel_atoms: int
    correct_novel_atoms: int
    wrong_novel_atoms: int
    precision: float
    recall_outside_seed: float
    target_used_for_proposals_or_ranking: bool


def _candidate_id(
    wave: int, parent: int, production: int, child: int,
    rotation: Matrix, translation: Vector, tolerance: float,
) -> str:
    identity = (wave, parent, production,
                _pose_key(child, rotation, translation, tolerance))
    return hashlib.sha256(repr(identity).encode("utf-8")).hexdigest()


def _validate_boundary(boundary: ExecutionBoundary | None) -> None:
    if boundary is None:
        return
    if (boundary.outer_radius <= 0 or
            not math.isfinite(boundary.outer_radius) or
            len(boundary.origin) != 3 or
            not all(math.isfinite(value) for value in boundary.origin)):
        raise ValueError("execution boundary must be a finite positive ball")


def execute_recurrent_macro_program(
    program: PromotedMacroProgram,
    seed_occurrences: Sequence[ClusterOccurrence], *,
    explicit_seed_sites: Sequence[Site] = (),
    boundary: ExecutionBoundary | None = None,
    maximum_waves: int = 2,
    maximum_accepted_per_wave: int = 64,
    pose_tolerance: float = .03,
    policy: FrozenExecutionPolicy = FrozenExecutionPolicy(),
    trace_rejections: bool = True,
) -> RecurrentMacroExecution:
    """Compose only train-frozen ports from the already placed frontier.

    There is deliberately no target argument or ranker callback.  The fixed
    ordering uses frozen port evidence and exact live overlap only.  A target
    can enter solely through :func:`score_recurrent_macro_execution` after the
    returned execution is immutable.
    """
    if not seed_occurrences:
        raise ValueError("at least one frozen macro seed is required")
    if maximum_waves < 0 or maximum_accepted_per_wave < 1:
        raise ValueError("invalid execution limits")
    if pose_tolerance <= 0 or not math.isfinite(pose_tolerance):
        raise ValueError("pose tolerance must be finite and positive")
    _validate_boundary(boundary)
    if (policy.strategy not in {
            "overlap-first", "evidence-first", "consensus",
            "causal-marking"} or
            not 0 <= policy.minimum_consensus_ratio <= 1 or
            not 0 <= policy.maximum_incoming_context <= 2):
        raise ValueError("unknown or invalid frozen execution policy")
    marking_scores = dict(policy.marking_scores)
    if (len(marking_scores) != len(policy.marking_scores) or
            any(not math.isfinite(value) for value in marking_scores.values())):
        raise ValueError("frozen marking table has duplicate or invalid scores")
    prototypes = {item.type_id: item for item in program.prototypes}
    productions = _compile_productions(program)
    port_geometry = _production_ports(program)
    by_parent = {}
    for production in productions:
        by_parent.setdefault(production.parent_type, []).append(production)

    nodes = []
    for occurrence in seed_occurrences:
        if (occurrence.type_id not in prototypes or
                not is_proper_rotation(occurrence.rotation)):
            raise ValueError("seed uses an unknown type or improper pose")
        nodes.append(SymbolicMacroNode(
            len(nodes), occurrence.type_id, occurrence.rotation,
            occurrence.translation, 0, None, None))
    occupied_list = list(_unique_sites(tuple(
        site for node in nodes for site in _render(
            prototypes[node.macro_type], node.rotation, node.translation)),
        pose_tolerance))
    exclusion = max(pose_tolerance, program.minimum_distance * .45)
    for species, raw_point in explicit_seed_sites:
        point = tuple(float(value) for value in raw_point)
        if len(point) != 3 or not all(math.isfinite(value) for value in point):
            raise ValueError("explicit seed sites need finite 3D coordinates")
        site: Site = (species, point)  # type: ignore[assignment]
        _overlap, emitted, invalid = _classify(
            (site,), occupied_list, pose_tolerance, exclusion)
        if invalid:
            raise ValueError("explicit seed site conflicts with macro seed")
        occupied_list.extend(emitted)
    occupied = _unique_sites(occupied_list, pose_tolerance)
    occupied_index = _SpatialSiteIndex(occupied, exclusion)
    occupied_by_coordinate = {
        tuple(round(value / pose_tolerance) for value in site[1]): site
        for site in occupied}
    occupied_species = {key: site[0]
                        for key, site in occupied_by_coordinate.items()}
    occupied_keys = {_site_key(site, pose_tolerance) for site in occupied}
    seed_sites = occupied
    existing_poses = {_pose_key(node.macro_type, node.rotation,
                                node.translation, pose_tolerance)
                      for node in nodes}
    orbit_cache = {}
    node_context = {}
    frontier = tuple(nodes)
    trace = []

    def record(event: RecurrentCandidateTrace) -> None:
        if trace_rejections or event.phase == "commit":
            trace.append(event)
    accepted = []
    eligible_snapshots = []
    waves = []
    attempted = duplicate = outside = collision = insufficient = commit = 0
    cap_deferred = 0
    exhausted = False
    for wave in range(1, maximum_waves + 1):
        eligible = {}
        incident_context = {}
        for parent in frontier:
            incident = []
            parent_pose = _pose_key(parent.macro_type, parent.rotation,
                                    parent.translation, pose_tolerance)
            for production in by_parent.get(parent.macro_type, ()):
                child_prototype = prototypes[production.child_type]
                orbit = orbit_cache.get(production.production_id)
                if orbit is None:
                    orbit = expand_port_orbit(
                        prototypes[production.parent_type], child_prototype,
                        port_geometry[production.production_id],
                        pose_tolerance)
                    orbit_cache[production.production_id] = orbit
                for relative_rotation, relative_translation in orbit:
                    rotation = matmul(parent.rotation, relative_rotation)
                    translation = _add(parent.translation, matvec(
                        parent.rotation, relative_translation))
                    pose = _pose_key(production.child_type, rotation,
                                     translation, pose_tolerance)
                    if pose != parent_pose and pose in existing_poses:
                        incident.append(production.production_id)
            incident_context[parent.node_id] = tuple(sorted(incident))[
                :policy.maximum_incoming_context]
            node_context.setdefault(parent.node_id,
                                    incident_context[parent.node_id])
        for parent in frontier:
            for production in by_parent.get(parent.macro_type, ()):
                child_prototype = prototypes[production.child_type]
                orbit = orbit_cache.get(production.production_id)
                if orbit is None:
                    orbit = expand_port_orbit(
                        prototypes[production.parent_type], child_prototype,
                        port_geometry[production.production_id],
                        pose_tolerance)
                    orbit_cache[production.production_id] = orbit
                for relative_rotation, relative_translation in orbit:
                    attempted += 1
                    rotation = matmul(parent.rotation, relative_rotation)
                    translation = _add(parent.translation, matvec(
                        parent.rotation, relative_translation))
                    candidate_id = _candidate_id(
                        wave, parent.node_id, production.production_id,
                        production.child_type, rotation, translation,
                        pose_tolerance)
                    pose = _pose_key(production.child_type, rotation,
                                     translation, pose_tolerance)
                    common = (wave, "enumerate", candidate_id,
                              parent.node_id, production.production_id,
                              production.production_kind,
                              production.child_type)
                    if pose in existing_poses:
                        duplicate += 1
                        record(RecurrentCandidateTrace(
                            *common, 0, 0, "duplicate-pose"))
                        continue
                    rendered = _render(child_prototype, rotation, translation)
                    if boundary is not None and any(
                            math.dist(point, boundary.origin) >
                            boundary.outer_radius + pose_tolerance
                            for _, point in rendered):
                        outside += 1
                        record(RecurrentCandidateTrace(
                            *common, 0, 0, "outside-public-boundary"))
                        continue
                    overlap, emitted, invalid = occupied_index.classify(
                        rendered, pose_tolerance, exclusion)
                    if invalid:
                        collision += 1
                        record(RecurrentCandidateTrace(
                            *common, len(overlap), 0,
                            "colored-or-exclusion-collision"))
                        continue
                    if len(overlap) < production.required_shared_atoms:
                        insufficient += 1
                        record(RecurrentCandidateTrace(
                            *common, len(overlap), len(emitted),
                            "insufficient-required-overlap"))
                        continue
                    if not emitted:
                        duplicate += 1
                        record(RecurrentCandidateTrace(
                            *common, len(overlap), 0, "interior-duplicate"))
                        continue
                    candidate = _Candidate(
                        parent.node_id, production.production_id,
                        production.child_type, rotation, translation,
                        rendered, overlap, emitted)
                    rendered_key = tuple(sorted(
                        _site_key(site, pose_tolerance) for site in rendered))
                    ranking = (production.production_id, candidate_id)
                    prior = eligible.get(rendered_key)
                    if prior is None or ranking < prior[0]:
                        if prior is not None:
                            duplicate += 1
                            old = prior[2]
                            record(RecurrentCandidateTrace(
                                wave, "enumerate", old, prior[1].parent_node,
                                prior[1].production_id,
                                productions[prior[1].production_id].production_kind,
                                prior[1].child_type, len(prior[1].overlap),
                                len(prior[1].emitted), "duplicate-rendered-union"))
                        witnesses = ({(parent.node_id,
                                       production.production_id)} if prior is None
                                     else set(prior[3]) | {(parent.node_id,
                                                           production.production_id)})
                        eligible[rendered_key] = (
                            ranking, candidate, candidate_id, witnesses)
                    else:
                        prior[3].add((parent.node_id,
                                      production.production_id))
                        duplicate += 1
                        record(RecurrentCandidateTrace(
                            *common, len(overlap), len(emitted),
                            "duplicate-rendered-union"))
        eligible_values = tuple(eligible.values())
        candidate_digest = hashlib.sha256(repr(tuple(sorted(
            item[2] for item in eligible_values))).encode("utf-8")).hexdigest()
        site_support = {}
        for _ranking, candidate, candidate_id, _witnesses in eligible_values:
            for site in {_site_key(item, pose_tolerance)
                         for item in candidate.emitted}:
                site_support.setdefault(site, set()).add(candidate_id)
        maximum_support = max((len(value) for value in site_support.values()),
                              default=1)

        def policy_key(item):
            _ranking, candidate, candidate_id, _witnesses = item
            production = productions[candidate.production_id]
            evidence = (production.training_observations +
                        production.training_child_port_witnesses)
            emitted_keys = {_site_key(site, pose_tolerance)
                            for site in candidate.emitted}
            consensus = min((len(site_support[key]) for key in emitted_keys),
                            default=0)
            stable = (production.production_kind != "overlap",
                      production.production_id, candidate_id)
            parent_node = nodes[candidate.parent_node]
            context = node_context[candidate.parent_node]
            if policy.strategy == "causal-marking":
                key = (parent_node.macro_type,
                       candidate.production_id, context)
                backoff = (parent_node.macro_type,
                           candidate.production_id, ())
                score = marking_scores.get(
                    key, marking_scores.get(backoff, 0.))
                return (-score, -len(candidate.overlap),
                        -len(candidate.emitted), -evidence, *stable)
            if policy.strategy == "evidence-first":
                return (-evidence, -len(candidate.overlap),
                        -len(candidate.emitted), *stable)
            if policy.strategy == "consensus":
                return (-consensus, -evidence, -len(candidate.overlap),
                        -len(candidate.emitted), *stable)
            return (-len(candidate.overlap), -len(candidate.emitted),
                    -evidence, *stable)

        ordered = sorted(eligible_values, key=policy_key)
        accepted_nodes = []
        wave_emitted = 0
        candidate_marking = {}
        for item in ordered:
            _ranking, candidate, candidate_id, _witnesses = item
            key = (nodes[candidate.parent_node].macro_type,
                   candidate.production_id,
                   node_context[candidate.parent_node])
            backoff = (key[0], key[1], ())
            candidate_marking[candidate_id] = (
                key[2], marking_scores.get(
                    key, marking_scores.get(backoff, 0.)))
            context, score = candidate_marking[candidate_id]
            production = productions[candidate.production_id]
            eligible_snapshots.append(EligibleMacroCandidate(
                wave, candidate_id, candidate.parent_node,
                nodes[candidate.parent_node].macro_type,
                candidate.production_id, production.production_kind,
                candidate.child_type, context, score,
                len(candidate.overlap), tuple(sorted(
                    _site_key(site, pose_tolerance)
                    for site in candidate.emitted))))
        for _ranking, candidate, candidate_id, witnesses in ordered:
            context, marking_score = candidate_marking[candidate_id]
            emitted_keys = {_site_key(site, pose_tolerance)
                            for site in candidate.emitted}
            consensus = min((len(site_support[key]) for key in emitted_keys),
                            default=0)
            if (policy.strategy == "consensus" and
                    consensus / maximum_support <
                    policy.minimum_consensus_ratio):
                record(RecurrentCandidateTrace(
                    wave, "commit", candidate_id, candidate.parent_node,
                    candidate.production_id,
                    productions[candidate.production_id].production_kind,
                    candidate.child_type, len(candidate.overlap),
                    len(candidate.emitted), "below-frozen-consensus",
                    context, marking_score))
                continue
            if len(accepted_nodes) >= maximum_accepted_per_wave:
                cap_deferred += 1
                record(RecurrentCandidateTrace(
                    wave, "commit", candidate_id, candidate.parent_node,
                    candidate.production_id,
                    productions[candidate.production_id].production_kind,
                    candidate.child_type, len(candidate.overlap),
                    len(candidate.emitted), "wave-cap", context,
                    marking_score))
                continue
            overlap, emitted, invalid = occupied_index.classify(
                candidate.rendered, pose_tolerance, exclusion)
            production = productions[candidate.production_id]
            if (invalid or len(overlap) < production.required_shared_atoms or
                    not emitted):
                commit += 1
                record(RecurrentCandidateTrace(
                    wave, "commit", candidate_id, candidate.parent_node,
                    candidate.production_id, production.production_kind,
                    candidate.child_type, len(overlap), len(emitted),
                    "commit-conflict", context, marking_score))
                continue
            node = SymbolicMacroNode(
                len(nodes), candidate.child_type, candidate.rotation,
                candidate.translation, wave, candidate.parent_node,
                candidate.production_id)
            committed = _Candidate(
                candidate.parent_node, candidate.production_id,
                candidate.child_type, candidate.rotation,
                candidate.translation, candidate.rendered, overlap, emitted)
            certificate = _certificate(
                committed, node.node_id, production, occupied,
                pose_tolerance, occupied_keys_before=occupied_keys)
            if not (certificate.overlap_is_subset and
                    certificate.emitted_is_exact_difference and
                    certificate.adjacency_witnessed_in_training):
                raise AssertionError("invalid frozen-port certificate")
            new_sites = []
            for site in emitted:
                coordinate = tuple(round(value / pose_tolerance)
                                   for value in site[1])
                if (coordinate in occupied_species and
                        occupied_species[coordinate] != site[0]):
                    raise AssertionError("commit created unlike-color overlap")
                if coordinate not in occupied_by_coordinate:
                    occupied_by_coordinate[coordinate] = site
                    occupied_species[coordinate] = site[0]
                    occupied_keys.add(_site_key(site, pose_tolerance))
                    new_sites.append(site)
            occupied_index.extend(new_sites)
            existing_poses.add(_pose_key(
                node.macro_type, node.rotation, node.translation,
                pose_tolerance))
            nodes.append(node)
            node_context[node.node_id] = tuple(sorted({
                production_id for _parent_id, production_id in witnesses
            }))[:policy.maximum_incoming_context]
            accepted_nodes.append(node)
            accepted.append(AcceptedMacroPlacement(
                wave, candidate_id, node, certificate))
            wave_emitted += len(new_sites)
            record(RecurrentCandidateTrace(
                wave, "commit", candidate_id, candidate.parent_node,
                candidate.production_id, production.production_kind,
                candidate.child_type, len(overlap), len(new_sites), "accepted",
                context, marking_score))
        occupied = tuple(occupied_by_coordinate[key]
                         for key in sorted(occupied_by_coordinate))
        waves.append(RecurrentMacroWave(
            wave, len(frontier), len(ordered), len(accepted_nodes),
            wave_emitted, len(occupied), candidate_digest))
        frontier = tuple(accepted_nodes)
        if not frontier:
            exhausted = True
            break
    exact = all(
        item.certificate.overlap_is_subset and
        item.certificate.emitted_is_exact_difference and
        item.certificate.adjacency_witnessed_in_training and
        item.certificate.conflicting_sites == 0 for item in accepted)
    longest_depth = max((node.depth for node in nodes), default=0)
    fixed_point = exhausted and cap_deferred == 0
    return RecurrentMacroExecution(
        policy, productions, len(seed_occurrences), seed_sites, tuple(nodes),
        tuple(accepted), tuple(eligible_snapshots), tuple(waves),
        tuple(trace), occupied, attempted,
        duplicate, outside, collision, insufficient, commit, cap_deferred,
        trace_rejections, exhausted, longest_depth, fixed_point,
        not exhausted,
        True, exact, False)


def _matched_indices(source: Sequence[Site], target: Sequence[Site],
                     tolerance: float, *, excluded: set[int] | None = None,
                     ) -> set[int]:
    unmatched = set(range(len(target))).difference(excluded or ())
    matched = set()
    for species, point in source:
        choices = [index for index in unmatched
                   if target[index][0] == species and
                   math.dist(point, target[index][1]) <= tolerance]
        if choices:
            chosen = min(choices, key=lambda index:
                         math.dist(point, target[index][1]))
            unmatched.remove(chosen)
            matched.add(chosen)
    return matched


def score_recurrent_macro_execution(
    execution: RecurrentMacroExecution,
    target_species: Sequence[Hashable],
    target_positions: Sequence[Sequence[float]], *, tolerance: float = .03,
) -> RecurrentMacroScore:
    """Post-hoc scorer; it cannot alter an already returned execution."""
    if len(target_species) != len(target_positions) or tolerance <= 0:
        raise ValueError("invalid scorer input")
    target = tuple((species, tuple(float(value) for value in point))
                   for species, point in zip(target_species, target_positions))
    seed_matches = _matched_indices(execution.seed_sites, target, tolerance)
    seed_keys = {_site_key(site, tolerance) for site in execution.seed_sites}
    proposed = tuple(site for site in execution.sites
                     if _site_key(site, tolerance) not in seed_keys)
    proposed_matches = _matched_indices(
        proposed, target, tolerance, excluded=seed_matches)
    correct = len(proposed_matches)
    heldout = len(target) - len(seed_matches)
    return RecurrentMacroScore(
        len(target), heldout, len(proposed), correct,
        len(proposed) - correct, correct / max(1, len(proposed)),
        correct / max(1, heldout),
        execution.target_used_for_proposals_or_ranking)
