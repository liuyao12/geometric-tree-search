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

with tempfile.TemporaryDirectory() as directory:
    proof = Path(directory) / "certificate.vipr"
    original = Path(directory) / "certificate.vipr_ori"
    proof.write_bytes(b"incomplete")
    original.write_bytes(b"original")
    discarded = MODULE.discard_unverified_proof(proof)
    assert discarded == {
        "discarded_vipr_bytes": 10,
        "discarded_vipr_original_problem_bytes": 8,
    }
    assert not proof.exists()
    assert not original.exists()

with tempfile.TemporaryDirectory() as directory:
    directory = Path(directory)
    mps = directory / "instance.mps"
    proof = directory / "certificate.vipr"
    original = directory / "certificate.vipr_ori"
    completed = directory / "certificate_complete.vipr"
    mps.write_bytes(b"mps")
    proof.write_bytes(b"incomplete")
    original.write_bytes(b"original")
    completed.write_bytes(b"verified-proof")
    retained = MODULE.retained_artifact_receipt(mps, proof, completed)
    compressed = Path(retained["compressed_vipr_path"])
    assert compressed.is_absolute()
    with gzip.open(compressed, "rb") as stream:
        assert stream.read() == b"verified-proof"
    assert hashlib.sha256(compressed.read_bytes()).hexdigest() == retained[
        "compressed_vipr_sha256"
    ]
    assert not proof.exists()
    assert not original.exists()
    assert not completed.exists()

# The same proof backend also accepts the exact solid-angle occupancy receipts
# used by the non-polycube affine-A3 alcove catalogue; it must not assume the
# older triangular-prism ``cells`` representation.
sliced = next(
    json.loads(line)
    for line in (
        ROOT / "data" / "a2-sliced-alcove-size7-directed-periodic-exact6.ndjson"
    ).read_text().splitlines()
    if json.loads(line)["id"] == "a2sa_7_00170"
)
sliced_orbit = MODULE.hnf_orbits(14)[6]
sliced_placements, sliced_orientation_count = MODULE.quotient_placements(
    sliced, tuple(sliced_orbit["representative_hnf"]), 14
)
assert sliced_orientation_count == 6
assert len(sliced_placements) == 84
assert len(MODULE.rooted_multicover(sliced_placements)["eligible_indices"]) == 83

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

sliced_exact12 = json.loads((
    ROOT / "data" /
    "a2-sliced-alcove-size7-periodic-exact12-a2sa_7_00139-orbit0.ndjson"
).read_text())
sliced_screen = sliced_exact12["periodic_exact_scip"]
assert sliced_exact12["id"] == "a2sa_7_00139"
assert sliced_screen["copies"] == 12
assert sliced_screen["determinant"] == 14
assert sliced_screen["orbit_range"] == [0, 1]
assert sliced_screen["hnf_covered"] == 6
sliced_receipt = sliced_screen["proof_receipts"][0]
assert sliced_receipt["verified"] is True
assert sliced_receipt["derivations"] == 102361
assert hashlib.sha256((ROOT / sliced_receipt["mps_path"]).read_bytes()).hexdigest() == (
    sliced_receipt["mps_sha256"]
)
sliced_compressed = ROOT / sliced_receipt["compressed_vipr_path"]
assert hashlib.sha256(sliced_compressed.read_bytes()).hexdigest() == (
    sliced_receipt["compressed_vipr_sha256"]
)
sliced_digest = hashlib.sha256()
sliced_bytes = 0
with gzip.open(sliced_compressed, "rb") as stream:
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        sliced_digest.update(block)
        sliced_bytes += len(block)
assert sliced_digest.hexdigest() == sliced_receipt["vipr_sha256"]
assert sliced_bytes == sliced_receipt["vipr_bytes"]

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
