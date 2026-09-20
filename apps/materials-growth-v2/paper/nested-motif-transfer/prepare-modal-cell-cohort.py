"""Geometry-development split: modal atom count per source file, first 120 fit.

No phase/temperature/pressure fields enter coordinate records. This is not a
physical-state classifier or independent-trajectory split.
"""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
coordp,provp,out=map(Path,sys.argv[1:]);out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
data=json.loads(coordp.read_text());provenance=json.loads(provp.read_text())
assert provenance['coordinateHash']==sha(coordp)
selected=[];rules=[]
for source in sorted({r['sourceHash'] for r in provenance['configurations']}):
    rows=sorted([r for r in provenance['configurations'] if r['sourceHash']==source and r['periodic']],key=lambda r:r['sourceFrame'])
    counts=Counter(r['atoms'] for r in rows);mode=max(counts,key=counts.get)
    assert sum(n==max(counts.values()) for n in counts.values())==1
    eligible=[r for r in rows if r['atoms']==mode];assert len(eligible)>120
    selected.extend(dict(r,split='train' if i<120 else 'test') for i,r in enumerate(eligible))
    rules.append(dict(sourceHash=source,modalAtomCount=mode,selected=len(eligible),excluded=len(rows)-len(eligible),train=120,test=len(eligible)-120))
ids={r['id'] for r in selected};coords=[c for c in data['configurations'] if c['id'] in ids]
with (out/'coordinates.json').open('x') as f:json.dump(dict(configurations=coords),f)
with (out/'metadata.json').open('x') as f:json.dump(dict(configurations=selected),f)
with (out/'selection.json').open('x') as f:json.dump(dict(scope=__doc__,sourceCoordinateHash=sha(coordp),sourceProvenanceHash=sha(provp),codeHash=sha(Path(__file__)),rules=rules,coordinateHash=sha(out/'coordinates.json'),metadataHash=sha(out/'metadata.json'),conditionMatched=False),f,indent=2)
print(json.dumps(rules))
