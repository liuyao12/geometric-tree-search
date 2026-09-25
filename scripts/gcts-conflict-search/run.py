#!/usr/bin/env python3
"""Build and run the standalone search, then independently check its result."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

import build
import encode

HERE = Path(__file__).resolve().parent
CNF_SHA256 = '102e050db3761b588d87e866168917802f9ad23e53fa40bf7000a476bd469b1d'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def witness_check(shape, placements_file, selected):
    # Replay integer voxels and both halo obligations, without evaluating CNF.
    shapes = (((0, 0, 0),),) if shape == 'cube' else encode.SHAPES
    inventory = [tuple(map(int, row.split())) for row in placements_file.read_text().splitlines()]
    root = set(shapes[0])
    occupied = set(root)
    first = []
    halo = lambda voxels: {tuple(a + b for a, b in zip(v, d)) for v in voxels for d in encode.OFFSETS}
    root_halo = halo(root)
    assert len(selected) == len(set(selected))
    for v in selected:
        assert 1 <= v <= len(inventory)
        oi, *anchor = inventory[v - 1]
        cells = {tuple(a + b for a, b in zip(offset, anchor)) for offset in shapes[oi]}
        assert not occupied.intersection(cells), 'overlap in witness'
        occupied.update(cells)
        if cells.intersection(root_halo):
            first.append(cells)
    assert root_halo <= occupied, 'missing first corona'
    assert all(halo(cells) <= occupied for cells in first), 'missing second corona'
    return {'verified': True, 'selectedTiles': len(selected), 'occupiedVoxelsIncludingRoot': len(occupied)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--shape', choices=['nonacube', 'cube'], default='nonacube')
    p.add_argument('--seconds', type=float, default=300)
    p.add_argument('--drat-trim', type=Path)
    p.add_argument('--audit', action='store_true', help='exhaustively recompute the graph at every branch/rollback')
    a = p.parse_args()
    assert a.seconds > 0
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    prefix = out / 'problem'
    stats = build.export(a.shape, prefix)
    formula_hash = sha(prefix.with_suffix('.cnf'))
    if a.shape == 'nonacube':
        assert formula_hash == CNF_SHA256, 'formula differs from the published certificate'
    subprocess.run(['c++', '-std=c++17', '-O3', '-DNDEBUG', str(HERE / 'solve.cc'), '-o', str(out / 'solver')], check=True)
    prepared = time.monotonic()
    cmd = [str(out / 'solver'), str(prefix.with_suffix('.cnf')), str(prefix.with_suffix('.points')), str(out / 'proof.drup'), str(a.seconds)]
    if a.audit:
        cmd.append('--audit')
    with (out / 'progress.log').open('w') as log:
        run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=log, text=True, check=True)
    result = json.loads(run.stdout)
    result.update(problem=stats, budgetSeconds=a.seconds, formulaSha256=formula_hash,
                  pointModelSha256=sha(prefix.with_suffix('.points')), proofSha256=sha(out / 'proof.drup'),
                  sourceSha256={name: sha(HERE / name) for name in ('solve.cc', 'encode.py', 'build.py', 'run.py')},
                  host={'system': platform.system(), 'machine': platform.machine()},
                  preparationSeconds=prepared-started, proofVerified=False, witnessVerified=False,
                  proofComplete=result['status'] == 'UNSAT')
    if result['status'] == 'SAT':
        result['witness'] = witness_check(a.shape, prefix.with_suffix('.placements.txt'), result['selected'])
        result['witnessVerified'] = True
    elif result['status'] == 'UNSAT' and a.drat_trim:
        check = subprocess.run([str(a.drat_trim.resolve()), str(prefix.with_suffix('.cnf')), str(out / 'proof.drup')], capture_output=True, text=True)
        (out / 'proof-check.log').write_text(check.stdout + check.stderr)
        result['proofVerified'] = check.returncode == 0 and 's VERIFIED' in check.stdout
        assert result['proofVerified'], 'proof checker rejected the result'
        result['checkerSha256'] = sha(a.drat_trim)
    result['totalSeconds'] = time.monotonic() - started
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
