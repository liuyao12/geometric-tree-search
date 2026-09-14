"""Independent exact integer and scalar checks on selected training witnesses.

The input's geometry is separately checked by verify-boron-face-precheck.py.
This verifier does not import or run the training MILP.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import networkx as nx

def verify(input_path,result_path):
    raw=Path(input_path).read_bytes();d=json.loads(raw);out=json.loads(Path(result_path).read_text());r=out['result']
    assert out['inputHash']==hashlib.sha256(raw).hexdigest()
    assert r['status']=='exact shared integer training cover','No successful witness to certify'
    capacity=r['capacity'];assert type(capacity) is int and capacity>0
    weights=r['weightsByRole'];roles=r['roleOfSite'];labels=r['scalarLabelsByRole']
    n=sum(len(t['positions']) for t in d['types']);assert len(roles)==n and len(labels)==len(weights)
    assert all(type(w) is int and 1<=w<=capacity for w in weights)
    assert set(roles)==set(range(len(weights)))
    sym=nx.Graph();sym.add_nodes_from(range(n))
    for t in d['types']:
        sym.add_edges_from((t['offset']+a,t['offset']+b) for a,b in t['ties'])
    components=list(nx.connected_components(sym))
    assert len(components)==len(weights)
    assert all(len({roles[v] for v in c})==1 for c in components)
    equality=nx.Graph();checks=[];total_selected=0
    assert len(r['selected'])==len(d['configurations'])
    for c,selected in zip(d['configurations'],r['selected']):
        assert len(set(selected))==len(selected) and all(type(i) is int and 0<=i<len(c['occurrences']) for i in selected)
        totals=[0]*c['atoms'];at=[[] for _ in totals];graph=nx.Graph();graph.add_nodes_from(range(c['atoms']));counts=Counter()
        for i in selected:
            o=c['occurrences'][i];t=d['types'][o['type']];counts[o['type']]+=1
            for u,p in enumerate(o['ids']):
                role=roles[t['offset']+u];totals[p]+=weights[role];at[p].append(role)
            graph.add_edges_from((o['ids'][0],p) for p in o['ids'][1:])
        assert all(v==capacity for v in totals)
        for group in at:
            assert group and all(labels[v] is not None for v in group)
            assert len({labels[v] for v in group})==1
            equality.add_nodes_from(group);equality.add_edges_from((group[0],v) for v in group[1:])
        present={o['type'] for o in c['occurrences'] if d['types'][o['type']]['kind']=='finite-face'}
        assert present<=set(counts)
        checks.append({'file':c['file'],'atoms':c['atoms'],'selected':len(selected),
                       'selectedByType':dict(counts),'positiveComponents':nx.number_connected_components(graph)})
        total_selected+=len(selected)
    assert len(checks)==len(r['checks'])
    if 'connectedGatePassed' in out:
        assert out['connectedGatePassed']==all(c['positiveComponents']==1 for c in checks)
    for expected,stored in zip(checks,r['checks']):
        assert {**expected,'selectedByType':{str(k):v for k,v in expected['selectedByType'].items()}}==stored
    count=nx.number_connected_components(equality)
    assert count==r['observedScalarClasses']==len({labels[v] for v in equality})
    assert all(labels[v] is None for v in set(range(len(weights)))-set(equality))
    assert r['unobservedRoles']==len(weights)-len(equality)
    summary={'capacity':capacity,'verifiedConfigurations':len(checks),'verifiedAtoms':sum(c['atoms'] for c in checks),
             'selectedOccurrences':total_selected,'weightRoles':len(weights),'observedScalarClasses':count,
             'unobservedRoles':r['unobservedRoles'],'checks':checks,
             'scope':'Joint all-input training; no held-out, coordinate-blind growth or reference-search claim.'}
    print(json.dumps(summary,indent=2));return summary

if __name__=='__main__':
    r=verify(*sys.argv[1:3])
    if len(sys.argv)>3:
        with Path(sys.argv[3]).open('x') as f:json.dump(r,f,indent=2)
