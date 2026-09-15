"""Repair failed assigned-base field prechecks using fitting bases only.

Frozen 80-frame field library, same global diagnostic radius and positional
tolerance. Search label-preserving proper Procrustes proposals for the same
observed atomic support, retaining the inferred component partition. Stop at
the first positive paired-field witness. Not complete continuous-pose search.
"""
import hashlib
import importlib.util
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.distance import cdist

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=module('portable','ice-portable-pairs.py');f=module('fields','gaussian-section-markings.py')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
args=list(sys.argv[1:]);minimax=bool(args and args[0]=='--minimax')
if minimax:args.pop(0)
pose=module('joint_pose','ice-joint-pose.py') if minimax else None
coordinates,cover_path,dictionary_path,library_path,transfer_path,output=map(Path,args)
corpus,cover,dictionary,library,transfer=[json.loads(path.read_text()) for path in [coordinates,cover_path,dictionary_path,library_path,transfer_path]]
assert transfer['libraryHash']==sha(library_path)
for key,path in [('coordinates',coordinates),('cover',cover_path),('dictionary',dictionary_path)]:assert library['sourceHashes'][key]==sha(path)
cc={c['id']:c for c in corpus['configurations']};cv={c['id']:c for c in cover['results']};dd={c['id']:c for c in dictionary['configurations']}
allowed={w['motif'] for row in library['trainingRegistrations'] if row['id'] in transfer['fitFrames'] for w in row['selected']}
bybase=defaultdict(list)
for i in sorted(allowed):bybase[library['motifs'][i]['base']].append(i)
radius=transfer['summary']['diagnosticThreshold'];epsilon=library['positionToleranceAngstrom']
def prepare(value):
    x,a,c=f.validate(value);v=(x,a,np.asarray(c),value['sigma']);return v,inner(v,v)
def inner(a,b):
    x,wa,ca,sigma=a;y,wb,cb,sigma2=b;assert sigma==sigma2
    return float(np.sum(wa[:,None]*wb[None,:]*np.exp(-cdist(x,y,'sqeuclidean')/(2*sigma*sigma))*(ca[:,None]==cb[None,:])))
def distance(a,b):
    av,aa=a;bv,bb=b;v=math.fsum([aa,bb,-2*inner(av,bv)])
    assert v>=-1e-10
    return math.sqrt(max(0.,v))
