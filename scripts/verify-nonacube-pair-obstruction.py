#!/usr/bin/env python3
"""Regenerate the finite formula and independently verify its UNSAT trace.

This is a specialized SAT proof control, not the reference growth scheduler.
With --drat-trim, use that external checker; otherwise use the repository's RUP
checker. No SAT solver is needed to replay the published certificate.
"""
import argparse
import gzip
import hashlib
import json
import subprocess
import tempfile
from itertools import product
from pathlib import Path
from certify_voxel_obstruction import construct
from lib.check_rup import RUPChecker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--drat-trim', help='Path to an independently built drat-trim executable')
    args = parser.parse_args()
    folder = Path(__file__).resolve().parents[1] / 'data/nonacube-pair-obstruction'
    data = json.loads((folder / 'problem.json').read_text())
    receipt = json.loads((folder / 'receipt.json').read_text())
    assert not data.get('pairExclusions')
    assert not any(o.get('marks') for o in data['model']['orientations'])
    # Reconstruct the complete radius-two target, including the fixed cubes.
    occupied = {tuple(v[i]+p['translation'][i]//2 for i in range(3))
                for p in data['fixed'] for v in data['model']['orientations'][p['oi']]['voxels']}
    assert len(occupied) == 18
    target = {tuple(v[i]+d[i] for i in range(3)) for v in occupied for d in product(range(-2,3), repeat=3)}
    assert {tuple(p['pos']) for p in data['model']['required']} == {tuple(2*x+1 for x in v) for v in target}
    formula, variables, stats = construct(data, amo='sequential')
    cnf = (f'p cnf {formula.variables} {len(formula.clauses)}\n'
           + ''.join(' '.join(map(str,c))+' 0\n' for c in formula.clauses)).encode()
    assert cnf == gzip.decompress((folder / 'proof.cnf.gz').read_bytes())
    proof = gzip.decompress((folder / 'proof.drup.gz').read_bytes())
    assert hashlib.sha256(cnf).hexdigest() == receipt['cnfSha256']
    assert hashlib.sha256(proof).hexdigest() == receipt['proofSha256']
    if args.drat_trim:
        with tempfile.TemporaryDirectory() as tmp:
            c, p = Path(tmp)/'formula.cnf', Path(tmp)/'trace.drup'
            c.write_bytes(cnf); p.write_bytes(proof)
            result = subprocess.run([args.drat_trim, str(c), str(p)], capture_output=True, text=True, check=True)
            assert 's VERIFIED' in result.stdout
            print(result.stdout.strip())
    else:
        print(RUPChecker(formula.clauses).verify(proof.decode().splitlines()))
    print(f'Certified forbidden pair: {len(target)} target voxels, {len(variables)} complete candidates; no boundary containment rule.')

if __name__ == '__main__':
    main()
