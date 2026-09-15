"""Geometric compound proposals: a face motif and its selected pair neighbors.

Learn finite collections of original placements, not a new tiling legality rule.
Keep all original candidates. Matching is restricted to the stored observed poses.
"""
from collections import defaultdict
from itertools import product
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

spec=importlib.util.spec_from_file_location('halo',Path(__file__).with_name('boron-halo-proposals.py'))
halo=importlib.util.module_from_spec(spec);spec.loader.exec_module(halo)

def load_geometry(d,folder):
    result=[]
    for fold,cfg in enumerate(d['configurations']):
        raw=(folder/f'{fold}-1.15-3.json').read_bytes()
        assert hashlib.sha256(raw).hexdigest()==cfg['sourceHash']
        src=json.loads(raw);positions=np.array(src['positions']);cell=np.array(src['cell'])
        lifted=[];at=defaultdict(list);frames={}
        for j,o in enumerate(cfg['occurrences']):
            typ=d['types'][o['type']]
            if typ['kind']=='finite-face':
                comp=src['components'][o['component']];shifts=dict(zip(comp['ids'],comp['imageOffsets']))
                xyz=np.array([positions[p]+np.array(shifts[p])@cell for p in o['ids']])
                q,t,err=halo.frame(typ['positions'],xyz)
                assert err<=d['epsilonAngstrom']+1e-8
                frames[j]=(q,t)
            else:
                xyz=np.array([positions[o['ids'][0]],positions[o['ids'][1]]+np.array(o['imageShift'])@cell])
                for u,p in enumerate(o['ids']):at[p].append((j,u))
            lifted.append(xyz)
        result.append((lifted,at,frames))
    return result

def aggregate(d,r,cfg,ids):
    assert len(ids)==len(set(ids))
    totals=defaultdict(int);marks={}
    for j in ids:
        o=cfg['occurrences'][j];typ=d['types'][o['type']]
        for u,p in enumerate(o['ids']):
            role=r['roleOfSite'][typ['offset']+u]
            totals[p]+=r['weightsByRole'][role]
            assert totals[p]<=r['capacity']
            label=r['scalarLabelsByRole'][role]
            if label is not None:
                assert p not in marks or marks[p]==label
                marks[p]=label
    return {'t':[[p,v] for p,v in sorted(totals.items())], 'm':[[p,v] for p,v in sorted(marks.items())]}

