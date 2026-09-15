"""Export an ambient-context control on exactly the existing training supports.

Same anchors, base identities, integer half weights and training registrations;
different m-cloud neighborhoods. Local contexts use all geometric neighbor
proposals and never inspect which cover is selected. No reconstruction claim.
"""
import hashlib
import importlib.util
import json
from collections import Counter,defaultdict
from pathlib import Path
import sys
import numpy as np
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
ambient=module('ambient','ice-ambient-context.py');portable=module('portable','ice-portable-pairs.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
coordinates,cover_path,dictionary_path,prior_path,output=map(Path,sys.argv[1:])
corpus,cover,dictionary,prior=[json.loads(p.read_text()) for p in [coordinates,cover_path,dictionary_path,prior_path]]
assert prior['sourceHashes']['coordinates']==dictionary['coordinateHash']==cover['coordinateHash']==sha(coordinates)
assert prior['sourceHashes']['cover']==dictionary['coverHash']==sha(cover_path)
assert prior['sourceHashes']['dictionary']==sha(dictionary_path)
cc={r['id']:r for r in corpus['configurations']};cv={r['id']:r for r in cover['results']};dd={r['id']:r for r in dictionary['configurations']}
cache={};motifs=[];intern={};registrations=[];old_by_occurrence=defaultdict(set);new_by_occurrence=defaultdict(set);sizes=Counter();checked=0
for reg in prior['trainingRegistrations']:
    cid=reg['id'];assert dd[cid]['training']
    if cid not in cache:
        rows=list(ambient.contexts(cc[cid],cv[cid]));cache[cid]={r['root']:portable.cloud_value(r) for r in rows}
        sizes.update(len(r['vectors']) for r in rows)
    selected=[];totals=[0]*len(cc[cid]['positions'])
    for placement in reg['selected']:
        edge=placement['edge'];o=dd[cid]['occurrences'][edge];assert o['matched']
        ends=portable.endpoints(o,cv[cid]['components'],cv[cid]['componentPairs'][edge]);rotation=np.asarray(o['rotationRow'])
        base=prior['motifs'][placement['motif']]['base'];b=prior['baseMotifs'][base]
        assert b['pairType']==o['type'] and b['componentSites']==[sites for sites,_ in ends]
        value=dict(base=base,cloudM=[portable.cloud.transform(cache[cid][root],rotation.T) for _,root in ends])
        serial=json.dumps(value,sort_keys=True)
        if serial not in intern:intern[serial]=len(motifs);motifs.append(value)
        selected.append(dict(placement,motif=intern[serial]))
        old_by_occurrence[cid,edge].add(placement['motif']);new_by_occurrence[cid,edge].add(intern[serial])
        for atom in o['ids']:totals[atom]+=1
        for side,(_,root) in enumerate(ends):
            transported=portable.cloud.transform(value['cloudM'][side],rotation)
            assert portable.cloud.contains(transported,cache[cid][root],1e-8) is not None
            checked+=1
    assert all(t==2 for t in totals)
    registrations.append(dict(reg,selected=selected))
assert all(len(values)==1 for values in new_by_occurrence.values())
report=dict(scope=__doc__,sourceHashes=prior['sourceHashes'],priorLibraryHash=sha(prior_path),
            codeHashes={n:sha(Path(__file__).with_name(n)) for n in ['ice-ambient-marking-library.py','ice-ambient-context.py']},
            capacity=prior['capacity'],positionToleranceAngstrom=prior['positionToleranceAngstrom'],markingRadiusAngstrom=prior['markingRadiusAngstrom'],
            baseMotifs=prior['baseMotifs'],motifs=motifs,trainingRegistrations=registrations,
            summary=dict(baseMotifs=len(prior['baseMotifs']),decoratedMotifs=len(motifs),trainingConfigurations=len(cache),trainingCovers=len(registrations),
                         distinctSelectedOccurrences=len(new_by_occurrence),occurrencesWithCoverDependentOldMarkings=sum(len(v)>1 for v in old_by_occurrence.values()),
                         occurrencesWithCoverDependentNewMarkings=0,verifiedTransportAssignments=checked,ambientCloudSizeHistogram=dict(sizes)),
            limits='Positive supplied-cover consistency, not search or transfer. Full local geometric proposal graph is frozen from prior training; marking radii and t halves inherited. Cover-independent does not mean boundary/neighbor-graph independent, physically complete, or a continuous-space model.')
with output.open('x') as f:json.dump(report,f)
print(json.dumps(report['summary']))
