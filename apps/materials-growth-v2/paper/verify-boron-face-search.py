"""Rebuild reference candidate models and independently check final point states."""
import hashlib
import json
from pathlib import Path
import sys
from collections import defaultdict
from itertools import combinations
import networkx as nx

def verify(input_path,learning_path,folder):
    raw=Path(input_path).read_bytes();learnraw=Path(learning_path).read_bytes();d=json.loads(raw);learn=json.loads(learnraw)['result'];results=[]
    for fold,c in enumerate(d['configurations']):
        for marked in (False,True):
            a=json.loads((Path(folder)/f'{fold}-{str(marked).lower()}.json').read_text());model=a['model'];result=a['result']
            assert a['inputHash']==hashlib.sha256(raw).hexdigest() and a['learningHash']==hashlib.sha256(learnraw).hexdigest()
            assert model['capacity']==learn['capacity'] and model['required']==list(map(str,range(c['atoms'])))
            expected=[]
            for i,o in enumerate(c['occurrences']):
                t=d['types'][o['type']];ts=[];ms=[]
                for u,p in enumerate(o['ids']):
                    role=learn['roleOfSite'][t['offset']+u];ts.append({'point':str(p),'value':learn['weightsByRole'][role]})
                    label=learn['scalarLabelsByRole'][role]
                    if marked and label is not None:ms.append({'point':str(p),'lo':label,'hi':label})
                expected.append({'id':str(i).zfill(6),'t':ts,'m':ms})
            assert model['candidates']==expected
            local=defaultdict(list)
            if marked:
                for candidate in expected:
                    m={x['point']:x['lo'] for x in candidate['m']}
                    for x in candidate['t']:
                        if x['point'] in m:local[x['point']].append((x['value'],m[x['point']]))
            mark_disagreements=sum(a[1]!=b[1] for group in local.values() for a,b in combinations(group,2))
            capacity_compatible_disagreements=sum(a[1]!=b[1] and a[0]+b[0]<=model['capacity'] for group in local.values() for a,b in combinations(group,2))
            byid={p['id']:p for p in expected};ids=result['selected'];assert len(set(ids))==len(ids)
            totals={p:0 for p in model['required']};marks={};graph=nx.Graph();graph.add_nodes_from(model['required'])
            for id in ids:
                p=byid[id];points=[x['point'] for x in p['t']]
                graph.add_edges_from((points[0],v) for v in points[1:])
                for x in p['t']:totals[x['point']]+=x['value']
                for x in p['m']:
                    if x['point'] in marks:assert marks[x['point']]==x['lo']
                    marks[x['point']]=x['lo']
            assert all(0<=v<=model['capacity'] for v in totals.values())
            complete=all(v==model['capacity'] for v in totals.values())
            assert complete==(result['status']=='exact finite point-cover witness')
            results.append({'file':c['file'],'marked':marked,'complete':complete,'selected':len(ids),
                            'positiveComponents':nx.number_connected_components(graph) if complete else None,
                            'filledPoints':sum(v==model['capacity'] for v in totals.values()),'required':c['atoms'],
                            'localMarkDisagreements':mark_disagreements,
                            'capacityCompatibleLocalMarkDisagreements':capacity_compatible_disagreements})
    out={'results':results,'scope':'Independent candidate reconstruction and exact final-state checks; in-sample finite pools, not blind growth.'}
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':
    out=verify(*sys.argv[1:4])
    if len(sys.argv)>4:
        with Path(sys.argv[4]).open('x') as f:json.dump(out,f,indent=2)
