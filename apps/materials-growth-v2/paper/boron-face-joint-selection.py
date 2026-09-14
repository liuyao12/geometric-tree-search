"""Joint shared site-weight and occurrence selection training, integer t-units.

All six full supercells train together. No unit-cell selection locking. Each
observed occurrence has its own binary choice. t-values are shared per role
across all inputs; witnessed self-isometries tie roles. A declared anti-collapse
condition retains at least one occurrence of each finite-face type in every
input where it was proposed. This is a MILP learning control, not GCTS search.
"""
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix

def roles(d):
    n=sum(len(t['positions']) for t in d['types']);parent=list(range(n))
    def root(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    for t in d['types']:
        for a,b in t['ties']:parent[root(t['offset']+a)]=root(t['offset']+b)
    keys={};labels=[]
    for a in range(n):
        r=root(a)
        if r not in keys:keys[r]=len(keys)
        labels.append(keys[r])
    return labels

def train(d,capacity=12,seconds=30,cuts=()):
    assert isinstance(capacity,int) and capacity>=1
    role=roles(d);nq=max(role)+1;occ=[];npnt=0;required=[];type_groups=[]
    for ci,c in enumerate(d['configurations']):
        groups=defaultdict(list)
        for oi,o in enumerate(c['occurrences']):
            t=d['types'][o['type']];index=len(occ)
            occ.append({'config':ci,'original':oi,'type':o['type'],
                        'sites':[(npnt+p,role[t['offset']+u]) for u,p in enumerate(o['ids'])]})
            if t['kind']=='finite-face':groups[t['id']].append(index)
        type_groups.extend(groups.values());npnt+=c['atoms']
    occurrence_index={(o['config'],o['original']):j for j,o in enumerate(occ)}
    nx=len(occ);nextvar=nq+nx;products={}
    # q_r in [1,C], x_o binary, z_or = q_r*x_o via exact binary-product bounds.
    for j,o in enumerate(occ):
        for r in sorted({r for _,r in o['sites']}):products[j,r]=nextvar;nextvar+=1
    rows=[];cols=[];values=[];lower=[];upper=[]
    def equation(terms,lo,hi):
        i=len(lower);lower.append(lo);upper.append(hi)
        for j,v in terms:rows.append(i);cols.append(j);values.append(v)
    point_terms=[[] for _ in range(npnt)]
    for j,o in enumerate(occ):
        for p,r in o['sites']:point_terms[p].append((products[j,r],1))
    for terms in point_terms:equation(terms,capacity,capacity)
    for (j,r),z in products.items():
        x=nq+j
        equation([(z,1),(r,-1)],-np.inf,0)
        equation([(z,1),(x,-capacity)],-np.inf,0)
        equation([(z,1),(r,-1),(x,-capacity)],-capacity,np.inf)
    for group in type_groups:equation([(nq+j,1) for j in group],1,np.inf)
    for ci,group in cuts:equation([(nq+occurrence_index[ci,j],1) for j in group],1,np.inf)
    A=coo_matrix((values,(rows,cols)),shape=(len(lower),nextvar)).tocsc()
    lb=np.zeros(nextvar);lb[:nq]=1
    ub=np.full(nextvar,float(capacity));ub[nq:nq+nx]=1
    integral=np.zeros(nextvar);integral[:nq+nx]=1
    # Feasibility only: no reported efficiency or optimal number of occurrences.
    started=time.monotonic()
    fit=milp(np.zeros(nextvar),integrality=integral,bounds=Bounds(lb,ub),
             constraints=LinearConstraint(A,lower,upper),options={'time_limit':seconds,'mip_rel_gap':0})
    out={'capacity':capacity,'seconds':time.monotonic()-started,'solverStatus':fit.message,
         'variables':nextvar,'weightRoles':nq,'occurrenceChoices':nx,'constraints':len(lower),
         'status':'unknown','roleOfSite':role}
    if fit.x is None:
        out['status']='numerical restricted integer infeasibility' if fit.status==2 else 'unknown: budget';return out
    weights=np.rint(fit.x[:nq]).astype(int).tolist();chosen=[[] for _ in d['configurations']]
    for j,o in enumerate(occ):
        if fit.x[nq+j]>.5:chosen[o['config']].append(o['original'])
    out.update(evaluate(d,role,weights,chosen,capacity))
    return out

def evaluate(d,role,weights,chosen,capacity):
    nq=max(role)+1
    checks=[];mark_groups=[]
    for c,selected in zip(d['configurations'],chosen):
        totals=[0]*c['atoms'];groups=[[] for _ in totals];parent=list(range(c['atoms']))
        def root(a):
            while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
            return a
        counts=defaultdict(int)
        for oi in selected:
            o=c['occurrences'][oi];t=d['types'][o['type']];counts[o['type']]+=1
            for u,p in enumerate(o['ids']):
                r=role[t['offset']+u];totals[p]+=weights[r];groups[p].append(r)
            for p in o['ids'][1:]:parent[root(p)]=root(o['ids'][0])
        present={o['type'] for o in c['occurrences'] if d['types'][o['type']]['kind']=='finite-face'}
        assert all(counts[t]>0 for t in present)
        assert all(v==capacity for v in totals) and all(1<=v<=capacity for v in weights)
        mark_groups.extend(groups)
        checks.append({'file':c['file'],'atoms':c['atoms'],'selected':len(selected),
                       'selectedByType':dict(counts),'positiveComponents':len({root(p) for p in range(c['atoms'])})})
    spec=importlib.util.spec_from_file_location('marks',Path(__file__).with_name('presearch-markings.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    labels=m.equality_labels(nq,mark_groups);observed={r for g in mark_groups for r in g}
    return dict(status='exact shared integer training cover',weightsByRole=weights,selected=chosen,checks=checks,
               scalarLabelsByRole=[label if r in observed else None for r,label in enumerate(labels)],
               observedScalarClasses=len({labels[r] for r in observed}),unobservedRoles=nq-len(observed))

if __name__=='__main__':
    raw=Path(sys.argv[1]).read_bytes();d=json.loads(raw)
    r=train(d,int(sys.argv[3]) if len(sys.argv)>3 else 12,float(sys.argv[4]) if len(sys.argv)>4 else 30)
    out={'scope':__doc__,'inputHash':hashlib.sha256(raw).hexdigest(),'result':r}
    with Path(sys.argv[2]).open('x') as f:json.dump(out,f)
    print(json.dumps({k:v for k,v in r.items() if k not in ('selected','roleOfSite','scalarLabelsByRole','weightsByRole')},indent=2))