def compile(d,r,folder):
    geometries=load_geometry(d,folder);library=[];bykey={}
    def pair_orientation_matches(ti,source_end,target_end):
        typ=d['types'][ti]
        for source,target in ((source_end,target_end),(1-source_end,1-target_end)):
            a=r['roleOfSite'][typ['offset']+source];b=r['roleOfSite'][typ['offset']+target]
            if (r['weightsByRole'][a],r['scalarLabelsByRole'][a])!=(r['weightsByRole'][b],r['scalarLabelsByRole'][b]):return False
        return True
    for fold,cfg in enumerate(d['configurations']):
        lifted,at,frames=geometries[fold];chosen=set(r['selected'][fold])
        for center in sorted(chosen&frames.keys()):
            own=cfg['occurrences'][center];q,t=frames[center];neighbors=[];base=[center]
            for u,p in enumerate(own['ids']):
                for j,v in at[p]:
                    if j not in chosen:continue
                    o=cfg['occurrences'][j]
                    assert len(set(o['ids'])&set(own['ids']))==1
                    point=lifted[j][1-v]+lifted[center][u]-lifted[j][v]
                    neighbors.append({'type':o['type'],'centerSite':u,'pairSite':v,
                                      'external':((point-t)@q.T).tolist()})
                    base.append(j)
            if not neighbors:continue
            neighbors.sort(key=lambda x:(x['centerSite'],x['type'],x['pairSite'],x['external']))
            key=json.dumps([own['type'],[(x['type'],x['centerSite'],x['pairSite'],np.round(x['external'],6).tolist()) for x in neighbors]],separators=(',',':'))
            aggregate(d,r,cfg,base)
            if key not in bykey:
                bykey[key]=len(library)
                library.append({'type':own['type'],'neighbors':neighbors,'sources':[]})
            library[bykey[key]]['sources'].append({'fold':fold,'center':center,'base':base})
    folds=[];eps=d['epsilonAngstrom']
    for fold,cfg in enumerate(d['configurations']):
        lifted,at,frames=geometries[fold];proposals={};rejected=0;fits=0
        for center,(q,t) in frames.items():
            own=cfg['occurrences'][center];typ=d['types'][own['type']]
            local=[]
            for u,p in enumerate(own['ids']):
                rows=[]
                for j,v in at[p]:
                    o=cfg['occurrences'][j]
                    if len(set(o['ids'])&set(own['ids']))!=1:continue
                    point=lifted[j][1-v]+lifted[center][u]-lifted[j][v]
                    rows.append((j,v,o['type'],(point-t)@q.T))
                local.append(rows)
            for li,entry in enumerate(library):
                if entry['type']!=own['type']:continue
                for si,sym in enumerate(typ['selfFits']):
                    perm=sym['permutation'];rotation=np.array(sym['rotationRow']);translation=np.array(sym['translation'])
                    choices=[];matched_neighbors=[]
                    for ni,n in enumerate(entry['neighbors']):
                        target=np.array(n['external'])@rotation+translation
                        hits=[j for j,v,ti,point in local[perm[n['centerSite']]]
                              if ti==n['type'] and pair_orientation_matches(ti,n['pairSite'],v) and np.linalg.norm(point-target)<=eps+1e-8]
                        if hits:choices.append(hits);matched_neighbors.append(ni)
                    # A whole one-hop neighborhood can be over-specific. Propose
                    # its matched subcompound, with at least two connectors.
                    # No absence here is used to delete a base candidate.
                    if len(choices)<2:continue
                    for picked in product(*choices):
                        if len(set(picked))!=len(picked):continue
                        base=[center,*sorted(picked)]
                        try:values=aggregate(d,r,cfg,base)
                        except AssertionError:rejected+=1;continue
                        fits+=1;key=tuple(base)
                        if key not in proposals:
                            proposals[key]={'base':base,'aggregate':values,'witnesses':[],'sourceFolds':[]}
                        p=proposals[key];p['witnesses'].append({'library':li,'symmetry':si,'neighbors':matched_neighbors,'matchedBase':list(picked)})
                        p['sourceFolds']=sorted(set(p['sourceFolds'])|{s['fold'] for s in entry['sources']})
        rows=list(proposals.values())
        folds.append({'fold':fold,'file':cfg['file'],'proposals':rows,
                      'crossConfigurationProposals':sum(any(f!=fold for f in p['sourceFolds']) for p in rows),
                      'validatedEmbeddingsBeforeDeduplication':fits,'rejectedInternalFillings':rejected})
        print(json.dumps({k:v for k,v in folds[-1].items() if k!='proposals'}),flush=True)
    return {'scope':__doc__,'library':library,'folds':folds,'epsilonAngstrom':eps,
            'limits':['Compound discovery uses selected training decompositions.',
                      'Library deduplication uses rounded local coordinates, not complete isometry classification.',
                      'Matching enumerates stored motif self poses, not all continuous orientations.',
                      'Source-configuration exclusion concerns compound observations only; base dictionary and t/m are joint-fit.',
                      'Proposals must only guide ordering; absence is not evidence of impossibility.']}

if __name__=='__main__':
    inp,learned,folder,out=map(Path,sys.argv[1:]);raw=inp.read_bytes();lr=learned.read_bytes()
    d=json.loads(raw);learning=json.loads(lr);assert learning['inputHash']==hashlib.sha256(raw).hexdigest()
    result=compile(d,learning['result'],folder)
    result.update(inputHash=hashlib.sha256(raw).hexdigest(),learningHash=hashlib.sha256(lr).hexdigest())
    with out.open('x') as f:json.dump(result,f)
    print(json.dumps({'libraryEntries':len(result['library']), 'sourceOccurrences':sum(len(x['sources']) for x in result['library'])}))
