"""Learn scalar equality components from selected training covers only.

Unobserved components are missing assignments, not artificial negative labels.
Template self-correspondence ties use the prior declared approximate symmetry.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
spec=importlib.util.spec_from_file_location('marks',Path(__file__).with_name('presearch-markings.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
destination=Path(sys.argv[3]);destination.mkdir()
for i in range(6):
    raw=(Path(sys.argv[1])/str(i)/'training-dictionary.json').read_bytes();d=json.loads(raw)
    selected_raw=(Path(sys.argv[2])/f'{i}.json').read_bytes();s=json.loads(selected_raw)
    assert s['trainingDictionaryHash']==hashlib.sha256(raw).hexdigest()
    chosen=s['trainingTrials'][-1];assert chosen['status']=='training passed'
    groups=[];active=set()
    for c,fit in zip(d['configurations'],chosen['fits']):
        assert fit['file']==c['file'];local=[[] for _ in range(c['atoms'])]
        for index in fit['selected']:
            o=c['occurrences'][index]
            for u,p in enumerate(o['permutation']):
                v=3*o['type']+u;active.add(v);local[o['ids'][p]].append(v)
        assert all(len(g)==chosen['k'] for g in local);groups+=local
    groups += [[3*t['id']+a,3*t['id']+b] for t in d['types'] for a,b in t['symmetryTies']]
    labels=m.equality_labels(3*len(d['types']),groups);observed={labels[v] for v in active}
    labels=[label if label in observed else None for label in labels]
    out={'scope':__doc__,'trainingDictionaryHash':hashlib.sha256(raw).hexdigest(),
        'selectedArtifactHash':hashlib.sha256(selected_raw).hexdigest(),'labels':labels,
        'summary':{'fold':i,'variables':len(labels),'observedVariables':len(active),
            'assignedVariables':sum(v is not None for v in labels),'classes':len(observed)}}
    (destination/f'{i}.json').write_text(json.dumps(out));print(json.dumps(out['summary']))
