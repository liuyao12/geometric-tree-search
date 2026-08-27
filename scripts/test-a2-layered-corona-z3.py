#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEOMETRY = load("a2_periodic_z3", "screen-a2-layered-periodic-z3.py")
CORONA = load("a2_corona_z3", "screen-a2-layered-corona-z3.py")
DIRECT = load("a2_corona2_direct", "screen-a2-layered-corona2-direct.py")
SUBSTITUTION = load("a2_substitution", "screen-a2-layered-substitution.py")
CLUSTER_SUBSTITUTION = load(
    "a2_cluster_substitution", "screen-a2-layered-two-cluster-substitution.py"
)
THREE_CLUSTER_SUBSTITUTION = load(
    "a2_three_cluster_substitution", "screen-a2-layered-three-cluster-substitution.py"
)

root_records = [
    json.loads(line)
    for line in (ROOT / "data" / "a2-layered-size7-corona1-z3.ndjson").read_text().splitlines()
    if line.strip()
]
assert len(root_records) == 111
assert all(record["corona_classification"] == "root_corona_exists" for record in root_records)
assert all(record["corona_z3"]["replay"]["verified"] is True for record in root_records)

probe = root_records[0]
root = GEOMETRY.tile_occupancy(probe["cells"])
orientations = GEOMETRY.orientations(root)
placements = CORONA.candidate_placements(root, orientations)
placement_index = {
    (placement["orientation_index"], tuple(placement["translation"])): index
    for index, placement in enumerate(placements)
}
witness = [
    placement_index[(placement["orientation_index"], tuple(placement["translation"]))]
    for placement in probe["corona_z3"]["witness"]
]
assert CORONA.replay_corona(root, placements, witness)["verified"] is True

focused = [
    json.loads(line)
    for line in (ROOT / "data" / "a2-layered-size7-corona2-focused.ndjson").read_text().splitlines()
    if line.strip()
]
assert len(focused) == 8
assert all(record["corona2_classification"] == "unresolved" for record in focused)
assert all(record["corona2_cegar"]["outer_exhausted"] is False for record in focused)
assert all(record["corona2_cegar"]["first_coronas_rejected"] == 8 for record in focused)

deep = json.loads((ROOT / "data" / "a2-layered-size7-corona2-a2lp_7_00232-deep.ndjson").read_text())
assert deep["id"] == "a2lp_7_00232"
assert deep["corona2_classification"] == "unresolved"
assert deep["corona2_cegar"]["first_coronas_rejected"] == 64
assert deep["corona2_cegar"]["outer_exhausted"] is False

unit = DIRECT.screen({
    "id": "a2_unit_prism_control",
    "cells": [{"q": 0, "r": 0, "k": 0, "kind": "u"}],
}, 10000, "default")
assert unit["corona2_direct_classification"] == "radius2_witness"
assert unit["corona2_direct"]["replay"]["verified"] is True

direct_timeout = json.loads(
    (ROOT / "data" / "a2-layered-size7-corona2-direct-a2lp_7_00232-qffd.ndjson").read_text()
)
assert direct_timeout["id"] == "a2lp_7_00232"
assert direct_timeout["corona2_direct_classification"] == "unresolved"
assert direct_timeout["corona2_direct"]["first_placements"] == 580
assert direct_timeout["corona2_direct"]["final_placements"] == 4643
assert direct_timeout["corona2_direct"]["final_incidences"] == 88217
assert direct_timeout["corona2_direct"]["stopped_by"] == "solver_timeout"

reduced_core = json.loads(
    (ROOT / "data" / "a2-layered-size7-corona2-core-a2lp_7_00232-minimized.ndjson").read_text()
)
assert reduced_core["id"] == "a2lp_7_00232"
assert reduced_core["classification"] == "sound_radius2_placement_obstruction"
assert len(reduced_core["source_outer_placement_indices"]) == 16
assert len(reduced_core["reduced_outer_placement_indices"]) == 12
assert reduced_core["minimal"] is False
assert reduced_core["initial_replay"]["result"] == "unsat"
assert reduced_core["final_replay"]["result"] == "unsat"

