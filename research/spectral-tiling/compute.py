#!/usr/bin/env python3
"""Reproducible P1 finite-element study of Tile(1,r), no tiling search.

Dependencies: numpy, scipy, matplotlib, triangle. Run from any directory.
Labels come from SMKGS (2024), not from a spectral classifier.
"""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import numpy as np
import scipy
import triangle
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigsh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
AXIAL = np.array([[0,0],[1,0],[1,1],[3,0],[4,1],[3,2],[3,3],
                  [1,4],[0,6],[-1,6],[-1,5],[-1,4],[0,3],[-1,2]], float)


def area(p):
    return float(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))/2)


def tile(r):
    p = AXIAL.copy()
    p[:,0] += p[:,1]/2
    p[:,1] *= np.sqrt(3)/2
    edges = np.roll(p,-1,axis=0)-p
    lengths = np.linalg.norm(edges,axis=1)
    new_edges = edges/lengths[:,None]*np.where(lengths>1.5,r,1)[:,None]
    assert np.linalg.norm(new_edges.sum(axis=0)) < 1e-12
    result = np.vstack((np.zeros(2),np.cumsum(new_edges,axis=0)[:-1]))
    assert np.isclose(area(result),np.sqrt(3)*(2+np.sqrt(3)*r+r*r))
    # Omit only the single straight-angle vertex, consistently throughout the family.
    incoming = result-np.roll(result,1,axis=0)
    outgoing = np.roll(result,-1,axis=0)-result
    turns = incoming[:,0]*outgoing[:,1]-incoming[:,1]*outgoing[:,0]
    return result[np.abs(turns)>1e-10]


def cross(a,b,c):
    return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))


def triangulate(p):
    """Ear clipping with inclusive point tests; orientation is counterclockwise."""
    remaining = list(range(len(p)))
    triangles = []
    while len(remaining)>3:
        for j,b in enumerate(remaining):
            a,c = remaining[j-1],remaining[(j+1)%len(remaining)]
            if cross(p[a],p[b],p[c]) <= 1e-10:
                continue
            if any(all(v>=-1e-10 for v in (cross(p[a],p[b],p[q]),
                   cross(p[b],p[c],p[q]),cross(p[c],p[a],p[q])))
                   for q in remaining if q not in (a,b,c)):
                continue
            triangles.append((a,b,c))
            remaining.pop(j)
            break
        else:
            raise ValueError('Ear clipping failed')
    triangles.append(tuple(remaining))
    return np.array(triangles,dtype=int)


def mesh(p,t,level,boundary_edges=None):
    boundary = {tuple(sorted(edge)) for edge in boundary_edges} if boundary_edges is not None else {
        tuple(sorted((i,(i+1)%len(p)))) for i in range(len(p))}
    for _ in range(level):
        points = p.tolist()
        midpoints = {}
        def midpoint(a,b):
            edge = tuple(sorted((int(a),int(b))))
            if edge not in midpoints:
                midpoints[edge] = len(points)
                points.append(((p[a]+p[b])/2).tolist())
            return midpoints[edge]
        children = []
        for a,b,c in t:
            ab,bc,ca = midpoint(a,b),midpoint(b,c),midpoint(c,a)
            children.extend(((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)))
        new_boundary = set()
        for a,b in boundary:
            m = midpoint(a,b)
            new_boundary.update((tuple(sorted((a,m))),tuple(sorted((m,b)))))
        boundary = new_boundary
        p,t = np.array(points),np.array(children)
    boundary_nodes = sorted({a for edge in boundary for a in edge})
    return p,t,np.array(boundary_nodes)


