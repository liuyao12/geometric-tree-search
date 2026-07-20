#!/usr/bin/env python3
"""Minimize Hat probe markings against the one-seed candidate graph metric."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

from hat_marking_search import MarkingSpec, doubled_midpoint, segment_payload
from hat_sample_marking import point_candidate_graph_metrics
from turtle_gcts_rl import Point, add, key


def load_probe_spec(path: Path) -> tuple[dict[str, object], MarkingSpec]:
    data = json.loads(path.read_text(encoding="utf-8"))
    segments = data["marking"]["segments"]  # type: ignore[index]
    if not isinstance(segments, dict):
        raise ValueError("expected a probe marking JSON with dict-valued marking.segments")

    def convert(items: object) -> tuple[tuple[int, Point, int], ...]:
        return tuple((int(edge), tuple(offset), int(value)) for edge, offset, value in items)  # type: ignore[misc]

    spec = MarkingSpec(
        str(data["marking"]["name"]),  # type: ignore[index]
        fore_probe_marks=convert(segments.get("probe_fore", [])),
        rear_probe_marks=convert(segments.get("probe_rear", [])),
        fore_site_marks=convert_site(segments.get("site_fore", [])),
        rear_site_marks=convert_site(segments.get("site_rear", [])),
    )
    return data, spec


def convert_site(items: object) -> tuple[tuple[Point, int, int], ...]:
    out = []
    for item in items:  # type: ignore[union-attr]
        if len(item) == 2:
            point, value = item
            component = 0
        else:
            point, component, value = item
        out.append((tuple(point), int(component), int(value)))
    return tuple(out)


def probe_physical_key(mark: tuple[int, Point, int]) -> str:
    edge, offset, _ = mark
    return key(add(doubled_midpoint(edge), offset))


def site_physical_key(mark: tuple[Point, int, int]) -> str:
    point, _, _ = mark
    return key(point)


def side_point_keys(spec: MarkingSpec, side: str) -> set[str]:
    probe_marks = spec.rear_probe_marks if side == "rear" else spec.fore_probe_marks
    site_marks = spec.rear_site_marks if side == "rear" else spec.fore_site_marks
    return {probe_physical_key(mark) for mark in probe_marks}.union(site_physical_key(mark) for mark in site_marks)


def marking_counts(spec: MarkingSpec) -> dict[str, int]:
    counts: dict[str, int] = {}
    for side in ("fore", "rear"):
        probe_marks = spec.rear_probe_marks if side == "rear" else spec.fore_probe_marks
        site_marks = spec.rear_site_marks if side == "rear" else spec.fore_site_marks
        counts[f"{side}_entries"] = len(probe_marks) + len(site_marks)
        counts[f"{side}_points"] = len(side_point_keys(spec, side))
    counts["entries"] = counts["fore_entries"] + counts["rear_entries"]
    counts["side_points"] = counts["fore_points"] + counts["rear_points"]
    return counts


def physical_site_groups(spec: MarkingSpec, site_mode: str) -> list[tuple[str, str]]:
    if site_mode == "paired":
        points = side_point_keys(spec, "fore").union(side_point_keys(spec, "rear"))
        return [("paired", point) for point in sorted(points)]
    if site_mode == "side":
        groups = []
        for side in ("fore", "rear"):
            groups.extend((side, point) for point in sorted(side_point_keys(spec, side)))
        return groups
    raise ValueError(f"unknown site mode: {site_mode}")


def remove_group(spec: MarkingSpec, group: tuple[str, str]) -> MarkingSpec:
    side, point = group
    if side == "paired":
        return replace(
            spec,
            fore_probe_marks=tuple(mark for mark in spec.fore_probe_marks if probe_physical_key(mark) != point),
            rear_probe_marks=tuple(mark for mark in spec.rear_probe_marks if probe_physical_key(mark) != point),
            fore_site_marks=tuple(mark for mark in spec.fore_site_marks if site_physical_key(mark) != point),
            rear_site_marks=tuple(mark for mark in spec.rear_site_marks if site_physical_key(mark) != point),
        )
    if side == "fore":
        return replace(
            spec,
            fore_probe_marks=tuple(mark for mark in spec.fore_probe_marks if probe_physical_key(mark) != point),
            fore_site_marks=tuple(mark for mark in spec.fore_site_marks if site_physical_key(mark) != point),
        )
    return replace(
        spec,
        rear_probe_marks=tuple(mark for mark in spec.rear_probe_marks if probe_physical_key(mark) != point),
        rear_site_marks=tuple(mark for mark in spec.rear_site_marks if site_physical_key(mark) != point),
    )


def metric_summary(metric: dict[str, object]) -> dict[str, object]:
    keys = [
        "frontier_points",
        "dead_points",
        "unique_candidates",
        "bipartite_edges",
        "limited_unique_candidates",
        "limited_bipartite_edges",
        "forced_points",
        "max_candidates_per_point",
        "mean_candidates_per_point",
    ]
    return {name: metric[name] for name in keys}


def preserves_target(metric: dict[str, object], target: dict[str, object]) -> bool:
    return (
        int(metric["unique_candidates"]) <= int(target["unique_candidates"])
        and int(metric["bipartite_edges"]) <= int(target["bipartite_edges"])
    )


def greedy_minimize(
    spec: MarkingSpec,
    target: dict[str, object],
    candidate_limit: int,
    seed: int,
    site_mode: str,
) -> tuple[MarkingSpec, int]:
    args = argparse.Namespace(candidate_limit=candidate_limit)
    rng = random.Random(seed)
    current = spec
    removed = 0
    changed = True
    while changed:
        changed = False
        groups = physical_site_groups(current, site_mode)
        rng.shuffle(groups)
        for group in groups:
            trial = remove_group(current, group)
            metric = point_candidate_graph_metrics(trial, args)
            if preserves_target(metric, target):
                current = trial
                removed += 1
                changed = True
    return current, removed


def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Probe marking JSON to minimize")
    parser.add_argument("--output", required=True, help="Where to write the minimized JSON")
    parser.add_argument("--candidate-limit", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument(
        "--site-mode",
        choices=["paired", "side"],
        default="paired",
        help="Remove paired fore/rear physical sites, or allow side-specific deletions.",
    )
    return parser.parse_args()


def main() -> None:
    args = read_args()
    source = Path(args.input)
    data, spec = load_probe_spec(source)
    metric_args = argparse.Namespace(candidate_limit=args.candidate_limit)
    target = point_candidate_graph_metrics(spec, metric_args)

    best_spec = spec
    best_metric = target
    best_removed = 0
    best_seed = args.seed
    counts = marking_counts(spec)
    best_score = (counts["side_points"], counts["entries"], int(target["bipartite_edges"]), int(target["unique_candidates"]))

    for offset in range(args.trials):
        seed = args.seed + offset
        trial_spec, removed = greedy_minimize(spec, target, args.candidate_limit, seed, args.site_mode)
        trial_metric = point_candidate_graph_metrics(trial_spec, metric_args)
        counts = marking_counts(trial_spec)
        score = (
            counts["side_points"],
            counts["entries"],
            int(trial_metric["bipartite_edges"]),
            int(trial_metric["unique_candidates"]),
        )
        if score < best_score:
            best_spec = trial_spec
            best_metric = trial_metric
            best_removed = removed
            best_seed = seed
            best_score = score

    output = dict(data)
    output["marking"] = {
        "name": f"{best_spec.name}:physical-min",
        "segments": segment_payload(best_spec),
    }
    output["minimized_from"] = str(source)
    output["minimization"] = {
        "objective": "remove physical A2 probe sites while preserving one-seed unique_candidates and bipartite_edges",
        "site_mode": args.site_mode,
        "candidate_limit": args.candidate_limit,
        "base_counts": marking_counts(spec),
        "minimized_counts": marking_counts(best_spec),
        "target_graph_metrics": metric_summary(target),
        "minimized_graph_metrics": metric_summary(best_metric),
        "greedy_seed": best_seed,
        "trials": args.trials,
        "removed_physical_sites": best_removed,
    }
    target_path = Path(args.output)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(output["minimization"], indent=2))
    print(f"wrote {target_path}")


if __name__ == "__main__":
    main()
