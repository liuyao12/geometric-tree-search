#!/usr/bin/env python3
"""Target-free execution of thresholded site masks within frozen macro sections."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, fit_occurrence_pose, is_proper_rotation, matmul, matvec)
from materials_gcts_partial_completion_executor import (
    PartialCompletionLevel, _classify, _dynamic_program, _full_rhs_sites,
    _minimum_distance, _pose_key, _render, _site_key,
    _verify_frozen_completion_ports)
from materials_gcts_partial_completion_marking import freeze_completion_candidate
from materials_gcts_partial_completion_sections import freeze_completion_sections
from materials_gcts_partial_completion_site_policy import (
    FrozenLocalSiteSectionPolicy, score_completion_sections)
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from materials_gcts_partial_site_accumulation import (
    initialize_partial_site_accumulation)


Site = tuple[Hashable, tuple[float, float, float]]


@dataclass(frozen=True)
class DeferredSiteResidual:
    site_key: tuple
    site: Site
    maximum_frozen_score: float
    witness_actions: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class AcceptedSiteCertificate:
    site_key: tuple
    exact_frozen_rhs_site: bool
    proper_se3_candidate: bool
    conflict_free: bool
    witness_actions: tuple[str, ...]
    digest: str


@dataclass(frozen=True)
class CompletedChildCertificate:
    pose_key: tuple
    exact_support_site_keys: tuple[tuple, ...]
    every_exact_site_present: bool
    proper_se3: bool
    digest: str


@dataclass(frozen=True)
class CompletedParentCertificate:
    pose_key: tuple
    all_child_poses_present: bool
    frozen_ports_reverified: bool
    proper_se3: bool
    exact_promoted_fit: bool
    digest: str


@dataclass(frozen=True)
class SiteMaskWave:
    wave: int
    whole_candidate_ids: tuple[str, ...]
    whole_candidate_digest: str
    section_ids: tuple[str, ...]
    section_digest: str
    proposed_novel_site_keys: tuple[tuple, ...]
    proposed_site_digest: str
    accepted_site_keys: tuple[tuple, ...]
    deferred_residuals: tuple[DeferredSiteResidual, ...]
    already_present_site_keys: tuple[tuple, ...]
    completed_children: int
    completed_parents: int
    complete_cover_accounted: bool


@dataclass(frozen=True)
class SiteMaskExecution:
    final_occurrences: tuple[ClusterOccurrence, ...]
    promoted_occurrences: tuple[ClusterOccurrence, ...]
    sites: tuple[Site, ...]
    waves: tuple[SiteMaskWave, ...]
    final_deferred_residuals: tuple[DeferredSiteResidual, ...]
    accepted_site_certificates: tuple[AcceptedSiteCertificate, ...]
    child_certificates: tuple[CompletedChildCertificate, ...]
    parent_certificates: tuple[CompletedParentCertificate, ...]
    frozen_site_threshold: float
    duplicate_site_witness_aggregation: str
    candidate_sections_frozen_before_site_scores: bool
    exact_certificates: bool
    self_fed: bool
    target_api_present: bool
    target_used: bool


def _add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def execute_partial_completion_site_masks(
    level: PartialCompletionLevel,
    seed_occurrences: Sequence[ClusterOccurrence], *,
    site_policy: FrozenLocalSiteSectionPolicy,
    explicit_seed_sites: Sequence[Site] = (), public_boundary=None,
    maximum_waves: int = 3, minimum_child_coverage: float = 0.,
    pose_tolerance: float = .03,
) -> SiteMaskExecution:
    """Commit a site union; child and parent nodes remain exact all-or-none."""
    if (not seed_occurrences or site_policy.target_used or
            site_policy.candidate_id_or_global_coordinate_feature_used or
            not 0 <= site_policy.site_acceptance_threshold <= 1 or
            maximum_waves < 0):
        raise ValueError("invalid frozen site-mask execution controls")
    frozen_site_threshold = site_policy.site_acceptance_threshold
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
    accepted_certificates = []
    child_certificates = []
    parent_certificates = []
    waves = []
    residual_by_key = {}
    exclusion = max(pose_tolerance, _minimum_distance(frozen) * .45)
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
        completion_by_id = {}
        sections = []
        proposals = {}
        already_proposed = set()
        for completion in frontier.completions:
            macro = macros[completion.macro_id]
            candidate = freeze_completion_candidate(
                dynamic, macro, completion, pose_tolerance=pose_tolerance)
            candidates.append(candidate)
            completion_by_id[candidate.candidate_id] = completion
            generated = freeze_completion_sections(
                dynamic, macro, completion, candidate,
                occupied_sites=tuple(occupied.values()),
                pose_tolerance=pose_tolerance)
            sections.extend(generated)
            scored = score_completion_sections(
                site_policy, generated, dynamic, macro, completion, candidate,
                tuple(occupied.values()), pose_tolerance)
            score_by_section = {item.section_id: item for item in scored}
            site_by_key = {_site_key(site, pose_tolerance): site
                           for item in generated for site in item.sites}
            for section in generated:
                already_proposed.update(
                    _site_key(site, pose_tolerance) for site in section.sites
                    if _site_key(site, pose_tolerance) in occupied)
                scored_section = score_by_section.get(section.section_id)
                if scored_section is None:
                    continue
                for key, score in scored_section.site_scores:
                    action_id = hashlib.sha256(repr(
                        (section.section_id, key)).encode()).hexdigest()
                    proposals.setdefault(key, []).append((
                        score, action_id, site_by_key[key],
                        section.exact_frozen_geometry and
                        section.frozen_port_witnessed))
        whole_ids = tuple(sorted(item.candidate_id for item in candidates))
        section_ids = tuple(sorted(item.section_id for item in sections))
        whole_digest = hashlib.sha256(repr(whole_ids).encode()).hexdigest()
        section_digest = hashlib.sha256(repr(section_ids).encode()).hexdigest()
        before_keys = set(occupied)
        novel_keys = tuple(sorted(key for key in proposals
                                  if key not in before_keys))
        proposed_digest = hashlib.sha256(repr(novel_keys).encode()).hexdigest()
        # A geometric site is committed when any frozen candidate witness is
        # above threshold.  This maximum-witness rule is fixed and reported.
        ranked = sorted(novel_keys, key=lambda key: (
            -max(item[0] for item in proposals[key]), key))
        batch = dict(occupied)
        accepted = []
        residuals = []
        for key in ranked:
            witnesses = tuple(sorted(item[1] for item in proposals[key]))
            eligible = tuple(item for item in proposals[key] if item[3])
            score, _action, site, _valid = max(
                eligible or proposals[key], key=lambda item: (item[0], item[1]))
            if not eligible:
                residuals.append(DeferredSiteResidual(
                    key, site, score, witnesses, "unwitnessed-section"))
                continue
            if score < frozen_site_threshold:
                residuals.append(DeferredSiteResidual(
                    key, site, score, witnesses, "below-frozen-threshold"))
                continue
            emitted, _overlap, collision = _classify(
                (site,), tuple(batch.values()), pose_tolerance, exclusion)
            if collision:
                residuals.append(DeferredSiteResidual(
                    key, site, score, witnesses, "batch-conflict"))
                continue
            if not emitted:
                residuals.append(DeferredSiteResidual(
                    key, site, score, witnesses, "redundant"))
                continue
            batch[key] = site
            accepted.append(key)
            accepted_certificates.append(AcceptedSiteCertificate(
                key, True, True, True, witnesses,
                hashlib.sha256(repr((key, witnesses)).encode()).hexdigest()))
        occupied = batch
        for key in accepted:
            residual_by_key.pop(key, None)
        for residual in residuals:
            residual_by_key[residual.site_key] = residual
        # Partial masks never instantiate a child.  Scan exact frozen supports
        # only after the complete accepted-site batch is materialized.
        existing_poses = {_pose_key(item.type_id, item.rotation,
                                    item.translation, pose_tolerance)
                          for item in occurrences}
        completed_children = 0
        accumulation_by_candidate = {}
        for candidate_id in whole_ids:
            completion = completion_by_id[candidate_id]
            macro = macros[completion.macro_id]
            parent_type = parents[completion.macro_id]
            state = initialize_partial_site_accumulation(
                frozen, macro, completion, tuple(occupied.values()),
                promoted_prototype=promoted_prototypes[parent_type],
                pose_tolerance=pose_tolerance)
            accumulation_by_candidate[candidate_id] = state
            certificates_by_node = {item.child_node: item
                                    for item in state.child_certificates}
            supports_by_node = {item.child_node: item
                                for item in state.child_supports}
            for child in completion.missing_children:
                support_state = supports_by_node[child.node]
                certificate = certificates_by_node[child.node]
                pose = _pose_key(support_state.child_type,
                                 support_state.rotation,
                                 support_state.translation, pose_tolerance)
                support = support_state.required_site_keys
                if pose in existing_poses or not certificate.occurrence_admissible:
                    continue
                occurrences.append(ClusterOccurrence(
                    len(occurrences), support_state.child_type,
                    support_state.rotation, support_state.translation))
                existing_poses.add(pose)
                completed_children += 1
                child_certificates.append(CompletedChildCertificate(
                    pose, support, certificate.complete_support,
                    certificate.proper_se3,
                    hashlib.sha256(repr((pose, support)).encode()).hexdigest()))
        completed_parents = 0
        for candidate_id in whole_ids:
            completion = completion_by_id[candidate_id]
            macro = macros[completion.macro_id]
            accumulation = accumulation_by_candidate[candidate_id]
            expected = []
            for placement in macro.child_placements:
                rotation = matmul(completion.macro_rotation,
                                  placement.rotation)
                translation = _add(completion.macro_translation, matvec(
                    completion.macro_rotation, placement.translation))
                expected.append(_pose_key(placement.cluster_type, rotation,
                                          translation, pose_tolerance))
            if (not accumulation.parent_certificate.promoted_parent_admissible or
                    not all(item in existing_poses for item in expected) or
                    not _verify_frozen_completion_ports(
                        frozen, macro, completion, prototypes,
                        pose_tolerance)):
                continue
            full_sites = _full_rhs_sites(completion, macro, prototypes)
            parent_type = parents[completion.macro_id]
            try:
                fitted = fit_occurrence_pose(
                    len(promoted), promoted_prototypes[parent_type],
                    full_sites, tolerance=pose_tolerance)
            except ValueError:
                continue
            pose = _pose_key(parent_type, fitted.rotation, fitted.translation,
                             pose_tolerance)
            if pose in promoted_pose_keys:
                continue
            promoted.append(ClusterOccurrence(
                len(promoted), parent_type, fitted.rotation,
                fitted.translation))
            promoted_pose_keys.add(pose)
            completed_parents += 1
            parent_certificates.append(CompletedParentCertificate(
                pose, True, True, is_proper_rotation(fitted.rotation), True,
                hashlib.sha256(repr((pose, tuple(sorted(expected,
                                                        key=repr)))).encode()
                               ).hexdigest()))
        proposed_all = set(novel_keys).union(already_proposed)
        represented = (set(accepted).union(
                       item.site_key for item in residuals).union(
                           already_proposed))
        accounted = (proposed_all == represented and
                     not set(accepted).intersection(
                         item.site_key for item in residuals))
        waves.append(SiteMaskWave(
            wave_index, whole_ids, whole_digest, section_ids, section_digest,
            novel_keys, proposed_digest, tuple(sorted(accepted)),
            tuple(sorted(residuals, key=lambda item: item.site_key)),
            tuple(sorted(already_proposed)),
            completed_children, completed_parents, accounted))
        if not accepted:
            break
    exact = (all(item.exact_frozen_rhs_site and item.proper_se3_candidate and
                 item.conflict_free for item in accepted_certificates) and
             all(item.every_exact_site_present and item.proper_se3
                 for item in child_certificates) and
             all(item.all_child_poses_present and item.frozen_ports_reverified
                 and item.proper_se3 and item.exact_promoted_fit
                 for item in parent_certificates) and
             all(item.complete_cover_accounted for item in waves))
    if not exact:
        raise AssertionError("site-mask execution certificate failed")
    # A second pass over the same partial candidate after accepting isolated
    # sites is accumulation, not self-feeding.  Self-feeding requires a child
    # occurrence completed in one wave to be available to a later wave.
    self_fed = any(
        item.completed_children > 0 and index + 1 < len(waves)
        for index, item in enumerate(waves))
    return SiteMaskExecution(
        tuple(occurrences), tuple(promoted),
        tuple(occupied[key] for key in sorted(occupied)), tuple(waves),
        tuple(residual_by_key[key] for key in sorted(residual_by_key)),
        tuple(accepted_certificates), tuple(child_certificates),
        tuple(parent_certificates), frozen_site_threshold,
        "maximum-frozen-witness-score", True, exact,
        self_fed, False, False)
