"""First-class turtle cluster tiles with inherited and level-own markings.

This is a declared aggregate tile system, not an atomic shortcut in the base
macro engine. Every type has a flattened distinct base expansion. Parent types
inherit child marking components and can acquire another scalar level channel.
Including the unmarked singleton type preserves every base solution as an
all-singleton path. Learned cluster restrictions must state their own scope.
No failure marking, substitution or tiling witness is supplied by this module.
"""
from collections import Counter,defaultdict
from dataclasses import dataclass,field,fields
from turtle import Model,Placement,State,Graph,CAPACITY,SYMMETRIES,add,sub,transform,verify_patch
from spatial import moved,keys_tuple

@dataclass(frozen=True)
class ClusterType:
    identity:str
    level:int
    expansion:tuple
    occupancy:tuple
    marks:tuple
    children:tuple=()

@dataclass(frozen=True)
class ClusterPlacement:
    key:tuple
    occupancy:tuple
    marks:tuple
    expansion:tuple
    vertices:tuple=()

@dataclass
class ClusterState(State):
    owned_base:set=field(default_factory=set)
    def copy(self):
        values={f.name:(getattr(self,f.name).copy() if isinstance(getattr(self,f.name),(dict,list,set)) else getattr(self,f.name)) for f in fields(State)}
        return ClusterState(**values,owned_base=self.owned_base.copy())
    def legal(self,c):
        return super().legal(c) and not self.owned_base.intersection(c.expansion)
    def place(self,c,seed=False):
        changed=super().place(c,seed);self.owned_base.update(c.expansion)
        return changed|{('base-inventory',key) for key in c.expansion}

class ClusterModel:
    """Frozen scalar channel action; full positive-support alignments per type.

    m component keys are (physical point, channel), not new occupancy points.
    Every component transforms its physical point and leaves its scalar value
    and channel unchanged. Component-level dependencies include exterior zero.
    """
    def __init__(self,types,base_marking=None,version='cluster-v1'):
        self.types={t.identity:t for t in types}
        if len(self.types)!=len(types):raise ValueError('duplicate type identity')
        self.base=Model(base_marking);self.version=version
        self.cache={};self.align_cache={};self.dependencies=defaultdict(set);self.metrics=Counter()
        self.orientations={name:tuple(tuple((transform(p,g),v) for p,v in t.occupancy) for g in SYMMETRIES) for name,t in self.types.items()}
        for t in types:
            if not verify_expansion(self.base,t):raise ValueError('invalid cluster expansion/interface')
            for (p,channel),v in t.marks:
                if len(p)!=3 or any(type(x) is not int for x in p) or sum(p)!=0 or type(v) is not int:
                    raise ValueError('exact lattice points and integer scalar colors required')
                if channel!='base' and channel not in {f'cluster:{n}' for n in range(t.level+1)}:
                    raise ValueError('undeclared marking channel')
            if t.children:
                child_expansion=set();inherited={}
                for key in t.children:
                    child=self.placement(key)
                    if self.types[child.key[0]].level>=t.level:raise ValueError('cyclic or non-descending hierarchy')
                    child_expansion.update(child.expansion)
                    for p,v in child.marks:
                        if p in inherited and inherited[p]!=v:raise ValueError('child marking disagreement')
                        inherited[p]=v
                if child_expansion!=set(t.expansion) or any(dict(t.marks).get(p)!=v for p,v in inherited.items()):
                    raise ValueError('forged child expansion or omitted inherited marking')
    def placement(self,key):
        name,o,tr=key;tr=tuple(tr);key=name,o,tr
        if name not in self.types or type(o) is not int or not 0<=o<12 or len(tr)!=3 or any(type(v) is not int for v in tr) or sum(tr)!=0:
            raise ValueError('invalid cluster placement')
        if key not in self.cache:
            t=self.types[name];g=SYMMETRIES[o]
            occupancy=tuple((add(p,tr),v) for p,v in self.orientations[name][o])
            marks=tuple(((add(transform(p,g),tr),channel),v) for (p,channel),v in t.marks)
            expansion=moved(t.expansion,g,tr)
            c=ClusterPlacement(key,occupancy,marks,expansion);self.cache[key]=c
            for p,_ in occupancy+marks:self.dependencies[p].add(key)
            for base_key in expansion:self.dependencies['base-inventory',base_key].add(key)
        return self.cache[key]
    def alignments(self,p):
        if p not in self.align_cache:
            keys=tuple((name,o,sub(p,q)) for name in sorted(self.types) for o,entries in enumerate(self.orientations[name]) for q,_ in entries)
            for key in keys:self.placement(key)
            self.align_cache[p]=keys
        return self.align_cache[p]

