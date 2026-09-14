"""Independent exact dual verification; no optimizer imported."""
import json
from pathlib import Path
from fractions import Fraction as F
import sys
d={c['id']:c for c in json.loads(Path(sys.argv[1]).read_text())['configurations']}
covers={c['id']:c for c in json.loads(Path(sys.argv[2]).read_text())['results']}
report=json.loads(Path(sys.argv[3]).read_text());verified=0
for r in report['results']:
    c=d[r['configuration']];assert c['training'];source=covers[c['id']]
    allowed=[i for i,o in enumerate(c['occurrences']) if o['matched']]
    edges=[source['componentPairs'][i] for i in allowed]
    assert allowed==r['allowedOccurrences'] and edges==r['edges'] and len(source['components'])==r['vertices']
    assert allowed[r['targetIndex']]==r['requiredOccurrence'] and c['occurrences'][r['requiredOccurrence']]['type']==r['targetType']
    p=r['certificate']
    if p is None:continue
    y=list(map(F,p['degreeDual']));lo=list(map(F,p['lowerDual']));hi=list(map(F,p['upperDual']))
    assert len(y)==r['vertices'] and len(lo)==len(hi)==len(edges)
    assert all(x>=0 for x in lo) and all(x<=0 for x in hi)
    for i,(a,b) in enumerate(edges):assert y[a]+y[b]+lo[i]+hi[i]==(-1 if i==r['targetIndex'] else 0)
    assert 2*sum(y,F())+sum(hi,F())==F(p['objectiveLowerBound'])==0
    verified+=1
assert verified==report['exactExcludedEdgeCertificates']
out={'exactlyVerifiedExcludedEdgeCertificates':verified,'scope':report['scope'],'optimizerUsedByVerifier':False}
with Path(sys.argv[4]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
