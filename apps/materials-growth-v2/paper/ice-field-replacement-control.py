"""Fixed-witness replacement control for periodic Gaussian markings.

On every independently accepted developmental cover, replace each decoration
in turn with every fitting decoration of the same base. Geometry, pose, t,
and all other selected decorations remain fixed. At each endpoint exactly one
other tile remains. Two radius-r Hilbert balls intersect iff center distance
is at most 2r; numerical boundary uncertainty is reported, not pruned.
Rejected decorations are incompatible with this witness context, not physical
negatives, globally forbidden motifs, or proof of search acceleration.
"""
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import time
import numpy as np
from scipy.spatial.distance import cdist

def load_module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=load_module('portable','ice-portable-pairs.py');f=load_module('field','gaussian-section-markings.py')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
cover_path,dictionary_path,library_path,transfer_path,check_path,output=map(Path,sys.argv[1:])
cover,dictionary,library,transfer,check=[json.loads(x.read_text()) for x in [cover_path,dictionary_path,library_path,transfer_path,check_path]]
assert check['resultHash']==sha(transfer_path) and check['libraryHash']==transfer['libraryHash']==sha(library_path)
assert library['sourceHashes']['cover']==sha(cover_path) and library['sourceHashes']['dictionary']==sha(dictionary_path)
cv={x['id']:x for x in cover['results']};dd={x['id']:x for x in dictionary['configurations']}
fit=set(transfer['fitFrames']);allowed={x['motif'] for r in library['trainingRegistrations'] if r['id'] in fit for x in r['selected']}
bybase=defaultdict(list)
for i in sorted(allowed):bybase[library['motifs'][i]['base']].append(i)
radius=transfer['summary']['diagnosticThreshold'];bound=(2*radius)**2
def prepare(value):
    x,a,c=f.validate(value);return x,a,np.asarray(c),value['sigma']
def inner(a,b):
    x,wa,ca,sigma=a;y,wb,cb,sigma2=b;assert sigma==sigma2
    return float(np.sum(wa[:,None]*wb[None,:]*np.exp(-cdist(x,y,'sqeuclidean')/(2*sigma*sigma))*(ca[:,None]==cb[None,:])))
prepared={i:[prepare(v) for v in library['motifs'][i]['fieldM']] for i in allowed}
norms={(i,s):inner(v,v) for i,values in prepared.items() for s,v in enumerate(values)}
rows=[];start=time.monotonic();reference_checks=0;max_ref_error=0.
for case in transfer['results']:
    if not case.get('complete',False):continue
    cid=case['id'];assert case['split']=='developmental' and not dd[cid]['training']
    incident=defaultdict(list);poses={};ends={};selected={x['edge']:x for x in case['matches']}
    for edge,w in selected.items():
        o=dd[cid]['occurrences'][edge];poses[edge]=np.asarray(o['rotationRow'])
        ends[edge]=p.endpoints(o,cv[cid]['components'],cv[cid]['componentPairs'][edge])
        for side,(_,root) in enumerate(ends[edge]):incident[root].append((edge,side))
    assert all(len(v)==2 for v in incident.values())
    outcomes=[];tested=0;rejected=0;unknown=0;retained_original=0;maximum=0.;maximum_witness=None;exclusions=[]
    for edge,w in selected.items():
        partners=[]
        for side,(_,root) in enumerate(ends[edge]):
            other,other_side=next(x for x in incident[root] if x[0]!=edge)
            j=selected[other]['motif'];v=prepared[j][other_side]
            # Put the neighbor field into the candidate base frame. No
            # independent orientation optimization is performed.
            partners.append(((v[0]@poses[other]@poses[edge].T,v[1],v[2],v[3]),norms[j,other_side],j,other_side))
        for i in bybase[w['base']]:
            separated=False;uncertain=False;distances=[]
            for side,(neighbor,nn,j,js) in enumerate(partners):
                a=prepared[i][side];raw=math.fsum([norms[i,side],nn,-2*inner(a,neighbor)])
                guard=256*np.finfo(float).eps*max(1.,(sum(abs(a[1]))+sum(abs(neighbor[1])))**2)
                assert raw>=-guard
                separated|=raw-guard>bound;uncertain|=raw+guard>bound
                distances.append(math.sqrt(max(0.,raw)))
                if tested%2000==0:
                    av=library['motifs'][i]['fieldM'][side];bv=dict(vectors=neighbor[0].tolist(),amplitudes=neighbor[1].tolist(),colors=json.loads(json.dumps(library['motifs'][j]['fieldM'][js]['colors'])),sigma=neighbor[3])
                    reference=f.discrepancy(av,bv);error=abs(raw-reference['rawSquared']);assert error<=guard
                    reference_checks+=1;max_ref_error=max(max_ref_error,error)
            tested+=1
            if max(distances)>maximum:maximum=max(distances);maximum_witness=dict(edge=edge,motif=i,distances=distances)
            if separated:rejected+=1;exclusions.append(dict(edge=edge,motif=i,distances=distances))
            elif uncertain:unknown+=1
            if i==w['motif']:
                assert not separated and not uncertain;retained_original+=1
    assert retained_original==len(selected)
    row=dict(id=cid,selectedPlacements=len(selected),testedReplacementsIncludingIdentity=tested,rejected=rejected,numericallyUnknown=unknown,
             originalWitnessesRetained=retained_original,maxEndpointDistance=maximum,maxDistanceWitness=maximum_witness,exclusions=exclusions)
    rows.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ['exclusions','maxDistanceWitness']}),flush=True)
summary=dict(configurations=len(rows),radius=radius,pairSeparationThreshold=2*radius,
             **{k:sum(r[k] for r in rows) for k in ['selectedPlacements','testedReplacementsIncludingIdentity','rejected','numericallyUnknown','originalWitnessesRetained']},
             maximumEndpointDistance=max(r['maxEndpointDistance'] for r in rows),scalarReferenceChecks=reference_checks,maxSquaredReferenceError=max_ref_error)
report=dict(scope=__doc__,sourceHashes={str(x.name):sha(x) for x in [cover_path,dictionary_path,library_path,transfer_path,check_path]},
            codeHash=sha(Path(__file__)),summary=summary,results=rows,seconds=time.monotonic()-start,
            limits='Same-base decoration replacements at known poses in positive covers only. Not geometry challenges, false-positive rates, global realizability or full search. Uncertainty guard is numerical, not certified interval arithmetic.')
with output.open('x') as out:json.dump(report,out,indent=2)
print(json.dumps(summary),flush=True)
