"""Amortized exact inventory construction for many boundaries in one envelope.

This is a representation optimization, not GCTS learning. The frozen universe
contains every legal aggregate placement with positive support inside P. A
request filters only immutable initial occupancy, marks and base ownership;
such rejected placements cannot revive below that request's root. Dynamic
domains, dependencies, scheduling, snapshots and verification remain exact.
Cold universe construction is reported separately and charged to the batch.
"""
import random,time
from collections import defaultdict
from turtle import Graph
from region_tiles import Boundary,RegionModel,features,verify_region,packed_state

class Universe:
    def __init__(self,types,allowed):
        if not allowed:raise ValueError('nonempty finite envelope required')
        start=time.monotonic();self.allowed=allowed;self.types=tuple(types)
        boundary=Boundary('resident-envelope',frozenset({min(allowed)}),allowed)
        self.model=RegionModel(types,boundary)
        self.keys=tuple(sorted({k for values in self.model.index.values() for k in values}))
        self.seconds=time.monotonic()-start
    def bind(self,boundary):return BoundModel(self,boundary)

class BoundModel(RegionModel):
    def __init__(self,universe,boundary):
        if boundary.allowed!=universe.allowed:raise ValueError('resident envelope mismatch')
        start=time.monotonic();initial=boundary.initial();shared=universe.model
        for name in ('types','base','version','orientations','cache'):setattr(self,name,getattr(shared,name))
        self.boundary=boundary;self.align_cache={};self.dependencies=defaultdict(set);self.index=defaultdict(set)
        from collections import Counter
        self.metrics=Counter();valid=0
        for key in universe.keys:
            c=self.placement(key)
            if not initial.legal(c):continue
            valid+=1
            for p,v in c.occupancy:self.index[p].add(key)
            for p,v in c.occupancy+c.marks:self.dependencies[p].add(key)
            for base_key in c.expansion:self.dependencies['base-inventory',base_key].add(key)
        self.admissible_placements=valid;self.compilation_seconds=time.monotonic()-start
        self.index={p:tuple(sorted(keys)) for p,keys in self.index.items()}
    def alignments(self,p):return self.index.get(p,())

def search(types,boundary,seed=0,node_limit=10000,seconds=5,policy=None,learn=False,rollout=False,universe=None):
    """Reference region search with a supplied exact model factory.

    Cold mode uses the unchanged RegionModel; resident mode changes initial
    inventory representation only. No sampler or policy contributes degrees.
    Atomic aggregate inventory is distinct from executing a base-tile macro.
    """
    start=time.monotonic()
    if universe is not None and tuple(types)!=universe.types:raise ValueError('resident tile/marking version mismatch')
    model=universe.bind(boundary) if universe else RegionModel(types,boundary)
    state=boundary.initial();graph=Graph(model,state);rng=random.Random(seed)
    nodes=branches=forced=backtracks=base_attempts=0;found=None;best=state.copy();traces=[];tree=None
    peak_points=len(graph.domains);peak_candidates=len(graph.edges);peak_incidences=sum(map(len,graph.domains.values()))
    class Budget(Exception):pass
    def visit(s,g):
        nonlocal nodes,branches,forced,backtracks,base_attempts,found,best,peak_points,peak_candidates,peak_incidences
        nodes+=1
        if nodes>node_limit or (seconds is not None and time.monotonic()-start>seconds):raise Budget()
        peak_points=max(peak_points,len(g.domains));peak_candidates=max(peak_candidates,len(g.edges));peak_incidences=max(peak_incidences,sum(map(len,g.domains.values())))
        if sum(s.totals.get(p,0)==12 for p in s.required)>sum(best.totals.get(p,0)==12 for p in best.required):best=s.copy()
        kind,p,keys=g.decision(s)
        if kind=='dead':return {'dead':p}
        if kind=='empty':
            if not verify_region(model,boundary,s,True):raise AssertionError('invalid completion')
            found=s.copy();return None
        if kind=='forced':forced+=1
        else:
            branches+=1;rng.shuffle(keys)
            if policy and learn:
                i,gradient=policy.select(rng,[features(model,s,g,k) for k in keys]);traces.append(gradient)
                keys=keys[i:i+1] if rollout else [keys[i]]+keys[:i]+keys[i+1:]
            elif policy:keys.sort(key=lambda k:sum(policy.weights[f]*v for f,v in features(model,s,g,k).items()),reverse=True)
            if rollout:keys=keys[:1]
        children=[]
        for key in keys:
            child=s.copy();cg=g.copy();c=model.placement(key);base_attempts+=len(c.expansion)
            cg.update(model,child,child.place(c));proof=visit(child,cg)
            if found:return None
            children.append({'placement':key,'proof':proof});backtracks+=1
        return {'kind':kind,'point':p,'children':children}
    try:
        tree=visit(state,graph);status='finite_exact_region' if found else 'dead_rollout' if rollout else 'exhausted_finite_region'
    except (Budget,RecursionError):status='unknown_budget';tree=None
    result=found or best
    if not verify_region(model,boundary,result,found is not None):raise AssertionError('invalid region state')
    coverage=sum(result.totals.get(p,0)==12 for p in result.required)/len(result.required)
    reward=coverage+(1 if found else -1)-.001*base_attempts-.001*nodes
    if policy and learn:policy.update(traces,reward)
    return {'status':status,'seed':seed,'nodes':nodes,'branches':branches,'forced':forced,'backtracks':backtracks,
            'seconds':time.monotonic()-start,'compilation_seconds':model.compilation_seconds,
            'inventory_mode':'resident' if universe else 'cold','admissible_placements':model.admissible_placements,
            'coverage_fraction':coverage,'required_points':len(boundary.required),'reward':reward,
            'certificate':tree if status=='exhausted_finite_region' else None,
            'peak_frontier_points':peak_points,'peak_candidate_nodes':peak_candidates,'peak_incidences':peak_incidences,
            'metrics':dict(model.metrics),'state':packed_state(result),'accepted_base_tiles':len(result.owned_base-set(boundary.owned)),
            'accepted_cluster_tiles':len(result.order),'attempted_base_placements':base_attempts,'verified':True,
            'budget':{'nodes':node_limit,'seconds':seconds,'construction_included':'per-request model/filter/graph included; resident universe cost is a separate one-time batch charge'}}
