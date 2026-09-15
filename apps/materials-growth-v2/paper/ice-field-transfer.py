"""Frozen 80-fit/20-calibration/100-developmental field-cover diagnostic."""
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import time
import numpy as np
from scipy.spatial.distance import cdist

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
f=module('fields','gaussian-section-markings.py');p=module('portable','ice-portable-pairs.py')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
coordinates,cover_path,dictionary_path,selection_path,library_path,output=map(Path,sys.argv[1:])
corpus,cover,dictionary,selection,library=[json.loads(path.read_text()) for path in [coordinates,cover_path,dictionary_path,selection_path,library_path]]
for key,path in [('coordinates',coordinates),('cover',cover_path),('dictionary',dictionary_path),('selection',selection_path)]:assert library['sourceHashes'][key]==sha(path)
cc={c['id']:c for c in corpus['configurations']};cv={c['id']:c for c in cover['results']};dd={c['id']:c for c in dictionary['configurations']};ss={c['id']:c for c in selection['results']}
fit={f'c{offset+i:05d}' for offset in [0,500,1000,1500] for i in range(20)}
cal=[f'c{offset+i:05d}' for offset in [0,500,1000,1500] for i in range(20,25)]
dev=[f'c{offset+i:05d}' for offset in [400,900,1400,1900] for i in range(25)]
assert len(fit)==80 and len(cal)==20 and len(dev)==100 and not (fit&set(cal) or fit&set(dev))
assert all(dd[c]['training'] for c in fit|set(cal)) and all(not dd[c]['training'] for c in dev)
allowed=set()
for reg in library['trainingRegistrations']:
    if reg['id'] in fit:allowed.update(x['motif'] for x in reg['selected'])
bybase=defaultdict(list)
for i in sorted(allowed):bybase[library['motifs'][i]['base']].append(i)
bases={json.dumps([b['pairType'],b['componentSites']]):i for i,b in enumerate(library['baseMotifs'])}
def prepare(field):
    v,a,c=f.validate(field)
    value=(v,a,np.asarray(c),field['sigma'])
    return value,inner(value,value)
def inner(a,b):
    x,wa,ca,sigma=a;y,wb,cb,sigma2=b;assert sigma==sigma2
    return float(np.sum(wa[:,None]*wb[None,:]*np.exp(-cdist(x,y,'sqeuclidean')/(2*sigma*sigma))*(ca[:,None]==cb[None,:])))
prepared={i:[prepare(x) for x in library['motifs'][i]['fieldM']] for i in sorted(allowed)}
def distance(a,b):
    av,aa=a;bv,bb=b;raw=math.fsum([aa,bb,-2*inner(av,bv)])
    guard=128*np.finfo(float).eps*max(1.,(sum(abs(av[1]))+sum(abs(bv[1])))**2)
    assert raw>=-guard
    return math.sqrt(max(0.,raw))
rows=[];threshold=None;start=time.monotonic()
for split,ids in [('calibration',cal),('developmental',dev)]:
    for cid in ids:
        c=cc[cid];v=cv[cid];assert all(c.get('pbc',[True]*3));values={}
        for root,atoms in enumerate(v['components']):
            center=p.junction.geometry.lift(c,atoms).mean(axis=0)
            values[root]=f.periodic_field(c['positions'],c['species'],c['cell'],center,library['supportRadiusAngstrom'],library['kernelWidthAngstrom'])
        matches=[]
        for edge in ss[cid]['selected']:
            o=dd[cid]['occurrences'][edge];ends=p.endpoints(o,v['components'],v['componentPairs'][edge])
            base=bases.get(p.base_key(o,ends));best=math.inf;winner=None;ds=None
            queries=[prepare(f.transform(values[root],np.asarray(o['rotationRow']).T)) for _,root in ends]
            for i in bybase.get(base,[]):
                d0=distance(queries[0],prepared[i][0])
                if d0>best:continue
                d1=distance(queries[1],prepared[i][1]);d=max(d0,d1)
                if d<best:best=d;winner=i;ds=[d0,d1]
            matches.append(dict(edge=edge,base=base,motif=winner,radius=best if math.isfinite(best) else None,endpointDistances=ds))
        missing=sum(x['radius'] is None for x in matches);finite=[x['radius'] for x in matches if x['radius'] is not None]
        row=dict(id=cid,split=split,occurrences=len(matches),missingFitBase=missing,requiredRadius=max(finite) if finite and not missing else None,matches=matches)
        if split=='developmental':row.update(accepted=sum(x['radius'] is not None and x['radius']<=threshold for x in matches),complete=all(x['radius'] is not None and x['radius']<=threshold for x in matches))
        rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='matches'}),flush=True)
    if split=='calibration':
        threshold=max(x['radius'] for r in rows for x in r['matches'] if x['radius'] is not None)+1e-8
        calibration_complete=all(r['requiredRadius'] is not None for r in rows)
        print(json.dumps(dict(frozenThreshold=threshold,completeCalibration=calibration_complete)),flush=True)
summary=dict(fitConfigurations=len(fit),fitDecorations=len(allowed),calibrationConfigurations=len(cal),calibrationFullyRepresented=calibration_complete,
             diagnosticThreshold=threshold,developmentalConfigurations=len(dev),developmentalComplete=sum(r.get('complete',False) for r in rows),
             developmentalOccurrences=sum(r['occurrences'] for r in rows if r['split']=='developmental'),developmentalAccepted=sum(r.get('accepted',0) for r in rows),
             developmentalMissingFitBase=sum(r['missingFitBase'] for r in rows if r['split']=='developmental'))
report=dict(scope=__doc__,protocolHash=sha(Path(__file__).with_name('ICE-FIELD-TRANSFER-PROTOCOL.md')),libraryHash=sha(library_path),codeHash=sha(Path(__file__)),
            fitFrames=sorted(fit),calibrationFrames=cal,developmentalFrames=dev,summary=summary,results=rows,seconds=time.monotonic()-start,
            limits='Positive supplied-cover precheck on fixed base poses. Base dictionary previously saw calibration geometry. No independent-trajectory or same-condition certification, specificity, independent witness replay, or search. Threshold is field-norm units, not Angstroms.')
with output.open('x') as out:json.dump(report,out)
print(json.dumps(summary),flush=True)
