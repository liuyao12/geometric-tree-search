"""Specialized positive uniform-weight selection diagnostic, not reference search.

Select pair unions forming a connected k-regular graph of geometric components.
Every site then has shared t=1/k. k is a declared hypothesis; tests do not tune it.
MILP connectivity cuts operate only on supplied-coordinate candidate pools.
"""
import json
from pathlib import Path
import sys
import time
from collections import defaultdict
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

def select(parts,pairs,allowed,k,budget):
    n=len(parts);edges=[pairs[i] for i in allowed];m=len(edges);cuts=[];start=time.monotonic();rounds=0
    if not m:return {'status':'empty candidate pool','selected':[]}
    while time.monotonic()-start<budget:
        rows=[];cols=[];values=[]
        for j,(a,b) in enumerate(edges):rows.extend([a,b]);cols.extend([j,j]);values.extend([1,1])
        for i,cut in enumerate(cuts):rows.extend([n+i]*len(cut));cols.extend(cut);values.extend([1]*len(cut))
        A=coo_matrix((values,(rows,cols)),shape=(n+len(cuts),m)).tocsc()
        crossing=2 if k%2==0 else 1
        result=milp(np.zeros(m),integrality=np.ones(m),bounds=Bounds(0,1),
            constraints=LinearConstraint(A,np.r_[np.full(n,k),np.full(len(cuts),crossing)],np.r_[np.full(n,k),np.full(len(cuts),np.inf)]),
            options={'time_limit':max(.01,budget-(time.monotonic()-start))})
        rounds+=1
        if result.x is None:return {'status':'solver infeasible' if result.status==2 else 'budget unknown','selected':[], 'rounds':rounds,'cuts':len(cuts)}
        chosen=np.flatnonzero(result.x>.5);degree=np.zeros(n,int);rr=[];cc=[]
        for j in chosen:
            a,b=edges[j];degree[a]+=1;degree[b]+=1;rr.extend([a,b]);cc.extend([b,a])
        assert np.all(degree==k)
        count,labels=connected_components(coo_matrix((np.ones(len(rr)),(rr,cc)),shape=(n,n)).tocsr(),directed=False)
        if count==1:return {'status':'connected positive finite cover','selected':[allowed[int(j)] for j in chosen],'rounds':rounds,'cuts':len(cuts)}
        for label in range(count):
            cut=[j for j,(a,b) in enumerate(edges) if (labels[a]==label)!=(labels[b]==label)]
            if len(cut)<crossing:return {'status':'no connected regular cover across cut','selected':[],'rounds':rounds,'cuts':len(cuts)}
            cuts.append(cut)
    return {'status':'budget unknown','selected':[],'rounds':rounds,'cuts':len(cuts)}

if __name__=='__main__':
    cover=json.loads(Path(sys.argv[1]).read_text());d=json.loads(Path(sys.argv[2]).read_text());k=int(sys.argv[3]);assert k>=2
    byid={c['id']:c for c in cover['results']};results=[]
    for c in d['configurations']:
        source=byid[c['id']];allowed=[i for i,o in enumerate(c['occurrences']) if o['matched']]
        r=select(source['components'],source['componentPairs'],allowed,k,5.)
        row={'id':c['id'],'training':c['training'],'atoms':c['atoms'],'proposals':len(allowed),**r}
        results.append(row);print(json.dumps({a:b for a,b in row.items() if a!='selected'}),flush=True)
    out={'scope':__doc__,'degreeHypothesis':k,'sharedWeight':f'1/{k}','perConfigurationBudgetSeconds':5,
         'results':results,'allTrainingPassed':all(r['status']=='connected positive finite cover' for r in results if r['training'])}
    with Path(sys.argv[4]).open('x') as f:json.dump(out,f)
