"""Learn frozen off-atom interfaces on periodic Voronoi candidate pairs.

Explicit lattice shifts distinguish different images and self-image edges.
Neighbor candidates are geometric proposals; no chemical rules are used.
This fits interfaces, not complete t/m-decorated tiles or a growth engine.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
from collections import defaultdict
import numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    coordp,metap,motifp,out=map(Path,sys.argv[1:]);coords=json.loads(coordp.read_text());meta=json.loads(metap.read_text());motifs=json.loads(motifp.read_text());assert motifs['coordinateHash']==sha(coordp) and motifs['metadataHash']==sha(metap)
    periodic=load('periodic','periodic-interface-proposals.py');learner=load('learner','learn-offatom-interfaces.py')
    cc={c['id']:c for c in coords['configurations']};mm={m['id']:m for m in meta['configurations']};observations=[];frames=[]
    for fi,r in enumerate(sorted(motifs['rows'],key=lambda r:(not r['training'],r['id']))):
        cid=r['id'];c=cc[cid];clusters=r['clusters']
        if any(not p['matched'] for p in clusters):frames.append(dict(configuration=cid,training=r['training'],status='unmapped-motif'));continue
        assert all(c['pbc']);cell=np.asarray(c['cell']);centers=np.asarray([p['fit']['translation'] for p in clusters]);wraps=np.floor(centers@np.linalg.inv(cell)).astype(int)
        graph=periodic.propose(centers,cell);ids=[];raw_edges=[]
        for i,j,s in graph['edges']:
            # Convert wrapped-centroid image labels to the actual pose gauge.
            shift=np.asarray(s,dtype=int)-wraps[j]+wraps[i]
            if (clusters[i]['type'],i)>(clusters[j]['type'],j):i,j=j,i;shift=-shift
            d=centers[j]+shift@cell-centers[i];p,q=clusters[i],clusters[j]
            ids.append(len(observations));raw_edges.append((i,j,shift.tolist()))
            observations.append(dict(configuration=cid,training=r['training'],clusterA=i,clusterB=j,typeA=p['type'],typeB=q['type'],imageShift=shift.tolist(),RA=np.asarray(p['fit']['rotationRow']),RB=np.asarray(q['fit']['rotationRow']),d=d))
        frames.append(dict(configuration=cid,training=r['training'],status='admitted',motifs=len(clusters),observations=ids,edges=raw_edges,imageShell=graph['shell'],imageBoundMargin=graph['imageBoundMargin']))
        if fi%80==0:print(json.dumps(dict(proposedFrames=fi+1,observations=len(observations))),flush=True)
    models=[];groups=defaultdict(list);index=defaultdict(list);matches={};tol=.30
    for oi,o in enumerate(observations):
        if not o['training']:continue
        key=(o['typeA'],o['typeB']);chosen=None
        for mi in index[key]:
            first=observations[groups[mi][0]]
            # Necessary bound for the unchanged displacement-target prior:
            # one vector cannot be within .30 of two points > .60 apart.
            if any(np.linalg.norm(o['d']@o[k].T-first['d']@first[k].T)>2*tol+1e-9 for k in ['RA','RB']):continue
            obs=[observations[j] for j in groups[mi]]+[o];proposed=learner.fit(obs)
            if all(max(learner.errors(proposed,p))<=tol+1e-10 for p in obs):chosen=mi;models[mi]=proposed;break
        if chosen is None:chosen=len(models);models.append(learner.fit([o]));index[key].append(chosen)
        groups[chosen].append(oi);matches[oi]=chosen
        if oi%1000==0:print(json.dumps(dict(trainingObservations=oi+1,models=len(models))),flush=True)
    usage={mi:{observations[j]['configuration'] for j in ids} for mi,ids in groups.items()}
    for oi,o in enumerate(observations):
        if o['training']:continue
        for mi in index[(o['typeA'],o['typeB'])]:
            if len(usage[mi])>=2 and max(learner.errors(models[mi],o))<=tol+1e-10:matches[oi]=mi;break
    for mi,model in enumerate(models):
        first=observations[groups[mi][0]];model.update(typeA=first['typeA'],typeB=first['typeB'],trainingObservations=groups[mi],trainingFrames=len(usage[mi]))
    saved=[]
    for oi,o in enumerate(observations):
        mi=matches.get(oi);row={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in o.items()};row.update(interface=mi,errors=learner.errors(models[mi],o) if mi is not None else None);saved.append(row)
    for frame in frames:
        if frame['status']!='admitted':continue
        selected=[edge for oi,edge in zip(frame['observations'],frame['edges']) if oi in matches and len(usage[matches[oi]])>=2]
        frame['recurringMatchedEdges']=len(selected);frame['matchedGraph']=periodic.graph_audit(frame['motifs'],selected)
    summary=[]
    for phase in sorted({m['phase'] for m in mm.values()}):
        for training in [True,False]:
            allframes=[r for r in frames if r['training']==training and mm[r['configuration']]['phase']==phase];good=[r for r in allframes if r['status']=='admitted']
            summary.append(dict(phase=phase,training=training,frames=len(allframes),admitted=len(good),proposedEdges=sum(len(r['edges']) for r in good),recurringMatchedEdges=sum(r['recurringMatchedEdges'] for r in good),connectedMatchedPeriodicGraphs=sum(r['matchedGraph']['connectedPeriodicLift'] for r in good)))
    report=dict(scope=__doc__,coordinateHash=sha(coordp),metadataHash=sha(metap),motifHash=sha(motifp),codeHash=sha(Path(__file__)),learnerHash=sha(Path(__file__).with_name('learn-offatom-interfaces.py')),proposalHash=sha(Path(__file__).with_name('periodic-interface-proposals.py')),models=models,observations=saved,frames=frames,summary=summary,positionPairTolerance=tol,valuePairTolerance=tol,valueTargetTolerance=tol,
                limits='Original atom-valid motif poses, no continuous re-registration in this lane. Positive pair coincidences with explicit periodic images; cross-interface collisions and multi-way marking agreement remain unaudited. Per-pair endpoint roles are prescribed, model count split greedily, no learned t-values. Connectivity of the matched abstract graph is not a GCTS filling certificate. No identical-condition provenance or blind growth claim.')
    with out.open('x') as f:json.dump(report,f)
    print(json.dumps(dict(models=len(models),recurringModels=sum(len(v)>=2 for v in usage.values()),summary=summary)),flush=True)
if __name__=='__main__':main()
