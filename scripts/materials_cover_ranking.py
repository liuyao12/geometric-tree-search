#!/usr/bin/env python3
"""RL-compatible branch ranking for lattice-free overlapping-cover search.

This module deliberately has no geometry API.  A candidate is described only
by the objects it covers, its cost, the current cover domains, and pairwise
compatibility supplied by the covering engine.  Consequently the same ranker
can guide covers of atoms, learned motifs, or clusters of clusters.

Minimal solver integration contract
-----------------------------------
At a non-forced branch the solver calls :func:`branch_features` once per legal
candidate with:

* ``candidate``: an occurrence exposing ``id``, ``covers``, and ``cost``;
* ``uncovered`` and ``covered``: current object-ID sets;
* ``selected``: selected occurrences (not their coordinates);
* ``domains``: legal occurrence sequences for every currently uncovered
  object after propagation;
* ``legal_occurrences``: the union of those domains; and
* ``pair_allowed(left, right)``: the solver's constraint predicate.

It then orders candidates by descending ``ranker.score(features)``.  Search,
propagation, admissibility, and backtracking remain owned by the solver.  After
an episode, one :class:`DescendantBranchOutcome` may be recorded for each
tried option.  It says whether that option's subtree found a cover, how much
it improved the incumbent, and how many descendant nodes it consumed.
:func:`train_from_descendant_outcomes` converts those records into ordinary
:class:`BranchExample` rows.  A solver with its own trace record only needs a
small adapter returning either dataclass; no ground-truth lattice or Cartesian
coordinate is part of this contract.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Hashable, Iterable, Mapping, Protocol, Sequence, Union


class OccurrenceLike(Protocol):
    """Structural type needed by the feature extractor."""

    id: Hashable
    covers: frozenset[Hashable]
    cost: float


PairAllowed = Callable[[OccurrenceLike, OccurrenceLike], bool]


FEATURE_NAMES = (
    "bias",
    "gain_fraction",
    "log_gain",
    "cost_per_gain",
    "cost_fraction",
    "overlap_fraction",
    "pivot_domain_inverse",
    "covered_domain_inverse_mean",
    "covered_domain_inverse_max",
    "forced_after_fraction",
    "peer_conflict_fraction",
    "uncovered_fraction",
    "selected_fraction",
    "incumbent_slack",
)


def _finite(value: float) -> float:
    return value if math.isfinite(value) else 0.0


def branch_features(
    *,
    candidate: OccurrenceLike,
    uncovered: Iterable[Hashable],
    covered: Iterable[Hashable],
    selected: Sequence[OccurrenceLike],
    domains: Mapping[Hashable, Sequence[OccurrenceLike]],
    legal_occurrences: Sequence[OccurrenceLike],
    pair_allowed: PairAllowed,
    universe_size: int,
    pivot_domain_size: int,
    selected_cost: float = 0.0,
    incumbent_cost: float | None = None,
) -> dict[str, float]:
    """Extract bounded, generic features for one legal branch candidate.

    Domain statistics make locally scarce objects valuable; conflict density
    measures how much a placement constrains other still-legal placements.
    ``forced_after_fraction`` is an inexpensive one-step propagation estimate:
    it counts newly covered objects whose current domain has size one or two,
    since selecting the candidate removes the need to branch on those objects.
    """

    uncovered_set = frozenset(uncovered)
    covered_set = frozenset(covered)
    support = frozenset(candidate.covers)
    newly_covered = support & uncovered_set
    gain = len(newly_covered)
    safe_gain = max(gain, 1)
    safe_universe = max(int(universe_size), 1)

    domain_sizes = [max(len(domains.get(item, ())), 1) for item in newly_covered]
    inverse_domains = [1.0 / size for size in domain_sizes]
    scarce_mean = (
        sum(inverse_domains) / len(inverse_domains) if inverse_domains else 0.0
    )
    scarce_max = max(inverse_domains, default=0.0)
    forced_after = (
        sum(size <= 2 for size in domain_sizes) / len(domain_sizes)
        if domain_sizes
        else 0.0
    )

    peers = [other for other in legal_occurrences if other.id != candidate.id]
    conflict_fraction = (
        sum(not pair_allowed(candidate, other) for other in peers) / len(peers)
        if peers
        else 0.0
    )
    incumbent_slack = 0.0
    if incumbent_cost is not None and math.isfinite(incumbent_cost):
        incumbent_slack = (incumbent_cost - selected_cost - candidate.cost) / max(
            abs(incumbent_cost), 1.0
        )

    values = {
        "bias": 1.0,
        "gain_fraction": gain / max(len(uncovered_set), 1),
        "log_gain": math.log1p(gain) / math.log1p(safe_universe),
        "cost_per_gain": candidate.cost / safe_gain,
        "cost_fraction": candidate.cost / max(abs(selected_cost) + candidate.cost, 1.0),
        "overlap_fraction": len(support & covered_set) / max(len(support), 1),
        "pivot_domain_inverse": 1.0 / max(pivot_domain_size, 1),
        "covered_domain_inverse_mean": scarce_mean,
        "covered_domain_inverse_max": scarce_max,
        "forced_after_fraction": forced_after,
        "peer_conflict_fraction": conflict_fraction,
        "uncovered_fraction": len(uncovered_set) / safe_universe,
        "selected_fraction": len(selected) / max(len(selected) + len(uncovered_set), 1),
        "incumbent_slack": incumbent_slack,
    }
    return {name: _finite(float(values[name])) for name in FEATURE_NAMES}


@dataclass(frozen=True)
class BranchExample:
    """One candidate's outcome within a particular branch context."""

    context_id: Hashable
    candidate_id: Hashable
    features: Mapping[str, float]
    reward: float


