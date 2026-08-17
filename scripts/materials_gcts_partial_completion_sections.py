#!/usr/bin/env python3
"""Target-free component-resolved execution of whole macro completions."""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, fit_occurrence_pose, is_proper_rotation, matmul, matvec)
from materials_gcts_partial_completion_executor import (
    PartialCompletionLevel, _classify, _dynamic_program, _full_rhs_sites,
    _minimum_distance, _placement_port_semantic, _pose_key, _render,
    _site_key, _verify_frozen_completion_ports)
from materials_gcts_partial_completion_marking import freeze_completion_candidate
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from materials_gcts_partial_completion_site_policy import (
    FrozenLocalSiteSectionPolicy, score_completion_sections)
from materials_gcts_partial_macro_components import (
    decompose_partial_macro_completion)


Site = tuple[Hashable, tuple[float, float, float]]
PortMark = tuple[str, tuple[str, ...], int]


@dataclass(frozen=True)
class CompletionSectionDescriptor:
    child_count: int
    site_count: int
    incoming_marks: tuple[PortMark, ...]
    internal_marks: tuple[PortMark, ...]
    training_port_evidence: int
    live_overlap_atoms: int
    live_collision_support: int


@dataclass(frozen=True)
class FrozenCompletionSection:
    section_id: str
    whole_candidate_id: str
    macro_id: int
    frozen_parent_type: int | None
    child_nodes: tuple[int, ...]
    sites: tuple[Site, ...]
    descriptor: CompletionSectionDescriptor
    stable_key: tuple
    exact_frozen_geometry: bool
    frozen_port_witnessed: bool


@dataclass(frozen=True)
class CompletionSectionTrace:
    descriptor: CompletionSectionDescriptor
    successful: bool
    learned_from_training_only: bool = True


@dataclass(frozen=True)
class FrozenCompletionSectionMarking:
    scores: tuple[tuple[CompletionSectionDescriptor, float], ...]
    marginal_score: float
    training_samples: int
    target_used: bool = False


@dataclass(frozen=True)
class CompletionSectionCertificate:
    section_id: str
    exact_frozen_component: bool
    proper_se3: bool
    frozen_port_witnessed: bool
    emitted_is_exact_difference: bool
    collision_free: bool
    digest: str


@dataclass(frozen=True)
class CompletionPromotionCertificate:
    macro_id: int
    frozen_parent_type: int
    full_rhs_child_poses_present: bool
    frozen_ports_reverified: bool
    proper_se3: bool
    exact_promoted_fit: bool
    digest: str


@dataclass(frozen=True)
class CompletionSectionWave:
    wave: int
    whole_candidates: int
    whole_candidate_digest: str
    whole_candidate_ids: tuple[str, ...]
    sections: int
    section_digest: str
    section_ids: tuple[str, ...]
    section_scores: tuple[tuple[str, float], ...]
    accepted_section_ids: tuple[str, ...]
    deferred_section_ids: tuple[str, ...]
    accepted_sections: int
    deferred_below_threshold: int
    rejected_conflicts: int
    rejected_redundant: int
    emitted_atoms: int
    appended_children: int
    completed_whole_macros: int


@dataclass(frozen=True)
class CompletionSectionExecution:
    final_occurrences: tuple[ClusterOccurrence, ...]
    promoted_occurrences: tuple[ClusterOccurrence, ...]
    sites: tuple[Site, ...]
    waves: tuple[CompletionSectionWave, ...]
    certificates: tuple[CompletionSectionCertificate, ...]
    promotion_certificates: tuple[CompletionPromotionCertificate, ...]
    whole_candidate_batches_frozen_before_section_marking: bool
    exact_certificates: bool
    self_fed: bool
    target_api_present: bool
    target_used: bool


