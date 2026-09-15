"""Compile factorized decorated-candidate blocks without projecting their counts.

Each endpoint retains one choice per original coupled source variant, including
duplicate values. No unproved deduplication is performed. The Cartesian product
is a new factorized learned model, not equivalent to the coupled hypothesis.
Cloud values are referenced from the hash-bound original registered model.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_path,output=sys.argv[1:];source=json.loads(Path(source_path).read_text());models=[];reports=[]
for row in source['models']:
    model=row['model'];grouped=defaultdict(list)
    for c in model['candidates']:grouped[c['base']].append(c)
    blocks=[];lookup={}
    for base,cs in grouped.items():
        first=cs[0];assert first['m']==[] and len(first['cloudM'])==2
        points=[m['point'] for m in first['cloudM']];assert len(set(points))==2
        for c in cs:
            assert c['t']==first['t'] and c['m']==[] and [m['point'] for m in c['cloudM']]==points
            assert c['registration']['rotationRow']==first['registration']['rotationRow']
        choices=[[dict(sourceCandidate=c['id'],sourceMotif=c['registration']['motif'],cloud=c['cloudM'][side]['cloud']) for c in cs] for side in range(2)]
        block=dict(id=base,inventory=base,t=first['t'],markPoints=points,endpointChoices=choices,
                   rotationRow=first['registration']['rotationRow'],candidateCount=str(len(cs)**2))
        for i,c in enumerate(cs):lookup[c['id']]=dict(block=base,left=i,right=i)
        blocks.append(block)
    lifts=[dict(name=lift['name'],selected=[lookup[c] for c in lift['selected']]) for lift in row['trainingLifts']]
    report=dict(file=row['file'],geometricBlocks=len(blocks),coupledCandidates=len(model['candidates']),
                factorizedCandidates=str(sum(int(b['candidateCount']) for b in blocks)),storedEndpointChoices=sum(sum(map(len,b['endpointChoices'])) for b in blocks),
                largestBlock=str(max(int(b['candidateCount']) for b in blocks)))
    reports.append(report)
    models.append(dict(file=row['file'],fold=row['fold'],capacity=model['capacity'],required=model['required'],cloudRadius=model['cloudRadius'],blocks=blocks,trainingLifts=lifts))
data=dict(scope=__doc__,sourceModelHash=sha(source_path),sourceHashes=source['sourceHashes'],codeHash=sha(__file__),models=models,summary=reports,
          limits='Storage compiler only. Source model supplies the cloud pool. No cloud legality, search, compression speedup, or change to forced-move semantics has been validated on materials yet.')
with Path(output).open('x') as f:json.dump(data,f)
print(json.dumps(reports),flush=True)
