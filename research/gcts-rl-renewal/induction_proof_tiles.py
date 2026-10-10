"""Complete point search with optional certified proof-resource markings.

The least dependency height in the finite rule hypergraph is a necessary
lower bound on a formula's logical slot. All original candidate types remain;
impossible early/unreachable outputs disagree with fixed mark-only zeros.
Disjoint backward formula cones additionally bound distinct ancestral cells.
No lemma path, learned policy, or previous certificate supplies either bound.
"""
import collections,time
import coarse_proof_tiles as M
import semantic_proof_tiles as S
from proof_clusters import digest
from turtle import Placement,Graph

def depth_point(slot):return (2*slot,3)
def support_point(slot):return (2*slot,4)

def supports(c):
    # Full backward dependency cones, including unreachable syntactic types.
    cones=[1<<i for i in range(len(c['formulas']))]
    while True:
        changed=False
        for r in c['rules']:
            value=cones[r['output']]
            for p in r['inputs']:value|=cones[p]
            if value!=cones[r['output']]:cones[r['output']]=value;changed=True
        if not changed:break
    disjoint=[all(not (cones[p]&cones[q]) for i,p in enumerate(r['inputs']) for q in r['inputs'][i+1:]) for r in c['rules']]
    bound=[None]*len(cones);rounds=[]
    while True:
        changes=[]
        for rid,r in enumerate(c['rules']):
            values=[bound[i] for i in r['inputs']]
            if any(v is None for v in values):continue
            size=1+(sum(values) if disjoint[rid] else max(values,default=0));j=r['output']
            if bound[j] is None or size<bound[j]:bound[j]=size;changes.append((j,size,rid))
        rounds.append(changes)
        if not changes:break
    return dict(cones=[hex(v) for v in cones],disjoint=disjoint,bound=bound,rounds=rounds,scope='Sound lower bound on distinct ancestral proof cells: add premise bounds only when their complete backward formula cones are pairwise disjoint; otherwise use their maximum. One cell for the current inference. All syntactic rules retained; no supplied proof path.')

def depths(c):
    rank=[None]*len(c['formulas']);rounds=[]
    while True:
        changes=[]
        for i,r in enumerate(c['rules']):
            values=[rank[p] for p in r['inputs']]
            if any(v is None for v in values):continue
            d=0 if not values else 1+max(values)
            j=r['output']
            if rank[j] is None or d<rank[j]:rank[j]=d;changes.append((j,d,i))
        rounds.append(changes)
        if not changes:break
    return dict(rank=rank,rounds=rounds,scope='least dependency height in the complete declared finite rule hypergraph, counting one compiled inference per logical cell; not primitive checker-line count')

class Model(M.Model):
    def __init__(self,c,length,certificate=None,support_certificate=None):
        super().__init__(c,length,1,())
        self.depth_certificate=certificate
        self.support_certificate=support_certificate
        if certificate is not None:
            rank=certificate['rank']
            if len(rank)!=len(c['formulas']):raise ValueError('depth language binding')
            for cid,old in list(self.cache.items()):
                key=self.descriptions[cid]['members'][0];slot,r,_=key
                level=rank[c['rules'][r]['output']]
                p=depth_point(slot);value=int(level is None or level>slot)
                self.cache[cid]=Placement(cid,old.occupancy,tuple(sorted(old.marks+((p,value),))),())
                self.dependencies[p].add(cid)
        if support_certificate is not None:
            bounds=support_certificate['bound']
            if len(bounds)!=len(c['formulas']):raise ValueError('support-bound language binding')
            for cid,old in list(self.cache.items()):
                key=self.descriptions[cid]['members'][0];slot,r,refs=key;rule=c['rules'][r]
                contacts=[(slot,rule['output'])]+list(zip(refs,rule['inputs']));marks={}
                for j,fid in contacts:
                    b=bounds[fid];p=support_point(j);v=int(b is None or b>j+1)
                    if p in marks and marks[p]!=v:raise ValueError('nonfunctional support mark')
                    marks[p]=v;self.dependencies[p].add(cid)
                self.cache[cid]=Placement(cid,old.occupancy,tuple(sorted(old.marks+tuple(marks.items()))),())
    def initial(self):
        s=super().initial()
        if self.depth_certificate is not None:s.marks.update({depth_point(i):0 for i in range(self.length)})
        if self.support_certificate is not None:s.marks.update({support_point(i):0 for i in range(self.length)})
        return s

def search(c,length,marked=False,support=False,seconds=15,attempt_limit=50000):
    if marked and support:raise ValueError('separate certified marking controls')
    began=time.perf_counter();certificate=depths(c) if marked else None;support_certificate=supports(c) if support else None
    marking_seconds=time.perf_counter()-began
    model=Model(c,length,certificate,support_certificate);build=time.perf_counter()-began
    s=model.initial();g=Graph(model,s);graph_seconds=time.perf_counter()-began-build
    stats=collections.Counter(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,tile_attempts=0)
    best=[];found=None;peaks=[len(g.domains),len(g.edges),sum(map(len,g.domains.values()))]
    def visit(state,graph):
        nonlocal best,found
        stats['nodes']+=1;node=dict(kind='cutoff',selected=list(state.order))
        if time.perf_counter()-began>seconds:node['cutoff']='wall_entry';return None,node
        kind,p,keys=graph.decision(state);node.update(kind=kind,point=p,graph_sha256=digest(graph.fingerprint()))
        peaks[1]=max(peaks[1],len(graph.edges));peaks[2]=max(peaks[2],sum(map(len,graph.domains.values())))
        if kind=='dead':return False,node
        if len(state.order)>len(best):best=list(state.order)
        if kind=='empty':found=list(state.order);return True,node
        stats['forced' if kind=='forced' else 'branches']+=1;node['children']=[]
        for cid in sorted(keys,key=model.ordering):
            if stats['base_attempts']>=attempt_limit:node['cutoff']='attempts_before_candidate';return None,node
            if time.perf_counter()-began>seconds:node['cutoff']='wall_before_candidate';return None,node
            stats['base_attempts']+=1;stats['tile_attempts']+=1
            child=state.copy();cg=graph.copy();cg.update(model,child,child.place(model.placement(cid)))
            ok,subtree=visit(child,cg);node['children'].append(dict(candidate=cid,tree=subtree))
            if ok is not False:return ok,node
            stats['backtracks']+=1
        return False,node
    ok,tree=visit(s,g);ids=found if found is not None else best;placements=model.expansion(ids)
    if not S.point_check(model.base,placements,ok is True):raise ValueError('invalid expansion to original unmarked point model')
    result=dict(status='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope',marked=marked or support,marking='depth' if marked else 'support' if support else 'none',depth_certificate=certificate,support_certificate=support_certificate,marking_seconds=marking_seconds,
        width=1,groups=model.groups,selected=ids,placements=placements,tile_generations=[1]*len(ids),search_tree=tree if ok is not None else None,partial_tree=tree if ok is None else None,
        build_seconds=build,graph_seconds=graph_seconds,seconds=time.perf_counter()-began,candidate_universe=len(model.cache),base_universe=len(model.base.cache),peak_frontier_points=peaks[0],peak_candidate_nodes=peaks[1],peak_incidences=peaks[2],
        metrics=dict(model.metrics),limits=dict(seconds=seconds,base_attempts=attempt_limit),index_instances=0,index_seconds=model.index_seconds,**stats)
    if ok:
        t=time.perf_counter();result['decoded']=S.decode(c,placements,length);result['decode_seconds']=time.perf_counter()-t;result['solution_transactions']=[]
    return result
