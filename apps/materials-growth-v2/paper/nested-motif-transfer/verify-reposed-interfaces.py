"""Independent periodic atom registration and transported pair-value replay."""
import hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(coordp,metap,motifp,interfacep,resultp):
    coords=json.loads(coordp.read_text());meta=json.loads(metap.read_text());motifs=json.loads(motifp.read_text());interfaces=json.loads(interfacep.read_text());result=json.loads(resultp.read_text())
    for key,path in [('coordinateHash',coordp),('metadataHash',metap),('motifHash',motifp),('interfaceHash',interfacep)]:assert result[key]==sha(path)
    spec=importlib.util.spec_from_file_location('mic_checker',Path(__file__).with_name('verify-offatom-interfaces.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    cc={c['id']:c for c in coords['configurations']};mm={m['id']:m for m in meta['configurations']};rr={r['id']:r for r in motifs['rows']}
    expected={i for i,o in enumerate(interfaces['observations']) if not o['training']};assert len(result['rows'])==len(expected) and {r['observation'] for r in result['rows']}==expected
    maxatom=0.;recovered=[]
    for r in result['rows']:
        o=interfaces['observations'][r['observation']];cid=o['configuration'];c=cc[cid];assert r['configuration']==cid and r['baselineMatched']==(o['interface'] is not None)
        w=r['witness']
        if w is None:assert not r['baselineMatched'];continue
        m=interfaces['models'][w['interface']];assert m['trainingFrames']>=2 and (m['typeA'],m['typeB'])==(o['typeA'],o['typeB'])
        for suffix in ['A','B']:
            cluster=rr[cid]['clusters'][o['cluster'+suffix]];t=motifs['types'][cluster['type']];p=w['pose'+suffix];R=np.asarray(p['rotationRow']);tr=np.asarray(p['translation']);perm=p['permutation'];ids=cluster['ids']
            assert sorted(perm)==list(range(len(ids))) and [c['species'][ids[i]] for i in perm]==t['species']
            assert abs(np.linalg.det(R)-1)<1e-8 and np.max(np.abs(R.T@R-np.eye(3)))<1e-8
            P=np.asarray(t['positions'])@R+tr;Q=np.asarray(c['positions'])[np.asarray(ids)[perm]]
            errors=[np.linalg.norm(mod.mic(x-y,c['cell'])) for x,y in zip(P,Q)]
            assert max(errors)<=motifs['epsilonAngstrom']+1e-9;maxatom=max(maxatom,float(max(errors)))
        RA=np.asarray(w['poseA']['rotationRow']);RB=np.asarray(w['poseB']['rotationRow']);d=mod.mic(np.asarray(w['poseB']['translation'])-np.asarray(w['poseA']['translation']),c['cell'])
        a=np.asarray(m['anchorA'])@RA;b=np.asarray(m['anchorB'])@RB+d;u=np.asarray(m['valueA'])@RA;v=np.asarray(m['valueB'])@RB
        errors=[np.linalg.norm(a-b),np.linalg.norm(u-v),max(np.linalg.norm(u-d),np.linalg.norm(v-d))]
        assert max(abs(x-y) for x,y in zip(errors,w['errors']))<1e-8
        for e,key in zip(errors,['positionPairTolerance','valuePairTolerance','valueTargetTolerance']):assert e<=interfaces[key]+1e-9
        if not r['baselineMatched']:recovered.append(dict(configuration=cid,observation=r['observation'],interface=w['interface']))
    summary=[]
    for phase in sorted({m['phase'] for m in mm.values()}):
        group=[r for r in result['rows'] if mm[r['configuration']]['phase']==phase];ids={r['configuration'] for r in group}
        summary.append(dict(phase=phase,pairs=len(group),baselineMatched=sum(r['baselineMatched'] for r in group),refittedMatched=sum(r['witness'] is not None for r in group),frames=len(ids),allPairsMatched=sum(all(r['witness'] is not None for r in group if r['configuration']==cid) for cid in ids)))
    assert summary==result['summary']
    return dict(resultHash=sha(resultp),interfaceHash=sha(interfacep),motifHash=sha(motifp),verifierHash=sha(Path(__file__)),micVerifierHash=sha(Path(__file__).with_name('verify-offatom-interfaces.py')),summary=summary,recovered=recovered,maximumAtomErrorAngstrom=maxatom,
                limits='Checks every reported positive pair, not absence of other continuous poses, nor simultaneous choices for motifs shared by multiple pairs. No new learned values, t-filling, global configuration reconstruction, condition matching or growth claim.')
if __name__=='__main__':
    coordp,metap,motifp,interfacep,resultp,out=map(Path,sys.argv[1:]);report=verify(coordp,metap,motifp,interfacep,resultp)
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))
