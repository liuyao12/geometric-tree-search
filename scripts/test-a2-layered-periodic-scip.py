#!/usr/bin/env python3
import gzip
import hashlib
import importlib.util
import json
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_periodic_scip", ROOT / "scripts" / "screen-a2-layered-periodic-scip.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
assert '"set presolving emphasis off"' in SPEC.loader.get_source("a2_periodic_scip")
MERGE_SPEC = importlib.util.spec_from_file_location(
    "a2_periodic_scip_merge", ROOT / "scripts" / "merge-a2-layered-periodic-scip.py"
)
MERGE_MODULE = importlib.util.module_from_spec(MERGE_SPEC)
MERGE_SPEC.loader.exec_module(MERGE_MODULE)

orbits = MODULE.hnf_orbits(28)
assert len(orbits) == 384
assert sum(len(orbit["member_indices"]) for orbit in orbits) == 1995
assert Counter(len(orbit["member_indices"]) for orbit in orbits) == {
    1: 2, 2: 2, 3: 97, 6: 283,
}
assert sorted(
    index for orbit in orbits for index in orbit["member_indices"]
) == list(range(1995))
for orbit in orbits:
    assert orbit["representative_index"] == min(orbit["member_indices"])

record = next(
    json.loads(line)
    for line in (
        ROOT / "data" / "a2-layered-size7-periodic-z3-through4.ndjson"
    ).read_text().splitlines()
    if json.loads(line)["id"] == "a2lp_7_00128"
)
placements, orientation_count = MODULE.quotient_placements(
    record, tuple(orbits[0]["representative_hnf"]), 28
)
assert orientation_count == 6
assert len(placements) == 168
rooted = MODULE.rooted_multicover(placements)
assert rooted["divisor"] == 4
assert rooted["full_weight"] == 12
assert len(rooted["capacity"]) == 28
assert len(rooted["eligible_indices"]) == 167
with tempfile.TemporaryDirectory() as directory:
    mps = Path(directory) / "control.mps"
    MODULE.write_mps(mps, rooted, 7)
    text = mps.read_text()
    assert text.startswith("NAME A2PERIODIC\nROWS\n N OBJ\n")
    assert " E COUNT\n" in text
    assert text.count(" BV BND X") == 167
    assert text.endswith("ENDATA\n")

report = json.loads((
    ROOT / "data" / "a2-layered-size7-periodic-exact8-a2lp_7_00128-orbit0.ndjson"
).read_text())
screen = report["periodic_exact_scip"]
assert report["classification"] == "unresolved"
assert screen["copies"] == 8
assert screen["determinant"] == 28
assert screen["certified_no_periodic_quotient"] is False
assert screen["orbit_range"] == [0, 1]
assert screen["orbit_representatives_visited"] == 1
assert screen["hnf_covered"] == 3
assert screen["hnf_total"] == 1995
assert screen["hnf_orbit_total"] == 384
assert screen["solver_unknown"] == 0
receipt = screen["proof_receipts"][0]
assert receipt["verified"] is True
assert receipt["kind"] == "completed_vipr_rational_infeasibility"
assert receipt["hnf_index"] == 0
assert receipt["orbit_size"] == 3
assert receipt["derivations"] == 48370

mps_path = ROOT / receipt["mps_path"]
compressed_path = ROOT / receipt["compressed_vipr_path"]
assert hashlib.sha256(mps_path.read_bytes()).hexdigest() == receipt["mps_sha256"]
assert hashlib.sha256(compressed_path.read_bytes()).hexdigest() == receipt["compressed_vipr_sha256"]
digest = hashlib.sha256()
uncompressed_bytes = 0
with gzip.open(compressed_path, "rb") as stream:
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
        uncompressed_bytes += len(block)
assert digest.hexdigest() == receipt["vipr_sha256"]
assert uncompressed_bytes == receipt["vipr_bytes"]

with tempfile.TemporaryDirectory() as checkpoint_directory:
    checkpoint = MODULE.orbit_checkpoint_report(
        record,
        {
            "result": "unsat",
            "proof": {key: value for key, value in receipt.items() if key not in {
                "hnf_index", "hnf", "orbit_size", "eligible_placements",
                "mps_path", "compressed_vipr_path", "compressed_vipr_sha256",
            }},
            "hnf_index": receipt["hnf_index"],
            "hnf": receipt["hnf"],
            "orbit_member_indices": orbits[0]["member_indices"],
            "eligible_placements": receipt["eligible_placements"],
        },
        8, 28, 0, 1995, 384, 123, screen["tools"],
    )
    checkpoint_path = MODULE.write_orbit_checkpoint(
        Path(checkpoint_directory), checkpoint, 0
    )
    reloaded_checkpoint = json.loads(checkpoint_path.read_text())
    assert reloaded_checkpoint["periodic_exact_scip"]["orbit_range"] == [0, 1]
    assert reloaded_checkpoint["periodic_exact_scip"]["solver_unknown"] == 0
    assert len(reloaded_checkpoint["periodic_exact_scip"]["proof_receipts"]) == 1
    assert not checkpoint_path.with_suffix(checkpoint_path.suffix + ".tmp").exists()

merged = MERGE_MODULE.merge([
    ROOT / "data" / "a2-layered-size7-periodic-exact8-a2lp_7_00128-orbit0.ndjson",
    ROOT / "data" / "a2-layered-size7-periodic-exact8-a2lp_7_00128-orbits1to3.ndjson",
])
merged_screen = merged["periodic_exact_scip"]
assert merged_screen["orbit_range"] == [0, 4]
assert merged_screen["orbit_representatives_visited"] == 4
assert merged_screen["hnf_covered"] == 21
assert len(merged_screen["proof_receipts"]) == 4
assert len(merged_screen["range_receipts"]) == 2
assert merged_screen["certified_no_periodic_quotient"] is False

longer_merged = json.loads((
    ROOT / "data" / "a2-layered-size7-periodic-exact8-a2lp_7_00128-orbits0to11.ndjson"
).read_text())
longer_screen = longer_merged["periodic_exact_scip"]
assert longer_screen["orbit_range"] == [0, 12]
assert longer_screen["orbit_representatives_visited"] == 12
assert longer_screen["hnf_covered"] == 63
assert longer_screen["solver_unknown"] == 0
assert len(longer_screen["proof_receipts"]) == 12
assert longer_screen["certified_no_periodic_quotient"] is False

periodic = json.loads((
    ROOT / "data" / "a2-layered-size7-periodic-exact8-a2lp_7_00694-witness.ndjson"
).read_text())
periodic_screen = periodic["periodic_exact_scip"]
assert periodic["classification"] == "periodic"
assert periodic_screen["replay"]["verified"] is True
assert periodic_screen["certificate"]["copies"] == 8
assert periodic_screen["certificate"]["determinant"] == 28
assert periodic_screen["certificate"]["period_vectors"] == [
    [2, 0, 0], [0, 2, 0], [0, 0, 7]
]

print("A2 exact SCIP/VIPR regression passed", {
    "determinant_28_hnfs": 1995,
    "point_group_orbits": len(orbits),
    "first_orbit_hnfs_covered": screen["hnf_covered"],
    "verified_derivations": receipt["derivations"],
    "merged_orbits": merged_screen["orbit_representatives_visited"],
    "periodic_witness": periodic["id"],
})