long_core = json.loads(
    (ROOT / "data" / "a2-layered-size7-corona2-core-a2lp_7_00232-long.ndjson").read_text()
)
assert long_core["id"] == "a2lp_7_00232"
assert long_core["corona2_core_classification"] == "unresolved"
assert long_core["corona2_core_cegar"]["outer_exhausted"] is False
assert long_core["corona2_core_cegar"]["rounds"] == 32
assert len(long_core["corona2_core_cegar"]["clauses"]) == 37
assert sum(
    clause.get("seeded") is True
    for clause in long_core["corona2_core_cegar"]["clauses"]
) == 5

expected_extended_clauses = {
    "a2lp_7_00128": 48,
    "a2lp_7_00211": 45,
    "a2lp_7_00232": 68,
    "a2lp_7_00235": 48,
    "a2lp_7_00694": 47,
    "a2lp_7_00755": 47,
    "a2lp_7_00777": 48,
    "a2lp_7_00809": 47,
}
extended = []
for candidate_id in expected_extended_clauses:
    extended.append(json.loads(
        (ROOT / "data" / f"a2-layered-size7-corona2-core-{candidate_id}-extended.ndjson").read_text()
    ))
assert {record["id"] for record in extended} == set(expected_extended_clauses)
assert all(record["corona2_core_classification"] == "unresolved" for record in extended)
assert all(record["corona2_core_cegar"]["outer_exhausted"] is False for record in extended)
assert all(record["corona2_core_cegar"]["rounds"] == 32 for record in extended)
assert {
    record["id"]: len(record["corona2_core_cegar"]["clauses"])
    for record in extended
} == expected_extended_clauses

expected_deeper_clauses = {
    "a2lp_7_00128": 111,
    "a2lp_7_00211": 109,
    "a2lp_7_00232": 126,
    "a2lp_7_00235": 109,
    "a2lp_7_00694": 109,
    "a2lp_7_00755": 111,
    "a2lp_7_00777": 112,
    "a2lp_7_00809": 111,
}
deeper = [
    json.loads(
        (ROOT / "data" / f"a2-layered-size7-corona2-core-{candidate_id}-deeper.ndjson").read_text()
    )
    for candidate_id in expected_deeper_clauses
]
assert all(record["corona2_core_classification"] == "unresolved" for record in deeper)
assert all(record["corona2_core_cegar"]["outer_exhausted"] is False for record in deeper)
assert all(record["corona2_core_cegar"]["rounds"] == 64 for record in deeper)
assert {
    record["id"]: len(record["corona2_core_cegar"]["clauses"])
    for record in deeper
} == expected_deeper_clauses
assert sum(expected_deeper_clauses.values()) == 898

expected_minimized_core_sizes = {
    "a2lp_7_00128": 7,
    "a2lp_7_00211": 4,
    "a2lp_7_00232": 12,
    "a2lp_7_00235": 9,
    "a2lp_7_00694": 7,
    "a2lp_7_00755": 3,
    "a2lp_7_00777": 6,
    "a2lp_7_00809": 8,
}
minimized_cores = [
    json.loads(
        (ROOT / "data" / f"a2-layered-size7-corona2-core-{candidate_id}-mincore.ndjson").read_text()
    )
    for candidate_id in expected_minimized_core_sizes
]
assert all(record["classification"] == "sound_radius2_placement_obstruction" for record in minimized_cores)
assert all(record["minimal"] is False for record in minimized_cores)
assert all(record["initial_replay"]["result"] == "unsat" for record in minimized_cores)
assert all(record["final_replay"]["result"] == "unsat" for record in minimized_cores)
assert {
    record["id"]: len(record["reduced_outer_placement_indices"])
    for record in minimized_cores
} == expected_minimized_core_sizes

expected_strengthened_clauses = {
    "a2lp_7_00128": 130,
    "a2lp_7_00211": 136,
    "a2lp_7_00232": 156,
    "a2lp_7_00235": 131,
    "a2lp_7_00694": 139,
    "a2lp_7_00755": 142,
    "a2lp_7_00777": 140,
    "a2lp_7_00809": 139,
}
strengthened = [
    json.loads(
        (ROOT / "data" / f"a2-layered-size7-corona2-core-{candidate_id}-strengthened.ndjson").read_text()
    )
    for candidate_id in expected_strengthened_clauses
]
assert all(record["corona2_core_classification"] == "unresolved" for record in strengthened)
assert all(record["corona2_core_cegar"]["outer_exhausted"] is False for record in strengthened)
assert all(record["corona2_core_cegar"]["rounds"] == 32 for record in strengthened)
assert {
    record["id"]: len(record["corona2_core_cegar"]["clauses"])
    for record in strengthened
} == expected_strengthened_clauses
assert sum(expected_strengthened_clauses.values()) == 1113

