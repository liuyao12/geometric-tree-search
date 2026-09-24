"""Exact cell occupancy / full vertex-contact corona SAT experiment.

Specialized CDCL control, not the reference GCTS scheduler. Free lattice
orientations including reflections; no learned geometric restrictions.
"""
import collections, functools, itertools, time, threading
from pysat.card import CardEnc, EncType
from pysat.solvers import Glucose3


def normalize(cells):
    cells = tuple(cells)
    x, y = min(p[0] for p in cells), min(p[1] for p in cells)
    return tuple(sorted((a-x, b-y, s) for a,b,s in cells))


class Grid:
    def __init__(self, family):
        assert family in ('omino', 'hex', 'iamond')
        self.family = family
        self.types = (0,1) if family == 'iamond' else (0,)
        self.offsets = {}
        for s in self.types:
            origin = set(self.vertices((0,0,s)))
            self.offsets[s] = tuple((x,y,t) for x in range(-2,3) for y in range(-2,3)
                for t in self.types if origin & set(self.vertices((x,y,t))))
        self.edges = {s:tuple(p for p in self.offsets[s]
            if p != (0,0,s) and len(set(self.vertices((0,0,s))) & set(self.vertices(p))) == 2)
            for s in self.types}

    def vertices(self, p):
        x,y,s = p
        if self.family == 'omino':
            return ((x,y),(x+1,y),(x+1,y+1),(x,y+1))
        if self.family == 'hex':
            return tuple((3*x+a,3*y+b) for a,b in ((1,1),(-1,2),(-2,1),(-1,-1),(1,-2),(2,-1)))
        if s == 0:
            return ((x,y),(x+1,y),(x,y+1))
        return ((x+1,y),(x+1,y+1),(x,y+1))

    def from_source(self, cells):
        if self.family != 'iamond':
            return normalize((x,y,0) for x,y in cells)
        assert all(x%3 == y%3 and x%3 in (0,1) for x,y in cells)
        return normalize((x//3,y//3,x%3) for x,y in cells)

    @functools.lru_cache(maxsize=100000)
    def orientations(self, cells):
        answer = set()
        for flip in (False,True):
            for turns in range(4 if self.family == 'omino' else 6):
                transformed = []
                for p in cells:
                    points = self.vertices(p) if self.family == 'iamond' else (p[:2],)
                    out = []
                    for x,y in points:
                        if flip: x,y=y,x
                        for _ in range(turns):
                            x,y=(-y,x) if self.family == 'omino' else (-y,x+y)
                        out.append((x,y))
                    x,y = min(v[0] for v in out),min(v[1] for v in out)
                    s = int((x,y) not in out) if self.family == 'iamond' else 0
                    transformed.append((x,y,s))
                answer.add(normalize(transformed))
        return tuple(sorted(answer))

    def halo(self, cells):
        return {(x+a,y+b,t) for x,y,s in cells for a,b,t in self.offsets[s]}

    def holes(self, cells):
        cells=set(cells)
        lo=[min(p[a] for p in cells)-2 for a in (0,1)]
        hi=[max(p[a] for p in cells)+2 for a in (0,1)]
        empty={(x,y,s) for x in range(lo[0],hi[0]+1) for y in range(lo[1],hi[1]+1) for s in self.types}-cells
        seen={p for p in empty if p[0] in (lo[0],hi[0]) or p[1] in (lo[1],hi[1])}
        todo=list(seen)
        while todo:
            x,y,s=todo.pop()
            for a,b,t in self.edges[s]:
                p=(x+a,y+b,t)
                if p in empty and p not in seen:seen.add(p);todo.append(p)
        return empty-seen


def enumerate_free(grid, size):
    current={((0,0,0),)}
    counts=[]
    for n in range(1,size+1):
        counts.append(dict(size=n,all=len(current),holeFree=sum(not grid.holes(s) for s in current)))
        if n == size: break
        next_shapes=set()
        for cells in current:
            boundary={(x+a,y+b,t) for x,y,s in cells for a,b,t in grid.edges[s]}-set(cells)
            for q in boundary:
                next_shapes.add(grid.orientations(normalize((*cells,q)))[0])
        current=next_shapes
    return sorted(s for s in current if not grid.holes(s)),counts


def build(grid, shape, depth):
    """Layer-labelled tiles; coverage variables per cumulative layer.

    Every halo cell of a selected layer-j tile is covered by layer <= j+1.
    Nonoverlap forces any tile touching an inner tile into the next layer
    or earlier. Extra disconnected tiles are harmless and removed on replay.
    """
    assert depth >= 1
    orientations=grid.orientations(tuple(shape));root=frozenset(orientations[0])
    known={}; previous={root}; scanned=set()
    for level in range(1,depth+1):
        target=set().union(*(grid.halo(s) for s in previous))-root-scanned
        scanned.update(target);new=set()
        for qx,qy,qs in sorted(target):
            for oi,o in enumerate(orientations):
                for x,y,s in o:
                    if s != qs:continue
                    dx,dy=qx-x,qy-y;key=(oi,dx,dy)
                    if key in known:continue
                    cells=frozenset((a+dx,b+dy,t) for a,b,t in o)
                    if cells & root:continue
                    known[key]=(cells,level);new.add(cells)
        previous=new
    keys=sorted(known);tiles=[known[key][0] for key in keys]
    ids={};top=0;clauses=[];inc=collections.defaultdict(list)
    for i,cells in enumerate(tiles):
        for level in range(known[keys[i]][1],depth+1):
            top+=1;ids[i,level]=top
        for q in sorted(cells):inc[q].append(i)
    for q,indices in sorted(inc.items()):
        vs=[ids[i,j] for i in indices for j in range(1,depth+1) if (i,j) in ids]
        if len(vs)>1:
            enc=CardEnc.atmost(vs,1,top_id=top,encoding=EncType.seqcounter)
            top=enc.nv;clauses.extend(enc.clauses)
    coverage={}
    def covered(q,level):
        nonlocal top
        if (q,level) not in coverage:
            top+=1;coverage[q,level]=top
            vs=[ids[i,j] for i in inc.get(q,()) for j in range(1,level+1) if (i,j) in ids]
            # Only the implication from coverage to a selected placement is
            # needed: coverage variables occur positively only in obligations.
            clauses.append([-top]+vs)
        return coverage[q,level]
    for q in sorted(grid.halo(root)-root):clauses.append([covered(q,1)])
    for (i,j),var in ids.items():
        if j<depth:
            for q in sorted(grid.halo(tiles[i])-root-tiles[i]):
                clauses.append([-var,covered(q,j+1)])
    return dict(root=root,tiles=tiles,ids=ids,clauses=clauses,variables=top,keys=keys)


def verify(grid, shape, root, tiles, depth):
    """Geometric replay using incident vertices, without encoder halos."""
    root=tuple(map(tuple,root));tiles=[tuple(map(tuple,t)) for t in tiles]
    allowed=set(grid.orientations(tuple(shape)))
    occupied=set();by_vertex=collections.defaultdict(set)
    for i,tile in enumerate([root]+tiles):
        assert normalize(tile) in allowed
        assert not occupied & set(tile)
        occupied.update(tile)
        for p in tile:
            for v in grid.vertices(p):by_vertex[v].add(i)
    patch=[set(root)]+list(map(set,tiles));layer={0};used={0};layers=[[sorted(root)]]
    for _ in range(depth):
        vertices={v for i in layer for p in patch[i] for v in grid.vertices(p)}
        # Sum the exact number of cell sectors at each vertex: four squares,
        # three hexagons, or six triangles. No floating-point angles.
        count=collections.Counter(v for p in occupied for v in grid.vertices(p) if v in vertices)
        assert all(count[v]=={'omino':4,'hex':3,'iamond':6}[grid.family] for v in vertices)
        layer={i for v in vertices for i in by_vertex[v]}-used
        used.update(layer);layers.append([sorted(patch[i]) for i in sorted(layer)])
    trimmed=set().union(*(patch[i] for i in used))
    return dict(verified=True,layers=layers,layerCounts=list(map(len,layers)),holeFree=not grid.holes(trimmed))


def solve(grid,shape,depth,seconds=30,proof=False):
    start=time.perf_counter();data=build(grid,shape,depth);build_seconds=time.perf_counter()-start
    result=dict(depth=depth,buildSeconds=build_seconds,placements=len(data['tiles']),variables=data['variables'],clauses=len(data['clauses']))
    with Glucose3(bootstrap_with=data['clauses'],with_proof=proof) as solver:
        start=time.perf_counter();timer=threading.Timer(seconds,solver.interrupt);timer.start()
        try:status=solver.solve_limited(expect_interrupt=True)
        finally:timer.cancel();timer.join()
        result.update(status='SAT' if status is True else 'UNSAT' if status is False else 'unknown',solveSeconds=time.perf_counter()-start,stats=solver.accum_stats())
        if status is True:
            model=set(solver.get_model());selected=sorted({i for (i,j),v in data['ids'].items() if v in model})
            result['witness']=verify(grid,shape,data['root'],[data['tiles'][i] for i in selected],depth)
        if status is False and proof:
            result['_proof']='\n'.join(solver.get_proof())+'\n'
    result['_data']=data
    return result


def periodic(grid, shape, max_copies=2):
    """Search bounded HNF period lattices; return replayed exact certificates."""
    n=len(shape);types=len(grid.types);orientations=grid.orientations(tuple(shape))
    for copies in range(1,max_copies+1):
        if n*copies%types:continue
        area=n*copies//types
        for b in range(1,area+1):
            if area%b:continue
            a=area//b
            for shift in range(a):
                def residue(p):
                    x,y,s=p
                    return ((x-(y//b)*shift)%a,y%b,s)
                placements={}
                for o in orientations:
                    for dx in range(a):
                        for dy in range(b):
                            tile=tuple((x+dx,y+dy,s) for x,y,s in o)
                            key=tuple(sorted(map(residue,tile)))
                            if len(set(key))==n:placements.setdefault(key,tile)
                items=sorted(placements.items());by=collections.defaultdict(list)
                for i,(key,tile) in enumerate(items,1):
                    for p in key:by[p].append(i)
                if len(by)!=n*copies:continue
                clauses=[];top=len(items)
                for p,vs in sorted(by.items()):
                    enc=CardEnc.equals(vs,1,top_id=top,encoding=EncType.seqcounter)
                    top=enc.nv;clauses.extend(enc.clauses)
                with Glucose3(bootstrap_with=clauses) as solver:
                    # These small quotient queries are bounded by conflicts.
                    solver.conf_budget(1000);status=solver.solve_limited()
                    if status is not True:continue
                    model=set(solver.get_model());tiles=[items[i-1][1] for i in range(1,len(items)+1) if i in model]
                residues=[residue(p) for t in tiles for p in t]
                assert len(residues)==len(set(residues))==n*copies
                assert all(normalize(t) in orientations for t in tiles)
                return dict(verified=True,basis=[[a,0],[shift,b]],tiles=tiles,cellCount=n*copies)
    return None
