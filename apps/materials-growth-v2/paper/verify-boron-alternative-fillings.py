"""Rebuild all atom totals and connectedness without the fitting solver."""
import hashlib
import json
import sys
from pathlib import Path


def check(d,r,run):
    cfg=d['configurations'][run['fold']]
    assert run['file']==cfg['file']
    selected=run['selected']; assert len(set(selected))==len(selected)
    assert all(type(j) is int and 0<=j<len(cfg['occurrences']) for j in selected)
    totals=[0]*cfg['atoms']; labels=[set() for _ in totals]; neighbors=[set() for _ in totals]
    present=set()
    for j in selected:
        o=cfg['occurrences'][j]; present.add(o['type'])
        for site,p in enumerate(o['ids']):
            role=r['roleOfSite'][d['types'][o['type']]['offset']+site]
            w=r['weightsByRole'][role]; assert 0<w<=r['capacity']
            totals[p]+=w; labels[p].add(r['scalarLabelsByRole'][role])
            neighbors[p].update(o['ids'])
    assert all(v==r['capacity'] for v in totals)
    required={o['type'] for o in cfg['occurrences'] if d['types'][o['type']]['kind']=='finite-face'}
    assert required<=present
    unseen=set(range(cfg['atoms'])); components=0
    while unseen:
        components+=1; todo=[unseen.pop()]
        while todo:
            p=todo.pop(); new=neighbors[p]&unseen; unseen.difference_update(new); todo.extend(new)
    assert components==run['components']
    if run['status']=='exact connected filling': assert components==1
    conflicts=sum(len(x)>1 for x in labels)
    assert conflicts==run['markDisagreementPoints']
    return {'fold':run['fold'],'file':cfg['file'],'seed':run['seed'],'selected':len(selected),
            'positiveComponents':components,'markDisagreementPoints':conflicts,
            'changedSelectionsFromParent':len(set(selected)^set(r['selected'][run['fold']])),
            'selectionHash':hashlib.sha256(json.dumps(sorted(selected)).encode()).hexdigest()}


if __name__=='__main__':
    inp,learned,runs,dest=map(Path,sys.argv[1:])
    d=json.loads(inp.read_text()); r=json.loads(learned.read_text())['result']; result=json.loads(runs.read_text())
    assert result['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest()
    assert result['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
    checks=[]; mutations=0
    for run in result['runs']:
        if 'selected' not in run: continue
        checks.append(check(d,r,run))
        for selected in (run['selected'][:-1],run['selected']+[run['selected'][0]]):
            try: check(d,r,{**run,'selected':selected})
            except AssertionError: mutations+=1
            else: raise AssertionError('invalid filling accepted')
    out={'scope':'Independent fixed-t filling, marking and connectedness checks; specialized MILP controls, not reference search.',
         'runsHash':hashlib.sha256(runs.read_bytes()).hexdigest(),'checked':len(checks),
         'mutationRejections':mutations,'checks':checks}
    dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
