#!/usr/bin/env python3
"""A small, auditable Hat GCTS run with online geometric memoization.

The run begins with an empty marking.  When a tried placement makes the local
boundary impossible to continue, the learner searches for a sparse A2 marking
extension that rejects that placement while replaying every accepted placement
without a marking conflict.  The local marking domain is not a fixed-radius
ball: witness sites are added one or two at a time, wherever the failed contact
requires them, up to ``--max-lattice-reach``.

The JSON trace is intentionally presentation-neutral.  The browser demo in
``apps/hat-gcts-online-demo`` renders it, and the checks in this file make the
claims in that animation reproducible from the command line.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from hat_marking_search import HAT_VERTS, MarkingSpec, build_hat_orientations, segment_payload
from hat_sample_marking import (
    LocalMark,
    MarkScheme,
    ProbeClause,
    ProbePair,
    contact_pairs_for_placement_against,
    lattice_site_points,
    placement_contact_pair_counts,
    train_coloring,
)
from turtle_gcts_rl import (
    Candidate,
    FrontierPoint,
    Placement,
    Point,
    TurtleState,
    candidate_keeps_boundary_alive,
    choose_frontier_option,
    key,
    mark_compatible_candidate,
    max_corona,
    norm,
    order_candidates,
    place,
    project_raw,
)


PathItem = tuple[int, Point, str]


@dataclass(frozen=True)
class FailureRecord:
    parent_path: tuple[PathItem, ...]
    orientation_idx: int
    translation: Point
    placement_key: str
    reason: str


@dataclass
class LearnedSection:
    scheme: MarkScheme = ()
    spec: MarkingSpec | None = None
    failures: list[FailureRecord] = field(default_factory=list)


def path_placements(path: Iterable[PathItem], orientations: list) -> list[Placement]:
    return [
        place(orientations[orientation_idx], translation, placement_key, depth=depth)
        for depth, (orientation_idx, translation, placement_key) in enumerate(path)
    ]


def state_for_path(path: Iterable[PathItem], orientations: list) -> TurtleState:
    state = TurtleState(orientations)
    for placement in path_placements(path, orientations):
        state.add_placement(placement, depth=placement.depth)
    return state


def local_mark_payload(mark: LocalMark) -> dict[str, object]:
    return {"name": mark.name, "point": list(mark.point), "component": mark.component}


def placement_payload(placement: Placement) -> dict[str, object]:
    return {
        "orientation": placement.orientation.idx,
        "translation": list(placement.translation),
        "placement_key": placement.placement_key,
        "depth": placement.depth,
        "polygon": [list(project_raw(point)) for point in placement.vertices],
    }


def candidate_payload(candidate: Candidate) -> dict[str, object]:
    trial = place(candidate.orientation, candidate.translation, candidate.pk)
    return {
        "orientation": candidate.orientation.idx,
        "translation": list(candidate.translation),
        "placement_key": candidate.pk,
        "polygon": [list(project_raw(point)) for point in trial.vertices],
    }


def marking_payload(spec: MarkingSpec | None) -> object:
    return segment_payload(spec) if spec is not None else {
        "site_fore": [],
        "site_rear": [],
    }


def training_args(seed: int) -> argparse.Namespace:
    return argparse.Namespace(
        probe_mode="lattice",
        side_action="opposite",
        assignment_mode="random",
        assignment_seed=seed,
        assignment_trials=400,
        assignment_steps=0,
        assignment_lock_initial=False,
        assignment_fill_unassigned=False,
        min_good=1,
        min_bad=1,
        max_good_for_bad=0,
        episodes=1,
    )


def scheme_from_marks(marks: Iterable[LocalMark]) -> MarkScheme:
    return tuple(sorted(set(marks), key=lambda mark: (key(mark.point), mark.component, mark.name)))


def mark_index(scheme: MarkScheme) -> dict[str, LocalMark]:
    return {mark.name: mark for mark in scheme}


def failure_clause(record: FailureRecord, scheme: MarkScheme, base_orientations: list) -> ProbeClause:
    parents = path_placements(record.parent_path, base_orientations)
    failed = place(
        base_orientations[record.orientation_idx],
        record.translation,
        record.placement_key,
    )
    return tuple(sorted(contact_pairs_for_placement_against(failed, parents, scheme, neighbors_only=False)))


def failure_candidate(record: FailureRecord, orientations: list) -> Candidate:
    # Only the marking-compatibility fields are read by mark_compatible_candidate.
    return Candidate(
        orientation=orientations[record.orientation_idx],
        translation=record.translation,
        pk=record.placement_key,
        frontier=FrontierPoint((0, 0, 0), 0, 0),
        anchor_value=0,
        score=0,
        line_matches=0,
        new_points=1,
        overlap_points=1,
        fill_value=0,
    )


def validate_section(
    spec: MarkingSpec,
    accepted_path: tuple[PathItem, ...],
    failures: list[FailureRecord],
) -> tuple[bool, dict[str, object]]:
    marked_orientations = build_hat_orientations(spec)
    try:
        state_for_path(accepted_path, marked_orientations)
    except ValueError as error:
        return False, {"accepted_replay": False, "error": str(error)}

    missed: list[int] = []
    for index, record in enumerate(failures):
        try:
            parent_state = state_for_path(record.parent_path, marked_orientations)
        except ValueError:
            return False, {"accepted_replay": False, "failure_parent": index}
        candidate = failure_candidate(record, marked_orientations)
        if mark_compatible_candidate(marked_orientations[record.orientation_idx], candidate, parent_state) is not None:
            missed.append(index)
    return not missed, {
        "accepted_replay": True,
        "accepted_placements": len(accepted_path),
        "memoized_failures": len(failures) - len(missed),
        "missed_failures": missed,
    }


def fit_section(
    accepted_path: tuple[PathItem, ...],
    failures: list[FailureRecord],
    scheme: MarkScheme,
    base_orientations: list,
    seed: int,
) -> tuple[MarkingSpec | None, dict[str, object]]:
    accepted = path_placements(accepted_path, base_orientations)
    good_counts = placement_contact_pair_counts(accepted, scheme, neighbors_only=False)
    clauses: Counter[ProbeClause] = Counter()
    bad_counts: Counter[ProbePair] = Counter()
    empty_failures = []
    for index, record in enumerate(failures):
        clause = failure_clause(record, scheme, base_orientations)
        if not clause:
            empty_failures.append(index)
            continue
        clauses[clause] += 1
        bad_counts.update(clause)
    if empty_failures:
        return None, {"assignment_satisfied": False, "empty_failure_clauses": empty_failures}

    spec, diagnostics = train_coloring(
        {
            "good_counts": good_counts,
            "branch_equalities": good_counts,
            "bad_counts": bad_counts,
            "bad_clauses": clauses,
        },
        training_args(seed),
        scheme,
    )
    if not diagnostics.get("assignment_satisfied", False):
        return None, diagnostics
    valid, validation = validate_section(spec, accepted_path, failures)
    diagnostics = {**diagnostics, **validation}
    return (spec if valid else None), diagnostics


def witness_extensions(
    record: FailureRecord,
    pool: MarkScheme,
    current: MarkScheme,
    base_orientations: list,
) -> list[tuple[LocalMark, ...]]:
    current_names = {mark.name for mark in current}
    pool_by_name = mark_index(pool)
    witnesses: set[tuple[LocalMark, ...]] = set()
    for pair in failure_clause(record, pool, base_orientations):
        additions = tuple(
            sorted(
                {
                    pool_by_name[variable[1]]
                    for variable in pair
                    if variable[1] not in current_names
                },
                key=lambda mark: (norm(mark.point), key(mark.point), mark.component),
            )
        )
        if additions:
            witnesses.add(additions)
    return sorted(
        witnesses,
        key=lambda additions: (
            len(additions),
            max(norm(mark.point) for mark in additions),
            sum(norm(mark.point) for mark in additions),
            tuple(mark.name for mark in additions),
        ),
    )


def learn_failure(
    section: LearnedSection,
    record: FailureRecord,
    accepted_path: tuple[PathItem, ...],
    pool: MarkScheme,
    base_orientations: list,
    seed: int,
) -> tuple[bool, dict[str, object]]:
    trial_failures = [*section.failures, record]
    attempts = 0
    for additions in witness_extensions(record, pool, section.scheme, base_orientations):
        attempts += 1
        trial_scheme = scheme_from_marks((*section.scheme, *additions))
        spec, diagnostics = fit_section(
            accepted_path,
            trial_failures,
            trial_scheme,
            base_orientations,
            seed + attempts,
        )
        if spec is None:
            continue
        previous_names = {mark.name for mark in section.scheme}
        section.scheme = trial_scheme
        section.spec = spec
        section.failures = trial_failures
        added = [mark for mark in trial_scheme if mark.name not in previous_names]
        return True, {
            "attempts": attempts,
            "added": [local_mark_payload(mark) for mark in added],
            "support_entries": len(section.scheme),
            "physical_sites": len({key(mark.point) for mark in section.scheme}),
            "max_support_norm": max((norm(mark.point) for mark in section.scheme), default=0),
            "diagnostics": {
                name: diagnostics.get(name)
                for name in (
                    "assignment_satisfied",
                    "accepted_replay",
                    "accepted_placements",
                    "memoized_failures",
                    "positive_pair_constraints",
                    "negative_clauses_used",
                )
            },
        }
    return False, {"attempts": attempts, "reason": "no safe mismatch certificate in support pool"}


def pool_scheme(max_reach: int, channels: int) -> MarkScheme:
    return tuple(
        LocalMark(f"{key(point)}:c{component}", point, component)
        for point in lattice_site_points(max_reach, "tile")
        for component in range(channels)
    )


def current_frame(
    event_type: str,
    message: str,
    path: tuple[PathItem, ...],
    base_orientations: list,
    section: LearnedSection,
    **extra: object,
) -> dict[str, object]:
    return {
        "type": event_type,
        "message": message,
        "placements": [placement_payload(item) for item in path_placements(path, base_orientations)],
        "marking": marking_payload(section.spec),
        "support": [local_mark_payload(mark) for mark in section.scheme],
        "learned_failures": len(section.failures),
        **extra,
    }


def run_demo(args: argparse.Namespace) -> dict[str, object]:
    started = time.perf_counter()
    rng = random.Random(args.seed)
    base_orientations = build_hat_orientations(None)
    pool = pool_scheme(args.max_lattice_reach, args.channels)
    section = LearnedSection()
    path: tuple[PathItem, ...] = ((0, (0, 0, 0), "seed"),)
    trace = [
        current_frame(
            "start",
            "One Hat, no marking and no remembered failures.",
            path,
            base_orientations,
            section,
        )
    ]
    trials = memo_hits = accepted = 0
    stop = "target_tiles"

    while len(path) < args.target_tiles:
        if args.wall_time_ms > 0 and (time.perf_counter() - started) * 1000 >= args.wall_time_ms:
            stop = "wall_time_ms"
            break
        geometric_state = state_for_path(path, base_orientations)
        marked_orientations = build_hat_orientations(section.spec)
        marked_state = state_for_path(path, marked_orientations)
        status, option = choose_frontier_option(geometric_state, args.frontier_limit, args.candidate_limit)
        if status != "ok" or option is None:
            stop = status
            break
        frontier_point, candidates = option
        ordered = order_candidates(candidates, geometric_state, {}, rng, args.policy, args.candidate_limit)
        placed = False
        for candidate in ordered:
            trials += 1
            marked_candidate = mark_compatible_candidate(
                marked_orientations[candidate.orientation.idx],
                candidate,
                marked_state,
            )
            if marked_candidate is None:
                memo_hits += 1
                trace.append(
                    current_frame(
                        "memo-hit",
                        "The learned mismatch rejects this placement before geometric lookahead.",
                        path,
                        base_orientations,
                        section,
                        candidate=candidate_payload(candidate),
                        frontier=list(frontier_point.point),
                    )
                )
                continue

            trace.append(
                current_frame(
                    "trial",
                    "Try an admissible geometric branch.",
                    path,
                    base_orientations,
                    section,
                    candidate=candidate_payload(candidate),
                    frontier=list(frontier_point.point),
                )
            )
            if not candidate_keeps_boundary_alive(candidate, geometric_state):
                record = FailureRecord(
                    parent_path=path,
                    orientation_idx=candidate.orientation.idx,
                    translation=candidate.translation,
                    placement_key=candidate.pk,
                    reason="dead_frontier_after_placement",
                )
                trace.append(
                    current_frame(
                        "failure",
                        "This branch creates a frontier point with no legal continuation.",
                        path,
                        base_orientations,
                        section,
                        candidate=candidate_payload(candidate),
                    )
                )
                learned, details = learn_failure(
                    section,
                    record,
                    path,
                    pool,
                    base_orientations,
                    args.seed + len(section.failures) * 1009,
                )
                if not learned:
                    stop = "unencodable_failure"
                    trace.append(
                        current_frame(
                            "learning-failed",
                            "No safe mismatch certificate was found within the configured support horizon.",
                            path,
                            base_orientations,
                            section,
                            candidate=candidate_payload(candidate),
                            learning=details,
                        )
                    )
                    placed = False
                    break
                trace.append(
                    current_frame(
                        "memoized",
                        "A sparse marking extension rejects the failed branch and replays the accepted prefix.",
                        path,
                        base_orientations,
                        section,
                        candidate=candidate_payload(candidate),
                        learning=details,
                    )
                )
                # Rebuild the marked state immediately; the new section is now live.
                marked_orientations = build_hat_orientations(section.spec)
                marked_state = state_for_path(path, marked_orientations)
                continue

            path = (*path, (candidate.orientation.idx, candidate.translation, candidate.pk))
            accepted += 1
            trace.append(
                current_frame(
                    "accept",
                    "The branch stays geometrically live and becomes part of the protected prefix.",
                    path,
                    base_orientations,
                    section,
                    accepted_orientation=candidate.orientation.idx,
                    accepted_translation=list(candidate.translation),
                )
            )
            placed = True
            break
        if stop == "unencodable_failure":
            break
        if not placed:
            stop = "exhausted_frontier_candidates"
            break

    final_valid = True
    final_validation: dict[str, object] = {
        "accepted_replay": True,
        "accepted_placements": len(path),
        "memoized_failures": 0,
    }
    if section.spec is not None:
        final_valid, final_validation = validate_section(section.spec, path, section.failures)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return {
        "schema": "hat-gcts-online-memo-demo/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": vars(args),
        "summary": {
            "stopped_reason": stop,
            "elapsed_ms": elapsed_ms,
            "tiles": len(path),
            "corona": max_corona(path_placements(path, base_orientations)),
            "trials": trials,
            "accepted_moves": accepted,
            "learned_failures": len(section.failures),
            "memo_hits": memo_hits,
            "marking_started_empty": True,
            "support_entries": len(section.scheme),
            "physical_support_sites": len({key(mark.point) for mark in section.scheme}),
            "final_validation": final_validation,
            "valid": final_valid,
        },
        "hat": {"vertices": [list(project_raw(point)) for point in HAT_VERTS]},
        "final_marking": marking_payload(section.spec),
        "final_support": [local_mark_payload(mark) for mark in section.scheme],
        "trace": trace,
    }


def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-tiles", type=int, default=16)
    parser.add_argument("--frontier-limit", type=int, default=10)
    parser.add_argument("--candidate-limit", type=int, default=14)
    parser.add_argument("--max-lattice-reach", type=int, default=4)
    parser.add_argument("--channels", type=int, choices=[1, 3], default=3)
    parser.add_argument("--policy", choices=["heuristic", "random"], default="random")
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--wall-time-ms", type=int, default=30000)
    parser.add_argument("--output", default="apps/hat-gcts-online-demo/demo-trace.json")
    return parser.parse_args()


def main() -> None:
    args = read_args()
    payload = run_demo(args)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
