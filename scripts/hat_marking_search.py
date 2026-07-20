#!/usr/bin/env python3
"""Search for Hat line markings that accelerate local GCTS.

This script reuses the local GCTS machinery in turtle_gcts_rl.py, but swaps in
the Hat outline from the Smith-Myers-Kaplan-Goodman-Strauss continuum as encoded
by the public H7/H8 substitution demo. It benchmarks candidate line markings
against an unmarked Hat baseline.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from turtle_gcts_rl import (
    MAX_ANGLE,
    MARK_REACH,
    Mark,
    Occupancy,
    Orientation,
    Point,
    Segment,
    add,
    aggregate_results,
    all_symmetries,
    component_for,
    interiors,
    key,
    load_policy,
    map_component,
    place,
    run_episode,
    run_tree_search,
    scale,
    segment_points,
    top_weights,
    sub,
    transform_linear,
    update_policy,
    unique_orientations,
)


# The "Hats" button in https://cs.uwaterloo.ca/~csk/hat/h7h8.js sets
# a = 1, b = sqrt(3). Converting those edge steps to the A2 lattice gives this
# 14-vertex outline. The final side is the implicit closing edge.
HAT_VERTS: list[Point] = [
    (0, 0, 0),
    (1, 0, -1),
    (1, 1, -2),
    (3, 0, -3),
    (4, 1, -5),
    (3, 2, -5),
    (3, 3, -6),
    (1, 4, -5),
    (0, 6, -6),
    (-1, 6, -5),
    (-1, 5, -4),
    (-1, 4, -3),
    (0, 3, -3),
    (-1, 2, -1),
]

HAT_ANGLES = [3, 4, 9, 4, 3, 8, 3, 8, 3, 4, 6, 4, 9, 4]

# A first hand candidate: same vertex-index pattern as the straight-line Turtle
# stripes, applied to the Hat outline. The search mode below tests whether this
# is actually useful; it is not assumed correct.
INDEX_STRIPES = (("v0", "v10", 1), ("v2", "v8", -1), ("v0", "v6", -1), ("v4", "v12", -1))


@dataclass(frozen=True)
class MarkingSpec:
    name: str
    segments: tuple[tuple[str, str, int], ...] = ()
    fore_segments: tuple[tuple[str, str, int], ...] = ()
    rear_segments: tuple[tuple[str, str, int], ...] = ()
    edge_marks: tuple[tuple[int, int], ...] = ()
    fore_edge_marks: tuple[tuple[int, int], ...] = ()
    rear_edge_marks: tuple[tuple[int, int], ...] = ()
    probe_marks: tuple[tuple[int, Point, int], ...] = ()
    fore_probe_marks: tuple[tuple[int, Point, int], ...] = ()
    rear_probe_marks: tuple[tuple[int, Point, int], ...] = ()
    site_marks: tuple[tuple[Point, int, int], ...] = ()
    fore_site_marks: tuple[tuple[Point, int, int], ...] = ()
    rear_site_marks: tuple[tuple[Point, int, int], ...] = ()


@dataclass(frozen=True)
class PatchShape:
    points: tuple[Point, ...]
    quad: tuple[Point, ...]
    label: str


@dataclass(frozen=True)
class PatchObject:
    shapes: tuple[PatchShape, ...]
    quad: tuple[Point, ...]


def normalize_endpoint_ref(raw: str | int) -> str:
    text = str(raw).strip()
    if text.isdigit():
        return f"v{text}"
    if len(text) >= 2 and text[0].lower() in {"v", "m"} and text[1:].isdigit():
        return f"{text[0].lower()}{int(text[1:])}"
    raise ValueError(f"bad endpoint reference {raw!r}; use vertex 2/v2 or midpoint m2")


def doubled_vertex(index: int) -> Point:
    return scale(HAT_VERTS[index % len(HAT_VERTS)], 2)


def doubled_midpoint(edge_index: int) -> Point:
    source = HAT_VERTS[edge_index % len(HAT_VERTS)]
    target = HAT_VERTS[(edge_index + 1) % len(HAT_VERTS)]
    return add(source, target)


def endpoint_point(ref: str) -> Point:
    normalized = normalize_endpoint_ref(ref)
    index = int(normalized[1:])
    return doubled_vertex(index) if normalized[0] == "v" else doubled_midpoint(index)


def endpoint_refs(mode: str) -> list[str]:
    vertices = [f"v{idx}" for idx in range(len(HAT_VERTS))]
    midpoints = [f"m{idx}" for idx in range(len(HAT_VERTS))]
    if mode == "vertices":
        return vertices
    if mode == "midpoints":
        return midpoints
    if mode == "all":
        return vertices + midpoints
    raise ValueError(f"unknown endpoint mode: {mode}")


def line_component_or_none(a: Point, b: Point) -> int | None:
    delta = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    nonzero = [value for value in delta if value != 0]
    if not nonzero:
        return None
    component = component_for(a, b)
    step_values = [delta[i] for i in range(3)]
    # The rank-3 marking bundle follows the three A2 line directions used by
    # the existing Turtle straight-line markings: one coordinate is twice the
    # opposite sign of the other equal pair, up to integer scaling.
    other = [idx for idx in range(3) if idx != component]
    if step_values[other[0]] == step_values[other[1]]:
        return component
    return None


def compile_segments(segment_refs: tuple[tuple[str, str, int], ...], spec_name: str) -> list[Segment]:
    segments: list[Segment] = []
    for source_ref, target_ref, value in segment_refs:
        p1, p2 = endpoint_point(source_ref), endpoint_point(target_ref)
        component = line_component_or_none(p1, p2)
        if component is None:
            raise ValueError(f"{spec_name}: segment {source_ref}->{target_ref} is not an A2 marking direction")
        segments.append(Segment(p1, p2, component, value))
    return segments


def edge_component(edge_index: int) -> int:
    return component_for(doubled_vertex(edge_index), doubled_vertex(edge_index + 1))


def side_segment_refs(spec: MarkingSpec | None, reflected: bool) -> tuple[tuple[str, str, int], ...]:
    if spec is None:
        return ()
    side_segments = spec.rear_segments if reflected else spec.fore_segments
    return (*spec.segments, *side_segments)


def side_edge_refs(spec: MarkingSpec | None, reflected: bool) -> tuple[tuple[int, int], ...]:
    if spec is None:
        return ()
    side_marks = spec.rear_edge_marks if reflected else spec.fore_edge_marks
    return (*spec.edge_marks, *side_marks)


def side_probe_refs(spec: MarkingSpec | None, reflected: bool) -> tuple[tuple[int, Point, int], ...]:
    if spec is None:
        return ()
    side_marks = spec.rear_probe_marks if reflected else spec.fore_probe_marks
    return (*spec.probe_marks, *side_marks)


def side_site_refs(spec: MarkingSpec | None, reflected: bool) -> tuple[tuple[Point, int, int], ...]:
    if spec is None:
        return ()
    side_marks = spec.rear_site_marks if reflected else spec.fore_site_marks
    return (*spec.site_marks, *side_marks)


def segment_count(spec: MarkingSpec | None) -> int:
    if spec is None:
        return 0
    return (
        len(spec.segments)
        + len(spec.fore_segments)
        + len(spec.rear_segments)
        + len(spec.edge_marks)
        + len(spec.fore_edge_marks)
        + len(spec.rear_edge_marks)
        + len(spec.probe_marks)
        + len(spec.fore_probe_marks)
        + len(spec.rear_probe_marks)
        + len(spec.site_marks)
        + len(spec.fore_site_marks)
        + len(spec.rear_site_marks)
    )


def segment_payload(spec: MarkingSpec | None) -> object:
    if spec is None:
        return []
    if (
        not spec.fore_segments
        and not spec.rear_segments
        and not spec.edge_marks
        and not spec.fore_edge_marks
        and not spec.rear_edge_marks
        and not spec.probe_marks
        and not spec.fore_probe_marks
        and not spec.rear_probe_marks
        and not spec.site_marks
        and not spec.fore_site_marks
        and not spec.rear_site_marks
    ):
        return [list(segment) for segment in spec.segments]
    return {
        "common": [list(segment) for segment in spec.segments],
        "fore": [list(segment) for segment in spec.fore_segments],
        "rear": [list(segment) for segment in spec.rear_segments],
        "edge_common": [list(mark) for mark in spec.edge_marks],
        "edge_fore": [list(mark) for mark in spec.fore_edge_marks],
        "edge_rear": [list(mark) for mark in spec.rear_edge_marks],
        "probe_common": [[edge, list(offset), value] for edge, offset, value in spec.probe_marks],
        "probe_fore": [[edge, list(offset), value] for edge, offset, value in spec.fore_probe_marks],
        "probe_rear": [[edge, list(offset), value] for edge, offset, value in spec.rear_probe_marks],
        "site_common": [[list(point), component, value] for point, component, value in spec.site_marks],
        "site_fore": [[list(point), component, value] for point, component, value in spec.fore_site_marks],
        "site_rear": [[list(point), component, value] for point, component, value in spec.rear_site_marks],
    }


def orient_hat_tile(
    occupancy: list[Occupancy],
    spec: MarkingSpec | None,
    sym,
    idx: int,
    mark_value_mode: str = "reflection",
    mark_reach: int = MARK_REACH,
) -> Orientation:
    stripes = compile_segments(side_segment_refs(spec, sym.plane_sign < 0), spec.name if spec else "none")
    vertices = tuple(transform_linear(point, sym) for point in HAT_VERTS)
    next_occupancy = tuple(
        Occupancy(transform_linear(entry.point, sym), entry.value, entry.kind) for entry in occupancy
    )
    marks: list[Mark] = []
    segments: list[Segment] = []
    for segment in stripes:
        p1 = transform_linear(segment.p1, sym)
        p2 = transform_linear(segment.p2, sym)
        component = map_component(segment.component, sym)
        if mark_value_mode == "reflection":
            value = segment.value * sym.plane_sign
        elif mark_value_mode == "constant":
            value = segment.value
        elif mark_value_mode == "presence":
            value = 1
        else:
            raise ValueError(f"unknown mark value mode: {mark_value_mode}")
        for point in segment_points(p1, p2, 2 * mark_reach):
            marks.append(Mark(point, component, value))
        segments.append(Segment(p1, p2, component, value))
    for edge_index, value in side_edge_refs(spec, sym.plane_sign < 0):
        point = transform_linear(doubled_midpoint(edge_index), sym)
        component = map_component(edge_component(edge_index), sym)
        marks.append(Mark(point, component, value))
    for edge_index, offset, value in side_probe_refs(spec, sym.plane_sign < 0):
        point = transform_linear(add(doubled_midpoint(edge_index), offset), sym)
        component = map_component(edge_component(edge_index), sym)
        marks.append(Mark(point, component, value))
    for point, component, value in side_site_refs(spec, sym.plane_sign < 0):
        marks.append(Mark(transform_linear(point, sym), map_component(component, sym), value))
    return Orientation(
        idx=idx,
        name="Hat",
        sym=sym,
        is_reflected=sym.plane_sign < 0,
        vertices=vertices,
        occupancy=next_occupancy,
        marks=tuple(marks),
        segments=tuple(segments),
        mark_scale=2,
    )


def build_hat_orientations(
    spec: MarkingSpec | None = None,
    mark_value_mode: str = "reflection",
    mark_reach: int = MARK_REACH,
):
    occupancy = [
        *(Occupancy(point, HAT_ANGLES[idx], "vertex") for idx, point in enumerate(HAT_VERTS)),
        *(Occupancy(point, MAX_ANGLE, "interior") for point in interiors(HAT_VERTS)),
    ]
    return unique_orientations(
        orient_hat_tile(occupancy, spec, sym, idx, mark_value_mode, mark_reach)
        for idx, sym in enumerate(all_symmetries())
    )


def rotate60(point: Point, turns: int) -> Point:
    out = point
    for _ in range(turns % 6):
        x, y, z = out
        out = (-y, -z, -x)
    return out


def reflect_source_x(point: Point) -> Point:
    x, y, z = point
    return (-z, -y, -x)


def translate_shape(shape: PatchShape, delta: Point) -> PatchShape:
    return PatchShape(
        tuple(add(point, delta) for point in shape.points),
        tuple(add(point, delta) for point in shape.quad),
        shape.label,
    )


def translate_object(obj: PatchObject, delta: Point) -> PatchObject:
    return PatchObject(
        tuple(translate_shape(shape, delta) for shape in obj.shapes),
        tuple(add(point, delta) for point in obj.quad),
    )


def rotate_and_match(obj: PatchObject, turns: int, qidx: int, target: Point) -> PatchObject:
    rotated = PatchObject(
        tuple(
            PatchShape(
                tuple(rotate60(point, turns) for point in shape.points),
                tuple(rotate60(point, turns) for point in shape.quad),
                shape.label,
            )
            for shape in obj.shapes
        ),
        tuple(rotate60(point, turns) for point in obj.quad),
    )
    if qidx < 0:
        return rotated
    return translate_object(rotated, sub(target, rotated.quad[qidx]))


def flatten_children(children: list[PatchObject]) -> tuple[PatchShape, ...]:
    return tuple(shape for child in children for shape in child.shapes)


def build_base_patch_system() -> dict[str, PatchObject]:
    quad = tuple(HAT_VERTS[index] for index in (1, 3, 9, 13))
    single = PatchObject((PatchShape(tuple(HAT_VERTS), quad, "single"),), quad)

    reflected = [reflect_source_x(HAT_VERTS[len(HAT_VERTS) - 1 - idx]) for idx in range(len(HAT_VERTS))]
    delta = sub(HAT_VERTS[0], reflected[5])
    reflected = [add(point, delta) for point in reflected]
    compound = PatchObject(
        (
            PatchShape(tuple(HAT_VERTS), quad, "unflipped"),
            PatchShape(tuple(reflected), quad, "flipped"),
        ),
        quad,
    )
    return {"H8": single, "H7": compound}


def build_supertiles(system: dict[str, PatchObject]) -> dict[str, PatchObject]:
    single = system["H8"]
    compound = system["H7"]
    children = [single]
    rules = [
        (1, 2, 0, False),
        (2, 2, 0, False),
        (0, 1, 1, True),
        (-2, 2, 2, False),
        (-1, 2, 0, False),
        (0, 2, 0, False),
    ]
    for turns, source_quad, target_quad, use_compound in rules:
        source = compound if use_compound else single
        children.append(rotate_and_match(source, turns, source_quad, children[-1].quad[target_quad]))

    super_quad = (children[1].quad[3], children[2].quad[0], children[4].quad[3], children[6].quad[0])
    return {
        "H8": PatchObject(flatten_children(children), super_quad),
        "H7": PatchObject(flatten_children(children[:-1]), super_quad),
    }


def substitution_patch(tile: str, levels: int) -> PatchObject:
    system = build_base_patch_system()
    for _ in range(levels):
        system = build_supertiles(system)
    return system[tile]


def canonical_points(points: tuple[Point, ...]) -> tuple[Point, tuple[str, ...]]:
    anchor = min(points)
    return anchor, tuple(sorted(key(sub(point, anchor)) for point in points))


def orientation_lookup(orientations) -> dict[tuple[str, ...], tuple[Point, object]]:
    lookup = {}
    for orientation in orientations:
        anchor, signature = canonical_points(orientation.vertices)
        lookup[signature] = (anchor, orientation)
    return lookup


def substitution_orientation_placements(orientations, tile: str, levels: int):
    patch = substitution_patch(tile, levels)
    lookup = orientation_lookup(orientations)
    out = []
    for shape_idx, shape in enumerate(patch.shapes):
        shape_anchor, shape_signature = canonical_points(shape.points)
        match = lookup.get(shape_signature)
        if match is None:
            continue
        orientation_anchor, orientation = match
        out.append((shape_idx, shape, orientation, sub(shape_anchor, orientation_anchor)))
    return out


def edge_mark_key(orientation, translation: Point, edge_index: int) -> tuple[str, int]:
    point = add(transform_linear(doubled_midpoint(edge_index), orientation.sym), scale(translation, 2))
    return key(point), map_component(edge_component(edge_index), orientation.sym)


class UnionFind:
    def __init__(self, values):
        self.parents = {value: value for value in values}

    def find(self, value):
        parent = self.parents[value]
        if parent != value:
            self.parents[value] = self.find(parent)
        return self.parents[value]

    def union(self, left, right) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return
        if right_root < left_root:
            left_root, right_root = right_root, left_root
        self.parents[right_root] = left_root


def mined_edge_marking_specs(tile: str, levels: int) -> list[MarkingSpec]:
    orientations = build_hat_orientations(None)
    variables = tuple((side, edge) for side in ("fore", "rear") for edge in range(len(HAT_VERTS)))
    groups: dict[tuple[str, int], set[tuple[str, int]]] = {}
    for _, _, orientation, translation in substitution_orientation_placements(orientations, tile, levels):
        side = "rear" if orientation.is_reflected else "fore"
        for edge_index in range(len(HAT_VERTS)):
            groups.setdefault(edge_mark_key(orientation, translation, edge_index), set()).add((side, edge_index))

    union_find = UnionFind(variables)
    internal_contacts = 0
    for group in groups.values():
        if len(group) < 2:
            continue
        internal_contacts += 1
        first, *rest = sorted(group)
        for item in rest:
            union_find.union(first, item)

    components: dict[tuple[str, int], list[tuple[str, int]]] = {}
    for variable in variables:
        components.setdefault(union_find.find(variable), []).append(variable)
    value_by_root = {root: idx + 1 for idx, root in enumerate(sorted(components))}
    value_by_variable = {variable: value_by_root[union_find.find(variable)] for variable in variables}
    fore_marks = tuple((edge, value_by_variable[("fore", edge)]) for edge in range(len(HAT_VERTS)))
    rear_marks = tuple((edge, value_by_variable[("rear", edge)]) for edge in range(len(HAT_VERTS)))
    class_count = len(set(value_by_variable.values()))
    return [
        MarkingSpec(
            f"edge-mined:{tile}{levels}:classes={class_count}:contacts={internal_contacts}",
            fore_edge_marks=fore_marks,
            rear_edge_marks=rear_marks,
        )
    ]


def mark_line_id(point: Point, component: int) -> int:
    if component == 0:
        return point[1] - point[2]
    if component == 1:
        return point[0] - point[2]
    return point[0] - point[1]


def mark_line_step(component: int) -> Point:
    if component == 0:
        return (-2, 1, 1)
    if component == 1:
        return (1, -2, 1)
    return (1, 1, -2)


def mark_continuity_metrics(mark_values: dict[tuple[Point, int], tuple[int, int]]) -> dict[str, object]:
    groups: dict[tuple[int, int, int], set[Point]] = {}
    for point, component in mark_values:
        value, _ = mark_values[(point, component)]
        groups.setdefault((component, value, mark_line_id(point, component)), set()).add(point)

    degree_counts = {0: 0, 1: 0, 2: 0}
    runs: list[int] = []
    for (component, _value, _line_id), points in groups.items():
        step = mark_line_step(component)
        for point in points:
            degree = int(add(point, step) in points) + int(sub(point, step) in points)
            degree_counts[degree] += 1
            if sub(point, step) in points:
                continue
            length = 0
            next_point = point
            while next_point in points:
                length += 1
                next_point = add(next_point, step)
            runs.append(length)

    mark_count = len(mark_values)
    squared_run_sum = sum(length * length for length in runs)
    score = squared_run_sum / mark_count if mark_count else 0.0
    return {
        "score": round(score, 3),
        "line_count": len(groups),
        "run_count": len(runs),
        "max_run": max(runs, default=0),
        "mean_run": round(sum(runs) / len(runs), 3) if runs else 0.0,
        "degree0": degree_counts[0],
        "degree1": degree_counts[1],
        "degree2": degree_counts[2],
        "top_runs": sorted(runs, reverse=True)[:12],
    }


def validate_substitution_patch(
    spec: MarkingSpec | None,
    orientations,
    tile: str,
    levels: int,
    conflict_limit: int = 8,
) -> dict[str, object]:
    patch = substitution_patch(tile, levels)
    lookup = orientation_lookup(orientations)
    mark_values: dict[tuple[Point, int], tuple[int, int]] = {}
    occupancy_values: dict[str, int] = {}
    missing_shapes = []
    mark_conflicts = []
    angle_overflows = []

    for shape_idx, shape in enumerate(patch.shapes):
        shape_anchor, shape_signature = canonical_points(shape.points)
        match = lookup.get(shape_signature)
        if match is None:
            missing_shapes.append({"shape": shape_idx, "label": shape.label})
            continue
        orientation_anchor, orientation = match
        translation = sub(shape_anchor, orientation_anchor)
        placement = place(orientation, translation, f"substitution-{shape_idx}")

        for entry in placement.occupancy:
            point_key = key(entry.point)
            next_value = occupancy_values.get(point_key, 0) + entry.value
            occupancy_values[point_key] = next_value
            if next_value > MAX_ANGLE and len(angle_overflows) < conflict_limit:
                angle_overflows.append({"shape": shape_idx, "point": list(entry.point), "value": next_value})

        for mark in placement.marks:
            mark_key = (mark.point, mark.component)
            previous = mark_values.get(mark_key)
            if previous is None:
                mark_values[mark_key] = (mark.value, shape_idx)
                continue
            previous_value, previous_shape = previous
            if previous_value != mark.value and len(mark_conflicts) < conflict_limit:
                mark_conflicts.append(
                    {
                        "shape": shape_idx,
                        "previous_shape": previous_shape,
                        "point": list(mark.point),
                        "component": mark.component,
                        "previous_value": previous_value,
                        "value": mark.value,
                    }
                )

    return {
        "tile": tile,
        "levels": levels,
        "shape_count": len(patch.shapes),
        "marking": spec.name if spec else "none",
        "valid": not missing_shapes and not mark_conflicts and not angle_overflows,
        "missing_shapes": missing_shapes[:conflict_limit],
        "mark_conflicts": mark_conflicts,
        "angle_overflows": angle_overflows,
        "mark_points": len(mark_values),
        "continuity": mark_continuity_metrics(mark_values),
    }


def lattice_steps(a: Point, b: Point) -> int:
    return math.gcd(math.gcd(abs(b[0] - a[0]), abs(b[1] - a[1])), abs(b[2] - a[2]))


def line_segment_candidates(min_lattice_steps: int, mode: str) -> list[tuple[tuple[str, str, int], int]]:
    base: list[tuple[tuple[str, str, int], int]] = []
    for source, target in itertools.combinations(endpoint_refs(mode), 2):
        p1, p2 = endpoint_point(source), endpoint_point(target)
        if line_component_or_none(p1, p2) is None:
            continue
        steps = lattice_steps(p1, p2)
        if steps < min_lattice_steps:
            continue
        base.append(((source, target, 1), steps))
    base.sort(key=lambda item: (item[0][0][0] == item[0][1][0], item[0][0], item[0][1]))
    return base


def all_line_segment_specs(max_segments: int, min_lattice_steps: int, mode: str) -> list[MarkingSpec]:
    base = [segment for segment, _ in line_segment_candidates(min_lattice_steps, mode)]

    specs = [MarkingSpec("index-stripes", tuple(INDEX_STRIPES))]
    for size in range(1, max_segments + 1):
        for combo in itertools.combinations(base, size):
            label = "+".join(f"{a}-{b}" for a, b, _ in combo)
            specs.append(MarkingSpec(f"line:{label}", combo))
    return specs


def side_prefiltered_segments(
    candidates: list[tuple[tuple[str, str, int], int]],
    side: str,
    tile: str,
    levels: int,
    mark_value_mode: str,
    mark_reach: int,
) -> list[tuple[tuple[str, str, int], int]]:
    if levels < 0:
        return candidates
    out = []
    for segment, steps in candidates:
        spec = MarkingSpec(
            f"prefilter:{side}:{format_segment(segment)}",
            fore_segments=(segment,) if side == "fore" else (),
            rear_segments=(segment,) if side == "rear" else (),
        )
        orientations = build_hat_orientations(spec, mark_value_mode, mark_reach)
        validation = validate_substitution_patch(spec, orientations, tile, levels)
        if validation["valid"]:
            out.append((segment, steps))
    return out


def all_gab_like_specs(
    fore_count: int,
    rear_count: int,
    min_lattice_steps: int,
    mode: str,
    tile: str,
    levels: int,
    require_ratio: bool,
    mark_value_mode: str,
    rear_sign_variants: bool,
    mark_reach: int,
) -> list[MarkingSpec]:
    candidates = line_segment_candidates(min_lattice_steps, mode)
    fore_candidates = side_prefiltered_segments(candidates, "fore", tile, levels, mark_value_mode, mark_reach)
    rear_candidates = side_prefiltered_segments(candidates, "rear", tile, levels, mark_value_mode, mark_reach)

    specs: list[MarkingSpec] = []
    for fore_combo in itertools.combinations(fore_candidates, fore_count):
        fore_segments = tuple(segment for segment, _ in fore_combo)
        fore_steps = sum(steps for _, steps in fore_combo)
        for rear_combo in itertools.combinations(rear_candidates, rear_count):
            rear_segments = tuple(segment for segment, _ in rear_combo)
            rear_steps = sum(steps for _, steps in rear_combo)
            if require_ratio and rear_steps != 4 * fore_steps:
                continue
            fore_label = "+".join(format_segment(segment) for segment in fore_segments)
            sign_patterns = itertools.product((1, -1), repeat=len(rear_segments)) if rear_sign_variants else [(1,) * len(rear_segments)]
            for signs in sign_patterns:
                signed_rear_segments = tuple(
                    (source, target, sign * abs(value))
                    for (source, target, value), sign in zip(rear_segments, signs)
                )
                rear_label = "+".join(format_segment(segment) for segment in signed_rear_segments)
                specs.append(
                    MarkingSpec(
                        f"gab:fore={fore_label}|rear={rear_label}",
                        fore_segments=fore_segments,
                        rear_segments=signed_rear_segments,
                    )
                )
    return specs


def summarize(result) -> dict[str, object]:
    return {
        "policy": result.policy,
        "seed": result.seed,
        "elapsed_ms": result.elapsed_ms,
        "tile_count": result.tile_count,
        "corona": result.corona,
        "reward": round(result.reward, 3),
        "stopped_reason": result.stopped_reason,
        "decisions": result.decisions,
        "forced_moves": result.forced_moves,
        "branch_moves": result.branch_moves,
        "dead_frontier_checks": result.dead_frontier_checks,
    }


def run_search_summary(orientations: list[Orientation], args: argparse.Namespace, stage: int = 1) -> dict[str, object]:
    if stage == 1:
        target_tiles = args.target_tiles
        target_corona = args.target_corona
        max_steps = args.max_steps
        node_limit = args.node_limit
        wall_time_ms = args.wall_time_ms
    else:
        target_tiles = args.stage2_target_tiles
        target_corona = args.stage2_target_corona
        max_steps = args.stage2_max_steps
        node_limit = args.stage2_node_limit
        wall_time_ms = args.stage2_wall_time_ms
    result = run_tree_search(
        orientations=orientations,
        weights=getattr(args, "policy_weights", {}),
        seed=args.seed,
        policy=args.policy,
        target_tiles=target_tiles,
        target_corona=target_corona,
        max_steps=max_steps,
        node_limit=node_limit,
        wall_time_ms=wall_time_ms,
        frontier_limit=args.frontier_limit,
        candidate_limit=args.candidate_limit,
        boundary_alive=not args.no_boundary_alive,
    )
    return summarize(result)


def continuity_score(validation: dict[str, object] | None) -> float:
    if not validation:
        return 0.0
    continuity = validation.get("continuity", {})
    if not isinstance(continuity, dict):
        return 0.0
    return float(continuity.get("score", 0.0))


def static_spec_payload(
    spec: MarkingSpec | None,
    orientations: list[Orientation],
    validation: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "marking": spec.name if spec else "none",
        "segment_count": segment_count(spec),
        "segments": segment_payload(spec),
        "orientation_count": len(orientations),
        "occupancy_points": len(orientations[0].occupancy),
        "mark_points": len(orientations[0].marks),
        "substitution_validation": validation,
    }


def should_skip_for_validation(
    spec: MarkingSpec | None,
    orientations: list[Orientation],
    validation: dict[str, object] | None,
    args: argparse.Namespace,
) -> dict[str, object] | None:
    if validation and args.require_substitution_valid and not validation["valid"]:
        return {
            **static_spec_payload(spec, orientations, validation),
            "skipped_reason": "substitution_validation_failed",
        }
    if validation and args.min_continuity_score > 0 and continuity_score(validation) < args.min_continuity_score:
        return {
            **static_spec_payload(spec, orientations, validation),
            "skipped_reason": "continuity_score_too_low",
        }
    return None


def run_spec(spec: MarkingSpec | None, args: argparse.Namespace, benchmark: bool = True) -> dict[str, object]:
    orientations = build_hat_orientations(spec, args.mark_value_mode, args.mark_reach)
    validation = None
    if args.validate_substitution_levels >= 0:
        validation = validate_substitution_patch(
            spec,
            orientations,
            args.substitution_tile,
            args.validate_substitution_levels,
        )
        skipped = should_skip_for_validation(spec, orientations, validation, args)
        if skipped:
            return skipped
    if args.validate_only or not benchmark:
        return {
            **static_spec_payload(spec, orientations, validation),
            "skipped_reason": "validate_only" if args.validate_only else "benchmark_limit",
        }
    result = run_search_summary(orientations, args, stage=1)
    return {
        **static_spec_payload(spec, orientations, validation),
        "result": result,
    }


def run_staged_spec(
    spec: MarkingSpec | None,
    args: argparse.Namespace,
    baseline_stage1: dict[str, object],
    benchmark: bool = True,
) -> dict[str, object]:
    orientations = build_hat_orientations(spec, args.mark_value_mode, args.mark_reach)
    validation = None
    if args.validate_substitution_levels >= 0:
        validation = validate_substitution_patch(spec, orientations, args.substitution_tile, args.validate_substitution_levels)
        skipped = should_skip_for_validation(spec, orientations, validation, args)
        if skipped:
            return skipped
    if args.validate_only or not benchmark:
        return {
            **static_spec_payload(spec, orientations, validation),
            "skipped_reason": "validate_only" if args.validate_only else "benchmark_limit",
        }

    stage1 = run_search_summary(orientations, args, stage=1)
    stage1_decision_gain = int(baseline_stage1["decisions"]) - int(stage1["decisions"])
    reaches_stage1_target = int(stage1["tile_count"]) >= args.target_tiles
    stage2 = None
    skipped_reason = None
    if args.stage1_require_target and not reaches_stage1_target:
        skipped_reason = "stage1_target_not_reached"
    elif stage1_decision_gain < args.stage1_min_decision_gain:
        skipped_reason = "stage1_decision_gain_too_small"
    else:
        stage2 = run_search_summary(orientations, args, stage=2)

    return {
        **static_spec_payload(spec, orientations, validation),
        "stage1": stage1,
        "stage1_decision_gain": stage1_decision_gain,
        "stage2": stage2,
        "skipped_reason": skipped_reason,
    }


def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search candidate Hat markings for local GCTS acceleration.")
    parser.add_argument("--mode", choices=["benchmark", "search", "staged", "train-policy"], default="search")
    parser.add_argument("--policy", choices=["random", "heuristic", "learned"], default="heuristic")
    parser.add_argument("--target-tiles", type=int, default=50)
    parser.add_argument("--target-corona", type=int, default=4)
    parser.add_argument("--max-steps", type=int, default=90)
    parser.add_argument("--node-limit", type=int, default=1200)
    parser.add_argument("--wall-time-ms", type=int, default=10000)
    parser.add_argument("--stage2-target-tiles", type=int, default=70)
    parser.add_argument("--stage2-target-corona", type=int, default=10)
    parser.add_argument("--stage2-max-steps", type=int, default=120)
    parser.add_argument("--stage2-node-limit", type=int, default=4000)
    parser.add_argument("--stage2-wall-time-ms", type=int, default=35000)
    parser.add_argument("--stage1-min-decision-gain", type=int, default=1)
    parser.add_argument(
        "--stage1-require-target",
        action="store_true",
        help="In staged mode, only run stage 2 if the candidate reaches the stage-1 tile target.",
    )
    parser.add_argument("--frontier-limit", type=int, default=12)
    parser.add_argument("--candidate-limit", type=int, default=18)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--eval-runs", type=int, default=1)
    parser.add_argument("--baseline-runs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--temperature", type=float, default=0.75)
    parser.add_argument("--policy-in")
    parser.add_argument("--policy-out")
    parser.add_argument("--max-mark-segments", type=int, default=2)
    parser.add_argument("--min-lattice-steps", type=int, default=2)
    parser.add_argument(
        "--endpoint-mode",
        choices=["vertices", "midpoints", "all"],
        default="all",
        help="Endpoint set for generated candidate markings.",
    )
    parser.add_argument(
        "--segments",
        help="Custom marking segments, e.g. '5-11', 'v2-m8', or 'v2-m8:-1'. Values default to +1.",
    )
    parser.add_argument("--fore-segments", help="Segments used only on non-reflected Hat orientations.")
    parser.add_argument("--rear-segments", help="Segments used only on reflected Hat orientations.")
    parser.add_argument(
        "--mark-value-mode",
        choices=["reflection", "constant", "presence"],
        default="reflection",
        help="How marking values transform under Hat orientation symmetries.",
    )
    parser.add_argument(
        "--mark-reach",
        type=int,
        default=MARK_REACH,
        help="Extra marking continuation reach in original A2 lattice units.",
    )
    parser.add_argument(
        "--search-family",
        choices=["line", "gab", "edge"],
        default="line",
        help="Candidate family used in --mode search.",
    )
    parser.add_argument("--fore-segment-count", type=int, default=1)
    parser.add_argument("--rear-segment-count", type=int, default=3)
    parser.add_argument(
        "--gab-ratio",
        action="store_true",
        help="For --search-family gab, require rear total lattice length to be 4x the fore length.",
    )
    parser.add_argument(
        "--rear-sign-variants",
        action="store_true",
        help="For --search-family gab, enumerate all +/- sign patterns on rear segments.",
    )
    parser.add_argument(
        "--shuffle-candidates",
        action="store_true",
        help="Shuffle generated search candidates deterministically before applying --limit.",
    )
    parser.add_argument(
        "--shuffle-seed",
        type=int,
        help="Seed used for candidate shuffling; defaults to --seed when omitted.",
    )
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument(
        "--max-benchmarks",
        type=int,
        default=0,
        help="Maximum number of validation-passing candidates to benchmark; 0 means no cap.",
    )
    parser.add_argument("--output", default="runs/hat-marking-search.json")
    parser.add_argument("--no-boundary-alive", action="store_true")
    parser.add_argument(
        "--validate-substitution-levels",
        type=int,
        default=-1,
        help="Validate markings on an H7/H8 substitution patch of this level; -1 disables validation.",
    )
    parser.add_argument("--substitution-tile", choices=["H7", "H8"], default="H8")
    parser.add_argument(
        "--require-substitution-valid",
        action="store_true",
        help="Skip GCTS benchmarking for candidates that conflict on the substitution patch.",
    )
    parser.add_argument(
        "--min-continuity-score",
        type=float,
        default=0.0,
        help="Skip GCTS benchmarking for validation-passing candidates below this substitution-patch continuity score.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only run substitution validation; do not benchmark GCTS candidates.",
    )
    return parser.parse_args()


def parse_segment_item(item: str) -> tuple[str, str, int]:
    segment_part, _, value_part = item.partition(":")
    parts = segment_part.split("-")
    if len(parts) != 2:
        raise ValueError(f"bad segment spec {item!r}; use a-b or a-b:value")
    source, target = normalize_endpoint_ref(parts[0]), normalize_endpoint_ref(parts[1])
    value = int(value_part) if value_part else 1
    return (source, target, value)


def parse_segment_list(raw: str | None) -> tuple[tuple[str, str, int], ...]:
    segments = []
    if not raw:
        return ()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        segments.append(parse_segment_item(item))
    return tuple(segments)


def format_segment(segment: tuple[str, str, int]) -> str:
    source, target, value = segment
    return f"{source}-{target}" if value == 1 else f"{source}-{target}:{value}"


def parse_custom_segments(common_raw: str | None, fore_raw: str | None, rear_raw: str | None) -> MarkingSpec:
    common = parse_segment_list(common_raw)
    fore = parse_segment_list(fore_raw)
    rear = parse_segment_list(rear_raw)
    segments = (*common, *fore, *rear)
    if not segments:
        raise ValueError("custom marking did not contain any segments")
    if fore or rear:
        common_label = "+".join(format_segment(segment) for segment in common) or "none"
        fore_label = "+".join(format_segment(segment) for segment in fore) or "none"
        rear_label = "+".join(format_segment(segment) for segment in rear) or "none"
        return MarkingSpec(
            f"custom:common={common_label}|fore={fore_label}|rear={rear_label}",
            common,
            fore,
            rear,
        )
    label = "+".join(format_segment(segment) for segment in common)
    return MarkingSpec(f"custom:{label}", common)


def score_entry(entry: dict[str, object], baseline: dict[str, object]) -> tuple[int, int, int, int]:
    result = entry["result"]
    base_result = baseline["result"]
    assert isinstance(result, dict) and isinstance(base_result, dict)
    tile_gain = int(result["tile_count"]) - int(base_result["tile_count"])
    corona_gain = int(result["corona"]) - int(base_result["corona"])
    decision_gain = int(base_result["decisions"]) - int(result["decisions"])
    time_gain = int(base_result["elapsed_ms"]) - int(result["elapsed_ms"])
    return (tile_gain, corona_gain, decision_gain, time_gain)


def score_staged_entry(entry: dict[str, object], baseline: dict[str, object]) -> tuple[int, int, int, int, int, int]:
    stage1 = entry["stage1"]
    stage2 = entry["stage2"]
    baseline_stage1 = baseline["stage1"]
    baseline_stage2 = baseline["stage2"]
    assert isinstance(stage1, dict) and isinstance(stage2, dict)
    assert isinstance(baseline_stage1, dict) and isinstance(baseline_stage2, dict)
    stage2_tile_gain = int(stage2["tile_count"]) - int(baseline_stage2["tile_count"])
    stage2_corona_gain = int(stage2["corona"]) - int(baseline_stage2["corona"])
    stage2_decision_gain = int(baseline_stage2["decisions"]) - int(stage2["decisions"])
    stage2_time_gain = int(baseline_stage2["elapsed_ms"]) - int(stage2["elapsed_ms"])
    stage1_decision_gain = int(baseline_stage1["decisions"]) - int(stage1["decisions"])
    stage1_time_gain = int(baseline_stage1["elapsed_ms"]) - int(stage1["elapsed_ms"])
    return (stage2_tile_gain, stage2_corona_gain, stage2_decision_gain, stage2_time_gain, stage1_decision_gain, stage1_time_gain)


def run_policy_experiment(spec: MarkingSpec | None, args: argparse.Namespace) -> dict[str, object]:
    orientations = build_hat_orientations(spec, args.mark_value_mode, args.mark_reach)
    validation = None
    if args.validate_substitution_levels >= 0:
        validation = validate_substitution_patch(spec, orientations, args.substitution_tile, args.validate_substitution_levels)
    skipped = should_skip_for_validation(spec, orientations, validation, args)
    if skipped:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": vars(args),
            "candidate": skipped,
            "training": {"episodes": 0, "checkpoints": [], "best_training_run": None},
            "evaluation": [],
            "learned_weights_top": [],
            "weights": {},
        }

    weights = load_policy(args.policy_in)
    boundary_alive = not args.no_boundary_alive
    training_results = []
    checkpoints: list[dict[str, object]] = []
    recent_rewards: list[float] = []
    best_training = None

    for episode in range(args.episodes):
        result = run_episode(
            orientations=orientations,
            weights=weights,
            seed=args.seed + episode * 17,
            policy="train",
            target_tiles=args.target_tiles,
            target_corona=args.target_corona,
            max_steps=args.max_steps,
            wall_time_ms=args.wall_time_ms,
            frontier_limit=args.frontier_limit,
            candidate_limit=args.candidate_limit,
            boundary_alive=boundary_alive,
            temperature=args.temperature,
            training=True,
        )
        training_results.append(result)
        recent_rewards.append(result.reward)
        if len(recent_rewards) > 24:
            recent_rewards.pop(0)
        mean_reward = sum(recent_rewards) / len(recent_rewards)
        variance = sum((value - mean_reward) ** 2 for value in recent_rewards) / max(1, len(recent_rewards) - 1)
        std_reward = math.sqrt(variance) or 1.0
        update_policy(weights, result, (result.reward - mean_reward) / std_reward, args.learning_rate)
        if best_training is None or result.reward > best_training.reward:
            best_training = result
        if episode == 0 or (episode + 1) % max(1, args.episodes // 10) == 0:
            window = training_results[-max(1, min(10, len(training_results))):]
            checkpoints.append(
                {
                    "episode": episode + 1,
                    "mean_reward_last": round(sum(item.reward for item in window) / len(window), 3),
                    "mean_tiles_last": round(sum(item.tile_count for item in window) / len(window), 2),
                    "max_tiles_so_far": max(item.tile_count for item in training_results),
                    "max_corona_so_far": max(item.corona for item in training_results),
                }
            )

    eval_results = {}
    for policy_name in ("random", "heuristic", "learned"):
        total_runs = args.eval_runs if policy_name == "learned" else args.baseline_runs
        if total_runs <= 0:
            continue
        runs = []
        for idx in range(total_runs):
            run_seed = args.seed + 10_000 + idx * 101 + len(policy_name)
            runs.append(
                run_tree_search(
                    orientations=orientations,
                    weights=weights,
                    seed=run_seed,
                    policy=policy_name,
                    target_tiles=args.target_tiles,
                    target_corona=args.target_corona,
                    max_steps=args.max_steps,
                    node_limit=args.node_limit,
                    wall_time_ms=args.wall_time_ms,
                    frontier_limit=args.frontier_limit,
                    candidate_limit=args.candidate_limit,
                    boundary_alive=boundary_alive,
                )
            )
        eval_results[policy_name] = runs

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": vars(args),
        "candidate": static_spec_payload(spec, orientations, validation),
        "training": {
            "episodes": len(training_results),
            "checkpoints": checkpoints,
            "best_training_run": summarize(best_training) if best_training else None,
        },
        "evaluation": [
            aggregate_results(policy_name, runs, args.target_tiles, args.target_corona)
            for policy_name, runs in eval_results.items()
        ],
        "learned_weights_top": top_weights(weights),
        "weights": weights,
    }
    if args.policy_out:
        target = Path(args.policy_out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"generated_at": payload["generated_at"], "weights": weights}, indent=2) + "\n", encoding="utf-8")
    return payload


def baseline_payload(args: argparse.Namespace) -> dict[str, object]:
    orientations = build_hat_orientations(None, args.mark_value_mode, args.mark_reach)
    validation = None
    if args.validate_substitution_levels >= 0:
        validation = validate_substitution_patch(None, orientations, args.substitution_tile, args.validate_substitution_levels)
    payload: dict[str, object] = static_spec_payload(None, orientations, validation)
    if args.validate_only:
        payload["skipped_reason"] = "validate_only"
        return payload
    if args.mode == "staged":
        payload["stage1"] = run_search_summary(orientations, args, stage=1)
        payload["stage2"] = run_search_summary(orientations, args, stage=2)
    else:
        payload["result"] = run_search_summary(orientations, args, stage=1)
    return payload


def main() -> None:
    args = read_args()
    args.policy_weights = load_policy(args.policy_in)

    custom_requested = bool(args.segments or args.fore_segments or args.rear_segments)
    generated_specs: list[MarkingSpec] | None = None
    if not custom_requested:
        if args.search_family == "edge":
            generated_specs = mined_edge_marking_specs(args.substitution_tile, args.validate_substitution_levels)
        elif args.search_family == "gab":
            generated_specs = all_gab_like_specs(
                args.fore_segment_count,
                args.rear_segment_count,
                args.min_lattice_steps,
                args.endpoint_mode,
                args.substitution_tile,
                args.validate_substitution_levels,
                args.gab_ratio,
                args.mark_value_mode,
                args.rear_sign_variants,
                args.mark_reach,
            )
        else:
            generated_specs = all_line_segment_specs(args.max_mark_segments, args.min_lattice_steps, args.endpoint_mode)

    if args.mode == "train-policy":
        spec = parse_custom_segments(args.segments, args.fore_segments, args.rear_segments) if custom_requested else generated_specs[0]
        payload = run_policy_experiment(spec, args)
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "candidate": payload["candidate"],
                    "training": payload["training"],
                    "evaluation": payload["evaluation"],
                    "learned_weights_top": payload["learned_weights_top"],
                },
                indent=2,
            )
        )
        print(f"wrote {args.output}")
        if args.policy_out:
            print(f"wrote {args.policy_out}")
        return

    baseline = baseline_payload(args)
    entries = [baseline]

    specs = [parse_custom_segments(args.segments, args.fore_segments, args.rear_segments)] if custom_requested else [
        MarkingSpec("index-stripes", tuple(INDEX_STRIPES))
    ]
    if args.mode in {"search", "staged"} and not custom_requested:
        assert generated_specs is not None
        specs = generated_specs
    if args.shuffle_candidates:
        random.Random(args.seed if args.shuffle_seed is None else args.shuffle_seed).shuffle(specs)
    specs = specs[: args.limit]

    benchmarked = 0
    for spec in specs:
        try:
            benchmark_allowed = args.max_benchmarks <= 0 or benchmarked < args.max_benchmarks
            if args.mode == "staged":
                baseline_stage1 = baseline.get("stage1", {})
                assert isinstance(baseline_stage1, dict)
                entry = run_staged_spec(spec, args, baseline_stage1, benchmark_allowed)
            else:
                entry = run_spec(spec, args, benchmark_allowed)
            if "result" in entry or "stage1" in entry:
                benchmarked += 1
        except ValueError as error:
            entry = {
                "marking": spec.name,
                "segment_count": segment_count(spec),
                "segments": segment_payload(spec),
                "error": str(error),
            }
        entries.append(entry)

    if args.mode == "staged":
        ranked = [
            {
                **entry,
                "score_vs_baseline": list(score_staged_entry(entry, baseline)),
            }
            for entry in entries[1:]
            if "stage2" in entry and entry["stage2"] is not None
        ]
        ranked.sort(key=lambda entry: tuple(entry["score_vs_baseline"]), reverse=True)
    else:
        ranked = [
            {
                **entry,
                "score_vs_baseline": list(score_entry(entry, baseline)),
            }
            for entry in entries[1:]
            if "result" in entry
        ]
        ranked.sort(key=lambda entry: tuple(entry["score_vs_baseline"]), reverse=True)

    validation_ranked = [
        {
            **entry,
            "continuity_score": continuity_score(entry.get("substitution_validation")),
        }
        for entry in entries[1:]
        if isinstance(entry.get("substitution_validation"), dict)
        and entry["substitution_validation"].get("valid")
    ]
    validation_ranked.sort(
        key=lambda entry: (
            entry["continuity_score"],
            entry["substitution_validation"]["continuity"]["max_run"],
            -entry["substitution_validation"]["continuity"]["run_count"],
        ),
        reverse=True,
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": vars(args),
        "hat_geometry": {
            "source": "https://cs.uwaterloo.ca/~csk/hat/h7h8.js",
            "vertices": [list(point) for point in HAT_VERTS],
            "angles": HAT_ANGLES,
            "mark_reach": args.mark_reach,
            "mark_lattice_scale": 2,
            "mark_value_mode": args.mark_value_mode,
        },
        "baseline": baseline,
        "entries": entries,
        "ranked": ranked[:20],
        "validation_ranked": validation_ranked[:20],
    }

    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"baseline": baseline, "ranked": ranked[:8], "validation_ranked": validation_ranked[:8]}, indent=2))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