@dataclass(frozen=True)
class DescendantBranchOutcome:
    """Search outcome below one candidate in one branch context.

    ``feasible`` means that the explored subtree produced a complete cover.
    ``incumbent_improvement`` is positive when that cover improves the
    incumbent visible at the branch (zero is appropriate for feasibility-only
    traces). ``descendant_nodes`` includes work below the candidate, not the
    parent branch itself. These fields are deliberately solver-independent.
    """

    context_id: Hashable
    candidate_id: Hashable
    features: Mapping[str, float]
    feasible: bool
    incumbent_improvement: float
    descendant_nodes: int


@dataclass(frozen=True)
class DescendantRewardConfig:
    """Auditable scalarization of branch quality for pairwise ranking."""

    feasible_reward: float = 1.0
    improvement_weight: float = 1.0
    node_weight: float = 0.1

    def reward(self, outcome: DescendantBranchOutcome) -> float:
        if outcome.descendant_nodes < 0:
            raise ValueError("descendant_nodes must be nonnegative")
        if not math.isfinite(outcome.incumbent_improvement):
            raise ValueError("incumbent_improvement must be finite")
        weights = (
            self.feasible_reward,
            self.improvement_weight,
            self.node_weight,
        )
        if not all(math.isfinite(value) and value >= 0.0 for value in weights):
            raise ValueError("descendant reward weights must be finite and nonnegative")
        return (
            self.feasible_reward * float(outcome.feasible)
            + self.improvement_weight * outcome.incumbent_improvement
            - self.node_weight * math.log1p(outcome.descendant_nodes)
        )


TraceAdapter = Callable[[Any], Union[BranchExample, DescendantBranchOutcome]]


@dataclass(frozen=True)
class DescendantTrainingReport:
    """Summary of deterministic value/ranking training from search traces."""

    ranker: "LinearBranchRanker"
    examples: tuple[BranchExample, ...]
    context_count: int
    outcome_count: int
    feasible_outcome_count: int
    improving_outcome_count: int
    min_reward: float
    max_reward: float


