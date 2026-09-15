"""Verify compound expansions, geometric witnesses and cross-source provenance."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.transform import Rotation

inp,learned,folder,proposal_path,out=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];a=json.loads(proposal_path.read_text())
assert a['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest()
assert a['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
eps=d['epsilonAngstrom'];geometry=[]
for f,cfg in enumerate(d['configurations']):
    raw=(folder/f'{f}-1.15-3.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==cfg['sourceHash']
    src=json.loads(raw);pos=np.array(src['positions']);cell=np.array(src['cell']);xyz=[];frames={}
    for j,o in enumerate(cfg['occurrences']):
        typ=d['types'][o['type']]
        if typ['kind']=='pair':points=np.array([pos[o['ids'][0]],pos[o['ids'][1]]+np.array(o['imageShift'])@cell])
        else:
            comp=src['components'][o['component']];offsets=dict(zip(comp['ids'],comp['imageOffsets']))
            points=np.array([pos[p]+np.array(offsets[p])@cell for p in o['ids']])
            template=np.array(typ['positions']);pc=template.mean(0);xc=points.mean(0)
            rot,_=Rotation.align_vectors(points-xc,template-pc)
            assert np.linalg.norm(rot.apply(template-pc)+xc-points,axis=1).max()<=eps+1e-8
            frames[j]=(rot,pc,xc)
        xyz.append(points)
    geometry.append((xyz,frames))

def external(f,center,j,site):
    cfg=d['configurations'][f];own=cfg['occurrences'][center];other=cfg['occurrences'][j]
    common=set(own['ids'])&set(other['ids']);assert common=={own['ids'][site]}
    end=other['ids'].index(own['ids'][site]);xyz,frames=geometry[f];rot,pc,xc=frames[center]
    target=xyz[j][1-end]+xyz[center][site]-xyz[j][end]
    return rot.inv().apply(target-xc)+pc,end

def values(f,base):
    cfg=d['configurations'][f];assert len(base)==len(set(base));totals=defaultdict(int);marks={};atoms=[]
    for j in base:
        o=cfg['occurrences'][j];typ=d['types'][o['type']];atoms.append(set(o['ids']))
        for u,p in enumerate(o['ids']):
            role=r['roleOfSite'][typ['offset']+u];totals[p]+=r['weightsByRole'][role]
            assert totals[p]<=r['capacity']
            m=r['scalarLabelsByRole'][role]
            if m is not None:assert p not in marks or marks[p]==m;marks[p]=m
    assert all(s&atoms[0] for s in atoms[1:])
    return {'t':sorted([p,v] for p,v in totals.items()),'m':sorted([p,v] for p,v in marks.items())}

source_checks=0
for entry in a['library']:
    for source in entry['sources']:
        f=source['fold'];center=source['center'];base=source['base'];cfg=d['configurations'][f]
        assert center==base[0] and cfg['occurrences'][center]['type']==entry['type']
        assert set(base)<=set(r['selected'][f]);values(f,base);matched=set()
        for n in entry['neighbors']:
            hits=[]
            for j in base[1:]:
                other=cfg['occurrences'][j]
                if other['type']!=n['type'] or cfg['occurrences'][center]['ids'][n['centerSite']] not in other['ids']:continue
                point,end=external(f,center,j,n['centerSite'])
                if end==n['pairSite'] and np.linalg.norm(point-n['external'])<=2e-6:hits.append(j)
            assert len(hits)==1;matched.add(hits[0])
        assert matched==set(base[1:]);source_checks+=1

checks=[];maximum_residual=0;witnesses=0
for fold in a['folds']:
    f=fold['fold'];cfg=d['configurations'][f];cross=0
    for proposal in fold['proposals']:
        base=proposal['base'];center=base[0];own=cfg['occurrences'][center];typ=d['types'][own['type']]
        assert values(f,base)==proposal['aggregate'];sources=set()
        for witness in proposal['witnesses']:
            entry=a['library'][witness['library']];assert entry['type']==own['type']
            sym=typ['selfFits'][witness['symmetry']];perm=sym['permutation'];q=np.array(sym['rotationRow']);t=np.array(sym['translation'])
            template=np.array(typ['positions']);assert abs(np.linalg.det(q)-1)<1e-7
            assert np.linalg.norm(template@q+t-template[perm],axis=1).max()<=eps+1e-8
            for u,v in enumerate(perm):
                ru=r['roleOfSite'][typ['offset']+u];rv=r['roleOfSite'][typ['offset']+v]
                assert (r['weightsByRole'][ru],r['scalarLabelsByRole'][ru])==(r['weightsByRole'][rv],r['scalarLabelsByRole'][rv])
            assert len(witness['neighbors'])>=2 and len(witness['neighbors'])==len(witness['matchedBase'])
            assert set(witness['matchedBase'])==set(base[1:])
            for ni,j in zip(witness['neighbors'],witness['matchedBase']):
                n=entry['neighbors'][ni];o=cfg['occurrences'][j];assert o['type']==n['type']
                point,end=external(f,center,j,perm[n['centerSite']])
                pair=d['types'][n['type']]
                for u,v in ((end,n['pairSite']),(1-end,1-n['pairSite'])):
                    ru=r['roleOfSite'][pair['offset']+u];rv=r['roleOfSite'][pair['offset']+v]
                    assert (r['weightsByRole'][ru],r['scalarLabelsByRole'][ru])==(r['weightsByRole'][rv],r['scalarLabelsByRole'][rv])
                error=float(np.linalg.norm(point-(np.array(n['external'])@q+t)))
                assert error<=eps+1e-8;maximum_residual=max(maximum_residual,error)
            sources.update(s['fold'] for s in entry['sources']);witnesses+=1
        assert sorted(sources)==proposal['sourceFolds'];cross+=any(s!=f for s in sources)
    assert cross==fold['crossConfigurationProposals']
    checks.append({'file':cfg['file'],'proposals':len(fold['proposals']),'crossConfigurationProposals':cross})
result={'scope':__doc__,'proposalHash':hashlib.sha256(proposal_path.read_bytes()).hexdigest(),
        'sourceOccurrencesChecked':source_checks,'geometricWitnessesChecked':witnesses,
        'maximumExternalResidualAngstrom':maximum_residual,'checks':checks,
        'limits':'Checks recorded witnesses, not exhaustive compound discovery or continuous-pose completeness.'}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
