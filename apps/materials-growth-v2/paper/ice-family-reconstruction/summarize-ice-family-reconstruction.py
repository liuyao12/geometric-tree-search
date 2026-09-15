"""Collect independently replayed finite reconstructions from a frozen library.

Usage: output (model result state-check proof-check)+
No timing comparison or same-condition provenance is inferred.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

out = Path(sys.argv[1])
paths = list(map(Path, sys.argv[2:]))
assert paths and len(paths) % 4 == 0
rows, shared_sources, selected_sets = [], None, {}
for offset in range(0, len(paths), 4):
    modelp, resultp, statep, proofp = paths[offset:offset + 4]
    model, result, state, proof = [json.loads(p.read_text()) for p in [modelp, resultp, statep, proofp]]
    assert result['sourceHash'] == digest(modelp) == proof['modelHash']
    assert proof['resultHash'] == digest(resultp)
    assert state['sourceHashes'][resultp.name] == digest(resultp)
    assert state['sourceHashes'][modelp.name] == digest(modelp)
    assert proof['verifiedCores'] == len(result['cores'])
    sources = model['sourceHashes']
    if shared_sources is None:
        shared_sources = sources
    assert sources == shared_sources, 'Library/dictionary/transfer inputs changed across cases'
    assert len(model['models']) == len(state['results']) == 1
    entry = model['models'][0]
    check = state['results'][0]
    assert entry['id'] == check['id'] and check['enabled']
    assert check['incompatiblePairs'] == 0
    assert len(result['selected']) == check['selectedPlacements']
    if result['status'] == 'complete-awaiting-independent-replay':
        assert check['complete']
    candidates = entry['model']['candidates']
    by_id = {c['id']: c for c in candidates}
    used = {by_id[i]['motif'] for i in result['selected']}
    selected_sets[entry['id']] = used
    rows.append(dict(id=entry['id'], **{k: v for k, v in check.items() if k != 'id'},
                     status='verified-finite-filling' if check['complete'] else 'incomplete-unknown',
                     registeredPlacements=len(model['registrations']), missingRegistrations=len(model['missing']),
                     decoratedCandidates=len(candidates), verifiedCores=proof['verifiedCores'],
                     totalRounds=result['totalRounds'], cumulativeSeconds=result['cumulativeSeconds'],
                     peakSavedRoundPlacementCount=max((r['selected'] for r in result['rounds']), default=0),
                     distinctSelectedDecorations=len(used),
                     artifactHashes={p.name: digest(p) for p in [modelp, resultp, statep, proofp]}))
overlap = [dict(first=a, second=b, sharedSelectedDecorations=len(selected_sets[a] & selected_sets[b]))
           for a, b in itertools.combinations(selected_sets, 2)]
report = dict(rows=rows, sharedSourceHashes=shared_sources, selectedDecorationOverlap=overlap,
              codeHash=digest(Path(__file__)),
              limits='Developmental cases, finite assigned-base registrations at known atom positions. Frozen library and radius, but not established identical conditions or independent trajectories. Incomplete states may be dead ends, not extendable growth. Proof-assisted search is not a learned-marking speedup. No pose completeness or growth beyond input.')
with out.open('x') as handle:
    json.dump(report, handle, indent=2)
print(json.dumps(rows))
