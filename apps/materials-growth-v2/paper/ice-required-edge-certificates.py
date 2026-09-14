"""Exact dual bounds for targeted edges excluded by the degree-two relaxation."""
import json
from pathlib import Path
from fractions import Fraction as F
import sys
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

d=json.loads(Path(sys.argv[1]).read_text());covers={c['id']:c for c in json.loads(Path(sys.argv[2]).read_text())['results']}
summary=json.loads(Path(sys.argv[3]).read_text());byid={c['id']:c for c in d['configurations']};results=[]
for trial in summary['trials']:
    if trial['status']=='connected positive finite cover':continue
    c=byid[trial['configuration']];source=covers[c['id']];allowed=[i for i,o in enumerate(c['occurrences']) if o['matched']]
    edges=[source['componentPairs'][i] for i in allowed];n=len(source['components']);m=len(edges);target=allowed.index(trial['requiredOccurrence'])
    rows=[];cols=[]
    for i,(a,b) in enumerate(edges):rows.extend([a,b]);cols.extend([i,i])
    A=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,m)).tocsr();cost=np.zeros(m);cost[target]=-1
    lp=linprog(cost,A_eq=A,b_eq=np.full(n,2),bounds=(0,1),method='highs')
    proof=None
    if lp.success:
        y=[F(float(x)).limit_denominator(4096) for x in lp.eqlin.marginals]
        lo=[F(float(x)).limit_denominator(4096) for x in lp.lower.marginals]
        hi=[F(float(x)).limit_denominator(4096) for x in lp.upper.marginals]
        valid=all(x>=0 for x in lo) and all(x<=0 for x in hi)
        valid=valid and all(y[a]+y[b]+lo[i]+hi[i]==(-1 if i==target else 0) for i,(a,b) in enumerate(edges))
        bound=2*sum(y,F())+sum(hi,F())
        if valid and bound==0:proof={'degreeDual':list(map(str,y)),'lowerDual':list(map(str,lo)),'upperDual':list(map(str,hi)),'objectiveLowerBound':'0'}
    results.append({'configuration':c['id'],'targetType':trial['targetType'],'requiredOccurrence':trial['requiredOccurrence'],
        'targetIndex':target,'vertices':n,'edges':edges,'allowedOccurrences':allowed,'certificate':proof})
out={'attemptedFailures':len(results),'exactExcludedEdgeCertificates':sum(r['certificate'] is not None for r in results),'results':results,
     'scope':'Proves target edge has zero weight in the fixed degree-two fractional graph relaxation. Not a geometric impossibility or unrestricted GCTS obstruction.'}
with Path(sys.argv[4]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='results'},indent=2))
