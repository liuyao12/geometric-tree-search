#!/usr/bin/env python3
"""Target-free certificates for accumulating partial frozen child supports.

This module deliberately does not create ``ClusterOccurrence`` objects.
Fragments first satisfy exact colored-site obligations.  A caller may create a
child occurrence only after ``occurrence_admissible`` becomes true, and may
create a promoted parent only after every child is complete, frozen ports are
verified, and an independently frozen promoted prototype fits the exact RHS.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace
from typing import Hashable, Sequence

from materials_gcts_oriented_overlap_ports import (
    fit_occurrence_pose, is_proper_rotation, matmul, matvec)

Site = tuple[Hashable, tuple[float, float, float]]
SiteKey = tuple[str, int, int, int]


@dataclass(frozen=True)
class FrozenChildSupport:
    child_node: int
    child_type: int
    rotation: tuple
    translation: tuple[float, float, float]
    required_sites: tuple[Site, ...]
    required_site_keys: tuple[SiteKey, ...]


@dataclass(frozen=True)
class ResidualSiteTerminal:
    site_key: SiteKey
    species: Hashable
    position: tuple[float, float, float]
    owner_child_nodes: tuple[int, ...]


@dataclass(frozen=True)
class ChildSupportCertificate:
    child_node: int
    required_sites: int
    satisfied_sites: int
    complete_support: bool
    proper_se3: bool
    occurrence_admissible: bool


@dataclass(frozen=True)
class ParentSupportCertificate:
    every_child_support_complete: bool
    frozen_ports_verified: bool
    exact_rhs_union: bool
    promoted_prototype_fit_verified: bool
    proper_se3: bool
    promoted_parent_admissible: bool


@dataclass(frozen=True)
class FrozenSiteFragment:
    fragment_id: str
    child_node: int
    sites: tuple[Site, ...]
    target_used: bool = False


@dataclass(frozen=True)
class PartialSiteAccumulation:
    macro_id: int
    pose_tolerance: float
    child_supports: tuple[FrozenChildSupport, ...]
    required_sites: tuple[tuple[SiteKey, Site], ...]
    shared_site_owners: tuple[tuple[SiteKey, tuple[int, ...]], ...]
    satisfied_site_keys: tuple[SiteKey, ...]
    residual_terminals: tuple[ResidualSiteTerminal, ...]
    child_certificates: tuple[ChildSupportCertificate, ...]
    parent_certificate: ParentSupportCertificate
    frozen_ports_verified: bool
    promoted_prototype_fit_verified: bool
    target_used: bool = False


def _site_key(site, tolerance):
    return ((site[0] if isinstance(site[0], str) else repr(site[0])),
            *(round(float(value) / tolerance) for value in site[1]))


def _add(left, right):
    return tuple(left[index] + right[index] for index in range(3))


def _render(prototype, rotation, translation):
    return tuple((species, _add(matvec(rotation, point), translation))
                 for species, point in prototype.sites)


def _admitted_semantics(program):
    atlas = getattr(program, "atlas", None)
    values = {(item.parent_type, item.child_type, item.symmetry_orbit_key)
              for item in getattr(atlas, "ports", ())}
    values.update((parent_type, child_type, key)
                  for _parent, _child, parent_type, child_type, key in
                  getattr(atlas, "relation_classes", ()))
    values.update((item.parent_type, item.child_type,
                   item.symmetry_orbit_key)
                  for item in getattr(program, "boundary_ports", ()))
    return frozenset(values)


def _certify(state, satisfied):
    satisfied = frozenset(satisfied)
    children = []
    for child in state.child_supports:
        required = set(child.required_site_keys)
        complete = required.issubset(satisfied)
        proper = is_proper_rotation(child.rotation)
        children.append(ChildSupportCertificate(
            child.child_node, len(required), len(required & satisfied),
            complete, proper, complete and proper))
    required_by_key = dict(state.required_sites)
    owners = dict(state.shared_site_owners)
    residuals = tuple(ResidualSiteTerminal(
        key, required_by_key[key][0], required_by_key[key][1], owners[key])
                      for key in sorted(set(required_by_key) - satisfied))
    exact_union = satisfied.issubset(required_by_key) and \
        satisfied | {item.site_key for item in residuals} == set(required_by_key)
    all_children = all(item.occurrence_admissible for item in children)
    proper = all(item.proper_se3 for item in children)
    parent = ParentSupportCertificate(
        all_children, state.frozen_ports_verified, exact_union,
        state.promoted_prototype_fit_verified, proper,
        all_children and state.frozen_ports_verified and exact_union and
        state.promoted_prototype_fit_verified and proper)
    return replace(state, satisfied_site_keys=tuple(sorted(satisfied)),
                   residual_terminals=residuals,
                   child_certificates=tuple(children),
                   parent_certificate=parent)


def initialize_partial_site_accumulation(
        program, macro, completion, occupied_sites: Sequence[Site], *,
        promoted_prototype=None, pose_tolerance=.03,
) -> PartialSiteAccumulation:
    if pose_tolerance <= 0 or not math.isfinite(pose_tolerance):
        raise ValueError("pose tolerance must be finite and positive")
    if getattr(program, "target_used", False) or completion.target_used:
        raise ValueError("partial-site accumulation requires target-free data")
    if completion.macro_id != macro.macro_id or \
            not completion.exact_frozen_rhs_geometry or \
            not is_proper_rotation(completion.macro_rotation):
        raise ValueError("completion is not an exact frozen proper-SE(3) RHS")
    prototypes = {item.type_id: item for item in program.prototypes}
    placements = {item.node: item for item in macro.child_placements}
    if set(placements) != set(completion.matched_nodes) | {
            item.node for item in completion.missing_children}:
        raise ValueError("completion does not partition the frozen RHS")
    supports = []
    required = {}
    owners = {}
    predicted_missing = {item.node: item
                         for item in completion.missing_children}
    for node, placement in sorted(placements.items()):
        rotation = matmul(completion.macro_rotation, placement.rotation)
        translation = _add(completion.macro_translation, matvec(
            completion.macro_rotation, placement.translation))
        if not is_proper_rotation(rotation):
            raise ValueError("frozen child has an improper pose")
        sites = _render(prototypes[placement.cluster_type], rotation,
                        translation)
        keys = tuple(_site_key(site, pose_tolerance) for site in sites)
        predicted = predicted_missing.get(node)
        if predicted is not None:
            predicted_keys = {_site_key(site, pose_tolerance)
                              for site in predicted.sites}
            if (predicted.type_id != placement.cluster_type or
                    not is_proper_rotation(predicted.rotation) or
                    predicted_keys != set(keys)):
                raise ValueError("predicted child differs from frozen RHS")
        for key, site in zip(keys, sites):
            previous = required.setdefault(key, site)
            if previous[0] != site[0]:
                raise ValueError("frozen RHS has a colored-site conflict")
            owners.setdefault(key, set()).add(node)
        supports.append(FrozenChildSupport(
            node, placement.cluster_type, rotation, translation, sites,
            tuple(sorted(set(keys)))))
    # Same quantized coordinate with different chemistry must fail even though
    # the colored key differs.
    coordinate_species = {}
    for key in required:
        previous = coordinate_species.setdefault(key[1:], key[0])
        if previous != key[0]:
            raise ValueError("frozen RHS has a colored-site conflict")
    occupied = {}
    for site in occupied_sites:
        key = _site_key(site, pose_tolerance)
        coordinate = key[1:]
        previous = next((other for other in required
                         if other[1:] == coordinate), None)
        if previous is not None and previous[0] != key[0]:
            raise ValueError("occupied site conflicts with frozen chemistry")
        occupied[key] = site
    admitted = _admitted_semantics(program)
    ports_verified = all(tuple(edge.port) in admitted
                         for edge in getattr(macro, "edges", ())) and all(
        tuple(slot.port) in admitted and slot.occurrence_support > 0 and
        slot.direction in ("incoming", "outgoing")
        for slot in getattr(macro, "boundary_slots", ()))
    full_sites = tuple(required[key] for key in sorted(required))
    promoted_fit = False
    if promoted_prototype is not None:
        try:
            fitted = fit_occurrence_pose(
                -1, promoted_prototype, full_sites, tolerance=pose_tolerance)
            promoted_fit = is_proper_rotation(fitted.rotation)
        except ValueError:
            promoted_fit = False
    empty_parent = ParentSupportCertificate(
        False, ports_verified, True, promoted_fit, True, False)
    state = PartialSiteAccumulation(
        macro.macro_id, pose_tolerance, tuple(supports),
        tuple((key, required[key]) for key in sorted(required)),
        tuple((key, tuple(sorted(owners[key]))) for key in sorted(owners)),
        (), (), (), empty_parent, ports_verified, promoted_fit, False)
    return _certify(state, set(required).intersection(occupied))


def freeze_site_fragment(state, child_node: int,
                         sites: Sequence[Site]) -> FrozenSiteFragment:
    if state.target_used:
        raise ValueError("target-tainted accumulation state")
    support = next((item for item in state.child_supports
                    if item.child_node == child_node), None)
    if support is None:
        raise ValueError("fragment names an unknown child")
    sites = tuple((species, tuple(map(float, point)))
                  for species, point in sites)
    keys = tuple(sorted({_site_key(site, state.pose_tolerance)
                         for site in sites}))
    if not keys or not set(keys).issubset(support.required_site_keys):
        raise ValueError("fragment contains unsupported child sites")
    payload = (state.macro_id, child_node, keys)
    return FrozenSiteFragment(
        hashlib.sha256(repr(payload).encode()).hexdigest(), child_node, sites,
        False)


def apply_site_fragment(state: PartialSiteAccumulation,
                        fragment: FrozenSiteFragment) -> PartialSiteAccumulation:
    if state.target_used or fragment.target_used:
        raise ValueError("target-tainted fragment is forbidden")
    canonical = freeze_site_fragment(state, fragment.child_node,
                                     fragment.sites)
    if fragment.fragment_id != canonical.fragment_id:
        raise ValueError("fragment digest does not match exact frozen sites")
    keys = {_site_key(site, state.pose_tolerance) for site in fragment.sites}
    if keys.issubset(state.satisfied_site_keys):
        raise ValueError("fragment is redundant")
    return _certify(state, set(state.satisfied_site_keys) | keys)
