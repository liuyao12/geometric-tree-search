"""Geometric-neighborhood marked variants of frozen three-site motifs.

Descriptor: neighbor count within 1.35 times pooled training median nearest
distance, in the same finite minimum-image quotient as prior controls. Each
observed ordered triple of site descriptors is a marked variant. All variants
are offered at each test geometry; no test descriptor selects a candidate.
This is a declared descriptor hypothesis, not chemistry or general anchor learning.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
from ase import Atoms
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('geometry',HERE/'boron-triple-precheck.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
dest=Path(sys.argv[4]);dest.mkdir();summaries=[]
for fold in range(6):
    train_raw=(Path(sys.argv[1])/str(fold)/'training-input.json').read_bytes();train=json.loads(train_raw)['results']
    dr=(Path(sys.argv[1])/str(fold)/'training-dictionary.json').read_bytes();d=json.loads(dr)
    assert d['inputHash']==hashlib.sha256(train_raw).hexdigest()
    sr=(Path(sys.argv[2])/f'{fold}.json').read_bytes();selection=json.loads(sr)
    assert selection['trainingDictionaryHash']==hashlib.sha256(dr).hexdigest()
    distances={};nearest=[]
    for c in train:
        matrix=Atoms('B'*c['atoms'],positions=c['positions'],cell=c['cell'],pbc=True).get_all_distances(mic=True)
        np.fill_diagonal(matrix,np.inf);distances[c['file']]=matrix;nearest.extend(matrix.min(axis=1))
    radius=1.35*float(np.median(nearest));descriptors={name:(matrix<=radius).sum(axis=1).tolist() for name,matrix in distances.items()}
    variants=[set() for _ in d['types']];training_checks=[]
    for c in d['configurations']:
        for o in c['occurrences']:
            variants[o['type']].add(tuple(descriptors[c['file']][o['ids'][p]] for p in o['permutation']))
    variants=[sorted(v) for v in variants];assert all(variants)
    for c,fit in zip(d['configurations'],selection['trainingTrials'][-1]['fits']):
        assigned=[set() for _ in range(c['atoms'])];totals=[0]*c['atoms']
        for index in fit['selected']:
            o=c['occurrences'][index];mark=tuple(descriptors[c['file']][o['ids'][p]] for p in o['permutation'])
            assert mark in variants[o['type']]
            for p,label in zip(o['permutation'],mark):point=o['ids'][p];totals[point]+=1;assigned[point].add(label)
        assert all(t==selection['summary']['learnedDenominator'] for t in totals) and all(len(x)==1 for x in assigned)
        training_checks.append({'file':c['file'],'filledAtoms':len(totals),'markingConflicts':0})
    # Freeze before reading held-out registration data.
    library={'scope':__doc__,'trainingDictionaryHash':hashlib.sha256(dr).hexdigest(),
        'trainingInputHash':hashlib.sha256(train_raw).hexdigest(),'selectionHash':hashlib.sha256(sr).hexdigest(),
        'descriptorRadius':radius,'variants':variants,'trainingDescriptors':descriptors,'trainingChecks':training_checks}
    lr=json.dumps(library).encode();(dest/f'{fold}-library.json').write_bytes(lr)
    pr=(Path(sys.argv[3])/f'{fold}.json').read_bytes();pool=json.loads(pr)
    assert pool['frozenDictionaryHash']==hashlib.sha256(dr).hexdigest()
    seen_base=set();seen_candidates=set();candidates=[];poses=[]
    for o in pool['testConfiguration']['occurrences']:
        key=(o['type'],tuple(o['ids']))
        if key in seen_base:continue
        seen_base.add(key);t=d['types'][o['type']]
        for perm in g.PERMS:
            fit=g.geom.fit(t['positions'],o['liftedPositions'],np.array([perm]),d['epsilonAngstrom'])
            if fit is None:continue
            pose_index=len(poses);poses.append({'ids':o['ids'],'type':o['type'],'liftedPositions':o['liftedPositions'],**fit})
            inventory=json.dumps([o['type'],sorted(o['ids'])])
            for variant_index,mark in enumerate(variants[o['type']]):
                points=sorted((o['ids'][p],label) for p,label in zip(fit['permutation'],mark))
                identity=(inventory,tuple(points))
                if identity in seen_candidates:continue
                seen_candidates.add(identity)
                candidates.append({'id':f'{len(candidates):08d}','inventory':inventory,'pose':pose_index,'variant':variant_index,
                    't':[{'point':str(p),'value':1} for p in o['ids']],
                    'm':[{'point':str(p),'lo':label,'hi':label} for p,label in points]})
    assert (dest/f'{fold}-library.json').read_bytes()==lr
    model={'capacity':selection['summary']['learnedDenominator'],
           'required':list(map(str,range(pool['testConfiguration']['atoms']))),'candidates':candidates}
    summary={'fold':fold,'heldOut':pool['summary']['heldOut'],'geometricTypes':len(variants),
        'markedVariants':sum(map(len,variants)),'typesWithMultipleVariants':sum(len(v)>1 for v in variants),
        'descriptorLabels':sorted({label for v in variants for mark in v for label in mark}),
        'testBasePlacements':len(seen_base),'testMarkedCandidates':len(candidates)}
    (dest/f'{fold}.json').write_text(json.dumps({'summary':summary,'libraryHash':hashlib.sha256(lr).hexdigest(),
        'sourcePoolHash':hashlib.sha256(pr).hexdigest(),'poses':poses,'model':model}))
    print(json.dumps(summary),flush=True);summaries.append(summary)
(dest/'summary.json').write_text(json.dumps({'scope':__doc__,'results':summaries},indent=2))
