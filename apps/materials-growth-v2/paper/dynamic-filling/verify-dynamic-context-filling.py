"""Replay dynamic latent obligations against frozen geometry and rational t."""
import hashlib,importlib.util,itertools,json,sys
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from ase.geometry import find_mic


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    coordp,motifp,interfacep,contextp,weightp,proposalp,poolp,searchp,out=map(Path,sys.argv[1:])
    coords,motifs,interfaces,inventory,learned,proposal,pool,search=[json.loads(p.read_text()) for p in [coordp,motifp,interfacep,contextp,weightp,proposalp,poolp,searchp]]
    assert search['poolHash']==sha(poolp) and pool['proposalHash']==sha(proposalp)
    for key,p in [('coordinateHash',coordp),('motifHash',motifp),('interfaceHash',interfacep),('contextHash',contextp),('weightHash',weightp)]:assert proposal[key]==sha(p)
    cc={r['id']:r for r in coords['configurations']};rr={r['id']:r for r in motifs['rows']};pp={r['configuration']:r for r in proposal['rows']}
    ss={r['configuration']:r for r in search['rows']}
    assert len(ss)==len(search['rows'])==len(pool['frames'])==len(pp)==88
    weights={(w['context'],w['port']):F(w['t']) for w in learned['weights']}
    spec=importlib.util.spec_from_file_location('paths',Path(__file__).with_name('verify-shared-interface-poses.py'))
    paths=importlib.util.module_from_spec(spec);spec.loader.exec_module(paths)
    evidence=[];complete_pools=0
    for frame in pool['frames']:
        cid=frame['configuration'];source=pp[cid];c=cc[cid];cell=np.asarray(c['cell']);inverse=np.linalg.inv(cell)
        key=lambda p:tuple(int(v)%10**12 for v in np.rint((np.asarray(p)@inverse%1)*10**12))
        expected_points={key(p) for p in c['positions']}
        expected_points.update(key(source['contacts'][ei]['position']) for ei in source.get('consistency',{}).get('contacts',[]))
        pointkeys=[tuple(p['fractionalKey']) for p in frame['points']]
        assert len(set(pointkeys))==len(pointkeys) and set(pointkeys)==expected_points
        target=np.asarray([p['position'] for p in frame['points']]);point_by_id={p['id']:i for i,p in enumerate(frame['points'])}
        assert np.array_equal(target,np.asarray(pointkeys)/10**12@cell)
        atom_points=[pointkeys.index(key(p)) for p in c['positions']]
        assert frame['required']==[f'p{i}' for i in atom_points]
        expected={};support_data={}
        for ci in source.get('consistency',{}).get('candidates',[]):
            candidate=source['candidates'][ci];k=candidate['cluster'];cluster=rr[cid]['clusters'][k];pose=cluster['fit'];context=inventory['contexts'][candidate['context']]
            R,tr=np.asarray(pose['rotationRow']),np.asarray(pose['translation'])
            assert context['baseType']==cluster['type'] and abs(np.linalg.det(R)-1)<1e-8 and np.max(np.abs(R.T@R-np.eye(3)))<1e-8
            template=motifs['types'][cluster['type']];perm=pose['permutation'];assert sorted(perm)==list(range(len(template['positions'])))
            ids=[cluster['ids'][i] for i in perm];assert template['species']==[c['species'][i] for i in ids]
            delta,_=find_mic(np.asarray(template['positions'])@R+tr-np.asarray(c['positions'])[ids],cell,pbc=True)
            assert max(np.linalg.norm(delta,axis=1))<=.15+1e-9
            domains=[]
            for pi,((mi,role),si) in enumerate(zip(context['ports'],candidate['supports'])):
                model=interfaces['models'][mi];position=np.asarray(model['anchor'+role])@R+tr;value=np.asarray(model['value'+role])@R;units=weights[candidate['context'],pi]*6
                s=source['supports'][si]
                assert s['cluster']==k and s['interface']==mi and s['role']==role and s['units']==units
                assert np.array_equal(s['position'],position) and np.array_equal(s['value'],value)
                support_data[si]=(k,position,value,units)
                delta,_=find_mic(target-position,cell,pbc=True)
                domains.append(np.flatnonzero(np.linalg.norm(delta,axis=1)<=.15+1e-9).tolist())
            assert len(candidate['supports'])==len(context['ports'])
            for mapping in itertools.product(*domains):
                totals=Counter({f'p{atom_points[i]}':F(6) for i in cluster['ids']})
                for si,j in zip(candidate['supports'],mapping):totals[f'p{j}']+=support_data[si][3]
                if max(totals.values())<=6:expected[ci,mapping]=totals
        actual=set();byid={}
        for cand in frame['candidates']:
            ci=cand['sourceCandidate'];mapping=tuple(point_by_id[p['point']] for p in cand['ports']);identity=(ci,mapping)
            assert identity in expected and identity not in actual;actual.add(identity)
            assert len(cand['t'])==len(expected[identity]) and {t['point']:F(t['value']) for t in cand['t']}==dict(expected[identity])
            assert [p['support'] for p in cand['ports']]==source['candidates'][ci]['supports']
            marks=[]
            for p in cand['ports']:
                value=support_data[p['support']][2]
                for channel,v in enumerate(value):marks.append(dict(point=p['point'],channel=str(channel),lo=v-.15-1e-9,hi=v+.15+1e-9))
            assert cand['m']==marks and cand['id'] not in byid;byid[cand['id']]=cand
        assert frame['complete'] and actual==set(expected);complete_pools+=1
        result=ss[cid]
        if result['status']!='verified-finite-point-model':continue
        assert result['marked'] and len(set(result['selected']))==len(result['selected'])
        totals=Counter();points=defaultdict(list);selected_clusters=[]
        for id in result['selected']:
            cand=byid[id];selected_clusters.append(source['candidates'][cand['sourceCandidate']]['cluster'])
            for t in cand['t']:totals[t['point']]+=F(t['value'],6)
            for p in cand['ports']:points[p['point']].append(support_data[p['support']])
        assert sorted(selected_clusters)==list(range(len(rr[cid]['clusters'])))
        assert set(frame['required'])<=set(totals) and all(v==1 for v in totals.values())
        graph=[];max_error=0.
        for point,ports in points.items():
            V=np.array([p[2] for p in ports]);error=float(max(np.linalg.norm(V-V.mean(axis=0),axis=1)));max_error=max(max_error,error)
            assert error<=.15+1e-9
            images=[]
            for k,position,value,units in ports:
                anchor=target[point_by_id[point]];delta,_=find_mic(position-anchor,cell,pbc=True)
                assert np.linalg.norm(delta)<=.15+1e-9
                shift=(anchor+delta-position)@inverse;integer=np.rint(shift).astype(int)
                assert np.max(np.abs(shift-integer))<1e-8
                images.append((k,integer))
            for k,image in images[1:]:graph.append((images[0][0],k,(image-images[0][1]).tolist()))
        proof=paths.periodic_paths(len(rr[cid]['clusters']),graph)
        evidence.append(dict(configuration=cid,requiredAtoms=len(frame['required']),activatedLatentPoints=len(set(totals)-set(frame['required'])),
                             allActiveSumsOne=True,maximumMarkBallError=max_error,periodicReachabilityPaths=len(proof)))
    report=dict(poolHash=sha(poolp),searchHash=sha(searchp),verifierHash=sha(Path(__file__)),finitePoolsReenumerated=complete_pools,positiveWitnesses=evidence,
                limits='Completeness is relative to consistency-surviving contexts and generated finite representative sites; preprocessing soundness tested separately. '
                       'Exact rational sums; approximate rigid geometry and marking balls. Atom target and motif partition/poses are given. No blind growth.')
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))


if __name__=='__main__':main()
