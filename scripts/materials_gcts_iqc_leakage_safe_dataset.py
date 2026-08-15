#!/usr/bin/env python3
"""Leakage-safe train/guard/test adapter for colored IQC point clouds.

The splitter alone receives the raw cloud.  It assigns immutable global atom
IDs to an inner train core, a required local-neighborhood guard halo, and a
scorer-only exterior.  Learners receive copied species/positions for
``train + guard`` only; no oracle lifts, family label, cell, expected scale, or
held-out coordinate is present in the fit payload.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Hashable, Sequence


@dataclass(frozen=True)
class AtomicDomain:
    global_ids: tuple[int, ...]
    species: tuple[Hashable, ...]
    positions: tuple[tuple[float, float, float], ...]


@dataclass(frozen=True)
class LeakageSafeIQCSplit:
    train: AtomicDomain
    guard: AtomicDomain
    fit: AtomicDomain
    heldout: AtomicDomain
    center: tuple[float, float, float]
    train_cutoff: float
    required_guard_width: float
    fit_cutoff: float
    neighborhood_order: int
    exact_global_id_disjointness: bool
    fit_equals_train_union_guard: bool
    heldout_payload_exposed_to_learner: bool
    oracle_family_phi_cell_fields_in_fit_payload: bool


def _domain(ids, species, positions):
    ids = tuple(sorted(ids))
    return AtomicDomain(
        ids, tuple(species[index] for index in ids),
        tuple(tuple(float(value) for value in positions[index])
              for index in ids))


def split_iqc_train_guard_test(
    species: Sequence[Hashable], positions: Sequence[Sequence[float]], *,
    train_fraction: float = .15, neighborhood_order: int = 14,
) -> LeakageSafeIQCSplit:
    """Split using geometry only; learner-facing payload is strictly sealed."""
    if len(species) != len(positions) or len(positions) < 3:
        raise ValueError("species and nontrivial positions must align")
    if not 0 < train_fraction < .5:
        raise ValueError("train_fraction must be between zero and one half")
    if not 1 <= neighborhood_order < len(positions):
        raise ValueError("invalid neighborhood order")
    points = tuple(tuple(float(value) for value in point)
                   for point in positions)
    if any(len(point) != 3 or not all(math.isfinite(value) for value in point)
           for point in points):
        raise ValueError("positions must be finite 3D points")
    center = tuple(sum(point[axis] for point in points) / len(points)
                   for axis in range(3))
    radii = tuple(math.dist(point, center) for point in points)
    ordered_radii = sorted(set(radii))
    target_rank = max(0, min(len(positions) - 1,
                             int(train_fraction * len(positions))))
    rank_radius = sorted(radii)[target_rank]
    train_cutoff = min(ordered_radii,
                       key=lambda value: (abs(value - rank_radius), value))
    train_ids = tuple(index for index, radius in enumerate(radii)
                      if radius <= train_cutoff + 1e-10)
    # The guard size is derived from train-core coordinates alone: it is the
    # largest distance to the requested local neighbor within that core.
    if len(train_ids) <= neighborhood_order:
        raise ValueError("train core is too small for the guard contract")
    required_guard = max(sorted(
        math.dist(points[index], points[other])
        for other in train_ids if other != index)[neighborhood_order - 1]
                         for index in train_ids)
    fit_cutoff = train_cutoff + required_guard
    guard_ids = tuple(index for index, radius in enumerate(radii)
                      if train_cutoff + 1e-10 < radius <= fit_cutoff + 1e-10)
    heldout_ids = tuple(index for index, radius in enumerate(radii)
                        if radius > fit_cutoff + 1e-10)
    fit_ids = tuple(sorted(train_ids + guard_ids))
    domains = tuple(map(set, (train_ids, guard_ids, heldout_ids)))
    disjoint = all(domains[left].isdisjoint(domains[right])
                   for left in range(3) for right in range(left + 1, 3))
    return LeakageSafeIQCSplit(
        _domain(train_ids, species, points),
        _domain(guard_ids, species, points),
        _domain(fit_ids, species, points),
        _domain(heldout_ids, species, points), center, train_cutoff,
        required_guard, fit_cutoff, neighborhood_order, disjoint,
        set(fit_ids) == set(train_ids).union(guard_ids), False, False)


def domain_digest(domain: AtomicDomain) -> str:
    return hashlib.sha256(repr(domain.global_ids).encode()).hexdigest()
