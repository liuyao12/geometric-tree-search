"""Leave-one-configuration-out motif-frequency ranking, not a legality rule.

The geometric dictionary and weights are still jointly fitted on all six inputs.
Only this ranking withholds the target's selected witness; not a held-out model
test, probability calibration, physical ensemble or learned GCTS marking.
"""
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


def fit_priors(d,selected):
    assert len(selected)==len(d['configurations']);folds=[]
    for excluded,target in enumerate(d['configurations']):
        successes=Counter();trials=Counter();sources=[]
        for i,c in enumerate(d['configurations']):
            if i==excluded:continue
            sources.append(i);assert len(set(selected[i]))==len(selected[i])
            trials.update(o['type'] for o in c['occurrences'])
            successes.update(c['occurrences'][j]['type'] for j in selected[i])
        scores=[Fraction(successes[ti]+1,trials[ti]+2) for ti in range(len(d['types']))]
        ranks={score:i for i,score in enumerate(sorted(set(scores)))}
        rows=[{'type':ti,'selected':successes[ti],'observed':trials[ti],
               'numerator':successes[ti]+1,'denominator':trials[ti]+2,'rank':ranks[scores[ti]]}
              for ti in range(len(d['types']))]
        folds.append({'excluded':excluded,'file':target['file'],'trainingConfigurations':sources,'types':rows})
    return folds


if __name__=='__main__':
    raw=Path(sys.argv[1]).read_bytes();lr=Path(sys.argv[2]).read_bytes();d=json.loads(raw);learning=json.loads(lr)
    assert learning['inputHash']==hashlib.sha256(raw).hexdigest()
    out={'scope':__doc__,'inputHash':hashlib.sha256(raw).hexdigest(),'learningHash':hashlib.sha256(lr).hexdigest(),
         'estimator':'(selected + 1) / (observed + 2), exact-rational ordering; unseen type gets 1/2',
         'folds':fit_priors(d,learning['result']['selected'])}
    with Path(sys.argv[3]).open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps({'folds':len(out['folds']),'types':len(d['types']),'scope':__doc__}))
