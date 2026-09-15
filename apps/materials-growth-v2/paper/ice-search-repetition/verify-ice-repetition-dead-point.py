"""Verify saved geometry-only dead-point witnesses, not aggregate visit counts."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
modelp,profilep,out=map(Path,sys.argv[1:]);raw=modelp.read_bytes();model=json.loads(raw)['models'][0]['model'];profile=json.loads(profilep.read_text())
assert profile['sourceHash']==hashlib.sha256(raw).hexdigest()
byid={c['id']:c for c in model['candidates']};geometry={}
for c in model['candidates']:
    support={t['point']:t['value'] for t in c['t']}
    if c['base'] in geometry:assert geometry[c['base']]==support
    geometry[c['base']]=support
checked=0;groups=0
for run in profile['results']:
    for state in run['deadStates']:
        groups+=1
        for witness in state['examples']:
            rows=[byid[i] for i in witness['selected']];owners={c['base'] for c in rows};assert len(owners)==len(rows) and sorted(owners)==state['owners']
            totals=Counter()
            for c in rows:totals.update({t['point']:t['value'] for t in c['t']})
            assert max(totals.values())<=model['capacity'];point=witness['point'];assert point in model['required'] and totals[point]<model['capacity']
            legal=[g for g,t in geometry.items() if point in t and g not in owners and all(totals[p]+v<=model['capacity'] for p,v in t.items())]
            assert len(legal)==witness['geometricallyLegalInventories']==0;checked+=1
report=dict(profileHash=hashlib.sha256(profilep.read_bytes()).hexdigest(),modelHash=hashlib.sha256(raw).hexdigest(),verifierHash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),geometryGroups=groups,checkedWitnesses=checked,limits='Verifies saved dead-point certificates independent of markings; does not independently replay aggregate visit counts or prove all marked states with the same geometry are equivalent.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