def make_type(base,identity,level,expansion,inherited=(),own_marking=None,children=()):
    """Shared constituent identities are a union; their occupancy counts once."""
    if not isinstance(identity,str) or not identity or type(level) is not int or level<0:raise ValueError('invalid type')
    expansion=tuple(sorted(set(keys_tuple(expansion))))
    if not expansion or not verify_patch(base,expansion):raise ValueError('illegal base expansion')
    totals=Counter();marks={}
    def assign(point,value):
        if point in marks and marks[point]!=value:raise ValueError('incompatible inherited/own marking')
        marks[point]=value
    for key in expansion:
        c=base.placement(key);totals.update(dict(c.occupancy))
        for p,v in c.marks:assign((p,'base'),v)
    for p,v in inherited:assign(p,v)
    for p,v in (own_marking or {}).items():assign((tuple(p),f'cluster:{level}'),v)
    return ClusterType(identity,level,expansion,tuple(sorted(totals.items())),tuple(sorted(marks.items())),tuple(children))

def compose_type(model,identity,children,own_marking=None):
    placements=[model.placement(key) for key in children]
    expansion=set();marks={}
    for c in placements:
        expansion.update(c.expansion)
        for p,v in c.marks:
            if p in marks and marks[p]!=v:raise ValueError('child marking mismatch')
            marks[p]=v
    if not placements:raise ValueError('nonempty child assembly required')
    level=1+max(model.types[c.key[0]].level for c in placements)
    return make_type(model.base,identity,level,expansion,marks.items(),own_marking,children)

def verify_expansion(base,t):
    if len(t.expansion)!=len(set(t.expansion)) or not verify_patch(base,t.expansion):return False
    totals=Counter();base_marks={}
    for key in t.expansion:
        c=base.placement(key);totals.update(dict(c.occupancy))
        for p,v in c.marks:base_marks[p,'base']=v
    marks=dict(t.marks)
    return (tuple(sorted(totals.items()))==t.occupancy and len(marks)==len(t.marks)
            and all(marks.get(p)==v for p,v in base_marks.items())
            and all(type(v) is int and 0<v<=CAPACITY for p,v in t.occupancy))

def exhaustive_domains(model,state):
    """Independent complete type/orientation/alignment scan, no indexes."""
    out={}
    for p in state.frontier():
        domain=set()
        for name,t in model.types.items():
            for o,g in enumerate(SYMMETRIES):
                for q,_ in t.occupancy:
                    tr=sub(p,transform(q,g));key=name,o,tr
                    expansion=moved(t.expansion,g,tr)
                    occ=[(add(transform(r,g),tr),v) for r,v in t.occupancy]
                    marks=[((add(transform(r,g),tr),ch),v) for (r,ch),v in t.marks]
                    if (key not in state.selected and not state.owned_base.intersection(expansion)
                        and all(state.totals.get(r,0)+v<=CAPACITY for r,v in occ)
                        and (state.allowed_points is None or all(r in state.allowed_points for r,v in occ))
                        and all(r not in state.marks or state.marks[r]==v for r,v in marks)):domain.add(key)
        out[p]=domain
    return out

def verify_state(model,state,required=()):
    """Flatten the selected abstract proof back to base point semantics."""
    totals=Counter();marks={};owned=set()
    for key in state.order:
        c=model.placement(key)
        if owned.intersection(c.expansion):return False
        owned.update(c.expansion);totals.update(dict(c.occupancy))
        for p,v in c.marks:
            if p in marks and marks[p]!=v:return False
            marks[p]=v
    return (owned==state.owned_base and dict(totals)==state.totals and marks==state.marks
            and verify_patch(model.base,sorted(owned),required)
            and all(totals[p]==CAPACITY for p in required))
