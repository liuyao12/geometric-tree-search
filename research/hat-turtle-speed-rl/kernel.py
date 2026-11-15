"""Self-contained exact kernel adapted from the repository's cold point engine.

Kept local so reproducing this experiment needs no cloud-backed source files.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import permutations

CAPACITY = 12
VERTICES = ((3,-2,-1),(2,0,-2),(0,1,-1),(0,2,-2),(-1,3,-2),
            (-2,2,0),(-1,0,1),(-2,0,2),(-2,-1,3),(0,-2,2),
            (1,-4,3),(2,-4,2),(3,-5,2),(4,-4,0))
SYMMETRIES = tuple((s,p) for s in (1,-1) for p in permutations(range(3)))
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def transform(p,g): return tuple(g[0]*p[i] for i in g[1])
def compose(g,h): return (g[0]*h[0],tuple(h[1][g[1][j]] for j in range(3)))
def inverse(p,g):
    out=[0,0,0]
    for j,i in enumerate(g[1]): out[i]=g[0]*p[j]
    return tuple(out)
def inside(p,polygon):
    x,y=p[:2];result=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        cross=(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])
        if cross==0 and min(a[0],b[0])<=x<=max(a[0],b[0]) and min(a[1],b[1])<=y<=max(a[1],b[1]):return False
        if (a[1]>y)!=(b[1]>y) and x<a[0]+Fraction((y-a[1])*(b[0]-a[0]),b[1]-a[1]):result=not result
    return result
def area2(loop): return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(loop,loop[1:]+loop[:1]))

# Exact common subdivision for all short/long A2 edges, from a2-polysnakes.
TEMPLATES={}
for tri in [((0,0),(6,0),(0,6)),((6,6),(0,6),(6,0))]:
    center=tuple(sum(v[k] for v in tri)//3 for k in range(2))
    for a,b in zip(tri,tri[1:]+tri[:1]):
        mid=tuple((a[k]+b[k])//2 for k in range(2))
        for v in (a,b):
            verts=tuple(sorted((center,mid,v)))
            TEMPLATES[tuple(sum(w[k] for w in verts) for k in range(2))]=verts
assert len(TEMPLATES)==12
def atomize(loop):
    polygon=tuple((18*x,18*y) for x,y in loop)
    atoms=frozenset((18*x+a,18*y+b)
        for x in range(min(p[0] for p in loop),max(p[0] for p in loop))
        for y in range(min(p[1] for p in loop),max(p[1] for p in loop))
        for a,b in TEMPLATES if inside((18*x+a,18*y+b),polygon))
    assert len(atoms)==6*abs(area2(loop))
    return atoms

@dataclass(frozen=True)
class Placement:
    key:tuple
    occupancy:tuple
    marks:tuple
    vertices:tuple

@dataclass
class State:
    totals:dict=field(default_factory=dict)
    marks:dict=field(default_factory=dict)
    generations:dict=field(default_factory=dict)
    roots:dict=field(default_factory=dict)
    selected:set=field(default_factory=set)
    order:list=field(default_factory=list)
    tile_generations:list=field(default_factory=list)
    def copy(self):return State(self.totals.copy(),self.marks.copy(),self.generations.copy(),self.roots.copy(),self.selected.copy(),self.order.copy(),self.tile_generations.copy())
    def legal(self,c):
        return c.key not in self.selected and all(self.totals.get(p,0)+v<=12 for p,v in c.occupancy) and all(p not in self.marks or self.marks[p]==v for p,v in c.marks)
    def place(self,c,seed=False):
        if not self.legal(c):raise ValueError('illegal point-value placement')
        incident=[self.generations[p] for p,_ in c.occupancy if p in self.generations]
        gen=0 if seed or not incident else 1+min(incident)
        for p,v in c.occupancy:
            self.totals[p]=self.totals.get(p,0)+v
            self.generations[p]=min(self.generations.get(p,gen),gen,self.roots.get(p,gen))
        for p,v in c.marks:self.marks[p]=v
        self.selected.add(c.key);self.order.append(c.key);self.tile_generations.append(gen)
        return {p for p,_ in c.occupancy+c.marks}
    def frontier(self):return {p for p in self.totals.keys()|self.roots.keys() if self.totals.get(p,0)<12}

class Graph:
    def __init__(self,model,state):
        self.domains={};self.edges={}
        self.update(model,state,set(state.totals)|set(state.roots)|set(state.marks))
    def copy(self):
        out=object.__new__(type(self));out.domains={p:cs.copy() for p,cs in self.domains.items()};out.edges={c:ps.copy() for c,ps in self.edges.items()};return out
    def update(self,model,state,changed):
        frontier=state.frontier()
        for p in self.domains.keys()-frontier:
            for k in self.domains[p]:
                self.edges[k].remove(p)
                if not self.edges[k]:del self.edges[k]
            del self.domains[p]
        fresh=frontier-self.domains.keys();candidates=set()
        for p in fresh:self.domains[p]=set();candidates.update(model.alignments(p))
        for p in changed:candidates.update(model.dependencies.get(p,()))
        for k in candidates:
            c=model.placement(k);model.metrics['candidate_tests']+=1
            wanted={p for p,_ in c.occupancy if p in frontier} if state.legal(c) else set()
            prior=self.edges.get(k,set())
            for p in prior-wanted:self.domains[p].remove(k)
            for p in wanted-prior:self.domains[p].add(k)
            if wanted:self.edges[k]=wanted
            elif k in self.edges:del self.edges[k]
    def decision(self,state):
        dead=sorted(p for p,cs in self.domains.items() if not cs)
        if dead:return 'dead',dead[0],[]
        forced=sorted(p for p,cs in self.domains.items() if len(cs)==1)
        if forced:return 'forced',forced[0],sorted(self.domains[forced[0]])
        if not self.domains:return 'empty',None,[]
        p=min(self.domains,key=lambda p:(state.generations.get(p,state.roots.get(p,0)),len(self.domains[p]),p))
        return 'branch',p,sorted(self.domains[p])
    def fingerprint(self):return (tuple(sorted((p,tuple(sorted(cs))) for p,cs in self.domains.items())),tuple(sorted((c,tuple(sorted(ps))) for c,ps in self.edges.items())))

class Limit(Exception):pass
