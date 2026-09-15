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
p.add_argument('--policies',nargs='+',choices=['baseline','support-rich','coupled-observed'],default=['baseline','support-rich'])
p.add_argument('--resume-compiled',action='store_true',help='Resume only from hash-verified compiled blocks; refuse partial later stages.')
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
args.output.mkdir(exist_ok=args.resume_compiled)
manifest = {
    'rule': 'First source frame of each author split in Ih, II, VI; frozen before search. Existing VIII runs are historical controls, not rerun timings.',
    'configurations': selected,
    'sourceHashes': {str(path): digest(path) for path in (dictionary, cover, args.library, args.pilot / 'provenance.json')},
    'orderingPolicies': args.policies,
    'searchBudgetSecondsPerFramePerPolicy': 30,
    'limits': 'Developmental, not blind. Conditions and independent trajectories unverified. Fixed registered positions; no beyond-input growth. Endpoint factorization broadens the coupled learned hypothesis. Half weights inherited, not relearned.',
}
if args.policies==['coupled-observed']:
    manifest['limits']='Developmental, not blind. Conditions and independent trajectories unverified. Fixed registered positions; no beyond-input growth. Search retains observed endpoint pairs; factorized preprocessing is a necessary superset filter only. Half weights inherited, not relearned.'
if args.resume_compiled:
    assert json.loads((args.output/'manifest.json').read_text())==manifest
else:
    with (args.output / 'manifest.json').open('x') as f:json.dump(manifest, f, indent=2)
def run(script, *values):
    runtime = args.node if script.endswith('.mjs') else sys.executable
    print(json.dumps({'starting': script, 'arguments': list(map(str, values))}), flush=True)
    subprocess.run([runtime, str(here / script), *map(str, values)], check=True)

for phase in ('Ih', 'II', 'VI'):
    target = args.output / phase
    target.mkdir(exist_ok=args.resume_compiled)
    source, blocks, filtered, proof, index = [target / name for name in ('source.json', 'blocks.json', 'filtered.json', 'proof.json', 'index.json')]
    ids = ','.join(r['id'] for r in selected if r['phase'] == phase)
    compiled_check=target/'blocks-check.json'
    if args.resume_compiled and compiled_check.exists():
        assert {p.name for p in target.iterdir()}=={'source.json','blocks.json','blocks-check.json'}, 'Later-stage files require explicit recovery, not replay'
        check=json.loads(compiled_check.read_text())
        assert check['sourceModelHash']==digest(source) and check['blocksHash']==digest(blocks)
        assert check['verifierHash']==digest(here/'verify-ice-factorized-blocks.mjs')
        compiled=json.loads(source.read_text())
        assert compiled['portableHash']==digest(args.library)
        assert compiled['sourceHashes']['dictionary']==digest(dictionary) and compiled['sourceHashes']['cover']==digest(cover)
        assert [r['file'] for r in compiled['models']]==ids.split(',')
        del compiled
        print(json.dumps({'resumedVerifiedCompile':phase,'checkHash':digest(compiled_check)}),flush=True)
    else:
        assert not list(target.iterdir()), 'Unverified partial compilation; refusing overwrite'
        run('compile-ice-multicover-search.py', dictionary, cover, args.library, ids, source)
        run('compile-ice-factorized-blocks.py', source, blocks)
        run('verify-ice-factorized-blocks.mjs', source, blocks, compiled_check)
    run('prune-ice-factorized-support.py', source, blocks, filtered, proof, '--full-cloud')
    run('verify-factorized-support.py', source, blocks, filtered, proof, target / 'support-check.json')
    run('compile-factorized-complement-index.py', source, filtered, index)
    run('verify-factorized-complement-index.py', source, filtered, index, target / 'index-check.json')
    for policy in manifest['orderingPolicies']:
        run('ice-dynamic-factorized-search.mjs', source, filtered, target / policy, index, target / 'index-check.json', policy)
        run('verify-ice-factorized-search.py', source, filtered, target / policy, target / f'{policy}-check.json')
    print(json.dumps({'completedPhase': phase}), flush=True)