larger_periodic = []
for part in (1, 2, 3):
    larger_periodic.extend(
        json.loads(line)
        for line in (
            ROOT / "data" / f"a2-layered-size7-periodic-z3-focus6to8-part{part}.ndjson"
        ).read_text().splitlines()
        if line.strip()
    )
assert len(larger_periodic) == 8
assert {record["id"] for record in larger_periodic} == set(expected_extended_clauses)
assert all(record["classification"] == "unresolved" for record in larger_periodic)
assert all(record["periodic_z3"]["active_copies"] == 6 for record in larger_periodic)
assert all(0 < record["periodic_z3"]["hnf_visited"] < 741 for record in larger_periodic)
assert all(record["periodic_z3"]["solver_unknown"] > 0 for record in larger_periodic)

substitution_unit = SUBSTITUTION.screen({
    "id": "a2_unit_prism_substitution_control",
    "cells": [{"q": 0, "r": 0, "k": 0, "kind": "u"}],
}, 2, 10000)
assert substitution_unit["substitution_classification"] == "scalar_substitution_rule"
assert substitution_unit["substitution"]["replay"]["verified"] is True
assert substitution_unit["substitution"]["replay"]["patch_copies"] == 8

anisotropic_unit = SUBSTITUTION.screen({
    "id": "a2_unit_prism_anisotropic_control",
    "cells": [{"q": 0, "r": 0, "k": 0, "kind": "u"}],
}, 2, 10000, 2, 0, 3)
assert anisotropic_unit["substitution_classification"] == "lattice_substitution_rule"
assert anisotropic_unit["substitution"]["copy_count"] == 12
assert anisotropic_unit["substitution"]["replay"]["verified"] is True

try:
    SUBSTITUTION.screen({
        "id": "a2_noncellular_control",
        "cells": [{"q": 0, "r": 0, "k": 0, "kind": "u"}],
    }, 2, 10000, 1, 1, 2)
    raise AssertionError("non-cellular Eisenstein multiplier must be rejected")
except ValueError as error:
    assert "rotates cell edges off" in str(error)

substitution_records = []
for scale in (2, 3, 4, 5, 6):
    records = [
        json.loads(line)
        for line in (
            ROOT / "data" / f"a2-layered-size7-substitution-scale{scale}-focused.ndjson"
        ).read_text().splitlines()
        if line.strip()
    ]
    assert len(records) == 8
    assert {record["id"] for record in records} == set(expected_extended_clauses)
    assert all(record["substitution_classification"] == "no_scalar_substitution_at_scale" for record in records)
    assert all(record["substitution"]["certified"] is True for record in records)
    assert all(
        (record["substitution"]["local_obstruction_replay"] or
         record["substitution"]["exact_unsat_replay"])["verified"] is True
        for record in records
    )
    substitution_records.extend(records)

anisotropic_records = [
    json.loads(line)
    for line in (
        ROOT / "data" / "a2-layered-size7-substitution-anisotropic-s2to8-focused.ndjson"
    ).read_text().splitlines()
    if line.strip()
]
assert len(anisotropic_records) == 336
assert {record["id"] for record in anisotropic_records} == set(expected_extended_clauses)
assert len({
    (
        record["substitution"]["eisenstein_multiplier"]["a"],
        record["substitution"]["vertical_scale"],
    )
    for record in anisotropic_records
}) == 42
assert all(
    record["substitution_classification"] == "no_lattice_substitution_for_inflation"
    for record in anisotropic_records
)

cluster_unit = {
    "id": "a2_unit_prism_cluster_substitution_control",
    "cells": [{"q": 0, "r": 0, "k": 0, "kind": "u"}],
}
for scale in (2, 3):
    screened = CLUSTER_SUBSTITUTION.screen_candidate(cluster_unit, 10000, scale)
    assert screened["classification"] == "two_copy_metatile_substitution_system"
    single = screened["two_copy_metatile_screen"]
    mixed = screened["mixed_two_copy_metatile_screen"]
    assert single["symmetry_distinct_metatiles"] == 2
    assert single["positive_metatile_indices"] == [0, 1]
    assert all(
        result["base_decomposition"]["replay"]["verified"] is True
        for result in single["results"]
    )
    assert mixed["classification"] == "mixed_two_copy_metatile_substitution_system"
    assert mixed["certified"] is True
    assert mixed["closed_alphabet"] == [0]

