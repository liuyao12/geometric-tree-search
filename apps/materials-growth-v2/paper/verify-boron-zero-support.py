"""Independent rational exclusion verifier plus training-witness preservation."""
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path

inp,learned,proofpath,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];proof=json.loads(proofpath.read_text())
assert proof['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest()
assert proof['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
checks=[]
for fold,(cfg,row) in enumerate(zip(d['configurations'],proof['results'],strict=True)):
    assert row['fold']==fold and row['file']==cfg['file']
    cert=row['certificate']
    if cert:
        excluded=set(cert['excluded']);assert len(excluded)==len(cert['excluded']) and excluded<=set(range(len(cfg['occurrences'])))
        y={p:F(v) for p,v in cert['y']};z={j:F(v) for j,v in cert['z']}
        assert len(y)==len(cert['y']) and len(z)==len(cert['z'])
        assert set(y)<=set(range(cfg['atoms'])) and set(z)<=set(range(len(cfg['occurrences'])))
        assert all(v>=0 for v in z.values())
        for j,o in enumerate(cfg['occurrences']):
            lhs=z.get(j,F(0))
            for u,p in enumerate(o['ids']):
                role=r['roleOfSite'][d['types'][o['type']]['offset']+u]
                lhs+=y.get(p,F(0))*r['weightsByRole'][role]
            assert lhs>=int(j in excluded)
        upper=r['capacity']*sum(y.values())+sum(z.values())
        assert upper==F(cert['bound']) and upper<1
        assert not excluded.intersection(r['selected'][fold])
    else:excluded=set()
    assert row['excluded']==len(excluded)
    checks.append({'file':cfg['file'],'excluded':len(excluded),'trainingWitnessPreserved':True})
out={'scope':'Exact exclusions in the supplied complete finite candidate models; not a proof that every retained candidate admits integer completion.',
     'proofHash':hashlib.sha256(proofpath.read_bytes()).hexdigest(),'checks':checks}
dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
