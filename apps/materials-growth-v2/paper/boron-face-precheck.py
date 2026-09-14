"""Shared site t-learning on finite face groups plus periodic fallback pairs.

All six observations train this diagnostic. Every proposed occurrence is used.
Proper self-registration witnesses tie template roles; they are not an exhaustive
approximate symmetry classification. Pair endpoints are tied by their exact
proper rotation. Atom-ID filling is rational-exact; registration is approximate.
No held-out transfer, continuous search, chemistry or occupancy rules.
"""
from collections import Counter
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, hstack, eye

def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
rigid=module('rigid','rigid-cluster-match.py')
prior=module('prior','boron-triple-precheck.py')

def solve(types,configs,tie_roles=True):
    n=sum(len(t['positions']) for t in types);groups=[]
    for c in configs:
        local=[[] for _ in range(c['atoms'])]
        for o in c['occurrences']:
            offset=types[o['type']]['offset']
            for u,p in enumerate(o['ids']):local[p].append(offset+u)
        groups.extend(local)
    active=sorted({v for g in groups for v in g});lookup={v:i for i,v in enumerate(active)}
    # Repeated supercell rows are redundant equations, not independent samples.
    equations={tuple(sorted(Counter(g).items())):1 for g in groups}
    if tie_roles:
        for t in types:
            for a,b in t['ties']:
                a+=t['offset'];b+=t['offset']
                if a in lookup and b in lookup:
                    equations[tuple(sorted(((a,1),(b,-1))))]=0
    rows=[];cols=[];vals=[];rhs=[]
    for i,(terms,value) in enumerate(equations.items()):
        rhs.append(value)
        for j,v in terms:rows.append(i);cols.append(lookup[j]);vals.append(v)
    A=coo_matrix((vals,(rows,cols)),shape=(len(rhs),len(active))).tocsr();k=len(active)
    fit=linprog([0]*k+[-1],A_eq=hstack([A,coo_matrix((len(rhs),1))]),b_eq=rhs,
        A_ub=hstack([-eye(k),np.ones((k,1))]),b_ub=np.zeros(k),bounds=[(0,1)]*(k+1),method='highs')
    out={'files':[c['file'] for c in configs],'roleTies':tie_roles,'requiredPoints':len(groups),
         'uniqueEquations':len(rhs),'activeVariables':k,'solverStatus':fit.message,'status':'unknown'}
    if not fit.success:
        out['status']='numerical restricted LP infeasibility' if fit.status==2 else 'unknown'
        if fit.status==2:
            # Farkas witness: A^T y >= 0, b^T y < 0 contradicts A w=b, w>=0.
            dual=linprog(rhs,A_ub=-A.T,b_ub=np.zeros(k),bounds=[(-1,1)]*len(rhs),method='highs')
            if dual.success:
                y=[Fraction(float(v)).limit_denominator(1000000) for v in dual.x]
                products=[Fraction(0)]*k
                for i,value in enumerate(y):
                    r=A.getrow(i)
                    for j,v in zip(r.indices,r.data):products[int(j)]+=value*int(v)
                b=sum(v*t for v,t in zip(y,rhs))
                if min(products)>=0 and b<0:
                    out.update(status='exact restricted nonnegative filling obstruction',
                               farkasRows=[{'terms':list(terms),'rhs':rhs[i],'multiplier':str(y[i])}
                                           for i,terms in enumerate(equations) if y[i]],
                               farkasRhs=str(b))
        return out
    w=prior.rational_polish(A,rhs,fit.x[:-1])
    if w is None:out['status']='exact equation inconsistency';return out
    exact=all(sum(Fraction(int(v))*w[int(j)] for j,v in zip(A.getrow(i).indices,A.getrow(i).data))==b for i,b in enumerate(rhs))
    out.update(exactEquations=exact,minimumWeight=str(min(w)),maximumWeight=str(max(w)),numericalMaxMin=float(fit.x[-1]))
    if not exact or min(w)<=0 or max(w)>1:
        out['status']='strict positive support gate failed';return out
    full=[None]*n
    for v,x in zip(active,w):full[v]=str(x)
    equalities=list(groups)
    if tie_roles:
        equalities.extend([t['offset']+a,t['offset']+b] for t in types for a,b in t['ties'])
    labels=prior.marks.equality_labels(n,equalities)
    out.update(status='exact positive finite-quotient precheck passed',weights=full,labels=labels,
               activeScalarClasses=len({labels[v] for v in active}))
    return out

def build(folder):
    folder=Path(folder);raw=(folder/'dictionary.json').read_bytes();d=json.loads(raw);eps=d['epsilonAngstrom']
    types=[];offset=0
    for t in d['types']:
        witnesses=list(rigid.matches(t['positions'],t['positions'],eps))
        ties=sorted({tuple(sorted((u,v))) for w in witnesses for u,v in enumerate(w['permutation']) if u!=v})
        types.append({**t,'kind':'finite-face','offset':offset,'ties':ties,'selfFits':witnesses});offset+=len(t['positions'])
    configs=[]
    for c in d['configurations']:
        data_raw=(folder/f"{c['fold']}-1.15-3.json").read_bytes();data=json.loads(data_raw)
        assert hashlib.sha256(data_raw).hexdigest()==c['sourceHash']
        occ=[]
        for o in c['occurrences']:
            g=data['components'][o['component']]
            occ.append({'type':o['type'],'ids':[g['ids'][v] for v in o['permutation']],
                        'component':o['component'],'residual':o['residual']})
        shifts={(a,b):np.array(s) for a,b,s in data['edgeShifts']};positions=np.array(data['positions']);cell=np.array(data['cell'])
        for a,b in data['fallbackPairs']:
            delta=positions[b]+shifts[a,b]@cell-positions[a];length=float(np.linalg.norm(delta))
            # Centered pair registration has site error half the length difference.
            t=next((t for t in types if t['kind']=='pair' and abs(length-t['length'])<=2*eps),None)
            if t is None:
                t={'id':len(types),'kind':'pair','length':length,'positions':[[-length/2,0,0],[length/2,0,0]],
                   'offset':offset,'ties':[[0,1]],'selfFits':[]}
                types.append(t);offset+=2
            occ.append({'type':t['id'],'ids':[a,b],'imageShift':shifts[a,b].tolist(),'length':length,
                        'residual':abs(length-t['length'])/2})
        assert not data['singletons'],'Singleton proposals must be explicitly modeled, not silently omitted.'
        configs.append({'fold':c['fold'],'file':c['file'],'atoms':len(positions),'sourceHash':c['sourceHash'],'occurrences':occ})
    return {'scope':__doc__,'dictionaryHash':hashlib.sha256(raw).hexdigest(),'epsilonAngstrom':eps,
            'types':types,'configurations':configs,'conditionMatchedEnsemble':False}

def main():
    out=build(sys.argv[1]);results=[]
    for tie in (False,True):
        for cs in [[c] for c in out['configurations']]+[out['configurations']]:
            r=solve(out['types'],cs,tie);results.append(r)
            print(json.dumps({k:v for k,v in r.items() if k not in ('weights','labels','farkasRows')}),flush=True)
    out['results']=results
    with Path(sys.argv[2]).open('x') as f:json.dump(out,f)
if __name__=='__main__':main()
