#!/usr/bin/env python3
"""Cross-family descendant-value learning for overlapping-cover GCTS.

The policy is trained only from abstract covering states and completed GCTS
search traces.  Geometry may be used upstream to construct a curriculum case,
but positions, rotations, lattice labels, and chemical species do not cross the
``CoverCurriculumCase`` boundary.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import DefaultDict, Iterable, Tuple

from materials_cover_curriculum import CoverCurriculumCase, build_cover_curriculum
from materials_cover_ranking import (
    BranchExample,
    DescendantBranchOutcome,
    DescendantRewardConfig,
    LinearBranchRanker,
    make_solver_branch_orderer,
    solver_branch_feature_rows,
    train_from_descendant_outcomes,
    train_from_exact_teacher,
)
from materials_overlap_cover import BranchCandidateOutcome


@dataclass(frozen=True)
class TrainingSummary:
    cases: int
    validation_cases: int
    imitation_examples: int
    descendant_outcomes: int
    descendant_contexts: int
    feasible_outcomes: int
    improving_outcomes: int


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    family: str
    optimum_cost: float
    optimum_occurrences: int
    unguided_nodes: int
    imitation_nodes: int
    descendant_nodes: int
    imitation_delta: int
    descendant_delta: int


@dataclass(frozen=True)
class FamilyResult:
    family: str
    cases: int
    unguided_nodes: int
    imitation_nodes: int
    descendant_nodes: int


@dataclass(frozen=True)
class LargeTransferResult:
    atoms: int
    node_budget: int
    unguided_cost: float
    imitation_cost: float
    descendant_cost: float
    unguided_optimal: bool
    imitation_optimal: bool
    descendant_optimal: bool


@dataclass(frozen=True)
class PolicySelectionResult:
    selected_policy: str
    unguided_validation_nodes: int
    imitation_validation_nodes: int
    descendant_validation_nodes: int
    reason: str


@dataclass(frozen=True)
class ValueBenchmarkResult:
    training: TrainingSummary
    selection: PolicySelectionResult
    held_out: Tuple[CaseResult, ...]
    families: Tuple[FamilyResult, ...]
    imitation_wins: int
    descendant_wins: int
    descendant_ties: int
    descendant_losses: int
    large_transfer: Tuple[LargeTransferResult, ...]


def _incumbent_improvement(event: BranchCandidateOutcome) -> float:
    if not event.improved_incumbent or event.incumbent_after is None:
        return 0.0
    if event.incumbent_before is None:
        return 1.0
    before_cost, before_count = event.incumbent_before
    after_cost, after_count = event.incumbent_after
    return max(0.0, before_cost - after_cost) + 0.05 * max(
        0, before_count - after_count)


def collect_descendant_outcomes(
    case: CoverCurriculumCase,
) -> Tuple[Tuple[DescendantBranchOutcome, ...], object]:
    """Run an exact teacher and convert its candidate-subtree events."""

    outcomes = []

    def observer(problem, event) -> None:
        if not isinstance(event, BranchCandidateOutcome):
            return
        if event.feasible is None:
            return
        options = event.context.domains[event.context.pivot]
        rows = solver_branch_feature_rows(problem, event.context, options)
        outcomes.append(DescendantBranchOutcome(
            context_id=(case.metadata.case_id, event.branch_id),
            candidate_id=problem.occurrences[event.candidate_index].id,
            features=rows[event.candidate_index],
            feasible=event.feasible,
            incumbent_improvement=_incumbent_improvement(event),
            descendant_nodes=event.descendant_expanded_nodes,
        ))

    teacher = case.problem.solve(branch_observer=observer)
    if not teacher.complete or not teacher.optimal:
        raise RuntimeError(
            f"curriculum teacher {case.metadata.case_id} was not certified")
    return tuple(outcomes), teacher


def train_curriculum_policies(
    cases: Iterable[CoverCurriculumCase],
    *,
    validation_cases: int = 0,
) -> Tuple[LinearBranchRanker, LinearBranchRanker, TrainingSummary]:
    imitation_examples = []
    descendant_outcomes = []
    case_count = 0
    for case in cases:
        case_count += 1
        imitation = train_from_exact_teacher(
            case.problem, fit_kwargs={"epochs": 0})
        imitation_examples.extend(
            BranchExample(
                context_id=(case.metadata.case_id, example.context_id),
                candidate_id=example.candidate_id,
                features=example.features,
                reward=example.reward,
            )
            for example in imitation.examples
        )
        outcomes, _ = collect_descendant_outcomes(case)
        descendant_outcomes.extend(outcomes)

    imitation_ranker = LinearBranchRanker().fit(
        imitation_examples, epochs=24, learning_rate=0.12)
    descendant_report = train_from_descendant_outcomes(
        descendant_outcomes,
        reward_config=DescendantRewardConfig(
            feasible_reward=1.0,
            improvement_weight=2.0,
            node_weight=0.16,
        ),
        fit_kwargs={"epochs": 24, "learning_rate": 0.12},
    )
    return imitation_ranker, descendant_report.ranker, TrainingSummary(
        cases=case_count,
        validation_cases=validation_cases,
        imitation_examples=len(imitation_examples),
        descendant_outcomes=descendant_report.outcome_count,
        descendant_contexts=descendant_report.context_count,
        feasible_outcomes=descendant_report.feasible_outcome_count,
        improving_outcomes=descendant_report.improving_outcome_count,
    )


def evaluate_case(
    case: CoverCurriculumCase,
    imitation_ranker: LinearBranchRanker,
    descendant_ranker: LinearBranchRanker,
) -> CaseResult:
    unguided = case.problem.solve()
    imitation = case.problem.solve(
        branch_orderer=make_solver_branch_orderer(imitation_ranker))
    descendant = case.problem.solve(
        branch_orderer=make_solver_branch_orderer(descendant_ranker))
    for label, result in (
        ("unguided", unguided),
        ("imitation", imitation),
        ("descendant", descendant),
    ):
        if not result.complete or not result.optimal:
            raise RuntimeError(f"{label} failed to certify {case.metadata.case_id}")
        if (result.total_cost, len(result.selected)) != (
                unguided.total_cost, len(unguided.selected)):
            raise RuntimeError(f"{label} changed the optimum")
    return CaseResult(
        case_id=case.metadata.case_id,
        family=case.metadata.family,
        optimum_cost=unguided.total_cost,
        optimum_occurrences=len(unguided.selected),
        unguided_nodes=unguided.expanded_nodes,
        imitation_nodes=imitation.expanded_nodes,
        descendant_nodes=descendant.expanded_nodes,
        imitation_delta=imitation.expanded_nodes - unguided.expanded_nodes,
        descendant_delta=descendant.expanded_nodes - unguided.expanded_nodes,
    )


def evaluate_large_transfer(
    imitation_ranker: LinearBranchRanker,
    descendant_ranker: LinearBranchRanker,
    node_budget: int = 100,
) -> LargeTransferResult:
    # Reuse the public learned-cover construction; no generator coordinates
    # enter either policy.
    from materials_cover_scaling_benchmark import build_instance

    problem, summary = build_instance(3)
    unguided = problem.solve(max_expanded_nodes=node_budget)
    imitation = problem.solve(
        max_expanded_nodes=node_budget,
        branch_orderer=make_solver_branch_orderer(imitation_ranker))
    descendant = problem.solve(
        max_expanded_nodes=node_budget,
        branch_orderer=make_solver_branch_orderer(descendant_ranker))
    return LargeTransferResult(
        atoms=summary.atoms,
        node_budget=node_budget,
        unguided_cost=unguided.total_cost,
        imitation_cost=imitation.total_cost,
        descendant_cost=descendant.total_cost,
        unguided_optimal=unguided.optimal,
        imitation_optimal=imitation.optimal,
        descendant_optimal=descendant.optimal,
    )


def benchmark() -> ValueBenchmarkResult:
    curriculum = build_cover_curriculum()
    # Reserve the final training seed of every family for policy selection.
    # The public test split and the 123-atom transfer remain untouched until
    # after the choice is frozen.
    training_cases = tuple(
        case for case in curriculum.train if "-002-" not in case.metadata.case_id)
    validation_cases = tuple(
        case for case in curriculum.train if "-002-" in case.metadata.case_id)
    imitation, descendant, training = train_curriculum_policies(
        training_cases, validation_cases=len(validation_cases))
    validation = tuple(
        evaluate_case(case, imitation, descendant) for case in validation_cases)
    validation_totals = {
        "unguided": sum(row.unguided_nodes for row in validation),
        "imitation": sum(row.imitation_nodes for row in validation),
        "descendant": sum(row.descendant_nodes for row in validation),
    }
    learned_choice = min(
        ("imitation", "descendant"),
        key=lambda name: (
            validation_totals[name],
            0 if name == "imitation" else 1,
        ),
    )
    selected_policy = (
        learned_choice
        if validation_totals[learned_choice] <= validation_totals["unguided"]
        else "unguided"
    )
    selection = PolicySelectionResult(
        selected_policy=selected_policy,
        unguided_validation_nodes=validation_totals["unguided"],
        imitation_validation_nodes=validation_totals["imitation"],
        descendant_validation_nodes=validation_totals["descendant"],
        reason=(
            "minimum validation nodes; prefer final-solution imitation when "
            "learned policies tie; fall back to unguided on regression"
        ),
    )
    held_out = tuple(
        evaluate_case(case, imitation, descendant) for case in curriculum.test)
    family_rows: DefaultDict[str, list[CaseResult]] = defaultdict(list)
    for result in held_out:
        family_rows[result.family].append(result)
    families = tuple(
        FamilyResult(
            family=family,
            cases=len(rows),
            unguided_nodes=sum(row.unguided_nodes for row in rows),
            imitation_nodes=sum(row.imitation_nodes for row in rows),
            descendant_nodes=sum(row.descendant_nodes for row in rows),
        )
        for family, rows in sorted(family_rows.items())
    )
    return ValueBenchmarkResult(
        training=training,
        selection=selection,
        held_out=held_out,
        families=families,
        imitation_wins=sum(row.imitation_nodes < row.unguided_nodes
                           for row in held_out),
        descendant_wins=sum(row.descendant_nodes < row.unguided_nodes
                            for row in held_out),
        descendant_ties=sum(row.descendant_nodes == row.unguided_nodes
                            for row in held_out),
        descendant_losses=sum(row.descendant_nodes > row.unguided_nodes
                              for row in held_out),
        large_transfer=tuple(
            evaluate_large_transfer(imitation, descendant, node_budget=budget)
            for budget in (50, 100)
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = benchmark()
    if arguments.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(result)


if __name__ == "__main__":
    main()
