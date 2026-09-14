"""Independent frozen-pool, rational deficit, and selected integer cover replay."""
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

spec=importlib.util.spec_from_file_location('geometry',Path(__file__).with_name('verify-boron-triples.py'))
geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)

def cover(c,selected,k):
    assert len(selected)==len(set(selected))
    totals=[0]*c['atoms'];adj=[set() for _ in totals];identities=set()
    for i in selected:
        assert 0<=i<len(c['occurrences'])
        o=c['occurrences'][i];ids=o['ids'];key=(o['type'],tuple(sorted(ids)))
        assert key not in identities;identities.add(key)
        for p in ids:totals[p]+=1;adj[p].update(ids)
    assert all(v==k for v in totals)
    unseen=set(range(c['atoms']));components=0
    while unseen:
        todo=[unseen.pop()];components+=1
        while todo:
            for p in adj[todo.pop()]&unseen:unseen.remove(p);todo.append(p)
    return components

def verify(source,training,pools,selected):
    raw=Path(source).read_bytes();configs=json.loads(raw)['results'];summary=[]
    for i in range(6):
        frozen=(Path(training)/str(i)/'training-dictionary.json').read_bytes();d=json.loads(frozen)
        pool_raw=(Path(pools)/f'{i}.json').read_bytes();p=json.loads(pool_raw)
        s=json.loads((Path(selected)/f'{i}.json').read_text())
        assert s['trainingDictionaryHash']==p['frozenDictionaryHash']==hashlib.sha256(frozen).hexdigest()
        assert s['testPoolHash']==hashlib.sha256(pool_raw).hexdigest() and p['sourceHash']==hashlib.sha256(raw).hexdigest()
        c=p['testConfiguration'];assert c['file']==configs[i]['file'] and c['atoms']==configs[i]['atoms']
        # Check every candidate's geometry against the source, independently of generation.
        check={**d,'inputHash':hashlib.sha256(raw).hexdigest(),'configurations':[c],'results':[]}
        with tempfile.TemporaryDirectory(prefix='gcts-boron-pool-check-') as tmp:
            path=Path(tmp)/'check.json';path.write_text(json.dumps(check));geometry.verify(source,path,True)
        w=list(map(Fraction,d['results'][-1]['weights']));labels=d['results'][-1]['labels'];totals=[Fraction(0)]*c['atoms'];seen=set()
        for o in c['occurrences']:
            values=tuple(sorted((o['ids'][v],str(w[3*o['type']+u]),labels[3*o['type']+u]) for u,v in enumerate(o['permutation'])))
            key=(o['type'],values);assert key not in seen;seen.add(key)
            for point,value,label in values:totals[point]+=Fraction(value)
        expected=[{'point':j,'availableTotal':str(v)} for j,v in enumerate(totals) if v<1]
        assert p['capacityDeficits']==expected and p['summary']['underCapacityPoints']==len(expected)
        chosen=s['summary']['learnedDenominator'];assert chosen in (2,3,4,6,12)
        for trial in s['trainingTrials']:
            k=trial['k']
            if trial['status']=='exact training divisibility obstruction':
                assert any((t['atoms']*k)%3 for t in d['configurations']);continue
            if trial['status']=='training passed':
                assert k==chosen
                for t,r in zip(d['configurations'],trial['fits']):
                    assert t['file']==r['file'] and cover(t,r['selected'],k)==r['positiveComponents']
        assert s['trainingTrials'][-1]['status']=='training passed'
        assert cover(c,s['test']['selected'],chosen)==s['summary']['positiveComponents']==s['test']['positiveComponents']
        summary.append(s['summary'])
    assert json.loads((Path(selected)/'summary.json').read_text())['results']==summary
    print(json.dumps({'verifiedSelectedTestCovers':len(summary),'connectedTestCovers':sum(s['positiveComponents']==1 for s in summary),
        'verifiedFrozenWeightCapacityObstructions':6,'markingsTested':False,'baseTreeSearchTested':False}))
if __name__=='__main__':verify(*sys.argv[1:5])
