"""Independent explicit-image, frozen-pose and pair-marking replay."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def verify(coordp,metap,motifp,resultp):
    result=json.loads(resultp.read_text());coords=json.loads(coordp.read_text());meta=json.loads(metap.read_text());motifs=json.loads(motifp.read_text())
    for key,path in [('coordinateHash',coordp),('metadataHash',metap),('motifHash',motifp)]:assert result[key]==sha(path)
    for key in ['positionPairTolerance','valuePairTolerance','valueTargetTolerance']:assert result[key]==.30
    # Recheck the source-derived motif geometry; do not trust the fit labels.
    base=load('base','verify-nested-recurring-motifs.py');base.verify(coordp,metap,motifp)
    periodic=load('periodic','periodic-interface-proposals.py');paths=load('paths','verify-shared-interface-poses.py')
    cc={c['id']:c for c in coords['configurations']};mm={m['id']:m for m in meta['configurations']};rr={r['id']:r for r in motifs['rows']}
    assert len(result['frames'])==len(rr) and {f['configuration'] for f in result['frames']}==set(rr)
    usage=defaultdict(set);owned=set();maximum=np.zeros(3);self_images=0;seen=set();frame_pairs=defaultdict(list)
    for mi,m in enumerate(result['models']):
        ids=m['trainingObservations'];assert ids and len(ids)==len(set(ids)) and not owned.intersection(ids);owned.update(ids)
        for oi in ids:
            o=result['observations'][oi];assert o['training'] and o['interface']==mi
            assert (m['typeA'],m['typeB'])==(o['typeA'],o['typeB']);usage[mi].add(o['configuration'])
        assert len(usage[mi])==m['trainingFrames']
    assert owned=={i for i,o in enumerate(result['observations']) if o['training']}
    for oi,o in enumerate(result['observations']):
        cid=o['configuration'];c=cc[cid];clusters=rr[cid]['clusters'];a=o['clusterA'];b=o['clusterB'];s=o['imageShift']
        assert len(s)==3 and all(isinstance(v,int) for v in s) and (a!=b or any(s))
        key=(cid,a,b,*s);assert key not in seen;seen.add(key);self_images+=a==b
        assert o['training']==rr[cid]['training']==(mm[cid]['split']=='train')
        assert o['typeA']==clusters[a]['type'] and o['typeB']==clusters[b]['type']
        pa=clusters[a]['fit'];pb=clusters[b]['fit'];RA=np.asarray(pa['rotationRow']);RB=np.asarray(pb['rotationRow']);assert np.array_equal(RA,o['RA']) and np.array_equal(RB,o['RB'])
        # Do NOT minimum-image this displacement: different periodic images
        # of the same pair, including self-pairs, are distinct interfaces.
        d=np.asarray(pb['translation'])+np.asarray(s)@c['cell']-pa['translation'];assert np.linalg.norm(d-o['d'])<1e-8
        frame_pairs[cid].append(oi);mi=o['interface']
        if mi is None:assert not o['training'] and o['errors'] is None;continue
        m=result['models'][mi];assert (m['typeA'],m['typeB'])==(o['typeA'],o['typeB'])
        if not o['training']:assert m['trainingFrames']>=2
        x=np.asarray(m['anchorA'])@RA;y=np.asarray(m['anchorB'])@RB+d;u=np.asarray(m['valueA'])@RA;v=np.asarray(m['valueB'])@RB
        errors=np.array([np.linalg.norm(x-y),np.linalg.norm(u-v),max(np.linalg.norm(u-d),np.linalg.norm(v-d))]);assert np.max(np.abs(errors-o['errors']))<1e-8 and max(errors)<=.30+1e-9;maximum=np.maximum(maximum,errors)
        assert max(np.linalg.norm((x+y)/2-x),np.linalg.norm((x+y)/2-y))<=.15+1e-9
        assert max(np.linalg.norm((u+v)/2-u),np.linalg.norm((u+v)/2-v))<=.15+1e-9
    positive_graphs=[];checked_frames=[]
    for frame in result['frames']:
        cid=frame['configuration'];r=rr[cid];c=cc[cid];assert frame['training']==r['training']
        if any(not p['matched'] for p in r['clusters']):assert frame['status']=='unmapped-motif' and cid not in frame_pairs;continue
        assert frame['status']=='admitted' and set(frame['observations'])==set(frame_pairs[cid]) and len(frame['observations'])==len(frame_pairs[cid])
        centers=np.asarray([p['fit']['translation'] for p in r['clusters']]);wraps=np.floor(centers@np.linalg.inv(c['cell'])).astype(int);expected=periodic.propose(centers,c['cell']);canonical=set();accepted=[]
        assert len(frame['edges'])==len(frame['observations'])
        for oi,edge in zip(frame['observations'],frame['edges']):
            o=result['observations'][oi];a,b,s=edge;assert edge==[o['clusterA'],o['clusterB'],o['imageShift']]
            shift=np.asarray(s)+wraps[b]-wraps[a];canonical.add(min((a,b,*shift),(b,a,*(-shift))))
            if o['interface'] is not None and len(usage[o['interface']])>=2:accepted.append(edge)
        assert canonical=={(a,b,*s) for a,b,s in expected['edges']}
        assert len(accepted)==frame['recurringMatchedEdges'];graph=periodic.graph_audit(frame['motifs'],accepted);assert graph==frame['matchedGraph']
        if graph['connectedPeriodicLift']:
            proof=paths.periodic_paths(frame['motifs'],accepted,bound=6);positive_graphs.append(dict(configuration=cid,training=r['training'],maxPathSteps=max(p['steps'] for p in proof)))
        checked_frames.append(frame)
    summary=[]
    for phase in sorted({m['phase'] for m in mm.values()}):
        for training in [True,False]:
            group=[r for r in result['frames'] if r['training']==training and mm[r['configuration']]['phase']==phase];good=[r for r in group if r['status']=='admitted']
            summary.append(dict(phase=phase,training=training,frames=len(group),admitted=len(good),proposedEdges=sum(len(r['edges']) for r in good),recurringMatchedEdges=sum(r['recurringMatchedEdges'] for r in good),connectedMatchedPeriodicGraphs=sum(r['matchedGraph']['connectedPeriodicLift'] for r in good)))
    assert summary==result['summary']
    cross_phase=sum(len({mm[c]['phase'] for c in frames})>1 for frames in usage.values())
    return dict(resultHash=sha(resultp),coordinateHash=sha(coordp),metadataHash=sha(metap),motifHash=sha(motifp),verifierHash=sha(Path(__file__)),summary=summary,models=len(result['models']),recurringModels=sum(len(v)>=2 for v in usage.values()),crossPhaseModels=cross_phase,observations=len(result['observations']),selfImageObservations=self_images,maximumPairErrors=maximum.tolist(),positiveGraphProofs=positive_graphs,
                limits='Replays source motif geometry, every claimed explicit-image pair witness, training-only recurrence, and constructive paths in positive matched graphs. Numerical Voronoi regeneration is a consistency check, not an independent exact tessellation proof. Does not verify missing-pair impossibility, all cross-interface coincidences, common values for multi-way overlaps, learned t-values, GCTS filling, condition matching or blind growth.')
if __name__=='__main__':
    coordp,metap,motifp,resultp,out=map(Path,sys.argv[1:]);report=verify(coordp,metap,motifp,resultp)
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='positiveGraphProofs'}))