for scale in (2, 3):
    three_cluster_unit = THREE_CLUSTER_SUBSTITUTION.screen_candidate(
        cluster_unit, 10000, progress_every=0, scale=scale
    )
    three_unit_screen = three_cluster_unit["three_copy_metatile_screen"]
    assert three_cluster_unit["classification"] == "three_copy_metatile_substitution_system"
    assert three_unit_screen["scale"] == scale
    assert three_unit_screen["symmetry_distinct_metatiles"] == 4
    assert three_unit_screen["raw_three_copy_extensions"] == 48
    assert three_unit_screen["canonical_sha256"] == (
        "c26bcfa2c65e5907b2ea04a21450562bbe871eda8d19f885e2942123e33dfb22"
    )
    assert three_unit_screen["closed_alphabet"] == [0, 1, 2, 3]
    assert three_unit_screen["parent_counts"] == {
        "local_obstruction": 0,
        "exact_unsat": 0,
        "mixed_metatile_rule": 4,
        "unresolved": 0,
    }
    assert all(
        parent["replay"]["verified"] is True
        and all("orientation_index" in child and "translation" in child for child in parent["rule"])
        for parent in three_unit_screen["parent_results"]
    )
    if scale == 3:
        checkpoint_seed = json.loads(json.dumps(three_cluster_unit))
        checkpoint_seed["classification"] = "partial"
        checkpoint_seed["three_copy_metatile_screen"]["certified"] = False
        checkpoint_seed["three_copy_metatile_screen"]["parent_results"] = (
            checkpoint_seed["three_copy_metatile_screen"]["parent_results"][:2]
        )
        resumed = THREE_CLUSTER_SUBSTITUTION.screen_candidate(
            cluster_unit, 10000, progress_every=0, scale=3,
            seed_report=checkpoint_seed,
        )
        assert resumed["classification"] == "three_copy_metatile_substitution_system"
        assert resumed["three_copy_metatile_screen"]["parent_counts"] == (
            three_unit_screen["parent_counts"]
        )

# The face index is an optimization only: on a scale-three control its graph
# must be exactly the graph obtained by checking every placement pair.
unit_metatile = THREE_CLUSTER_SUBSTITUTION.enumerate_three_copy_metatiles(cluster_unit)["metatiles"][0]
unit_target = SUBSTITUTION.scaled_cells(unit_metatile["cells"], 3)
unit_graph = THREE_CLUSTER_SUBSTITUTION.placement_graph(
    unit_target, SUBSTITUTION.oriented_cells(cluster_unit["cells"])
)
brute_adjacency = [set() for _ in unit_graph["placements"]]
brute_faces = []
for cells in unit_graph["cell_sets"]:
    faces = set()
    for q, r, k, kind in cells:
        faces.update(THREE_CLUSTER_SUBSTITUTION.TWO.cell_faces({
            "q": q, "r": r, "k": k, "kind": kind,
        }))
    brute_faces.append(faces)
for left in range(len(unit_graph["placements"])):
    for right in range(left + 1, len(unit_graph["placements"])):
        if (
            unit_graph["cell_sets"][left].isdisjoint(unit_graph["cell_sets"][right])
            and brute_faces[left].intersection(brute_faces[right])
        ):
            brute_adjacency[left].add(right)
            brute_adjacency[right].add(left)
assert unit_graph["adjacency"] == brute_adjacency

algorithm_x_target = {
    (0, 0, 0, "u"), (1, 0, 0, "u"), (2, 0, 0, "u"),
}
algorithm_x_placements = [
    {"cells": {(0, 0, 0, "u"), (1, 0, 0, "u")}},
    {"cells": {(1, 0, 0, "u"), (2, 0, 0, "u")}},
]
algorithm_x_negative = THREE_CLUSTER_SUBSTITUTION.replay_unsat_with_independent_algorithm_x(
    algorithm_x_target, algorithm_x_placements, 10000
)
assert algorithm_x_negative["verified"] is True
assert algorithm_x_negative["result"] == "unsat"