prepared={i:[prepare(value) for value in library['motifs'][i]['fieldM']] for i in allowed}
rows=[]
for case in transfer['results']:
    if case['split']!='developmental':continue
    cid=case['id'];c=cc[cid];v=cv[cid];cache={};repairs=[]
    for old in case['matches']:
        if old['radius'] is not None and old['radius']<=radius:continue
        edge=old['edge'];o=dd[cid]['occurrences'][edge];ids=o['ids'];y=p.junction.geometry.lift(c,ids)
        labels=[c['species'][i] for i in ids];permutation_cache={};witness=None;pose_count=0;bases_tested=0;refinements=0
        for base in sorted(bybase):
            b=library['baseMotifs'][base]
            if sorted(b['species'])!=sorted(labels):continue
            key=tuple(b['species'])
            if key not in permutation_cache:
                permutations=[perm for perm in itertools.permutations(range(len(ids))) if all(labels[j]==b['species'][i] for i,j in enumerate(perm))]
                permutation_cache[key]=np.asarray(permutations,dtype=int)
            perms=permutation_cache[key];x=np.asarray(b['anchors']);xc=x-x.mean(axis=0);yy=y[perms];mean=yy.mean(axis=1)
            distances=np.linalg.norm(yy[:,:,None]-yy[:,None,:],axis=3);xd=np.linalg.norm(x[:,None]-x[None,:],axis=2)
            keep=np.max(np.abs(distances-xd),axis=(1,2))<=2*epsilon+1e-10;bases_tested+=1
            if not keep.any():continue
            yy=yy[keep];pp=perms[keep];mean=mean[keep]
            u,_,vt=np.linalg.svd(np.einsum('ni,pnj->pij',xc,yy-mean[:,None,:]))
            fix=np.repeat(np.eye(3)[None],len(yy),axis=0);fix[:,2,2]=np.linalg.det(u@vt);rot=u@fix@vt
            errors=np.max(np.linalg.norm(xc[None]@rot+mean[:,None,:]-yy,axis=2),axis=1)
            translations=np.array([mean[k]-x.mean(axis=0)@rot[k] for k in range(len(rot))])
            if minimax:
                for k in np.flatnonzero(errors>epsilon+1e-10):
                    site_atoms=[ids[j] for j in pp[k]]
                    partitions=[{site_atoms[j] for j in sites} for sites in b['componentSites']]
                    expected=[set(v['components'][root]) for root in v['componentPairs'][edge]]
                    if not all(part in expected for part in partitions):continue
                    # Zero auxiliary marking arrays make this a geometry-only
                    # use of the existing optimizer. Field fits follow later.
                    zero=np.zeros((1,1,3))
                    result=pose.solve(x,yy[k],zero,zero,rot[k],translations[k],epsilon,1.)
                    refinements+=1
                    rr=np.asarray(result['rotationRow']);tt=np.asarray(result['translation'])
                    error=float(np.linalg.norm(x@rr+tt-yy[k],axis=1).max())
                    if error<=epsilon:
                        rot[k]=rr;translations[k]=tt;errors[k]=error
            for k in np.flatnonzero(errors<=epsilon+1e-10):
                perm=pp[k];rotation=rot[k];pose_count+=1
                atom_of_site=[ids[j] for j in perm];roots=[]
                for sites in b['componentSites']:
                    atoms={atom_of_site[j] for j in sites}
                    match=[root for root in v['componentPairs'][edge] if atoms==set(v['components'][root])]
                    if len(match)!=1:break
                    roots.append(match[0])
                if len(roots)!=2 or len(set(roots))!=2:continue
                queries=[]
                for root in roots:
                    if root not in cache:
                        center=p.junction.geometry.lift(c,v['components'][root]).mean(axis=0)
                        cache[root]=f.periodic_field(c['positions'],c['species'],c['cell'],center,4.,.4)
                    queries.append(prepare(f.transform(cache[root],rotation.T)))
                for i in bybase[base]:
                    d0=distance(queries[0],prepared[i][0])
                    if d0>radius:continue
                    d1=distance(queries[1],prepared[i][1])
                    if d1<=radius:
                        witness=dict(base=base,motif=i,permutation=perm.tolist(),rotationRow=rotation.tolist(),translation=translations[k].tolist(),
                                     roots=roots,maxPositionResidualAngstrom=float(errors[k]),endpointDistances=[d0,d1])
                        break
                if witness:break
            if witness:break
        repairs.append(dict(edge=edge,previousBase=old['base'],previousRadius=old['radius'],basesTested=bases_tested,geometricProposals=pose_count,minimaxRefinements=refinements,witness=witness))
    row=dict(id=cid,previousAccepted=case['accepted'],occurrences=case['occurrences'],attempted=len(repairs),rescued=sum(r['witness'] is not None for r in repairs),repairs=repairs)
    row['accepted']=row['previousAccepted']+row['rescued'];row['complete']=row['accepted']==row['occurrences'];rows.append(row)
    if repairs:print(json.dumps({k:v for k,v in row.items() if k!='repairs'}),flush=True)
summary=dict(configurations=len(rows),**{k:sum(r[k] for r in rows) for k in ['occurrences','attempted','rescued','accepted','complete']})
summary.update(minimaxEnabled=minimax,minimaxRefinements=sum(a['minimaxRefinements'] for r in rows for a in r['repairs']))
report=dict(scope=__doc__,sourceHashes={x.name:sha(x) for x in [coordinates,cover_path,dictionary_path,library_path,transfer_path]},codeHash=sha(Path(__file__)),summary=summary,results=rows,
            poseOptimizerHash=sha(Path(__file__).with_name('ice-joint-pose.py')) if minimax else None,
            limits='Positive first-witness rescue only, pending independent replay. Same atoms and component partition, no training expansion or phase input. Broad radius already shown ineffective for decoration pruning. No blind growth, full continuous-pose completeness, condition-matched provenance or new specificity claim.')
with output.open('x') as out:json.dump(report,out,indent=2)
print(json.dumps(summary),flush=True)
