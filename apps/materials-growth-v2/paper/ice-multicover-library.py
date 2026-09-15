"""Build comparable one-cover and multi-cover raw-cloud training libraries.

Both use the same learned six-site geometry and marking radius. Endpoint clouds
are training observations in the base frame, without junction prototype fitting.
The second library only adds contexts from alternative covers of training atoms.
Uniform-half t is inherited from the declared decomposition, not learned here.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('p',Path(__file__).with_name('ice-portable-pairs.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
coordinates,cover_path,dictionary_path,selection_path,alternative_path,original_out,augmented_out=sys.argv[1:]
paths=[coordinates,cover_path,dictionary_path,selection_path]
corpus,cover,dictionary,selection=[json.loads(Path(path).read_text()) for path in paths]
alternative=json.loads(Path(alternative_path).read_text())
assert dictionary['coordinateHash']==sha(coordinates) and dictionary['coverHash']==sha(cover_path)
assert alternative['originalSelectionHash']==sha(selection_path) and alternative['dictionaryHash']==sha(dictionary_path)
cv={r['id']:r for r in cover['results']};dc={r['id']:r for r in dictionary['configurations']}
ss={r['id']:r for r in selection['results']};aa={r['id']:r for r in alternative['results']}
bases=[];motifs=[];registrations=[];base_ids={};intern={}
for lane,destination in [('original',original_out),('alternative',augmented_out)]:
    for c in corpus['configurations']:
        cid=c['id'];d=dc[cid]
        if not d['training']:continue
        if lane=='alternative' and aa[cid]['unchanged']:continue
        selected=(ss if lane=='original' else aa)[cid]['selected'];observation=cv[cid]
        values={q['root']:p.cloud_value(q) for q in p.junction.junctions(c,observation,selected)}
        rows=[]
        for edge in selected:
            o=d['occurrences'][edge];assert o['matched']
            ends=p.endpoints(o,observation['components'],observation['componentPairs'][edge]);key=p.base_key(o,ends)
            if key not in base_ids:
                base_ids[key]=len(bases);t=dictionary['types'][o['type']];positions=t['positions']
                bases.append(dict(pairType=o['type'],anchors=positions,species=t['species'],t=[1]*len(positions),
                    componentSites=[sites for sites,_ in ends],markAnchors=[np.asarray(positions)[sites].mean(axis=0).tolist() for sites,_ in ends]))
            rotation=np.asarray(o['rotationRow'])
            motif=dict(base=base_ids[key],cloudM=[p.cloud.transform(values[root],rotation.T) for _,root in ends])
            serial=json.dumps(motif,sort_keys=True)
            if serial not in intern:intern[serial]=len(motifs);motifs.append(motif)
            rows.append(dict(edge=edge,motif=intern[serial],roots=[root for _,root in ends]))
        registrations.append(dict(id=cid,coverVariant=lane,selected=rows))
    data=dict(scope=__doc__,sourceHashes=dict(zip(['coordinates','cover','dictionary','selection'],map(sha,paths))),
        alternativeCoverHash=sha(alternative_path) if lane=='alternative' else None,codeHash=sha(__file__),
        capacity=2,positionToleranceAngstrom=dictionary['epsilonAngstrom'],markingRadiusAngstrom=dictionary['epsilonAngstrom'],
        baseMotifs=bases,motifs=motifs,trainingRegistrations=registrations,
        summary=dict(baseMotifs=len(bases),decoratedMotifs=len(motifs),trainingConfigurations=len({r['id'] for r in registrations}),trainingCovers=len(registrations)),
        limits='Observed raw-cloud library; same geometry/t and radius in both lanes. No compression, negative-connection guarantee, search result, or condition-matched admission claim.')
    with Path(destination).open('x') as f:json.dump(data,f)
    print(json.dumps(dict(lane=lane,**data['summary'])),flush=True)
