#!/usr/bin/env python3
"""Injectable causal incoming-port marking ablation for a sealed frontier.

Integration API
---------------
An exterior executor must supply three artifacts, in this order:

``training_traces``
    Causal choices observed wholly inside the training domain. Each trace names
    the already accepted incoming ports (at most interaction order two) and the
    outgoing frozen production chosen next.

``frozen_candidates``
    One target-blind candidate batch from the heldout frontier. Candidate
    geometry, production identity, incoming context, and baseline order are
    frozen before the scorer is invoked.

``score_callback(frozen_candidates)``
    A sealed oracle callback returning, for each candidate id, the subset of
    its novel colored-site keys that is correct. It cannot add or remove a
    candidate. A placement contributes atoms only when every emitted novel
    site is correct; otherwise it is an immediate geometric backtrack.

``run_causal_marking_ablation`` fits only the training traces, creates 31
within-parent label shuffles, ranks the byte-identical candidate batch under
all arms, and stops each arm after the same union of correct novel atoms has
been recovered. Thus proposal checks and backtracks are matched-quality work,
not incomparable fixed-step trajectories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from statistics import median
from typing import Callable, Hashable, Mapping, Sequence


@dataclass(frozen=True)
class CausalGrowthTrace:
    parent_occurrence: int
    parent_type: Hashable
    incoming_ports: tuple[Hashable, ...]
    chosen_outgoing_port: Hashable
    occurrence_domain: tuple[int, ...]
    causal: bool = True
    within_training_domain: bool = True


@dataclass(frozen=True)
class FrozenFrontierAction:
    candidate_id: int
    parent_occurrence: int
    parent_type: Hashable
    incoming_ports: tuple[Hashable, ...]
    production_id: Hashable
    novel_site_keys: tuple[Hashable, ...]
    baseline_order: tuple


@dataclass(frozen=True)
class SearchWork:
    arm: str
    matched_correct_novel_atoms: int
    proposal_checks: int
    geometric_backtracks: int
    wrong_novel_atoms_checked: int

    @property
    def proposal_plus_backtrack_work(self) -> int:
        return self.proposal_checks + self.geometric_backtracks


@dataclass(frozen=True)
class CausalFrontierMarkingAblation:
    training_traces: int
    maximum_interaction_order: int
    frozen_candidates: int
    candidate_digest: str
    matched_correct_novel_atoms: int
    marked: SearchWork
    unmarked: SearchWork
    shuffled: tuple[SearchWork, ...]
    shuffled_runs: int
    shuffled_median_proposals: float
    shuffled_median_backtracks: float
    shuffled_median_total_work: float
    empirical_work_p_value: float
    marked_beats_unmarked: bool
    marked_beats_shuffle_median: bool
    candidate_set_identical: bool
    all_traces_causal_and_train_only: bool
    within_parent_shuffle: bool
    heldout_labels_used_during_fit_or_candidate_freeze: bool
    benchmark_passed: bool


@dataclass(frozen=True)
class SealedIQCExecutorReadiness:
    training_atoms: int
    learned_occurrences: int
    causal_training_traces: int
    maximum_interaction_order: int
    frozen_productions: int
    exterior_candidates: int
    target_used_for_candidate_generation: bool
    executor_ready_for_ablation: bool
    reason: str


@dataclass(frozen=True)
class _Marking:
    exact: Mapping[tuple[Hashable, tuple[Hashable, ...]], Counter]
    order_one: Mapping[tuple[Hashable, Hashable], Counter]
    marginal: Mapping[Hashable, Counter]


def _fit(traces: Sequence[CausalGrowthTrace],
         minimum_state_support: int = 1) -> _Marking:
    exact = defaultdict(Counter)
    order_one = defaultdict(Counter)
    marginal = defaultdict(Counter)
    for trace in traces:
        exact[(trace.parent_type, trace.incoming_ports)][
            trace.chosen_outgoing_port] += 1
        for incoming in trace.incoming_ports:
            order_one[(trace.parent_type, incoming)][
                trace.chosen_outgoing_port] += 1
        marginal[trace.parent_type][trace.chosen_outgoing_port] += 1
    exact = {key: value for key, value in exact.items()
             if sum(value.values()) >= minimum_state_support}
    order_one = {key: value for key, value in order_one.items()
                 if sum(value.values()) >= minimum_state_support}
    return _Marking(exact, order_one, dict(marginal))


def _rank(marking: _Marking, action: FrozenFrontierAction) -> tuple:
    exact = marking.exact.get(
        (action.parent_type, action.incoming_ports), Counter())[
            action.production_id]
    order_one = sum(marking.order_one.get(
        (action.parent_type, incoming), Counter())[action.production_id]
                    for incoming in action.incoming_ports)
    marginal = marking.marginal.get(
        action.parent_type, Counter())[action.production_id]
    return (-exact, -order_one, -marginal, action.baseline_order,
            action.candidate_id)


def _shuffle_within_parent(
    traces: Sequence[CausalGrowthTrace], seed: int,
) -> tuple[CausalGrowthTrace, ...]:
    groups = defaultdict(list)
    for index, trace in enumerate(traces):
        groups[trace.parent_type].append(index)
    result = list(traces)
    rng = random.Random(seed)
    for indices in groups.values():
        labels = [traces[index].chosen_outgoing_port for index in indices]
        rng.shuffle(labels)
        for index, label in zip(indices, labels):
            original = traces[index]
            result[index] = CausalGrowthTrace(
                original.parent_occurrence, original.parent_type,
                original.incoming_ports, label, original.occurrence_domain,
                original.causal, original.within_training_domain)
    return tuple(result)


def _candidate_digest(actions: Sequence[FrozenFrontierAction]) -> str:
    code = tuple(sorted((
        action.candidate_id, action.parent_occurrence, action.parent_type,
        action.incoming_ports, action.production_id,
        tuple(sorted(map(repr, action.novel_site_keys))),
        repr(action.baseline_order)) for action in actions))
    return hashlib.sha256(repr(code).encode()).hexdigest()


def _work(
    name: str, order: Sequence[FrozenFrontierAction],
    correct_by_candidate: Mapping[int, frozenset[Hashable]],
    target_sites: frozenset[Hashable],
) -> SearchWork:
    recovered = set()
    backtracks = wrong_atoms = 0
    for checks, action in enumerate(order, 1):
        correct = correct_by_candidate.get(action.candidate_id, frozenset())
        emitted = frozenset(action.novel_site_keys)
        valid = bool(emitted) and correct == emitted
        if valid:
            recovered.update(correct)
        else:
            backtracks += 1
            wrong_atoms += len(emitted.difference(correct))
        if target_sites.issubset(recovered):
            return SearchWork(
                name, len(target_sites), checks, backtracks, wrong_atoms)
    raise RuntimeError("frozen candidates cannot reach the matched target")


def run_causal_marking_ablation(
    training_traces: Sequence[CausalGrowthTrace],
    frozen_candidates: Sequence[FrozenFrontierAction],
    score_callback: Callable[
        [tuple[FrozenFrontierAction, ...]],
        Mapping[int, frozenset[Hashable]]], *,
    shuffled_runs: int = 31, maximum_interaction_order: int = 2,
    minimum_state_support: int = 1,
) -> CausalFrontierMarkingAblation:
    """Fit causally, freeze candidates, then invoke the sealed scorer once."""
    traces = tuple(training_traces)
    candidates = tuple(frozen_candidates)
    if shuffled_runs != 31:
        raise ValueError("the confirmatory ablation requires 31 shuffles")
    if maximum_interaction_order != 2:
        raise ValueError("the initial marking contract fixes maximum order two")
    if minimum_state_support < 1:
        raise ValueError("minimum state support must be positive")
    if not traces or not candidates:
        raise ValueError("training traces and frozen candidates are required")
    if (any(len(trace.incoming_ports) > maximum_interaction_order
            for trace in traces) or
            not all(trace.causal and trace.within_training_domain
                    for trace in traces)):
        raise ValueError("marking traces must be causal, train-only, and order <=2")
    ids = [action.candidate_id for action in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate ids must be unique")
    digest = _candidate_digest(candidates)
    marking = _fit(traces, minimum_state_support)
    shuffled_markings = tuple(_fit(_shuffle_within_parent(
        traces, 104729 + run * 7919), minimum_state_support)
                              for run in range(shuffled_runs))
    # This is the sole oracle boundary. Candidate generation and every marking
    # fit have already completed.
    scored = score_callback(candidates)
    if set(scored) != set(ids):
        raise ValueError("sealed scorer must return exactly the frozen ids")
    correct_by_candidate = {
        candidate_id: frozenset(values)
        for candidate_id, values in scored.items()}
    for action in candidates:
        if not correct_by_candidate[action.candidate_id].issubset(
                frozenset(action.novel_site_keys)):
            raise ValueError("scorer returned a site absent from its candidate")
    valid_targets = frozenset(site for action in candidates
        if (frozenset(action.novel_site_keys) and
            correct_by_candidate[action.candidate_id] ==
            frozenset(action.novel_site_keys))
        for site in action.novel_site_keys)
    if not valid_targets:
        raise ValueError("frozen frontier contains no exact heldout action")

    baseline_order = tuple(sorted(
        candidates, key=lambda action: (
            action.baseline_order, action.candidate_id)))
    marked_order = tuple(sorted(candidates,
                                key=lambda action: _rank(marking, action)))
    marked = _work("marked", marked_order, correct_by_candidate, valid_targets)
    unmarked = _work(
        "unmarked", baseline_order, correct_by_candidate, valid_targets)
    shuffled = tuple(_work(
        f"shuffle-{run}", tuple(sorted(
            candidates, key=lambda action: _rank(fitted, action))),
        correct_by_candidate, valid_targets)
        for run, fitted in enumerate(shuffled_markings))
    marked_total = marked.proposal_plus_backtrack_work
    shuffled_total = tuple(item.proposal_plus_backtrack_work
                           for item in shuffled)
    p_value = ((1 + sum(value <= marked_total for value in shuffled_total)) /
               (shuffled_runs + 1))
    beats_unmarked = (
        marked.proposal_checks < unmarked.proposal_checks and
        marked.geometric_backtracks < unmarked.geometric_backtracks)
    beats_shuffle = (
        marked.proposal_checks < median(
            item.proposal_checks for item in shuffled) and
        marked.geometric_backtracks < median(
            item.geometric_backtracks for item in shuffled))
    passed = beats_unmarked and beats_shuffle and p_value <= .05
    return CausalFrontierMarkingAblation(
        len(traces), maximum_interaction_order, len(candidates), digest,
        len(valid_targets), marked, unmarked, shuffled, shuffled_runs,
        median(item.proposal_checks for item in shuffled),
        median(item.geometric_backtracks for item in shuffled),
        median(shuffled_total), p_value, beats_unmarked, beats_shuffle,
        True, True, True, False, passed)


def causal_occurrence_traces(program, positions) -> tuple[CausalGrowthTrace, ...]:
    """Extract radial inward-before-outward traces from one training cloud."""
    center = tuple(sum(point[axis] for point in positions) / len(positions)
                   for axis in range(3))
    occurrence = {item.occurrence_id: item for item in program.occurrences}
    radius = {key: math.dist(value.translation, center)
              for key, value in occurrence.items()}
    production = {(item.parent_type, item.child_type,
                   item.port.symmetry_orbit_key): item.production_id
                  for item in program.productions}
    incoming = defaultdict(list)
    outgoing = defaultdict(list)
    for parent, child, parent_type, child_type, port_key in (
            program.relation_classes):
        action = production.get((parent_type, child_type, port_key))
        if action is None or math.isclose(radius[parent], radius[child]):
            continue
        if radius[parent] < radius[child]:
            outgoing[parent].append((action, child))
            incoming[child].append((action, parent))
    traces = []
    for parent in sorted(outgoing):
        context_pairs = sorted(incoming.get(parent, ()))[:2]
        context = tuple(action for action, _ in context_pairs)
        inward_nodes = tuple(node for _, node in context_pairs)
        for action, child in sorted(outgoing[parent]):
            traces.append(CausalGrowthTrace(
                parent, occurrence[parent].type_id, context, action,
                tuple(sorted({parent, child, *inward_nodes}))))
    return tuple(traces)


def probe_sealed_iqc_executor() -> SealedIQCExecutorReadiness:
    """Exercise the actual frozen IQC executor without consulting its target."""
    from materials_gcts_frozen_frontier_replay import (
        enumerate_frontier, fit_frozen_frontier_program,
        seed_patch_from_training)
    from materials_gcts_icosahedral_modelset import oracle_patch
    from materials_gcts_irregular_port_atlas import compile_irregular_port_program

    training, _ = oracle_patch(3, 9.0)
    learned = compile_irregular_port_program(
        training.species, training.positions)
    program = fit_frozen_frontier_program(learned)
    traces = causal_occurrence_traces(
        type("TraceProgram", (), {
            "occurrences": learned.occurrences,
            "relation_classes": learned.atlas.relation_classes,
            "productions": program.productions})(), training.positions)
    seed = seed_patch_from_training(
        learned, training.species, training.positions)
    frontier = enumerate_frontier(
        program, seed.occurrences,
        explicit_gap_sites=seed.explicit_gap_sites)
    ready = bool(frontier.candidates)
    return SealedIQCExecutorReadiness(
        len(training.positions), len(learned.occurrences), len(traces), 2,
        len(program.productions), len(frontier.candidates), False, ready,
        "" if ready else
        "full frozen IQC seed enumerates no exterior candidate; integrate "
        "the next exterior-capable executor through the documented API")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = probe_sealed_iqc_executor()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
