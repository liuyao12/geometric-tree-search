"""Train-only off-atom interface locations and transported vector values.

Diagnostic on proposed motif pairs, not a complete tile decoration or search.
Each motif proposes its nearest other motif by periodic centroid distance;
the undirected union is used. Pair types are ordered by dictionary identity.
Equal types retain both endpoint roles as distinct, not quotient-equivalent.
"""
import hashlib,json,sys
from pathlib import Path
from collections import defaultdict
import numpy as np
from ase.geometry import find_mic

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fit(observations):
    # Solve coincidence under all observed poses, without pinning either
    # local anchor to an atom or to a prescribed midpoint. The null-space
    # gauge stays nearest the mean observed midpoint coordinates.
    A=np.vstack([np.hstack([o['RA'].T,-o['RB'].T]) for o in observations])
    b=np.concatenate([o['d'] for o in observations])
    prior=np.r_[np.mean([o['d']@o['RA'].T/2 for o in observations],axis=0),np.mean([-o['d']@o['RB'].T/2 for o in observations],axis=0)]
    delta,_,rank,_=np.linalg.lstsq(A,b-A@prior,rcond=None);x=prior+delta
    # A nonconstant vector target from the data avoids the vacuous all-zero
    # equality solution; this choice is an explicit representation prior.
    va=np.mean([o['d']@o['RA'].T for o in observations],axis=0)
    vb=np.mean([o['d']@o['RB'].T for o in observations],axis=0)
    return dict(anchorA=x[:3].tolist(),anchorB=x[3:].tolist(),valueA=va.tolist(),valueB=vb.tolist(),positionRank=int(rank))

def errors(model,o):
    a=np.asarray(model['anchorA'])@o['RA'];b=np.asarray(model['anchorB'])@o['RB']+o['d']
    va=np.asarray(model['valueA'])@o['RA'];vb=np.asarray(model['valueB'])@o['RB']
    return float(np.linalg.norm(a-b)),float(np.linalg.norm(va-vb)),max(float(np.linalg.norm(va-o['d'])),float(np.linalg.norm(vb-o['d'])))

def main():
    coordp,metap,motifp,out=map(Path,sys.argv[1:]);corpus=json.loads(coordp.read_text());metadata=json.loads(metap.read_text());motifs=json.loads(motifp.read_text())
    assert motifs['coordinateHash']==sha(coordp) and motifs['metadataHash']==sha(metap)
    cc={c['id']:c for c in corpus['configurations']};mm={m['id']:m for m in metadata['configurations']};observations=[]
    for r in sorted(motifs['rows'],key=lambda r:(not r['training'],r['id'])):
        if any(not p['matched'] for p in r['clusters']):continue
        c=cc[r['id']];clusters=r['clusters'];centers=np.asarray([p['fit']['translation'] for p in clusters]);n=len(clusters)
        if n<2:continue
        vectors,dist=find_mic((centers[None,:,:]-centers[:,None,:]).reshape(-1,3),np.asarray(c['cell']),pbc=c['pbc']);vectors=vectors.reshape(n,n,3);dist=dist.reshape(n,n);np.fill_diagonal(dist,np.inf)
        pairs=sorted({tuple(sorted((i,int(np.argmin(dist[i]))))) for i in range(n)})
        for i,j in pairs:
            if (clusters[i]['type'],i)>(clusters[j]['type'],j):i,j=j,i
            p,q=clusters[i],clusters[j]
            observations.append(dict(configuration=r['id'],training=r['training'],clusterA=i,clusterB=j,typeA=p['type'],typeB=q['type'],RA=np.asarray(p['fit']['rotationRow']),RB=np.asarray(q['fit']['rotationRow']),d=vectors[i,j]))
    models=[];groups=defaultdict(list);index=defaultdict(list);matches={};threshold=.30;target_error=.30
    for oi,o in enumerate(observations):
        if not o['training']:continue
        key=(o['typeA'],o['typeB']);chosen=None
        for mi in index[key]:
            proposed=fit([observations[j] for j in groups[mi]]+[o])
            if all(max(errors(proposed,observations[j])[:2])<=threshold+1e-10 and errors(proposed,observations[j])[2]<=target_error+1e-10 for j in groups[mi]+[oi]):chosen=mi;models[mi]=proposed;break
        if chosen is None:
            chosen=len(models);models.append(fit([o]));index[key].append(chosen)
        groups[chosen].append(oi);matches[oi]=chosen
    usage={mi:{observations[j]['configuration'] for j in ids} for mi,ids in groups.items()}
    for oi,o in enumerate(observations):
        if o['training']:continue
        for mi in index[(o['typeA'],o['typeB'])]:
            if len(usage[mi])<2:continue
            e=errors(models[mi],o)
            if max(e[:2])<=threshold+1e-10 and e[2]<=target_error+1e-10:matches[oi]=mi;break
    saved=[]
    for oi,o in enumerate(observations):
        row={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in o.items()};mi=matches.get(oi)
        row.update(interface=mi,errors=errors(models[mi],o) if mi is not None else None);saved.append(row)
    for mi,model in enumerate(models):
        first=observations[groups[mi][0]];model.update(typeA=first['typeA'],typeB=first['typeB'],trainingObservations=groups[mi],trainingFrames=len(usage[mi]))
    summary=[]
    for phase in sorted({m['phase'] for m in mm.values()}):
        rr=[r for r in saved if not r['training'] and mm[r['configuration']]['phase']==phase];ids={r['configuration'] for r in rr}
        summary.append(dict(phase=phase,framesWithPairs=len(ids),pairs=len(rr),matchedPairs=sum(r['interface'] is not None for r in rr),allProposedPairsMatched=sum(all(r['interface'] is not None for r in rr if r['configuration']==cid) for cid in ids)))
    report=dict(scope=__doc__,coordinateHash=sha(coordp),metadataHash=sha(metap),motifHash=sha(motifp),codeHash=sha(Path(__file__)),models=models,observations=saved,summary=summary,positionPairTolerance=threshold,valuePairTolerance=threshold,valueTargetTolerance=target_error,
        limits='Learned interface positions are free continuous variables, but each model has two prescribed endpoint roles and greedy model-count selection. Nearest-centroid pairs are a proposal prior, not a complete connection graph. Vector displacement targets are a representation prior, not physics. Single-observation models are not eligible at evaluation. Common radius-.15 ball witnesses apply only to each tested pair, not larger overlap groups. No learned t-values, full motif decoration, negative-connection certificate, reference-tree-search reconstruction, condition matching, or growth is established.')
    with out.open('x') as f:json.dump(report,f)
    print(json.dumps(dict(models=len(models),recurringModels=sum(len(v)>=2 for v in usage.values()),summary=summary)))
if __name__=='__main__':main()
