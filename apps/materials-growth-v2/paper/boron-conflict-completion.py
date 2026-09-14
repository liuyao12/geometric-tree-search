"""Test completion of m-conflicting but t-compatible pairs, with exact LP bounds.

For A x=b, 0<=x<=1, y free and z>=0 with A' y+z>=c give
c'x<=b'y+sum(z). A bound <2 excludes selecting both members of c.
"""
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from scipy.optimize import linprog, milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix

inp,learned,pairpath,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];pairs=json.loads(pairpath.read_text())
assert pairs['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest()
assert pairs['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
results=[]
for fold,(cfg,record) in enumerate(zip(d['configurations'],pairs['results'])):
    if not record['survivingPairs']:continue
    columns=[];ii=[];jj=[];vv=[]
    for j,o in enumerate(cfg['occurrences']):
        column=[]
        for u,p in enumerate(o['ids']):
            w=r['weightsByRole'][r['roleOfSite'][d['types'][o['type']]['offset']+u]]
            column.append((p,w));ii.append(p);jj.append(j);vv.append(w)
        columns.append(column)
    a=coo_matrix((vv,(ii,jj)),shape=(cfg['atoms'],len(columns))).tocsc()
    b=np.full(cfg['atoms'],r['capacity'])
    for item in record['survivingPairs']:
        pair=item['candidates'];c=np.zeros(len(columns));c[pair]=1
        fit=linprog(-c,A_eq=a,b_eq=b,bounds=(0,1),method='highs',options={'time_limit':2})
        row={'fold':fold,'candidates':pair,'lpStatus':fit.message}
        if fit.success:
            y=[F(float(-v)).limit_denominator(100000) for v in fit.eqlin.marginals]
            z=[max(F(0),F(int(c[j]))-sum(y[p]*w for p,w in col)) for j,col in enumerate(columns)]
            bound=r['capacity']*sum(y)+sum(z)
            row.update(bound=str(bound),y=[[p,str(v)] for p,v in enumerate(y) if v],
                       z=[[j,str(v)] for j,v in enumerate(z) if v])
            if bound<2:
                row['status']='exact LP certificate: pair cannot complete'
            else:
                lb=np.zeros(len(columns));lb[pair]=1
                integer=milp(np.zeros(len(columns)),integrality=np.ones(len(columns)),
                    bounds=Bounds(lb,np.ones(len(columns))),constraints=LinearConstraint(a,b,b),options={'time_limit':2})
                row['integerStatus']=integer.message
                if integer.x is not None:
                    chosen=np.flatnonzero(integer.x>.5).tolist()
                    totals=[0]*cfg['atoms']
                    for j in chosen:
                        for p,w in columns[j]:totals[p]+=w
                    assert set(pair)<=set(chosen) and all(t==r['capacity'] for t in totals)
                    row.update(status='exact unmarked completion containing conflicting pair',selected=chosen)
                else:row['status']='unknown: no exact exclusion or completion certificate'
        else:row['status']='unknown: LP did not return optimal dual'
        results.append(row)
        print(json.dumps({k:v for k,v in row.items() if k not in ('y','z','selected')}),flush=True)
out={'scope':__doc__,'inputHash':pairs['inputHash'],'learningHash':pairs['learningHash'],'results':results}
dest.write_text(json.dumps(out,indent=2)+'\n')
