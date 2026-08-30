#!/usr/bin/env python3
"""Exact anisotropic substitutions for A2-sliced Kuhn-alcove unions.

The integer map M = p I + c J scales the transverse A2 directions by p and
the x+y+z direction by v = p + 3c.  Its determinant is p^2 v.  Exact Fraction
arithmetic enumerates the unit Kuhn alcoves contained in every transformed
source alcove before the ordinary exact-cover substitution test is applied.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUB = load("a2_sliced_scalar_substitution", "screen-a2-sliced-alcove-substitution.py")
PERMUTATIONS = tuple(itertools.permutations(range(3)))


def transform_point(point, planar_scale: int, coupling: int):
    total = sum(point)
    return tuple(planar_scale * value + coupling * total for value in point)


def inverse_point(point, planar_scale: int, layer_scale: int, coupling: int):
    total = sum(point)
    return tuple(
        Fraction(value, planar_scale)
        - Fraction(coupling * total, planar_scale * layer_scale)
        for value in point
    )


def point_in_transformed_cell(point, source, planar_scale, layer_scale, coupling):
    preimage = inverse_point(point, planar_scale, layer_scale, coupling)
    local = [preimage[axis] - source["base"][axis] for axis in range(3)]
    a, b, c = source["order"]
    return 0 <= local[c] <= local[b] <= local[a] <= 1


def boundary_facets(cells):
    facets = {}
    for cell in cells:
        vertices = SUB.cell_vertices(cell)
        for omitted in range(4):
            facet = tuple(sorted(vertex for index, vertex in enumerate(vertices)
                                 if index != omitted))
            facets[facet] = facets.get(facet, 0) + 1
    return [facet for facet, multiplicity in facets.items() if multiplicity == 1]


def facet_normal(facet):
    left = tuple(facet[1][axis] - facet[0][axis] for axis in range(3))
    right = tuple(facet[2][axis] - facet[0][axis] for axis in range(3))
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


ARRANGEMENT_NORMALS = (
    (1, 0, 0), (0, 1, 0), (0, 0, 1),
    (1, -1, 0), (1, 0, -1), (0, 1, -1),
)


def proportional(left, right):
    return (
        left[0] * right[1] == left[1] * right[0]
        and left[0] * right[2] == left[2] * right[0]
        and left[1] * right[2] == left[2] * right[1]
    )


def transformed_covector(normal, planar_scale, layer_scale, coupling):
    total = sum(normal)
    return tuple(
        Fraction(value, planar_scale)
        - Fraction(coupling * total, planar_scale * layer_scale)
        for value in normal
    )


def noncellular_boundary_witness(cells, planar_scale, layer_scale):
    coupling = (layer_scale - planar_scale) // 3
    for facet in boundary_facets(cells):
        source_normal = facet_normal(facet)
        image_normal = transformed_covector(
            source_normal, planar_scale, layer_scale, coupling
        )
        if not any(proportional(image_normal, allowed)
                   for allowed in ARRANGEMENT_NORMALS):
            return {
                "source_facet": [list(vertex) for vertex in facet],
                "source_normal": list(source_normal),
                "transformed_normal": [
                    [component.numerator, component.denominator]
                    for component in image_normal
                ],
                "allowed_hyperplane_normals": [list(item)
                                                for item in ARRANGEMENT_NORMALS],
            }
    return None


def inflated_cells(cells, planar_scale: int, layer_scale: int):
    if planar_scale < 2 or layer_scale < 2:
        raise ValueError("both A2 and layer scales must be at least two")
    delta = layer_scale - planar_scale
    if delta % 3:
        raise ValueError("integral pI+cJ inflation requires layer_scale == planar_scale mod 3")
    coupling = delta // 3
    target = set()
    for source in cells:
        transformed_vertices = [
            transform_point(point, planar_scale, coupling)
            for point in SUB.cell_vertices(source)
        ]
        minima = [min(point[axis] for point in transformed_vertices) for axis in range(3)]
        maxima = [max(point[axis] for point in transformed_vertices) for axis in range(3)]
        for x in range(minima[0], maxima[0]):
            for y in range(minima[1], maxima[1]):
                for z in range(minima[2], maxima[2]):
                    for order in PERMUTATIONS:
                        candidate = {"base": [x, y, z], "order": list(order)}
                        if all(point_in_transformed_cell(
                            point, source, planar_scale, layer_scale, coupling
                        ) for point in SUB.cell_vertices(candidate)):
                            target.add(SUB.cell_key(candidate))
    determinant = planar_scale * planar_scale * layer_scale
    expected = len(cells) * determinant
    if len(target) != expected:
        raise RuntimeError(
            f"anisotropic target has {len(target)} alcoves, expected {expected}"
        )
    return target


def screen(record, planar_scale, layer_scale, timeout_ms, include_reflections=False):
    delta = layer_scale - planar_scale
    if planar_scale < 2 or layer_scale < 2 or delta % 3:
        raise ValueError("inflation must be expansive with layer_scale == planar_scale mod 3")
    boundary_witness = noncellular_boundary_witness(
        record["alcoves"], planar_scale, layer_scale
    )
    if boundary_witness is not None:
        return {
            **record,
            "anisotropic_substitution_classification": "inflation_not_alcove_cellular",
            "anisotropic_substitution": {
                "inflation_kind": "a2_transverse_by_layer_pI_plus_cJ",
                "planar_scale": planar_scale,
                "layer_scale": layer_scale,
                "coupling": delta // 3,
                "determinant": planar_scale * planar_scale * layer_scale,
                "certified": True,
                "claim_scope": "fixed_affine_A3_alcove_cellular_substitution_only",
                "boundary_witness": boundary_witness,
                "noncellular_substitution_open": True,
            },
        }
    orientations = SUB.oriented_cells(record["alcoves"], include_reflections)
    target = inflated_cells(record["alcoves"], planar_scale, layer_scale)
    copies = planar_scale * planar_scale * layer_scale
    common = {
        "inflation_kind": "a2_transverse_by_layer_pI_plus_cJ",
        "planar_scale": planar_scale,
        "layer_scale": layer_scale,
        "coupling": (layer_scale - planar_scale) // 3,
        "determinant": copies,
        "target_alcoves": len(target),
        "expected_copies": copies,
        "include_reflections": include_reflections,
        "orientations": len(orientations),
    }
    atomic_uncovered = SUB.first_atomically_uncovered(target, orientations)
    if atomic_uncovered is not None:
        return {
            **record,
            "anisotropic_substitution_classification": "no_anisotropic_substitution",
            "anisotropic_substitution": {
                **common,
                "placements_considered": 0,
                "nodes": 0,
                "failed_states": 0,
                "certified": True,
                "claim_scope": "direct_monotile_pI_plus_cJ_alcove_subdivision",
                "atomic_uncovered_alcove": list(atomic_uncovered),
                "independent_replay": {
                    "verified": True,
                    "method": "all_orientation_anchor_containment_scan",
                },
            },
        }
    placements = SUB.candidate_placements(target, orientations)
    solved = SUB.COVER.exact_cover(target, placements, timeout_ms)
    detail = {
        **common,
        "placements_considered": len(placements),
        "nodes": solved["nodes"],
        "failed_states": solved["failed_states"],
    }
    if solved["result"] == "sat":
        checked = SUB.COVER.replay(target, placements, solved["solution"], copies)
        if not checked["verified"]:
            raise RuntimeError(f"anisotropic substitution replay failed: {checked}")
        return {
            **record,
            "anisotropic_substitution_classification": "anisotropic_substitution_rule",
            "anisotropic_substitution": {
                **detail,
                "rule": [{
                    "orientation_index": placements[index]["orientation_index"],
                    "translation": placements[index]["translation"],
                } for index in solved["solution"]],
                "replay": checked,
            },
        }
    if solved["result"] == "unsat":
        return {
            **record,
            "anisotropic_substitution_classification": "no_anisotropic_substitution",
            "anisotropic_substitution": {
                **detail,
                "certified": True,
                "claim_scope": "direct_monotile_pI_plus_cJ_alcove_subdivision",
                "root_uncovered_alcove": solved["root_uncovered_cell"],
            },
        }
    return {
        **record,
        "anisotropic_substitution_classification": "unresolved",
        "anisotropic_substitution": {**detail, "stopped_by": "time_limit"},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--planar-scale", type=int, required=True)
    parser.add_argument("--layer-scale", type=int, required=True)
    parser.add_argument("--timeout-ms", type=int, default=120000)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--ids", default="")
    args = parser.parse_args()
    requested = {value for value in args.ids.split(",") if value}
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines()
               if line.strip()]
    if requested:
        records = [record for record in records if record["id"] in requested]
    output = Path(args.output)
    output.write_text("")
    counts = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen(record, args.planar_scale, args.layer_scale,
                            args.timeout_ms, args.include_reflections)
            classification = result["anisotropic_substitution_classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {classification}", flush=True)
    print(json.dumps({"records": len(records), "counts": counts,
                      "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
