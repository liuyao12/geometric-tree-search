"""Independent holdout/provenance and frozen-weight replay; not a growth verifier."""
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import numpy as np

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('geometry_verifier',HERE/'verify-boron-triples.py')
geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)

def verify(source_path,folder):
    source_path=Path(source_path);folder=Path(folder)
    raw=source_path.read_bytes();source=json.loads(raw)['results'];results=[]
    for index in range(6):
        root=folder/str(index);train=json.loads((root/'training-input.json').read_text())
        assert train['results']==[c for i,c in enumerate(source) if i!=index]
        frozen=(root/'training-dictionary.json').read_bytes();dictionary=json.loads(frozen)
        test=json.loads((root/'test-result.json').read_text());result=test['result'];c=test['testConfiguration']
        assert test['sourceHash']==hashlib.sha256(raw).hexdigest()
        assert test['frozenDictionaryHash']==hashlib.sha256(frozen).hexdigest()
        assert c['file']==result['heldOut']==source[index]['file']
        assert c['atoms']==source[index]['atoms'] and test['epsilonAngstrom']==dictionary['epsilonAngstrom']
        assert all(c['file']!=t['file'] for t in dictionary['configurations'])
        # Each template must have an exact originating occurrence in the training input.
        origins=set()
        for t in dictionary['configurations']:
            for o in t['occurrences']:
                lifted=np.array(o['liftedPositions'])[o['permutation']]
                if np.max(np.abs(np.array(dictionary['types'][o['type']]['positions'])-(lifted-lifted.mean(axis=0))))<1e-10:
                    origins.add(o['type'])
        assert origins==set(range(len(dictionary['types'])))
        geometry.verify(root/'training-input.json',root/'training-dictionary.json')
        # Reuse the independently implemented pose checks on held-out geometry only.
        checked={**dictionary,'inputHash':hashlib.sha256(raw).hexdigest(),'configurations':[c],'results':[]}
        with tempfile.TemporaryDirectory(prefix='gcts-boron-loo-check-') as tmp:
            path=Path(tmp)/'geometry.json';path.write_text(json.dumps(checked));geometry.verify(source_path,path)
        match={tuple(o['ids']) for o in c['occurrences']};missing={tuple(x) for x in test['unmatchedSupports']}
        assert not match.intersection(missing)
        assert len(match)==result['matched'] and len(missing)==result['unmatched']
        assert len(match)+len(missing)==result['supports']
        fit=dictionary['results'][-1];assert fit['status']==result['trainingStatus']
        if 'weights' in fit:
            w=list(map(Fraction,fit['weights']));labels=fit['labels']
            totals=[Fraction(0)]*c['atoms'];marks=[set() for _ in totals]
            for o in c['occurrences']:
                for u,p in enumerate(o['permutation']):
                    v=3*o['type']+u;point=o['ids'][p];totals[point]+=w[v];marks[point].add(labels[v])
            expected={'exactlyFilled':sum(x==1 for x in totals),'underfilled':sum(x<1 for x in totals),
                'overfilled':sum(x>1 for x in totals),'markingConflicts':sum(len(s)>1 for s in marks),
                'allMatchedCoverValid':all(x==1 for x in totals) and all(len(s)<=1 for s in marks)}
            assert all(result[k]==v for k,v in expected.items())
        results.append(result)
    assert json.loads((folder/'summary.json').read_text())['results']==results
    print(json.dumps({'verifiedFolds':len(results),'trainingOnlyTemplateOrigins':True,
        'validFrozenAllOccurrenceTestCovers':sum(r.get('allMatchedCoverValid',False) for r in results),
        'scope':'Known-coordinate restricted registrations, not exhaustive placement or blind growth'}))
if __name__=='__main__':verify(sys.argv[1],sys.argv[2])
