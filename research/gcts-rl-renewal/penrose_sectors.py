"""Unmarked connected rhomb vertex-sector point model over Z[zeta_5].

Domain: Z[zeta_5] x {0,...,9}. Each occupied 36-degree sector has t=1.
Every placed vertex activates ALL ten sector obligations, including t=0.
These explicitly activated obligations are generation-zero roots. C10 acts
on coordinates and sector labels together; m, when present, is scalar.

No polygon predicate participates in legality. A complete developed rhomb
complex/plane equivalence is NOT established here. In particular finite point
support cannot test arbitrary geometric intersections in the dense module.
This is an explicitly declared connected-star model, not full-domain coverage
of every module point and not an arrow-marked Penrose tiling problem.
"""
import random,time
from collections import Counter,defaultdict
from dataclasses import dataclass
import cyclotomic as ring

ETA=ring.neg(ring.power(ring.ZETA,3))
DIRECTIONS=tuple(ring.power(ETA,i) for i in range(10))
KINDS=("thick","thin")
VERTICES={"thick":ring.RHOMBS["thick"]["vertices"],
          "thin":tuple(reversed(ring.RHOMBS["thin"]["vertices"]))}

def sub(a,b):return ring.add(a,ring.neg(b))
def rotate(a,r):return ring.mul(a,DIRECTIONS[r%10])
def point_action(p,r,tr):return ring.add(rotate(p[0],r),tr),(p[1]+r)%10

def prototype(vertices):
    out=set()
    for i,v in enumerate(vertices):
        following=DIRECTIONS.index(sub(vertices[(i+1)%4],v))
        preceding=DIRECTIONS.index(sub(vertices[i-1],v))
        width=(preceding-following)%10
        assert 0<width<5
        out.update((v,(following+j)%10) for j in range(width))
    assert len(out)==10
    return frozenset(out)

BASE={kind:prototype(vertices) for kind,vertices in VERTICES.items()}

def placement_key(key):
    kind,r,tr=key;tr=tuple(tr)
    if kind not in KINDS or type(r) is not int or not 0<=r<10:
        raise ValueError("undeclared tile kind/orientation")
    if len(tr)!=4 or any(type(v) is not int for v in tr):
        raise ValueError("exact four-integer translation required")
    return kind,r,tr

@dataclass(frozen=True)
class Placement:
    key:tuple
    positive:frozenset
    marks:tuple
    vertices:tuple
    active:frozenset

class Model:
    def __init__(self,markings=None):
        self.markings={kind:dict((markings or {}).get(kind,{})) for kind in KINDS}
        self.cache={};self.align_cache={};self.dependencies=defaultdict(set);self.metrics=Counter()
    def placement(self,key):
        key=placement_key(key);kind,r,tr=key
        if key not in self.cache:
            vertices=tuple(ring.add(rotate(v,r),tr) for v in VERTICES[kind])
            c=Placement(key,frozenset(point_action(p,r,tr) for p in BASE[kind]),
                        tuple(sorted((point_action(p,r,tr),v) for p,v in self.markings[kind].items())),
                        vertices,frozenset((v,s) for v in vertices for s in range(10)))
            self.cache[key]=c
            for p in c.positive|frozenset(p for p,v in c.marks):self.dependencies[p].add(key)
            self.metrics["placements_constructed"]+=1
        return self.cache[key]
    def alignments(self,p):
        p=(tuple(p[0]),p[1])
        if p not in self.align_cache:
            keys=set()
            for kind in KINDS:
                for r in range(10):
                    for q,s in BASE[kind]:
                        if (s+r)%10==p[1]:keys.add((kind,r,sub(p[0],rotate(q,r))))
            self.align_cache[p]=tuple(sorted(keys));self.metrics["alignment_points"]+=1
            for key in self.align_cache[p]:self.placement(key)
        return self.align_cache[p]

class State:
    def __init__(self):
        self.totals=set();self.marks={};self.active=set();self.roots={};self.generations={}
        self.selected=set();self.order=[];self.tile_generations=[]
    def copy(self):
        result=State()
        for name in ("totals","active","selected"):setattr(result,name,getattr(self,name).copy())
        for name in ("marks","roots","generations"):setattr(result,name,getattr(self,name).copy())
        result.order=self.order.copy();result.tile_generations=self.tile_generations.copy();return result
    def legal(self,c,metrics=None):
        reason=None
        if c.key in self.selected:reason="inventory"
        elif self.totals&c.positive:reason="capacity"
        elif any(p in self.marks and self.marks[p]!=v for p,v in c.marks):reason="marking"
        if metrics is not None:
            metrics["candidate_checks"]+=1
            if reason:metrics["rejected_"+reason]+=1
        return reason is None
    def place(self,c,seed=False):
        if not self.legal(c):raise ValueError("illegal point placement")
        incident=[self.generations[p] for p in c.positive if p in self.generations]
        generation=0 if seed or not incident else 1+min(incident)
        self.totals.update(c.positive);self.active.update(c.active);self.marks.update(c.marks)
        # Explicit zero-valued star obligations are roots, not incident tiles.
        for p in c.active:self.roots[p]=0;self.generations[p]=0
        self.selected.add(c.key);self.order.append(c.key);self.tile_generations.append(generation)
        return c.active|frozenset(p for p,v in c.marks)

