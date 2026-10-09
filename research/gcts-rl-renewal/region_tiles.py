"""Finite point boundary problems and first-class cluster search.

The required set, admissible support envelope and fixed exterior are explicit.
Only required points become obligations. Complete frozen-boundary compilation
is an exact inventory optimization, not a learned GCTS marking. Atomic search
uses the declared aggregate inventory; all singleton types remain available.
"""
import random,time
from collections import Counter,defaultdict
from dataclasses import dataclass,field,fields
from turtle import CAPACITY,SYMMETRIES,Graph,Policy,sub
from cluster_tiles import ClusterModel,ClusterState
from spatial import keys_tuple

def point(p):
    return isinstance(p,tuple) and len(p)==3 and all(type(x) is int for x in p) and sum(p)==0

@dataclass(frozen=True)
class Boundary:
    identity:str
    required:frozenset
    allowed:frozenset
    exterior:tuple=()
    marks:tuple=()
    owned:tuple=()

    def __post_init__(self):
        if not isinstance(self.required,frozenset) or not isinstance(self.allowed,frozenset):raise ValueError('immutable finite point sets required')
        if not isinstance(self.identity,str) or not self.identity or not self.required or not self.required<=self.allowed:
            raise ValueError('nonempty named required set inside finite allowed envelope required')
        if any(not point(p) for p in self.required|self.allowed):raise ValueError('exact lattice points required')
        if len(dict(self.exterior))!=len(self.exterior) or any(not point(p) or type(v) is not int or not 0<=v<=CAPACITY for p,v in self.exterior):
            raise ValueError('invalid exterior occupancy')
        if len(dict(self.marks))!=len(self.marks) or any(not point(p) or not isinstance(ch,str) or type(v) is not int for (p,ch),v in self.marks):
            raise ValueError('invalid exterior marking components')
        if len(set(self.owned))!=len(self.owned) or any(type(o) is not int or not 0<=o<12 or not point(tr) for o,tr in self.owned):
            raise ValueError('invalid fixed exterior ownership')

    def initial(self):
        state=RegionState(totals=dict(self.exterior),marks=dict(self.marks),
            generations={p:0 for p,v in self.exterior},roots={p:0 for p in self.required},
            allowed_points=self.allowed,owned_base=set(self.owned),required=self.required)
        state.generations.update(state.roots)
        return state

    def packed(self):
        return {'identity':self.identity,'required':sorted(self.required),'allowed':sorted(self.allowed),
                'exterior':self.exterior,'marks':self.marks,'owned':self.owned}

    @classmethod
    def unpack(cls,d):
        return cls(d['identity'],frozenset(tuple(p) for p in d['required']),frozenset(tuple(p) for p in d['allowed']),
                   tuple((tuple(p),v) for p,v in d['exterior']),
                   tuple(((tuple(p),ch),v) for (p,ch),v in d['marks']),tuple((o,tuple(tr)) for o,tr in d['owned']))

@dataclass
class RegionState(ClusterState):
    required:frozenset=field(default_factory=frozenset)
    def copy(self):
        return RegionState(**{f.name:(getattr(self,f.name).copy() if isinstance(getattr(self,f.name),(dict,list,set)) else getattr(self,f.name)) for f in fields(self)})
    def frontier(self):
        return {p for p in self.required if self.totals.get(p,0)<CAPACITY}

class RegionModel(ClusterModel):
    """Enumerate the complete finite admissible inventory before searching.

    Anchor a positive prototype point at every allowed point. Each other
    positive point must fit the declared envelope and immutable exterior.
    No other placement can be legal. All mutable marks/occupancy/ownership
    still go through Graph. Mark-only support is never confined to the envelope.
    """
    def __init__(self,types,boundary,base_marking=None):
        start=time.monotonic();super().__init__(types,base_marking,'finite-boundary-v1')
        self.boundary=boundary;self.index=defaultdict(set);initial=boundary.initial()
        ext=initial.totals
        for name in sorted(self.types):
            for o,entries in enumerate(self.orientations[name]):
                entries=sorted(entries,key=lambda pv:-pv[1]);q,v=entries[0]
                translations={sub(p,q) for p in boundary.allowed if ext.get(p,0)+v<=CAPACITY}
                for q,v in entries[1:]:
                    translations={tr for tr in translations if (p:=tuple(a+b for a,b in zip(q,tr))) in boundary.allowed and ext.get(p,0)+v<=CAPACITY}
                    if not translations:break
                for tr in sorted(translations):
                    key=name,o,tr;c=self.placement(key)
                    if initial.legal(c):
                        for p,v in c.occupancy:self.index[p].add(key)
        self.compilation_seconds=time.monotonic()-start
        self.admissible_placements=len({k for ks in self.index.values() for k in ks})
    def alignments(self,p):return tuple(sorted(self.index.get(p,())))

