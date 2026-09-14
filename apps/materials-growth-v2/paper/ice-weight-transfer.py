"""Does a validation cover fill for every weight assignment allowed by training?"""
import json
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
import sys

d=json.loads(Path(sys.argv[1]).read_text());r=json.loads(Path(sys.argv[2]).read_text())
selection={x['id']:x for x in json.loads(Path(sys.argv[3]).read_text())['results']}
meta={x['id']:x for x in json.loads(Path(sys.argv[4]).read_text())['configurations']}
expressions={}
for ci,c in enumerate(r['components']):
    if c['kind']=='forced-half':
        for x in c['sites']:expressions[x]=(Fraction(1,2),None,0)
    else:
        for x in c['side0']:expressions[x]=(Fraction(0),('component',ci),1)
        for x in c['side1']:expressions[x]=(Fraction(1),('component',ci),-1)
for x in r['unobservedSites']:expressions[x]=(Fraction(0),('unobserved',x),1)
groups=defaultdict(Counter);results=[]
for c in d['configurations']:
    if c['training']:continue
    constants=[Fraction() for _ in range(c['atoms'])];coefficients=[defaultdict(int) for _ in constants]
    for index in selection[c['id']]['selected']:
        o=c['occurrences'][index]
        for u,j in enumerate(o['permutation']):
            point=o['ids'][j];constant,key,value=expressions[d['offsets'][o['type']]+u]
            constants[point]+=constant
            if key is not None:coefficients[point][key]+=value
    guaranteed=sum(a==1 and all(v==0 for v in b.values()) for a,b in zip(constants,coefficients))
    # These bounds preserve shared parameters; they are exact per point, not
    # independently selectable simultaneous extrema at every point.
    low=min(a+sum(v for v in b.values() if v<0) for a,b in zip(constants,coefficients))
    high=max(a+sum(v for v in b.values() if v>0) for a,b in zip(constants,coefficients))
    g=groups[meta[c['id']]['phase']];g['covers']+=1;g['universallyFilledCovers']+=int(guaranteed==c['atoms'])
    g['atoms']+=c['atoms'];g['universallyFilledAtoms']+=guaranteed
    results.append({'id':c['id'],'universallyFilledAtoms':guaranteed,'atoms':c['atoms'],'minimumPossiblePointSum':str(low),'maximumPossiblePointSum':str(high)})
out={'scope':__doc__,'groups':[dict(phase=k,**v) for k,v in groups.items()],'results':results,
 'limits':'Universal consistency of one supplied cover, conditional on two-incidence training. Failure is not proof that another cover or some learned weight choice cannot work.'}
with Path(sys.argv[5]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out['groups'],indent=2))
