"""Cold own-level scalar markings from complete base extension certificates.

Only a searched cluster SHAPE is reused. Its base marking and own channel
start free. The labeling oracle always uses all unmarked base placements;
provisional values never enter that oracle. Selected aggregate placements
have disjoint base ownership. A negative has a complete base-search tree.
"""
import dataclasses,time
from collections import Counter
from turtle import Model,State,Graph,BASE,CAPACITY,SYMMETRIES,UnionFind,add,sub,transform,verify_patch,exhaustive_domains
from cluster_tiles import ClusterModel,ClusterState,make_type
from spatial import keys_tuple
from validate_halo import point_domain

def exact_point(p):return isinstance(p,tuple) and len(p)==3 and all(type(v) is int for v in p) and sum(p)==0

def exact_keys(keys):
    out=[]
    for o,tr in keys:
        tr=tuple(tr)
        if type(o) is not int or not 0<=o<12 or not exact_point(tr):raise ValueError('invalid base placement')
        out.append((o,tr))
    return tuple(out)

class IndependentOracle:
    """Literal base support alignments; cache values only, never domains.

    The separate replay cache contains neither Model placements nor Graph
    indexes. Every legality decision rechecks the current point totals.
    """
    def __init__(self):
        self.orientations=tuple(tuple((transform(p,g),v) for p,v in BASE.items()) for g in SYMMETRIES)
        self.values={}
    def domain(self,state,p):
        out=set()
        for o,entries in enumerate(self.orientations):
            for q,v in entries:
                tr=sub(p,q);key=o,tr
                if key in state.selected:continue
                if key not in self.values:self.values[key]=tuple((add(r,tr),w) for r,w in entries)
                values=self.values[key]
                if all(state.totals.get(r,0)+w<=CAPACITY for r,w in values) and (state.allowed_points is None or all(r in state.allowed_points for r,w in values)):
                    out.add(key)
        return out
    def domains(self,state):return {p:self.domain(state,p) for p in state.frontier()}

def seeded(model,keys):
    s=State()
    for k in keys:s.place(model.placement(k),seed=True)
    return s

def catalog(prototype):
    model=ClusterModel([prototype]);root=ClusterState();root.place(model.placement((prototype.identity,0,(0,0,0))),seed=True)
    aligned={(prototype.identity,o,sub(p,transform(q,g))) for p,v in prototype.occupancy for o,g in enumerate(SYMMETRIES) for q,w in prototype.occupancy}
    return [k for k in sorted(aligned) if root.legal(model.placement(k))]

def pair_expansion(model,second):
    first=model.placement((second[0],0,(0,0,0)));other=model.placement(second)
    if set(first.expansion)&set(other.expansion):raise ValueError('shared ownership is not a selected cluster pair')
    keys=tuple(sorted(first.expansion+other.expansion))
    if not verify_patch(model.base,keys):raise ValueError('capacity-illegal contact')
    return keys

def corona(base,keys,node_limit=500,seconds=3):
    """Reference base scheduler; initial support full, exposed frontier viable."""
    start=time.monotonic();initial=seeded(base,keys);required=set(initial.totals)
    nodes=branches=forced=backtracks=0;witness=None;tree=None
    class Budget(Exception):pass
    def visit(s,g):
        nonlocal nodes,branches,forced,backtracks,witness
        nodes+=1
        if nodes>node_limit or time.monotonic()-start>seconds:raise Budget()
        kind,p,options=g.decision(s)
        if kind=='dead':return {'dead':p}
        if all(s.totals.get(p,0)==CAPACITY for p in required):
            assert verify_patch(base,s.order,required);witness=s.copy();return None
        if kind=='empty':raise AssertionError('unsatisfied initial support vanished')
        if kind=='forced':forced+=1
        else:branches+=1
        children=[]
        for key in options:
            child=s.copy();cg=g.copy();cg.update(base,child,child.place(base.placement(key)))
            proof=visit(child,cg)
            if witness is not None:return None
            children.append({'placement':key,'proof':proof});backtracks+=1
        return {'kind':kind,'point':p,'children':children}
    try:
        tree=visit(initial,Graph(base,initial));status='positive' if witness else 'negative'
    except (Budget,RecursionError):status='unresolved'
    return {'status':status,'nodes':nodes,'branches':branches,'forced':forced,'backtracks':backtracks,
            'seconds':time.monotonic()-start,'witness':witness.order if witness else None,
            'tile_generations':witness.tile_generations if witness else None,'certificate':tree if status=='negative' else None,
            'required_points':len(required),'seed_expansion':keys,
            'scope':'fixed disjoint cluster constituents; all base placements; complete initial positive support and viable exposed frontier'}

