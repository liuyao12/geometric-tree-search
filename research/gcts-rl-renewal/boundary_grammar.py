"""Exact boundary/hull words for substitution hypotheses, never legality.

Polygon segments only author structural descriptors of already verified point
clusters. Primitive edge cancellation yields a boundary word when the boundary
is manifold. Dropping lengths defines an ABSTRACT type, not an exact metatile.
Hull descriptors are an explicitly weaker geometric control. No known family
or substitution is supplied to either classifier.
"""
import math
from collections import Counter,defaultdict
from turtle import Model,SYMMETRIES,add,sub,transform
from spatial import keys_tuple,moved,interface,partition

def cross(a,b,c): return (b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
def area2(loop): return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(loop,loop[1:]+loop[:1]))
def primitive(d):
    n=math.gcd(math.gcd(abs(d[0]),abs(d[1])),abs(d[2]))
    if not n: raise ValueError("zero edge")
    return tuple(v//n for v in d),n
def simplify(loop):
    loop=list(loop)
    while len(loop)>3:
        indices=[i for i in range(len(loop)) if cross(loop[i-1],loop[i],loop[(i+1)%len(loop)])==0]
        if not indices: break
        loop=[p for i,p in enumerate(loop) if i not in indices]
    return tuple(loop)

def boundary(model,keys):
    edges=Counter()
    for key in keys:
        loop=model.placement(key).vertices
        if area2(loop)<0: loop=tuple(reversed(loop))
        for a,b in zip(loop,loop[1:]+loop[:1]):
            d,n=primitive(sub(b,a))
            for i in range(n):
                p=add(a,tuple(i*v for v in d));q=add(p,d)
                edges[p,q]+=1
    residual=Counter({(a,b):max(0,n-edges[b,a]) for (a,b),n in edges.items()})
    residual=+residual
    if any(n!=1 for n in residual.values()): return None
    outgoing=defaultdict(list);incoming=Counter()
    for a,b in residual: outgoing[a].append(b);incoming[b]+=1
    if any(len(bs)!=1 or incoming[p]!=1 for p,bs in outgoing.items()): return None
    unseen=set(outgoing);loops=[]
    while unseen:
        first=min(unseen);p=first;loop=[]
        while p in unseen:
            unseen.remove(p);loop.append(p);p=outgoing[p][0]
        if p!=first: return None
        loops.append(simplify(loop))
    return tuple(sorted(loops))

def hull(points):
    ps=sorted(set(points))
    if len(ps)<3: return tuple(ps)
    lower=[];upper=[]
    for p in ps:
        while len(lower)>1 and cross(lower[-2],lower[-1],p)<=0: lower.pop()
        lower.append(p)
    for p in reversed(ps):
        while len(upper)>1 and cross(upper[-2],upper[-1],p)<=0: upper.pop()
        upper.append(p)
    return tuple(lower[:-1]+upper[:-1])

def words(loops,lengths=False):
    """Canonical oriented direction cycles, with or without integer edge lengths."""
    if not loops: return None
    candidates=[]
    for g in SYMMETRIES:
        encoded=[]
        for loop in loops:
            transformed=tuple(transform(p,g) for p in loop)
            # Preserve each loop's interior/hole winding under reflection.
            if area2(transformed)*area2(loop)<0: transformed=tuple(reversed(transformed))
            entries=[]
            for a,b in zip(transformed,transformed[1:]+transformed[:1]):
                d,n=primitive(sub(b,a));entries.append((d,n) if lengths else d)
            entries=tuple(entries)
            encoded.append(min(entries[i:]+entries[:i] for i in range(len(entries))))
        candidates.append(tuple(sorted(encoded)))
    return min(candidates)

def descriptors(model,keys):
    keys=keys_tuple(keys);loops=boundary(model,keys)
    h=hull(p for key in keys for p in model.placement(key).vertices)
    return {"boundary":words(loops),"boundary_with_lengths":words(loops,True),
            "hull":words((h,)),"hull_with_lengths":words((h,),True),"manifold_boundary":loops is not None}

def infer(model,donors,library,levels=4,partitioner=partition):
    """Inspect recurrence of abstract types/child rules across grouping levels."""
    registries={mode:{} for mode in ("boundary","hull")}
    evidence={mode:defaultdict(list) for mode in registries};productions={mode:Counter() for mode in registries}
    samples=[];nonmanifold=0
    for donor in donors:
        if donor["status"]!="consistent_finite_patch": continue
        keys=keys_tuple(donor["placements"])
        grouping=partitioner(model,keys,library,levels)
        previous={mode:[] for mode in registries}
        rows=[]
        for lev in grouping["levels"]:
            current={mode:[] for mode in registries};groups=[]
            for group in lev["groups"]:
                selected=[keys[i] for i in group["base_ids"]];d=descriptors(model,selected)
                if not d["manifold_boundary"]: nonmanifold+=1
                types={}
                for mode,registry in registries.items():
                    word=d[mode]
                    typ=None if word is None else registry.setdefault(word,len(registry))
                    types[mode]=typ;current[mode].append(typ)
                    if typ is not None:
                        evidence[mode][typ].append({"seed":donor["seed"],"level":lev["level"],"base_tiles":len(selected)})
                        if "children" in group:
                            children=tuple(sorted(previous[mode][i] for i in group["children"] if previous[mode][i] is not None))
                            if len(children)==len(group["children"]):productions[mode][typ,children]+=1
                groups.append({**group,"descriptors":d,"abstract_types":types})
            rows.append({"level":lev["level"],"groups":groups});previous=current
        samples.append({"seed":donor["seed"],"placements":keys,"levels":rows,
                        "verified_partition":grouping["levels"][-1]["verified_partition"]})
    summaries={}
    for mode,registry in registries.items():
        inverse={typ:word for word,typ in registry.items()}
        classes=[]
        for typ,obs in sorted(evidence[mode].items()):
            ls=sorted({o["level"] for o in obs});sizes=sorted({o["base_tiles"] for o in obs})
            classes.append({"id":typ,"word":inverse[typ],"observations":obs,"levels":ls,"base_tile_counts":sizes})
        choices=defaultdict(set)
        for p,cs in productions[mode]:
            if len(cs)>1:choices[p].add(cs)
        summaries[mode]={"types":classes,"type_count":len(classes),
            "types_across_three_levels":sum(len(c["levels"])>=3 for c in classes),
            "types_with_growing_instances":sum(len(c["base_tile_counts"])>=3 for c in classes),
            "parent_types_with_multiple_child_patterns":sum(len(cs)>1 for cs in choices.values()),
            "observed_productions":[{"parent":p,"children":cs,"count":n} for (p,cs),n in productions[mode].most_common()],
            "scope":"abstract structural hypotheses; no exact recursive placement map or substitution certificate"}
    return {"classifiers":summaries,"samples":samples,"nonmanifold_instances":nonmanifold,
            "scope":"finite hierarchy inspection; polygon boundary/hull authoring only, never a base legality test"}
