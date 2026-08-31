#!/usr/bin/env python3
"""Certify an atomic obstruction for every integer scalar inflation s >= 2."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_scalar_substitution", ROOT / "scripts/screen-a2-sliced-alcove-substitution.py"
)
SUB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUB)


def affine_vertices(slope, intercept, order):
    vertices = [(tuple(slope), tuple(intercept))]
    current = list(intercept)
    for axis in order:
        current = current.copy()
        current[axis] += 1
        vertices.append((tuple(slope), tuple(current)))
    return vertices


def containment_inequalities(slope, intercept, order, source):
    """Return A,B pairs for every required inequality A*s+B >= 0."""
    a, b, c = source["order"]
    inequalities = []
    for point_slope, point_intercept in affine_vertices(slope, intercept, order):
        local_slope = tuple(point_slope[axis] - source["base"][axis]
                            for axis in range(3))
        local_intercept = point_intercept
        inequalities.extend((
            (local_slope[c], local_intercept[c]),
            (local_slope[b] - local_slope[c],
             local_intercept[b] - local_intercept[c]),
            (local_slope[a] - local_slope[b],
             local_intercept[a] - local_intercept[b]),
            (1 - local_slope[a], -local_intercept[a]),
        ))
    return inequalities


def always_holds(inequality, min_scale):
    coefficient, constant = inequality
    return coefficient >= 0 and coefficient * min_scale + constant >= 0


def permanently_fails(inequality, min_scale):
    coefficient, constant = inequality
    return coefficient <= 0 and coefficient * min_scale + constant < 0


def always_in_target(cells, slope, intercept, order, min_scale):
    return next((
        source_index for source_index, source in enumerate(cells)
        if all(always_holds(item, min_scale) for item in containment_inequalities(
            slope, intercept, order, source
        ))
    ), None)


def outside_target_certificate(cells, slope, intercept, order, min_scale):
    failures = []
    for source_index, source in enumerate(cells):
        inequalities = containment_inequalities(slope, intercept, order, source)
        failed = next((item for item in inequalities
                       if permanently_fails(item, min_scale)), None)
        if failed is None:
            return None
        failures.append({
            "source_alcove_index": source_index,
            "failed_inequality": list(failed),
            "value_at_min_scale": failed[0] * min_scale + failed[1],
        })
    return failures


def certify(record, include_reflections, witness_slope, witness_intercept,
            witness_order=(0, 1, 2), min_scale=2):
    cells = record["alcoves"]
    witness_source = always_in_target(
        cells, witness_slope, witness_intercept, witness_order, min_scale
    )
    if witness_source is None:
        raise RuntimeError("affine witness is not permanently inside the target")
    orientations = SUB.oriented_cells(cells, include_reflections)
    cases = []
    for orientation_index, orientation in enumerate(orientations):
        for anchor_index, anchor in enumerate(orientation["cells"]):
            if tuple(anchor["order"]) != tuple(witness_order):
                continue
            translation_intercept = tuple(
                witness_intercept[axis] - anchor["base"][axis]
                for axis in range(3)
            )
            blocker = None
            for child_index, child in enumerate(orientation["cells"]):
                child_intercept = tuple(
                    translation_intercept[axis] + child["base"][axis]
                    for axis in range(3)
                )
                failures = outside_target_certificate(
                    cells, witness_slope, child_intercept,
                    tuple(child["order"]), min_scale,
                )
                if failures is not None:
                    blocker = {
                        "child_alcove_index": child_index,
                        "base_slope": list(witness_slope),
                        "base_intercept": list(child_intercept),
                        "order": list(child["order"]),
                        "source_failures": failures,
                    }
                    break
            if blocker is None:
                raise RuntimeError(
                    f"unblocked covering case orientation={orientation_index} anchor={anchor_index}"
                )
            cases.append({
                "orientation_index": orientation_index,
                "anchor_alcove_index": anchor_index,
                "blocking_child": blocker,
            })
    if not cases:
        raise RuntimeError("no orientation anchor shares the witness alcove order")
    # Replay several concrete members of the infinite family through the
    # independent finite-cell checker as a guard against affine bookkeeping.
    finite_replay = []
    for scale in range(min_scale, min_scale + 4):
        target = SUB.inflated_cells(cells, scale)
        witness = (*(
            witness_slope[axis] * scale + witness_intercept[axis]
            for axis in range(3)
        ), "".join(map(str, witness_order)))
        uncovered = SUB.first_atomically_uncovered(target, orientations)
        finite_replay.append({
            "scale": scale,
            "witness_in_target": witness in target,
            "witness_uncovered": all(
                not all((cell[0] + witness[0] - own[0],
                         cell[1] + witness[1] - own[1],
                         cell[2] + witness[2] - own[2], cell[3]) in target
                        for cell in [SUB.cell_key(item) for item in orientation["cells"]])
                for orientation in orientations
                for own in [SUB.cell_key(item) for item in orientation["cells"]]
                if own[3] == witness[3]
            ),
            "first_atomic_obstruction": list(uncovered) if uncovered else None,
        })
    if not all(item["witness_in_target"] and item["witness_uncovered"]
               for item in finite_replay):
        raise RuntimeError("finite replay rejected the affine witness")
    return {
        "id": record["id"],
        "classification": "no_direct_scalar_substitution_all_integer_scales",
        "scalar_family_atomic_obstruction": {
            "certified": True,
            "include_reflections": include_reflections,
            "integer_scale_range": [min_scale, None],
            "witness": {
                "base_slope": list(witness_slope),
                "base_intercept": list(witness_intercept),
                "order": list(witness_order),
                "permanent_target_source_alcove_index": witness_source,
            },
            "orientation_anchor_cases_exhausted": len(cases),
            "covering_case_obstructions": cases,
            "finite_replay": finite_replay,
            "proof_method": "affine_integer_inequality_tangent_cone_exhaustion",
            "claim_scope": "direct_monotile_scalar_substitution_with_selected_a2_orientation_group",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", required=True)
    args = parser.parse_args()
    requested = {value for value in args.ids.split(",") if value}
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines()
               if line.strip()]
    records = [record for record in records if record["id"] in requested]
    if {record["id"] for record in records} != requested:
        raise ValueError("not every requested candidate is present")
    output = []
    for record in records:
        for include_reflections in (False, True):
            if include_reflections and record["id"] == "a2sa_9_11364":
                slope, intercept = (1, 0, 0), (-2, 0, 0)
            else:
                slope, intercept = (0, 0, 0), (0, 0, 0)
            output.append(certify(
                record, include_reflections, slope, intercept
            ))
    Path(args.output).write_text("".join(
        json.dumps(record, separators=(",", ":")) + "\n" for record in output
    ))
    print(json.dumps({
        "candidates": len(records), "certificates": len(output),
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
