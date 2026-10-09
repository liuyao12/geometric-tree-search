"""Geometric certificates for the frozen A2 turtle point model.

Inspection only: no polygon predicate, atom inventory, or new marking enters
search. Coordinates use the first two cube components, with exact rationals.
The elementary triangular grid is subdivided into vertex/midpoint/centroid
flags. Each flag belongs to one original lattice point.
"""
from collections import Counter
from fractions import Fraction
from turtle import BASE, VERTICES, SYMMETRIES, transform
from audit_geometry import triangulate, cross, area

DIRECTIONS=((1,0),(0,1),(-1,1),(-1,0),(0,-1),(1,-1))

def triangle(key):
    """Three integer vertices at coordinate scale six, positive orientation."""
    x,y,i,s=key;a,b=DIRECTIONS[i],DIRECTIONS[(i+1)%6];n=(a,b)[s]
    out=((6*x,6*y),(6*x+3*n[0],6*y+3*n[1]),
         (6*x+2*(a[0]+b[0]),6*y+2*(a[1]+b[1])))
    return out if area(out)>0 else (out[0],out[2],out[1])

def intersection_area(a,b):
    out=[tuple(Fraction(x) for x in p) for p in a]
    for u,v in zip(b,b[1:]+b[:1]):
        prior,out=out,[]
        if not prior:return Fraction(0)
        for p,q in zip(prior,prior[1:]+prior[:1]):
            sp,sq=cross(u,v,p),cross(u,v,q)
            if sp>=0:out.append(p)
            if (sp<0 and sq>=0) or (sp>=0 and sq<0):
                t=sp/(sp-sq);out.append(tuple(x+t*(y-x) for x,y in zip(p,q)))
    return abs(area(out))/2 if out else Fraction(0)

def prototype():
    poly=tuple((6*p[0],6*p[1]) for p in VERTICES);pieces=triangulate(poly)
    selected=[];tests=0
    for x in range(min(p[0] for p in VERTICES)-1,max(p[0] for p in VERTICES)+2):
        for y in range(min(p[1] for p in VERTICES)-1,max(p[1] for p in VERTICES)+2):
            for i in range(6):
                for s in range(2):
                    k=(x,y,i,s);t=triangle(k)
                    # Every potential intersection is clipped, not inferred from
                    # one point. Strict box separation is an exact zero control.
                    a=Fraction(0)
                    for u in pieces:
                        tests+=1
                        if any(max(p[d] for p in t)<=min(p[d] for p in u) or
                               max(p[d] for p in u)<=min(p[d] for p in t) for d in (0,1)):continue
                        a+=intersection_area(t,u)
                    if a not in (0,3):raise ValueError('turtle edge cuts a flag interior')
                    if a:selected.append(k)
    if 3*len(selected)!=abs(area(poly))/2:raise ValueError('atom area does not cover polygon')
    values=Counter((x,y,-x-y) for x,y,i,s in selected)
    if values!=BASE:raise ValueError('flag counts differ from frozen point data')
    return tuple(sorted(selected)),{'candidate_flags':(max(p[0] for p in VERTICES)-min(p[0] for p in VERTICES)+3)*(max(p[1] for p in VERTICES)-min(p[1] for p in VERTICES)+3)*12,
        'triangle_clip_candidates':tests,'occupied_flags':len(selected),'point_count':len(values),
        'coordinate_area':str(Fraction(abs(area(poly)),72)),
        'flag_coordinate_area':'1/12','coordinate_scale':6}

def mapped(key,g):
    p=(key[0],key[1],-key[0]-key[1]);owner=transform(p,g)
    wanted=frozenset(transform((x,y,-x-y),g)[:2] for x,y in triangle(key))
    for i in range(6):
        for s in range(2):
            k=(owner[0],owner[1],i,s)
            if frozenset(triangle(k))==wanted:return k
    raise ValueError('symmetry does not preserve canonical flags')

