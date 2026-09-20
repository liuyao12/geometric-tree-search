"""Bounded correspondence enumeration: one proper least-squares pose per map.

Not complete continuous max-error feasibility. Rank-deficient clouds retain
unresolved rotations even if every correspondence has been visited.
"""
import numpy as np

def enumerate_poses(template,target,species,epsilon=.15,max_nodes=20000):
    X=np.asarray(template);Y=np.asarray(target);n=len(X);colors=np.asarray(species)
    assert X.shape==Y.shape==(n,3) and len(colors)==n
    DX=np.linalg.norm(X[:,None]-X[None,:],axis=2);DY=np.linalg.norm(Y[:,None]-Y[None,:],axis=2)
    groups=[np.flatnonzero(colors==c) for c in sorted(set(species))]
    SX=np.concatenate([np.sort(DX[:,ids],axis=1) for ids in groups],axis=1)
    SY=np.concatenate([np.sort(DY[:,ids],axis=1) for ids in groups],axis=1)
    choices=[np.flatnonzero((colors==colors[i])&(np.max(np.abs(SY-SX[i]),axis=1)<=2*epsilon+1e-10)).tolist() for i in range(n)]
    order=sorted(range(n),key=lambda i:(len(choices[i]),-float(DX[i].sum()),i));assignment={};used=set();nodes=0;truncated=False;answers=[];xc=X.mean(axis=0)
    def visit(k):
        nonlocal nodes,truncated
        if nodes>=max_nodes:truncated=True;return
        nodes+=1
        if k==n:
            perm=[assignment[i] for i in range(n)];Q=Y[perm];yc=Q.mean(axis=0)
            u,_,vt=np.linalg.svd((X-xc).T@(Q-yc));sign=np.eye(3);sign[2,2]=np.linalg.det(u@vt)
            R=u@sign@vt;tr=yc-xc@R;error=float(np.max(np.linalg.norm(X@R+tr-Q,axis=1)))
            if error<=epsilon+1e-10:answers.append(dict(permutation=perm,rotationRow=R.tolist(),translation=tr.tolist(),residual=error))
            return
        i=order[k]
        for j in choices[i]:
            if j in used or any(abs(DX[i,p]-DY[j,q])>2*epsilon+1e-10 for p,q in assignment.items()):continue
            assignment[i]=j;used.add(j);visit(k+1);used.remove(j);del assignment[i]
            if truncated:return
    if all(choices):visit(0)
    return answers,dict(nodes=nodes,truncated=truncated,templateRank=int(np.linalg.matrix_rank(X-xc)),targetRank=int(np.linalg.matrix_rank(Y-Y.mean(axis=0))))
