"""Maximally separating scalar marking under observed anchor equalities.

Scalar action is invariant under proper rotations. No unobserved pair is
labeled physically forbidden. This is conditional on the learned t-support.
"""
import hashlib
import itertools
import json
from collections import Counter,defaultdict
from pathlib import Path
import sys
supportp,checkp,out=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
support,check=[json.loads(p.read_text()) for p in [supportp,checkp]]
assert check['resultHash']==sha(supportp) and check['trainingPassed']==check['trainingTotal']==len(support['trainingFrames'])
anchors=support['anchors'];n=len(anchors);parents=list(range(n));sites=defaultdict(list)
def root(i):
    while parents[i]!=i:
        parents[i]=parents[parents[i]];i=parents[i]
    return i
for i,a in enumerate(anchors):
    for cid,atom in a['observations']:
        assert cid in support['trainingFrames']
        sites[cid,atom].append(i)
edges=set()
for values in sites.values():
    for a,b in itertools.combinations(sorted(set(values)),2):
        edges.add((a,b));ra,rb=root(a),root(b)
        if ra!=rb:parents[max(ra,rb)]=min(ra,rb)
classes=sorted({root(i) for i in range(n)})
labels={r:j for j,r in enumerate(classes)};m=[labels[root(i)] for i in range(n)]
sizes=Counter(m);class_species={str(k):sorted({a['species'] for i,a in enumerate(anchors) if m[i]==k}) for k in sizes}
assert all(len(v)==1 for v in class_species.values())
same_species=separable=implied=unobserved=0
for a,b in itertools.combinations(range(n),2):
    if anchors[a]['species']!=anchors[b]['species']:continue
    same_species+=1
    if (a,b) not in edges:
        unobserved+=1
        implied+=m[a]==m[b]
    separable+=m[a]!=m[b]
report=dict(scope=__doc__,supportHash=sha(supportp),supportCheckHash=sha(checkp),codeHash=sha(Path(__file__)),
            anchorCount=n,observedEqualityEdges=[list(e) for e in sorted(edges)],observedAtomicSites=len(sites),
            values=m,freeEqualityClasses=len(classes),equationRank=n-len(classes),classSizes=dict(sorted(sizes.items())),classSpecies=class_species,
            sameSpeciesAnchorPairs=same_species,separableSameSpeciesPairs=separable,
            unobservedSameSpeciesPairs=unobserved,forcedEqualUnobservedSameSpeciesPairs=implied,
            limits='Conditional exact equality model; fixed learned t-support and supplied training poses. Distinct class labels are gauge choices, not learned physical properties. Cross-class rejection is an unproved restriction outside observations. No geometry-valid negative set, m-support relocation, contextual decoration, held-out marking reconstruction or search acceleration.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['values','observedEqualityEdges','classSpecies','classSizes']}))
