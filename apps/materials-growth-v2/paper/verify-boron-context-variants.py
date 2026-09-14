"""Independent context-library, candidate expansion and final point-cover checks.

Test neighbor descriptors are computed only here for post-search evaluation.
The frozen candidate builder and reference search do not receive them.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np

def distances(c):
    cell=np.array(c['cell']);p=np.array(c['positions'])@np.linalg.inv(cell)
    delta=p[:,None,:]-p[None,:,:];delta-=np.rint(delta);best=np.full(delta.shape[:2],np.inf)
    for shift in itertools.product((-1,0,1),repeat=3):
        best=np.minimum(best,np.linalg.norm((delta+shift)@cell,axis=2))
    np.fill_diagonal(best,np.inf);return best

def verify(source,training,variants,search):
    source=json.loads(Path(source).read_text())['results'];reports=[]
    for fold in range(6):
        tr=(Path(training)/str(fold)/'training-input.json').read_bytes();train=json.loads(tr)['results']
        assert train==[c for i,c in enumerate(source) if i!=fold]
        dr=(Path(training)/str(fold)/'training-dictionary.json').read_bytes();d=json.loads(dr)
        lr=(Path(variants)/f'{fold}-library.json').read_bytes();lib=json.loads(lr)
        vr=(Path(variants)/f'{fold}.json').read_bytes();v=json.loads(vr)
        assert v['libraryHash']==hashlib.sha256(lr).hexdigest()
        assert lib['trainingDictionaryHash']==hashlib.sha256(dr).hexdigest() and lib['trainingInputHash']==hashlib.sha256(tr).hexdigest()
        matrices={c['file']:distances(c) for c in train};nearest=np.concatenate([x.min(axis=1) for x in matrices.values()])
        radius=float(np.median(nearest))*1.35;assert abs(radius-lib['descriptorRadius'])<1e-9
        descriptors={key:(x<=radius).sum(axis=1).tolist() for key,x in matrices.items()}
        assert descriptors==lib['trainingDescriptors']
        expected=[set() for _ in d['types']]
        for c in d['configurations']:
            for o in c['occurrences']:expected[o['type']].add(tuple(descriptors[c['file']][o['ids'][p]] for p in o['permutation']))
        assert [sorted(x) for x in expected]==[[tuple(mark) for mark in options] for options in lib['variants']]
        # All learned variants must be offered at every supplied pose, regardless
        # of held-out neighborhood. Deduplication is by decorated point map.
        expected_candidates=set()
        for o in v['poses']:
            R=np.array(o['rotationRow']);lifted=np.array(o['liftedPositions']);perm=o['permutation']
            assert np.max(np.abs(R.T@R-np.eye(3)))<1e-9 and abs(np.linalg.det(R)-1)<1e-9
            assert sorted(perm)==[0,1,2]
            predicted=np.array(d['types'][o['type']]['positions'])@R+o['translation']
            assert max(np.linalg.norm(predicted-lifted[perm],axis=1))<=d['epsilonAngstrom']+1e-9
            shifts=(lifted-np.array(source[fold]['positions'])[o['ids']])@np.linalg.inv(source[fold]['cell'])
            assert np.max(np.abs(shifts-np.rint(shifts)))<1e-9
            for mark in lib['variants'][o['type']]:
                expected_candidates.add((o['type'],tuple(sorted(o['ids'])),tuple(sorted((str(o['ids'][p]),label) for p,label in zip(perm,mark)))))
        actual=set()
        for c in v['model']['candidates']:
            o=v['poses'][c['pose']];mark=lib['variants'][o['type']][c['variant']]
            assert json.loads(c['inventory'])==[o['type'],sorted(o['ids'])]
            assert {x['point']:x['value'] for x in c['t']}=={str(p):1 for p in o['ids']}
            assert {x['point']:x['lo'] for x in c['m']}=={str(o['ids'][p]):label for p,label in zip(o['permutation'],mark)}
            assert all(x['lo']==x['hi'] for x in c['m'])
            actual.add((o['type'],tuple(sorted(o['ids'])),tuple(sorted((x['point'],x['lo']) for x in c['m']))))
        assert len(actual)==len(v['model']['candidates']) and actual==expected_candidates
        truth=(distances(source[fold])<=radius).sum(axis=1)
        for lane in ('unmarked-collapsed','unmarked-expanded','marked'):
            artifact=json.loads((Path(search)/f'{fold}-{lane}.json').read_text());r=artifact['result'];model=artifact['model']
            assert artifact['inputHash']==hashlib.sha256(vr).hexdigest()
            wanted=[];seen=set()
            for c in v['model']['candidates']:
                if lane=='unmarked-collapsed' and c['inventory'] in seen:continue
                seen.add(c['inventory']);wanted.append({**c,'m':c['m'] if lane=='marked' else []})
            assert model=={**v['model'],'candidates':wanted}
            by_id={c['id']:c for c in model['candidates']};totals=[0]*len(truth);assigned={};inventory=set();adj=[set() for _ in truth]
            assert len(set(r['selected']))==len(r['selected'])
            for id in r['selected']:
                c=by_id[id];assert c['inventory'] not in inventory;inventory.add(c['inventory'])
                for t in c['t']:p=int(t['point']);totals[p]+=t['value'];adj[p].update(int(x['point']) for x in c['t'])
                for m in c['m']:
                    p=int(m['point']);assert p not in assigned or assigned[p]==m['lo'];assigned[p]=m['lo']
            assert all(x<=model['capacity'] for x in totals)
            if r['status']=='exact finite point-cover witness':assert all(x==model['capacity'] for x in totals)
            unseen=set(range(len(truth)));components=0
            while unseen:
                components+=1;todo=[unseen.pop()]
                while todo:
                    for p in adj[todo.pop()]&unseen:unseen.remove(p);todo.append(p)
            reports.append({'fold':fold,'lane':lane,'status':r['status'],'componentsIncludingUnfilledSingletons':components,
                'assignedPoints':len(assigned),'posthocContextMatches':int(sum(label==truth[p] for p,label in assigned.items()))})
    out={'scope':__doc__,'results':reports};print(json.dumps(out,indent=2));return out
if __name__=='__main__':
    out=verify(*sys.argv[1:5])
    if len(sys.argv)>5:
        with Path(sys.argv[5]).open('x') as f:json.dump(out,f,indent=2)
