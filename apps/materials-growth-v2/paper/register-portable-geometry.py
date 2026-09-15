"""Propose portable pair registrations directly from observed candidate geometry.

Reads no junction states, selected fillings, class relations or target labels.
It still uses the finite observed base-pair incidence, not a blind-growth domain.
Two-vector frame seeds plus proper least-squares refinement are proposals, not
a complete solver for every rotation in an approximate matching neighborhood.
"""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def source_cloud(motif):
    delta=np.asarray(motif['anchors'][1]);vectors=[delta.tolist()];colors=[[-1]]
    for side,mark in enumerate(motif['cloudM']):
        vectors.extend((np.asarray(mark['vectors'])+side*delta).tolist())
        colors.extend([[side,*c] for c in mark['colors']])
    return np.asarray(vectors),colors

def basis(a,b):
    e0=a/np.linalg.norm(a);v=b-e0*np.dot(b,e0)
    if np.linalg.norm(v)<1e-10:return None
    e1=v/np.linalg.norm(v);return np.array([e0,e1,np.cross(e0,e1)])

def refine(p,q,permutation):
    u,_,vt=np.linalg.svd(p.T@q[permutation]);fix=np.eye(3);fix[-1,-1]=np.linalg.det(u@vt);rot=u@fix@vt
    return rot,float(np.linalg.norm(p@rot-q[permutation],axis=1).max())

def registrations(p,colors,q,target_colors,eps):
    """Enumerate frame proposals; cap only pathological ambiguous assignments."""
    if len(p)>len(q):return [],False
    counts=Counter(map(tuple,target_colors))
    if any(n>counts[c] for c,n in Counter(map(tuple,colors)).items()):return [],False
    if abs(np.linalg.norm(p[0])-np.linalg.norm(q[0]))>eps+1e-8:return [],False
    anchor=int(np.argmax(np.linalg.norm(np.cross(p[0],p),axis=1)));b=basis(p[0],p[anchor])
    if b is None:return [],True
    choices=[i for i,c in enumerate(target_colors) if c==colors[anchor] and abs(np.linalg.norm(q[i])-np.linalg.norm(p[anchor]))<=eps+1e-8]
    allowed=np.array([[c==d for d in target_colors] for c in colors]);answers=[];seen=set();truncated=False
    for target in choices:
        qb=basis(q[0],q[target])
        if qb is None:continue
        initial=b.T@qb;distance=np.linalg.norm((p@initial)[:,None,:]-q[None,:,:],axis=2)
        options=[sorted(np.flatnonzero(allowed[i]&(distance[i]<=8*eps+1e-8)).tolist(),key=lambda k:distance[i,k]) for i in range(len(p))]
        options[0]=[0];options[anchor]=[target]
        if any(not row for row in options):continue
        order=sorted(range(len(p)),key=lambda i:len(options[i]));assignment={};used=set();leaves=0
        def visit(k):
            nonlocal leaves,truncated
            if leaves>=4096:truncated=True;return
            if k==len(p):
                leaves+=1;perm=[assignment[i] for i in range(len(p))];rot,error=refine(p,q,perm)
                if error<=eps+1e-8:
                    key=(tuple(perm),rot.tobytes())
                    if key not in seen:seen.add(key);answers.append({'permutation':perm,'rotationRow':rot.tolist(),'residual':error})
                return
            i=order[k]
            for target_index in options[i]:
                if target_index in used:continue
                assignment[i]=target_index;used.add(target_index);visit(k+1);used.remove(target_index);del assignment[i]
        visit(0)
    return answers,truncated

