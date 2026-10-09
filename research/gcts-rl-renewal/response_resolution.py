"""One-decision RL controller for the cost of a whole finite boundary request.

This pilot chooses a proposal resolution before search. It does not refine a
failed prefix, alter the target, omit a base candidate or import a completion.
Choosing base avoids response enumeration and its policy feature construction.
"""
from turtle import Policy,Model,add
from coverage import hexagon
from region_tiles import Boundary
from boundary_responses import search

MODES=('base','small','hierarchy')
def training_boundaries(allowed):
    out=[]
    for i,(r,c) in enumerate(((3,(1,-1,0)),(5,(-1,0,1)),(7,(1,1,-2)),(9,(-2,1,1)))):
        out.append(Boundary('resolution-regular-'+str(i),frozenset(add(p,c) for p in hexagon(r)),allowed))
    for i,r in enumerate((5,7)):
        pts={p for p in hexagon(r) if not(p[0]>1 and p[1]>1)}|{(r+4,-3,-r-1)}
        out.append(Boundary('resolution-notch-'+str(i),frozenset(pts),allowed))
    fixed=Model().placement((0,(5,-2,-3)))
    out.append(Boundary('resolution-exterior',frozenset(hexagon(5)),allowed,fixed.occupancy,(),((0,(5,-2,-3)),)))
    return tuple(out)

def features(boundary,mode):
    pts=boundary.required;spans=[max(p[i] for p in pts)-min(p[i] for p in pts)+1 for i in range(3)]
    # Features use only externally declared problem data, before inventory bind.
    density=len(pts)/(min(spans)*max(spans));prefix='mode:'+mode+':'
    return {prefix+'bias':1.,prefix+'area':len(pts)/300,prefix+'density':density,
            prefix+'exterior':float(bool(boundary.exterior)),prefix+'span':max(spans)/24}

def request(boundary,universe,atlases,policy,seed,learn=False,zero=False,seconds=6):
    import random,time
    start=time.monotonic();fs=[features(boundary,m) for m in MODES]
    if learn:i,gradient=policy.select(random.Random(seed),fs)
    else:
        active=Policy() if zero else policy
        scores=[sum(active.weights[k]*v for k,v in f.items()) for f in fs]
        top=max(scores);ties=[j for j,v in enumerate(scores) if v==top]
        i=random.Random(seed).choice(ties);gradient=None
    mode=MODES[i];selection_seconds=time.monotonic()-start
    r=search(boundary,universe,seed,seconds=seconds,atlas=atlases.get(mode))
    # Completed value and wall cost, rather than the number of chosen macros.
    reward=2*float(r['status']=='finite_exact_region')+r['coverage_fraction']-r['seconds']
    if learn:policy.update([gradient],reward)
    return {'mode':mode,'scores':None if learn else scores,'features':fs,'selection_seconds':selection_seconds,
            'total_request_seconds':time.monotonic()-start,'reward':reward,'result':r}
