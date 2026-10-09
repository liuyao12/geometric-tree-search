"""Fresh exact point-value turtle search. No supplied marking or substitution.

The only imported facts are the polygon vertices and integer angle units in
GCTS-I.html. Polygon membership authors point data; search sees only that data.
"""
from __future__ import annotations

import math
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import permutations

CAPACITY = 12
VERTICES = ((3,-2,-1),(2,0,-2),(0,1,-1),(0,2,-2),(-1,3,-2),
            (-2,2,0),(-1,0,1),(-2,0,2),(-2,-1,3),(0,-2,2),
            (1,-4,3),(2,-4,2),(3,-5,2),(4,-4,0))
ANGLES = (6,4,9,4,3,4,9,4,3,8,3,8,3,4)
SYMMETRIES = tuple((s,p) for s in (1,-1) for p in permutations(range(3)))

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def transform(p,g): return tuple(g[0]*p[i] for i in g[1])
def compose(g,h): return (g[0]*h[0],tuple(h[1][g[1][j]] for j in range(3)))
def inverse(p,g):
    out = [0,0,0]
    for j,i in enumerate(g[1]): out[i] = g[0]*p[j]
    return tuple(out)

def inside(p, polygon=VERTICES):
    """Strict point membership, rational ray test, no tolerance."""
    x,y = p[:2]
    result = False
    for a,b in zip(polygon, polygon[1:]+polygon[:1]):
        cross = (b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])
        if cross == 0 and min(a[0],b[0]) <= x <= max(a[0],b[0]) and min(a[1],b[1]) <= y <= max(a[1],b[1]):
            return False
        if (a[1]>y) != (b[1]>y):
            if x < a[0] + Fraction((y-a[1])*(b[0]-a[0]),b[1]-a[1]): result = not result
    return result

