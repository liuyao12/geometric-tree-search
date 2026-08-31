#!/usr/bin/env python3
"""Regression for copy-count-specific bounded campaign summaries."""

import json
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

print("A2-sliced bounded periodic summary regression passed")
