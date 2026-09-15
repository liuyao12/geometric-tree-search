"""Collect hash-bound phase tests without exporting coordinate-derived clouds."""
import hashlib
import json
from pathlib import Path
import sys

folder, output = map(Path, sys.argv[1:3])
assert sys.argv[3:] in ([], ['--include-connected-diagnostic'])
def read(p):
    return json.loads(p.read_text())
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
manifest = read(folder / 'manifest.json')
rows = []
for phase in ('Ih', 'II', 'VI'):
    base = folder / phase
    hashes = {key: digest(base / name) for key, name in (
        ('source', 'source.json'), ('blocks', 'blocks.json'), ('filtered', 'filtered.json'),
        ('proof', 'proof.json'), ('index', 'index.json'))}
    bc, sc, ic = [read(base / name) for name in ('blocks-check.json', 'support-check.json', 'index-check.json')]
    assert bc['sourceModelHash'] == hashes['source'] and bc['blocksHash'] == hashes['blocks']
    assert sc['proofHash'] == hashes['proof'] and sc['filteredHash'] == hashes['filtered']
    assert ic['sourceModelHash'] == hashes['source'] and ic['blocksHash'] == hashes['filtered'] and ic['indexHash'] == hashes['index']
    for policy in manifest['orderingPolicies']:
        summary = read(base / policy / 'summary.json')
        check = read(base / f'{policy}-check.json')
        assert summary['sourceModelHash'] == check['sourceModelHash'] == hashes['source']
        assert summary['blocksHash'] == check['blocksHash'] == hashes['filtered']
        assert summary['sourceHashes']['partnerIndex'] == hashes['index']
        assert summary['sourceHashes']['partnerIndexCheck'] == digest(base / 'index-check.json')
        for result, verified in zip(summary['results'], check['results'], strict=True):
            assert (result['file'], result['fold'], result['selected']) == (verified['file'], verified['fold'], verified['selected'])
            assert verified['runHash'] == digest(base / policy / f"{result['fold']}.json")
            assert result['rootRollback'] and result['ordering'] == policy
            assert result['scalarComplete'] == verified['complete']
            if verified['complete']:
                assert result['status'] == 'complete-awaiting-independent-verification'
                assert result['markingStatus'] == 'verified-common-values'
                assert verified['verifiedAssignments'] == 2 * verified['selected']
            metadata = next(c for c in manifest['configurations'] if c['id'] == result['file'])
            assert metadata['phase'] == phase
            rows.append({'phase': phase, 'split': 'training' if metadata['split'] == 'train' else 'developmental',
                         'atoms': metadata['atoms'], 'result': result, 'independentCheck': verified,
                         'artifactHashes': hashes, 'checkHash': digest(base / f'{policy}-check.json')})
assert len(rows) == 12
report = {'scope': __doc__, 'manifestHash': digest(folder / 'manifest.json'),
          'configurations': manifest['configurations'], 'results': rows,
          'completeRuns': sum(r['independentCheck']['complete'] for r in rows),
          'completeConfigurations': sorted({r['result']['file'] for r in rows if r['independentCheck']['complete']}),
          'limits': manifest['limits'], 'summarizerHash': digest(Path(__file__))}
if sys.argv[3:]:
    diagnostics = []
    for phase in ('Ih', 'II', 'VI'):
        base = folder / phase
        summary = read(base / 'connected-oracle/summary.json')
        check = read(base / 'connected-oracle-check.json')
        assert summary['sourceModelHash'] == check['sourceModelHash'] == digest(base / 'source.json')
        assert summary['blocksHash'] == check['blocksHash'] == digest(base / 'filtered.json')
        for result, verified in zip(summary['results'], check['results'], strict=True):
            assert result['referenceSearch'] is False and result['connectedCoverRequested'] is True
            assert (result['file'], result['fold'], result['selected']) == (verified['file'], verified['fold'], verified['selected'])
            assert result['scalarComplete'] == verified['complete']
            assert verified['runHash'] == digest(base / 'connected-oracle' / f"{result['fold']}.json")
            if verified['complete']:
                assert result['markingStatus'] == 'verified-common-values'
                assert verified['verifiedAssignments'] == 2 * verified['selected']
                assert verified['positiveSupportComponents'] == 1
            diagnostics.append({'phase': phase, 'result': result, 'independentCheck': verified,
                                'checkHash': digest(base / 'connected-oracle-check.json')})
    assert len(diagnostics) == 6
    report['separateConnectedExistenceDiagnostic'] = diagnostics
with output.open('x') as f:
    json.dump(report, f, indent=2)
print(json.dumps({'runs': len(rows), 'completeRuns': report['completeRuns'], 'completeConfigurations': report['completeConfigurations']}))
