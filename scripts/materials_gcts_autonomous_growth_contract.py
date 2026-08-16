#!/usr/bin/env python3
"""Authoritative claim boundary for autonomous material growth.

Compilation and execution receive only a training cloud and seed.  A target
factory is called only after the proposal trace has been frozen, then a scorer
may compare the immutable trace with that target.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Any, Callable, Hashable, Sequence


@dataclass(frozen=True)
class FrozenAutonomousTrace:
    system: str
    backend: str
    production_kind: str
    train_digest: str
    seed_digest: str
    trace_digest: str
    candidate_wave_digests: tuple[str, ...]
    accepted_actions_per_wave: tuple[int, ...]
    emitted_sites_per_wave: tuple[int, ...]
    self_fed: bool
    cluster_actions: int
    promoted_cluster_of_cluster_actions: int
    seed_sites: tuple[tuple[Hashable, tuple[float, float, float]], ...]
    proposed_sites: tuple[tuple[Hashable, tuple[float, float, float]], ...]
    marking_ablation_same_frozen_candidates: bool
    marked_work: int | None
    unmarked_work: int | None
    best_shuffled_work: int | None
    marking_empirical_p: float | None
    symbolic_counts: tuple[int, ...]
    training_evaluation_raw_ids_disjoint: bool
    target_used_during_compile_or_execution: bool
    family_phi_cell_target_size_used: bool


@dataclass(frozen=True)
class ColoredGrowthScore:
    proposed_novel_atoms: int
    correct_novel_atoms: int
    target_novel_atoms: int
    precision: float
    recall: float


@dataclass(frozen=True)
class AutonomousGrowthCaseAudit:
    system: str
    role: str
    backend: str
    precision: float
    recall: float
    precision_recall_gate: bool
    self_fed_multiwave_gate: bool
    generic_clusters_of_clusters_gate: bool
    marking_ablation_gate: bool
    symbolic_amplification_factors: tuple[float, ...]
    symbolic_amplification_gate: bool
    leak_free: bool
    target_constructed_after_trace_frozen: bool
    autonomous_case_passed: bool
    reason: str


@dataclass(frozen=True)
class AutonomousGrowthContractAudit:
    cases: tuple[AutonomousGrowthCaseAudit, ...]
    amorphous_rejected: bool
    roles_present: tuple[str, ...]
    one_generic_production_kind: bool
    benchmark_passed: bool
    nonqualifying_evidence_notes: tuple[str, ...]


def cloud_digest(species: Sequence[Hashable], positions) -> str:
    payload = tuple(sorted((repr(label), tuple(round(float(value), 8)
                            for value in point))
                           for label, point in zip(species, positions)))
    return hashlib.sha256(repr(payload).encode()).hexdigest()


def freeze_trace(trace: FrozenAutonomousTrace) -> FrozenAutonomousTrace:
    payload = (
        trace.system, trace.backend, trace.production_kind,
        trace.train_digest, trace.seed_digest,
        trace.candidate_wave_digests,
        trace.accepted_actions_per_wave, trace.emitted_sites_per_wave,
        trace.self_fed, trace.cluster_actions,
        trace.promoted_cluster_of_cluster_actions,
        tuple(sorted(trace.seed_sites, key=repr)),
        tuple(sorted(trace.proposed_sites, key=repr)),
        trace.marking_ablation_same_frozen_candidates, trace.marked_work,
        trace.unmarked_work, trace.best_shuffled_work,
        trace.marking_empirical_p, trace.symbolic_counts,
        trace.training_evaluation_raw_ids_disjoint,
        trace.target_used_during_compile_or_execution,
        trace.family_phi_cell_target_size_used)
    digest = hashlib.sha256(repr(payload).encode()).hexdigest()
    if trace.trace_digest and trace.trace_digest != digest:
        raise ValueError("proposal trace changed after freezing")
    from dataclasses import replace
    return replace(trace, trace_digest=digest)


def execute_then_open_target(
        train: Any, seed: Any, *,
        executor: Callable[[Any, Any], FrozenAutonomousTrace],
        target_factory: Callable[[], Any],
        scorer: Callable[[FrozenAutonomousTrace, Any], ColoredGrowthScore],
) -> tuple[FrozenAutonomousTrace, ColoredGrowthScore, bool]:
    """Enforce the target-after-trace call order in the public API."""
    trace = freeze_trace(executor(train, seed))
    frozen_digest = trace.trace_digest
    target = target_factory()
    score = scorer(trace, target)
    if trace.trace_digest != frozen_digest:
        raise AssertionError("scoring mutated the frozen proposal trace")
    return trace, score, True


def audit_growth_case(
        trace: FrozenAutonomousTrace, score: ColoredGrowthScore, *,
        role: str, target_constructed_after_trace_frozen: bool,
        minimum_precision: float = .99, minimum_recall: float = .95,
) -> AutonomousGrowthCaseAudit:
    if role not in ("crystal", "quasicrystal"):
        raise ValueError("autonomous case role must be crystal or quasicrystal")
    accuracy = (score.proposed_novel_atoms > 0 and
                score.precision >= minimum_precision and
                score.recall >= minimum_recall)
    nonempty_waves = sum(value > 0 for value in
                         trace.accepted_actions_per_wave)
    multiwave = (trace.self_fed and nonempty_waves >= 3 and
                 trace.cluster_actions >= nonempty_waves)
    macro = (trace.production_kind == "recurring_port_graph_macro" and
             trace.promoted_cluster_of_cluster_actions > 0)
    marking = (
        trace.marking_ablation_same_frozen_candidates and
        trace.marked_work is not None and trace.unmarked_work is not None and
        trace.best_shuffled_work is not None and
        trace.marked_work < trace.unmarked_work and
        trace.marked_work < trace.best_shuffled_work and
        trace.marking_empirical_p is not None and
        trace.marking_empirical_p <= .05)
    factors = tuple(right / left for left, right in zip(
        trace.symbolic_counts, trace.symbolic_counts[1:]) if left > 0)
    amplification = (
        len(factors) >= 3 and all(value > 3. for value in factors[:3]) and
        any(value >= 1_000_000 for value in trace.symbolic_counts[:8]))
    leak_free = (
        target_constructed_after_trace_frozen and
        trace.training_evaluation_raw_ids_disjoint and
        not trace.target_used_during_compile_or_execution and
        not trace.family_phi_cell_target_size_used and
        all(len(value) == 64 for value in trace.candidate_wave_digests) and
        len(trace.train_digest) == len(trace.seed_digest) ==
        len(trace.trace_digest) == 64)
    passed = accuracy and multiwave and macro and marking and amplification and \
        leak_free
    failed = tuple(name for name, value in (
        ("precision/recall", accuracy), ("self-fed multiwave", multiwave),
        ("generic clusters-of-clusters", macro),
        ("matched marking ablation", marking),
        ("symbolic amplification", amplification),
        ("leakage", leak_free)) if not value)
    return AutonomousGrowthCaseAudit(
        trace.system, role, trace.backend, score.precision, score.recall,
        accuracy, multiwave, macro, marking, factors, amplification,
        leak_free, target_constructed_after_trace_frozen, passed,
        "" if passed else "failed: " + ", ".join(failed))


def audit_contract(cases: Sequence[AutonomousGrowthCaseAudit], *,
                   amorphous_rejected: bool,
                   nonqualifying_evidence_notes: Sequence[str] = (),
                   ) -> AutonomousGrowthContractAudit:
    roles = tuple(sorted({item.role for item in cases}))
    kinds_generic = all(item.generic_clusters_of_clusters_gate
                        for item in cases)
    passed = (roles == ("crystal", "quasicrystal") and
              amorphous_rejected and kinds_generic and
              all(item.autonomous_case_passed for item in cases))
    return AutonomousGrowthContractAudit(
        tuple(cases), amorphous_rejected, roles, kinds_generic, passed,
        tuple(nonqualifying_evidence_notes))
