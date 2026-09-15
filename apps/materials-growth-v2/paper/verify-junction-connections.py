"""Independently rebuild observed class relations and compiled state-pair tables."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

inp,learned,alt,junction_path,connection_path,out=map(Path,sys.argv[1:])
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];alternatives=json.loads(alt.read_text());junctions=json.loads(junction_path.read_text());data=json.loads(connection_path.read_text())
for key,p in [('inputHash',inp),('learningHash',learned),('alternativeHash',alt),('junctionHash',junction_path)]:assert data[key]==digest(p)
source_class={}
for li,entry in enumerate(junctions['library']):
    for source in entry['sources']:
        key=(source['fold'],source['point'],frozenset(source['candidates']));assert key not in source_class;source_class[key]=li
expected=defaultdict(set);covers=[]
for fold,cfg in enumerate(d['configurations']):
    records=[r['selected'][fold]]+[run['selected'] for run in alternatives['runs'] if run['fold']==fold];covers.append(records)
    nodes={n['point']:n for n in junctions['folds'][fold]['nodes']}
    for ci,record in enumerate(records):
        selected=set(record);assignment={p:source_class[fold,p,frozenset(e['candidate'] for e in n['incident'] if e['candidate'] in selected)] for p,n in nodes.items()}
        for index,o in enumerate(cfg['occurrences']):
            if index not in selected or len(o['ids'])!=2 or not set(o['ids'])<=nodes.keys():continue
            a,b=map(assignment.get,o['ids']);expected[o['type'],a,b].add((fold,ci))
            t=d['types'][o['type']];roles=r['roleOfSite'][t['offset']:t['offset']+2]
            decoration=[(r['weightsByRole'][role],r['scalarLabelsByRole'][role]) for role in roles]
            if decoration[0]==decoration[1]:expected[o['type'],b,a].add((fold,ci))
actual={(x['type'],x['leftClass'],x['rightClass']):set(map(tuple,x['sourceRecords'])) for x in data['rules']}
assert actual==dict(expected) and len(actual)==len(data['rules'])
checks=[]
for fold,cfg in enumerate(d['configurations']):
    nodes={n['point']:n for n in junctions['folds'][fold]['nodes']};row=data['folds'][fold];edges=row['edges']
    assert {e['candidate'] for e in edges}=={i for i,o in enumerate(cfg['occurrences']) if len(o['ids'])==2 and set(o['ids'])<=nodes.keys()}
    assert len(edges)==len({e['candidate'] for e in edges});full_pairs=0;allowed_pairs=0;training_checks=0
    for edge in edges:
        o=cfg['occurrences'][edge['candidate']];assert edge['points']==o['ids'] and edge['type']==o['type']
        left,right=[nodes[p] for p in edge['points']];allowed=set()
        for a,sa in enumerate(left['states']):
            if edge['candidate'] not in sa['candidates']:continue
            for b,sb in enumerate(right['states']):
                if edge['candidate'] not in sb['candidates']:continue
                full_pairs+=1
                if any((edge['type'],wa['library'],wb['library']) in expected for wa in sa['witnesses'] for wb in sb['witnesses']):allowed.add((a,b))
        assert allowed==set(map(tuple,edge['allowedPresentStates'])) and len(allowed)==len(edge['allowedPresentStates'])
        assert len(edge['classWitnesses'])==len(edge['allowedPresentStates'])
        for (a,b),(li,lj) in zip(edge['allowedPresentStates'],edge['classWitnesses']):
            assert li in {w['library'] for w in left['states'][a]['witnesses']} and lj in {w['library'] for w in right['states'][b]['witnesses']}
            assert (edge['type'],li,lj) in expected
        allowed_pairs+=len(allowed)
        for record in covers[fold]:
            selected=set(record)
            if edge['candidate'] not in selected:continue
            pair=tuple(next(i for i,s in enumerate(n['states']) if set(s['candidates'])==selected&{e['candidate'] for e in n['incident']}) for n in (left,right))
            assert pair in allowed;training_checks+=1
    assert training_checks==row['trainingConnectionsChecked']
    checks.append({'file':cfg['file'],'coupledEdges':len(edges),'uncoupledPresentStatePairs':full_pairs,'learnedPresentStatePairs':allowed_pairs,
                   'excludedStateCombinations':full_pairs-allowed_pairs,'trainingConnectionsVerified':training_checks})
result={'scope':__doc__,'connectionHash':digest(connection_path),'junctionHash':digest(junction_path),'rulesVerified':len(expected),'checks':checks,
        'limits':'Checks algebraic compilation and provenance; geometric fits are separately checked by verify-boron-junctions.py.'}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