class Graph:
    def __init__(self,model,state):
        self.model=model;self.domains={};self.edges={};self.update(state,state.active)
    def copy(self):
        result=object.__new__(Graph);result.model=self.model
        result.domains={p:cs.copy() for p,cs in self.domains.items()}
        result.edges={key:ps.copy() for key,ps in self.edges.items()};return result
    def remove(self,key):
        for p in self.edges.pop(key,set()):self.domains[p].discard(key)
    def add(self,key):
        ps=self.model.placement(key).positive.intersection(self.domains)
        if ps:
            self.edges.setdefault(key,set()).update(ps)
            for p in ps:self.domains[p].add(key)
    def update(self,state,changed):
        affected=set()
        for p in changed:affected.update(self.model.dependencies.get(p,()))
        for key in affected:
            if key in self.edges and not state.legal(self.model.placement(key),self.model.metrics):self.remove(key)
        for p in tuple(self.domains):
            if p in state.totals:
                for key in self.domains.pop(p):
                    self.edges[key].discard(p)
                    if not self.edges[key]:del self.edges[key]
        new=sorted(state.active-state.totals-set(self.domains))
        for p in new:self.domains[p]=set()
        for p in new:
            for key in self.model.alignments(p):
                if state.legal(self.model.placement(key),self.model.metrics):self.add(key)
        self.model.metrics["graph_updates"]+=1
    def decision(self,state,core=frozenset()):
        dead=sorted(p for p,cs in self.domains.items() if not cs)
        if dead:return "dead",dead[0],()
        forced=sorted(p for p,cs in self.domains.items() if len(cs)==1)
        if forced:p=forced[0];return "forced",p,tuple(self.domains[p])
        if not self.domains:return "empty",None,()
        p=min(self.domains,key=lambda p:(state.generations[p],p[0] not in core,len(self.domains[p]),p))
        return "branch",p,tuple(sorted(self.domains[p]))

def rooted(model,kind="thick",second=None):
    state=State();state.place(model.placement((kind,0,ring.ZERO)),seed=True)
    if second is not None:state.place(model.placement(second),seed=True)
    return state

def exhaustive_domains(model,state):
    """Independent alignment/legality, without caches or candidate graph."""
    domains={}
    for p in state.active-state.totals:
        domain=set()
        for kind in KINDS:
            for r in range(10):
                for q,s in BASE[kind]:
                    if (s+r)%10!=p[1]:continue
                    key=(kind,r,sub(p[0],rotate(q,r)))
                    if key in state.selected:continue
                    positive={point_action(a,r,key[2]) for a in BASE[kind]}
                    if state.totals&positive:continue
                    marks=[(point_action(a,r,key[2]),v) for a,v in model.markings[kind].items()]
                    if any(a in state.marks and state.marks[a]!=v for a,v in marks):continue
                    domain.add(key)
        domains[p]=domain
    return domains

def verify_patch(model,keys,required=()):
    try:
        seen=set();totals=set();marks={}
        for raw_key in keys:
            key=placement_key(raw_key);kind,r,tr=key
            if key in seen:return False
            seen.add(key);positive={point_action(p,r,tuple(tr)) for p in BASE[kind]}
            if totals&positive:return False
            totals.update(positive)
            for p,v in model.markings[kind].items():
                world=point_action(p,r,tuple(tr))
                if world in marks and marks[world]!=v:return False
                marks[world]=v
        return set(required)<=totals
    except (TypeError,ValueError,KeyError,IndexError):return False

def pair_catalog(model,kind):
    state=rooted(model,kind);keys=set()
    for p in state.active-state.totals:keys.update(model.alignments(p))
    return sorted(key for key in keys if state.legal(model.placement(key)))

class Limit(Exception):pass

