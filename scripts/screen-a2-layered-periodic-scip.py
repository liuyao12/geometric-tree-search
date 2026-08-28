#!/usr/bin/env python3
"""Proof-producing periodic quotient screen for the A2 layered candidates.

SCIP is run in its numerically exact mode and emits a VIPR proof for every
negative quotient.  ``viprcomp`` completes safe LP derivations and the
independent ``viprchk`` program verifies the resulting certificate in rational
arithmetic.  A negative is recorded only after that final check succeeds.

The determinant-D HNFs are quotiented by the proper A2 point group.  Because
all proper tile orientations are already available to the quotient model, HNF
sublattices in the same point-group orbit define isomorphic feasibility
problems and need only one proof.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_periodic_exact", ROOT / "scripts" / "screen-a2-layered-periodic-z3.py"
)
GEOMETRY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEOMETRY)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discard_unverified_proof(path: Path) -> dict:
    """Remove SCIP proof artifacts that cannot certify the reported result."""
    discarded = {}
    for label, artifact in (
        ("vipr", path),
        ("vipr_original_problem", path.with_name(path.name + "_ori")),
    ):
        if artifact.exists():
            discarded[f"discarded_{label}_bytes"] = artifact.stat().st_size
            artifact.unlink()
    return discarded


def retained_artifact_receipt(mps: Path, proof: Path, completed_proof: Path) -> dict:
    """Compress a verified proof deterministically and retain replayable paths."""
    compressed = completed_proof.with_suffix(completed_proof.suffix + ".gz")
    with completed_proof.open("rb") as source, compressed.open("wb") as raw_target:
        with gzip.GzipFile(fileobj=raw_target, mode="wb", filename="", mtime=0) as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)

    def display_path(path: Path) -> str:
        resolved = path.resolve()
        try:
            return str(resolved.relative_to(ROOT.resolve()))
        except ValueError:
            return str(resolved)

    receipt = {
        "mps_path": display_path(mps),
        "compressed_vipr_path": display_path(compressed),
        "compressed_vipr_sha256": sha256(compressed),
    }
    proof.unlink(missing_ok=True)
    proof.with_name(proof.name + "_ori").unlink(missing_ok=True)
    completed_proof.unlink()
    return receipt


def executable_identity(path: Path) -> dict:
    return {
        "path": str(path.resolve()),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def transformed_hnf(hnf, isometry):
    a, b, c, d, e, f = hnf
    basis = Matrix(((a, b, c), (0, d, e), (0, 0, f)))
    sign, permutation = isometry
    transform = Matrix(3, 3, lambda row, column: sign if permutation[row] == column else 0)
    result = hermite_normal_form(transform * basis)
    return (
        int(result[0, 0]), int(result[0, 1]), int(result[0, 2]),
        int(result[1, 1]), int(result[1, 2]), int(result[2, 2]),
    )


def hnf_orbits(determinant: int) -> list[dict]:
    hnfs = GEOMETRY.hnf_candidates(determinant)
    index = {hnf: position for position, hnf in enumerate(hnfs)}
    parent = list(range(len(hnfs)))

    def find(position):
        while parent[position] != position:
            parent[position] = parent[parent[position]]
            position = parent[position]
        return position

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    for position, hnf in enumerate(hnfs):
        for isometry in GEOMETRY.A2_LAYER_ISOMETRIES:
            transformed = transformed_hnf(hnf, isometry)
            if transformed not in index:
                raise RuntimeError(f"transformed HNF missing: {hnf} -> {transformed}")
            union(position, index[transformed])
    classes = {}
    for position in range(len(hnfs)):
        classes.setdefault(find(position), []).append(position)
    return [
        {
            "representative_index": min(members),
            "representative_hnf": hnfs[min(members)],
            "member_indices": sorted(members),
        }
        for members in sorted(classes.values(), key=min)
    ]


def quotient_placements(record: dict, hnf, determinant: int) -> tuple[list[dict], int]:
    occupancy = GEOMETRY.record_occupancy(record)
    tile_orientations = GEOMETRY.orientations(occupancy)
    placements = []
    for orientation_index, orientation in enumerate(tile_orientations):
        for x in range(hnf[0]):
            for y in range(hnf[3]):
                for z in range(hnf[5]):
                    vector = [0] * determinant
                    for point, weight in orientation["occupancy"].items():
                        translated = (point[0] + x, point[1] + y, point[2] + z)
                        vector[GEOMETRY.quotient_index(translated, hnf)] += weight
                    placements.append({
                        "orientation_index": orientation_index,
                        "translation": (x, y, z),
                        "weights": vector,
                    })
    return placements, len(tile_orientations)


def rooted_multicover(placements: list[dict]) -> dict:
    divisor = math.gcd(48, *(
        weight for placement in placements for weight in placement["weights"]
    ))
    full = 48 // divisor
    vectors = [tuple(weight // divisor for weight in placement["weights"]) for placement in placements]
    capacity = tuple(full - weight for weight in vectors[0])
    eligible_indices = [
        index for index, vector in enumerate(vectors[1:], 1)
        if all(weight <= available for weight, available in zip(vector, capacity))
    ]
    return {
        "divisor": divisor,
        "full_weight": full,
        "capacity": capacity,
        "eligible_indices": eligible_indices,
        "eligible_vectors": [vectors[index] for index in eligible_indices],
    }


def write_mps(path: Path, model: dict, remaining_copies: int) -> None:
    vectors = model["eligible_vectors"]
    with path.open("w") as stream:
        stream.write("NAME A2PERIODIC\nROWS\n N OBJ\n")
        for residue in range(len(model["capacity"])):
            stream.write(f" E R{residue}\n")
        stream.write(" E COUNT\nCOLUMNS\n MARK0000 'MARKER' 'INTORG'\n")
        for offset, vector in enumerate(vectors, 1):
            variable = f"X{offset}"
            for residue, weight in enumerate(vector):
                if weight:
                    stream.write(f" {variable} R{residue} {weight}\n")
            stream.write(f" {variable} COUNT 1\n")
        stream.write(" MARK0001 'MARKER' 'INTEND'\nRHS\n")
        for residue, capacity in enumerate(model["capacity"]):
            stream.write(f" RHS1 R{residue} {capacity}\n")
        stream.write(f" RHS1 COUNT {remaining_copies}\nBOUNDS\n")
        for offset in range(1, len(vectors) + 1):
            stream.write(f" BV BND X{offset}\n")
        stream.write("ENDATA\n")


def run(command, timeout, cwd=None) -> tuple[subprocess.CompletedProcess, float]:
    started = time.monotonic()
    completed = subprocess.run(
        [str(value) for value in command], cwd=cwd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
    )
    return completed, time.monotonic() - started


def selected_offsets(solution_text: str) -> list[int]:
    return [
        int(match.group(1)) - 1
        for line in solution_text.splitlines()
        if (match := re.match(r"^X(\d+)\s+1(?:\.0+)?(?:\s|$)", line.strip()))
    ]


def solve_quotient(record, hnf_record, copies, tools, timeout_seconds, proof_directory=None):
    hnf = tuple(hnf_record["representative_hnf"])
    determinant = math.prod((hnf[0], hnf[3], hnf[5]))
    placements, orientation_count = quotient_placements(record, hnf, determinant)
    model = rooted_multicover(placements)
    if proof_directory:
        work = Path(proof_directory) / (
            f"{record['id']}-h{hnf_record['representative_index']:04d}"
        )
        work.mkdir(parents=True, exist_ok=True)
        temporary = None
    else:
        temporary = tempfile.TemporaryDirectory(prefix="a2-exact-scip-")
        work = Path(temporary.name)
    mps = work / "instance.mps"
    proof = work / "certificate.vipr"
    solution = work / "solution.sol"
    write_mps(mps, model, copies - 1)
    scip_command = [
        tools["scip"], "-q",
        "-c", "set exact enable TRUE",
        "-c", "set separating emphasis off",
        "-c", "set presolving emphasis off",
        "-c", f"set certificate filename {proof}",
        "-c", f"set limits time {timeout_seconds}",
        "-c", f"read {mps}",
        "-c", "optimize",
        "-c", f"write solution {solution}",
        "-c", "quit",
    ]
    scip, scip_seconds = run(scip_command, timeout_seconds + 120)
    if scip.returncode != 0 or not solution.exists():
        raise RuntimeError(f"exact SCIP failed ({scip.returncode}): {scip.stdout[-2000:]}")
    solution_text = solution.read_text()
    offsets = selected_offsets(solution_text)
    if offsets:
        chosen_indices = [0] + [model["eligible_indices"][offset] for offset in offsets]
        certificate = {
            "kind": "weighted_periodic_hnf_quotient",
            "certified": True,
            "can_tile": True,
            "model": "a2_layered_lattice_function",
            "copies": copies,
            "determinant": determinant,
            "period_vectors": [list(vector) for vector in GEOMETRY.period_vectors(hnf)],
            "placements": [
                {
                    "orientation_index": placements[index]["orientation_index"],
                    "translation": list(placements[index]["translation"]),
                }
                for index in chosen_indices
            ],
            "hnf_index": hnf_record["representative_index"],
        }
        orientations = GEOMETRY.orientations(GEOMETRY.record_occupancy(record))
        replay = GEOMETRY.replay_certificate(orientations, certificate)
        if not replay["verified"]:
            raise RuntimeError(f"SCIP witness replay failed: {replay}")
        result = {
            "result": "sat", "certificate": certificate, "replay": replay,
            "scip_seconds": scip_seconds,
        }
    elif "solution status: infeasible" in solution_text:
        if not proof.exists():
            result = {
                "result": "unknown",
                "scip_seconds": scip_seconds,
                "unknown_reason": "infeasible_status_without_vipr_proof",
            }
            result.update({
                "hnf_index": hnf_record["representative_index"],
                "hnf": list(hnf),
                "orbit_member_indices": hnf_record["member_indices"],
                "orientation_count": orientation_count,
                "eligible_placements": len(model["eligible_indices"]),
            })
            if temporary is not None:
                temporary.cleanup()
            return result
        completion, completion_seconds = run(
            [tools["viprcomp"], "--threads=8", "--verbosity=0", proof.name],
            timeout_seconds + 300, cwd=work,
        )
        completed_proof = work / "certificate_complete.vipr"
        if completion.returncode != 0 or not completed_proof.exists() or (
            "Completion of File successful!" not in completion.stdout
        ):
            raise RuntimeError(f"VIPR completion failed: {completion.stdout[-2000:]}")
        verification, verification_seconds = run(
            [tools["viprchk"], completed_proof], timeout_seconds + 300,
        )
        if verification.returncode != 0 or (
            "Successfully verified infeasibility." not in verification.stdout
        ):
            raise RuntimeError(f"VIPR verification failed: {verification.stdout[-2000:]}")
        derivations = next((
            int(match.group(1))
            for line in completed_proof.open(errors="replace")
            if (match := re.match(r"DER (\d+)", line))
        ), None)
        result = {
            "result": "unsat",
            "proof": {
                "kind": "completed_vipr_rational_infeasibility",
                "verified": True,
                "mps_sha256": sha256(mps),
                "vipr_sha256": sha256(completed_proof),
                "vipr_bytes": completed_proof.stat().st_size,
                "derivations": derivations,
                "scip_seconds": scip_seconds,
                "completion_seconds": completion_seconds,
                "verification_seconds": verification_seconds,
            },
        }
        if proof_directory:
            result["proof"].update(
                retained_artifact_receipt(mps, proof, completed_proof)
            )
    else:
        result = {"result": "unknown", "scip_seconds": scip_seconds}
    if result["result"] != "unsat":
        result.update(discard_unverified_proof(proof))
    result.update({
        "hnf_index": hnf_record["representative_index"],
        "hnf": list(hnf),
        "orbit_member_indices": hnf_record["member_indices"],
        "orientation_count": orientation_count,
        "eligible_placements": len(model["eligible_indices"]),
    })
    if temporary is not None:
        temporary.cleanup()
    return result


def orbit_checkpoint_report(record, solved, copies, determinant, orbit_index,
                            hnf_total, orbit_total, milliseconds, tools):
    covered = len(solved["orbit_member_indices"])
    if solved["result"] == "sat":
        return {
            **record, "classification": "periodic",
            "periodic_exact_scip": {
                "certificate": solved["certificate"],
                "replay": solved["replay"],
                "orbit_range": [orbit_index, orbit_index + 1],
                "orbit_representatives_visited": 1,
                "hnf_covered": covered,
                "hnf_total": hnf_total,
                "hnf_orbit_total": orbit_total,
                "proof_receipts": [],
                "milliseconds": milliseconds,
                "tools": tools,
            },
        }
    receipt = []
    if solved["result"] == "unsat":
        receipt.append({
            **solved["proof"],
            "hnf_index": solved["hnf_index"],
            "hnf": solved["hnf"],
            "orbit_size": covered,
            "eligible_placements": solved["eligible_placements"],
        })
    return {
        **record, "classification": "unresolved",
        "periodic_exact_scip": {
            "copies": copies,
            "determinant": determinant,
            "certified_no_periodic_quotient": False,
            "orbit_range": [orbit_index, orbit_index + 1],
            "orbit_representatives_visited": 1,
            "hnf_covered": covered,
            "hnf_total": hnf_total,
            "hnf_orbit_total": orbit_total,
            "solver_unknown": int(solved["result"] == "unknown"),
            "proof_receipts": receipt,
            "milliseconds": milliseconds,
            "tools": tools,
        },
    }


def write_orbit_checkpoint(directory: Path, report: dict, orbit_index: int):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{report['id']}-orbit{orbit_index:04d}.ndjson"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, separators=(",", ":")) + "\n")
    temporary.replace(path)
    return path


def screen_candidate(record, args, tools, identities):
    occupancy = GEOMETRY.record_occupancy(record)
    numerator = sum(occupancy.values()) * args.copies
    if numerator % 48:
        raise ValueError("copy count does not give an integral quotient determinant")
    determinant = numerator // 48
    all_orbits = hnf_orbits(determinant)
    start = max(0, args.orbit_start)
    stop = min(len(all_orbits), args.orbit_stop or len(all_orbits))
    if start >= stop:
        raise ValueError("empty HNF-orbit range")
    receipts = []
    started = time.monotonic()
    covered = 0
    unknown = 0
    for local_index, orbit in enumerate(all_orbits[start:stop], start + 1):
        orbit_started = time.monotonic()
        solved = solve_quotient(
            record, orbit, args.copies, tools, args.hnf_timeout_seconds,
            args.proof_directory or None,
        )
        checkpoint = orbit_checkpoint_report(
            record, solved, args.copies, determinant, local_index - 1,
            len(GEOMETRY.hnf_candidates(determinant)), len(all_orbits),
            round((time.monotonic() - orbit_started) * 1000), identities,
        )
        if args.checkpoint_directory:
            write_orbit_checkpoint(
                Path(args.checkpoint_directory), checkpoint, local_index - 1
            )
        covered += len(orbit["member_indices"])
        if solved["result"] == "sat":
            return {
                **record, "classification": "periodic",
                "periodic_exact_scip": {
                    "certificate": solved["certificate"],
                    "replay": solved["replay"],
                    "orbit_representatives_visited": local_index - start,
                    "hnf_covered": covered,
                    "hnf_total": len(GEOMETRY.hnf_candidates(determinant)),
                    "hnf_orbit_total": len(all_orbits),
                    "proof_receipts": receipts,
                },
            }
        if solved["result"] == "unsat":
            receipts.append({
                **solved["proof"],
                "hnf_index": solved["hnf_index"],
                "hnf": solved["hnf"],
                "orbit_size": len(solved["orbit_member_indices"]),
                "eligible_placements": solved["eligible_placements"],
            })
        else:
            unknown += 1
        if args.progress_every and local_index % args.progress_every == 0:
            print(
                f"{record['id']} orbit={local_index}/{len(all_orbits)} "
                f"covered={covered} verified={len(receipts)} unknown={unknown} "
                f"elapsed_s={time.monotonic() - started:.1f}", flush=True,
            )
    complete = start == 0 and stop == len(all_orbits) and unknown == 0
    return {
        **record, "classification": "unresolved",
        "periodic_exact_scip": {
            "copies": args.copies,
            "determinant": determinant,
            "certified_no_periodic_quotient": complete,
            "orbit_range": [start, stop],
            "orbit_representatives_visited": stop - start,
            "hnf_covered": covered,
            "hnf_total": len(GEOMETRY.hnf_candidates(determinant)),
            "hnf_orbit_total": len(all_orbits),
            "solver_unknown": unknown,
            "proof_receipts": receipts,
            "milliseconds": round((time.monotonic() - started) * 1000),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--copies", type=int, default=8)
    parser.add_argument("--scip", required=True)
    parser.add_argument("--viprcomp", required=True)
    parser.add_argument("--viprchk", required=True)
    parser.add_argument("--hnf-timeout-seconds", type=int, default=300)
    parser.add_argument("--orbit-start", type=int, default=0)
    parser.add_argument("--orbit-stop", type=int, default=0)
    parser.add_argument("--progress-every", type=int, default=1)
    parser.add_argument("--proof-directory", default="")
    parser.add_argument("--checkpoint-directory", default="")
    args = parser.parse_args()
    if args.copies < 1:
        parser.error("copies must be positive")
    tools = {
        name: Path(getattr(args, name)).resolve()
        for name in ("scip", "viprcomp", "viprchk")
    }
    for name, path in tools.items():
        if not path.is_file():
            parser.error(f"{name} executable not found: {path}")
    requested = {value for value in args.ids.split(",") if value}
    records = [
        json.loads(line) for line in Path(args.input).read_text().splitlines()
        if line.strip()
    ]
    if requested:
        records = [record for record in records if record["id"] in requested]
    identities = {name: executable_identity(path) for name, path in tools.items()}
    output = Path(args.output)
    output.write_text("")
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen_candidate(record, args, tools, identities)
            result["periodic_exact_scip"]["tools"] = identities
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {result['classification']}", flush=True)


if __name__ == "__main__":
    main()