def orientations(atoms):
    for g in SYMMETRIES:
        if len({mapped((0,0,i,s),g) for i in range(6) for s in range(2)})!=12:
            raise ValueError('symmetry loses flags')
    out=tuple(frozenset(mapped(k,g) for k in atoms) for g in SYMMETRIES)
    for g,a in zip(SYMMETRIES,out):
        if Counter((x,y,-x-y) for x,y,i,s in a)!={transform(p,g):v for p,v in BASE.items()}:
            raise ValueError('transformed occupancy differs')
    return out

def translated(atoms,tr):return frozenset((x+tr[0],y+tr[1],i,s) for x,y,i,s in atoms)

def pair_catalog(oriented):
    rows=[];root=oriented[0]
    for o,(g,atoms) in enumerate(zip(SYMMETRIES,oriented)):
        poly=tuple(transform(p,g) for p in VERTICES);occ={transform(p,g):v for p,v in BASE.items()}
        xr=(min(p[0] for p in VERTICES)-max(p[0] for p in poly),max(p[0] for p in VERTICES)-min(p[0] for p in poly))
        yr=(min(p[1] for p in VERTICES)-max(p[1] for p in poly),max(p[1] for p in VERTICES)-min(p[1] for p in poly))
        for x in range(xr[0],xr[1]+1):
            for y in range(yr[0],yr[1]+1):
                if (o,x,y)==(0,0,0):continue
                shifted={(p[0]+x,p[1]+y,p[2]-x-y):v for p,v in occ.items()}
                conflicts=sorted(p for p,v in shifted.items() if BASE.get(p,0)+v>12)
                shared=sorted(root & translated(atoms,(x,y,-x-y)))
                if bool(conflicts)!=bool(shared):raise ValueError('point/polygon disagreement')
                rows.append({'pose':[o,[x,y,-x-y]],'overloaded_points':conflicts,
                    'shared_flags':shared,'shared_positive_points':len(set(BASE)&set(shifted))})
    return rows

def exact_pose(key):
    if not isinstance(key,(tuple,list)) or len(key)!=2:raise ValueError('invalid base pose')
    o,tr=key
    if type(o) is not int or not 0<=o<12 or len(tr)!=3 or any(type(v) is not int for v in tr) or sum(tr):
        raise ValueError('pose must use the declared integer A2 translations')
    return o,tuple(tr)

def patch_flags(keys,oriented):
    keys=tuple(exact_pose(k) for k in keys)
    if len(keys)!=len(set(keys)):raise ValueError('duplicate placement owner')
    occupied=set();totals=Counter()
    for o,tr in keys:
        a=translated(oriented[o],tr)
        if occupied & a:raise ValueError('polygon interiors overlap')
        occupied.update(a);totals.update((x,y,-x-y) for x,y,i,s in a)
    if any(v>12 for v in totals.values()):raise ValueError('capacity conflict')
    return frozenset(occupied),totals

def exact_points(points):
    out=frozenset(tuple(p) for p in points)
    if any(len(p)!=3 or any(type(x) is not int for x in p) or sum(p) for p in out):raise ValueError('invalid A2 point set')
    return out

def cell_flags(points):return frozenset((p[0],p[1],i,s) for p in exact_points(points) for i in range(6) for s in range(2))

def verify_region(keys,required,allowed,oriented):
    required=exact_points(required);allowed=exact_points(allowed)
    occupied,totals=patch_flags(keys,oriented);required_atoms=cell_flags(required)
    return {'tiles':len(keys),'occupied_flags':len(occupied),'required_points':len(required),
        'required_flags':len(required_atoms),'missing_required_flags':len(required_atoms-occupied),
        'extra_flags_outside_required':len(occupied-required_atoms),
        'flags_outside_allowed':sum((x,y,-x-y) not in allowed for x,y,i,s in occupied),
        'point_complete':all(totals[p]==12 for p in required)}
