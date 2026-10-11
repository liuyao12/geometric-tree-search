#!/usr/bin/env python3
"""Two-mesh P1 tetrahedral Neumann modes on the exact seven-cube chair.

Finite projections approximate a sampled target; they do not inherit exact
matching or an aperiodicity theorem. Surface samples support the 3D viewer.
"""
from itertools import permutations, product
from pathlib import Path
import hashlib
import json
import time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigsh
from scipy.linalg import eigh

ROOT=Path(__file__).resolve().parent
COUNT=60


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def field(points,panels):
    result=np.zeros(len(points))
    for p in panels:
        normal=np.array(p['normal']);a=np.array(p['arrow']);d=np.array(p['cubic'])
        offset=points-p['center'];r=offset@normal;y=offset-r[:,None]*normal
        rho=np.sum(y*y,axis=1);active=(rho<1/16)&(abs(r)<1/4)
        result[active]+=np.exp(2-1/(1-16*rho[active])-1/(1-16*r[active]**2))*(y[active]@a+16*rho[active]*(y[active]@d))
    return result


def mesh(n,panels):
    integer=np.array([p for p in product(range(2*n+1),repeat=3) if not all(v>n for v in p)],int)
    points=integer/n;lookup=np.full((2*n+1,)*3,-1,int);lookup[tuple(integer.T)]=np.arange(len(points))
    cubes=np.array([p for p in product(range(2*n),repeat=3) if not all(v>=n for v in p)],int)
    tetrahedra=[];stiffness=[];mass=[]
    for order in permutations(range(3)):
        increments=np.vstack([np.zeros(3,int),np.eye(3,dtype=int)[list(order)]]).cumsum(axis=0)
        vertices=cubes[:,None,:]+increments[None,:,:]
        ids=lookup[tuple(vertices.transpose(2,0,1))];assert (ids>=0).all()
        J=(increments[1:]-increments[0]).T/n
        inverse=np.linalg.inv(J);gradients=np.vstack([-inverse.sum(axis=0),inverse])
        volume=abs(np.linalg.det(J))/6
        tetrahedra.append(ids)
        stiffness.append(np.broadcast_to(volume*(gradients@gradients.T),(len(cubes),4,4)))
        mass.append(np.broadcast_to(volume*(np.ones((4,4))+np.eye(4))/20,(len(cubes),4,4)))
    t=np.concatenate(tetrahedra);rows=np.repeat(t,4,axis=1).ravel();cols=np.tile(t,(1,4)).ravel()
    K=coo_matrix((np.concatenate(stiffness).ravel(),(rows,cols)),shape=(len(points),)*2).tocsr()
    M=coo_matrix((np.concatenate(mass).ravel(),(rows,cols)),shape=(len(points),)*2).tocsr()
    faces=[]
    for p in panels:
        normal=np.array(p['normal']);axis=np.flatnonzero(normal)[0];tangent=[i for i in range(3) if i!=axis]
        low=np.round((np.array(p['center'])-.5*np.array([int(i!=axis) for i in range(3)]))*n).astype(int)
        for i,j in product(range(n),repeat=2):
            quad=[]
            for u,v in [(0,0),(1,0),(1,1),(0,1)]:
                q=low.copy();q[tangent[0]]+=i+u;q[tangent[1]]+=j+v;quad.append(lookup[tuple(q)])
            assert min(quad)>=0
            faces.extend([[quad[0],quad[1],quad[2]],[quad[0],quad[2],quad[3]]])
    faces=np.array(faces,int);surface=np.unique(faces);surface_map=np.full(len(points),-1,int);surface_map[surface]=np.arange(len(surface))
    assert abs(M.sum()-7)<1e-10 and np.max(abs(K@np.ones(len(points))))<1e-10
    assert len(t)==42*n**3 and len(faces)==48*n**2
    return points,t,K,M,surface,surface_map[faces]


