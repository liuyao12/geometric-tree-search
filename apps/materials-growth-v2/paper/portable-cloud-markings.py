"""Portable, rotation-covariant set-valued markings at point anchors.

A value is a colored cloud of displacement vectors. A radius defines the set
of possible common values through color-preserving bijections. Agreement of
several assignments requires one common witness, not a chain of close pairs.
This module verifies supplied witnesses; failure to find a witness is unknown.
"""
from collections import Counter
import numpy as np

def transform(cloud, rotation):
    r=np.asarray(rotation,dtype=float)
    if r.shape!=(3,3) or not np.isfinite(r).all() or np.max(np.abs(r.T@r-np.eye(3)))>1e-7 or abs(np.linalg.det(r)-1)>1e-7:
        raise ValueError('Expected a finite proper rotation')
    return {'vectors':(np.asarray(cloud['vectors'])@r).tolist(),'colors':[list(c) for c in cloud['colors']]}

def contains(assignment, witness, radius):
    """Return a checked bijection, without fitting any additional rotation."""
    if not np.isfinite(radius) or radius<0:raise ValueError('Invalid radius')
    a=np.asarray(assignment['vectors'],dtype=float);b=np.asarray(witness['vectors'],dtype=float)
    if a.ndim!=2 or b.ndim!=2 or a.shape[1:]!=(3,) or b.shape[1:]!=(3,) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Invalid marking vectors')
    ca=list(map(tuple,assignment['colors']));cb=list(map(tuple,witness['colors']))
    if len(ca)!=len(a) or len(cb)!=len(b):raise ValueError('Color/vector size mismatch')
    if Counter(ca)!=Counter(cb):return None
    distances=np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2)
    options=[[k for k in range(len(b)) if ca[i]==cb[k] and distances[i,k]<=radius+1e-10] for i in range(len(a))]
    owner={}
    def augment(i,seen):
        for k in options[i]:
            if k in seen:continue
            seen.add(k)
            if k not in owner or augment(owner[k],seen):owner[k]=i;return True
        return False
    if not all(augment(i,set()) for i in sorted(range(len(a)),key=lambda i:len(options[i]))):return None
    perm=[None]*len(a)
    for k,i in owner.items():perm[i]=k
    return {'permutation':perm,'maxResidual':float(max(distances[i,k] for i,k in enumerate(perm)))}

def common_witness(assignments, witness, radius):
    """All assigned m-sets contain the SAME value; pairwise chaining is forbidden."""
    fits=[contains(a,witness,radius) for a in assignments]
    return fits if all(f is not None for f in fits) else None

def propose_common_witness(assignments, radius):
    """Find and verify a consensus without a target cloud; failure stays unknown.

    A first-cloud correspondence and mean are proposals, not a complete solver
    for all correspondences or intersections. Never use unknown to kill a branch.
    """
    if not assignments:raise ValueError('At least one assignment is required')
    reference=assignments[0];aligned=[]
    for assignment in assignments:
        fit=contains(assignment,reference,2*radius)
        if fit is None:return {'status':'unknown'}
        vectors=np.empty_like(np.asarray(reference['vectors'],dtype=float))
        for i,k in enumerate(fit['permutation']):vectors[k]=assignment['vectors'][i]
        aligned.append(vectors)
    for vectors in [np.mean(aligned,axis=0),*aligned]:
        witness={'vectors':vectors.tolist(),'colors':[list(c) for c in reference['colors']]}
        fits=common_witness(assignments,witness,radius)
        if fits is not None:return {'status':'verified-witness','witness':witness,'fits':fits}
    return {'status':'unknown'}
