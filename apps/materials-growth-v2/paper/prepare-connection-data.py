"""Freeze geometry-only data for the connection-transfer experiment.

Usage: python3 prepare-connection-data.py /path/to/216-atoms.xyz output.json
The downloaded XYZ is from lamrosset/aSi-data, CC BY 4.0. No energies or
forces are supplied to the experiment. Original headers are provenance only.
"""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from materials_gcts_cdyb_oracle import generate_cdyb, SOURCE

raw = Path(sys.argv[1]).read_bytes()
lines = raw.decode().splitlines()
frames = []
offset = 0
for frame in range(24):
    n = int(lines[offset])
    header = lines[offset + 1]
    atoms = []
    for line in lines[offset + 2:offset + n + 2]:
        fields = line.split()
        atoms.append({"species": fields[0], "position": list(map(float, fields[1:4]))})
    frames.append({"id": frame, "header": header, "atoms": atoms})
    offset += n + 2
qc = generate_cdyb(4, (60., 60., 60.))
result = {
    "schema": "connection-transfer-data/1",
    "silicon": {"url": "https://github.com/lamrosset/aSi-data/blob/main/data/xyz/216-atoms.xyz",
        "doi": "10.5281/zenodo.14203730", "license": "CC BY 4.0",
        "downloadSha256": hashlib.sha256(raw).hexdigest(),
        "selection": "First 24 configurations in file order; 216 atoms, quench label 10^10, terminal anneal 293K/10ps. Preparation-parameter sweep, NOT an identical-condition equilibrium ensemble.",
        "frames": frames},
    "quasicrystal": {"source": SOURCE, "box": 60, "maxIndex": 4,
        "scope": "Finite truncation of the published deterministic model, not independent experimental replicates or an infinite-structure certificate.",
        "atoms": [{"species": s, "position": p} for s, p in zip(qc.symbols, qc.positions)]}}
Path(sys.argv[2]).write_text(json.dumps(result, separators=(",", ":")) + "\n")
print(json.dumps({"siliconConfigurations": len(frames), "quasicrystalAtoms": qc.count}))
