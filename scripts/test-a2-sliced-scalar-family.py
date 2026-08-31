#!/usr/bin/env python3
"""Independently replay the all-scale atomic substitution certificates."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "a2_scalar", ROOT / "scripts/screen-a2-sliced-alcove-substitution.py"
)
sub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sub)


def inequalities(slope, intercept, order, source):
    points = []
    current = list(intercept)
    points.append(tuple(current))
    for axis in order:
        current = current.copy()
        current[axis] += 1
        points.append(tuple(current))
    a, b, c = source["order"]
    result = []
    local_slope = [slope[axis] - source["base"][axis] for axis in range(3)]
    for point in points:
        result.extend((
            (local_slope[c], point[c]),
            (local_slope[b] - local_slope[c], point[b] - point[c]),
            (local_slope[a] - local_slope[b], point[a] - point[b]),
            (1 - local_slope[a], -point[a]),
        ))
    return result


candidates = {
    record["id"]: record
    for record in map(json.loads, (
        ROOT / "data/a2-sliced-alcove-size9-focused-periodic-exact8.ndjson"
    ).read_text().splitlines())
}
receipts = [
    json.loads(line) for line in (
        ROOT / "data/a2-sliced-alcove-size9-scalar-family-certificates.ndjson"
    ).read_text().splitlines() if line.strip()
]
assert len(receipts) == 6
assert {receipt["id"] for receipt in receipts} == {
    "a2sa_9_11364", "a2sa_9_13833", "a2sa_9_15635"
}

for receipt in receipts:
    assert receipt["classification"] == "no_direct_scalar_substitution_all_integer_scales"
    proof = receipt["scalar_family_atomic_obstruction"]
    assert proof["certified"] is True
    assert proof["integer_scale_range"] == [2, None]
    record = candidates[receipt["id"]]
    cells = record["alcoves"]
    witness = proof["witness"]
    witness_inequalities = inequalities(
        witness["base_slope"], witness["base_intercept"], witness["order"],
        cells[witness["permanent_target_source_alcove_index"]],
    )
    assert all(a >= 0 and 2 * a + b >= 0 for a, b in witness_inequalities)

    orientations = sub.oriented_cells(cells, proof["include_reflections"])
    expected_cases = {
        (orientation_index, anchor_index)
        for orientation_index, orientation in enumerate(orientations)
        for anchor_index, anchor in enumerate(orientation["cells"])
        if anchor["order"] == witness["order"]
    }
    actual_cases = {
        (case["orientation_index"], case["anchor_alcove_index"])
        for case in proof["covering_case_obstructions"]
    }
    assert actual_cases == expected_cases
    assert proof["orientation_anchor_cases_exhausted"] == len(expected_cases)

    for case in proof["covering_case_obstructions"]:
        orientation = orientations[case["orientation_index"]]["cells"]
        anchor = orientation[case["anchor_alcove_index"]]
        blocker = case["blocking_child"]
        child = orientation[blocker["child_alcove_index"]]
        expected_intercept = [
            witness["base_intercept"][axis] - anchor["base"][axis]
            + child["base"][axis] for axis in range(3)
        ]
        assert blocker["base_slope"] == witness["base_slope"]
        assert blocker["base_intercept"] == expected_intercept
        assert blocker["order"] == child["order"]
        assert len(blocker["source_failures"]) == len(cells)
        for failure in blocker["source_failures"]:
            source_index = failure["source_alcove_index"]
            failed = tuple(failure["failed_inequality"])
            assert failed in inequalities(
                blocker["base_slope"], blocker["base_intercept"],
                blocker["order"], cells[source_index],
            )
            assert failed[0] <= 0 and 2 * failed[0] + failed[1] < 0
            assert failure["value_at_min_scale"] == 2 * failed[0] + failed[1]

    for scale in (2, 5, 13):
        target = sub.inflated_cells(cells, scale)
        witness_key = tuple(
            witness["base_slope"][axis] * scale + witness["base_intercept"][axis]
            for axis in range(3)
        ) + ("".join(map(str, witness["order"])),)
        assert witness_key in target
        for orientation in orientations:
            own = [sub.cell_key(cell) for cell in orientation["cells"]]
            for anchor in own:
                if anchor[3] != witness_key[3]:
                    continue
                delta = tuple(witness_key[axis] - anchor[axis] for axis in range(3))
                assert not all((cell[0] + delta[0], cell[1] + delta[1],
                                cell[2] + delta[2], cell[3]) in target
                               for cell in own)

print("A2 scalar all-scale substitution certificates replayed")