def fit_completion_section_marking(
    traces: Sequence[CompletionSectionTrace],
) -> FrozenCompletionSectionMarking:
    traces = tuple(traces)
    if not traces or any(not item.learned_from_training_only for item in traces):
        raise ValueError("section marking requires train-only traces")
    counts = {}
    total = Counter()
    for trace in traces:
        counts.setdefault(trace.descriptor, Counter())[trace.successful] += 1
        total[trace.successful] += 1
    scores = tuple(sorted((descriptor,
                           (values[True] + 1) / (sum(values.values()) + 2))
                          for descriptor, values in counts.items()), key=repr)
    return FrozenCompletionSectionMarking(
        scores, (total[True] + 1) / (len(traces) + 2), len(traces), False)


def _port_models(program):
    result = {}
    for kind, ports in (("overlap", getattr(program.atlas, "ports", ())),
                        ("boundary", getattr(program, "boundary_ports", ()))):
        for port in ports:
            semantic = (port.parent_type, port.child_type,
                        port.symmetry_orbit_key)
            mark = (kind,
                    tuple(sorted(map(repr, getattr(port,
                                                   "overlap_species", ())))),
                    getattr(port, "observations",
                            getattr(port, "occurrence_observations", 0)))
            previous = result.get(semantic)
            if previous is None or mark[2] > previous[2]:
                result[semantic] = mark
    return result


def _components(nodes, edges, children, tolerance):
    remaining = set(nodes)
    adjacency = {node: set() for node in remaining}
    for edge in edges:
        if edge.source in remaining and edge.target in remaining:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)
    site_keys = {node: {_site_key(site, tolerance)
                        for site in children[node].sites}
                 for node in remaining}
    coordinate_species = {}
    for keys in site_keys.values():
        for key in keys:
            previous = coordinate_species.setdefault(key[1:], key[0])
            if previous != key[0]:
                raise ValueError("frozen RHS has a colored-site conflict")
    ordered = sorted(remaining)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            if site_keys[left].intersection(site_keys[right]):
                adjacency[left].add(right)
                adjacency[right].add(left)
    result = []
    while remaining:
        root = min(remaining)
        pending = [root]
        component = set()
        while pending:
            node = pending.pop()
            if node in component:
                continue
            component.add(node)
            pending.extend(adjacency[node] - component)
        remaining.difference_update(component)
        result.append(tuple(sorted(component)))
    return tuple(result)


def freeze_completion_sections(program, macro, completion, candidate, *,
                               occupied_sites=(), pose_tolerance=.03):
    """Partition only the missing RHS; the enumerated parent remains whole."""
    models = _port_models(program)
    placements = {item.node: item for item in macro.child_placements}
    children = {item.node: item for item in completion.missing_children}
    matched = set(completion.matched_nodes)
    exclusion = max(pose_tolerance, _minimum_distance(program) * .45)
    decomposition = decompose_partial_macro_completion(
        program, macro, completion, pose_tolerance=pose_tolerance)
    if not decomposition.complete_cover:
        raise ValueError("partial macro decomposition lost frozen RHS sites")
    component_nodes = tuple(
        item.child_nodes for item in
        (*decomposition.emission_components,
         *decomposition.residual_subclusters))
    result = []
    for nodes in sorted(component_nodes):
        node_set = set(nodes)
        incoming = []
        internal = []
        valid = True
        for edge in getattr(macro, "edges", ()):
            if edge.source not in placements or edge.target not in placements:
                valid = False
                continue
            semantic = _placement_port_semantic(
                placements[edge.source], placements[edge.target],
                {item.type_id: item for item in program.prototypes},
                pose_tolerance)
            if semantic != tuple(edge.port) or semantic not in models:
                valid = False
                continue
            if edge.source in matched and edge.target in node_set:
                incoming.append(models[semantic])
            if edge.source in node_set and edge.target in node_set:
                internal.append(models[semantic])
        for slot in getattr(macro, "boundary_slots", ()):
            if (slot.node not in matched or slot.direction != "outgoing" or
                    tuple(slot.port) not in models or
                    slot.occurrence_support <= 0):
                continue
            for node in nodes:
                target = placements[node]
                if target.cluster_type != slot.outside_type:
                    continue
                semantic = _placement_port_semantic(
                    placements[slot.node], target,
                    {item.type_id: item for item in program.prototypes},
                    pose_tolerance)
                if semantic == tuple(slot.port):
                    incoming.append(models[semantic])
        sites_by_key = {}
        for node in nodes:
            for site in children[node].sites:
                sites_by_key.setdefault(_site_key(site, pose_tolerance), site)
        sites = tuple(sites_by_key[key] for key in sorted(sites_by_key))
        emitted, overlap, collision = _classify(
            sites, tuple(occupied_sites), pose_tolerance, exclusion)
        evidence = sum(item[2] for item in (*incoming, *internal))
        descriptor = CompletionSectionDescriptor(
            len(nodes), len(sites), tuple(sorted(incoming, key=repr)),
            tuple(sorted(internal, key=repr)), evidence, overlap,
            int(collision))
        payload = (candidate.candidate_id, nodes,
                   tuple(sorted(_site_key(site, pose_tolerance)
                                for site in sites)))
        section_id = hashlib.sha256(repr(payload).encode()).hexdigest()
        result.append(FrozenCompletionSection(
            section_id, candidate.candidate_id, completion.macro_id,
            completion.frozen_parent_type, nodes, sites, descriptor,
            (int(collision), -evidence, -overlap, nodes, section_id),
            completion.exact_frozen_rhs_geometry and valid,
            valid and bool(incoming)))
    return tuple(result)


