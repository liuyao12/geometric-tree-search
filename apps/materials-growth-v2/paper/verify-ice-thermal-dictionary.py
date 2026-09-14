"""Check stored rigid witnesses, species, frozen types and rational point sums."""
import hashlib
import json
from pathlib import Path
import sys
from fractions import Fraction
from collections import defaultdict
import numpy as np

raw=Path(sys.argv[1]).read_bytes();cover_raw=Path(sys.argv[2]).read_bytes();d=json.loads(Path(sys.argv[3]).read_text())
assert hashlib.sha256(raw).hexdigest()==d['coordinateHash'] and hashlib.sha256(cover_raw).hexdigest()==d['coverHash']
corpus={c['id']:c for c in json.loads(raw)['configurations']};cover=json.loads(cover_raw)
supports={c['id']:c['supports'] for c in cover['results']};train=set(cover['trainingIds'])
weights=[Fraction(x) for x in d['filling']['weights']] if d['filling']['weights'] else None
seen=set();maxres=0.;summaries=[];training_exact=True;incidences=[]
for c in d['configurations']:
    original=corpus[c['id']];pos=np.array(original['positions']);cell=np.array(original['cell']);inv=np.linalg.inv(cell)
    assert c['training']==(c['id'] in train) and c['atoms']==len(pos)
    assert [sorted(o['ids']) for o in c['occurrences']]==[sorted(s) for s in supports[c['id']]]
    totals=[Fraction() for _ in pos];marks=defaultdict(list);sites_by_point=defaultdict(list)
    for o in c['occurrences']:
        if not o['matched']:continue
        ti=o['type'];t=d['types'][ti];perm=o['permutation'];n=len(o['ids']);assert sorted(perm)==list(range(n))
        if c['training']:seen.add(ti)
        else:assert ti in seen
        R=np.array(o['rotationRow']);assert np.allclose(R.T@R,np.eye(3),atol=1e-10) and abs(np.linalg.det(R)-1)<1e-10
        transformed=np.array(t['positions'])@R+o['translation'];targets=[o['ids'][j] for j in perm]
        delta=(transformed-pos[targets])@inv;errors=np.linalg.norm((delta-np.rint(delta))@cell,axis=1)
        assert max(errors)<=d['epsilonAngstrom']+1e-9;maxres=max(maxres,float(max(errors)))
        for u,p in enumerate(targets):
            assert t['species'][u]==original['species'][p];site=d['offsets'][ti]+u
            if weights is not None:totals[p]+=weights[site]
            marks[p].append(d['scalarLabels'][site]);sites_by_point[p].append(site)
    if c['training']:
        incidences.extend(sites_by_point.values());training_exact=training_exact and weights is not None and all(x==1 for x in totals)
    conflicts=sum(sum(x!=values[i-1] for i,x in enumerate(values) if i) for values in marks.values())
    summaries.append({'id':c['id'],'training':c['training'],'atoms':len(pos),'proposals':len(c['occurrences']),
        'matched':sum(o['matched'] for o in c['occurrences']),
        'exactlyFilledAtoms':sum(x==1 for x in totals) if d['filling']['exactTrainingEquations'] else None,
        'markConflictIncidences':conflicts})
assert summaries==d['summary'] and training_exact==d['filling']['exactTrainingEquations']
# Reconstruct the maximal equality partition from training overlaps.
parent=list(range(len(d['scalarLabels'])))
def root(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for sites in incidences:
    for s in sites[1:]:parent[root(s)]=root(sites[0])
a=defaultdict(set);b=defaultdict(set)
for i,label in enumerate(d['scalarLabels']):a[root(i)].add(label);b[label].add(root(i))
assert all(len(v)==1 for v in a.values()) and all(len(v)==1 for v in b.values())
out={'verifiedConfigurations':len(summaries),'typeCount':len(d['types']),'maximumPeriodicResidualAngstrom':maxres,
 'rationalTrainingFilling':training_exact,'scalarClasses':len(a),'summary':summaries,
 'scope':'Registered finite candidates and shared-value precheck only. No continuous completeness, infeasibility certificate, or growth claim.'}
with Path(sys.argv[4]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='summary'},indent=2))
