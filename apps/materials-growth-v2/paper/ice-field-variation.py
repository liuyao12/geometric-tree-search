"""Training-only paired-field variation, one occurrence per base per frame.

First occurrence in stored cover order is chosen before distance evaluation.
Both endpoint fields stay in the stored shared base frame. Distance is maximum
of the two endpoint RKHS distances, not independently aligned endpoints.
This subset diagnostic neither calibrates a threshold nor tests transfer.
"""
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.distance import cdist

spec=importlib.util.spec_from_file_location('field',Path(__file__).with_name('gaussian-section-markings.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source,output=map(Path,sys.argv[1:]);raw=source.read_bytes();library=json.loads(raw)
chosen={}
for reg in library['trainingRegistrations']:
    for p in reg['selected']:
        chosen.setdefault((library['motifs'][p['motif']]['base'],reg['id']),p['motif'])
groups=defaultdict(list)
for (base,frame),motif in chosen.items():groups[base].append((frame,motif))
prepared={};checks=0;reference_checks=0;max_reference_error=0.
def prepare(i,s):
    key=i,s
    if key not in prepared:
        f=library['motifs'][i]['fieldM'][s];v,a,c=m.validate(f)
        prepared[key]=(v,a,np.asarray(c),f['sigma'])
    return prepared[key]
def inner(a,b):
    x,wa,ca,sigma=a;y,wb,cb,sigma_b=b;assert sigma==sigma_b
    return float(np.sum(wa[:,None]*wb[None,:]*np.exp(-cdist(x,y,'sqeuclidean')/(2*sigma*sigma))*(ca[:,None]==cb[None,:])))
norms={};rows=[]
for base,entries in sorted(groups.items()):
    best={frame:(math.inf,None) for frame,_ in entries}
    for u,(frame,i) in enumerate(entries):
        for other,j in entries[u+1:]:
            distances=[]
            for side in [0,1]:
                a=prepare(i,side);b=prepare(j,side)
                for key,value in [((i,side),a),((j,side),b)]:
                    if key not in norms:norms[key]=inner(value,value)
                rawd=math.fsum([norms[i,side],norms[j,side],-2*inner(a,b)])
                guard=128*np.finfo(float).eps*max(1.,(sum(abs(a[1]))+sum(abs(b[1])))**2)
                assert rawd>=-guard
                if checks%1000==0:
                    reference=m.discrepancy(library['motifs'][i]['fieldM'][side],library['motifs'][j]['fieldM'][side])
                    error=abs(rawd-reference['rawSquared']);assert error<=guard
                    reference_checks+=1;max_reference_error=max(max_reference_error,error)
                distances.append(math.sqrt(max(0.,rawd)))
            distance=max(distances);checks+=1
            if distance<best[frame][0]:best[frame]=(distance,other)
            if distance<best[other][0]:best[other]=(distance,frame)
    for frame,i in entries:
        distance,neighbor=best[frame]
        rows.append(dict(base=base,frame=frame,motif=i,neighborFrame=neighbor,distance=distance if math.isfinite(distance) else None))
    if base%50==0:print(json.dumps(dict(base=base,pairedComparisons=checks)),flush=True)
finite=[r['distance'] for r in rows if r['distance'] is not None]
summary=dict(selectedBaseFrameOccurrences=len(rows),baseTypes=len(groups),withoutOtherFrame=len(rows)-len(finite),
             pairedComparisons=checks,scalarReferenceEndpointChecks=reference_checks,maxReferenceSquaredError=max_reference_error,
             nearestPairedFieldDistanceQuantiles={str(q):float(np.quantile(finite,q)) for q in [.0,.5,.9,.95,1.]})
report=dict(scope=__doc__,libraryHash=hashlib.sha256(raw).hexdigest(),codeHash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),summary=summary,results=rows,
            units='Unnormalized Gaussian-field RKHS norm; not Angstroms.',
            limitations='Subset of training occurrences and fixed stored poses. Not phase separation, full nearest-neighbor calibration, negative examples, learned marking tolerance, independent configurations, or reconstruction.')
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(summary),flush=True)
