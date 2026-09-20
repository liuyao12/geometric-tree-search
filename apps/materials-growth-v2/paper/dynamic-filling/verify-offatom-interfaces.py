"""Independent source-pose, pair-proposal and interface-witness replay."""
import hashlib,itertools,json,sys
from pathlib import Path
from collections import Counter
import numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mic(d,cell):
    cell=np.asarray(cell);base=d-np.round(d@np.linalg.inv(cell))@cell
    images=base+np.asarray(list(itertools.product(range(-2,3),repeat=3)))@cell
    lengths=np.linalg.norm(images,axis=1);i=int(np.argmin(lengths));best=images[i]
    assert 3*np.linalg.svd(cell,compute_uv=False)[-1]-np.linalg.norm(base)>lengths[i]+1e-8
    return best

def verify(coordp,metap,motifp,resultp):
    coords=json.loads(coordp.read_text());meta=json.loads(metap.read_text());motifs=json.loads(motifp.read_text());result=json.loads(resultp.read_text())
    assert result['coordinateHash']==sha(coordp) and result['metadataHash']==sha(metap) and result['motifHash']==sha(motifp)
    cc={c['id']:c for c in coords['configurations']};mm={m['id']:m for m in meta['configurations']};rr={r['id']:r for r in motifs['rows']}
    expected=set();pair_displacements={}
    for r in motifs['rows']:
        if any(not p['matched'] for p in r['clusters']):continue
        clusters=r['clusters'];n=len(clusters)
        if n<2:continue
        c=cc[r['id']];assert all(c['pbc']);centers=[np.asarray(p['fit']['translation']) for p in clusters];dist=np.full((n,n),np.inf)
        for i in range(n):
            for j in range(n):
                if i==j:continue
                d=mic(centers[j]-centers[i],c['cell']);pair_displacements[r['id'],i,j]=d;dist[i,j]=np.linalg.norm(d)
        for i in range(n):
            j=int(np.argmin(dist[i]));a,b=sorted((i,j),key=lambda k:(clusters[k]['type'],k));expected.add((r['id'],a,b))
    observed=[(o['configuration'],o['clusterA'],o['clusterB']) for o in result['observations']]
    assert len(observed)==len(set(observed)) and set(observed)==expected
    maxima=np.zeros(3);radii=[];offatom=[];training_members={}
    for mi,m in enumerate(result['models']):
        ids=m['trainingObservations'];assert len(ids)==len(set(ids)) and ids
        obs=[result['observations'][i] for i in ids];assert all(o['training'] and o['interface']==mi for o in obs)
        frames={o['configuration'] for o in obs};assert len(frames)==m['trainingFrames'];training_members[mi]=set(ids)
        assert all(o['typeA']==m['typeA'] and o['typeB']==m['typeB'] for o in obs)
        for suffix in ['A','B']:
            anchor=np.asarray(m['anchor'+suffix]);radii.append(float(np.linalg.norm(anchor)))
            cloud=np.asarray(motifs['types'][m['type'+suffix]]['positions']);offatom.append(float(np.min(np.linalg.norm(cloud-anchor,axis=1))))
    for oi,o in enumerate(result['observations']):
        cid=o['configuration'];r=rr[cid];assert o['training']==(mm[cid]['split']=='train')==r['training']
        a=r['clusters'][o['clusterA']];b=r['clusters'][o['clusterB']]
        assert o['typeA']==a['type'] and o['typeB']==b['type']
        RA=np.asarray(a['fit']['rotationRow']);RB=np.asarray(b['fit']['rotationRow'])
        assert np.array_equal(RA,o['RA']) and np.array_equal(RB,o['RB'])
        d=pair_displacements[cid,o['clusterA'],o['clusterB']];assert np.linalg.norm(d-o['d'])<1e-8
        mi=o['interface']
        if mi is None:assert not o['training'] and o['errors'] is None;continue
        m=result['models'][mi];assert (m['typeA'],m['typeB'])==(o['typeA'],o['typeB'])
        if o['training']:assert oi in training_members[mi]
        else:assert m['trainingFrames']>=2
        p=np.asarray(m['anchorA'])@RA;q=np.asarray(m['anchorB'])@RB+d
        u=np.asarray(m['valueA'])@RA;v=np.asarray(m['valueB'])@RB
        errors=np.array([np.linalg.norm(p-q),np.linalg.norm(u-v),max(np.linalg.norm(u-d),np.linalg.norm(v-d))]);maxima=np.maximum(maxima,errors)
        assert np.max(np.abs(errors-o['errors']))<1e-8
        assert errors[0]<=result['positionPairTolerance']+1e-9 and errors[1]<=result['valuePairTolerance']+1e-9 and errors[2]<=result['valueTargetTolerance']+1e-9
        # A common witness must exist, not just a verbal 'close' label.
        assert max(np.linalg.norm((p+q)/2-p),np.linalg.norm((p+q)/2-q))<=result['positionPairTolerance']/2+1e-9
        assert max(np.linalg.norm((u+v)/2-u),np.linalg.norm((u+v)/2-v))<=result['valuePairTolerance']/2+1e-9
    summary=[];failure_counts=Counter()
    for o in result['observations']:
        if o['training']:continue
        candidates=[m for m in result['models'] if (m['typeA'],m['typeB'])==(o['typeA'],o['typeB'])]
        recurring=[m for m in candidates if m['trainingFrames']>=2]
        if not candidates:failure_counts['unseenTypePair']+=1;continue
        if not recurring:failure_counts['noRecurringInterface']+=1;continue
        RA=np.asarray(o['RA']);RB=np.asarray(o['RB']);d=np.asarray(o['d']);positional=[];agree=[];faithful=[]
        for m in recurring:
            p=np.asarray(m['anchorA'])@RA;q=np.asarray(m['anchorB'])@RB+d
            u=np.asarray(m['valueA'])@RA;v=np.asarray(m['valueB'])@RB
            if np.linalg.norm(p-q)>result['positionPairTolerance']+1e-9:continue
            positional.append(m)
            if np.linalg.norm(u-v)>result['valuePairTolerance']+1e-9:continue
            agree.append(m)
            if max(np.linalg.norm(u-d),np.linalg.norm(v-d))<=result['valueTargetTolerance']+1e-9:faithful.append(m)
        assert bool(faithful)==(o['interface'] is not None)
        failure_counts['matched' if faithful else 'valueTargetPriorFails' if agree else 'markingAgreementFails' if positional else 'anchorCoincidenceFails']+=1
    for phase in sorted({m['phase'] for m in mm.values()}):
        obs=[o for o in result['observations'] if not o['training'] and mm[o['configuration']]['phase']==phase];ids={o['configuration'] for o in obs}
        summary.append(dict(phase=phase,framesWithPairs=len(ids),pairs=len(obs),matchedPairs=sum(o['interface'] is not None for o in obs),allProposedPairsMatched=sum(all(o['interface'] is not None for o in obs if o['configuration']==cid) for cid in ids)))
    assert summary==result['summary']
    return dict(resultHash=sha(resultp),coordinateHash=sha(coordp),metadataHash=sha(metap),motifHash=sha(motifp),verifierHash=sha(Path(__file__)),summary=summary,frozenModelFailureCounts=dict(failure_counts),models=len(result['models']),recurringModels=sum(m['trainingFrames']>=2 for m in result['models']),anchorCount=len(radii),anchorsMoreThan015FromTemplateAtoms=sum(d>.15 for d in offatom),anchorRadiusQuantiles=dict(zip(['min','median','p90','p99','max'],map(float,np.quantile(radii,[0,.5,.9,.99,1])))),maximumVerifiedErrors=maxima.tolist(),
                limits='Positive pair-witness replay only. Unknown pairs are not proved inadmissible; missed overlaps impose no GCTS marking restriction. Independent minimum-image enumeration is certified for these checked cells. Base motif pose correctness is a prerequisite checked separately. Locality, learned t-values, globally consistent multi-way overlaps, full tile interfaces and condition matching remain unproved.')
if __name__=='__main__':
    coordp,metap,motifp,resultp,out=map(Path,sys.argv[1:]);report=verify(coordp,metap,motifp,resultp)
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))
