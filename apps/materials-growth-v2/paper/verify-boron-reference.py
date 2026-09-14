"""Independent selected-training marking graph and finite search witness audit."""
import hashlib
import json
from pathlib import Path
import sys

def sha(raw):return hashlib.sha256(raw).hexdigest()
def verify(training,pools,selections,markings,search):
    results=[]
    for fold in range(6):
        dr=(Path(training)/str(fold)/'training-dictionary.json').read_bytes();d=json.loads(dr)
        sr=(Path(selections)/f'{fold}.json').read_bytes();s=json.loads(sr)
        mr=(Path(markings)/f'{fold}.json').read_bytes();marks=json.loads(mr)
        pr=(Path(pools)/f'{fold}.json').read_bytes();pool=json.loads(pr)
        assert marks['selectedArtifactHash']==sha(sr) and marks['trainingDictionaryHash']==pool['frozenDictionaryHash']==sha(dr)
        n=3*len(d['types']);adj=[set() for _ in range(n)];active=set()
        def connect(group):
            for v in group[1:]:adj[group[0]].add(v);adj[v].add(group[0])
        trial=s['trainingTrials'][-1]
        for c,selected in zip(d['configurations'],trial['fits']):
            points=[[] for _ in range(c['atoms'])]
            for i in selected['selected']:
                o=c['occurrences'][i]
                for u,p in enumerate(o['permutation']):
                    v=3*o['type']+u;points[o['ids'][p]].append(v);active.add(v)
            assert all(len(g)==trial['k'] for g in points)
            for g in points:connect(g)
        for t in d['types']:
            for a,b in t['symmetryTies']:connect([3*t['id']+a,3*t['id']+b])
        unseen=set(range(n));label_components={}
        while unseen:
            start=unseen.pop();todo=[start];component={start}
            while todo:
                for v in adj[todo.pop()]&unseen:unseen.remove(v);todo.append(v);component.add(v)
            values={marks['labels'][v] for v in component}
            assert len(values)==1
            label=next(iter(values))
            if component&active:
                assert label is not None and label not in label_components;label_components[label]=component
            else:assert label is None
        lanes=[]
        for marked in (False,True):
            artifact=json.loads((Path(search)/f'{fold}-{str(marked).lower()}.json').read_text())
            assert artifact['poolHash']==sha(pr) and artifact['markHash']==sha(mr) and artifact['selectionHash']==sha(sr)
            model=artifact['model'];r=artifact['result'];assert model['capacity']==trial['k']
            assert set(model['required'])==set(map(str,range(pool['testConfiguration']['atoms'])))
            by_id={c['id']:c for c in model['candidates']};assert len(by_id)==len(model['candidates'])
            for c in model['candidates']:
                o=pool['testConfiguration']['occurrences'][int(c['id'])]
                assert {x['point']:x['value'] for x in c['t']}=={str(p):1 for p in o['ids']}
                assert json.loads(c['inventory'])==[o['type'],sorted(o['ids'])]
                expected={str(o['ids'][p]):marks['labels'][3*o['type']+u] for u,p in enumerate(o['permutation']) if marks['labels'][3*o['type']+u] is not None} if marked else {}
                assert {x['point']:x['lo'] for x in c['m']}==expected
                assert all(x['lo']==x['hi'] for x in c['m'])
            totals={p:0 for p in model['required']};assigned={};inventory=set()
            assert len(set(r['selected']))==len(r['selected'])
            adjacency={p:set() for p in totals}
            for id in r['selected']:
                c=by_id[id];assert c['inventory'] not in inventory;inventory.add(c['inventory'])
                for x in c['t']:totals[x['point']]+=x['value'];adjacency[x['point']].update(t['point'] for t in c['t'])
                for x in c['m']:
                    assert x['point'] not in assigned or assigned[x['point']]==x['lo'];assigned[x['point']]=x['lo']
            assert all(v<=model['capacity'] for v in totals.values())
            if r['status']=='exact finite point-cover witness':assert all(v==model['capacity'] for v in totals.values())
            unseen=set(totals);components=0
            while unseen:
                todo=[unseen.pop()];components+=1
                while todo:
                    for v in adjacency[todo.pop()]&unseen:unseen.remove(v);todo.append(v)
            lanes.append(model)
            results.append({'fold':fold,'marked':marked,'status':r['status'],'selected':len(r['selected']),
                'assignedTestPoints':len(assigned),'positiveComponentsIncludingUnfilledSingletons':components})
        assert [{k:v for k,v in c.items() if k!='m'} for c in lanes[0]['candidates']]==[{k:v for k,v in c.items() if k!='m'} for c in lanes[1]['candidates']]
    out={'verifiedResults':results,'trainingOnlyMarkingPartitionsChecked':True,'matchedCandidatePools':True}
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':
    out=verify(*sys.argv[1:6])
    if len(sys.argv)>6:
        with Path(sys.argv[6]).open('x') as f:json.dump(out,f,indent=2)