def independent_domains(model,state):
    """No finite inventory index: every type/orientation/support alignment."""
    from cluster_tiles import exhaustive_domains
    return exhaustive_domains(model,state)

def verify_region(model,boundary,state,complete=False):
    """Independent flattening, exterior agreement, inventory and generations.

    Reads explicit prototypes and base values, never a graph/domain/index.
    Exterior data are externally declared problem data, not proof-nominated.
    """
    totals=Counter(dict(boundary.exterior));marks=dict(boundary.marks);owned=set(boundary.owned)
    gens={p:0 for p,v in boundary.exterior};gens.update({p:0 for p in boundary.required});tile_gens=[]
    selected=set()
    for key in state.order:
        if key in selected:return False
        try:c=model.placement(key)
        except (KeyError,ValueError,IndexError,TypeError):return False
        if owned.intersection(c.expansion) or any(p not in boundary.allowed for p,v in c.occupancy):return False
        incident=[gens[p] for p,v in c.occupancy if p in gens];gen=1+min(incident) if incident else 0
        tile_gens.append(gen);selected.add(key);owned.update(c.expansion)
        base_totals=Counter();base_marks={}
        for k in c.expansion:
            base=model.base.placement(k);base_totals.update(dict(base.occupancy))
            for p,v in base.marks:
                if (p,'base') in base_marks and base_marks[p,'base']!=v:return False
                base_marks[p,'base']=v
        if dict(base_totals)!=dict(c.occupancy) or any(dict(c.marks).get(p)!=v for p,v in base_marks.items()):return False
        for p,v in base_totals.items():
            totals[p]+=v;gens[p]=min(gens.get(p,gen),gen)
            if totals[p]>CAPACITY:return False
        for p,v in c.marks:
            if p in marks and marks[p]!=v:return False
            marks[p]=v
    return (dict(totals)==state.totals and marks==state.marks and owned==state.owned_base
            and selected==state.selected and gens==state.generations and tile_gens==state.tile_generations
            and state.required==boundary.required and state.allowed_points==boundary.allowed
            and state.roots=={p:0 for p in boundary.required}
            and (not complete or all(totals[p]==CAPACITY for p in boundary.required)))

def packed_state(state):
    return {'placements':state.order,'tile_generations':state.tile_generations,
            'base_expansion':sorted(state.owned_base),'totals':sorted(state.totals.items()),
            'marks':sorted(state.marks.items())}

def unpack_state(model,boundary,d):
    if any(type(g) is not int or g<0 for g in d['tile_generations']):raise ValueError('invalid generation')
    if any(type(o) is not int or not 0<=o<12 or not point(tuple(tr)) for o,tr in d['base_expansion']):raise ValueError('invalid base identity')
    if any(not point(tuple(p)) or type(v) is not int for p,v in d['totals']):raise ValueError('invalid point total')
    if any(not point(tuple(p)) or type(v) is not int for (p,ch),v in d['marks']):raise ValueError('invalid marking')
    state=boundary.initial()
    for name,o,tr in d['placements']:state.place(model.placement((name,o,tuple(tr))))
    if (state.tile_generations!=d['tile_generations'] or sorted(state.owned_base)!=list(keys_tuple(d['base_expansion']))
        or sorted(state.totals.items())!=[(tuple(p),v) for p,v in d['totals']]
        or sorted(state.marks.items())!=[((tuple(p),ch),v) for (p,ch),v in d['marks']]):
        raise ValueError('altered expansion, point data or generations')
    return state

def features(model,state,graph,key):
    c=model.placement(key);fill=sum(state.totals.get(p,0)+v==CAPACITY for p,v in c.occupancy if p in state.required)
    gain=sum(v for p,v in c.occupancy if p in state.required)
    return {'bias':1.,'type:'+key[0]:1.,'size':len(c.expansion)/5,'fill':fill/28,
            'required_gain':gain/240,'frontier':len(graph.domains)/100,
            'exterior_contact':sum(p in dict(model.boundary.exterior) for p,v in c.occupancy)/len(c.occupancy)}

