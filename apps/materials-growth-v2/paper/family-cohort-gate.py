"""Evidence gates for claims, not chemistry rules or a ban on exploratory fitting.

Input records are external provenance, never geometry-learner features.
Unknown conditions cannot be grouped as though None were a shared state point.
"""
import json
import sys
from pathlib import Path


def assess(records):
    assert records and len({r['id'] for r in records})==len(records)
    assert all(r['split'] in ('train','test') and r['elements'] and
               all(isinstance(e,str) and e for e in r['elements']) for r in records)
    reasons=[]
    elements={tuple(sorted(set(r['elements']))) for r in records}
    if len(elements)!=1: reasons.append('different element sets')
    verified=[]
    for r in records:
        valid=(r.get('temperatureK') is not None and r.get('pressurePa') is not None
               and r.get('conditionEvidence')=='file-linked protocol'
               and bool(r.get('conditionSource')))
        if not valid: reasons.append('missing file-linked condition evidence');continue
        t,p=r['temperatureK'],r['pressurePa']
        if isinstance(t,bool) or isinstance(p,bool) or not isinstance(t,(int,float)) or not isinstance(p,(int,float)):
            reasons.append('invalid condition values');continue
        import math
        if not math.isfinite(t) or not math.isfinite(p) or t<0:
            reasons.append('invalid condition values');continue
        verified.append((t,p))
    if len(set(verified))>1:reasons.append('different declared conditions')
    condition_pass=not reasons
    independence=[]
    train={r.get('trajectoryId') for r in records if r['split']=='train'}
    test={r.get('trajectoryId') for r in records if r['split']=='test'}
    if not train or not test:independence.append('missing training or test group')
    if None in train or None in test or '' in train or '' in test:independence.append('unknown trajectory identities')
    if (train&test)-{None,''}:independence.append('trajectory shared across train and test')
    if any(r.get('independenceEvidence')!='documented independent runs' or not r.get('trajectorySource') for r in records):
        independence.append('independent runs not documented')
    return {'sameConditionClaimAdmitted':condition_pass,'conditionReasons':sorted(set(reasons)),
            'independentTrajectoryHoldoutAdmitted':condition_pass and not independence,
            'independenceReasons':sorted(set(independence)),
            'exploratoryGeometryTrainingAllowed':True,
            'scope':'Provenance claim gate only. Disjoint trajectory IDs alone do not establish independence; declared evidence requires audit. Same elements need not imply same composition, equilibrium or sampling distribution.'}


if __name__=='__main__':
    source,dest=map(Path,sys.argv[1:])
    records=json.loads(source.read_text())['records']
    result=assess(records)
    dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
