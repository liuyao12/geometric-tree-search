"""Frozen first-frame phase expansion; serial runs, no outcome-selected policy."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('pilot', type=Path)
p.add_argument('library', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--node', required=True)
args = p.parse_args()
here = Path(__file__).resolve().parent
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
metadata = json.loads((args.pilot / 'provenance.json').read_text())['configurations']
dictionary = args.pilot / 'thermal-dictionary-e015.json'
cover = args.pilot / 'overlap-broad.json'
selected = [r for r in metadata if r['sourceFrame'] == 0 and r['phase'] in ('Ih', 'II', 'VI')]
assert len(selected) == 6
training = {r['id']: r['training'] for r in json.loads(dictionary.read_text())['configurations']}
assert all(training[r['id']] == (r['split'] == 'train') for r in selected)
args.output.mkdir()
manifest = {
    'rule': 'First source frame of each author split in Ih, II, VI; frozen before search. Existing VIII runs are historical controls, not rerun timings.',
    'configurations': selected,
    'sourceHashes': {str(path): digest(path) for path in (dictionary, cover, args.library, args.pilot / 'provenance.json')},
    'orderingPolicies': ['baseline', 'support-rich'],
    'searchBudgetSecondsPerFramePerPolicy': 30,
    'limits': 'Developmental, not blind. Conditions and independent trajectories unverified. Fixed registered positions; no beyond-input growth. Endpoint factorization broadens the coupled learned hypothesis. Half weights inherited, not relearned.',
}
with (args.output / 'manifest.json').open('x') as f:
    json.dump(manifest, f, indent=2)
def run(script, *values):
    runtime = args.node if script.endswith('.mjs') else sys.executable
    print(json.dumps({'starting': script, 'arguments': list(map(str, values))}), flush=True)
    subprocess.run([runtime, str(here / script), *map(str, values)], check=True)

for phase in ('Ih', 'II', 'VI'):
    target = args.output / phase
    target.mkdir()
    source, blocks, filtered, proof, index = [target / name for name in ('source.json', 'blocks.json', 'filtered.json', 'proof.json', 'index.json')]
    ids = ','.join(r['id'] for r in selected if r['phase'] == phase)
    run('compile-ice-multicover-search.py', dictionary, cover, args.library, ids, source)
    run('compile-ice-factorized-blocks.py', source, blocks)
    run('verify-ice-factorized-blocks.mjs', source, blocks, target / 'blocks-check.json')
    run('prune-ice-factorized-support.py', source, blocks, filtered, proof, '--full-cloud')
    run('verify-factorized-support.py', source, blocks, filtered, proof, target / 'support-check.json')
    run('compile-factorized-complement-index.py', source, filtered, index)
    run('verify-factorized-complement-index.py', source, filtered, index, target / 'index-check.json')
    for policy in manifest['orderingPolicies']:
        run('ice-dynamic-factorized-search.mjs', source, filtered, target / policy, index, target / 'index-check.json', policy)
        run('verify-ice-factorized-search.py', source, filtered, target / policy, target / f'{policy}-check.json')
    print(json.dumps({'completedPhase': phase}), flush=True)
