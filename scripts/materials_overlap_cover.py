#!/usr/bin/env python3
"""Lattice-free overlapping-cover search for learned material clusters.

The engine deliberately knows nothing about coordinates, lattices, or rotations.
Upstream code supplies a finite universe of object IDs and already-enumerated
cluster occurrences.  An occurrence may represent any rigid transformation of
a learned cluster and may overlap other selected occurrences.

The exact solver is a small CSP/GCTS kernel: it propagates forced placements,
branches on the most-constrained uncovered object, and uses branch-and-bound to
minimize ``(total occurrence cost, number of occurrences)`` lexicographically.
Pairwise compatibility can encode markings, geometric clashes, or other local
constraints without changing the covering algorithm.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, FrozenSet, Hashable, Iterable, Mapping, Optional, Sequence, Tuple, Union


ObjectId = Hashable
OccurrenceId = Hashable


@dataclass(frozen=True)
class Occurrence:
    """One candidate placement of a cluster.

    ``covers`` may overlap the support of any other occurrence.  Pairwise
    constraints, rather than overlap itself, decide whether two placements are
    mutually admissible.
    """

    id: OccurrenceId
    covers: FrozenSet[ObjectId]
    cost: float = 1.0

    def __init__(
        self,
        id: OccurrenceId,
        covers: Iterable[ObjectId],
        cost: float = 1.0,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "covers", frozenset(covers))
        object.__setattr__(self, "cost", float(cost))


PairPredicate = Callable[[Occurrence, Occurrence], bool]


@dataclass(frozen=True)
class BranchContext:
    """Lattice-free cover state exposed to a branch-ordering policy."""

    selected_indices: Tuple[int, ...]
    covered: FrozenSet[ObjectId]
    uncovered: FrozenSet[ObjectId]
    pivot: ObjectId
    domains: Mapping[ObjectId, Tuple[int, ...]]
    legal_indices: Tuple[int, ...]
    selected_cost: float
    incumbent_cost: Optional[float]


BranchOrderer = Callable[
    ["OverlapCoverProblem", BranchContext, Tuple[int, ...]], Sequence[int]
]


@dataclass(frozen=True)
class BranchStarted:
    """Observation emitted before a non-forced branch is explored."""

    branch_id: int
    context: BranchContext
    ordered_indices: Tuple[int, ...]


@dataclass(frozen=True)
class BranchCandidateOutcome:
    """Outcome of one candidate subtree in a non-forced branch.

    ``feasible`` is true when the explored subtree reached a complete cover,
    false when it did not, and ``None`` when a node budget interrupted the
    subtree before either conclusion.  If a cover was reached before an
    interruption it remains true.  ``best_objective`` is the best complete
    ``(cost, occurrence count)`` actually encountered in this subtree; it is
    deliberately not copied from the global incumbent.
    """

    branch_id: int
    context: BranchContext
    candidate_index: int
    candidate_position: int
    descendant_expanded_nodes: int
    feasible: Optional[bool]
    interrupted: bool
    improved_incumbent: bool
    incumbent_before: Optional[Tuple[float, int]]
    incumbent_after: Optional[Tuple[float, int]]
    best_objective: Optional[Tuple[float, int]]


BranchEvent = Union[BranchStarted, BranchCandidateOutcome]
BranchObserver = Callable[["OverlapCoverProblem", BranchEvent], None]


def _bit_indices(mask: int) -> Iterable[int]:
    """Yield set-bit indices in ascending input order."""

    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def _popcount(mask: int) -> int:
    """Python 3.9-compatible population count, executed in C via ``bin``."""

    return bin(mask).count("1")


@dataclass(frozen=True)
class CoverResult:
    """A cover and auditable search counters."""

    complete: bool
    selected: Tuple[OccurrenceId, ...]
    covered: FrozenSet[ObjectId]
    total_cost: float
    expanded_nodes: int
    backtracks: int
    pruned_nodes: int
    memo_hits: int = 0
    optimal: bool = True


class OverlapCoverProblem:
    """Finite overlapping-cover CSP, independent of the source geometry.

    Args:
        universe: Objects that must each be covered at least once.
        occurrences: Candidate cluster placements.
        conflict_pairs: Explicit unordered pairs of occurrence IDs that cannot
            coexist.
        compatible_pairs: If supplied, every pair of selected occurrences must
            occur in this explicit unordered allow-list.
        conflict_predicate: Returns true when two occurrences conflict.
        compatibility_predicate: Returns true when two occurrences may coexist.

    Explicit conflicts take precedence over compatibility.  Overlap is allowed
    by default and is never treated as a conflict.
    """

    def __init__(
        self,
        universe: Iterable[ObjectId],
        occurrences: Sequence[Occurrence],
        *,
        conflict_pairs: Iterable[Tuple[OccurrenceId, OccurrenceId]] = (),
        compatible_pairs: Optional[
            Iterable[Tuple[OccurrenceId, OccurrenceId]]
        ] = None,
        conflict_predicate: Optional[PairPredicate] = None,
        compatibility_predicate: Optional[PairPredicate] = None,
    ) -> None:
        self.universe = frozenset(universe)
        self.occurrences = tuple(occurrences)
        self._conflicts = frozenset(
            frozenset((left, right)) for left, right in conflict_pairs
        )
        self._compatible = (
            None
            if compatible_pairs is None
            else frozenset(
                frozenset((left, right)) for left, right in compatible_pairs
            )
        )
        self._conflict_predicate = conflict_predicate
        self._compatibility_predicate = compatibility_predicate
        self._validate()

        by_object = {item: [] for item in self.universe}
        for index, occurrence in enumerate(self.occurrences):
            for item in occurrence.covers:
                by_object[item].append(index)
        self._by_object = {
            item: tuple(indices) for item, indices in by_object.items()
        }

    def _validate(self) -> None:
        ids = [occurrence.id for occurrence in self.occurrences]
        if len(set(ids)) != len(ids):
            raise ValueError("occurrence IDs must be unique")
        for occurrence in self.occurrences:
            if not occurrence.covers:
                raise ValueError(f"occurrence {occurrence.id!r} covers nothing")
            outside = occurrence.covers - self.universe
            if outside:
                raise ValueError(
                    f"occurrence {occurrence.id!r} covers objects outside the "
                    f"universe: {outside!r}"
                )
            if not math.isfinite(occurrence.cost) or occurrence.cost < 0.0:
                raise ValueError("occurrence costs must be finite and nonnegative")
        known = set(ids)
        pair_ids = set().union(*self._conflicts) if self._conflicts else set()
        if self._compatible:
            pair_ids.update(set().union(*self._compatible))
        unknown = pair_ids - known
        if unknown:
            raise ValueError(f"pair constraint refers to unknown IDs: {unknown!r}")

    def _pair_allowed(self, left_index: int, right_index: int) -> bool:
        if left_index == right_index:
            return True
        left = self.occurrences[left_index]
        right = self.occurrences[right_index]
        pair = frozenset((left.id, right.id))
        if pair in self._conflicts:
            return False
        if self._compatible is not None and pair not in self._compatible:
            return False
        if self._conflict_predicate is not None:
            if self._conflict_predicate(left, right):
                return False
        if self._compatibility_predicate is not None:
            if not self._compatibility_predicate(left, right):
                return False
        return True

    def _allowed_with_selected(
        self, candidate: int, selected: FrozenSet[int]
    ) -> bool:
        return all(self._pair_allowed(candidate, other) for other in selected)

    def _result(
        self,
        selected: Iterable[int],
        *,
        expanded_nodes: int,
        backtracks: int,
        pruned_nodes: int,
        memo_hits: int = 0,
        optimal: bool = True,
    ) -> CoverResult:
        chosen = tuple(sorted(set(selected)))
        covered = frozenset().union(
            *(self.occurrences[index].covers for index in chosen)
        ) if chosen else frozenset()
        return CoverResult(
            complete=self.universe <= covered,
            selected=tuple(self.occurrences[index].id for index in chosen),
            covered=covered,
            total_cost=sum(self.occurrences[index].cost for index in chosen),
            expanded_nodes=expanded_nodes,
            backtracks=backtracks,
            pruned_nodes=pruned_nodes,
            memo_hits=memo_hits,
            optimal=optimal,
        )

    def greedy(self) -> CoverResult:
        """Fast baseline: repeatedly choose best cost per newly covered object.

        It deliberately performs no backtracking, so it can be trapped by an
        initially attractive occurrence.  Ties are resolved by input order.
        """

        selected: FrozenSet[int] = frozenset()
        covered: FrozenSet[ObjectId] = frozenset()
        expanded = 0
        while not self.universe <= covered:
            candidates = []
            for index, occurrence in enumerate(self.occurrences):
                if index in selected or not self._allowed_with_selected(index, selected):
                    continue
                gain = len(occurrence.covers - covered)
                if gain:
                    ratio = occurrence.cost / gain
                    candidates.append((ratio, -gain, occurrence.cost, index))
            if not candidates:
                break
            index = min(candidates)[-1]
            selected = selected | {index}
            covered = covered | self.occurrences[index].covers
            expanded += 1
        return self._result(
            selected,
            expanded_nodes=expanded,
            backtracks=0,
            pruned_nodes=0,
            optimal=False,
        )

    def solve(
        self,
        *,
        frontier_memo: bool = True,
        partition_branches: bool = True,
        packing_bound: bool = True,
        max_expanded_nodes: Optional[int] = None,
        branch_orderer: Optional[BranchOrderer] = None,
        branch_observer: Optional[BranchObserver] = None,
    ) -> CoverResult:
        """Return an optimal compatible full cover, or an incomplete result.

        ``frontier_memo`` merges histories only when their canonical remaining
        CSPs are identical. ``partition_branches`` assigns every completion to
        the branch containing its earliest selected option at the pivot, which
        avoids enumerating the same set in multiple orders.  Both switches are
        exposed for exact ablations. ``packing_bound`` greedily finds uncovered
        objects with pairwise-disjoint live occurrence domains; they provably
        require distinct future placements and strengthen the lower bound.

        If ``max_expanded_nodes`` interrupts the proof, the best complete
        incumbent found so far is returned with ``optimal=False``.

        ``branch_observer`` receives immutable events for non-forced branch
        contexts and candidate outcomes.  It is observational only: its return
        value is ignored and enabling it does not change candidate order,
        legality, memoization, bounds, incumbents, or search counters.
        """

        if max_expanded_nodes is not None:
            if (
                isinstance(max_expanded_nodes, bool)
                or not isinstance(max_expanded_nodes, int)
                or max_expanded_nodes < 0
            ):
                raise ValueError("max_expanded_nodes must be nonnegative or None")

        incumbent = self.greedy()
        best: Optional[int] = None
        best_cost = math.inf
        best_count = math.inf
        if incumbent.complete:
            selected_ids = set(incumbent.selected)
            best = sum(
                1 << index
                for index, occurrence in enumerate(self.occurrences)
                if occurrence.id in selected_ids
            )
            best_cost = incumbent.total_cost
            best_count = _popcount(best)

        # Dense integer state for the exact kernel.  Arbitrary external object
        # and occurrence IDs remain at the API boundary; only stable local
        # indices enter the search.
        objects = tuple(sorted(self.universe, key=lambda item: repr(item)))
        object_index = {item: index for index, item in enumerate(objects)}
        full_object_mask = (1 << len(objects)) - 1
        occurrence_count = len(self.occurrences)
        full_occurrence_mask = (1 << occurrence_count) - 1
        support_masks = tuple(
            sum(1 << object_index[item] for item in occurrence.covers)
            for occurrence in self.occurrences
        )
        by_object_masks = [0] * len(objects)
        for occurrence_index, support in enumerate(support_masks):
            remaining = support
            while remaining:
                object_bit = remaining & -remaining
                by_object_masks[object_bit.bit_length() - 1] |= (
                    1 << occurrence_index
                )
                remaining ^= object_bit
        compatibility_masks = []
        for selected_index in range(occurrence_count):
            mask = 0
            for candidate_index in range(occurrence_count):
                # Preserve _allowed_with_selected's argument order even for a
                # user predicate that happens not to be symmetric.
                if self._pair_allowed(candidate_index, selected_index):
                    mask |= 1 << candidate_index
            compatibility_masks.append(mask)
        costs = tuple(occurrence.cost for occurrence in self.occurrences)

        expanded_nodes = 0
        backtracks = 0
        pruned_nodes = 0
        memo_hits = 0
        interrupted = False
        next_branch_id = 0
        # The legacy/history key must include exclusions: the same selected
        # set can have a different future under sound branch partitioning.
        visited: set[Tuple[int, int]] = set()
        frontier_best: dict[Tuple[int, int], Tuple[float, int]] = {}

        def occurrences_touching(object_mask: int) -> int:
            result = 0
            remaining = object_mask
            while remaining:
                bit = remaining & -remaining
                result |= by_object_masks[bit.bit_length() - 1]
                remaining ^= bit
            return result

        def bound_prunes(
            selected: int,
            covered: int,
            cost: float,
            candidate_mask: int,
            selected_count: int,
        ) -> Tuple[bool, Optional[Tuple[float, int]]]:
            nonlocal pruned_nodes
            if best is None:
                return False
            uncovered = full_object_mask & ~covered
            if not uncovered:
                return False
            available = candidate_mask & occurrences_touching(uncovered)
            if not available:
                return False
            max_gain = max(
                _popcount(support_masks[index] & uncovered)
                for index in _bit_indices(available)
            )
            min_needed = math.ceil(_popcount(uncovered) / max_gain)
            min_cost = min(costs[index] for index in _bit_indices(available))
            per_object_cost = 0.0
            object_domains = []
            remaining = uncovered
            while remaining:
                object_bit = remaining & -remaining
                object_id = object_bit.bit_length() - 1
                domain = candidate_mask & by_object_masks[
                    object_id
                ]
                domain_min_cost = min(
                    costs[index] for index in _bit_indices(domain)
                )
                per_object_cost = max(
                    per_object_cost,
                    domain_min_cost,
                )
                object_domains.append(
                    (object_id, domain, _popcount(domain), domain_min_cost)
                )
                remaining ^= object_bit

            base_remaining_cost = max(
                min_needed * min_cost,
                per_object_cost,
            )

            def lower_bound_prunes(
                remaining_cost: float, remaining_count: int
            ) -> bool:
                lower_cost = cost + remaining_cost
                lower_count = selected_count + remaining_count
                return lower_cost > best_cost + 1e-12 or (
                    abs(lower_cost - best_cost) <= 1e-12
                    and lower_count >= best_count
                )

            # Most visited states are already discharged by the cheap bound;
            # only construct packing witnesses when they can add information.
            if lower_bound_prunes(base_remaining_cost, min_needed):
                pruned_nodes += 1
                return True

            packing_count = 0
            packing_cost = 0.0
            if packing_bound:
                # Each ordering yields a sound maximal packing.  Taking the
                # strongest count and cost bounds independently remains sound.
                for ordered_domains in (
                    sorted(object_domains, key=lambda row: (row[2], row[0])),
                    sorted(
                        object_domains,
                        key=lambda row: (-row[3], row[2], row[0]),
                    ),
                ):
                    used_occurrences = 0
                    witness_count = 0
                    witness_cost = 0.0
                    for _, domain, _, domain_min_cost in ordered_domains:
                        if domain & used_occurrences:
                            continue
                        used_occurrences |= domain
                        witness_count += 1
                        witness_cost += domain_min_cost
                    packing_count = max(packing_count, witness_count)
                    packing_cost = max(packing_cost, witness_cost)

            min_needed = max(min_needed, packing_count)
            remaining_cost = max(
                min_needed * min_cost,
                per_object_cost,
                packing_cost,
            )
            if lower_bound_prunes(remaining_cost, min_needed):
                pruned_nodes += 1
                return True
            return False

        def search(
            selected: int,
            covered: int,
            cost: float,
            excluded: int,
            compatible: int,
            selected_count: int,
        ) -> Tuple[bool, Optional[Tuple[float, int]]]:
            nonlocal best, best_cost, best_count
            nonlocal expanded_nodes, backtracks, pruned_nodes, memo_hits
            nonlocal interrupted

            if interrupted:
                return False, None

            # Unit propagation: a currently uncovered object with one legal
            # occurrence forces that occurrence into every completion.
            while True:
                uncovered = full_object_mask & ~covered
                if not uncovered:
                    break
                candidate_mask = compatible & ~selected & ~excluded & full_occurrence_mask
                best_domain = 0
                best_domain_size = occurrence_count + 1
                best_object_index = len(objects)
                remaining = uncovered
                while remaining:
                    object_bit = remaining & -remaining
                    item_index = object_bit.bit_length() - 1
                    domain = candidate_mask & by_object_masks[item_index]
                    domain_size = _popcount(domain)
                    if (
                        domain_size < best_domain_size
                        or (
                            domain_size == best_domain_size
                            and item_index < best_object_index
                        )
                    ):
                        best_domain = domain
                        best_domain_size = domain_size
                        best_object_index = item_index
                    remaining ^= object_bit
                domain_size = best_domain_size
                if domain_size == 0:
                    backtracks += 1
                    return False, None
                if domain_size != 1:
                    break
                forced_bit = best_domain
                forced = forced_bit.bit_length() - 1
                selected |= forced_bit
                selected_count += 1
                covered |= support_masks[forced]
                compatible &= compatibility_masks[forced]
                cost += costs[forced]
                if best is not None and (
                    cost > best_cost + 1e-12
                    or (abs(cost - best_cost) <= 1e-12
                        and selected_count >= best_count
                        and covered != full_object_mask)
                ):
                    pruned_nodes += 1
                    return False, None

            history_key = (selected, excluded)
            if not frontier_memo:
                if history_key in visited:
                    pruned_nodes += 1
                    return False, None
                visited.add(history_key)
            else:
                uncovered = full_object_mask & ~covered
                candidate_mask = compatible & ~selected & ~excluded & full_occurrence_mask
                viable = candidate_mask & occurrences_touching(uncovered)
                key = (uncovered, viable)
                prefix = (cost, selected_count)
                previous = frontier_best.get(key)
                if previous is not None and prefix >= previous:
                    memo_hits += 1
                    pruned_nodes += 1
                    return False, None
                frontier_best[key] = prefix

            if (
                max_expanded_nodes is not None
                and expanded_nodes >= max_expanded_nodes
            ):
                interrupted = True
                return False, None
            expanded_nodes += 1

            if covered == full_object_mask:
                objective = (cost, selected_count)
                if objective < (best_cost, best_count):
                    best = selected
                    best_cost, best_count = objective
                return True, objective

            candidate_mask = compatible & ~selected & ~excluded & full_occurrence_mask
            if bound_prunes(
                selected, covered, cost, candidate_mask, selected_count
            ):
                return False, None

            # Most-constrained uncovered-object branching (MRV).
            options = best_domain
            uncovered = full_object_mask & ~covered
            ordered = sorted(
                _bit_indices(options),
                key=lambda index: (
                    costs[index]
                    / _popcount(support_masks[index] & uncovered),
                    -_popcount(support_masks[index] & uncovered),
                    costs[index],
                    index,
                ),
            )
            context = None
            if branch_orderer is not None or branch_observer is not None:
                domain_map = {}
                remaining_objects = uncovered
                while remaining_objects:
                    object_bit = remaining_objects & -remaining_objects
                    item_index = object_bit.bit_length() - 1
                    domain_map[objects[item_index]] = tuple(_bit_indices(
                        candidate_mask & by_object_masks[item_index]))
                    remaining_objects ^= object_bit
                legal = candidate_mask & occurrences_touching(uncovered)
                context = BranchContext(
                    selected_indices=tuple(_bit_indices(selected)),
                    covered=frozenset(
                        objects[index] for index in _bit_indices(covered)),
                    uncovered=frozenset(
                        objects[index] for index in _bit_indices(uncovered)),
                    pivot=objects[best_object_index],
                    domains=MappingProxyType(domain_map),
                    legal_indices=tuple(_bit_indices(legal)),
                    selected_cost=cost,
                    incumbent_cost=(best_cost if math.isfinite(best_cost) else None),
                )
            if branch_orderer is not None:
                proposed = tuple(branch_orderer(
                    self, context, tuple(ordered)))
                if (len(proposed) != len(ordered)
                        or set(proposed) != set(ordered)):
                    raise ValueError(
                        "branch_orderer must return a permutation of candidate indices")
                ordered = list(proposed)
            branch_id = -1
            if branch_observer is not None:
                nonlocal next_branch_id
                branch_id = next_branch_id
                next_branch_id += 1
                branch_observer(
                    self,
                    BranchStarted(branch_id, context, tuple(ordered)),
                )
            feasible = False
            subtree_best: Optional[Tuple[float, int]] = None
            earlier_options = 0
            for position, index in enumerate(ordered):
                occurrence_bit = 1 << index
                child_excluded = excluded
                if partition_branches:
                    child_excluded = excluded | earlier_options
                expanded_before = expanded_nodes
                incumbent_before = (
                    (best_cost, best_count) if best is not None else None
                )
                child_feasible, child_best = search(
                    selected | occurrence_bit,
                    covered | support_masks[index],
                    cost + costs[index],
                    child_excluded,
                    compatible & compatibility_masks[index],
                    selected_count + 1,
                )
                incumbent_after = (
                    (best_cost, best_count) if best is not None else None
                )
                if child_best is not None and (
                    subtree_best is None or child_best < subtree_best
                ):
                    subtree_best = child_best
                if branch_observer is not None:
                    branch_observer(
                        self,
                        BranchCandidateOutcome(
                            branch_id=branch_id,
                            context=context,
                            candidate_index=index,
                            candidate_position=position,
                            descendant_expanded_nodes=(
                                expanded_nodes - expanded_before
                            ),
                            feasible=(
                                True if child_feasible else
                                None if interrupted else False
                            ),
                            interrupted=interrupted,
                            improved_incumbent=(
                                incumbent_after is not None
                                and (
                                    incumbent_before is None
                                    or incumbent_after < incumbent_before
                                )
                            ),
                            incumbent_before=incumbent_before,
                            incumbent_after=incumbent_after,
                            best_objective=child_best,
                        ),
                    )
                feasible = child_feasible or feasible
                earlier_options |= occurrence_bit
                if interrupted:
                    break
            if not feasible and not interrupted:
                backtracks += 1
            return feasible, subtree_best

        search(0, 0, 0.0, 0, full_occurrence_mask, 0)
        if best is None:
            return CoverResult(
                complete=False,
                selected=(),
                covered=frozenset(),
                total_cost=math.inf,
                expanded_nodes=expanded_nodes,
                backtracks=backtracks,
                pruned_nodes=pruned_nodes,
                memo_hits=memo_hits,
                optimal=not interrupted,
            )
        return self._result(
            _bit_indices(best),
            expanded_nodes=expanded_nodes,
            backtracks=backtracks,
            pruned_nodes=pruned_nodes,
            memo_hits=memo_hits,
            optimal=not interrupted,
        )


def solve_overlap_cover(
    universe: Iterable[ObjectId],
    occurrences: Sequence[Occurrence],
    *,
    frontier_memo: bool = True,
    partition_branches: bool = True,
    packing_bound: bool = True,
    max_expanded_nodes: Optional[int] = None,
    branch_orderer: Optional[BranchOrderer] = None,
    branch_observer: Optional[BranchObserver] = None,
    **constraints: object,
) -> CoverResult:
    """Convenience wrapper around :class:`OverlapCoverProblem`."""

    return OverlapCoverProblem(universe, occurrences, **constraints).solve(
        frontier_memo=frontier_memo,
        partition_branches=partition_branches,
        packing_bound=packing_bound,
        max_expanded_nodes=max_expanded_nodes,
        branch_orderer=branch_orderer,
        branch_observer=branch_observer,
    )
