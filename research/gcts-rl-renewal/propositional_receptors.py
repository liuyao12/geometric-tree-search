"""Direct bounded propositional proof families with finite-alphabet point marks.

This is a positional family adapter to the existing point graph, not a new
translation-invariant finite Wang inventory. No proof paths are supplied.
Ground axiom instances use a fixed query-independent syntactic parameter pool.
"""
import collections, copy, itertools, json, random, time
from turtle import CAPACITY, State, Graph, Placement, Policy

P = ('P',)
Q = ('Q',)
def imp(a,b): return ('imp',a,b)
def neg(a): return ('not',a)
def freeze(a): return tuple(freeze(x) for x in a) if isinstance(a,(list,tuple)) else a
def encode(a):
    if a in (P,Q): return a[0]
    if a[0]=='imp': return 'i'+encode(a[1])+encode(a[2])
    if a[0]=='not': return 'n'+encode(a[1])
    raise ValueError('formula outside the declared two-atom alphabet')
def tex(a):
    if a in (P,Q): return a[0]
    if a[0]=='not': return r'\neg '+('('+tex(a[1])+')')
    return '('+tex(a[1])+r'\Rightarrow '+tex(a[2])+')'
def formula_marks(slot,a):
    # A terminator makes a shorter prefix incompatible with any extension.
    return [((2*slot,2+j),v) for j,v in enumerate(encode(a)+'e')]
def cell(slot): return (2*slot,0)
def scope(slot): return (2*slot,1)
def substitute(a,mapping):
    if a in mapping: return mapping[a]
    return (a[0],)+(tuple(substitute(x,mapping) for x in a[1:]))

def basis():
    pool=(P,Q)+tuple(imp(a,b) for a,b in itertools.product((P,Q),repeat=2))
    rules=[]
    for a,b in itertools.product(pool,repeat=2):
        rules.append(dict(kind='H1',inputs=(),output=imp(a,imp(b,a))))
    for a,b,c in itertools.product(pool,repeat=3):
        rules.append(dict(kind='H2',inputs=(),output=imp(imp(a,imp(b,c)),imp(imp(a,b),imp(a,c)))))
    for a,b in itertools.product(pool,repeat=2):
        rules.append(dict(kind='H3',inputs=(),output=imp(imp(neg(b),neg(a)),imp(a,b))))
    universe=set()
    def collect(a):
        if a in universe:return
        universe.add(a)
        for x in a[1:]:collect(x)
    for r in rules:collect(r['output'])
    for a in sorted(universe,key=encode):
        if a[0]=='imp':rules.append(dict(kind='mp',inputs=(a[1],a),output=a[2]))
    return dict(parameter_pool=pool,formulas=tuple(sorted(universe,key=encode)),rules=rules,
                marking_alphabet=('P','Q','i','n','e'),scope_value=0)

def family_from_discovery(proof):
    if proof[-1]['formula']!=imp(P,P) or any(r['kind']=='lemma' for r in proof):
        raise ValueError('a primitive identity discovery is required')
    return dict(name='identity',parameter=P,conclusion=imp(P,P),proof=copy.deepcopy(proof))

def catalog(base,library=()):
    out=copy.deepcopy(base)
    for family in library:
        for a in base['parameter_pool']:
            mapping={family['parameter']:a}
            expanded=[dict(r,formula=substitute(r['formula'],mapping)) for r in family['proof']]
            out['rules'].append(dict(kind='lemma',name=family['name'],parameter=a,inputs=(),
                                     output=substitute(family['conclusion'],mapping),expansion=expanded))
    return out

class Model:
    def __init__(self,catalog,target,length,hypotheses=()):
        self.catalog=catalog;self.target=target;self.length=length;self.hypotheses=tuple(hypotheses)
        self.cache={};self.align_cache={};self.dependencies=collections.defaultdict(set)
        self.metrics=collections.Counter()
        for slot in range(length):
            keys=[]
            for rid,r in enumerate(catalog['rules']):
                for refs in itertools.product(range(-len(hypotheses),slot),repeat=len(r['inputs'])):
                    marks=dict(formula_marks(slot,r['output']));marks[scope(slot)]=0;valid=True
                    for j,a in zip(refs,r['inputs']):
                        for p,v in formula_marks(j,a)+[(scope(j),0)]:
                            if p in marks and marks[p]!=v:valid=False;break
                            marks[p]=v
                        if not valid:break
                    if not valid:continue
                    key=(slot,rid,refs)
                    c=Placement(key,((cell(slot),CAPACITY),),tuple(sorted(marks.items())),())
                    self.cache[key]=c;keys.append(key)
                    for p,_ in c.occupancy+c.marks:self.dependencies[p].add(key)
            self.align_cache[cell(slot)]=tuple(keys)
    def placement(self,key):return self.cache[key]
    def alignments(self,p):return self.align_cache.get(p,())
    def initial(self):
        roots={cell(j):0 for j in range(self.length)}
        marks=dict(formula_marks(self.length-1,self.target));marks[scope(self.length-1)]=0
        for j,a in enumerate(self.hypotheses,-len(self.hypotheses)):
            marks.update(formula_marks(j,a));marks[scope(j)]=0
        return State(roots=roots,generations=dict(roots),marks=marks,allowed_points=frozenset(roots))

