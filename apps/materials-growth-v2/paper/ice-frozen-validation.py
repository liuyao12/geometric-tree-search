"""Register the untouched 300 author-validation frames against frozen learned tiles.

Admit only types whose every positive site is forced to 1/2 by the training
weight certificate. Retain the other types in provenance, not as filled-in weights.
No geometry, tolerance, threshold, or dictionary update uses validation frames.
"""
import json
import hashlib
import importlib.util
from pathlib import Path
import sys
import numpy as np

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
geometry=module('geometry','ice-motif-dictionary.py');proposal=module('proposal','ice-overlap-cover.py')
source=Path(sys.argv[1]);draw=Path(sys.argv[2]).read_bytes();d=json.loads(draw);cover_raw=Path(sys.argv[3]).read_bytes();prior=json.loads(cover_raw)
wraw=Path(sys.argv[4]).read_bytes();weights=json.loads(wraw);out=Path(sys.argv[5]);out.mkdir()
assert weights['dictionaryHash']==hashlib.sha256(draw).hexdigest()
assert d['coverHash']==hashlib.sha256(cover_raw).hexdigest()
all_data=json.loads((source/'coordinates.json').read_text())['configurations'];all_meta=json.loads((source/'provenance.json').read_text())['configurations']
meta=[c for c in all_meta if c['split']=='test' and c['sourceFrame']>=25];ids={c['id'] for c in meta}
corpus=[c for c in all_data if c['id'] in ids];assert len(corpus)==300 and not(ids&{c['id'] for c in d['configurations']})
forced={s for c in weights['components'] if c['kind']=='forced-half' for s in c['sites']}
admitted=[i for i,(a,b) in enumerate(zip(d['offsets'],d['offsets'][1:])) if set(range(a,b))<=forced]
descriptors=[]
for t in d['types']:
    x=np.array(t['positions']);descriptors.append(np.sort(np.linalg.norm(x[:,None]-x[None,:],axis=2)[np.triu_indices(len(x),1)]))
descriptors=np.array(descriptors);perms={};registered=[];covers=[];labels=[None]*d['offsets'][-1]
for i,component in enumerate(weights['components']):
    for s in component['sites']:labels[s]=i
for c in corpus:
    parts,cross=proposal.prepare(c,prior['componentThreshold']);pairs=[[i,j] for i in range(len(parts)) for j in range(i+1,len(parts)) if cross[i,j]<prior['interfaceThreshold']]
    supports=[sorted(parts[i]+parts[j]) for i,j in pairs];occurrences=[]
    for support in supports:
        order=sorted(support,key=lambda i:(c['species'][i],i));species=tuple(c['species'][i] for i in order);positions=geometry.lift(c,order)
        if len(order)!=6:
            occurrences.append({'ids':order,'matched':False,'reason':'no six-site type'});continue
        descriptor=np.sort(np.linalg.norm(positions[:,None]-positions[None,:],axis=2)[np.triu_indices(6,1)])
        if species not in perms:perms[species]=geometry.maps(species)
        found=None
        possible=[i for i in admitted if np.max(np.abs(descriptors[i]-descriptor))<=2*d['epsilonAngstrom']+1e-10]
        for ti in possible:
            t=d['types'][ti]
            if tuple(t['species'])!=species:continue
            fit=geometry.fit(t['positions'],positions,perms[species],d['epsilonAngstrom'])
            if fit is not None:found={'ids':order,'matched':True,'type':ti,**fit};break
        occurrences.append(found if found else {'ids':order,'matched':False,'reason':'no witnessed admitted-type fit'})
    registered.append({'id':c['id'],'training':False,'atoms':len(c['positions']),'occurrences':occurrences})
    covers.append({'id':c['id'],'components':parts,'componentPairs':pairs,'supports':supports})
    print(json.dumps({'id':c['id'],'proposals':len(occurrences),'matched':sum(o['matched'] for o in occurrences)}),flush=True)
(out/'coordinates.json').write_text(json.dumps({'configurations':corpus}))
(out/'provenance.json').write_text(json.dumps({'configurations':meta}))
(out/'cover.json').write_text(json.dumps({'results':covers,'componentThreshold':prior['componentThreshold'],'interfaceThreshold':prior['interfaceThreshold']}))
result={'scope':__doc__,'sourceDictionaryHash':hashlib.sha256(draw).hexdigest(),'weightCertificateHash':hashlib.sha256(wraw).hexdigest(),
 'coordinateHash':hashlib.sha256((out/'coordinates.json').read_bytes()).hexdigest(),'coverHash':hashlib.sha256((out/'cover.json').read_bytes()).hexdigest(),
 'types':d['types'],'offsets':d['offsets'],'admittedTypeIds':admitted,'epsilonAngstrom':d['epsilonAngstrom'],'scalarLabels':labels,
 'configurations':registered,'fixedWeight':'1/2','summary':{'configurations':len(registered),'admittedTypes':len(admitted),
 'unidentifiedTypes':len(d['types'])-len(admitted),'proposals':sum(len(c['occurrences']) for c in registered),
 'matched':sum(o['matched'] for c in registered for o in c['occurrences'])}}
(out/'dictionary.json').write_text(json.dumps(result));print(json.dumps(result['summary']),flush=True)