class LinearBranchRanker:
    """Deterministic pairwise linear ranker suitable as an RL baseline.

    ``fit`` performs online pairwise large-margin updates.  Only reward order
    within a context matters, so rewards from different search trees need not
    share a scale.  This is intentionally small and auditable; a neural policy
    can later implement the same ``score(features)`` interface.
    """

    def __init__(self, weights: Mapping[str, float] | None = None) -> None:
        self.weights = {name: 0.0 for name in FEATURE_NAMES}
        if weights:
            unknown = set(weights) - set(FEATURE_NAMES)
            if unknown:
                raise ValueError(f"unknown feature weights: {sorted(unknown)!r}")
            self.weights.update({name: float(value) for name, value in weights.items()})

    def score(self, features: Mapping[str, float]) -> float:
        return sum(self.weights[name] * float(features.get(name, 0.0)) for name in FEATURE_NAMES)

    def rank(
        self, candidates: Iterable[tuple[Hashable, Mapping[str, float]]]
    ) -> list[Hashable]:
        """Return candidate IDs best-first with a stable, generic tie break."""

        scored = [
            (self.score(features), repr(candidate_id), candidate_id)
            for candidate_id, features in candidates
        ]
        return [candidate_id for _, _, candidate_id in sorted(scored, key=lambda row: (-row[0], row[1]))]

    def fit(
        self,
        examples: Iterable[BranchExample],
        *,
        epochs: int = 30,
        learning_rate: float = 0.15,
        margin: float = 0.1,
        l2: float = 1e-4,
    ) -> "LinearBranchRanker":
        """Learn from candidate rewards using deterministic pairwise updates."""

        if epochs < 0 or learning_rate <= 0.0 or margin < 0.0 or l2 < 0.0:
            raise ValueError("invalid training hyperparameters")
        grouped: dict[Hashable, list[BranchExample]] = {}
        for example in examples:
            if not math.isfinite(example.reward):
                raise ValueError("branch rewards must be finite")
            grouped.setdefault(example.context_id, []).append(example)

        pairs: list[tuple[BranchExample, BranchExample]] = []
        for context_id in sorted(grouped, key=repr):
            group = sorted(grouped[context_id], key=lambda item: repr(item.candidate_id))
            for left_index, left in enumerate(group):
                for right in group[left_index + 1 :]:
                    if left.reward == right.reward:
                        continue
                    pairs.append((left, right) if left.reward > right.reward else (right, left))

        for _ in range(epochs):
            for better, worse in pairs:
                difference = {
                    name: float(better.features.get(name, 0.0))
                    - float(worse.features.get(name, 0.0))
                    for name in FEATURE_NAMES
                }
                gap = sum(self.weights[name] * difference[name] for name in FEATURE_NAMES)
                if gap < margin:
                    for name in FEATURE_NAMES:
                        self.weights[name] += learning_rate * difference[name]
                if l2:
                    shrink = max(0.0, 1.0 - learning_rate * l2)
                    for name in FEATURE_NAMES:
                        self.weights[name] *= shrink
        return self


def train_from_descendant_outcomes(
    records: Iterable[Any],
    *,
    adapter: TraceAdapter | None = None,
    reward_config: DescendantRewardConfig | None = None,
    ranker: LinearBranchRanker | None = None,
    fit_kwargs: Mapping[str, Any] | None = None,
) -> DescendantTrainingReport:
    """Train a branch ranker from descendant returns or ready-made examples.

    Each input may already be a :class:`BranchExample` or a
    :class:`DescendantBranchOutcome`.  For a solver-specific trace type, pass
    ``adapter(record)`` returning one of those dataclasses.  That is the entire
    integration surface: the adapter copies the branch context/candidate IDs,
    the feature row captured at the parent, feasibility, incumbent improvement,
    and descendant-node count.  It does not expose coordinates or solver state.

    This is supervised pairwise value/ranking from completed search traces,
    not a claim of online reinforcement learning.  A future RL loop can reuse
    the same examples while changing how traces are collected.
    """

    config = reward_config or DescendantRewardConfig()
    learner = ranker if ranker is not None else LinearBranchRanker()
    examples: list[BranchExample] = []
    outcome_count = 0
    feasible_count = 0
    improving_count = 0

    for raw_record in records:
        record = adapter(raw_record) if adapter is not None else raw_record
        if isinstance(record, BranchExample):
            example = record
        elif isinstance(record, DescendantBranchOutcome):
            outcome_count += 1
            feasible_count += int(record.feasible)
            improving_count += int(record.incumbent_improvement > 0.0)
            example = BranchExample(
                context_id=record.context_id,
                candidate_id=record.candidate_id,
                features=record.features,
                reward=config.reward(record),
            )
        else:
            raise TypeError(
                "trace adapter must return BranchExample or "
                "DescendantBranchOutcome"
            )
        if not math.isfinite(example.reward):
            raise ValueError("branch rewards must be finite")
        examples.append(example)

    if not examples:
        raise ValueError("at least one branch training record is required")
    learner.fit(examples, **dict(fit_kwargs or {}))
    frozen = tuple(examples)
    rewards = [example.reward for example in frozen]
    return DescendantTrainingReport(
        ranker=learner,
        examples=frozen,
        context_count=len({example.context_id for example in frozen}),
        outcome_count=outcome_count,
        feasible_outcome_count=feasible_count,
        improving_outcome_count=improving_count,
        min_reward=min(rewards),
        max_reward=max(rewards),
    )