def execute_partial_completion_sections(
    level: PartialCompletionLevel,
    seed_occurrences: Sequence[ClusterOccurrence], *,
    explicit_seed_sites: Sequence[Site] = (), public_boundary=None,
    marking: FrozenCompletionSectionMarking | FrozenLocalSiteSectionPolicy |
    None = None,
    minimum_marking_score: float = 0., maximum_waves: int = 3,
    maximum_accepted_per_wave: int = 32,
    minimum_child_coverage: float = 0., pose_tolerance: float = .03,
) -> CompletionSectionExecution:
    if (not seed_occurrences or maximum_waves < 0 or
            maximum_accepted_per_wave < 1 or
            not math.isfinite(minimum_marking_score)):
        raise ValueError("invalid section execution controls")
    if marking is not None and marking.target_used:
        raise ValueError("target-tainted section marking is forbidden")
    frozen = level.frozen_lower_program
    prototypes = {item.type_id: item for item in frozen.prototypes}
    promoted_prototypes = {item.type_id: item
                           for item in level.promoted_program.prototypes}
    macros = {item.macro_id: item for item in level.alternatives}
    parents = dict(level.alternative_parent_types)
    occurrences = list(seed_occurrences)
    occupied = {}
    for occurrence in occurrences:
        if occurrence.type_id not in prototypes or not is_proper_rotation(
                occurrence.rotation):
            raise ValueError("invalid frozen seed occurrence")
        for site in _render(prototypes[occurrence.type_id],
                            occurrence.rotation, occurrence.translation):
            occupied.setdefault(_site_key(site, pose_tolerance), site)
    for species, point in explicit_seed_sites:
        site = species, tuple(map(float, point))
        occupied.setdefault(_site_key(site, pose_tolerance), site)
    promoted = []
    promoted_pose_keys = set()
    certificates = []
    promotion_certificates = []
    waves = []
    exclusion = max(pose_tolerance, _minimum_distance(frozen) * .45)
    descriptor_scores = (dict(marking.scores)
                         if isinstance(marking,
                                       FrozenCompletionSectionMarking) else {})
    marginal = (marking.marginal_score
                if isinstance(marking, FrozenCompletionSectionMarking) else 0.)
    for wave_index in range(1, maximum_waves + 1):
        dynamic = _dynamic_program(frozen, occurrences, pose_tolerance)
        frontier = enumerate_partial_promoted_completions(
            dynamic, level.alternatives, minimum_matched_children=1,
            minimum_child_coverage=minimum_child_coverage,
            explicit_seed_sites=tuple(occupied.values()),
            public_boundary=public_boundary,
            frozen_parent_types=level.alternative_parent_types,
            pose_tolerance=pose_tolerance)
        candidates = []
        completion_by_candidate = {}
        sections = []
        site_policy_scores = {}
        for completion in frontier.completions:
            missing_sites = tuple(site for child in completion.missing_children
                                  for site in child.sites)
            _emitted, overlap, collision = _classify(
                missing_sites, tuple(occupied.values()), pose_tolerance,
                exclusion)
            candidate = freeze_completion_candidate(
                dynamic, macros[completion.macro_id], completion,
                live_overlap_support=overlap,
                live_collision_support=int(collision),
                pose_tolerance=pose_tolerance)
            candidates.append(candidate)
            completion_by_candidate[candidate.candidate_id] = completion
            generated = freeze_completion_sections(
                dynamic, macros[completion.macro_id], completion, candidate,
                occupied_sites=tuple(occupied.values()),
                pose_tolerance=pose_tolerance)
            sections.extend(generated)
            if isinstance(marking, FrozenLocalSiteSectionPolicy):
                site_policy_scores.update(
                    (item.section_id, item.aggregate_score) for item in
                    score_completion_sections(
                        marking, generated, dynamic,
                        macros[completion.macro_id], completion, candidate,
                        tuple(occupied.values()), pose_tolerance))
        if len({item.section_id for item in sections}) != len(sections):
            raise AssertionError("section action IDs are not unique")
        whole_ids = tuple(sorted(item.candidate_id for item in candidates))
        section_ids = tuple(sorted(item.section_id for item in sections))
        whole_digest = hashlib.sha256(repr(whole_ids).encode()).hexdigest()
        section_digest = hashlib.sha256(repr(section_ids).encode()).hexdigest()
        def section_score(item):
            if isinstance(marking, FrozenLocalSiteSectionPolicy):
                return site_policy_scores.get(item.section_id, -math.inf)
            return descriptor_scores.get(item.descriptor, marginal)
        ordered = sorted(sections, key=lambda item: (
            -section_score(item), item.stable_key))
        accepted = deferred = conflicts = redundant = emitted_count = 0
        appended = completed = 0
        accepted_ids = []
        deferred_ids = []
        batch_sites = dict(occupied)
        touched_candidates = set()
        for section in ordered:
            score = section_score(section)
            if score < minimum_marking_score:
                deferred += 1
                deferred_ids.append(section.section_id)
                continue
            if accepted >= maximum_accepted_per_wave:
                deferred += 1
                deferred_ids.append(section.section_id)
                continue
            if not section.exact_frozen_geometry or not section.frozen_port_witnessed:
                conflicts += 1
                continue
            emitted, _overlap, collision = _classify(
                section.sites, tuple(batch_sites.values()), pose_tolerance,
                exclusion)
            if collision:
                conflicts += 1
                continue
            if not emitted:
                redundant += 1
                continue
            completion = completion_by_candidate[section.whole_candidate_id]
            missing_by_node = {item.node: item
                               for item in completion.missing_children}
            existing = {_pose_key(item.type_id, item.rotation,
                                  item.translation, pose_tolerance)
                        for item in occurrences}
            section_appended = 0
            for node in section.child_nodes:
                child = missing_by_node[node]
                pose = _pose_key(child.type_id, child.rotation,
                                 child.translation, pose_tolerance)
                if pose not in existing:
                    occurrences.append(ClusterOccurrence(
                        len(occurrences), child.type_id,
                        child.rotation, child.translation))
                    existing.add(pose)
                    section_appended += 1
            before = set(batch_sites)
            for site in emitted:
                batch_sites[_site_key(site, pose_tolerance)] = site
            payload = (section.section_id,
                       tuple(sorted(_site_key(site, pose_tolerance)
                                    for site in emitted)))
            certificates.append(CompletionSectionCertificate(
                section.section_id, True,
                is_proper_rotation(completion.macro_rotation), True,
                all(_site_key(site, pose_tolerance) not in before
                    for site in emitted), not collision,
                hashlib.sha256(repr(payload).encode()).hexdigest()))
            accepted += 1
            accepted_ids.append(section.section_id)
            appended += section_appended
            emitted_count += len(emitted)
            touched_candidates.add(section.whole_candidate_id)
        # Preserve hierarchy: only a complete exact RHS becomes a parent node.
        existing_poses = {_pose_key(item.type_id, item.rotation,
                                    item.translation, pose_tolerance)
                          for item in occurrences}
        for candidate_id in sorted(touched_candidates):
            completion = completion_by_candidate[candidate_id]
            macro = macros[completion.macro_id]
            expected = []
            for placement in macro.child_placements:
                rotation = matmul(completion.macro_rotation,
                                  placement.rotation)
                shifted = matvec(completion.macro_rotation,
                                 placement.translation)
                translation = tuple(completion.macro_translation[axis] +
                                    shifted[axis] for axis in range(3))
                expected.append(_pose_key(placement.cluster_type, rotation,
                                          translation, pose_tolerance))
            all_children_present = all(item in existing_poses
                                       for item in expected)
            if not all_children_present or not _verify_frozen_completion_ports(
                    frozen, macro, completion, prototypes, pose_tolerance):
                continue
            full_sites = _full_rhs_sites(completion, macro, prototypes)
            parent_type = parents[completion.macro_id]
            try:
                fitted = fit_occurrence_pose(
                    len(promoted), promoted_prototypes[parent_type], full_sites,
                    tolerance=pose_tolerance)
            except ValueError:
                continue
            pose = _pose_key(parent_type, fitted.rotation, fitted.translation,
                             pose_tolerance)
            if pose not in promoted_pose_keys:
                promoted.append(ClusterOccurrence(
                    len(promoted), parent_type, fitted.rotation,
                    fitted.translation))
                promoted_pose_keys.add(pose)
                completed += 1
                payload = (completion.macro_id, parent_type, pose,
                           tuple(sorted(expected, key=repr)))
                promotion_certificates.append(CompletionPromotionCertificate(
                    completion.macro_id, parent_type, True, True,
                    is_proper_rotation(fitted.rotation), True,
                    hashlib.sha256(repr(payload).encode()).hexdigest()))
        occupied = batch_sites
        waves.append(CompletionSectionWave(
            wave_index, len(candidates), whole_digest, whole_ids,
            len(sections), section_digest, section_ids,
            tuple(sorted((item.section_id, section_score(item))
                         for item in sections)),
            tuple(accepted_ids), tuple(deferred_ids),
            accepted, deferred, conflicts, redundant,
            emitted_count, appended, completed))
        if not accepted:
            break
    exact = all(all((item.exact_frozen_component, item.proper_se3,
                     item.frozen_port_witnessed,
                     item.emitted_is_exact_difference,
                     item.collision_free)) for item in certificates)
    exact &= all(all((item.full_rhs_child_poses_present,
                      item.frozen_ports_reverified, item.proper_se3,
                      item.exact_promoted_fit))
                 for item in promotion_certificates)
    if not exact:
        raise AssertionError("section certificate failed")
    return CompletionSectionExecution(
        tuple(occurrences), tuple(promoted),
        tuple(occupied[key] for key in sorted(occupied)), tuple(waves),
        tuple(certificates), tuple(promotion_certificates), True, exact,
        len(waves) > 1 and any(item.appended_children
                               for item in waves[:-1]), False, False)
