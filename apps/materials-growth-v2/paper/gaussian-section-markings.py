"""Finite Gaussian kernel fields as rotation-covariant geometric m-values.

For opaque channel c, f_c(x)=sum_i a_i exp(-|x-v_i|²/(2 sigma²)).
The product RKHS inner product is sum_ij a_i b_j k(v_i,w_j) within
matching channels. Fields are not physical potentials or atom configurations.
Atoms outside a compact radial window have zero amplitude. Field values are
not normalized to unit mass; labels and weighted density remain distinguishable.
"""
import math
import json
import itertools
import numpy as np

def validate(field):
    v=np.asarray(field['vectors'],dtype=float);a=np.asarray(field['amplitudes'],dtype=float)
    if not len(a):v=v.reshape(0,3)
    if v.shape!=(len(a),3) or len(field['colors'])!=len(a) or not np.isfinite(v).all() or not np.isfinite(a).all():raise ValueError('Invalid finite field')
    if not np.isfinite(field['sigma']) or field['sigma']<=0:raise ValueError('Invalid kernel width')
    return v,a,[json.dumps(c,sort_keys=True) for c in field['colors']]

def from_points(vectors,colors,radius,sigma):
    if not np.isfinite(radius) or radius<=0:raise ValueError('Invalid support radius')
    v=np.asarray(vectors,dtype=float).reshape(-1,3)
    if len(v)!=len(colors):raise ValueError('Point/color mismatch')
    if not np.isfinite(v).all():raise ValueError('Nonfinite coordinates')
    amplitudes=np.maximum(0,1-np.sum(v*v,axis=1)/radius**2)**3
    keep=amplitudes>0
    f=dict(vectors=v[keep].tolist(),colors=[c for c,k in zip(colors,keep) if k],amplitudes=amplitudes[keep].tolist(),sigma=float(sigma))
    validate(f);return f

def periodic_field(positions,colors,cell,anchor,radius,sigma,max_images=2000000):
    """All periodic images strictly inside a radial window, not minimum images.

    Row-vector cell convention; channels are opaque labels. An image of a
    labeled point has the same channel. No chemistry or cover graph enters.
    Bounds follow |(v @ inverse_cell)[k]| <= radius*norm(inverse_cell[:,k]).
    A safety ceiling raises rather than returning a truncated neighborhood.
    Floating-point extraction is not an exact boundary certificate. Because
    the window vanishes cubically at its boundary, boundary entries have
    vanishing weight. Nearly singular cells are rejected explicitly.
    """
    p=np.asarray(positions,dtype=float).reshape(-1,3)
    c=np.asarray(cell,dtype=float);o=np.asarray(anchor,dtype=float)
    if len(p)!=len(colors) or not np.isfinite(p).all():raise ValueError('Invalid positions/channels')
    if c.shape!=(3,3) or o.shape!=(3,) or not np.isfinite(c).all() or not np.isfinite(o).all():raise ValueError('Invalid cell/anchor')
    if not np.isfinite(radius) or radius<=0:raise ValueError('Invalid support radius')
    if np.linalg.cond(c)>1e10:raise ValueError('Cell is singular or ill-conditioned')
    if not isinstance(max_images,int) or max_images<1:raise ValueError('Invalid image budget')
    inv=np.linalg.inv(c)
    # Wrap each input independently: equivalent translated unit-cell choices
    # produce the same infinite point set, with image multiplicity retained.
    fractional=(p-o)@inv
    fractional-=np.floor(fractional+.5)
    bounds=np.ceil(radius*np.linalg.norm(inv,axis=0)+.5+1e-10).astype(int)
    count=len(p)*math.prod(2*int(b)+1 for b in bounds)
    if count>max_images:raise ValueError(f'Periodic image budget exceeded: {count} > {max_images}')
    vectors=[];labels=[]
    for shift in itertools.product(*(range(-int(b),int(b)+1) for b in bounds)):
        v=(fractional+shift)@c
        for i in np.flatnonzero(np.sum(v*v,axis=1)<radius**2):
            vectors.append(v[i]);labels.append(colors[i])
    return from_points(vectors,labels,radius,sigma)

def transform(field,rotation):
    v,_,_=validate(field);r=np.asarray(rotation,dtype=float)
    if r.shape!=(3,3) or not np.isfinite(r).all() or np.max(np.abs(r.T@r-np.eye(3)))>1e-8 or abs(np.linalg.det(r)-1)>1e-8:raise ValueError('Proper rotation required')
    return dict(field,vectors=(v@r).tolist())

def inner(a,b):
    x,wa,ca=validate(a);y,wb,cb=validate(b)
    if a['sigma']!=b['sigma']:raise ValueError('Kernel widths differ')
    terms=[float(wa[i]*wb[j]*math.exp(-float(np.dot(u-v,u-v))/(2*a['sigma']**2)))
           for i,u in enumerate(x) for j,v in enumerate(y) if ca[i]==cb[j]]
    return math.fsum(terms)

def discrepancy(a,b):
    aa=inner(a,a);bb=inner(b,b);ab=inner(a,b);raw=math.fsum([aa,bb,-2*ab])
    mass=sum(map(abs,a['amplitudes']))+sum(map(abs,b['amplitudes']))
    guard=128*np.finfo(float).eps*max(1.,mass*mass)
    if raw < -guard:raise ArithmeticError('Negative squared norm beyond numerical guard')
    return dict(squared=max(0.,raw),rawSquared=raw,roundoffGuard=guard,
                lower=max(0.,raw-guard),upper=max(0.,raw+guard))

def mixture(a,b):
    validate(a);validate(b)
    if a['sigma']!=b['sigma']:raise ValueError('Kernel widths differ')
    return dict(vectors=a['vectors']+b['vectors'],colors=a['colors']+b['colors'],
                amplitudes=[v/2 for v in a['amplitudes']+b['amplitudes']],sigma=a['sigma'])

def pair_status(a,b,radius):
    if not np.isfinite(radius) or radius<0:raise ValueError('Invalid marking radius')
    d=discrepancy(a,b);bound=4*radius**2
    # Engineering floating-point guard, not certified interval arithmetic.
    status='separated' if d['lower']>bound else 'compatible' if d['upper']<=bound else 'numerically-unresolved'
    return dict(status=status,**d)

def evaluate(field,points,color):
    v,a,c=validate(field);key=json.dumps(color,sort_keys=True)
    return [math.fsum(float(w*math.exp(-float(np.dot(np.asarray(p)-x,np.asarray(p)-x))/(2*field['sigma']**2))) for x,w,k in zip(v,a,c) if k==key) for p in points]
