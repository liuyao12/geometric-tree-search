"""Exact coarse-only corona gate for searched parent libraries.

No finite support envelope, learned marking or base-singleton fallback is used
in this declared restricted inventory. Immutable-root compilation removes only
placements incompatible with the root, and preserves every candidate below it.
Failure therefore concerns the coarse library, never the original turtle.
"""
import dataclasses,gc,hashlib,json,time
from collections import Counter,defaultdict
from pathlib import Path
from turtle import Model,Graph,SYMMETRIES,CAPACITY,add,sub,transform,compose
from spatial import canonical,moved
from cluster_tiles import ClusterModel,ClusterState,compose_type,verify_state
from cluster_learning import exact_point
from run_multiscale_regions import initial_types,HERE,DOCS

def parent_library(stage):
    """Reuse prior positive contacts only as shape declarations, not witnesses."""
    children=initial_types()[1:];model=ClusterModel(children);by_shape=defaultdict(list)
    for i,s in enumerate(stage['samples']):
        if s['status']!='positive':continue
        a,b,o,tr=s['contact'];keys=((a,0,(0,0,0)),(b,o,tuple(tr)))
        t=compose_type(model,'candidate',keys);by_shape[canonical(t.expansion)].append((i,keys))
    parents=[];provenance=[]
    for j,shape in enumerate(sorted(by_shape)):
        i,keys=min(by_shape[shape]);t=compose_type(model,'candidate',keys)
        for g in SYMMETRIES:
            expansion=moved(t.expansion,g);origin=min(tr for o,tr in expansion)
            if tuple(sorted((o,sub(tr,origin)) for o,tr in expansion))==shape:break
        normalized=tuple((n,SYMMETRIES.index(compose(g,SYMMETRIES[o])),sub(transform(tr,g),origin)) for n,o,tr in keys)
        parent=compose_type(model,f'coarse-parent-{j:02}',normalized)
        if parent.expansion!=shape:raise AssertionError('normalization omitted a child transform')
        parents.append(parent);provenance.append({'type':parent.identity,'source_sample':i,
            'equivalent_positive_contacts':[k for k,_ in by_shape[shape]],'children':normalized,
            'normalization':[SYMMETRIES.index(g),tuple(-x for x in origin)]})
    return children,tuple(parents),provenance

class RootModel(ClusterModel):
    """Complete unbounded alignments, compiled against an immutable root only.

    Auxiliary child definitions validate expansions but are not search types.
    Rejected root-incompatible placements cannot revive below this fixed root.
    The rejection cache stores Boolean exact decisions, not full illegal values.
    All initial-legal candidate values/dependencies use the existing graph.
    """
    def __init__(self,definitions,active,root):
        super().__init__(definitions,version='coarse-root-v1')
        self.active=tuple(sorted(active));self.root=root.copy();self.initial_legal={}
        if not self.active or not set(self.active)<=self.types.keys():raise ValueError('invalid active inventory')
        if any(k[0] not in self.active for k in root.order) or root.allowed_points is not None:raise ValueError('unbounded active root required')
        # Constructor child-map checks intern auxiliary placements. These must
        # not leak into graph incidence through the reverse dependency index.
        self.cache={};self.dependencies=defaultdict(set);self.align_cache={}
        self.scan={n:tuple(tuple(sorted(entries,key=lambda pv:-pv[1])) for entries in self.orientations[n]) for n in self.active}
    def root_legal(self,key):
        if key not in self.initial_legal:
            n,o,tr=key;g=SYMMETRIES[o];t=self.types[n];r=self.root
            ok=(key not in r.selected and
                all(r.totals.get(add(p,tr),0)+v<=CAPACITY for p,v in self.scan[n][o]) and
                not r.owned_base.intersection(moved(t.expansion,g,tr)) and
                all((q:=(add(transform(p,g),tr),ch)) not in r.marks or r.marks[q]==v for (p,ch),v in t.marks))
            self.initial_legal[key]=ok
        return self.initial_legal[key]
    def alignments(self,p):
        if p not in self.align_cache:
            keys={(n,o,sub(p,q)) for n in self.active for o,entries in enumerate(self.orientations[n]) for q,v in entries}
            self.align_cache[p]=tuple(k for k in sorted(keys) if self.root_legal(k))
            for key in self.align_cache[p]:self.placement(key)
        return self.align_cache[p]

def root_state(definitions,name):
    model=ClusterModel(definitions);s=ClusterState();s.place(model.placement((name,0,(0,0,0))),seed=True);return s

