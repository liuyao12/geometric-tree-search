"""Export saved support indices and source mapping, never atomic coordinates."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from ase.io import read

pilot, corpus, runs, output = map(Path, sys.argv[1:])
def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest = load(runs / 'manifest.json')
coords = {c['id']: c for c in load(pilot / 'coordinates.json')['configurations']}
rows = []
for phase in ('Ih', 'II', 'VI'):
    folder = runs / phase
    data = load(folder / 'filtered.json')
    for model in data['models']:
        meta = next(c for c in manifest['configurations'] if c['id'] == model['file'])
        assert meta['sourceFrame'] == 0
        path = corpus / meta['sourceFile']
        assert sha(path) == meta['sourceSha256']
        atoms = read(path, index=0, format='extxyz')
        order = np.random.default_rng(meta['shuffleSeed']).permutation(len(atoms)).tolist()
        c = coords[meta['id']]
        assert np.array_equal(atoms.positions[order], c['positions'])
        assert [atoms.get_chemical_symbols()[i] for i in order] == c['species']
        frame = b''.join(path.read_bytes().splitlines(keepends=True)[:len(atoms)+2])
        name = 'training-set-energy-forces-stress-400.extxyz' if meta['split'] == 'train' else 'validation-set-energy-forces-stress.extxyz'
        row = {'id': meta['id'], 'phase': phase, 'split': 'training' if meta['split'] == 'train' else 'developmental',
               'atoms': len(atoms), 'sourceOrder': order,
               'sourceUrl': f'https://raw.githubusercontent.com/venkatkapil24/fine-tuning-MLPs-ice-polymorphs/c9a4bb534b35bfc8f467d7388f3056325bd2dd4e/dft_data/{phase}/{name}',
               'firstFrameHash': hashlib.sha256(frame).hexdigest(), 'sourceFileHash': sha(path), 'states': {}}
        for policy in ('baseline', 'support-rich', 'connected-oracle'):
            run_path = folder / policy / f"{model['fold']}.json"
            run = load(run_path)
            check = load(folder / f'{policy}-check.json')
            verified = next(r for r in check['results'] if r['file'] == model['file'])
            assert verified['runHash'] == sha(run_path)
            assert run['blocksHash'] == sha(folder / 'filtered.json')
            supports = []
            totals = [0] * len(atoms)
            for selected in run['selected']:
                block = model['blocks'][selected['index']]
                assert block['id'] == selected['block']
                assert all(t['value'] == 1 for t in block['t'])
                ids = [int(t['point']) for t in block['t']]
                for i in ids: totals[i] += 1
                supports.append(ids)
            assert all(t <= 2 for t in totals)
            assert all(t == 2 for t in totals) == verified['complete']
            assert len(supports) == verified['selected']
            row['states'][policy] = {'supports': supports, 'totals': totals,
                'complete': verified['complete'], 'commonValues': verified['commonValues'],
                'supportComponents': verified['positiveSupportComponents'], 'runHash': sha(run_path),
                'checkHash': sha(folder / f'{policy}-check.json'), 'search': policy != 'connected-oracle',
                'massFraction': sum(totals) / (2 * len(atoms))}
        rows.append(row)
out = {'scope': __doc__, 'configurations': rows, 'exporterHash': sha(Path(__file__)),
       'limits': 'Saved final states, not time histories. Coordinates fetched from author source; only the first frame is streamed and verified. Atomic positions and cell are not republished. Occupancy is geometric t, not physical density or chemistry.'}
with output.open('x') as f: json.dump(out, f, separators=(',', ':'))
print(json.dumps({'configurations': len(rows), 'savedStates': sum(len(r['states']) for r in rows), 'coordinateArraysExported': False}))
