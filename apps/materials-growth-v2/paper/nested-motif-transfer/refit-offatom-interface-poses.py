"""Frozen-interface transfer under additional atom-valid motif registrations.

No refitted anchors/values/types, no wider tolerances, no swapped endpoint
roles. Original poses remain explicit. Each endpoint's rotation transports
its atoms, anchor and vector value together.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
from collections import Counter
import numpy as np
from ase import Atoms
from ase.geometry import find_mic

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    coordp,metap,motifp,interfacep,out=map(Path,sys.argv[1:]);coords=json.loads(coordp.read_text());meta=json.loads(metap.read_text());motifs=json.loads(motifp.read_text());interfaces=json.loads(interfacep.read_text())
    assert interfaces['coordinateHash']==sha(coordp) and interfaces['metadataHash']==sha(metap) and interfaces['motifHash']==sha(motifp)
    spec=importlib.util.spec_from_file_location('enumerator',Path(__file__).with_name('enumerate-rigid-proposals.py'));enum=importlib.util.module_from_spec(spec);spec.loader.exec_module(enum)
    cc={c['id']:c for c in coords['configurations']};mm={m['id']:m for m in meta['configurations']};rr={r['id']:r for r in motifs['rows']};cache={};distance_cache={};rows=[];stats=[]
    def poses(cid,k):
        key=(cid,k)
        if key in cache:return cache[key]
        c=cc[cid];p=rr[cid]['clusters'][k];t=motifs['types'][p['type']];ids=p['ids']
        if cid not in distance_cache:
            a=Atoms(c['species'],positions=c['positions'],cell=c['cell'],pbc=c['pbc']);v=a.get_all_distances(mic=True,vector=True);distance_cache[cid]=(v,np.linalg.norm(v,axis=2))
        vectors,dist=distance_cache[cid];lifted={ids[0]:np.asarray(c['positions'][ids[0]])};pending=set(ids[1:])
        while pending:
            _,u,v=min((dist[u,v],u,v) for u in lifted for v in pending);lifted[v]=lifted[u]+vectors[u,v];pending.remove(v)
        target=np.asarray([lifted[i] for i in ids]);found,s=enum.enumerate_poses(t['positions'],target,t['species'],motifs['epsilonAngstrom'])
        # Preserve decorated identities; do not quotient different maps.
        result=[p['fit']]+found;cache[key]=result;stats.append(dict(configuration=cid,cluster=k,poses=len(result),**s));return result
    for oi,o in enumerate(interfaces['observations']):
        if o['training']:continue
        cid=o['configuration'];c=cc[cid];a=poses(cid,o['clusterA']);b=poses(cid,o['clusterB']);witness=None;tested=0
        for mi,m in enumerate(interfaces['models']):
            if m['trainingFrames']<2 or (m['typeA'],m['typeB'])!=(o['typeA'],o['typeB']):continue
            for pa in a:
                for pb in b:
                    tested+=1;RA=np.asarray(pa['rotationRow']);RB=np.asarray(pb['rotationRow']);d,_=find_mic(np.asarray(pb['translation'])-np.asarray(pa['translation']),np.asarray(c['cell']),pbc=c['pbc'])
                    x=np.asarray(m['anchorA'])@RA;y=np.asarray(m['anchorB'])@RB+d;u=np.asarray(m['valueA'])@RA;v=np.asarray(m['valueB'])@RB
                    errors=[float(np.linalg.norm(x-y)),float(np.linalg.norm(u-v)),float(max(np.linalg.norm(u-d),np.linalg.norm(v-d)))]
                    if all(e<=interfaces[k]+1e-10 for e,k in zip(errors,['positionPairTolerance','valuePairTolerance','valueTargetTolerance'])):
                        witness=dict(interface=mi,poseA=pa,poseB=pb,errors=errors);break
                if witness:break
            if witness:break
        assert o['interface'] is None or witness is not None
        rows.append(dict(observation=oi,configuration=cid,baselineMatched=o['interface'] is not None,witness=witness,testedCombinations=tested))
    summary=[]
    for phase in sorted({m['phase'] for m in mm.values()}):
        group=[r for r in rows if mm[r['configuration']]['phase']==phase];ids={r['configuration'] for r in group}
        summary.append(dict(phase=phase,pairs=len(group),baselineMatched=sum(r['baselineMatched'] for r in group),refittedMatched=sum(r['witness'] is not None for r in group),frames=len(ids),allPairsMatched=sum(all(r['witness'] is not None for r in group if r['configuration']==cid) for cid in ids)))
    report=dict(scope=__doc__,coordinateHash=sha(coordp),metadataHash=sha(metap),motifHash=sha(motifp),interfaceHash=sha(interfacep),codeHash=sha(Path(__file__)),enumeratorHash=sha(Path(__file__).with_name('enumerate-rigid-proposals.py')),rows=rows,registrationStats=stats,summary=summary,
                limits='Pairwise positive registrations only, not simultaneous orientation consistency for motifs shared across pairs. Model types and endpoint roles remain fixed. One Kabsch pose per bounded correspondence does not exhaust continuous tolerance-feasible rotations; collinear clouds leave unsampled freedom. No t-learning, global filling, negative connection proof, condition matching or material growth.')
    with out.open('x') as f:json.dump(report,f)
    print(json.dumps(dict(summary=summary,registeredClusters=len(stats),maxPoses=max(s['poses'] for s in stats),budgetStops=sum(s['truncated'] for s in stats),rankCounts=dict(Counter(s['templateRank'] for s in stats)))))
if __name__=='__main__':main()
