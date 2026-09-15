"""Training-only nearest contexts from different configurations of the same base.

Distance is the smaller of the two endpoint bottleneck cloud distances, with
color-preserving bijections in the stored base frame. No extra rotation fit,
phase label, target frame, physical variable or search witness is used.
This is a calibration diagnostic, not a rule admitting all such substitutions.
"""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys
import time
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

spec=importlib.util.spec_from_file_location('half',Path(__file__).with_name('half-cloud-support.py'))
half=importlib.util.module_from_spec(spec);spec.loader.exec_module(half)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def bottleneck(a,b):
    ca=[json.dumps(c,sort_keys=True) for c in a['colors']];cb=[json.dumps(c,sort_keys=True) for c in b['colors']]
    if sorted(ca)!=sorted(cb):return float('inf')
    distances=cdist(a['vectors'],b['vectors']);compatible=np.array(ca)[:,None]==np.array(cb)[None,:]
    levels=np.unique(distances[compatible]);lo=0;hi=len(levels)-1
    while lo<hi:
        mid=(lo+hi)//2;permitted=compatible&(distances<=levels[mid]);r,c=linear_sum_assignment(~permitted)
        if permitted[r,c].all():hi=mid
        else:lo=mid+1
    return float(levels[lo])

def calibrate(library,progress=None):
    motifs=library['motifs'];frames=defaultdict(set);groups=defaultdict(list)
    for row in library['trainingRegistrations']:
        for p in row['selected']:frames[p['motif']].add(row['id'])
    assert set(frames)==set(range(len(motifs)))
    for i,m in enumerate(motifs):groups[m['base']].append(i)
    results=[];checks=0
    for base,ids in sorted(groups.items()):
        n=len(ids);lower=np.full((n,n),np.inf)
        for side in range(2):
            buckets=defaultdict(list);features={}
            for local,i in enumerate(ids):
                layout,x=half.signature(motifs[i]['cloudM'][side]);buckets[layout].append(local);features[local]=x
            for locals_ in buckets.values():
                x=np.array([features[k] for k in locals_]);at=np.ix_(locals_,locals_)
                lower[at]=np.minimum(lower[at],cdist(x,x,metric='chebyshev'))
        cache={}
        for local,i in enumerate(ids):
            best=float('inf');neighbor=None;eligible=0
            for other in np.argsort(lower[local],kind='stable'):
                j=ids[other]
                # Conservative source-frame-disjoint diagnostic; explicitly
                # exclude any overlap if an observation has multiple sources.
                if frames[i]&frames[j]:continue
                eligible+=1
                if lower[local,other]>best+1e-10:break
                key=tuple(sorted((i,j)))
                if key not in cache:
                    cache[key]=min(bottleneck(motifs[i]['cloudM'][s],motifs[j]['cloudM'][s]) for s in range(2));checks+=1
                distance=cache[key]
                if distance<best:best=distance;neighbor=j
            results.append(dict(motif=i,base=base,sourceFrames=sorted(frames[i]),neighbor=neighbor,
                                neighborFrames=sorted(frames[neighbor]) if neighbor is not None else [],
                                distanceAngstrom=best if np.isfinite(best) else None))
        if progress and base%30==0:progress(dict(base=base,processed=len(results),distanceChecks=checks))
    results.sort(key=lambda r:r['motif']);finite=[r['distanceAngstrom'] for r in results if r['distanceAngstrom'] is not None]
    radius=library['markingRadiusAngstrom']
    return dict(scope=__doc__,results=results,summary=dict(motifs=len(motifs),bases=len(groups),
                basesSeenInOneFrame=sum(len(set().union(*(frames[i] for i in ids)))==1 for ids in groups.values()),
                noCrossFrameContext=len(results)-len(finite),withinExistingTolerance=sum(d<=radius+1e-10 for d in finite),
                existingToleranceAngstrom=radius,quantilesAngstrom={str(q):float(np.quantile(finite,q)) for q in [.5,.9,.95,1]} if finite else {},distanceChecks=checks),
                limits='Training-only in-sample dictionary; not leave-one-out dictionary refitting or independent-trajectory validation. Nearest contexts do not certify valid connections, full filling preservation, transferable markings, or a suitable tolerance. Same-condition provenance remains unverified.')

if __name__=='__main__':
    source,output=map(Path,sys.argv[1:]);start=time.monotonic()
    report=calibrate(json.loads(source.read_text()),lambda x:print(json.dumps(x),flush=True))
    report.update(libraryHash=sha(source),codeHash=sha(__file__),seconds=time.monotonic()-start)
    with output.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report['summary']),flush=True)
