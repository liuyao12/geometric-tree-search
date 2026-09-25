#!/usr/bin/env python3
"""Rebuild the exact input and check the published standalone-engine proof."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import subprocess

import build
from run import CNF_SHA256, sha

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--drat-trim', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
artifacts = Path(__file__).resolve().parents[2] / 'data/gcts-conflict-search'
receipt = json.loads((artifacts / 'result.json').read_text())
archive = artifacts / 'nonacube-proof.drat.gz'
assert sha(archive) == receipt['publishedProof']['gzipSha256'], 'compressed proof hash mismatch'
build.export('nonacube', a.output / 'problem')
cnf = a.output / 'problem.cnf'
assert sha(cnf) == CNF_SHA256, 'formula differs from the audited input'
proof = a.output / 'proof.drat'
with gzip.open(archive, 'rb') as src, proof.open('wb') as dst:
    shutil.copyfileobj(src, dst)
assert sha(proof) == receipt['publishedProof']['sha256'], 'expanded proof hash mismatch'
check = subprocess.run([str(a.drat_trim.resolve()), str(cnf), str(proof), '-i', '-U'], capture_output=True, text=True)
(a.output / 'proof-check.log').write_text(check.stdout + check.stderr)
assert check.returncode == 0 and 's VERIFIED' in check.stdout, 'proof check failed; see proof-check.log'
print(json.dumps({'status': 'UNSAT', 'proofVerified': True, 'formulaSha256': CNF_SHA256,
                  'proofSha256': sha(proof), 'checkerSha256': sha(a.drat_trim)}, indent=2))
