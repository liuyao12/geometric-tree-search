"""Compile unconditional halo supports and learn an additional scalar channel.

Fixed observed poses and full-target training. Geometric coalescing is a declared
approximate point-identity hypothesis, not continuous correspondence completeness.
"""
from collections import defaultdict
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

spec=importlib.util.spec_from_file_location('halo',Path(__file__).with_name('boron-halo-proposals.py'))
halo=importlib.util.module_from_spec(spec);spec.loader.exec_module(halo)
inp,learned,folder,proposalpath,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];h=json.loads(proposalpath.read_text())
assert h['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest()
assert h['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
n=len(r['weightsByRole']);offsets=[]
for typ in h['types']:offsets.append(n);n+=len(typ.get('anchors',[]))
parent=list(range(n))
def root(p):
    while parent[p]!=p:parent[p]=parent[parent[p]];p=parent[p]
    return p
def merge(group):
    if group:
        for q in group[1:]:parent[root(q)]=root(group[0])
models=[];eps=h['epsilonAngstrom']
for fold,cfg in enumerate(d['configurations']):
    raw=(folder/f'{fold}-1.15-3.json').read_bytes();src=json.loads(raw)
    assert hashlib.sha256(raw).hexdigest()==cfg['sourceHash']
    positions=np.array(src['positions']);cell=np.array(src['cell']);inverse=np.linalg.inv(cell)
    allpoints=positions.tolist();domains=[];base=[];halo_count=0
    for j,o in enumerate(cfg['occurrences']):
        typ=d['types'][o['type']];rows=[];ts=[];marks=[]
        for u,p in enumerate(o['ids']):
            role=r['roleOfSite'][typ['offset']+u];rows.append([p,role]);ts.append({'point':str(p),'value':r['weightsByRole'][role]})
            marks.append({'point':str(p),'channel':'0','lo':r['scalarLabelsByRole'][role],'hi':r['scalarLabelsByRole'][role]})
        anchors=h['types'][o['type']].get('anchors',[])
        if anchors:
            group=src['components'][o['component']];shifts=dict(zip(group['ids'],group['imageOffsets']))
            xyz=np.array([positions[p]+np.array(shifts[p])@cell for p in o['ids']])
            rotation,translation,error=halo.frame(typ['positions'],xyz);assert error<=eps+1e-8
            for u,anchor in enumerate(anchors):
                point=np.array(anchor['position'])@rotation+translation
                rows.append([len(allpoints),offsets[o['type']]+u]);allpoints.append(point.tolist());halo_count+=1
        domains.append(rows);base.append({'id':str(j).zfill(6),'t':ts,'m':marks})
    fractional=(np.array(allpoints)@inverse)%1;tree=cKDTree(fractional,boxsize=1)
    neighbors=defaultdict(set)
    radius=eps/np.linalg.svd(cell,compute_uv=False).min()
    for a,b in tree.query_pairs(radius):
        delta=fractional[a]-fractional[b];delta-=np.round(delta)
        if np.linalg.norm(delta@cell)<=eps:neighbors[a].add(b);neighbors[b].add(a)
    # Fixed representatives, not transitive proximity chains. Prioritize the
    # observed atoms; unmatched points seed additional mark-only identities.
    identities={p:str(p) for p in range(cfg['atoms'])};representatives={str(p):p for p in range(cfg['atoms'])}
    for p in range(cfg['atoms']):
        for q in neighbors[p]:
            assert q>=cfg['atoms'],'two atomic identities within tolerance'
            assert q not in identities or identities[q]==str(p),'multiple eligible atomic identities'
            identities[q]=str(p)
    ghosts=0;unmatched=0
    for p in range(cfg['atoms'],len(allpoints)):
        if p in identities:continue
        pid=f'g:{ghosts}';ghosts+=1;representatives[pid]=p;identities[p]=pid;unmatched+=1
        for q in neighbors[p]:
            if q not in identities:identities[q]=pid;unmatched+=1
    max_residual=0
    for p,pid in identities.items():
        delta=fractional[p]-fractional[representatives[pid]];delta-=np.round(delta)
        error=float(np.linalg.norm(delta@cell));assert error<=eps+1e-8;max_residual=max(max_residual,error)
    mapped=[];training=defaultdict(list);chosen=set(r['selected'][fold]);shared_points=0
    for j,rows in enumerate(domains):
        local=defaultdict(list)
        for p,v in rows:local[identities[p]].append(v)
        for group in local.values():merge(group)
        mapped.append([[p,v] for p,group in local.items() for v in sorted(set(group))])
        if j in chosen:
            for p,group in local.items():training[p].append(group)
    for groups in training.values():
        merge([v for group in groups for v in group])
        if len(groups)>1:shared_points+=1
    model={'fold':fold,'file':cfg['file'],'capacity':r['capacity'],'required':[str(p) for p in range(cfg['atoms'])],
           'candidates':base,'haloDomains':mapped,'trainingSelected':[str(j).zfill(6) for j in r['selected'][fold]],
           'geometryWitness':{'cell':cell.tolist(),'fractionalPoints':fractional.tolist(),'identityOfPoint':[identities[p] for p in range(len(allpoints))],
                              'representatives':representatives},
           'geometryAudit':{'identityPolicy':'atom-first, fixed-seed radius coalescing in stored candidate order; not all correspondences',
                            'transportedHaloPoints':halo_count,'unmatchedHaloPointsRetained':unmatched,'markOnlyIdentities':ghosts,
                            'maximumCoalescingResidual':max_residual,'sharedTrainingChannelPoints':shared_points}}
    models.append(model);print(json.dumps({'file':cfg['file'],**model['geometryAudit']}),flush=True)
classes={};labels=[]
for j in range(n):
    p=root(j)
    if p not in classes:classes[p]=len(classes)
    labels.append(classes[p])
for model in models:
    for c,domain in zip(model['candidates'],model['haloDomains']):
        values=defaultdict(set)
        for p,v in domain:values[p].add(labels[v])
        assert all(len(v)==1 for v in values.values())
        c['m'].extend({'point':p,'channel':'halo','lo':next(iter(v)),'hi':next(iter(v))} for p,v in values.items())
out={'scope':__doc__,'inputHash':h['inputHash'],'learningHash':h['learningHash'],'proposalsHash':hashlib.sha256(proposalpath.read_bytes()).hexdigest(),
     'variables':n,'classes':len(classes),'labels':labels,'epsilonAngstrom':eps,'models':models}
dest.write_text(json.dumps(out)+'\n');print(json.dumps({'variables':n,'classes':len(classes)}))