def solve(n,panels):
    start=time.monotonic();p,t,K,M,surface,faces=mesh(n,panels)
    values,vectors=eigsh(K,k=COUNT,M=M,sigma=-.1,which='LM',tol=1e-10)
    order=np.argsort(values);values=values[order];vectors=vectors[:,order]
    assert abs(values[0])<1e-8
    values[0]=0;vectors[:,0]=1/np.sqrt(7)
    for k in range(COUNT):
        if vectors[np.argmax(abs(vectors[:,k])),k]<0:vectors[:,k]*=-1
    orthogonality=np.max(abs(vectors.T@(M@vectors)-np.eye(COUNT)))
    kv=K@vectors;mv=M@vectors
    residuals=np.linalg.norm(kv-mv*values,axis=0)/np.maximum(np.linalg.norm(kv,axis=0)+np.linalg.norm(mv*values,axis=0),1e-12)
    target=field(p,panels);coefficients=vectors.T@(M@target);norm=target@(M@target)
    assert norm>0 and np.isfinite(vectors).all() and np.isfinite(coefficients).all()
    assert orthogonality<1e-8 and residuals[1:].max()<1e-7
    truncations=[]
    for count in [8,16,32,60]:
        approximation=vectors[:,:count]@coefficients[:count];error=approximation-target
        truncations.append({'modes':count,'sampled_squared_mass_fraction':float(np.sum(coefficients[:count]**2)/norm),
            'relative_sampled_mass_error':float(np.sqrt(error@(M@error)/norm)),
            'maximum_sampled_boundary_error_over_target_peak':float(abs(error[surface]).max()/abs(target).max())})
    controls=[]
    for q in [1,2,3,4]:
        frequencies=[a for a in product(range(3),repeat=3) if sum(v*v for v in a)==q]
        analytic=np.column_stack([np.prod(np.cos(np.pi*p*np.array(a)),axis=1) for a in frequencies])
        exactnorm=analytic.T@(M@analytic);projection=vectors.T@(M@analytic)
        indices=np.argsort(np.sum(projection**2,axis=1))[-len(frequencies):];indices=np.sort(indices)
        selected=projection[indices]
        scores=eigh(selected.T@selected,exactnorm,eigvals_only=True)
        controls.append({'q':q,'frequencies':frequencies,'nearest_mode_indices':indices.tolist(),
            'minimum_sampled_subspace_capture':float(scores.min()),
            'maximum_relative_eigenvalue_difference':float(abs(values[indices]/(np.pi**2*q)-1).max())})
    run={'subdivisions_per_unit':n,'eigenvalues':values.tolist(),'coefficients':coefficients.tolist(),
        'sampled_target_squared_mass_norm':float(norm),'truncations':truncations,'cube_cosine_controls':controls,
        'diagnostics':{'nodes':len(p),'tetrahedra':len(t),'surface_triangles':len(faces),'volume':float(M.sum()),
            'maximum_mass_orthogonality_error':float(orthogonality),'maximum_positive_relative_matrix_residual':float(residuals[1:].max()),
            'sampled_constant_coefficient':float(coefficients[0]),'elapsed_seconds':time.monotonic()-start}}
    print(json.dumps({'mesh':n,**run['diagnostics'],'captured_60':truncations[-1]['sampled_squared_mass_fraction']}),flush=True)
    return run,{'points':p[surface].tolist(),'triangles':faces.tolist(),
        'surface_values':[vectors[surface,k].tolist() for k in range(COUNT)],
        'full_nodal_peaks':np.max(abs(vectors),axis=0).tolist(),'relative_matrix_residuals':residuals.tolist(),
        'exact_target_surface_values':target[surface].tolist()}


def main():
    data=json.loads((ROOT/'chair-boundary-field.json').read_text());panels=data['panels'];runs=[]
    for n in [6,12]:
        run,viewer=solve(n,panels);runs.append(run)
    movement=max(abs(a-b)/max(1,abs(b)) for a,b in zip(runs[0]['eigenvalues'],runs[1]['eigenvalues']))
    output={'date':'2026-10-11','status':'passed','script_sha256':digest(Path(__file__)),
        'input_sha256':{'chair-boundary-field.json':digest(ROOT/'chair-boundary-field.json')},
        'method':'Conforming P1 tetrahedral FEM, consistent mass, two nested uniform Freudenthal meshes; natural weak Neumann conditions.',
        'mesh_runs':runs,'maximum_last_refinement_relative_eigenvalue_change':movement,'viewer':viewer,
        'versions':{'numpy':np.__version__},
        'limitations':'Uncertified eigenvalue estimates and projections of nodal P1 targets. Plots show surface traces, not interior slices. No finite matching theorem or numerical tolerance cutoff follows from these computations.'}
    (ROOT/'chair-modal-projection.json').write_text(json.dumps(output,separators=(',',':'),allow_nan=False)+'\n')


if __name__=='__main__':main()
