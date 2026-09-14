"""Training-only sensitivity test, not a new material law or reference search.

Select alternative exact degree-two covers without requiring connectedness.
Test and refit binary type contrasts against their individual cycles, together
with the original training witnesses. Disconnected decompositions of a known
configuration need not be admissible growth histories: this is a robustness
control, not evidence that every unmarked cover must be preserved.
"""
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter
import numpy as np
import networkx as nx
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix


def run(dictionary, cover_path, marking_path):
    raw=Path(dictionary).read_bytes(); d=json.loads(raw)
    cover_raw=Path(cover_path).read_bytes(); cover=json.loads(cover_raw)
    mark_raw=Path(marking_path).read_bytes(); mark=json.loads(mark_raw)
    assert mark['dictionaryHash']==hashlib.sha256(raw).hexdigest()
    assert d['coverHash']==hashlib.sha256(cover_raw).hexdigest()
    admitted=set(mark['admittedTypes']); source={c['id']:c for c in cover['results']}
    results=[]; rows=[r['oddMultiplicityTypes'] for r in mark['rows']]
    for c in d['configurations']:
        if not c['training']:continue
        s=source[c['id']]; n=len(s['components'])
        allowed=[i for i,o in enumerate(c['occurrences']) if o['matched'] and o['type'] in admitted]
        edges=[s['componentPairs'][i] for i in allowed]; rr=[];cc=[]
        for j,(a,b) in enumerate(edges):rr.extend([a,b]);cc.extend([j,j])
        A=coo_matrix((np.ones(len(rr)),(rr,cc)),shape=(n,len(edges))).tocsc()
        for seed in range(3):
            # Random linear costs are an explicit sampling heuristic, not a
            # uniform sample of covers. No marking or cycle parity in objective.
            costs=np.random.default_rng(seed).uniform(-1,1,len(edges))
            fit=milp(costs,integrality=np.ones(len(edges)),bounds=Bounds(0,1),
                     constraints=LinearConstraint(A,2,2),options={'time_limit':2.})
            r={'id':c['id'],'seed':seed,'selected':[],'status':'unknown','solverStatus':int(fit.status)}
            if fit.x is not None:
                chosen=np.flatnonzero(fit.x>.5); assert np.all(A[:,chosen].sum(axis=1)==2)
                selected=[allowed[int(j)] for j in chosen];g=nx.Graph();g.add_nodes_from(range(n))
                for j in chosen:
                    a,b=edges[j];assert not g.has_edge(a,b);g.add_edge(a,b,index=allowed[int(j)])
                assert all(degree==2 for _,degree in g.degree())
                cycle_rows=[];lengths=[]
                for group in nx.connected_components(g):
                    types=[c['occurrences'][v['index']]['type'] for _,_,v in g.subgraph(group).edges(data=True)]
                    row=sorted(ti for ti,count in Counter(types).items() if count%2)
                    rows.append(row);cycle_rows.append(row);lengths.append(len(types))
                r.update(selected=selected,status='exact degree-two cover',cycleRows=cycle_rows,
                         cycleLengths=lengths,oldBinaryLiftable=all(len(row)%2==0 for row in cycle_rows))
            results.append(r)
        print(json.dumps({'id':c['id'],'completed':sum(r['status']=='exact degree-two cover' for r in results[-3:]),
                          'oldBinaryRejected':sum(r.get('oldBinaryLiftable') is False for r in results[-3:])}),flush=True)
    types=sorted(admitted);index={ti:i for i,ti in enumerate(types)}
    distinct=sorted(set(tuple(row) for row in rows)-{()});rr=[];cc=[];vv=[]
    for i,row in enumerate(distinct):
        for ti in row:rr.append(i);cc.append(index[ti]);vv.append(1)
        rr.append(i);cc.append(len(types)+i);vv.append(-2)
    A=coo_matrix((vv,(rr,cc)),shape=(len(distinct),len(types)+len(distinct))).tocsc()
    fit=milp(np.r_[-np.ones(len(types)),np.zeros(len(distinct))],integrality=np.ones(A.shape[1]),
             bounds=Bounds(0,np.r_[np.ones(len(types)),[len(row)//2 for row in distinct]]),
             constraints=LinearConstraint(A,0,0),options={'time_limit':30.})
    contrasts=None
    if fit.x is not None:
        values=np.rint(fit.x).astype(int);assert np.all(A@values==0)
        contrasts={str(ti):int(values[index[ti]]) for ti in types}
    # Exact GF(2) rank and forced-zero coordinates of the homogeneous system.
    basis={}
    for row in distinct:
        bits=sum(1<<index[ti] for ti in row)
        while bits:
            pivot=bits.bit_length()-1
            if pivot in basis:bits^=basis[pivot]
            else:basis[pivot]=bits;break
    forced=[]
    for ti in types:
        bits=1<<index[ti]
        for pivot in sorted(basis,reverse=True):
            if (bits>>pivot)&1:bits^=basis[pivot]
        if bits==0:forced.append(ti)
    return {'scope':__doc__,'dictionaryHash':hashlib.sha256(raw).hexdigest(),
            'coverHash':hashlib.sha256(cover_raw).hexdigest(),'markingHash':hashlib.sha256(mark_raw).hexdigest(),
            'results':results,'contrastRows':distinct,'rank':len(basis),'nullity':len(types)-len(basis),
            'forcedZeroTypes':forced,'refitContrasts':contrasts,'refitSolverStatus':int(fit.status),
            'refitContrastingTypes':sum(contrasts.values()) if contrasts is not None else None,
            'refitObjectiveDualBound':float(fit.mip_dual_bound) if getattr(fit,'mip_dual_bound',None) is not None else None,
            'summary':{'attempted':len(results),'exactCovers':sum(r['status']=='exact degree-two cover' for r in results),
                       'oldBinaryRejected':sum(r.get('oldBinaryLiftable') is False for r in results),
                       'connectedCovers':sum(len(r.get('cycleLengths',[]))==1 for r in results)}}


if __name__=='__main__':
    out=run(*sys.argv[1:4])
    with Path(sys.argv[4]).open('x') as f:json.dump(out,f)
    print(json.dumps({k:v for k,v in out.items() if k not in ('results','contrastRows','refitContrasts')},indent=2))