def decode(model,keys):
    slots={k[0]:k for k in keys}
    if set(slots)!=set(range(model.length)) or len(slots)!=len(keys):raise ValueError('incomplete proof')
    proof=[]
    for j in range(model.length):
        _,rid,refs=slots[j];r=model.catalog['rules'][rid]
        row=dict(kind=r['kind'],formula=r['output'],refs=refs)
        if r['kind']=='lemma':row.update(name=r['name'],parameter=r['parameter'],expansion=r['expansion'])
        proof.append(row)
    return proof

def features(model,state,key):
    slot,rid,refs=key;r=model.catalog['rules'][rid]
    return {'bias':1.,'target':float(r['output']==model.target),'mp':float(r['kind']=='mp'),
            'lemma':float(r['kind']=='lemma'),'known_refs':sum(j<0 or cell(j) in state.totals for j in refs),
            'unfilled_refs':sum(j>=0 and cell(j) not in state.totals for j in refs),
            'length':len(encode(r['output']))/40.,'reach':max((slot-j for j in refs),default=0)/max(1,model.length)}

def propose(model,state,graph,policy,rng,learn=False):
    """A variable length, explicitly expanded cluster; no candidate filtering."""
    s=state.copy();g=graph.copy();sequence=[];traces=[]
    for _ in range(rng.randint(1,3)):
        kind,p,keys=g.decision(s)
        if kind in ('dead','empty'):break
        if kind=='forced':key=keys[0]
        elif learn:
            idx,gradient=policy.select(rng,[features(model,s,k) for k in keys]);key=keys[idx];traces.append(gradient)
        else:
            key=max(keys,key=lambda k:(sum(policy.weights[n]*v for n,v in features(model,s,k).items()),tuple(-x if isinstance(x,int) else x for x in k[:2])))
        sequence.append(key);g.update(model,s,s.place(model.placement(key)))
    return sequence,traces,s,g

def train(model,episodes=24,seed=42001):
    start=time.perf_counter();policy=Policy();rows=[]
    for n in range(episodes):
        rng=random.Random(seed+n);s=model.initial();g=Graph(model,s);traces=[];clusters=[]
        while True:
            kind,p,keys=g.decision(s)
            if kind in ('dead','empty'):break
            seq,gs,s,g=propose(model,s,g,policy,rng,True);traces+=gs;clusters.append(seq)
        reward=len(s.order)/model.length+(1 if kind=='empty' else -1)
        policy.update(traces,reward)
        rows.append(dict(seed=seed+n,outcome=kind,placed=len(s.order),reward=reward,clusters=clusters))
    return dict(seconds=time.perf_counter()-start,episodes=episodes,updates=policy.updates,
                weights=dict(policy.weights),baseline=policy.baseline,rollouts=rows,
                scope='REINFORCE learns variable-length continuation proposals; single training target, no proof supplied')

