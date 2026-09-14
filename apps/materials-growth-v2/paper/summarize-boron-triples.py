"""Export aggregate results without redistributing source coordinate geometries."""
import collections
import hashlib
import json
from pathlib import Path
import sys
runs=[]
for path in sys.argv[2:]:
    raw=Path(path).read_bytes();data=json.loads(raw)
    configurations=[set() for _ in data['types']]
    for c in data['configurations']:
        for o in c['occurrences']:configurations[o['type']].add(c['file'])
    runs.append({'artifactHash':hashlib.sha256(raw).hexdigest(),'inputHash':data['inputHash'],
        'epsilonAngstrom':data['epsilonAngstrom'],'radiusScale':data['radiusScale'],
        'types':len(data['types']),'occurrences':sum(len(c['occurrences']) for c in data['configurations']),
        'singleOccurrenceTypes':sum(t['trainingOccurrences']==1 for t in data['types']),
        'typeConfigurationCounts':dict(sorted(collections.Counter(map(len,configurations)).items())),
        'results':[{k:v for k,v in r.items() if k not in ('weights','labels')} for r in data['results']]})
with open(sys.argv[1],'x') as out:json.dump({'scope':'Known-coordinate training prechecks, not held-out transfer or growth',
    'conditionMatchedEnsemble':False,'runs':runs},out,indent=2)
