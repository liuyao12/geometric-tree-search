"""Independent sparse quarter-unit perturbations of every training-free parameter."""
import json
from pathlib import Path
import sys
from fractions import Fraction
import numpy as np
from scipy.sparse import coo_matrix

d=json.loads(Path(sys.argv[1]).read_text());r=json.loads(Path(sys.argv[2]).read_text())
s={x['id']:x for x in json.loads(Path(sys.argv[3]).read_text())['results']};audit=json.loads(Path(sys.argv[4]).read_text())
n=d['offsets'][-1];columns=[np.full(n,2,dtype=np.int16)]
for c in r['components']:
    if c['kind']!='free-complement':continue
    w=columns[0].copy();w[c['side0']]=1;w[c['side1']]=3;columns.append(w)
for u in r['unobservedSites']:
    w=columns[0].copy();w[u]=1;columns.append(w)
W=np.stack(columns,axis=1);verified=0;guaranteed_covers=0
for c in d['configurations']:
    rows=[];cols=[]
    for i in s[c['id']]['selected']:
        o=c['occurrences'][i]
        for u,j in enumerate(o['permutation']):rows.append(o['ids'][j]);cols.append(d['offsets'][o['type']]+u)
    A=coo_matrix((np.ones(len(rows),dtype=np.int16),(rows,cols)),shape=(c['atoms'],n)).tocsr()
    sums=A@W;assert np.all(sums[:,0]==4)
    if c['training']:assert np.all(sums==4);continue
    out=next(x for x in audit['results'] if x['id']==c['id']);valid=int(np.all(sums==4,axis=1).sum())
    assert valid==out['universallyFilledAtoms']
    spread=np.abs(sums[:,1:]-4).sum(axis=1)
    assert Fraction(4-2*int(spread.max()),4)==Fraction(out['minimumPossiblePointSum'])
    assert Fraction(4+2*int(spread.max()),4)==Fraction(out['maximumPossiblePointSum'])
    verified+=1;guaranteed_covers+=int(valid==c['atoms'])
result={'verifiedValidationCovers':verified,'universallyFilledCovers':guaranteed_covers,
 'independentParameterPerturbations':len(columns)-1,'exactIntegerArithmetic':True,
 'scope':'Checks an affine basis of training-consistent weights on the original selected covers; no universal reconstruction claim.'}
with Path(sys.argv[5]).open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