class Limit(Exception):pass
def search(model,node_limit=10000,seconds=20,policy_weights=None):
    model.metrics.clear();began=time.perf_counter();state=model.initial();graph=Graph(model,state);graph_seconds=time.perf_counter()-began
    metrics=collections.Counter();found=None;best=state;proposals=[];preferences={};samples=[]
    policy=Policy()
    if policy_weights is not None:policy.weights.update(policy_weights)
    rng=random.Random(901)
    def visit(s,g):
        nonlocal found,best
        metrics['nodes']+=1
        if metrics['nodes']>node_limit or time.perf_counter()-began>seconds:raise Limit()
        kind,p,keys=g.decision(s)
        metrics['peak_candidate_nodes']=max(metrics['peak_candidate_nodes'],len(g.edges))
        metrics['peak_incidences']=max(metrics['peak_incidences'],sum(map(len,g.domains.values())))
        if len(samples)<12:samples.append(dict(kind=kind,point=p,degree=len(keys),placed=list(s.order)))
        if kind=='dead':metrics['dead']+=1;return False,dict(kind=kind,point=p)
        if len(s.order)>len(best.order):best=s
        if kind=='empty':found=s;return True,dict(kind=kind,point=p)
        metrics['forced' if kind=='forced' else 'branches']+=1
        if kind=='branch' and policy_weights is not None:
            prefix=tuple(s.order)
            if prefix not in preferences:
                seq,_,_,_=propose(model,s,g,policy,rng)
                proposals.append(dict(incoming=list(s.order),expansion=seq))
                for key in seq:preferences[prefix]=key;prefix=prefix+(key,)
            chosen=preferences.get(tuple(s.order))
            if chosen in keys:keys=[chosen]+[k for k in keys if k!=chosen]
        tree=dict(kind=kind,point=p,children=[])
        for key in keys:
            metrics['attempts']+=1;child=s.copy();cg=g.copy()
            cg.update(model,child,child.place(model.placement(key)))
            ok,subtree=visit(child,cg);tree['children'].append(dict(key=key,tree=subtree))
            if ok:return True,tree
            metrics['backtracks']+=1
        return False,tree
    tree=None
    try:ok,tree=visit(state,graph);status='finite_exact_proof_tiling' if ok else 'exhausted_finite_envelope'
    except Limit:ok=False;status='unknown_search_budget'
    selected=found or best
    return dict(status=status,placements=selected.order,tile_generations=selected.tile_generations,
                proof=decode(model,selected.order) if found else None,metrics=dict(metrics),
                graph_metrics=dict(model.metrics),seconds=time.perf_counter()-began,graph_seconds=graph_seconds,
                candidate_universe=len(model.cache),samples=samples,proposals=proposals,
                limits=dict(nodes=node_limit,seconds=seconds),policy=policy_weights,search_tree=tree)

def chronological(model,node_limit=10000,seconds=20):
    began=time.perf_counter();metrics=collections.Counter();found=None
    def visit(keys,values):
        nonlocal found
        metrics['nodes']+=1
        if metrics['nodes']>node_limit or time.perf_counter()-began>seconds:raise Limit()
        j=len(keys)
        if j==model.length:found=keys;return True
        choices=[]
        for rid,r in enumerate(model.catalog['rules']):
            if j==model.length-1 and r['output']!=model.target:continue
            ds=[[i for i,v in values.items() if v==a] for a in r['inputs']]
            choices.extend((j,rid,refs) for refs in itertools.product(*ds))
        if len(choices)>1:metrics['branches']+=1
        for key in choices:
            metrics['attempts']+=1
            if visit(keys+[key],values|{j:model.catalog['rules'][key[1]]['output']}):return True
            metrics['backtracks']+=1
        return False
    try:
        ok=visit([],{j:a for j,a in enumerate(model.hypotheses,-len(model.hypotheses))})
        status='symbolic_proof_found' if ok else 'exhausted_finite_envelope'
    except Limit:status='unknown_search_budget'
    return dict(status=status,metrics=dict(metrics),seconds=time.perf_counter()-began,
                placements=found,proof=decode(model,found) if found else None,limits=dict(nodes=node_limit,seconds=seconds))

def forward(catalog,target,hypotheses=()):
    """Complete finite formula saturation, with duplicate proof facts shared.

    Same rules, no slot-length constraint: report this difference explicitly.
    """
    began=time.perf_counter();known={a:(j,None) for j,a in enumerate(hypotheses,-len(hypotheses))};steps=0
    while True:
        changed=False
        for rid,r in enumerate(catalog['rules']):
            steps+=1
            if r['output'] in known or not all(a in known for a in r['inputs']):continue
            known[r['output']]=(rid,r);changed=True
        if target in known or not changed:break
    proof=[];ids={a:j for j,a in enumerate(hypotheses,-len(hypotheses))}
    def emit(a):
        if a in ids:return ids[a]
        rid,r=known[a];refs=tuple(emit(p) for p in r['inputs']);j=len(proof);row=dict(kind=r['kind'],formula=a,refs=refs)
        if r['kind']=='lemma':row.update(name=r['name'],parameter=r['parameter'],expansion=r['expansion'])
        proof.append(row);ids[a]=j;return j
    if target in known:emit(target)
    return dict(status='saturation_proof_found' if target in known else 'exhausted_finite_formula_closure',
                proof=proof if target in known else None,known=len(known),rule_tests=steps,seconds=time.perf_counter()-began,
                scope='same finite rules and hypotheses; shares facts and has no exact proof-slot length bound')
