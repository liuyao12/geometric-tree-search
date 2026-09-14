"""Verify every stored dead-point certificate without consulting search state.

Recompute exact totals and interval intersections from each certificate alone.
Check the complete positive-support candidate set at its required point.
Source model reconstruction is separately verified by verify-boron-face-search.py.
"""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import sys


def verify(folder,learning_path):
    lr=Path(learning_path).read_bytes();learning=json.loads(lr);results=[]
    for fold,witness in enumerate(learning['result']['selected']):
        for marked in (False,True):
            path=Path(folder)/f'{fold}-{str(marked).lower()}.json'
            raw=path.read_bytes();data=json.loads(raw);model=data['model'];r=data['result']
            assert data['learningHash']==hashlib.sha256(lr).hexdigest()
            assert data['inputHash']==learning['inputHash']
            for name,digest in data['researchSourceHashes'].items():
                assert hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()==digest
            byid={c['id']:c for c in model['candidates']};at=defaultdict(list)
            for c in model['candidates']:
                for x in c['t']:at[x['point']].append(c)
            sizes=[];hashes=set();capacity=model['capacity'];training={f'{i:06d}' for i in witness}
            for cert in data['certificates']:
                ids=set(cert['ids']);p=cert['point'];assert len(ids)==len(cert['ids']) and p in model['required']
                key=tuple(sorted(ids));assert key not in hashes;hashes.add(key)
                totals=Counter();marks={}
                for id in ids:
                    c=byid[id]
                    for x in c['t']:totals[x['point']]+=x['value']
                    for x in c['m']:
                        k=(x['point'],x.get('channel','0'));a,b=marks.get(k,(float('-inf'),float('inf')))
                        marks[k]=(max(a,x['lo']),min(b,x['hi']));assert marks[k][0]<=marks[k][1]
                assert all(0<=v<=capacity for v in totals.values()) and totals[p]<capacity
                for c in at[p]:
                    if c['id'] in ids:continue
                    if any(totals[x['point']]+x['value']>capacity for x in c['t']):continue
                    assert any((x['point'],x.get('channel','0')) in marks and
                               (x['lo']>marks[(x['point'],x.get('channel','0'))][1] or x['hi']<marks[(x['point'],x.get('channel','0'))][0])
                               for x in c['m']),f'Candidate {c["id"]} is not blocked'
                assert not ids<=training,'Excluded a verified connected training witness'
                sizes.append(len(ids))
            assert len(sizes)==r['proofDiagnostics']['certified']
            assert r['proofVersion']==len(sizes)
            results.append({'fold':fold,'marked':marked,'certificates':len(sizes),'minimumSize':min(sizes,default=None),
                            'maximumSize':max(sizes,default=None),'meanSize':sum(sizes)/len(sizes) if sizes else None,
                            'trainingWitnessPreserved':True,'runHash':hashlib.sha256(raw).hexdigest()})
    return {'scope':__doc__,'results':results,'totalCertificates':sum(r['certificates'] for r in results),
            'allStoredTrainingWitnessesPreserved':True}


if __name__=='__main__':
    out=verify(*sys.argv[1:3])
    with Path(sys.argv[3]).open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))