expected_metatile_types = {
    "a2lp_7_00128": 95,
    "a2lp_7_00211": 93,
    "a2lp_7_00232": 85,
    "a2lp_7_00235": 89,
    "a2lp_7_00694": 73,
    "a2lp_7_00755": 73,
    "a2lp_7_00777": 73,
    "a2lp_7_00809": 71,
}
expected_metatile_hashes = {
    "a2lp_7_00128": "ca3343e4d56917e316f32f5a4b7149a1c4d14b6e856c4e5d7afb5c65fe28d0bd",
    "a2lp_7_00211": "6088fe594f74921f54c5f56eb0a6e9dadde823bc3a7c8c4af4375d57f353bb27",
    "a2lp_7_00232": "4a0ca098cda08646936f3d495638ddfdecb8e4a971a81f4adca16cfb21bbaa11",
    "a2lp_7_00235": "287bf2caf08824dfd7e8502a5ff2e408db7af09fec2a7ec5dca0cbde6c742732",
    "a2lp_7_00694": "7228dc0ee98f8bc4b7252cf024e38fa42ce4f0ab6755acabebf3c9a1b227cc5e",
    "a2lp_7_00755": "972465932c166eae79530bfede40b2c69a84e73cd7d6ec724123057cab44fd15",
    "a2lp_7_00777": "73a166af61d4e4b50639241c4eb38f8226890f8a704bb850f0b09500f3fba02a",
    "a2lp_7_00809": "e1090be203af7682a2c9d827383e8c223d6444db9cad2eb2c7231c22e3eeffcf",
}
expected_mixed_exact_unsat = {
    2: {"a2lp_7_00211": 11, "a2lp_7_00235": 2},
    3: {"a2lp_7_00211": 12, "a2lp_7_00235": 13},
}
cluster_records = []
for scale in (2, 3):
    records = [
        json.loads(line)
        for line in (
            ROOT / "data" /
            f"a2-layered-size7-two-cluster-substitution-scalar{scale}-focused.ndjson"
        ).read_text().splitlines()
        if line.strip()
    ]
    assert len(records) == 8
    assert {record["id"] for record in records} == set(expected_metatile_types)
    assert all(
        record["classification"] == f"no_two_copy_metatile_scalar{scale}_substitution"
        for record in records
    )
    assert {
        record["id"]: record["two_copy_metatile_screen"]["symmetry_distinct_metatiles"]
        for record in records
    } == expected_metatile_types
    assert {
        record["id"]: record["two_copy_metatile_screen"]["canonical_sha256"]
        for record in records
    } == expected_metatile_hashes
    for record in records:
        single = record["two_copy_metatile_screen"]
        mixed = record["mixed_two_copy_metatile_screen"]
        assert single["certified"] is True
        assert not single["positive_metatile_indices"]
        assert not single["unknown_metatile_indices"]
        assert all(
            result["base_decomposition"]["replay"]["verified"] is True
            for result in single["results"]
        )
        assert all(
            result["substitution"]["certified"] is True
            for result in single["results"]
        )
        assert mixed["classification"] == f"no_mixed_two_copy_metatile_scalar{scale}_substitution"
        assert mixed["certified"] is True
        assert mixed["closed_alphabet"] is None
        expected_exact = expected_mixed_exact_unsat[scale].get(record["id"], 0)
        assert mixed["parent_counts"]["exact_unsat"] == expected_exact
        assert mixed["parent_counts"]["local_obstruction"] + expected_exact == expected_metatile_types[record["id"]]
        for parent in mixed["parent_results"]:
            replay = parent.get("local_obstruction_replay") or parent.get("exact_unsat_replay")
            assert replay["verified"] is True
    cluster_records.extend(records)

