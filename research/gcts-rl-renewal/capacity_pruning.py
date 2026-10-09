"""Analytic residual-capacity pruning, separate from GCTS marking learning.

Any completed point's remaining capacity is a sum of future positive tile
contributions. The unbounded additive monoid of all declared contribution
values is a safe relaxation of those future placements. An unreachable deficit
therefore cannot occur in a completed point tiling. For finite region problems,
apply this constraint ONLY at declared required points. The coarse corona gate
below explicitly requires future completion of every activated positive point;
its failure scope is complete coarse point tilings, not a pure finite corona.
"""
import dataclasses,gc,hashlib,json,time
from collections import Counter
from pathlib import Path
from turtle import Graph,CAPACITY,SYMMETRIES,add
from cluster_tiles import ClusterState,ClusterModel,verify_state
from coarse_continuation import (parent_library,RootModel,LiteralOracle,root_state,
    exact_key,HERE,DOCS,exact_point)

def reachable(values,capacity=CAPACITY):
    if type(capacity) is not int or capacity<1 or any(type(v) is not int or not 0<v<=capacity for v in values):
        raise ValueError('exact positive integer contributions required')
    values=tuple(sorted(set(values)));out={0}
    for n in range(1,capacity+1):
        if any(n-v in out for v in values):out.add(n)
    return frozenset(out)

def inventory_values(definitions,active):
    by_name={t.identity:t for t in definitions}
    return tuple(sorted({v for n in active for p,v in by_name[n].occupancy}))

class CapacityState(ClusterState):
    def __init__(self,deficits,completion_points=None):
        super().__init__();self.deficits=frozenset(deficits)
        self.completion_points=None if completion_points is None else frozenset(completion_points)
    def copy(self):
        out=CapacityState(self.deficits,self.completion_points)
        for f in dataclasses.fields(ClusterState):
            v=getattr(self,f.name);setattr(out,f.name,v.copy() if isinstance(v,(dict,list,set)) else v)
        return out
    def residual_ok(self,c):
        return all(CAPACITY-self.totals.get(p,0)-v in self.deficits
                   for p,v in c.occupancy if self.completion_points is None or p in self.completion_points)
    def legal(self,c):return super().legal(c) and self.residual_ok(c)

class CapacityRootModel(RootModel):
    def root_legal(self,key):
        ok=super().root_legal(key)
        if ok:
            n,o,tr=key;r=self.root
            ok=all(CAPACITY-r.totals.get(add(p,tr),0)-v in r.deficits for p,v in self.scan[n][o])
            self.initial_legal[key]=ok
        return ok

class CapacityGraph(Graph):
    """Keep the same graph and scheduler; identify the analytic removal reason."""
    def copy(self):
        out=object.__new__(CapacityGraph);out.domains={p:cs.copy() for p,cs in self.domains.items()}
        out.edges={k:ps.copy() for k,ps in self.edges.items()};return out
    def update(self,model,state,changed):
        prior={k:ps.copy() for k,ps in self.edges.items()};super().update(model,state,changed)
        for key,points in prior.items():
            removed=points-self.edges.get(key,set())
            if not removed:continue
            c=model.placement(key)
            if ClusterState.legal(state,c) and not state.residual_ok(c):
                # The base Graph uses its generic fallback label for plug-ins.
                model.metrics['removed_incidences:completed_frontier']-=len(removed)
                model.metrics['removed_incidences:residual_capacity']+=len(removed)

def capacity_root(definitions,active,name):
    model=ClusterModel(definitions);s=CapacityState(reachable(inventory_values(definitions,active)))
    s.place(model.placement((name,0,(0,0,0))),seed=True);return s

def search(definitions,active,name,nodes=4000,seconds=15):
    start=time.monotonic();s=capacity_root(definitions,active,name);required=frozenset(s.totals)
    model=CapacityRootModel(definitions,active,s);g=CapacityGraph(model,s);construction=time.monotonic()-start
    count=branches=forced=backtracks=0;found=None;best=s.copy();tree=None
    class Budget(Exception):pass
    def visit(state,graph):
        nonlocal count,branches,forced,backtracks,found,best
        count+=1
        if count>nodes or time.monotonic()-start>seconds:raise Budget()
        if sum(state.totals.get(p,0)==12 for p in required)>sum(best.totals.get(p,0)==12 for p in required):best=state.copy()
        kind,p,keys=graph.decision(state)
        if kind=='dead':return {'dead':p}
        if all(state.totals.get(p,0)==12 for p in required):found=state.copy();return None
        if kind=='empty':raise AssertionError('missing initial support')
        if kind=='forced':forced+=1
        else:branches+=1
        children=[]
        for key in keys:
            child=state.copy();cg=graph.copy();cg.update(model,child,child.place(model.placement(key)))
            proof=visit(child,cg)
            if found is not None:return None
            children.append({'placement':key,'proof':proof});backtracks+=1
        return {'kind':kind,'point':p,'children':children}
    try:tree=visit(s,g);status='positive' if found is not None else 'negative'
    except (Budget,RecursionError):status='unresolved';tree=None
    result=found or best
    if not verify_state(model,result,required if found else ()):raise AssertionError('invalid coarse expansion')
    return {'root':name,'status':status,'nodes':count,'branches':branches,'forced':forced,'backtracks':backtracks,
        'seconds':time.monotonic()-start,'construction_seconds':construction,'required':sorted(required),
        'placements':result.order,'tile_generations':result.tile_generations,'base_expansion':sorted(result.owned_base),
        'covered':sum(result.totals.get(p,0)==12 for p in required),'certificate':tree if status=='negative' else None,
        'root_compiled_keys':len(model.initial_legal),'root_compatible_keys':sum(model.initial_legal.values()),
        'metrics':dict(model.metrics),'budget':{'nodes':nodes,'seconds':seconds,'construction_included':True},
        'contribution_values':inventory_values(definitions,active),'reachable_deficits':sorted(s.deficits),
        'scope':'unbounded coarse inventory with analytic necessary full-point residual constraint; finite witnesses remain finite'}