def solver_branch_feature_rows(problem, context, options):
    """Extract feature rows from the solver's generic branch callback."""

    occurrences = problem.occurrences
    selected = tuple(occurrences[index]
                     for index in context.selected_indices)
    domains = {
        item: tuple(occurrences[index] for index in indices)
        for item, indices in context.domains.items()
    }
    legal = tuple(occurrences[index] for index in context.legal_indices)
    index_by_identity = {
        id(occurrence): index for index, occurrence in enumerate(occurrences)
    }
    features = {}
    for index in options:
        features[index] = branch_features(
                candidate=occurrences[index],
                uncovered=context.uncovered,
                covered=context.covered,
                selected=selected,
                domains=domains,
                legal_occurrences=legal,
                pair_allowed=lambda left, right: problem._pair_allowed(
                    index_by_identity[id(left)], index_by_identity[id(right)],
                ),
                universe_size=len(problem.universe),
                pivot_domain_size=len(options),
                selected_cost=context.selected_cost,
                incumbent_cost=context.incumbent_cost,
            )
    return features


def make_solver_branch_orderer(ranker: LinearBranchRanker):
    """Adapt a feature ranker to ``OverlapCoverProblem.solve``.

    The adapter intentionally uses only the public occurrence collection and
    the lattice-free :class:`~materials_overlap_cover.BranchContext`.  The
    solver remains responsible for validating that the returned order is a
    permutation of the admissible branch candidates.
    """

    def order(problem, context, options):
        position = {index: rank for rank, index in enumerate(options)}
        features = solver_branch_feature_rows(problem, context, options)
        return tuple(sorted(
            options,
            key=lambda index: (-ranker.score(features[index]), position[index]),
        ))

    return order


@dataclass(frozen=True)
class TeacherImitationReport:
    """Audit record for one exact-search policy-imitation pass."""

    ranker: LinearBranchRanker
    teacher_result: Any
    examples: tuple[BranchExample, ...]
    recorded_context_count: int
    labeled_context_count: int
    example_count: int
    positive_example_count: int


def train_from_exact_teacher(
    problem,
    *,
    ranker: LinearBranchRanker | None = None,
    solve_kwargs: Mapping[str, Any] | None = None,
    fit_kwargs: Mapping[str, Any] | None = None,
) -> TeacherImitationReport:
    """Imitate branches belonging to a certified exact teacher solution.

    The teacher runs with the solver's ordinary candidate order while a
    callback records feature rows for every observed branch.  Once exact
    search finishes, candidates in the final optimal cover receive reward
    one and the other candidates in the same context receive reward zero.
    Contexts with no teacher-selected candidate are not used: they belong to
    parts of the search tree for which the final cover supplies no action
    label.

    This is behavioral cloning from exact search, not yet reinforcement
    learning.  The example/reward interface is intentionally identical to the
    one a later search-cost or return-based trainer can use.
    """

    solver_options = dict(solve_kwargs or {})
    if "branch_orderer" in solver_options:
        raise ValueError("solve_kwargs must not override the teacher recorder")
    learner = ranker if ranker is not None else LinearBranchRanker()
    recorded: list[tuple[int, tuple[int, ...], dict[int, dict[str, float]]]] = []

    def recorder(instance, context, options):
        rows = solver_branch_feature_rows(instance, context, options)
        recorded.append((len(recorded), tuple(options), rows))
        # Preserve the exact solver's proposed order.  The recorder observes
        # the teacher; it does not guide it.
        return options

    teacher = problem.solve(branch_orderer=recorder, **solver_options)
    if not teacher.optimal:
        raise ValueError("teacher solve must prove optimality before training")
    if not teacher.complete:
        raise ValueError("teacher solve has no complete cover to imitate")

    selected_ids = frozenset(teacher.selected)
    selected_indices = frozenset(
        index
        for index, occurrence in enumerate(problem.occurrences)
        if occurrence.id in selected_ids
    )
    examples: list[BranchExample] = []
    labeled_contexts = 0
    positives = 0
    for context_id, options, rows in recorded:
        positive_options = selected_indices & frozenset(options)
        if not positive_options:
            continue
        labeled_contexts += 1
        for index in options:
            reward = 1.0 if index in positive_options else 0.0
            positives += int(reward)
            examples.append(
                BranchExample(
                    context_id=context_id,
                    candidate_id=problem.occurrences[index].id,
                    features=rows[index],
                    reward=reward,
                )
            )

    learner.fit(examples, **dict(fit_kwargs or {}))
    frozen_examples = tuple(examples)
    return TeacherImitationReport(
        ranker=learner,
        teacher_result=teacher,
        examples=frozen_examples,
        recorded_context_count=len(recorded),
        labeled_context_count=labeled_contexts,
        example_count=len(frozen_examples),
        positive_example_count=positives,
    )
