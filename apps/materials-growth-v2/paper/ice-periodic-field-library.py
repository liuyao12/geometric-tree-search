"""Training-observed paired Gaussian fields on the frozen ice base library.

All atom images inside R contribute, independent of selected covering.
R and sigma are declared diagnostic choices, not learned parameters. Endpoint
fields use species as opaque labels and one shared motif rotation. No physics,
phase label or configuration identity occurs inside the marking value.
"""
import hashlib
import importlib.util
import json
from collections import Counter,defaultdict
from pathlib import Path
import sys
import numpy as np

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

field=module('field','gaussian-section-markings.py')
portable=module('portable','ice-portable-pairs.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

coordinates,cover_path,dictionary_path,prior_path,output=map(Path,sys.argv[1:])
corpus,cover,dictionary,prior=[json.loads(p.read_text()) for p in [coordinates,cover_path,dictionary_path,prior_path]]
assert prior['sourceHashes']['coordinates']==dictionary['coordinateHash']==cover['coordinateHash']==sha(coordinates)
assert prior['sourceHashes']['cover']==dictionary['coverHash']==sha(cover_path)
assert prior['sourceHashes']['dictionary']==sha(dictionary_path)
cc={r['id']:r for r in corpus['configurations']};cv={r['id']:r for r in cover['results']};dd={r['id']:r for r in dictionary['configurations']}
cache={};motifs=[];intern={};registrations=[];sizes=Counter();checked=0;residual=0.;seen=defaultdict(set)
for reg in prior['trainingRegistrations']:
    cid=reg['id'];assert dd[cid]['training'];c=cc[cid]
    assert all(c.get('pbc',[True]*3))
    if cid not in cache:
        cache[cid]={}
        for root,ids in enumerate(cv[cid]['components']):
            center=portable.junction.geometry.lift(c,ids).mean(axis=0)
            value=field.periodic_field(c['positions'],c['species'],c['cell'],center,4.,.4)
            cache[cid][root]=value;sizes[len(value['vectors'])]+=1
        print(json.dumps(dict(frame=cid,trainingFrames=len(cache))),flush=True)
    selected=[];totals=[0]*len(c['positions'])
    for placement in reg['selected']:
        edge=placement['edge'];o=dd[cid]['occurrences'][edge];assert o['matched']
        ends=portable.endpoints(o,cv[cid]['components'],cv[cid]['componentPairs'][edge])
        rotation=np.asarray(o['rotationRow']);base=prior['motifs'][placement['motif']]['base'];b=prior['baseMotifs'][base]
        assert b['pairType']==o['type'] and b['componentSites']==[sites for sites,_ in ends]
        value=dict(base=base,fieldM=[field.transform(cache[cid][root],rotation.T) for _,root in ends])
        serial=json.dumps(value,sort_keys=True)
        if serial not in intern:intern[serial]=len(motifs);motifs.append(value)
        selected.append(dict(placement,motif=intern[serial]));seen[cid,edge].add(intern[serial])
        for atom in o['ids']:totals[atom]+=1
        for side,(_,root) in enumerate(ends):
            transported=field.transform(value['fieldM'][side],rotation);expected=cache[cid][root]
            assert transported['colors']==expected['colors'] and transported['amplitudes']==expected['amplitudes']
            err=float(np.max(np.abs(np.asarray(transported['vectors'])-expected['vectors'])))
            assert err<1e-10;residual=max(residual,err);checked+=1
    assert all(t==2 for t in totals)
    registrations.append(dict(reg,selected=selected))
assert all(len(v)==1 for v in seen.values())
summary=dict(trainingConfigurations=len(cache),trainingCovers=len(registrations),baseMotifs=len(prior['baseMotifs']),
             observedDecorations=len(motifs),checkedEndpointTransports=checked,maximumTransportResidualAngstrom=residual,
             coverDependentOccurrences=0,fieldSizeHistogram=dict(sizes))
report=dict(scope=__doc__,sourceHashes=prior['sourceHashes'],priorLibraryHash=sha(prior_path),
            codeHashes={n:sha(Path(__file__).with_name(n)) for n in ['gaussian-section-markings.py','ice-periodic-field-library.py']},
            capacity=prior['capacity'],positionToleranceAngstrom=prior['positionToleranceAngstrom'],
            supportRadiusAngstrom=4.,kernelWidthAngstrom=.4,markingTolerance=None,
            baseMotifs=prior['baseMotifs'],motifs=motifs,trainingRegistrations=registrations,summary=summary,
            limits='Observed field catalogue, not learned compression or negative-connection rejection. Supplied t halves and anchors inherited. Positive round-trip transport only; independent all-cover witness verification pending. No search, developmental transfer, same-condition certification or beyond-input growth.')
with output.open('x') as f:json.dump(report,f)
print(json.dumps(summary),flush=True)
