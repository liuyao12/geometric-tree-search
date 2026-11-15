"""Cold exact hat/turtle point model; geometry authors data, never search rules.

The reference graph/state are reused. Atom-centroid capacity points additionally
certify polygon nonoverlap. No known marking/substitution module is imported.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import kernel as ref
geo = ref
SHAPES = {
    "turtle": ref.VERTICES,
    "hat": ((0,0,0),(1,0,-1),(1,1,-2),(3,0,-3),(4,1,-5),(3,2,-5),
            (3,3,-6),(1,4,-5),(0,6,-6),(-1,6,-5),(-1,5,-4),
            (-1,4,-3),(0,3,-3),(-1,2,-1)),
}
SCALE = 18
DIRECTIONS = ((1,0),(1,1),(0,1),(-1,2),(-1,1),(-2,1),
              (-1,0),(-1,-1),(0,-1),(1,-2),(1,-1),(2,-1))


def point_data(vertices):
    """Angle units from exact direction indices, plus interior lattice points."""
    loop = tuple(vertices)
    orientation = 1 if geo.area2(tuple(p[:2] for p in loop)) > 0 else -1
    edges = []
    for a,b in zip(loop, loop[1:]+loop[:1]):
        dx,dy = b[0]-a[0],b[1]-a[1]
        g = math.gcd(abs(dx),abs(dy))
        edges.append(DIRECTIONS.index((dx//g,dy//g)))
    data = {}
    for i,p in enumerate(loop):
        turn = (edges[i]-edges[i-1]+6)%12-6
        data[p] = 6-orientation*turn
        assert 0 < data[p] < 12
    for a,b in zip(loop,loop[1:]+loop[:1]):
        d = ref.sub(b,a)
        n = math.gcd(*map(abs,d))
        for j in range(1,n): data[ref.add(a,tuple(j*v//n for v in d))] = 6
    for x in range(min(p[0] for p in loop),max(p[0] for p in loop)+1):
        for y in range(min(p[1] for p in loop),max(p[1] for p in loop)+1):
            p = (x,y,-x-y)
            if ref.inside(p,loop): data[p] = 12
    return data


class Model:
    def __init__(self, name, marks=None):
        self.name = name
        self.vertices = SHAPES[name]
        self.lattice_data = point_data(self.vertices)
        self.base = {tuple(SCALE*x for x in p):v for p,v in self.lattice_data.items()}
        self.atoms = geo.atomize(tuple(p[:2] for p in self.vertices))
        self.base.update({(x,y,-x-y):12 for x,y in self.atoms})
        self.marks = marks or {}  # (prototype point, tensor index) -> integer
        self.orientations = tuple(tuple((ref.transform(p,g),v) for p,v in self.base.items())
                                  for g in ref.SYMMETRIES)
        self.cache = {}
        self.align_cache = {}
        self.dependencies = defaultdict(set)
        self.metrics = Counter()

    def placement(self, key):
        key = (int(key[0]),tuple(key[1]))
        if key not in self.cache:
            o,tr = key
            assert all(x%SCALE == 0 for x in tr) and sum(tr) == 0
            g = ref.SYMMETRIES[o]
            occupancy = tuple((ref.add(p,tr),v) for p,v in self.orientations[o])
            inverse_perm = tuple(g[1].index(i) for i in range(3))
            marks = []
            for (p,index),v in self.marks.items():
                q = ref.add(ref.transform(tuple(SCALE*x for x in p),g),tr)
                world_index = tuple(inverse_perm[i] for i in index)
                marks.append(((q,world_index),g[0]**len(index)*v))
            self.cache[key] = ref.Placement(key,occupancy,tuple(marks),
                tuple(ref.add(ref.transform(tuple(SCALE*x for x in p),g),tr) for p in self.vertices))
            for p,_ in occupancy+tuple(marks): self.dependencies[p].add(key)
        return self.cache[key]

    def alignments(self, p):
        if p not in self.align_cache:
            keys = []
            for o,entries in enumerate(self.orientations):
                for q,_ in entries:
                    tr = ref.sub(p,q)
                    if all(x%SCALE == 0 for x in tr):
                        key = (o,tr)
                        self.placement(key)
                        keys.append(key)
            self.align_cache[p] = tuple(keys)
        return self.align_cache[p]

    def rooted(self, second=None):
        state = ref.State()
        state.place(self.placement((0,(0,0,0))),seed=True)
        if second is not None: state.place(self.placement(second),seed=True)
        return state

    def pairs(self):
        s = self.rooted()
        keys = set()
        # A positive contribution at an already full point cannot be legal.
        for p in s.frontier(): keys.update(self.alignments(p))
        return sorted(k for k in keys if s.legal(self.placement(k)))

    def verify(self, keys, required=(), viable=False):
        """Independent transformed-polygon rasterization plus t/m replay."""
        totals = Counter()
        marks = {}
        atoms = set()
        seen = set()
        for o,tr in keys:
            key = (int(o),tuple(tr))
            assert key not in seen
            seen.add(key)
            g = ref.SYMMETRIES[o]
            loop = tuple(ref.add(ref.transform(p,g),tuple(x//SCALE for x in tr)) for p in self.vertices)
            raster = geo.atomize(tuple(p[:2] for p in loop))
            assert not atoms&raster, "polygon interiors overlap"
            atoms.update(raster)
            for p,v in self.lattice_data.items():
                q = ref.add(ref.transform(tuple(SCALE*x for x in p),g),tr)
                totals[q] += v
            for x,y in raster: totals[(x,y,-x-y)] += 12
            for (p,index),value in self.marks.items():
                q = ref.add(ref.transform(tuple(SCALE*x for x in p),g),tr)
                # Independent tensor-index evaluation by world-to-local action.
                w = tuple(g[1].index(i) for i in index)
                v = g[0]**len(index)*value
                assert (q,w) not in marks or marks[q,w] == v
                marks[q,w] = v
        assert all(v<=12 for v in totals.values())
        assert all(totals[p] == 12 for p in required)
        if viable:
            state = ref.State()
            for k in keys: state.place(self.placement(k))
            assert ref.Graph(self,state).decision(state)[0] != "dead"
        return {"tiles":len(seen),"atoms":len(atoms),"markValues":len(marks),"verified":True}


def relative(a,b):
    """Bring a to the identity; placement translations stay in scaled units."""
    oa,ta = a
    ob,tb = b
    ga,gb = ref.SYMMETRIES[oa],ref.SYMMETRIES[ob]
    inv = (ga[0],tuple(ga[1].index(i) for i in range(3)))
    g = ref.compose(inv,gb)
    return ref.SYMMETRIES.index(g),ref.inverse(ref.sub(tb,ta),ga)


def corona(model, second, node_limit=200, seconds=2):
    import time
    initial = model.rooted(second)
    required = set(initial.totals)
    started = time.monotonic()
    count = Counter()
    witness = None

    def visit(state,graph):
        nonlocal witness
        count['nodes'] += 1
        if count['nodes'] > node_limit or time.monotonic()-started > seconds: raise ref.Limit()
        kind,p,keys = graph.decision(state)
        if kind == 'dead': return {"dead":p}
        if all(state.totals.get(p,0)==12 for p in required):
            model.verify(state.order,required)
            witness = state.order
            return None
        count[kind] += 1
        children = []
        for key in keys:
            child,graph2 = state.copy(),graph.copy()
            graph2.update(model,child,child.place(model.placement(key)))
            result = visit(child,graph2)
            if witness is not None: return None
            children.append({'placement':key,'proof':result})
            count['backtracks'] += 1
        return {'kind':kind,'point':p,'children':children}

    proof = None
    try:
        proof = visit(initial,ref.Graph(model,initial))
        status = 'positive' if witness else 'negative'
    except ref.Limit:
        status = 'unresolved'
    return dict(second=second,status=status,witness=witness,proof=proof,stats=dict(count),seconds=time.monotonic()-started)


def grow(model, seed=19, target=24, nodes=2000, seconds=10):
    """DFS with exact snapshots and the reference scheduler; no learned teacher."""
    import random,time
    rng = random.Random(seed)
    started = time.monotonic()
    stats = Counter()
    best = model.rooted()
    found = None
    def visit(s,g):
        nonlocal best,found
        stats['nodes'] += 1
        if stats['nodes']>nodes or time.monotonic()-started>seconds: raise ref.Limit()
        kind,p,keys = g.decision(s)
        if kind == 'dead': return False
        if len(s.order)>len(best.order): best = s.copy()
        if len(s.order)>=target: found=s;return True
        if kind == 'empty': return False
        stats[kind] += 1
        rng.shuffle(keys)
        for key in keys:
            child,cg = s.copy(),g.copy()
            cg.update(model,child,child.place(model.placement(key)))
            if visit(child,cg): return True
            stats['backtracks'] += 1
        return False
    try:
        visit(best,ref.Graph(model,best))
        status = 'consistent_finite_patch' if found else 'exhausted_finite_growth_goal'
    except ref.Limit: status = 'unknown_budget'
    result = found or best
    model.verify(result.order,viable=True)
    graph=ref.Graph(model,result)
    return dict(seed=seed,status=status,placements=result.order,stats=dict(stats),seconds=time.monotonic()-started,
                frontierPoints=len(graph.domains),candidateNodes=len(graph.edges),
                incidences=sum(map(len,graph.domains.values())),metrics=dict(model.metrics))
