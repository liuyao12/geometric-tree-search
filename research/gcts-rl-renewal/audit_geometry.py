"""Independent exact polygon-overlap audit; never an input to base legality.

Ear triangulation and rational convex clipping certify positive intersection
area. The audit replays completed run artifacts; it cannot influence learning.
"""
import hashlib
import json
from fractions import Fraction
from itertools import permutations
from pathlib import Path

def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def area(poly): return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1]))
def triangulate(poly):
    poly = list(poly)
    if area(poly)<0: poly.reverse()
    while any(cross(poly[i-1],p,poly[(i+1)%len(poly)])==0 for i,p in enumerate(poly)):
        for i,p in enumerate(poly):
            if cross(poly[i-1],p,poly[(i+1)%len(poly)])==0:
                poly.pop(i)
                break
    out = []
    while len(poly)>3:
        for i,b in enumerate(poly):
            a,c = poly[i-1],poly[(i+1)%len(poly)]
            if cross(a,b,c)<=0: continue
            others = [p for j,p in enumerate(poly) if j not in ((i-1)%len(poly),i,(i+1)%len(poly))]
            if any(cross(a,b,p)>=0 and cross(b,c,p)>=0 and cross(c,a,p)>=0 for p in others): continue
            out.append([a,b,c])
            poly.pop(i)
            break
        else: raise ValueError("polygon could not be triangulated")
    out.append(poly)
    return out

def positive_intersection(a,b):
    if max(p[0] for p in a)<=min(p[0] for p in b) or max(p[0] for p in b)<=min(p[0] for p in a): return False
    if max(p[1] for p in a)<=min(p[1] for p in b) or max(p[1] for p in b)<=min(p[1] for p in a): return False
    out = [tuple(Fraction(x) for x in p) for p in a]
    for u,v in zip(b,b[1:]+b[:1]):
        incoming,out = out,[]
        if not incoming: return False
        for p,q in zip(incoming,incoming[1:]+incoming[:1]):
            sp,sq = cross(u,v,p),cross(u,v,q)
            if sp>=0: out.append(p)
            if (sp<0 and sq>=0) or (sp>=0 and sq<0):
                t = sp/(sp-sq)
                out.append(tuple(x+t*(y-x) for x,y in zip(p,q)))
    return bool(out) and area(out)!=0

def audit(data):
    # Sanity checks exercise touching, overlapping, nested, and separate triangles.
    tri = [(0,0),(2,0),(0,2)]
    assert positive_intersection(tri,tri)
    assert positive_intersection(tri,[(0,0),(1,0),(0,1)])
    assert not positive_intersection(tri,[(2,0),(3,0),(2,1)])
    assert not positive_intersection(tri,[(4,0),(5,0),(4,1)])
    base = [tuple(p[:2]) for p in data["point_model"]["vertices"]]
    triangles = triangulate(base)
    assert sum(area(t) for t in triangles)==abs(area(base))
    syms = [(s,p) for s in (1,-1) for p in permutations(range(3))]
    cache = {}
    def placement(key):
        o,tr = key
        ident = (o,tuple(tr))
        if ident not in cache:
            s,p = syms[o]
            transformed = []
            for triangle in triangles:
                points = []
                for x,y in triangle:
                    q = (x,y,-x-y)
                    points.append(tuple(s*q[p[i]]+tr[i] for i in (0,1)))
                if area(points)<0: points.reverse()
                transformed.append(points)
            cache[ident] = transformed
        return cache[ident]
    def overlaps(a,b):
        return any(positive_intersection(u,v) for u in placement(a) for v in placement(b))
    contacts = []
    for i,sample in enumerate(data["pair_catalog"]["samples"]):
        if overlaps((0,(0,0,0)),sample["second"]): contacts.append({"index":i,"label":sample["status"]})
    runs = []
    for run in data["evaluation"]:
        keys = run["placements"]
        bad = [(i,j) for i,a in enumerate(keys) for j,b in enumerate(keys[:i]) if overlaps(a,b)]
        runs.append({"lane":run["lane"],"seed":run["seed"],"tiles":len(keys),"overlapping_pairs":bad})
    return {"method":"exact ear triangulation and rational triangle clipping; inspection only",
            "prototype_triangles":len(triangles),"catalog_overlap_contacts":contacts,
            "evaluation_runs":runs,"all_reported_patches_nonoverlapping":all(not r["overlapping_pairs"] for r in runs),
            "scope":"finite polygon interiors only; does not prove coverage or faithfulness of all point-model solutions",
            "audit_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}

if __name__=="__main__":
    root = Path(__file__).resolve().parents[2]
    path = root/"docs/research/gcts-rl-renewal/iteration-001.json"
    data = json.loads(path.read_text())
    result = audit(data)
    data["geometry_audit"] = result
    # Public inspection evidence does not need this machine's filesystem path.
    data["config"]["output"] = Path(data["config"]["output"]).name
    path.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("catalog_overlap_contacts","evaluation_runs")},indent=2))
    print("catalog overlapping pairs",len(result["catalog_overlap_contacts"]))