def solve(p,t,level,k=12,boundary_edges=None):
    domain_area = area(p) if boundary_edges is None else None
    p,t,boundary = mesh(p,t,level,boundary_edges)
    v = p[t]
    det = (v[:,1,0]-v[:,0,0])*(v[:,2,1]-v[:,0,1])-(v[:,1,1]-v[:,0,1])*(v[:,2,0]-v[:,0,0])
    assert np.all(det>1e-13), 'Common triangulation inverted'
    a = det/2
    gradients = np.stack((v[:,[1,2,0],1]-v[:,[2,0,1],1],
                          v[:,[2,0,1],0]-v[:,[1,2,0],0]),axis=2)/det[:,None,None]
    ke = a[:,None,None]*np.einsum('tik,tjk->tij',gradients,gradients)
    me = a[:,None,None]/12*(np.ones((3,3))+np.eye(3))
    rows = np.repeat(t,3,axis=1).ravel()
    cols = np.tile(t,(1,3)).ravel()
    n = len(p)
    K = coo_matrix((ke.ravel(),(rows,cols)),shape=(n,n)).tocsr()
    M = coo_matrix((me.ravel(),(rows,cols)),shape=(n,n)).tocsr()
    interior = np.setdiff1d(np.arange(n),boundary)
    K = K[interior][:,interior]
    M = M[interior][:,interior]
    vals,vecs = eigsh(K,k=k,M=M,sigma=0,which='LM',tol=1e-10,
                     v0=np.linspace(1,2,len(interior)))
    order = np.argsort(vals)
    vals,vecs = vals[order],vecs[:,order]
    residual = max(np.linalg.norm(K@vecs[:,j]-vals[j]*(M@vecs[:,j]))/
                   (np.linalg.norm(K@vecs[:,j])+abs(vals[j])*np.linalg.norm(M@vecs[:,j]))
                   for j in range(k))
    domain_area = float(a.sum()) if domain_area is None else domain_area
    return {'eigenvalues':vals.tolist(),'area_eigenvalues':(vals*domain_area).tolist(),
            'nodes':n,'triangles':len(t),'free_nodes':len(interior),
            'max_relative_residual':float(residual),'mesh_area':float(a.sum())}