expected_three_metatile_types = {
    "a2lp_7_00128": 10115,
    "a2lp_7_00211": 10446,
    "a2lp_7_00232": 8878,
    "a2lp_7_00235": 9583,
    "a2lp_7_00694": 6329,
    "a2lp_7_00755": 6406,
    "a2lp_7_00777": 6329,
    "a2lp_7_00809": 5923,
}
expected_three_metatile_hashes = {
    "a2lp_7_00128": "3efbe89c569f6c61049e48db4ba6c6d87bfac4c5cb22af2675661f16ddbbc792",
    "a2lp_7_00211": "91537237d3568e90790297c84260834f5e468b9205b371e751e23bd31e35a215",
    "a2lp_7_00232": "a8d45104aba8267a85d2c7111a1260003967c0e1545640a999ca59f3d499e8e5",
    "a2lp_7_00235": "ad69470b9a8777e4a9140f9e879d5fdfb938b2ee49ba522c304585c41bdd5c12",
    "a2lp_7_00694": "4f28f466f35d94638f7123506c3af712cc3b06e3ee8ddc1a16e9197563e693ed",
    "a2lp_7_00755": "b38b9b77cf1305216b50329ef61dcd51008ec94ebc8c210872da8a970c141e2a",
    "a2lp_7_00777": "45affe0606eaa34bd8c462213087626e47f4cf6f9f4b4a9b876299ea76e23b30",
    "a2lp_7_00809": "f4ef25d35f2283cc301e4d115a2d6539181835eb4cc76784ef2a9e3fad863870",
}
expected_three_exact_unsat = {
    2: {
        "a2lp_7_00128": 0, "a2lp_7_00211": 246,
        "a2lp_7_00232": 0, "a2lp_7_00235": 6,
        "a2lp_7_00694": 0, "a2lp_7_00755": 0,
        "a2lp_7_00777": 0, "a2lp_7_00809": 0,
    },
    3: {
        "a2lp_7_00128": 0, "a2lp_7_00211": 488,
        "a2lp_7_00232": 0, "a2lp_7_00235": 484,
        "a2lp_7_00694": 0, "a2lp_7_00755": 0,
        "a2lp_7_00777": 0, "a2lp_7_00809": 0,
    },
}
three_cluster_records = {2: [], 3: []}
for scale in (2, 3):
    for candidate_id in expected_three_metatile_types:
        record = json.loads((
            ROOT / "data" /
            f"a2-layered-size7-three-cluster-substitution-scalar{scale}-{candidate_id}.ndjson"
        ).read_text())
        screen = record["three_copy_metatile_screen"]
        exact_unsat = expected_three_exact_unsat[scale][candidate_id]
        assert record["classification"] == f"no_three_copy_metatile_scalar{scale}_substitution"
        assert screen["certified"] is True
        assert screen.get("scale", 2) == scale
        assert screen["symmetry_distinct_metatiles"] == expected_three_metatile_types[candidate_id]
        assert screen["canonical_sha256"] == expected_three_metatile_hashes[candidate_id]
        assert screen["parent_counts"] == {
            "local_obstruction": expected_three_metatile_types[candidate_id] - exact_unsat,
            "exact_unsat": exact_unsat,
            "mixed_metatile_rule": 0,
            "unresolved": 0,
        }
        assert len(screen["parent_results"]) == expected_three_metatile_types[candidate_id]
        assert all(
            (
                parent.get("local_obstruction_replay")
                or parent.get("exact_unsat_replay")
            )["verified"] is True
            for parent in screen["parent_results"]
        )
        three_cluster_records[scale].append(record)

resolved_three = next(
    record for record in three_cluster_records[2] if record["id"] == "a2lp_7_00211"
)["three_copy_metatile_screen"]
assert resolved_three["residual_resolutions"][0]["parent_index"] == 1168
assert resolved_three["residual_resolutions"][0]["prior_replay"]["result"] == "unknown"
assert resolved_three["residual_resolutions"][0]["resolution"]["verified"] is True
assert all(record["substitution"]["certified"] is True for record in anisotropic_records)
assert all(
    (record["substitution"]["local_obstruction_replay"] or
     record["substitution"]["exact_unsat_replay"])["verified"] is True
    for record in anisotropic_records
)

print("A2 layered corona regression passed", {
    "root_coronas_replayed": len(root_records),
    "focused_candidates": len(focused),
    "distinct_first_coronas_rejected_each": 8,
    "deep_candidate_rejected_first_coronas": 64,
    "direct_positive_control": unit["corona2_direct"]["replay"]["patch_copies"],
    "sound_gcts_clauses_by_candidate": expected_strengthened_clauses,
    "smallest_certified_cores": expected_minimized_core_sizes,
    "larger_periodic_partial_candidates": len(larger_periodic),
    "scalar_substitution_negatives": len(substitution_records),
    "anisotropic_substitution_negatives": len(anisotropic_records),
    "two_copy_metatile_parent_scale_cases": sum(expected_metatile_types.values()) * 2,
    "three_copy_metatile_parent_scale_cases": sum(expected_three_metatile_types.values()) * 2,
})
