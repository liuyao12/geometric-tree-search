"""Find certified unsupported candidates in the unmarked finite filling model.

LP witnesses only guide which candidates to investigate. Pruning requires an
exact dual bound <1 on the sum of the remaining binary selection variables.
"""
import hashlib
import json
import sys
import time
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

inp,learned,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];results=[]
for fold,cfg in enumerate(d['configurations']):
    columns=[];ii=[];jj=[];vv=[]
    for j,o in enumerate(cfg['occurrences']):
        col=[]
        for u,p in enumerate(o['ids']):
            w=r['weightsByRole'][r['roleOfSite'][d['types'][o['type']]['offset']+u]]
            col.append((p,w));ii.append(p);jj.append(j);vv.append(w)
        columns.append(col)
    a=coo_matrix((vv,(ii,jj)),shape=(cfg['atoms'],len(columns))).tocsc()
    remaining=set(range(len(columns)));history=[];certificate=None;started=time.monotonic()
    # No selected training answer is used to initialize this investigation.
    for iteration in range(30):
        if not remaining:break
        c=np.array([int(j in remaining) for j in range(len(columns))])
        fit=linprog(-c,A_eq=a,b_eq=np.full(cfg['atoms'],r['capacity']),bounds=(0,1),
                    method='highs',options={'time_limit':2})
        if not fit.success:
            history.append({'iteration':iteration,'status':fit.message});break
        y=[F(float(-v)).limit_denominator(100000) for v in fit.eqlin.marginals]
        z=[max(F(0),F(int(c[j]))-sum(y[p]*w for p,w in col)) for j,col in enumerate(columns)]
        bound=r['capacity']*sum(y)+sum(z)
        history.append({'iteration':iteration,'investigated':len(remaining),'bound':str(bound)})
        if bound<1:
            certificate={'excluded':sorted(remaining),'bound':str(bound),
                         'y':[[p,str(v)] for p,v in enumerate(y) if v],
                         'z':[[j,str(v)] for j,v in enumerate(z) if v]};break
        positive={j for j in remaining if fit.x[j]>1e-7}
        if not positive:break
        remaining-=positive
    row={'fold':fold,'file':cfg['file'],'candidates':len(columns),'seconds':time.monotonic()-started,
         'history':history,'certificate':certificate,
         'excluded':len(certificate['excluded']) if certificate else 0,
         'unresolvedInvestigation':len(remaining) if certificate is None else 0}
    results.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ('history','certificate')}),flush=True)
dest.write_text(json.dumps({'scope':__doc__,'inputHash':hashlib.sha256(inp.read_bytes()).hexdigest(),
    'learningHash':hashlib.sha256(learned.read_bytes()).hexdigest(),'results':results},indent=2)+'\n')
