"""Independent positive-witness replay, not nearest-neighbor optimality proof.

Rebuilds periodic query fields without importing producer code. Evaluates each
RKHS discrepancy as one signed quadratic form in world coordinates, rather
than the producer's three cached inner products in the base frame.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import numpy as np

coordinates,cover_path,dictionary_path,selection_path,library_path,result_path,output=map(Path,sys.argv[1:])
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
corpus,cover,dictionary,selection,library,result=map(read,[coordinates,cover_path,dictionary_path,selection_path,library_path,result_path])
assert result['libraryHash']==sha(library_path)
for key,path in [('coordinates',coordinates),('cover',cover_path),('dictionary',dictionary_path),('selection',selection_path)]:assert library['sourceHashes'][key]==sha(path)
cc={x['id']:x for x in corpus['configurations']};cv={x['id']:x for x in cover['results']};dd={x['id']:x for x in dictionary['configurations']};ss={x['id']:x for x in selection['results']}
fit={f'c{off+i:05d}' for off in [0,500,1000,1500] for i in range(20)}
cal=[f'c{off+i:05d}' for off in [0,500,1000,1500] for i in range(20,25)]
dev=[f'c{off+i:05d}' for off in [400,900,1400,1900] for i in range(25)]
assert result['fitFrames']==sorted(fit) and result['calibrationFrames']==cal and result['developmentalFrames']==dev
assert all(dd[c]['training'] for c in fit|set(cal)) and all(not dd[c]['training'] for c in dev)
allowed={p['motif'] for r in library['trainingRegistrations'] if r['id'] in fit for p in r['selected']}
assert len(allowed)==result['summary']['fitDecorations']
allowed_bases={library['motifs'][i]['base'] for i in allowed}
base_keys={json.dumps([b['pairType'],b['componentSites']]):i for i,b in enumerate(library['baseMotifs'])}
images=np.array(list(itertools.product(range(-4,5),repeat=3)));short=np.array(list(itertools.product(range(-2,3),repeat=3)))
R=library['supportRadiusAngstrom'];sigma=library['kernelWidthAngstrom'];assert R==4 and sigma==.4 and library['capacity']==2
checked=0;max_squared_error=0.;verified=[];cal_radii=[]
for row,cid in zip(result['results'],cal+dev,strict=True):
    assert row['id']==cid and row['split']==('calibration' if cid in cal else 'developmental')
    c=cc[cid];v=cv[cid];cell=np.asarray(c['cell']);positions=np.asarray(c['positions']);inv=np.linalg.inv(cell);smin=np.linalg.svd(cell,compute_uv=False)[-1]
    assert all(c.get('pbc',[True]*3));shifts=images@cell;shortshifts=short@cell
    def mic(d):
        wrapped=d-np.round(d@inv)@cell;options=wrapped+shortshifts
        chosen=options[np.argmin(np.linalg.norm(options,axis=1))]
        assert 3*smin-np.linalg.norm(wrapped)>np.linalg.norm(chosen)+1e-10
        return chosen
    fields={}
    for root,ids in enumerate(v['components']):
        x=np.array([positions[ids[0]]+mic(positions[i]-positions[ids[0]]) for i in ids])
        for a,i in enumerate(ids):
            for b,j in enumerate(ids):assert np.linalg.norm(x[b]-x[a]-mic(positions[j]-positions[i]))<1e-9
        center=x.mean(axis=0);fractional=(positions-center)@inv;fractional-=np.round(fractional);wrapped=fractional@cell
        assert 5*smin-max(np.linalg.norm(wrapped,axis=1))>R+1e-10
        vectors=[];labels=[];weights=[]
        for shift in shifts:
            points=wrapped+shift
            for i in np.flatnonzero(np.linalg.norm(points,axis=1)<R):
                vectors.append(points[i]);labels.append(c['species'][i]);weights.append((1-float(np.dot(points[i],points[i]))/R**2)**3)
        fields[root]=(np.asarray(vectors),np.asarray(labels),np.asarray(weights))
    total=np.zeros(len(positions),dtype=int);root_counts={};accepted=0;missing=0;finite=[]
    assert [r['edge'] for r in row['matches']]==ss[cid]['selected']
    assert len({r['edge'] for r in row['matches']})==len(row['matches'])
    for witness in row['matches']:
        edge=witness['edge'];o=dd[cid]['occurrences'][edge];assert o['matched']
        total[o['ids']]+=1;atom_of_site=[o['ids'][p] for p in o['permutation']]
        ends=sorted((sorted(i for i,atom in enumerate(atom_of_site) if atom in v['components'][root]),root) for root in v['componentPairs'][edge])
        key=json.dumps([o['type'],[sites for sites,_ in ends]]);base=base_keys.get(key);assert base==witness['base']
        for _,root in ends:root_counts[root]=root_counts.get(root,0)+1
        if witness['motif'] is None:
            assert base not in allowed_bases and witness['radius'] is None;missing+=1;continue
        assert witness['motif'] in allowed
        motif=library['motifs'][witness['motif']];assert motif['base']==base
        rotation=np.asarray(o['rotationRow']);assert np.max(np.abs(rotation.T@rotation-np.eye(3)))<1e-10 and abs(np.linalg.det(rotation)-1)<1e-10
        distances=[]
        for side,(_,root) in enumerate(ends):
            value=motif['fieldM'][side];assert value['sigma']==sigma
            points,labels,weights=fields[root]
            x=np.vstack([np.asarray(value['vectors'])@rotation,points]);w=np.r_[value['amplitudes'],-weights];colors=np.r_[value['colors'],labels]
            square=np.sum((x[:,None,:]-x[None,:,:])**2,axis=2)
            terms=w[:,None]*w[None,:]*np.exp(-square/(2*sigma*sigma))*(colors[:,None]==colors[None,:])
            squared=math.fsum(map(float,terms.ravel()))
            guard=256*np.finfo(float).eps*max(1.,sum(abs(w))**2)
            assert squared>=-guard
            error=abs(squared-witness['endpointDistances'][side]**2);assert error<max(guard,1e-10)
            max_squared_error=max(max_squared_error,error);distances.append(math.sqrt(max(0.,squared)));checked+=1
        assert abs(max(distances)-witness['radius'])<1e-8
        finite.append(witness['radius'])
        if cid in cal:cal_radii.append(witness['radius'])
        elif max(distances)<=result['summary']['diagnosticThreshold']:accepted+=1
    assert np.all(total==2) and len(root_counts)==len(v['components']) and all(n==2 for n in root_counts.values())
    assert missing==row['missingFitBase'] and row['occurrences']==len(row['matches'])
    assert row['requiredRadius']==(max(finite) if finite and not missing else None)
    if cid in dev:
        assert accepted==row['accepted'] and (accepted==len(row['matches']))==row['complete']
    verified.append(dict(id=cid,split=row['split'],assignments=2*len(finite),missing=missing,accepted=accepted if cid in dev else None,complete=row.get('complete')))
    print(json.dumps(verified[-1]),flush=True)
assert abs(max(cal_radii)+1e-8-result['summary']['diagnosticThreshold'])<1e-12
assert sum(r['complete'] for r in verified if r['split']=='developmental')==result['summary']['developmentalComplete']
report=dict(scope=__doc__,resultHash=sha(result_path),libraryHash=sha(library_path),verifierHash=sha(Path(__file__)),
            checkedEndpointDistances=checked,maxSquaredDistanceDiscrepancy=max_squared_error,verifiedConfigurations=len(verified),results=verified,
            limits='Positive witnesses independently verified; nearest-neighbor optimality not re-proved. Missing assigned bases checked exactly within frozen fit library. Threshold protocol replayed but no statistical guarantee, specificity, physics, search or blind-growth claim.')
with output.open('x') as out:json.dump(report,out,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='results'}),flush=True)