class CapacityOracle(LiteralOracle):
    """Independent direct values, without model or root-compilation decisions."""
    def __init__(self,definitions,active):
        super().__init__(definitions,active);self.deficits=reachable(inventory_values(definitions,active))
    def domain(self,s,p):
        out=set()
        for n in self.active:
            t=self.types[n]
            for o,entries in enumerate(self.orientations[n]):
                from turtle import sub,transform
                from spatial import moved
                g=SYMMETRIES[o]
                for q,v in entries:
                    tr=sub(p,q);key=n,o,tr
                    if key in s.selected:continue
                    # Compute literal values afresh. No enormous cache of
                    # illegal full footprints, and no RootModel callback.
                    if any((new:=s.totals.get(add(r,tr),0)+w)>12 or 12-new not in self.deficits for r,w in entries):continue
                    if s.owned_base.intersection(moved(t.expansion,g,tr)):continue
                    if any((r:=(add(transform(q,g),tr),ch)) in s.marks and s.marks[r]!=w for (q,ch),w in t.marks):continue
                    out.add(key)
        return out

def check_failure(definitions,active,name,tree):
    initial=root_state(definitions,name);required=set(initial.totals);oracle=CapacityOracle(definitions,active)
    model=ClusterModel(definitions);count=0
    def visit(s,node):
        nonlocal count
        count+=1
        if 'dead' in node:
            p=tuple(node['dead']);return exact_point(p) and p in s.frontier() and not oracle.domain(s,p)
        domains=oracle.domains(s)
        if not domains or any(not d for d in domains.values()) or all(s.totals.get(p,0)==12 for p in required):return False
        forced=sorted(p for p,d in domains.items() if len(d)==1)
        p=forced[0] if forced else min(domains,key=lambda p:(s.generations[p],len(domains[p]),p))
        if tuple(node['point'])!=p or node['kind']!=('forced' if forced else 'branch'):return False
        keys=[exact_key(c['placement'],active) for c in node['children']]
        if len(set(keys))!=len(keys) or set(keys)!=domains[p]:return False
        for c,key in zip(node['children'],keys):
            child=s.copy();child.place(model.placement(key))
            if not visit(child,c['proof']):return False
        return True
    try:ok=visit(initial,tree)
    except (KeyError,ValueError,TypeError,IndexError,RecursionError):ok=False
    return ok,count

def main():
    start=time.monotonic();path=DOCS/'multiscale-level1-001.json';stage=json.loads(path.read_text())
    children,parents,provenance=parent_library(stage);definitions=children+parents;active=tuple(t.identity for t in parents);results=[]
    sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('capacity_pruning.py','coarse_continuation.py')}
    for p in parents:
        r=search(definitions,active,p.identity);results.append(r)
        print(p.identity,r['status'],r['nodes'],'nodes',round(r['seconds'],3),'s',flush=True);gc.collect()
        if r['status']=='negative':
            t=time.monotonic();ok,n=check_failure(definitions,active,p.identity,r['certificate'])
            if not ok:raise AssertionError('independent capacity certificate rejected')
            r['independent_failure_audit']={'nodes':n,'seconds':time.monotonic()-t}
            print('audit',p.identity,n,'nodes',round(r['independent_failure_audit']['seconds'],3),'s',flush=True);gc.collect()
        output={'definitions':[dataclasses.asdict(t) for t in definitions],'active_types':active,'parent_provenance':provenance,
            'reuse':{'artifact':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':'prior positive contacts supply shapes only'},
            'source_sha256':sources,'results':results,'seconds':time.monotonic()-start,
            'counts':dict(Counter(r['status'] for r in results)),'complete_catalog':len(results)==len(parents),
            'scope':'analytic residual-capacity constraint, necessary for complete point tilings by this fixed parent library; not a learned GCTS marking'}
        (HERE/'results/capacity-continuation-checkpoint.json').write_text(json.dumps(output,separators=(',',':'))+'\n')
    print('capacity gate complete',dict(Counter(r['status'] for r in results)),round(time.monotonic()-start,3),'s',flush=True)

if __name__=='__main__':main()
