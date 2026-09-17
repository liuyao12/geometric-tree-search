"""Unmarked residual-filling diagnostic using any frozen learned motif type.

Supplied valid occurrences remain fixed. Proper rigid registrations use
species/distance correspondence proposals; no original occurrence atom lists.
MILP is a separate feasibility diagnostic, not the reference tree search.
"""
import hashlib,itertools,json,time
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix

coordp,supportp,posep,checkp,out=map(Path,sys.argv[1:6])
release_neighbors=len(sys.argv)>6 and sys.argv[6]=='release-neighbors'
selected_ids=set(sys.argv[7].split(',')) if len(sys.argv)>7 and sys.argv[7]!='all' else None
poolout=Path(sys.argv[8]) if len(sys.argv)>8 else None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
corpus,support,poses,check=[json.loads(p.read_text()) for p in [coordp,supportp,posep,checkp]]
assert check['resultHash']==sha(supportp) and check['poseHash']==sha(posep)
assert support['sourceHashes'][coordp.name]==sha(coordp)
cc={c['id']:c for c in corpus['configurations']};groups=defaultdict(list)
for a in support['anchors']:
    assert a['t'] in [.5,1.];groups[a['type']].append(a)
templates={typ:(np.asarray([a['position'] for a in aa]),[a['species'] for a in aa],np.asarray([round(2*a['t']) for a in aa])) for typ,aa in groups.items()}
rows=[];pools=[];tol=support['positionTolerance']
for row in check['rows']:
    if row['training'] or row['valid']:continue
    if selected_ids is not None and row['id'] not in selected_ids:continue
    start=time.monotonic();cid=row['id'];c=cc[cid];cell=np.asarray(c['cell']);inv=np.linalg.inv(cell)
    pos=(np.asarray(c['positions'])@inv%1)@cell;species=np.asarray(c['species']);totals=np.zeros(len(pos),dtype=int)
    shifts=np.asarray(list(itertools.product([-2,-1,0,1,2],repeat=3)))@cell
    assert 2*np.linalg.svd(cell,compute_uv=False)[-1]>tol
    tree=cKDTree((pos[:,None,:]+shifts[None,:,:]).reshape(-1,3));fixed=[];dropped=0
    for p in poses['poses']:
        if p['configuration']!=cid or p['type'] not in templates:continue
        X,colors,w=templates[p['type']];R=np.asarray(p['rotationRow']);tr=np.asarray(p['translation']);pred=((X@R+tr)@inv%1)@cell;ids=[]
        for x,col in zip(pred,colors):
            hits=[j//125 for j in tree.query_ball_point(x,tol+1e-9) if species[j//125]==col]
            if len(hits)!=1:break
            ids.append(hits[0])
        if len(ids)!=len(X) or len(set(ids))!=len(ids):dropped+=1;continue
        totals[ids]+=w;fixed.append(dict(type=p['type'],rotationRow=p['rotationRow'],translation=p['translation'],ids=ids,units=w.tolist()))
    released=[]
    if release_neighbors:
        defects=set(np.flatnonzero(totals!=2))
        released=[p for p in fixed if defects.intersection(p['ids'])]
        fixed=[p for p in fixed if not defects.intersection(p['ids'])]
        totals[:]=0
        for p in fixed:totals[p['ids']]+=p['units']
    if np.any(totals>2):
        rows.append(dict(id=cid,status='frozen-part-overfilled',fixed=fixed,droppedInvalidPoses=dropped));continue
    residual=2-totals;sites=np.flatnonzero(residual);candidates=[];seen=set();leaves=0;truncated=False
    for typ,(X,colors,w) in sorted(templates.items()):
        if len(X)>len(sites):continue
        D=np.linalg.norm(X[:,None,:]-X[None,:,:],axis=2)
        for origin in sites:
            if species[origin]!=colors[0] or residual[origin]<w[0]:continue
            delta=pos[sites]-pos[origin];delta-=np.round(delta@inv)@cell
            images=delta[:,None,:]+shifts[None,:,:];nearest=np.argmin(np.sum(images**2,axis=2),axis=1);Q=images[np.arange(len(sites)),nearest]
            choices=[np.flatnonzero((species[sites]==col)&(residual[sites]>=weight)).tolist() for col,weight in zip(colors,w)]
            choices[0]=[int(np.flatnonzero(sites==origin)[0])]
            if any(not opts for opts in choices):continue
            order=[0]+sorted(range(1,len(X)),key=lambda i:len(choices[i]));assigned={};used=set()
            def visit(k):
                global leaves,truncated
                if leaves>=100000 or time.monotonic()-start>60:truncated=True;return
                if k==len(X):
                    leaves+=1;perm=[assigned[i] for i in range(len(X))];Y=Q[perm]+pos[origin]
                    xc=X.mean(axis=0);yc=Y.mean(axis=0);u,s,vt=np.linalg.svd((X-xc).T@(Y-yc));fix=np.eye(3);fix[2,2]=np.linalg.det(u@vt);R=u@fix@vt;tr=yc-xc@R
                    error=float(np.max(np.linalg.norm(X@R+tr-Y,axis=1)))
                    if error>tol+1e-9:return
                    ids=sites[perm].tolist();key=(typ,tuple(ids))
                    # One sampled pose per template/correspondence, not an
                    # equivalence or completeness claim for continuous poses.
                    if key in seen:return
                    seen.add(key);candidates.append(dict(type=typ,rotationRow=R.tolist(),translation=tr.tolist(),ids=ids,units=w.tolist(),error=error));return
                i=order[k]
                for j in choices[i]:
                    if j in used:continue
                    if any(abs(np.linalg.norm(Q[j]-Q[q])-D[i,p])>2*tol+1e-9 for p,q in assigned.items()):continue
                    assigned[i]=j;used.add(j);visit(k+1);used.remove(j);del assigned[i]
                    if truncated:return
            visit(0)
            if truncated:break
        if truncated:break
    # Export only the pre-diagnostic candidate universe and the declared fixed
    # prefix. No selected MILP repair is present in this separate search input.
    geometry={f'fixed:{i}':p for i,p in enumerate(fixed)}|{f'proposal:{i}':p for i,p in enumerate(candidates)}
    pools.append(dict(id=cid,geometry=geometry,model=dict(capacity=2,required=[f'a:{i}' for i in range(len(pos))],complete=True,
                 initial=[f'fixed:{i}' for i in range(len(fixed))],candidates=[dict(id=k,t=[dict(point=f'a:{a}',value=int(v)) for a,v in zip(p['ids'],p['units'])],m=[]) for k,p in geometry.items()])))
    selected=[];verified=False;status='no-proposed-filling'
    if candidates:
        rr=[];jj=[];vv=[]
        for j,p in enumerate(candidates):
            for atom,v in zip(p['ids'],p['units']):rr.append(atom);jj.append(j);vv.append(v)
        A=coo_matrix((vv,(rr,jj)),shape=(len(pos),len(candidates))).tocsr()
        solution=milp(np.zeros(len(candidates)),integrality=np.ones(len(candidates)),bounds=Bounds(0,1),constraints=LinearConstraint(A,residual,residual),options={'time_limit':10})
        status=str(solution.message)
        if solution.x is not None:
            bits=np.rint(solution.x).astype(int);assert set(bits)<={0,1};verified=bool(np.all(A@bits==residual));selected=[p for p,b in zip(candidates,bits) if b]
    result=dict(id=cid,status='unmarked-filling-awaiting-replay' if verified else status,fixed=fixed,added=selected,releasedPlacements=len(released),
                residualAtoms=len(sites),candidateCount=len(candidates),correspondenceLeaves=leaves,truncated=truncated,droppedInvalidPoses=dropped,seconds=time.monotonic()-start)
    rows.append(result);print(json.dumps({k:v for k,v in result.items() if k not in ['fixed','added']}),flush=True)
report=dict(sourceHashes={p.name:sha(p) for p in [coordp,supportp,posep,checkp]},codeHash=sha(Path(__file__)),rows=rows,releaseNeighbors=release_neighbors,selectedIds=sorted(selected_ids) if selected_ids is not None else None,
            limits=__doc__+' Registration is a bounded finite proposal procedure: one closest periodic image per residual atom, pair-distance pruning, least-squares pose fit, 100000 correspondence leaves/60 seconds and a 10-second MILP diagnostic per case. No completeness, marking compatibility or blind-growth claim. One sampled pose per learned type and ordered atom correspondence; different types remain distinct. Two-point supports retain only one tested proper orientation.')
with out.open('x') as f:json.dump(report,f,indent=2)
if poolout:
    with poolout.open('x') as f:json.dump(dict(sourceHashes=report['sourceHashes'],codeHash=report['codeHash'],models=pools,scope='Finite unmarked residual pools with supplied fixed prefixes. No MILP selections. Incomplete continuous registration proposals.'),f)