def point_data(vertices=VERTICES):
    data = dict(zip(vertices,ANGLES))
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        d = sub(b,a)
        n = math.gcd(math.gcd(abs(d[0]),abs(d[1])),abs(d[2]))
        for j in range(1,n): data[add(a,tuple(j*v//n for v in d))] = 6
    for x in range(min(p[0] for p in vertices),max(p[0] for p in vertices)+1):
        for y in range(min(p[1] for p in vertices),max(p[1] for p in vertices)+1):
            p = (x,y,-x-y)
            if inside(p,vertices): data[p] = 12
    return data

BASE = point_data()

@dataclass(frozen=True)
class Placement:
    key: tuple
    occupancy: tuple
    marks: tuple
    vertices: tuple

class Model:
    """Scalar prototype marking: pullback under all twelve lattice symmetries.

    Missing entries are free. Zero is assigned. The marking is frozen per run.
    Intern tables and complete alignment caches contain no learned search data.
    """
    def __init__(self, marking=None):
        self.marking = dict(marking or {})
        self.orientations = tuple(tuple((transform(p,g),v) for p,v in BASE.items()) for g in SYMMETRIES)
        self.cache = {}
        self.align_cache = {}
        self.dependencies = defaultdict(set)
        self.metrics = Counter()

    def placement(self, key):
        key = (int(key[0]),tuple(key[1]))
        if key not in self.cache:
            o,tr = key
            g = SYMMETRIES[o]
            occupancy = tuple((add(p,tr),v) for p,v in self.orientations[o])
            marks = tuple((add(transform(p,g),tr),v) for p,v in self.marking.items())
            self.cache[key] = Placement(key,occupancy,marks,tuple(add(transform(p,g),tr) for p in VERTICES))
            for p,_ in occupancy+marks: self.dependencies[p].add(key)
        return self.cache[key]

    def alignments(self,p):
        if p not in self.align_cache:
            keys = tuple((o,sub(p,q)) for o,entries in enumerate(self.orientations) for q,_ in entries)
            for key in keys: self.placement(key)
            self.align_cache[p] = keys
        return self.align_cache[p]

@dataclass
class State:
    totals: dict = field(default_factory=dict)
    marks: dict = field(default_factory=dict)
    generations: dict = field(default_factory=dict)
    roots: dict = field(default_factory=dict)
    selected: set = field(default_factory=set)
    order: list = field(default_factory=list)
    tile_generations: list = field(default_factory=list)
    allowed_points: frozenset | None = None

    def copy(self):
        return State(self.totals.copy(),self.marks.copy(),self.generations.copy(),self.roots.copy(),
                     self.selected.copy(),self.order.copy(),self.tile_generations.copy(),self.allowed_points)

    def legal(self,c):
        return (c.key not in self.selected
                and (self.allowed_points is None or all(p in self.allowed_points for p,_ in c.occupancy))
                and all(self.totals.get(p,0)+v <= CAPACITY for p,v in c.occupancy)
                and all(p not in self.marks or self.marks[p] == v for p,v in c.marks))

    def place(self,c,seed=False):
        if not self.legal(c): raise ValueError("illegal point-value placement")
        incident = [self.generations[p] for p,_ in c.occupancy if p in self.generations]
        gen = 0 if seed or not incident else 1+min(incident)
        for p,v in c.occupancy:
            self.totals[p] = self.totals.get(p,0)+v
            self.generations[p] = min(self.generations.get(p,gen),gen,self.roots.get(p,gen))
        for p,v in c.marks: self.marks[p] = v
        self.selected.add(c.key)
        self.order.append(c.key)
        self.tile_generations.append(gen)
        return {p for p,_ in c.occupancy+c.marks}

    def frontier(self):
        return {p for p in self.totals.keys() | self.roots.keys() if self.totals.get(p,0)<CAPACITY}

class Graph:
    """Complete shared incidence. Differential updates preserve unaffected domains.

    Snapshots copy all semantic state; the interned candidate universe is an
    append-only cache, independent of branch exclusions. No shortlist is used.
    """
    def __init__(self,model,state):
        self.domains = {}
        self.edges = {}
        self.update(model,state,set(state.totals) | set(state.roots) | set(state.marks))

    def copy(self):
        out = object.__new__(Graph)
        out.domains = {p:cs.copy() for p,cs in self.domains.items()}
        out.edges = {c:ps.copy() for c,ps in self.edges.items()}
        return out

    def update(self,model,state,changed):
        frontier = state.frontier()
        for p in self.domains.keys()-frontier:
            for key in self.domains[p]:
                self.edges[key].remove(p)
                if not self.edges[key]: del self.edges[key]
            del self.domains[p]
        fresh = frontier-self.domains.keys()
        candidates = set()
        for p in fresh:
            self.domains[p] = set()
            candidates.update(model.alignments(p))
        for p in changed: candidates.update(model.dependencies.get(p,()))
        for key in candidates:
            c = model.placement(key)
            model.metrics["candidate_tests"] += 1
            wanted = {p for p,_ in c.occupancy if p in frontier} if state.legal(c) else set()
            prior = self.edges.get(key,set())
            if prior-wanted:
                if key in state.selected: reason = "selected"
                elif any(state.totals.get(p,0)+v>12 for p,v in c.occupancy): reason = "capacity"
                elif any(p in state.marks and state.marks[p]!=v for p,v in c.marks): reason = "marking"
                else: reason = "completed_frontier"
                model.metrics["removed_incidences:"+reason] += len(prior-wanted)
            for p in prior-wanted: self.domains[p].remove(key)
            for p in wanted-prior: self.domains[p].add(key)
            if wanted: self.edges[key] = wanted
            elif key in self.edges: del self.edges[key]

    def decision(self,state):
        dead = sorted(p for p,cs in self.domains.items() if not cs)
        if dead: return "dead",dead[0],[]
        forced = sorted(p for p,cs in self.domains.items() if len(cs)==1)
        if forced:
            p = forced[0]
            return "forced",p,sorted(self.domains[p])
        if not self.domains: return "empty",None,[]
        p = min(self.domains,key=lambda p:(state.generations.get(p,state.roots.get(p,0)),len(self.domains[p]),p))
        return "branch",p,sorted(self.domains[p])

    def fingerprint(self):
        return (tuple(sorted((p,tuple(sorted(cs))) for p,cs in self.domains.items())),
                tuple(sorted((c,tuple(sorted(ps))) for c,ps in self.edges.items())))

def rooted(model,second=None):
    state = State()
    state.place(model.placement((0,(0,0,0))),seed=True)
    if second is not None: state.place(model.placement(second),seed=True)
    return state

def exhaustive_domains(model,state):
    """Independent enumeration without Graph's incremental indexes or align cache."""
    result = {}
    for p in state.frontier():
        result[p] = set()
        for o,g in enumerate(SYMMETRIES):
            for q in BASE:
                tr = sub(p,transform(q,g))
                key = (o,tr)
                occupancy = [(add(transform(r,g),tr),v) for r,v in BASE.items()]
                marks = [(add(transform(r,g),tr),v) for r,v in model.marking.items()]
                if (key not in state.selected and all(state.totals.get(r,0)+v<=12 for r,v in occupancy)
                    and (state.allowed_points is None or all(r in state.allowed_points for r,v in occupancy))
                    and all(r not in state.marks or state.marks[r]==v for r,v in marks)):
                    result[p].add(key)
    return result

def verify_patch(model,keys,required=()):
    """Replay t/m independently of State.place and Graph; exact integer comparisons."""
    totals = Counter()
    marks = {}
    seen = set()
    for o,tr in keys:
        key = (o,tuple(tr))
        if key in seen: return False
        seen.add(key)
        g = SYMMETRIES[o]
        for p,v in BASE.items(): totals[add(transform(p,g),tr)] += v
        for p,v in model.marking.items():
            q = add(transform(p,g),tr)
            if q in marks and marks[q]!=v: return False
            marks[q] = v
    return all(v<=12 for v in totals.values()) and all(totals[p]==12 for p in required)

def features(model,state,graph,key):
    c = model.placement(key)
    filled = sum(state.totals.get(p,0)+v==12 for p,v in c.occupancy)
    old = sum(p in state.totals for p,_ in c.occupancy)
    o,tr = key
    out = {"bias":1.,"fill":filled/28,"overlap":old/28,"new":(28-old)/28,
           "frontier":len(graph.domains)/100,"orientation:"+str(o):1.}
    # Translation features are generic residues, not a supplied geometric rule.
    for modulus in (2,3): out[f"residue:{modulus}:{tr[0]%modulus}:{tr[1]%modulus}"] = 1.
    return out

class Policy:
    """On-policy REINFORCE over validated continuation candidates.

    A rollout is a variable-length cluster proposal, with no predetermined
    shape, orientation, period, or substitution. Its expansion is saved.
    """
    def __init__(self):
        self.weights = defaultdict(float)
        self.baseline = 0.
        self.updates = 0
    def distribution(self,fs):
        scores = [sum(self.weights[k]*v for k,v in f.items()) for f in fs]
        top = max(scores)
        values = [math.exp(s-top) for s in scores]
        total = sum(values)
        return [v/total for v in values]
    def select(self,rng,fs):
        probabilities = self.distribution(fs)
        i = rng.choices(range(len(fs)),weights=probabilities)[0]
        expected = defaultdict(float)
        for p,f in zip(probabilities,fs):
            for k,v in f.items(): expected[k] += p*v
        gradient = {k:fs[i].get(k,0)-expected.get(k,0) for k in fs[i].keys()|expected.keys()}
        return i,gradient
    def update(self,traces,reward):
        advantage = reward-self.baseline
        self.baseline = .9*self.baseline+.1*reward
        for g in traces:
            for k,v in g.items(): self.weights[k] += .03*advantage*v/max(1,len(traces))
        self.updates += 1

def rollout(model,seed,target=24,policy=None,learn=False):
    start = time.monotonic()
    rng = random.Random(seed)
    state = rooted(model)
    graph = Graph(model,state)
    traces = []
    branches = forced = 0
    status = "unknown"
    decisions = []
    while True:
        kind,p,keys = graph.decision(state)
        if kind=="dead":
            status = "dead_prefix"
            break
        if kind=="empty":
            status = "local_frontier_empty"
            break
        # Stop only after ruling out every known dead point.
        if len(state.order)>=target:
            status = "consistent_finite_patch"
            break
        if kind=="forced":
            key = keys[0]
            forced += 1
        else:
            fs = [features(model,state,graph,key) for key in keys]
            if policy:
                i,gradient = policy.select(rng,fs)
                traces.append(gradient)
            else: i = rng.randrange(len(keys))
            key = keys[i]
            branches += 1
        decisions.append({"kind":kind,"point":p,"degree":len(keys),"placement":key})
        changed = state.place(model.placement(key))
        graph.update(model,state,changed)
    full = sum(v==12 for v in state.totals.values())
    # Reward is measured in base placements/satisfied obligations; macros earn no bonus.
    reward = (len(state.order)-1)/target + full/(28*target) - .5*(kind=="dead")
    if policy and learn: policy.update(traces,reward)
    assert verify_patch(model,state.order)
    return {"seed":seed,"tiles":len(state.order),"satisfied_points":full,"branches":branches,
            "forced":forced,"backtracks":0,"status":status,"reward":reward,
            "seconds":time.monotonic()-start,"placements":state.order,
            "tile_generations":state.tile_generations,"decisions":decisions,
            "frontier_points":len(graph.domains),"candidate_nodes":len(graph.edges),
            "incidences":sum(map(len,graph.domains.values())),"verified":True}

class Limit(Exception): pass

def sequence_actions(model,state,graph,keys,library,remaining):
    actions = [(key,) for key in keys]
    for key in keys:
        for motif in library:
            seq = motif["expansion"]
            if seq[0][0]!=key[0] or len(seq)>remaining: continue
            tr = sub(key[1],seq[0][1])
            expanded = tuple((o,add(q,tr)) for o,q in seq)
            model.metrics["cluster_validation_attempts"] += 1
            trial = state.copy()
            try:
                for k in expanded: trial.place(model.placement(k))
            except ValueError: continue
            if verify_patch(model,trial.order): actions.append(expanded)
    return actions

def action_features(model,state,graph,seq):
    f = features(model,state,graph,seq[0])
    f["sequence_length"] = len(seq)/5
    f["sequence:"+str(tuple(o for o,_ in seq))] = 1.
    return f

def growth_search(model,seed,target=24,node_limit=600,seconds=10,policy=None,library=(),second=None):
    """Complete DFS with bounded execution; policy changes branch order only."""
    start = time.monotonic()
    rng = random.Random(seed)
    nodes = branches = forced = backtracks = 0
    best = rooted(model,second)
    found = None
    def visit(state,graph):
        nonlocal nodes,branches,forced,backtracks,best,found
        nodes += 1
        if nodes>node_limit or time.monotonic()-start>seconds: raise Limit()
        kind,p,keys = graph.decision(state)
        if kind=="dead": return False
        if len(state.order)>len(best.order): best = state.copy()
        if len(state.order)>=target:
            found = state
            return True
        if kind=="empty": return False
        if kind=="forced":
            forced += 1
            actions = [(keys[0],)]
        else:
            branches += 1
            actions = sequence_actions(model,state,graph,keys,library,target-len(state.order))
            rng.shuffle(actions)
            if policy:
                actions.sort(key=lambda seq:sum(policy.weights[q]*v for q,v in action_features(model,state,graph,seq).items()),reverse=True)
        for seq in actions:
            child,child_graph = state.copy(),graph.copy()
            executed = 0
            for key in seq:
                step_kind,_,step_keys = child_graph.decision(child)
                if step_kind in ("dead","empty") or key not in step_keys: break
                if executed and step_kind=="forced": forced += 1
                child_graph.update(model,child,child.place(model.placement(key)))
                executed += 1
            if not executed: continue
            model.metrics["cluster_extra_moves"] += max(0,executed-1)
            if visit(child,child_graph): return True
            backtracks += 1
        return False
    try:
        visit(best,Graph(model,best))
        status = "consistent_finite_patch" if found else "exhausted_growth_goal"
    except Limit: status = "unknown_budget"
    result = found or best
    assert verify_patch(model,result.order)
    graph = Graph(model,result)
    assert graph.decision(result)[0]!="dead"
    return {"seed":seed,"tiles":len(result.order),"nodes":nodes,"branches":branches,
            "forced":forced,"backtracks":backtracks,"status":status,
            "seconds":time.monotonic()-start,"placements":result.order,
            "tile_generations":result.tile_generations,"verified":True,
            "frontier_points":len(graph.domains),"candidate_nodes":len(graph.edges),
            "incidences":sum(map(len,graph.domains.values()))}

def mine_clusters(model,episodes,max_length=5):
    """Inspectably expanded sequences, translation-normalized; no supplied motifs."""
    counts = Counter()
    for episode in episodes:
        if episode["status"]!="consistent_finite_patch": continue
        order = [(o,tuple(tr)) for o,tr in episode["placements"]]
        for size in range(2,max_length+1):
            for start in range(1,len(order)-size+1):
                seq = order[start:start+size]
                origin = seq[0][1]
                normalized = tuple((o,sub(tr,origin)) for o,tr in seq)
                if verify_patch(model,normalized): counts[normalized] += 1
    return [{"id":i,"count":count,"expansion":seq} for i,(seq,count) in enumerate(counts.most_common(80))]

def cluster_rollout(model,seed,library,target=24,policy=None,learn=False):
    """RL chooses sequence proposals; execution rechecks every scheduler step.

    Every legal base candidate is retained as a singleton fallback. A cluster
    interrupted by a global forced move is closed and proposals are regenerated.
    Only full independently verified expansions become available as proposals.
    """
    start = time.monotonic()
    rng = random.Random(seed)
    state = rooted(model)
    graph = Graph(model,state)
    traces = []
    branches = forced = proposals = validations = consumed = 0
    expansions = []
    while True:
        kind,p,keys = graph.decision(state)
        if kind=="dead": status = "dead_prefix"; break
        if kind=="empty": status = "local_frontier_empty"; break
        if len(state.order)>=target: status = "consistent_finite_patch"; break
        if kind=="forced":
            graph.update(model,state,state.place(model.placement(keys[0])))
            forced += 1
            continue
        # Finite sequence pool does not alter the graph or the base domains.
        before_validations = model.metrics["cluster_validation_attempts"]
        actions = sequence_actions(model,state,graph,keys,library,target-len(state.order))
        validations += model.metrics["cluster_validation_attempts"]-before_validations
        fs = [action_features(model,state,graph,seq) for seq in actions]
        proposals += len(actions)
        if policy:
            i,gradient = policy.select(rng,fs)
            traces.append(gradient)
        else: i = rng.randrange(len(actions))
        seq = actions[i]
        branches += 1
        executed = []
        for key in seq:
            step_kind,step_p,step_keys = graph.decision(state)
            if step_kind!="branch" or key not in step_keys: break
            graph.update(model,state,state.place(model.placement(key)))
            executed.append(key)
        consumed += max(0,len(executed)-1)
        expansions.append({"proposed":seq,"executed":executed})
    full = sum(v==12 for v in state.totals.values())
    reward = (len(state.order)-1)/target + full/(28*target) - .5*(kind=="dead")
    if policy and learn: policy.update(traces,reward)
    assert verify_patch(model,state.order)
    return {"seed":seed,"tiles":len(state.order),"status":status,"branches":branches,"forced":forced,
            "backtracks":0,"seconds":time.monotonic()-start,"reward":reward,"placements":state.order,
            "proposals":proposals,"validation_attempts":validations,"sequence_extra_moves":consumed,
            "sequence_expansions":expansions,"verified":True}

def one_corona(model,second,node_limit=100,seconds=3):
    start = time.monotonic()
    initial = rooted(model,second)
    target = set(initial.totals)
    nodes = branches = forced = backtracks = 0
    witness = None
    certificate = None

    def visit(state,graph):
        nonlocal nodes,branches,forced,backtracks,witness
        nodes += 1
        if nodes>node_limit or time.monotonic()-start>seconds: raise Limit()
        kind,p,keys = graph.decision(state)
        if kind=="dead": return {"dead":p}
        if all(state.totals.get(p,0)==12 for p in target):
            assert verify_patch(model,state.order,target)
            witness = state.order
            return None
        if kind=="empty": raise AssertionError("unsatisfied target vanished")
        if kind=="forced": forced += 1
        else: branches += 1
        children = []
        for key in keys:
            child = state.copy()
            child_graph = graph.copy()
            changed = child.place(model.placement(key))
            child_graph.update(model,child,changed)
            result = visit(child,child_graph)
            if witness is not None: return None
            children.append({"placement":key,"proof":result})
            backtracks += 1
        return {"kind":kind,"point":p,"children":children}

    try:
        certificate = visit(initial,Graph(model,initial))
        status = "positive" if witness else "negative"
    except Limit: status = "unresolved"
    return {"second":second,"status":status,"nodes":nodes,"branches":branches,
            "forced":forced,"backtracks":backtracks,"seconds":time.monotonic()-start,
            "witness":witness,"certificate":certificate,
            "scope":"all initially occupied points complete; entire exposed frontier viable"}

def pair_catalog(model):
    state = rooted(model)
    keys = set()
    for p in state.totals: keys.update(model.alignments(p))
    return sorted(key for key in keys if state.legal(model.placement(key)))

def check_failure_certificate(model,second,proof):
    """Independent full-domain re-enumeration at every proof node."""
    count = 0
    target = set(rooted(model,second).totals)
    def check(state,node):
        nonlocal count
        count += 1
        domains = exhaustive_domains(model,state)
        if "dead" in node:
            p = tuple(node["dead"])
            return p in domains and not domains[p]
        if all(state.totals.get(p,0)==12 for p in target): return False
        dead = [p for p,cs in domains.items() if not cs]
        if dead: return False
        forced = sorted(p for p,cs in domains.items() if len(cs)==1)
        p = forced[0] if forced else min(domains,key=lambda p:(state.generations[p],len(domains[p]),p))
        if tuple(node["point"])!=p: return False
        if node["kind"]!=("forced" if forced else "branch"): return False
        children = node["children"]
        keys = [(int(c["placement"][0]),tuple(c["placement"][1])) for c in children]
        if len(keys)!=len(set(keys)) or set(keys)!=domains[p]: return False
        for child,key in zip(children,keys):
            state2 = state.copy()
            state2.place(model.placement(key))
            if not check(state2,child["proof"]): return False
        return True
    return check(rooted(model,second),proof),count

class UnionFind:
    def __init__(self,points): self.parent = {p:p for p in points}
    def find(self,p):
        while self.parent[p]!=p:
            self.parent[p] = self.parent[self.parent[p]]
            p = self.parent[p]
        return p
    def union(self,p,q):
        a,b = self.find(p),self.find(q)
        self.parent[max(a,b)] = min(a,b)

def verify_redundancy_scope(marking,samples):
    """Check every transformed catalog contact and scalar equivariance.

    Combined with checked negative proof trees this certifies the finite premises
    of the report's redundancy lemma. It does not prove a tiling exists.
    """
    assert set(marking)<=set(BASE)
    assert all(s["status"] in ("positive","negative") for s in samples)
    model = Model(marking)
    negative = {s["second"] for s in samples if s["status"]=="negative"}
    rejected = set()
    root = rooted(model)
    for s in samples:
        if not root.legal(model.placement(s["second"])):
            assert s["second"] in negative
            rejected.add(s["second"])
    checked = 0
    for i,g in enumerate(SYMMETRIES):
        state = State()
        state.place(model.placement((i,(0,0,0))),seed=True)
        for s in samples:
            o,tr = s["second"]
            key = (SYMMETRIES.index(compose(g,SYMMETRIES[o])),transform(tr,g))
            assert (not state.legal(model.placement(key))) == (s["second"] in rejected)
            checked += 1
    return {"transformed_contact_checks":checked,"canonical_rejected_pairs":len(rejected),
            "occupancy_supported":True,"scalar_equivariance_checked":True,
            "conditional_lemma":"all complete unmarked point-model tilings satisfy this marking"}

def synthesize(samples,radius=1):
    """Cold scalar equality encoder; all resolved labels used, unknown labels ignored.

    This deliberately small hypothesis class can fail. It never feeds its own
    provisional marking into the unmarked label oracle. Returned assignments
    are ephemeral, and are not persisted as a reusable learned model.
    """
    support = set(BASE)
    for p in list(BASE):
        for x in range(-radius,radius+1):
            for y in range(-radius,radius+1):
                d = (x,y,-x-y)
                if max(map(abs,d))<=radius: support.add(add(p,d))
    uf = UnionFind(support)
    def overlaps(key):
        o,tr = key
        return [(world,local) for local in sorted(support)
                if (world:=add(transform(local,SYMMETRIES[o]),tr)) in support]
    history = []
    for i,s in enumerate(samples):
        if s["status"]=="positive":
            for a,b in overlaps(s["second"]): uf.union(a,b)
        if s["status"]!="unresolved":
            negative = [q for q in samples[:i+1] if q["status"]=="negative"]
            rejected = sum(any(uf.find(a)!=uf.find(b) for a,b in overlaps(q["second"])) for q in negative)
            history.append({"resolved":sum(q["status"]!="unresolved" for q in samples[:i+1]),
                            "components":len({uf.find(p) for p in support}),
                            "negatives":len(negative),"rejected":rejected})
    # Sparsify by retaining one differing overlap for each representable negative.
    selected = set()
    for s in samples:
        if s["status"]=="negative":
            for a,b in overlaps(s["second"]):
                if uf.find(a)!=uf.find(b):
                    selected.update((a,b))
                    break
    roots = sorted({uf.find(p) for p in selected})
    colors = {p:i for i,p in enumerate(roots)}
    marking = {p:colors[uf.find(p)] for p in selected}
    def accepted(key):
        return all(marking[a]==marking[b] for a,b in overlaps(key) if a in marking and b in marking)
    positives = [s for s in samples if s["status"]=="positive"]
    negatives = [s for s in samples if s["status"]=="negative"]
    return marking,{"support_points":len(support),"assigned":len(marking),"free":len(support)-len(marking),
                    "components":len({uf.find(p) for p in support}),"colors":len(roots),
                    "positives":len(positives),"positive_accepted":sum(accepted(s["second"]) for s in positives),
                    "negatives":len(negatives),"negative_rejected":sum(not accepted(s["second"]) for s in negatives),
                    "history":history,"class":"scalar pullback marking with free entries; sample restriction"}
