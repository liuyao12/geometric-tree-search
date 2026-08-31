#!/usr/bin/env python3
"""Regression for copy-count-specific bounded campaign summaries."""

import json
import gzip
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "summarize-a2-sliced-periodic-bounded.py"


with tempfile.TemporaryDirectory() as directory_name:
    directory = Path(directory_name)
    shard = directory / "probe-orbits000-001.ndjson"
    shard.write_text(json.dumps({
        "id": "probe",
        "classification": "unresolved",
        "periodic_z3": {
            "hnf_range": [0, 1],
            "hnf_visited": 1,
            "hnf_orbit_representatives": True,
            "hnf_orbit_total": 1,
            "solver_unknown": 0,
            "hnf_covered": 5,
            "hnf_total": 5,
            "exact_multicover_nodes": 17,
            "exact_multicover_failed_states": 17,
            "milliseconds": 3,
        },
    }) + "\n")
    output = directory / "summary.json"
    subprocess.run([
        sys.executable,
        str(SCRIPT),
        "--input-dir", str(directory),
        "--output", str(output),
        "--candidate-ids", "probe",
        "--copies", "8",
        "--orbit-total", "1",
        "--exact-node-limit", "2000000",
        "--campaign", "palindromic_size9_copy8_probe",
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    summary = json.loads(output.read_text())
    assert summary["campaign"] == "palindromic_size9_copy8_probe"
    assert summary["copies"] == 8
    assert summary["claim_scope"] == "fixed_8_copy_weighted_hnf_quotients"
    assert summary["candidates"][0]["exact_negative_orbits"] == 1

    retry_directory = directory / "retry"
    retry_directory.mkdir()
    retry_shard = retry_directory / shard.name
    retry_record = json.loads(shard.read_text())
    retry_record["periodic_z3"].update({
        "solver_unknown": 0,
        "hnf_covered": 5,
        "exact_multicover_nodes": 23,
        "exact_multicover_failed_states": 22,
        "milliseconds": 7,
    })
    retry_shard.write_text(json.dumps(retry_record) + "\n")
    archive = directory / "strongest.ndjson.gz"
    subprocess.run([
        sys.executable,
        str(SCRIPT),
        "--input-dir", str(directory),
        "--retry-dir", str(retry_directory),
        "--output", str(output),
        "--receipt-archive", str(archive),
        "--candidate-ids", "probe",
        "--copies", "8",
        "--orbit-total", "1",
        "--exact-node-limit", "20",
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    summary = json.loads(output.read_text())
    assert summary["candidates"][0]["exact_multicover_nodes"] == 23
    archived = [json.loads(line) for line in gzip.open(archive, "rt") if line.strip()]
    assert len(archived) == 1
    assert archived[0]["periodic_z3"]["exact_multicover_nodes"] == 23

    probe_directory = directory / "solver-probe"
    probe_directory.mkdir()
    full_probe = json.loads(shard.read_text())
    full_probe["periodic_z3"].update({
        "solver_unknown": 1,
        "hnf_covered": 0,
        "milliseconds": 120,
    })
    (probe_directory / "full.ndjson").write_text(json.dumps(full_probe) + "\n")
    partial_probe = json.loads(json.dumps(full_probe))
    partial_probe["periodic_z3"]["milliseconds"] = 30
    (probe_directory / "partial.ndjson").write_text(json.dumps(partial_probe) + "\n")
    subprocess.run([
        sys.executable,
        str(SCRIPT),
        "--input-dir", str(directory),
        "--output", str(output),
        "--candidate-ids", "probe",
        "--copies", "8",
        "--orbit-total", "1",
        "--exact-node-limit", "2000000",
        "--probe-dir", str(probe_directory),
        "--probe-solver", "qffd",
        "--probe-timeout-ms", "120",
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    summary = json.loads(output.read_text())
    assert summary["solver_probe"] == {
        "solver": "qffd",
        "timeout_ms_per_orbit": 120,
        "completed_shards": 1,
        "partial_interrupted_receipts_excluded": 1,
        "periodic_certificates": 0,
        "exact_negative_orbits": 0,
        "solver_unknown_shards": 1,
    }

print("A2-sliced bounded periodic summary regression passed")