def check_corona_failure(base,seeds,tree):
    if base.marking:raise ValueError('failure oracle must be unmarked')
    seeds=exact_keys(seeds);count=0;initial=seeded(base,seeds);required=set(initial.totals);oracle=IndependentOracle()
    def visit(s,node):
        nonlocal count
        count+=1
        if 'dead' in node:
            p=tuple(node['dead']);return exact_point(p) and p in s.frontier() and not oracle.domain(s,p)
        domains=oracle.domains(s)
        if not domains or any(not cs for cs in domains.values()) or all(s.totals.get(p,0)==CAPACITY for p in required):return False
        forced=sorted(p for p,cs in domains.items() if len(cs)==1)
        p=forced[0] if forced else min(domains,key=lambda p:(s.generations[p],len(domains[p]),p))
        if tuple(node['point'])!=p or node['kind']!=('forced' if forced else 'branch'):return False
        children=node['children'];keys=exact_keys([c['placement'] for c in children])
        if len(keys)!=len(set(keys)) or set(keys)!=domains[p]:return False
        for child,key in zip(children,keys):
            s2=s.copy();s2.place(base.placement(key))
            if not visit(s2,child['proof']):return False
        return True
    try:valid=visit(initial,tree)
    except (KeyError,TypeError,ValueError,IndexError,RecursionError):valid=False
    return valid,count

def check_corona_positive(base,seeds,keys):
    if base.marking:raise ValueError('positive oracle must be unmarked')
    try:seeds=exact_keys(seeds);keys=exact_keys(keys)
    except (TypeError,ValueError,IndexError):return False
    initial=seeded(base,seeds)
    if keys[:len(seeds)]!=seeds or not verify_patch(base,keys,set(initial.totals)):return False
    # Only existence and exposed viability are premises of the positive label.
    s=seeded(base,keys)
    oracle=IndependentOracle();return all(oracle.domain(s,p) for p in s.frontier())

class Encoder:
    """Online equality state, then sparse free entries; one scalar channel.

    Full provisional colors are arbitrary component IDs. Each positive merges
    every matching support overlap; negatives remain inequality alternatives.
    Unknown samples impose no constraints. Final sparsification retains one
    differing overlap per representable negative, with all other values free.
    """
    def __init__(self,prototype,radius=0):
        self.prototype=prototype;self.support=set(dict(prototype.occupancy))
        for p in list(self.support):
            for x in range(-radius,radius+1):
                for y in range(-radius,radius+1):
                    d=(x,y,-x-y)
                    if max(map(abs,d))<=radius:self.support.add(add(p,d))
        self.uf=UnionFind(self.support);self.samples=[];self.history=[];self.overlap_cache={}
    def overlaps(self,key):
        o,tr=key[1],key[2]
        if key not in self.overlap_cache:
            self.overlap_cache[key]=tuple((world,p) for p in sorted(self.support) if (world:=add(transform(p,SYMMETRIES[o]),tr)) in self.support)
        return self.overlap_cache[key]
    def add(self,sample):
        self.samples.append(sample)
        if sample['status']=='positive':
            for a,b in self.overlaps(sample['second']):self.uf.union(a,b)
        roots=sorted({self.uf.find(p) for p in self.support});colors={r:i for i,r in enumerate(roots)}
        negative=[s for s in self.samples if s['status']=='negative']
        counts=Counter(s['status'] for s in self.samples)
        self.history.append({'sample':len(self.samples)-1,'counts':dict(counts),'components':len(roots),
            'provisional_negative_rejected':sum(any(self.uf.find(a)!=self.uf.find(b) for a,b in self.overlaps(s['second'])) for s in negative),
            'values':[(p,colors[self.uf.find(p)]) for p in sorted(self.support)]})
    def finish(self):
        selected=set()
        for s in self.samples:
            if s['status']=='negative':
                for a,b in self.overlaps(s['second']):
                    if self.uf.find(a)!=self.uf.find(b):selected.update((a,b));break
        roots=sorted({self.uf.find(p) for p in selected});colors={r:i for i,r in enumerate(roots)}
        marking={p:colors[self.uf.find(p)] for p in selected}
        def accepts(s):return all(marking[a]==marking[b] for a,b in self.overlaps(s['second']) if a in marking and b in marking)
        counts=Counter(s['status'] for s in self.samples)
        return marking,{'support_points':len(self.support),'assigned':len(marking),'free':len(self.support)-len(marking),'colors':len(roots),
            'counts':dict(counts),'positive_accepted':sum(accepts(s) for s in self.samples if s['status']=='positive'),
            'negative_rejected':sum(not accepts(s) for s in self.samples if s['status']=='negative'),
            'unresolved_rejected':sum(not accepts(s) for s in self.samples if s['status']=='unresolved'),
            'history':self.history,'method':'online positive-equality unions; negative inequality alternatives; deterministic sparse witnesses',
            'status':'learned restriction until all possible disagreeing contacts have independent negative certificates'}

def decorated(prototype,marking):
    return make_type(Model(),prototype.identity,prototype.level,prototype.expansion,
                     inherited=prototype.marks,own_marking=marking,children=prototype.children)

def all_disagreements(prototype,marking):
    """All possible m overlaps, not just occupancy contact catalog lookups."""
    plain=ClusterModel([prototype]);marked=ClusterModel([decorated(prototype,marking)])
    a=ClusterState();a.place(plain.placement((prototype.identity,0,(0,0,0))),seed=True)
    b=ClusterState();b.place(marked.placement((prototype.identity,0,(0,0,0))),seed=True)
    candidates={(prototype.identity,o,sub(p,transform(q,g))) for p in marking for o,g in enumerate(SYMMETRIES) for q in marking}
    return {k for k in candidates if a.legal(plain.placement(k)) and not b.legal(marked.placement(k))}