def search(definitions,active,name,nodes=4000,seconds=15):
    start=time.monotonic();s=root_state(definitions,name);required=frozenset(s.totals)
    model=RootModel(definitions,active,s);graph=Graph(model,s);construction=time.monotonic()-start
    count=branches=forced=backtracks=0;found=None;best=s.copy()
    class Budget(Exception):pass
    def visit(state,g):
        nonlocal count,branches,forced,backtracks,found,best
        count+=1
        if count>nodes or time.monotonic()-start>seconds:raise Budget()
        if sum(state.totals.get(p,0)==12 for p in required)>sum(best.totals.get(p,0)==12 for p in required):best=state.copy()
        kind,p,keys=g.decision(state)
        if kind=='dead':return {'dead':p}
        if all(state.totals.get(p,0)==12 for p in required):found=state.copy();return None
        if kind=='empty':raise AssertionError('missing required root support')
        if kind=='forced':forced+=1
        else:branches+=1
        children=[]
        for key in keys:
            child=state.copy();cg=g.copy();cg.update(model,child,child.place(model.placement(key)))
            proof=visit(child,cg)
            if found is not None:return None
            children.append({'placement':key,'proof':proof});backtracks+=1
        return {'kind':kind,'point':p,'children':children}
    tree=None
    try:tree=visit(s,graph);status='positive' if found is not None else 'negative'
    except (Budget,RecursionError):status='unresolved';tree=None
    result=found or best
    if not verify_state(model,result,required if found is not None else ()):raise AssertionError('invalid flattened coarse state')
    return {'root':name,'status':status,'nodes':count,'branches':branches,'forced':forced,'backtracks':backtracks,
        'seconds':time.monotonic()-start,'construction_seconds':construction,'required':sorted(required),
        'placements':result.order,'tile_generations':result.tile_generations,'base_expansion':sorted(result.owned_base),
        'covered':sum(result.totals.get(p,0)==12 for p in required),'certificate':tree if status=='negative' else None,
        'root_compiled_keys':len(model.initial_legal),'root_compatible_keys':sum(model.initial_legal.values()),
        'budget':{'nodes':nodes,'seconds':seconds,'construction_included':True},
        'scope':'coarse-only unbounded positive-support corona with viable exposed frontier; restricted inventory'}

class LiteralOracle:
    """Independent full orientation/alignment scan, no compiled-root filters."""
    def __init__(self,definitions,active):
        self.types={t.identity:t for t in definitions};self.active=tuple(sorted(active));self.values={}
        self.orientations={n:tuple(tuple((transform(p,g),v) for p,v in self.types[n].occupancy) for g in SYMMETRIES) for n in self.active}
    def domain(self,s,p):
        out=set()
        for n in self.active:
            t=self.types[n]
            for o,entries in enumerate(self.orientations[n]):
                g=SYMMETRIES[o]
                for q,v in entries:
                    tr=sub(p,q);key=n,o,tr
                    if key in s.selected:continue
                    if key not in self.values:
                        self.values[key]=(tuple((add(r,tr),w) for r,w in entries),moved(t.expansion,g,tr),
                            tuple(((add(transform(r,g),tr),ch),w) for (r,ch),w in t.marks))
                    occ,exp,marks=self.values[key]
                    if (all(s.totals.get(r,0)+w<=12 for r,w in occ) and not s.owned_base.intersection(exp) and
                        all(r not in s.marks or s.marks[r]==w for r,w in marks)):out.add(key)
        return out
    def domains(self,s):return {p:self.domain(s,p) for p in s.frontier()}

def exact_key(k,active):
    n,o,tr=k;tr=tuple(tr)
    if n not in active or type(o) is not int or not 0<=o<12 or not exact_point(tr):raise ValueError('invalid coarse key')
    return n,o,tr

def check_failure(definitions,active,name,tree):
    initial=root_state(definitions,name);required=set(initial.totals);oracle=LiteralOracle(definitions,active);model=ClusterModel(definitions);count=0
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
    except (KeyError,TypeError,ValueError,IndexError,RecursionError):ok=False
    return ok,count

def main():
    start=time.monotonic();source_path=DOCS/'multiscale-level1-001.json';stage=json.loads(source_path.read_text())
    children,parents,provenance=parent_library(stage);definitions=children+parents;active=tuple(t.identity for t in parents);results=[]
    for p in parents:
        r=search(definitions,active,p.identity);results.append(r)
        print(p.identity,r['status'],r['nodes'],'nodes',round(r['seconds'],3),'s',flush=True);gc.collect()
        if r['status']=='negative':
            t=time.monotonic();ok,n=check_failure(definitions,active,p.identity,r['certificate'])
            if not ok:raise AssertionError('independent coarse failure rejected')
            r['independent_failure_audit']={'nodes':n,'seconds':time.monotonic()-t}
            print('audit',p.identity,n,'nodes',round(r['independent_failure_audit']['seconds'],3),'s',flush=True);gc.collect()
        # Save the checked growing checkpoint. Cutoffs never acquire trees.
        output={'definitions':[dataclasses.asdict(t) for t in definitions],'active_types':active,'parent_provenance':provenance,
            'reuse':{'artifact':source_path.name,'sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
                    'use':'all prior finite-positive contacts supply shapes only; no marking, policy or completion witness supplied to the coarse oracle'},
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results,
            'seconds':time.monotonic()-start,'counts':dict(Counter(r['status'] for r in results)),
            'complete_catalog':len(results)==len(parents),'scope':'fixed searched parent library only; no base turtle non-tiling or infinite continuation conclusion without verified final lifting'}
        (HERE/'results/coarse-continuation-checkpoint.json').write_text(json.dumps(output,separators=(',',':'))+'\n')
    print('joint gate complete',dict(Counter(r['status'] for r in results)),round(time.monotonic()-start,3),'s',flush=True)

if __name__=='__main__':main()
