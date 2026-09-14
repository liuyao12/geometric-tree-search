"""Independently reconstruct cross-configuration motif-count rankings.

This verifies only withholding for ranking. The motif/weight model was jointly
trained, so this must not be reported as wholly held-out reconstruction.
"""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


def verify(input_path,learning_path,prior_path,search_path,runner_snapshot=None):
    raw=Path(input_path).read_bytes();lr=Path(learning_path).read_bytes();pr=Path(prior_path).read_bytes()
    d=json.loads(raw);learning=json.loads(lr);prior=json.loads(pr);checks=[]
    assert prior['inputHash']==learning['inputHash']==hashlib.sha256(raw).hexdigest()
    assert prior['learningHash']==hashlib.sha256(lr).hexdigest()
    assert len(prior['folds'])==len(d['configurations'])
    for target,fold in enumerate(prior['folds']):
        assert fold['excluded']==target and fold['file']==d['configurations'][target]['file']
        assert fold['trainingConfigurations']==[i for i in range(len(d['configurations'])) if i!=target]
        totals=[0]*len(d['types']);selected=[0]*len(totals)
        for source in fold['trainingConfigurations']:
            chosen=set(learning['result']['selected'][source]);c=d['configurations'][source]
            for i,o in enumerate(c['occurrences']):totals[o['type']]+=1;selected[o['type']]+=i in chosen
        scores=[Fraction(s+1,n+2) for s,n in zip(selected,totals)];unique=sorted(set(scores))
        assert len(fold['types'])==len(totals)
        for ti,row in enumerate(fold['types']):
            assert row=={'type':ti,'selected':selected[ti],'observed':totals[ti],
                        'numerator':selected[ti]+1,'denominator':totals[ti]+2,'rank':unique.index(scores[ti])}
        checks.append({'fold':target,'trainingConfigurations':fold['trainingConfigurations'],
                       'unseenTypes':sum(n==0 for n in totals),'distinctRanks':len(unique)})
        for marked in (False,True):
            run=json.loads((Path(search_path)/f'{target}-{str(marked).lower()}.json').read_text())
            assert run['inputHash']==prior['inputHash'] and run['learningHash']==prior['learningHash']
            assert run['result']['priorHash']==hashlib.sha256(pr).hexdigest() and run['result']['ordering']=='type-prior'
            assert len(run['model']['candidates'])==len(d['configurations'][target]['occurrences'])
            for name,digest in run['researchSourceHashes'].items():
                source=Path(runner_snapshot) if runner_snapshot and name=='boron-face-reference-search.mjs' else Path(__file__).with_name(name)
                assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    return {'scope':__doc__,'priorHash':hashlib.sha256(pr).hexdigest(),'folds':checks,'verifiedSearchBindings':2*len(checks),
            'scopeLimitation':'Target selected witness withheld only for ranking; shared dictionary and t/m values use all six inputs.'}


if __name__=='__main__':
    out=verify(*sys.argv[1:5],runner_snapshot=sys.argv[6] if len(sys.argv)>6 else None)
    with Path(sys.argv[5]).open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))
