"""Training-cover robustness of scalar marks: no new atomic configurations.

Pool the original selected cover and eight alternative valid covers generated
by seeded candidate-order shuffles. Only five training inputs are consulted.
This probes cover-choice dependence, not a physical ensemble or generalization.
"""
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).parent
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
selected=module('selected','boron-selected-training.py');marks=module('marks','presearch-markings.py')

def labels_for(d,covers,k):
    groups=[];active=set()
    for bundle in covers:
        for c,fit in zip(d['configurations'],bundle):
            assert c['file']==fit['file'];points=[[] for _ in range(c['atoms'])]
            for i in fit['selected']:
                o=c['occurrences'][i]
                for u,p in enumerate(o['permutation']):
                    v=3*o['type']+u;active.add(v);points[o['ids'][p]].append(v)
            assert all(len(g)==k for g in points);groups+=points
    groups += [[3*t['id']+a,3*t['id']+b] for t in d['types'] for a,b in t['symmetryTies']]
    labels=marks.equality_labels(3*len(d['types']),groups);observed={labels[v] for v in active}
    labels=[v if v in observed else None for v in labels]
    return labels,{'classes':len(observed),'assignedVariables':sum(v is not None for v in labels),'observedVariables':len(active)}

def run(args):
    training,selections,dest,fold=args
    raw=(Path(training)/str(fold)/'training-dictionary.json').read_bytes();d=json.loads(raw)
    sr=(Path(selections)/f'{fold}.json').read_bytes();s=json.loads(sr)
    assert s['trainingDictionaryHash']==hashlib.sha256(raw).hexdigest()
    original=s['trainingTrials'][-1];assert original['status']=='training passed'
    covers=[original['fits']];snapshots=[]
    for round in range(9):
        if round:
            bundle=[]
            for i,c in enumerate(d['configurations']):
                seed=10000*fold+100*round+i
                fit=selected.selection(c,original['k'],seed)
                assert fit['status']=='exact integer coverage witness',fit
                bundle.append({'file':c['file'],'seed':seed,**fit})
            covers.append(bundle)
        if round in (0,1,2,4,8):
            labels,summary=labels_for(d,covers,original['k'])
            snapshots.append({'additionalCoversPerConfiguration':round,**summary,'labels':labels})
            print(json.dumps({'fold':fold,'round':round,**summary}),flush=True)
    unique=[len({tuple(sorted(bundle[i]['selected'])) for bundle in covers}) for i in range(5)]
    out={'scope':__doc__,'trainingDictionaryHash':hashlib.sha256(raw).hexdigest(),'selectedArtifactHash':hashlib.sha256(sr).hexdigest(),
        'k':original['k'],'covers':covers,'snapshots':snapshots,'uniqueCoversPerConfiguration':unique}
    with (Path(dest)/f'{fold}.json').open('x') as f:json.dump(out,f)
    return {'fold':fold,'uniqueCoversPerConfiguration':unique,'snapshots':[{k:v for k,v in s.items() if k!='labels'} for s in snapshots]}

if __name__=='__main__':
    dest=Path(sys.argv[3]);dest.mkdir()
    with ProcessPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(run,[(sys.argv[1],sys.argv[2],str(dest),i) for i in range(6)]))
    (dest/'summary.json').write_text(json.dumps({'scope':__doc__,'results':results},indent=2))