def search(types,boundary,seed=0,node_limit=10000,seconds=10,policy=None,learn=False,rollout=False):
    start=time.monotonic();model=RegionModel(types,boundary);state=boundary.initial();graph=Graph(model,state)
    rng=random.Random(seed);nodes=branches=forced=backtracks=base_attempts=0;traces=[];found=None;best=state.copy();tree=None
    peak_points=len(graph.domains);peak_candidates=len(graph.edges);peak_incidences=sum(map(len,graph.domains.values()))
    class Budget(Exception):pass
    def visit(s,g):
        nonlocal nodes,branches,forced,backtracks,base_attempts,found,best,peak_points,peak_candidates,peak_incidences
        nodes+=1
        if nodes>node_limit or (seconds is not None and time.monotonic()-start>seconds):raise Budget()
        peak_points=max(peak_points,len(g.domains));peak_candidates=max(peak_candidates,len(g.edges));peak_incidences=max(peak_incidences,sum(map(len,g.domains.values())))
        if sum(s.totals.get(p,0)==CAPACITY for p in s.required)>sum(best.totals.get(p,0)==CAPACITY for p in best.required):best=s.copy()
        kind,p,keys=g.decision(s)
        if kind=='dead':return {'dead':p}
        if kind=='empty':
            if not verify_region(model,boundary,s,True):raise AssertionError('invalid region completion')
            found=s.copy();return None
        if kind=='forced':forced+=1
        else:
            branches+=1;rng.shuffle(keys)
            if policy and learn:
                i,gradient=policy.select(rng,[features(model,s,g,k) for k in keys]);traces.append(gradient)
                keys=keys[i:i+1] if rollout else [keys[i]]+keys[:i]+keys[i+1:]
            elif policy:
                keys.sort(key=lambda k:sum(policy.weights[f]*v for f,v in features(model,s,g,k).items()),reverse=True)
            if rollout:keys=keys[:1]
        children=[]
        for key in keys:
            child=s.copy();cg=g.copy();c=model.placement(key);base_attempts+=len(c.expansion)
            cg.update(model,child,child.place(c))
            result=visit(child,cg)
            if found is not None:return None
            children.append({'placement':key,'proof':result});backtracks+=1
        return {'kind':kind,'point':p,'children':children}
    try:
        tree=visit(state,graph);status='finite_exact_region' if found else 'dead_rollout' if rollout else 'exhausted_finite_region'
    except Budget:status='unknown_budget';tree=None
    result=found or best;assert verify_region(model,boundary,result,found is not None)
    coverage=sum(result.totals.get(p,0)==CAPACITY for p in result.required)/len(result.required)
    reward=coverage+(1. if found else -1.)-.001*base_attempts-.001*nodes
    if policy and learn:policy.update(traces,reward)
    return {'status':status,'seed':seed,'nodes':nodes,'branches':branches,'forced':forced,'backtracks':backtracks,
            'seconds':time.monotonic()-start,'compilation_seconds':model.compilation_seconds,'admissible_placements':model.admissible_placements,
            'coverage_fraction':coverage,'required_points':len(boundary.required),'reward':reward,'certificate':tree if status=='exhausted_finite_region' else None,
            'peak_frontier_points':peak_points,'peak_candidate_nodes':peak_candidates,'peak_incidences':peak_incidences,
            'metrics':dict(model.metrics),'state':packed_state(result),'accepted_base_tiles':len(result.owned_base-set(boundary.owned)),
            'accepted_cluster_tiles':len(result.order),'attempted_base_placements':base_attempts,'verified':True}

def check_failure(model,boundary,tree):
    """Independently re-enumerate all scheduler domains and every alternative."""
    count=0
    def visit(state,node):
        nonlocal count
        count+=1;domains=independent_domains(model,state)
        if 'dead' in node:
            p=tuple(node['dead']);return p in domains and not domains[p]
        if not domains or any(not cs for cs in domains.values()):return False
        forced=sorted(p for p,cs in domains.items() if len(cs)==1)
        p=forced[0] if forced else min(domains,key=lambda p:(state.generations.get(p,state.roots.get(p,0)),len(domains[p]),p))
        if tuple(node['point'])!=p or node['kind']!=('forced' if forced else 'branch'):return False
        children=node['children'];keys=[(c['placement'][0],c['placement'][1],tuple(c['placement'][2])) for c in children]
        if len(keys)!=len(set(keys)) or set(keys)!=domains[p]:return False
        for child,key in zip(children,keys):
            s=state.copy();s.place(model.placement(key))
            if not visit(s,child['proof']):return False
        return True
    try:valid=visit(boundary.initial(),tree)
    except (KeyError,TypeError,ValueError,IndexError):valid=False
    return valid,count

def movable_search(types,boundaries,seed=0,node_limit=10000,seconds=10,policy=None):
    """Existential finite boundary family; distinct branches have fresh state.

    A cutoff in an earlier boundary never becomes its refutation. Every member
    receives the declared per-member budget, and all outcomes remain exported.
    This finite-family pilot is not a continuous shape optimization algorithm.
    """
    if not boundaries or len({b.identity for b in boundaries})!=len(boundaries):raise ValueError('nonempty distinct boundary family required')
    start=time.monotonic();attempts=[]
    for i,b in enumerate(boundaries):
        r=search(types,b,seed+i,node_limit,seconds,policy);attempts.append({'boundary':b.identity,'result':r})
        if r['status']=='finite_exact_region':
            return {'status':'finite_exact_movable_region','selected':b.identity,'attempts':attempts,'seconds':time.monotonic()-start}
    return {'status':'exhausted_finite_boundary_family' if all(a['result']['status']=='exhausted_finite_region' for a in attempts) else 'unknown_budget',
            'selected':None,'attempts':attempts,'seconds':time.monotonic()-start}
