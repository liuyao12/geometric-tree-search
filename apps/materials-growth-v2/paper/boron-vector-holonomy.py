"""Training-only vector cycle-closure diagnostic on the nine-cover ensembles."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).parent
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
transport=module('transport','transport-holonomy.py');geom=module('geometry','ice-motif-dictionary.py')
dest=Path(sys.argv[3]);dest.mkdir();summaries=[]
for fold in range(6):
    dr=(Path(sys.argv[1])/str(fold)/'training-dictionary.json').read_bytes();d=json.loads(dr)
    er=(Path(sys.argv[2])/f'{fold}.json').read_bytes();e=json.loads(er)
    assert e['trainingDictionaryHash']==hashlib.sha256(dr).hexdigest()
    edges=[];seen=set();observed=set()
    def add(a,ra,b,rb):
        if a>b:a,b,ra,rb=b,a,rb,ra
        key=(a,b,tuple(np.asarray(ra).ravel()),tuple(np.asarray(rb).ravel()))
        if key in seen:return
        seen.add(key);edges.append((a,np.asarray(ra).tolist(),b,np.asarray(rb).tolist()))
    for bundle in e['covers']:
        for c,selected in zip(d['configurations'],bundle):
            points=[[] for _ in range(c['atoms'])]
            for index in selected['selected']:
                o=c['occurrences'][index]
                for u,p in enumerate(o['permutation']):
                    v=3*o['type']+u;observed.add(v);points[o['ids'][p]].append((v,np.array(o['rotationRow']).T))
            assert all(len(g)==e['k'] for g in points)
            for group in points:
                for (a,ra),(b,rb) in itertools.combinations(group,2):add(a,ra,b,rb)
    # Recompute self-correspondence rotations: scalar ties alone are insufficient
    # for vector-valued markings. Only observed components are introduced.
    for t in d['types']:
        if not any(3*t['id']+u in observed for u in range(3)):continue
        for perm in itertools.permutations(range(3)):
            fit=geom.fit(t['positions'],t['positions'],np.array([perm]),d['epsilonAngstrom'])
            if fit is None:continue
            R=np.array(fit['rotationRow']).T
            for u,p in enumerate(perm):
                a,b=3*t['id']+p,3*t['id']+u;observed.update([a,b]);add(a,np.eye(3),b,R)
    result=transport.analyze(sorted(observed),edges)
    cs=result['components'];largest=max(cs,key=lambda c:len(c['members']))
    summary={'fold':fold,'observedVariables':len(observed),'constraints':len(edges),'components':len(cs),
        'numericallyFullRankComponents':sum(c['numericalNullity']==0 for c in cs),
        'variablesInFullRankComponents':sum(len(c['members']) for c in cs if c['numericalNullity']==0),
        'largestComponentVariables':len(largest['members']),'largestComponentNullity':largest['numericalNullity'],
        'largestComponentUnitRootRms':largest['unitRootRmsMismatch'],
        'largestComponentUnitRootMaximum':largest['unitRootMaximumMismatch']}
    out={'trainingDictionaryHash':hashlib.sha256(dr).hexdigest(),'ensembleHash':hashlib.sha256(er).hexdigest(),
        'summary':summary,'constraints':edges,**result}
    with (dest/f'{fold}.json').open('x') as f:json.dump(out,f)
    summaries.append(summary);print(json.dumps(summary),flush=True)
(dest/'summary.json').write_text(json.dumps({'scope':transport.__doc__,'results':summaries},indent=2))
