"""Independent exact replay of dead-point, forced and resolution proof nodes.

No search graph, branch stack, JavaScript verifier or optimizer is consulted.
The separate filling verifier binds candidate values to the learned model.
"""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import sys


def check_nodes(model,nodes,witness):
    byid={c['id']:c for c in model['candidates']};at=defaultdict(list);types=Counter();uses_prior=0
    for c in model['candidates']:
        for x in c['t']:at[x['point']].append(c)
    for i,node in enumerate(nodes):
        ids=set(node['ids']);assert sorted(ids)==node['ids'] and ids<=byid.keys();kind=node['kind'];types[kind]+=1
        def previous(index):
            assert type(index) is int and 0<=index<i
            return nodes[index]
        if kind=='resolve':
            clause=previous(node['clause']);imp=previous(node['implication'])
            assert clause['kind'] in ('dead','resolve') and imp['kind']=='force' and imp['target'] in clause['ids']
            assert ids==(set(clause['ids'])-{imp['target']})|set(imp['ids'])
        else:
            assert kind in ('dead','force') and node['point'] in model['required']
            totals=Counter();marks={}
            for id in ids:
                for x in byid[id]['t']:totals[x['point']]+=x['value']
                for x in byid[id]['m']:
                    k=(x['point'],x.get('channel','0'));a,b=marks.get(k,(float('-inf'),float('inf')))
                    marks[k]=(max(a,x['lo']),min(b,x['hi']));assert marks[k][0]<=marks[k][1]
            assert all(v<=model['capacity'] for v in totals.values()) and totals[node['point']]<model['capacity']
            if kind=='force':assert node['target'] not in ids and any(c['id']==node['target'] for c in at[node['point']])
            prior=[previous(j) for j in node['uses']];uses_prior+=bool(prior)
            assert all(p['kind'] in ('dead','resolve') for p in prior)
            for c in at[node['point']]:
                if kind=='force' and c['id']==node['target']:continue
                if c['id'] in ids or any(totals[x['point']]+x['value']>model['capacity'] for x in c['t']):continue
                if any((x['point'],x.get('channel','0')) in marks and
                       (x['lo']>marks[(x['point'],x.get('channel','0'))][1] or x['hi']<marks[(x['point'],x.get('channel','0'))][0]) for x in c['m']):continue
                assert any(c['id'] in p['ids'] and set(p['ids'])-{c['id']}<=ids for p in prior),'Unexplained candidate'
        if ids<=witness:assert kind=='force' and node['target'] in witness,'Proof excludes the known training solution'
    return dict(types),uses_prior


def verify(folder,learning_path):
    lr=Path(learning_path).read_bytes();learning=json.loads(lr);results=[]
    for fold,witness in enumerate(learning['result']['selected']):
        for marked in (False,True):
            raw=(Path(folder)/f'{fold}-{str(marked).lower()}.json').read_bytes();d=json.loads(raw)
            assert d['learningHash']==hashlib.sha256(lr).hexdigest() and d['inputHash']==learning['inputHash']
            for name,digest in d['researchSourceHashes'].items():
                assert hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()==digest
            types,uses=check_nodes(d['model'],d['proofNodes'],{f'{i:06d}' for i in witness})
            seen=set()
            for cert in d['certificates']:
                assert type(cert['proof']) is int and 0<=cert['proof']<len(d['proofNodes'])
                node=d['proofNodes'][cert['proof']];assert node['kind'] in ('dead','resolve') and node['ids']==cert['ids']
                key=tuple(cert['ids']);assert key not in seen;seen.add(key)
            diag=d['result']['proofDiagnostics']
            assert types.get('force',0)==diag['forcedImplications'] and types.get('dead',0)==diag['deadClauses'] and types.get('resolve',0)==diag['resolutions']
            assert len(seen)==diag['learnedClauses']==d['result']['proofVersion']
            results.append({'fold':fold,'marked':marked,'proofNodes':len(d['proofNodes']),'nodeTypes':types,
                            'leavesUsingEarlierClauses':uses,'registeredClauses':len(seen),'trainingWitnessPreserved':True,
                            'runHash':hashlib.sha256(raw).hexdigest()})
    return {'scope':__doc__,'results':results,'verifiedNodes':sum(r['proofNodes'] for r in results),
            'registeredClauses':sum(r['registeredClauses'] for r in results),'allTrainingWitnessesPreserved':True}


if __name__=='__main__':
    out=verify(*sys.argv[1:3])
    with Path(sys.argv[3]).open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))
