"""Six-frame periodic-field extraction control; not training or tree search.

Uses first eight previously inferred component-centroid anchors per frame.
Window/width are diagnostic choices, not calibrated marking tolerances.
Independent image enumeration uses a fixed [-4,4]^3 box for these cells,
after checking its adequacy from singular-value lower bounds.
"""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import numpy as np

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

m=module('fields','gaussian-section-markings.py')
ambient=module('ambient','ice-ambient-context.py')
coordinates,coverfile,output=map(Path,sys.argv[1:])
corpus=json.loads(coordinates.read_text());covers=json.loads(coverfile.read_text())
cc={x['id']:x for x in corpus['configurations']};cv={x['id']:x for x in covers['results']}
q,_=np.linalg.qr(np.random.default_rng(551).normal(size=(3,3)))
if np.linalg.det(q)<0:q[:,0]*=-1
rows=[]
for cid in ['c00000','c00400','c00500','c00900','c01000','c01400']:
    c=cc[cid];cell=np.asarray(c['cell']);p=np.asarray(c['positions'])
    assert all(c.get('pbc',[True]*3))
    for root,ids in enumerate(cv[cid]['components'][:8]):
        anchor=ambient.junction.geometry.lift(c,ids).mean(axis=0)
        # Root anchor is inferred geometry. Every atom has only its opaque
        # source label; no molecular role, energy, or selected cover is read.
        f=m.periodic_field(p,c['species'],cell,anchor,4.,.4)
        fractional=(p-anchor)@np.linalg.inv(cell)
        fractional-=np.floor(fractional+.5)
        wrapped=fractional@cell
        # Any omitted shift has norm >=5. Reverse triangle inequality gives
        # a strict lower bound for its image distance in this finite check.
        bound=5*np.linalg.svd(cell,compute_uv=False)[-1]-max(np.linalg.norm(wrapped,axis=1))
        assert bound>4., (cid,bound)
        vectors=[];labels=[]
        for shift in itertools.product(range(-4,5),repeat=3):
            x=wrapped+np.asarray(shift)@cell
            for i in np.flatnonzero(np.linalg.norm(x,axis=1)<4.):
                vectors.append(x[i]);labels.append(c['species'][i])
        # Compare the complete weighted point lists, not only an aggregate
        # norm that might obscure missed contributions.
        def ordered(v,colors):
            return sorted([(str(label),*map(float,x)) for x,label in zip(v,colors)])
        actual=ordered(f['vectors'],f['colors']);expected=ordered(vectors,labels)
        assert len(actual)==len(expected)
        assert [a[0] for a in actual]==[a[0] for a in expected]
        residual=float(np.max(np.abs(np.array([a[1:] for a in actual])-np.array([a[1:] for a in expected]))))
        assert residual<1e-10
        rotated=m.periodic_field(p@q+2,c['species'],cell@q,anchor@q+2,4.,.4)
        d=m.discrepancy(m.transform(f,q),rotated)
        assert d['squared']<=d['roundoffGuard']
        rows.append(dict(id=cid,root=root,points=len(actual),coordinateResidualAngstrom=residual,
                         rotationSquaredDiscrepancy=d['squared'],roundoffGuard=d['roundoffGuard']))
report=dict(scope=__doc__,radiusAngstrom=4.,sigmaAngstrom=.4,frames=6,anchors=len(rows),
            sourceHashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [coordinates,coverfile]},
            codeHashes={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['gaussian-section-markings.py','check-ice-periodic-fields.py']},
            results=rows,limitations='Fixed diagnostic radius/width; inherited anchors; no learned t/m fit, negative-connection test, search integration or growth. Numerical checks, not exact certification. Same-condition provenance remains unverified.')
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(frames=6,anchors=len(rows),fieldPoints=sum(r['points'] for r in rows),
                     maximumCoordinateResidual=max(r['coordinateResidualAngstrom'] for r in rows))))