def invariants(p):
    e = np.roll(p,-1,axis=0)-p
    prev = np.roll(e,1,axis=0)
    turns = np.arctan2(prev[:,0]*e[:,1]-prev[:,1]*e[:,0],np.sum(prev*e,axis=1))
    angles = np.pi-turns
    return {'area':area(p),'perimeter':float(np.linalg.norm(e,axis=1).sum()),
            'corner_heat_constant':float(np.sum((np.pi**2-angles**2)/(24*np.pi*angles))),
            'angles_over_pi':(angles/np.pi).tolist()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--levels',nargs='+',type=int,default=[1,2,3])
    args = parser.parse_args()
    params = [.9,.95,.99,.998,1.,1.002,1.01,1.05,1.2,float(np.sqrt(3))]
    base = tile(1)
    topology = triangulate(base)
    quality = triangle.triangulate({'vertices':base,'segments':np.array(
        [(i,(i+1)%len(base)) for i in range(len(base))])},'pq28a0.025')
    # Deform one common quality mesh through a continuous piecewise-affine map.
    mapped_weights = np.zeros((len(quality['vertices']),len(base)))
    located = np.zeros(len(mapped_weights),dtype=bool)
    for ids in topology:
        v = base[ids]
        bary = np.linalg.solve(np.vstack((v.T,np.ones(3))),
                               np.vstack((quality['vertices'].T,np.ones(len(mapped_weights))))).T
        select = (~located)&np.all(bary>=-1e-9,axis=1)
        mapped_weights[np.ix_(select,ids)] = bary[select]
        located[select] = True
    assert np.all(located)
    cases = []
    for r in params:
        p = tile(r)
        # Same abstract triangulation for all r. Verify exact coverage in floating arithmetic.
        ta = np.array([cross(*p[t])/2 for t in topology])
        assert np.all(ta>0) and np.isclose(ta.sum(),area(p))
        mapped = mapped_weights@p
        results = {str(level):solve(mapped,quality['triangles'],level,
                                   boundary_edges=quality['segments']) for level in args.levels}
        cases.append({'r':r,'vertices':p.tolist(),'known_label':
                      'admits periodic tilings' if r==1 else 'forces aperiodicity',
                      'invariants':invariants(p),'meshes':results})
        print(f'r={r:.6f}: first area-normalized eigenvalue={results[str(max(args.levels))]["area_eigenvalues"][0]:.8f}',flush=True)
    square = np.array([[0,0],[1,0],[1,1],[0,1]],float)
    exact = sorted(np.pi**2*(m*m+n*n) for m in range(1,8) for n in range(1,8))[:12]
    square_quality = triangle.triangulate({'vertices':square,'segments':np.array(
        [(i,(i+1)%4) for i in range(4)])},'pq28a0.003')
    controls = {str(level):solve(square_quality['vertices'],square_quality['triangles'],level,
                               boundary_edges=square_quality['segments']) for level in args.levels}
    for level,data in controls.items():
        data['max_relative_error_vs_exact'] = float(max(abs(np.array(data['eigenvalues'])/exact-1)))
    reference = next(c for c in cases if c['r']==1)
    for case in cases:
        case['relative_difference_from_equilateral'] = {
          level:float(max(abs(np.array(data['area_eigenvalues'])/
                            reference['meshes'][level]['area_eigenvalues']-1)))
          for level,data in case['meshes'].items()}
        if len(args.levels)>1:
            lo,hi = str(min(args.levels)),str(max(args.levels))
            case['max_relative_mesh_change'] = float(max(abs(
              np.array(case['meshes'][lo]['area_eigenvalues'])/
              case['meshes'][hi]['area_eigenvalues']-1)))
            assert np.all(np.array(case['meshes'][hi]['eigenvalues']) <=
                          np.array(case['meshes'][lo]['eigenvalues'])*(1+1e-9))
    assert max(c['meshes'][str(max(args.levels))]['max_relative_residual'] for c in cases)<1e-7
    assert np.ptp([c['invariants']['corner_heat_constant'] for c in cases])<1e-12
    report = {'date':'2026-10-07','operator':'Dirichlet -Laplacian, planar Euclidean metric',
              'normalization':'area times eigenvalue','method':'conforming linear FEM, consistent mass, Triangle quality mesh at r=1, common piecewise-affine deformation, nested midpoint refinement',
              'proof_scope':'Numerical eigenvalue estimates; theorem-derived tiling labels. No spectral decision theorem is claimed.',
              'source':'https://arxiv.org/html/2303.10798v2#S6','levels':args.levels,
              'versions':{'python':platform.python_version(),'numpy':np.__version__,
                          'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,
                          'triangle':triangle.__version__},
              'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'square_control':{'exact':exact,'meshes':controls},'cases':cases}
    (ROOT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fine = str(max(args.levels))
    fig,axes = plt.subplots(1,2,figsize=(11.5,4.1),layout='constrained')
    for j in [0,1,2,5,11]:
        axes[0].plot(params,[c['meshes'][fine]['area_eigenvalues'][j] for c in cases],'.-',label=rf'$A\lambda_{{{j+1}}}$')
    axes[0].axvline(1,color='#c74a40',ls='--',lw=1)
    axes[0].set(xlabel=r'$r=b/a$',ylabel=r'$A\lambda_j$',title='Smooth spectral variation across aperiodicity')
    axes[0].legend(ncol=2,fontsize=9)
    delta = np.array(params)-1
    diffs = [c['relative_difference_from_equilateral'][fine]*100 for c in cases]
    axes[1].plot(delta,diffs,'o-',color='#187f89')
    axes[1].set(xlabel=r'$r-1$',ylabel='Largest change among first 12 modes (%)',title='Distance from the periodic member')
    axes[1].set_xlim(-.055,.055)
    axes[1].set_ylim(-.02,max(diffs[1],diffs[7])*1.2)
    axes[1].axvline(0,color='#c74a40',ls='--',lw=1)
    fig.savefig(ROOT/'spectral-continuity.png',dpi=200)
    fig.savefig(ROOT/'spectral-continuity.pdf')
    plt.close(fig)
    fig,axes = plt.subplots(1,4,figsize=(11.5,3.1),layout='constrained')
    for ax,r in zip(axes,[.8,1,1.2,np.sqrt(3)]):
        p = tile(r)/np.sqrt(area(tile(r)))
        closed = np.vstack((p,p[0]))
        ax.fill(closed[:,0],closed[:,1],color='#dcebe8',edgecolor='#187f89',lw=2)
        ax.set_aspect('equal');ax.axis('off')
        ax.set_title(rf'$r={r:.3f}$'+'\n'+('Periodic tiling exists' if r==1 else 'Forced aperiodic'),fontsize=11)
    fig.savefig(ROOT/'tile-family.png',dpi=200)
    fig.savefig(ROOT/'tile-family.pdf')
    plt.close(fig)
    print('Wrote results.json and two figures.',flush=True)


if __name__=='__main__':
    main()