def main():
    inp,folder,portable,out=map(Path,sys.argv[1:]);d=json.loads(inp.read_text());p=json.loads(portable.read_text());assert p['inputHash']==sha(inp)
    eps=p['positionToleranceAngstrom'];sources=[source_cloud(m) for m in p['motifs']];bytype=defaultdict(list)
    for i,m in enumerate(p['motifs']):bytype[m['pairType']].append(i)
    folds=[];cache={};tested=0;truncated=0;maxerror=0.
    for f,cfg in enumerate(d['configurations']):
        raw=folder/f'{f}-1.15-3.json';assert sha(raw)==cfg['sourceHash'];geom=json.loads(raw.read_text());xyz=np.asarray(geom['positions']);cell=np.asarray(geom['cell'])
        incident=defaultdict(list);face=set()
        for cid,occ in enumerate(cfg['occurrences']):
            typ=p['baseMotifs'][occ['type']]
            if typ['kind']!='pair':face.update(occ['ids']);continue
            a,b=occ['ids'];delta=xyz[b]+np.asarray(occ['imageShift'])@cell-xyz[a]
            for side,point in enumerate((a,b)):
                incident[point].append({'candidate':cid,'vector':(delta*(1 if side==0 else -1)).tolist(),'color':[occ['type'],typ['t'][side],typ['t'][1-side],typ['scalarM'][side],typ['scalarM'][1-side]]})
        nodes={point:edges for point,edges in incident.items() if point not in face};edges=[]
        for cid,occ in enumerate(cfg['occurrences']):
            if len(occ['ids'])!=2 or not all(point in nodes for point in occ['ids']):continue
            a,b=occ['ids'];delta=np.asarray(next(e['vector'] for e in nodes[a] if e['candidate']==cid));query=[delta.tolist()];colors=[[-1]];arms=[None]
            for side,point in enumerate((a,b)):
                for edge in nodes[point]:query.append((np.asarray(edge['vector'])+side*delta).tolist());colors.append([side,*edge['color']]);arms.append(edge['candidate'])
            q=np.asarray(query)
            # Quantized descriptor caching is solely a proposal optimization.
            # Every retained fit is recomputed and checked on unrounded geometry.
            # Negative cached proposals are NOT claimed exhaustive near boundaries.
            key=(occ['type'],tuple(map(tuple,colors)),tuple(q.round(9).ravel()))
            if key not in cache:
                proposals=[]
                for mi in bytype[occ['type']]:
                    s,sc=sources[mi];fits,cut=registrations(s,sc,q,colors,eps);tested+=1;truncated+=cut
                    proposals.extend({'template':mi,**fit} for fit in fits)
                cache[key]=proposals
            placements=[]
            for proposal in cache[key]:
                mi=proposal['template'];s,sc=sources[mi];perm=proposal['permutation'];assert all(sc[i]==colors[k] for i,k in enumerate(perm))
                rot,error=refine(s,q,perm)
                if error>eps+1e-8:continue
                maxerror=max(maxerror,error)
                selected=[[],[]]
                for i,k in enumerate(perm):
                    if i:selected[sc[i][0]].append(arms[k])
                placements.append({'template':mi,'rotationRow':rot.tolist(),'residual':error,'selectedArms':selected})
            edges.append({'candidate':cid,'points':[a,b],'registrations':placements})
            if len(edges)%100==0:print(json.dumps({'fold':f,'edges':len(edges),'descriptorGroups':len(cache),'templateTests':tested}),flush=True)
        folds.append({'fold':f,'file':cfg['file'],'edges':edges});print(json.dumps({'foldDone':f,'edges':len(edges),'registrations':sum(len(e['registrations']) for e in edges)}),flush=True)
    result={'scope':__doc__,'inputHash':sha(inp),'portableHash':sha(portable),'sourceHash':sha(Path(__file__)),'epsilonAngstrom':eps,'descriptorGridAngstrom':1e-9,'templateTests':tested,'ambiguousOrTruncatedTemplateQueries':truncated,'maximumResidualAngstrom':maxerror,'folds':folds,
            'limits':['Observed base-pair pool and pair-only applicability are still target-derived.','No junction states or known selected fillings are read.','Descriptor caching, frame seeds and the 4096 correspondence cap define a proposal procedure, not continuous-pose completeness.']}
    with out.open('x') as stream:json.dump(result,stream)

if __name__=='__main__':main()