def corona(model,kind="thick",second=None,seed=0,node_limit=1000,seconds=5):
    start=time.monotonic();initial=rooted(model,kind,second);core={p[0] for p in initial.active}
    required=initial.active.copy();nodes=branches=forced=backtracks=0;witness=None;best=initial
    rng=random.Random(seed)
    def visit(state,graph):
        nonlocal nodes,branches,forced,backtracks,witness,best
        nodes+=1
        if nodes>node_limit or time.monotonic()-start>seconds:raise Limit()
        mode,p,keys=graph.decision(state,core)
        if mode=="dead":return {"dead":p}
        if len(state.order)>len(best.order):best=state
        if required<=state.totals:witness=state;return None
        if mode=="empty":raise AssertionError("required zero point disappeared")
        if mode=="forced":forced+=1
        else:branches+=1
        choices=list(keys);rng.shuffle(choices);children=[]
        for key in choices:
            child=state.copy();g=graph.copy();g.update(child,child.place(model.placement(key)))
            proof=visit(child,g)
            if witness is not None:return None
            children.append({"placement":key,"proof":proof});backtracks+=1
        return {"kind":mode,"point":p,"children":children}
    proof=None
    try:
        proof=visit(initial,Graph(model,initial));status="positive" if witness else "negative"
    except (Limit,RecursionError):status="unresolved"
    final=witness or best
    assert verify_patch(model,final.order,required if witness else ())
    return {"root_kind":kind,"second":second,"seed":seed,"status":status,"nodes":nodes,"branches":branches,
            "forced":forced,"backtracks":backtracks,"seconds":time.monotonic()-start,"tiles":len(final.order),
            "placements":final.order,"tile_generations":final.tile_generations,"required_points":sorted(required),
            "frontier_points":len(final.active-final.totals),"certificate":proof,
            "scope":"all initial vertex-sector stars complete; exposed connected-star frontier viable; plane faithfulness open"}

def check_failure(model,kind,second,proof):
    count=0;initial=rooted(model,kind,second);required=initial.active.copy();core={p[0] for p in required}
    def check(state,node):
        nonlocal count
        count+=1;domains=exhaustive_domains(model,state)
        if "dead" in node:
            v,s=node["dead"];p=tuple(v),s
            return p in domains and not domains[p]
        if required<=state.totals or not domains or any(not cs for cs in domains.values()):return False
        forced=sorted(p for p,cs in domains.items() if len(cs)==1)
        p=forced[0] if forced else min(domains,key=lambda p:(state.generations[p],p[0] not in core,len(domains[p]),p))
        if (tuple(node["point"][0]),node["point"][1])!=p:return False
        if node["kind"]!=("forced" if forced else "branch"):return False
        children=node["children"];keys=[(c["placement"][0],c["placement"][1],tuple(c["placement"][2])) for c in children]
        if len(keys)!=len(set(keys)) or set(keys)!=domains[p]:return False
        for key,child in zip(keys,children):
            next_state=state.copy();next_state.place(model.placement(key))
            if not check(next_state,child["proof"]):return False
        return True
    try:return check(initial,proof),count
    except (ValueError,KeyError,TypeError,IndexError,RecursionError):return False,count

# The following exact polygon audit is NEVER called by Model/State/Graph/search.
def surd_sign(a,b):
    """Sign of a+b sqrt(5), with integer arithmetic."""
    if a==0:return (b>0)-(b<0)
    if b==0:return (a>0)-(a<0)
    if (a>0)==(b>0):return (a>0)-(a<0)
    delta=a*a-5*b*b
    return ((a>0)-(a<0))*((delta>0)-(delta<0))

def real_sign(p):
    a,b,c,d=p;return surd_sign(4*a-b-c-d,b-c-d)
def imag_sign(p):
    a,b,c,d=p;return surd_sign(2*c-2*d+b,b)
def cross_sign(u,v):return imag_sign(ring.mul(ring.conjugate(u),v))
def polygon(key):
    kind,r,tr=key;return tuple(ring.add(rotate(p,r),tuple(tr)) for p in VERTICES[kind])
def overlaps(a,b):
    """Strict positive-area intersection of convex CCW polygons (exact SAT)."""
    for first,other in ((a,b),(b,a)):
        for p,q in zip(first,first[1:]+first[:1]):
            if all(cross_sign(sub(q,p),sub(v,p))<=0 for v in other):return False
    return True
def geometry_audit(keys):
    polygons=[polygon(key) for key in keys]
    return [[i,j] for i,a in enumerate(polygons) for j in range(i+1,len(polygons)) if overlaps(a,polygons[j])]

def dense_support_obstruction():
    inverse=ring.add(ring.PHI,ring.neg(ring.ONE));support=set(VERTICES["thick"])
    differences={sub(a,b) for a in support for b in support}
    for k in range(1,41):
        delta=ring.power(inverse,k)
        if delta in differences:continue
        root=("thick",0,ring.ZERO);shifted=("thick",0,delta)
        if overlaps(polygon(root),polygon(shifted)):
            model=Model();state=rooted(model);assert state.legal(model.placement(shifted))
            return {"inverse_phi":inverse,"power":k,"translation":delta,"placements":[root,shifted],
                    "disjoint_vertex_support":True,"exact_positive_area_overlap":True,"point_capacity_legal":True,
                    "scope":"counterexample to unrestricted finite-vertex support equaling polygon non-overlap; disconnected placement control"}
    raise AssertionError("missing dense-support witness")
