#!/usr/bin/env python3
"""Sealed contract for stationary recurring port-graph growth.

This module does not provide another material-family detector.  It defines the
benchmark boundary that a future generic clusters-of-clusters engine must
cross.  Learning receives only a finite colored Cartesian point cloud.  The
held-out point clouds are passed only to the scorer after execution has
finished, and execution itself receives only the frozen program and seed.

The represented-site curve concerns a recursive derivation DAG.  Explicitly
materializing its atoms remains linear in the number of output atoms.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Hashable, Sequence

Point = tuple[float, float, float]
EXPECTED_PRODUCTION_KIND = "recurring_port_graph_macro"
REQUIRED_ROLES = frozenset(("crystal", "ideal_iqc", "cdyb"))


@dataclass(frozen=True)
class ColoredPointCloud:
    """The complete information exposed to compilation or execution."""

    positions: tuple[Point, ...]
    species: tuple[Hashable, ...]

    def __post_init__(self) -> None:
        if not self.positions or len(self.positions) != len(self.species):
            raise ValueError("a cloud needs equally many positions and species")
        if any(len(point) != 3 or not all(math.isfinite(value) for value in point)
               for point in self.positions):
            raise ValueError("cloud positions must be finite three-vectors")
        try:
            tuple(hash(label) for label in self.species)
        except TypeError as error:
            raise ValueError("species labels must be hashable") from error


@dataclass(frozen=True)
class PromotionWitness:
    """One train-observed, normalized macro production between two levels."""

    source_level: int
    target_level: int
    normalized_production_key: str
    learned_similarity_scale: float
    learned_from_training_only: bool = True


@dataclass(frozen=True)
class LeakageAudit:
    family_label_used: bool = False
    heldout_geometry_used: bool = False
    target_enumerator_used_for_growth: bool = False
    oracle_or_source_site_used: bool = False
    cell_or_lattice_used: bool = False
    physical_potential_used: bool = False
    prescribed_scale_or_action_radius_used: bool = False
    scorer_guided_branching: bool = False
    absolute_frame_used: bool = False

    @property
    def clean(self) -> bool:
        return not any((
            self.family_label_used, self.heldout_geometry_used,
            self.target_enumerator_used_for_growth,
            self.oracle_or_source_site_used, self.cell_or_lattice_used,
            self.physical_potential_used,
            self.prescribed_scale_or_action_radius_used,
            self.scorer_guided_branching, self.absolute_frame_used,
        ))


@dataclass(frozen=True)
class StationaryProgramAudit:
    deterministic: bool
    production_kind: str
    hierarchy_depth: int
    promotion_witnesses: tuple[PromotionWitness, ...]
    complete_training_cover: bool
    repeated_training_coverage: float
    finite_oriented_ports: bool
    causal_local_marking: bool
    self_fed_execution: bool
    unique_overlap_counting: bool
    independent_symbolic_count_verified: bool
    explicit_materialization_is_linear: bool
    leakage: LeakageAudit


@dataclass(frozen=True)
class StationaryCase:
    """One sealed train/two-level test case.

    ``role`` is held by the benchmark harness and is never passed to any
    callback.  It prevents three convenient crystal fixtures from being
    reported as a cross-family result.
    """

    role: str
    training: ColoredPointCloud
    explicit_references: tuple[ColoredPointCloud, ColoredPointCloud]


class StationaryProductionRejected(RuntimeError):
    """Intentional compiler result for a cloud with no stationary grammar."""


@dataclass(frozen=True)
class StationaryCallbacks:
    compile_program: Callable[[ColoredPointCloud], Any]
    audit_program: Callable[[Any], StationaryProgramAudit]
    execute_actions: Callable[
        [Any, ColoredPointCloud, int], tuple[ColoredPointCloud, ...]]
    represented_sites: Callable[[Any, int, int], int]
    canonical_signature: Callable[[Any], bytes]


@dataclass(frozen=True)
class StationaryCaseReport:
    role: str
    training_atoms: int
    production_kind: str
    deterministic: bool
    adjacent_stationary_scales_observed: bool
    hierarchy_depth_at_least_three: bool
    training_cover_gate: bool
    port_and_marking_gate: bool
    exact_first_two_levels: bool
    explicit_counts_match_symbolic: bool
    represented_counts_actions_zero_to_seven: tuple[int, ...]
    first_three_growth_factors: tuple[float, ...]
    three_actions_above_three: bool
    first_million_action: int | None
    million_within_seven_actions: bool
    count_certificate_gate: bool
    leakage_audit_clean: bool
    permutation_rotation_signature_invariant: bool
    permutation_rotation_output_equivariant: bool
    case_passed: bool
    failure_reason: str


@dataclass(frozen=True)
class StationaryPortGraphBenchmark:
    cases: tuple[StationaryCaseReport, ...]
    required_roles_present_once: bool
    one_generic_production_kind: bool
    amorphous_stationary_production_rejected: bool
    all_leakage_audits_clean: bool
    all_metamorphic_audits_passed: bool
    benchmark_passed: bool


def _adjacent_stationary_witnesses(
        witnesses: Sequence[PromotionWitness], tolerance: float = 1e-9) -> bool:
    """Require the same normalized rule at l->l+1 and l+1->l+2."""
    valid = tuple(witness for witness in witnesses
                  if witness.target_level == witness.source_level + 1 and
                  witness.learned_from_training_only and
                  witness.normalized_production_key and
                  math.isfinite(witness.learned_similarity_scale) and
                  witness.learned_similarity_scale > 1.0)
    return any(
        left.target_level == right.source_level and
        left.normalized_production_key == right.normalized_production_key and
        math.isclose(left.learned_similarity_scale,
                     right.learned_similarity_scale,
                     rel_tol=tolerance, abs_tol=tolerance)
        for left in valid for right in valid)


def _transform(cloud: ColoredPointCloud) -> ColoredPointCloud:
    """A fixed nontrivial proper rigid motion plus input permutation."""
    rotation = ((0.0, -1.0, 0.0),
                (1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0))
    translation = (1.125, -2.25, .75)

    def moved(point: Point) -> Point:
        return tuple(translation[row] + sum(
            rotation[row][column] * point[column] for column in range(3))
                     for row in range(3))  # type: ignore[return-value]

    records = tuple(reversed(tuple(zip(cloud.positions, cloud.species))))
    return ColoredPointCloud(
        tuple(moved(point) for point, _ in records),
        tuple(species for _, species in records))


def _same_cloud(actual: ColoredPointCloud, expected: ColoredPointCloud,
                tolerance: float) -> bool:
    """Species-preserving one-to-one spatial match using bounded hash bins."""
    if len(actual.positions) != len(expected.positions):
        return False
    if tolerance <= 0 or not math.isfinite(tolerance):
        raise ValueError("matching tolerance must be finite and positive")
    inverse = 1.0 / tolerance

    def cell(point: Point) -> tuple[int, int, int]:
        return tuple(math.floor(value * inverse) for value in point)  # type: ignore[return-value]

    bins: dict[tuple[Hashable, tuple[int, int, int]], list[int]] = {}
    for index, (point, species) in enumerate(zip(
            expected.positions, expected.species)):
        bins.setdefault((species, cell(point)), []).append(index)
    unmatched = set(range(len(expected.positions)))
    for point, species in zip(actual.positions, actual.species):
        base = cell(point)
        candidates = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    candidates.extend(index for index in bins.get((
                        species, (base[0] + dx, base[1] + dy,
                                  base[2] + dz)), ()) if index in unmatched)
        candidates = [index for index in candidates
                      if math.dist(point, expected.positions[index]) <= tolerance]
        if not candidates:
            return False
        chosen = min(candidates,
                     key=lambda index: math.dist(point,
                                                 expected.positions[index]))
        unmatched.remove(chosen)
    return not unmatched


def _safe_signature(callbacks: StationaryCallbacks, program: Any) -> bytes:
    signature = callbacks.canonical_signature(program)
    if not isinstance(signature, bytes) or not signature:
        raise ValueError("canonical program signature must be nonempty bytes")
    return signature


def _failed_case(case: StationaryCase, reason: str) -> StationaryCaseReport:
    return StationaryCaseReport(
        case.role, len(case.training.positions), "", False, False, False,
        False, False, False, False, (), (), False, None, False, False,
        False, False, False, False, reason)


def evaluate_case(case: StationaryCase, callbacks: StationaryCallbacks,
                  *, matching_tolerance: float = 1e-6) -> StationaryCaseReport:
    """Compile and score one case without exposing references to callbacks."""
    try:
        program = callbacks.compile_program(case.training)
        audit = callbacks.audit_program(program)
        signature = _safe_signature(callbacks, program)
    except StationaryProductionRejected as error:
        return _failed_case(case, f"stationary production rejected: {error}")
    except Exception as error:  # A benchmark report stays inspectably red.
        return _failed_case(case, f"compile/audit failed: {error}")

    adjacent = _adjacent_stationary_witnesses(audit.promotion_witnesses)
    hierarchy = audit.hierarchy_depth >= 3
    cover = (audit.complete_training_cover and
             audit.repeated_training_coverage >= .95)
    ports = audit.finite_oriented_ports and audit.causal_local_marking
    try:
        explicit = callbacks.execute_actions(program, case.training, 2)
        exact = (len(explicit) == 2 and all(
            _same_cloud(actual, reference, matching_tolerance)
            for actual, reference in zip(explicit, case.explicit_references)))
        counts = tuple(callbacks.represented_sites(
            program, len(case.training.positions), action)
                       for action in range(8))
        if (len(counts) != 8 or any(isinstance(value, bool) or
                                    not isinstance(value, int) or value <= 0
                                    for value in counts) or
                counts[0] != len(case.training.positions)):
            raise ValueError("represented counts must be positive integers rooted at the seed")
        explicit_counts = (len(explicit) == 2 and
                           tuple(len(item.positions) for item in explicit) ==
                           counts[1:3])
        factors = tuple(counts[index] / counts[index - 1]
                        for index in range(1, 4))
        exponential = len(factors) == 3 and all(factor > 3.0
                                                for factor in factors)
        million = next((action for action, count in enumerate(counts)
                        if count >= 1_000_000), None)
        million_gate = million is not None and million <= 7
    except Exception as error:
        explicit = ()
        exact = explicit_counts = exponential = million_gate = False
        counts = ()
        factors = ()
        million = None
        execution_failure = str(error)
    else:
        execution_failure = ""

    try:
        transformed_training = _transform(case.training)
        transformed_program = callbacks.compile_program(transformed_training)
        transformed_audit = callbacks.audit_program(transformed_program)
        signature_invariant = (
            transformed_audit.production_kind == audit.production_kind and
            _safe_signature(callbacks, transformed_program) == signature)
        transformed_explicit = callbacks.execute_actions(
            transformed_program, transformed_training, 2)
        output_equivariant = (len(transformed_explicit) == 2 and all(
            _same_cloud(actual, _transform(reference), matching_tolerance)
            for actual, reference in zip(
                transformed_explicit, case.explicit_references)))
    except Exception:
        signature_invariant = output_equivariant = False

    count_certificate = (
        audit.unique_overlap_counting and
        audit.independent_symbolic_count_verified and
        audit.explicit_materialization_is_linear and explicit_counts)
    passed = all((
        audit.deterministic,
        audit.production_kind == EXPECTED_PRODUCTION_KIND,
        adjacent, hierarchy, cover, ports, audit.self_fed_execution,
        exact, exponential, million_gate, count_certificate,
        audit.leakage.clean, signature_invariant, output_equivariant,
    ))
    return StationaryCaseReport(
        case.role, len(case.training.positions), audit.production_kind,
        audit.deterministic, adjacent, hierarchy, cover, ports, exact,
        explicit_counts, counts, factors, exponential, million, million_gate,
        count_certificate, audit.leakage.clean, signature_invariant,
        output_equivariant, passed, execution_failure)


def _amorphous_rejected(cloud: ColoredPointCloud,
                        callbacks: StationaryCallbacks) -> bool:
    try:
        callbacks.compile_program(cloud)
    except StationaryProductionRejected:
        return True
    except Exception:
        return False
    # Returning a stochastic or otherwise unauditable program is not a clean
    # rejection; the compiler must explicitly decline stationary recursion.
    return False


def evaluate_stationary_port_graph_contract(
        cases: Sequence[StationaryCase], amorphous: ColoredPointCloud,
        callbacks: StationaryCallbacks, *,
        matching_tolerance: float = 1e-6) -> StationaryPortGraphBenchmark:
    """Evaluate the complete cross-family stationary-production contract."""
    reports = tuple(evaluate_case(case, callbacks,
                                  matching_tolerance=matching_tolerance)
                    for case in cases)
    roles = tuple(case.role for case in cases)
    roles_ok = len(roles) == len(REQUIRED_ROLES) and set(roles) == REQUIRED_ROLES
    kinds = {report.production_kind for report in reports
             if report.production_kind}
    one_kind = (len(kinds) == 1 and kinds == {EXPECTED_PRODUCTION_KIND} and
                len(reports) == len(REQUIRED_ROLES))
    amorphous_rejected = _amorphous_rejected(amorphous, callbacks)
    clean = bool(reports) and all(report.leakage_audit_clean
                                  for report in reports)
    metamorphic = bool(reports) and all(
        report.permutation_rotation_signature_invariant and
        report.permutation_rotation_output_equivariant for report in reports)
    passed = (roles_ok and one_kind and amorphous_rejected and clean and
              metamorphic and all(report.case_passed for report in reports))
    return StationaryPortGraphBenchmark(
        reports, roles_ok, one_kind, amorphous_rejected, clean, metamorphic,
        passed)
