"""Six training-only dictionaries, tested against omitted known-coordinate supports.

No test type creation or weight refitting. This is configuration holdout, not
independent-source validation: the six models come from the same supplement.
"""
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('triples',HERE/'boron-triple-precheck.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fold(args):
    source,folder,index=args
    raw=Path(source).read_bytes();inputs=json.loads(raw)['results'];held=inputs[index]
    out=Path(folder)/str(index);out.mkdir()
    train={'scope':'Five training configurations only','results':[c for i,c in enumerate(inputs) if i!=index]}
    (out/'training-input.json').write_text(json.dumps(train))
    with (out/'training.log').open('x') as log:
        subprocess.run([sys.executable,str(HERE/'boron-triple-precheck.py'),str(out/'training-input.json'),
                        str(out/'training-dictionary.json'),'.01'],stdout=log,stderr=subprocess.STDOUT,check=True)
    frozen=(out/'training-dictionary.json').read_bytes();dictionary=json.loads(frozen)
    types=dictionary['types'];fit=dictionary['results'][-1];epsilon=dictionary['epsilonAngstrom']
    radius,supports=m.propose_supports(held);occurrences=[];unmatched=[]
    lengths_array=np.array([t['lengths'] for t in types])
    for ids,positions in sorted(supports.items()):
        lengths=np.sort([np.linalg.norm(positions[a]-positions[b]) for a,b in ((0,1),(0,2),(1,2))])
        found=None
        for index_type in np.flatnonzero(np.max(np.abs(lengths_array-lengths),axis=1)<=2*epsilon):
            t=types[int(index_type)];registration=m.geom.fit(t['positions'],positions,m.PERMS,epsilon)
            if registration is not None:found=(t,registration);break
        if found is None:unmatched.append(list(ids));continue
        t,registration=found
        occurrences.append({'ids':ids,'type':t['id'],'liftedPositions':positions.tolist(),**registration})
    result={'heldOut':held['file'],'trainingStatus':fit['status'],'types':len(types),
            'supports':len(supports),'matched':len(occurrences),'unmatched':len(unmatched)}
    if 'weights' in fit:
        w=list(map(Fraction,fit['weights']));labels=fit['labels']
        totals=[Fraction(0)]*held['atoms'];marks=[set() for _ in totals]
        for o in occurrences:
            for u,p in enumerate(o['permutation']):
                v=3*o['type']+u;point=o['ids'][p];totals[point]+=w[v];marks[point].add(labels[v])
        result.update(atoms=held['atoms'],exactlyFilled=sum(v==1 for v in totals),
            underfilled=sum(v<1 for v in totals),overfilled=sum(v>1 for v in totals),
            markingConflicts=sum(len(s)>1 for s in marks),trainingScalarClasses=fit['activeScalarClasses'],
            allMatchedCoverValid=all(v==1 for v in totals) and all(len(s)<=1 for s in marks))
    assert (out/'training-dictionary.json').read_bytes()==frozen
    artifact={'scope':__doc__,'sourceHash':hashlib.sha256(raw).hexdigest(),
        'frozenDictionaryHash':hashlib.sha256(frozen).hexdigest(),'epsilonAngstrom':epsilon,
        'result':result,'testConfiguration':{'file':held['file'],'atoms':held['atoms'],
         'radius':radius,'occurrences':occurrences},'unmatchedSupports':unmatched}
    (out/'test-result.json').write_text(json.dumps(artifact))
    print(json.dumps(result),flush=True);return result

if __name__=='__main__':
    source=Path(sys.argv[1]).resolve();folder=Path(sys.argv[2]).resolve();folder.mkdir()
    with ProcessPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(fold,[(str(source),str(folder),i) for i in range(6)]))
    (folder/'summary.json').write_text(json.dumps({'scope':__doc__,'results':results},indent=2))
