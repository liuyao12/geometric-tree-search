#!/usr/bin/env python3
"""Strict finite-state substitution-cycle recurrence evidence.

This is additive to, and does not relax, the stationary-production gate.  A
nontrivial period-p cycle needs 2p+1 consecutive observations, so every state
and directed transition is seen twice.  State identity retains canonical exact
chemistry, chirality, geometry, directed ports, overlap chemistry, and boundary
semantics.  Repeated transitions must have the same independently learned
scale and exact checked population-substitution matrix.  A train-learned cycle
passes only after an independently observed heldout/self-fed replay.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Sequence

from materials_gcts_recurring_action_submacro_audit import _independent_subset
from materials_gcts_stationary_production_signature import (
    PortGraphProduction, audit_chemical_population_substitution,
    canonicalize_production)


@dataclass(frozen=True)
class CycleObservation:
    hierarchy_level: int
    record_id: str
    production: PortGraphProduction
    occurrence_supports: tuple[frozenset[int], ...]
    mdl_saving: int
    split: str
    learned_from_training_only: bool
    geometry_scale_independently_observed: bool


@dataclass(frozen=True)
class CycleWitness:
    period: int
    train_record_ids: tuple[str, ...]
    validation_record_ids: tuple[str, ...]
    state_keys: tuple[str, ...]
    transition_scales: tuple[float, ...]
    transition_population_matrices: tuple[tuple[tuple[int, ...], ...], ...]
    cycle_scale: float


@dataclass(frozen=True)
class FiniteStateCycleAudit:
    recurrent: bool
    train_levels: tuple[int, ...]
    validation_levels: tuple[int, ...]
    eligible_train_observations: int
    eligible_validation_observations: int
    learned_state_count: int
    evaluated_train_paths: int
    train_cycle_candidates: int
    heldout_confirmed_cycles: int
    witnesses: tuple[CycleWitness, ...]
    exact_semantics_required: bool
    population_substitution_required: bool
    heldout_independent_scale_required: bool
    stationary_gate_weakened: bool
    leakage_clean: bool
    reason: str


@dataclass(frozen=True)
class _Prepared:
    observation: CycleObservation
    state_key: str
    intrinsic_scale: float


def _prepare(observations, maximum_overlap, tolerance):
    prepared = []
    leakage_clean = True
    for item in observations:
        leakage_clean &= (item.learned_from_training_only
                          if item.split == "train" else True)
        try:
            canonical = canonicalize_production(
                item.production, tolerance=tolerance)
        except ValueError:
            continue
        independent, overlap = _independent_subset(
            item.occurrence_supports, maximum_overlap)
        if (len(independent) < 2 or overlap > maximum_overlap or
                item.mdl_saving <= 0):
            continue
        prepared.append(_Prepared(
            item, canonical.normalized_key,
            canonical.intrinsic_translation_scale))
    return tuple(prepared), leakage_clean


def _transition(left, right, tolerance):
    scale = right.intrinsic_scale / left.intrinsic_scale
    population = audit_chemical_population_substitution(
        left.observation.production, right.observation.production)
    if (not math.isfinite(scale) or scale <= 0 or not population.checked or
            not population.consistent):
        return None
    return scale, population.substitution_matrix


def _cycle_signature(path, period, tolerance):
    keys = tuple(item.state_key for item in path)
    if any(keys[index] != keys[index + period]
           for index in range(period + 1)):
        return None
    # Period is minimal: accepting A,A,A as a period-2 cycle would merely
    # rename stationary recurrence.
    if len(set(keys[:period])) < 2 or any(
            all(keys[index] == keys[index + divisor]
                for index in range(period + divisor + 1 - divisor))
            for divisor in range(1, period) if period % divisor == 0):
        return None
    transitions = tuple(_transition(left, right, tolerance)
                        for left, right in zip(path, path[1:]))
    if any(item is None for item in transitions):
        return None
    scales = tuple(item[0] for item in transitions)  # type: ignore[index]
    matrices = tuple(item[1] for item in transitions)  # type: ignore[index]
    if any(not math.isclose(scales[index], scales[index + period],
                            rel_tol=tolerance, abs_tol=tolerance)
           or matrices[index] != matrices[index + period]
           for index in range(period)):
        return None
    cycle_scale = math.prod(scales[:period])
    if cycle_scale <= 1 + tolerance:
        return None
    return keys[:period], scales[:period], matrices[:period], cycle_scale


def _paths(records, period, maximum_paths):
    by_level = {}
    for item in records:
        by_level.setdefault(item.observation.hierarchy_level, []).append(item)
    evaluated = 0
    for start in sorted(by_level):
        levels = tuple(range(start, start + 2 * period + 1))
        if any(level not in by_level for level in levels):
            continue
        for path in itertools.product(*(by_level[level] for level in levels)):
            evaluated += 1
            if evaluated > maximum_paths:
                return
            yield path


def audit_finite_state_cycles(
        observations: Sequence[CycleObservation], *, maximum_period: int = 4,
        maximum_evidence_overlap_fraction: float = .1,
        tolerance: float = 1e-6, maximum_paths: int = 100000,
) -> FiniteStateCycleAudit:
    if maximum_period < 2 or maximum_paths < 1:
        raise ValueError("cycle bounds must be positive and nontrivial")
    train, train_clean = _prepare(
        (item for item in observations if item.split == "train"),
        maximum_evidence_overlap_fraction, tolerance)
    validation, validation_clean = _prepare(
        (item for item in observations if item.split in ("heldout", "self-fed")),
        maximum_evidence_overlap_fraction, tolerance)
    train_levels = tuple(sorted({item.observation.hierarchy_level
                                 for item in train}))
    validation_levels = tuple(sorted({item.observation.hierarchy_level
                                      for item in validation}))
    train_candidates = []
    evaluated = 0
    for period in range(2, maximum_period + 1):
        for path in _paths(train, period, maximum_paths):
            evaluated += 1
            signature = _cycle_signature(path, period, tolerance)
            if signature is not None:
                train_candidates.append((period, path, signature))

    witnesses = []
    for period, train_path, signature in train_candidates:
        state_keys, scales, matrices, cycle_scale = signature
        for validation_path in _paths(validation, period, maximum_paths):
            if not all(item.observation.geometry_scale_independently_observed
                       for item in validation_path):
                continue
            validation_signature = _cycle_signature(
                validation_path, period, tolerance)
            if validation_signature is None:
                continue
            other_keys, other_scales, other_matrices, other_cycle_scale = \
                validation_signature
            if (state_keys != other_keys or matrices != other_matrices or
                    any(not math.isclose(left, right, rel_tol=tolerance,
                                         abs_tol=tolerance)
                        for left, right in zip(scales, other_scales)) or
                    not math.isclose(cycle_scale, other_cycle_scale,
                                     rel_tol=tolerance, abs_tol=tolerance)):
                continue
            witnesses.append(CycleWitness(
                period,
                tuple(item.observation.record_id for item in train_path),
                tuple(item.observation.record_id
                      for item in validation_path), state_keys, scales,
                matrices, cycle_scale))
    witnesses = tuple(sorted(set(witnesses), key=lambda item: (
        item.period, item.train_record_ids, item.validation_record_ids)))
    recurrent = bool(witnesses)
    if recurrent:
        reason = ""
    elif not train_candidates:
        reason = ("no train-only finite-state production cycle has two full "
                  "consecutive traversals with equal scale and population semantics")
    elif not validation:
        reason = "train cycle lacks heldout/self-fed recurrence observations"
    elif not all(item.observation.geometry_scale_independently_observed
                 for item in validation):
        reason = ("heldout records replay frozen geometry; hierarchy scale was "
                  "not independently observed")
    else:
        reason = "no train cycle transfers exactly to heldout/self-fed levels"
    return FiniteStateCycleAudit(
        recurrent, train_levels, validation_levels, len(train),
        len(validation), len({item.state_key for item in train}), evaluated,
        len(train_candidates), len(witnesses), witnesses, True, True, True,
        False, train_clean and validation_clean, reason)
