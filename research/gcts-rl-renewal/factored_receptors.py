"""Exact lazy incidence for the one-slot propositional point model.

Schema parameters are Cartesian blocks; MP references are two integer masks,
with their diagonal removed. Each candidate touches one occupied point, so its
reverse incidence is the singleton containing that slot. This specialization
does not support arbitrary partial formula ports, fractional/shared occupancy,
or additional learned marking channels.
"""
import bisect,collections,itertools,random,time
import propositional_receptors as R
from turtle import Policy,Placement,CAPACITY

def pool(kind='plain'):
    atoms=(R.P,R.Q) if kind=='plain' else (R.P,R.Q,R.neg(R.P),R.neg(R.Q))
    if kind not in ('plain','negated'):raise ValueError('declared parameter pool')
    return atoms+tuple(R.imp(a,b) for a,b in itertools.product(atoms,repeat=2))
def schema(kind,params):
    if kind=='H1':a,b=params;return R.imp(a,R.imp(b,a))
    if kind=='H2':a,b,c=params;return R.imp(R.imp(a,R.imp(b,c)),R.imp(R.imp(a,b),R.imp(a,c)))
    if kind=='H3':a,b=params;return R.imp(R.imp(R.neg(b),R.neg(a)),R.imp(a,b))
    raise ValueError('schema')
def bits(mask):
    while mask:
        v=mask&-mask;yield v.bit_length()-1;mask-=v
def popcount(mask):return bin(mask).count('1')
class Rules:
    def __init__(self,u):self.u=u
    def __len__(self):return self.u.rule_count
    def __getitem__(self,j):return self.u.rule(j)
    def __iter__(self):
        for j in range(len(self)):yield self[j]
class Universe:
    def __init__(self,kind='plain',family=None):
        self.kind=kind;self.pool=pool(kind);self.positions={a:j for j,a in enumerate(self.pool)};self.n=len(self.pool)
        n=self.n;self.starts=(0,n*n,n*n+n**3);self.schema_count=n**3+2*n*n
        formulas=set()
        def collect(a):
            if a in formulas:return
            formulas.add(a)
            for x in a[1:]:collect(x)
        # Still builds the finite implication catalog. No candidate/reference
        # products or persistent H-schema instance table is constructed.
        for k,arity in (('H1',2),('H2',3),('H3',2)):
            for ps in itertools.product(self.pool,repeat=arity):collect(schema(k,ps))
        self.implications=tuple(sorted((a for a in formulas if a[0]=='imp'),key=R.encode))
        self.formulas_count=len(formulas);self.by_output=collections.defaultdict(list)
        for j,a in enumerate(self.implications):self.by_output[a[2]].append(self.schema_count+j)
        self.lemma_start=self.schema_count+len(self.implications);self.family=family
        self.rule_count=self.lemma_start+(n if family else 0);self.rules=Rules(self)
    def rule(self,rid):
        if type(rid) is not int or not 0<=rid<self.rule_count:raise IndexError('rule identity')
        n=self.n
        if rid<self.schema_count:
            k=2 if rid>=self.starts[2] else 1 if rid>=self.starts[1] else 0
            x=rid-self.starts[k];arity=(2,3,2)[k];ps=[None]*arity
            for j in reversed(range(arity)):x,i=divmod(x,n);ps[j]=self.pool[i]
            return dict(kind=('H1','H2','H3')[k],inputs=(),output=schema(('H1','H2','H3')[k],ps))
        if rid<self.lemma_start:
            a=self.implications[rid-self.schema_count];return dict(kind='mp',inputs=(a[1],a),output=a[2])
        a=self.pool[rid-self.lemma_start];f=self.family
        expanded=[dict(r,formula=R.substitute(r['formula'],{f['parameter']:a})) for r in f['proof']]
        return dict(kind='lemma',name=f['name'],parameter=a,inputs=(),output=R.imp(a,a),expansion=expanded)
    def bound_schemas(self,a):
        out=[]
        for k,kind in enumerate(('H1','H2','H3')):
            try:
                ps=(a[1],a[2][1]) if k==0 else (a[1][1],a[1][2][1],a[1][2][2]) if k==1 else (a[2][1],a[2][2])
                if schema(kind,ps)!=a or any(v not in self.positions for v in ps):continue
                rid=0
                for v in ps:rid=rid*self.n+self.positions[v]
                out.append(self.starts[k]+rid)
            except (IndexError,TypeError,ValueError):pass
        return out
    def cardinality(self,length,hypotheses):
        h=len(hypotheses)
        return sum(self.schema_count+(self.n if self.family else 0)+len(self.implications)*(j+h)*(j+h-1) for j in range(length))
class Domain:
    def __init__(self,slot,h,blocks):
        self.slot=slot;self.h=h;self.blocks=tuple(blocks);self.starts=tuple(b[0] for b in blocks)
        self.count=sum(stop-start if a is None else popcount(a)*popcount(b)-popcount(a&b) for start,stop,a,b in blocks)
    def __len__(self):return self.count
    def __bool__(self):return self.count!=0
    def __iter__(self):
        for start,stop,a,b in self.blocks:
            if a is None:
                for rid in range(start,stop):yield (self.slot,rid,())
            else:
                for i in bits(a):
                    for j in bits(b&~(1<<i)):yield (self.slot,start,(i-self.h,j-self.h))
    def __getitem__(self,j):
        if j!=0:raise IndexError('only singleton extraction is supported')
        return next(iter(self))
    def __contains__(self,key):
        slot,rid,refs=key
        if slot!=self.slot:return False
        j=bisect.bisect_right(self.starts,rid)-1
        if j<0:return False
        start,stop,a,b=self.blocks[j]
        if not start<=rid<stop:return False
        if a is None:return refs==()
        return len(refs)==2 and refs[0]!=refs[1] and all(-self.h<=i<self.slot for i in refs) and bool(a&(1<<(refs[0]+self.h))) and bool(b&(1<<(refs[1]+self.h)))
class Model:
    def __init__(self,universe,target,length,hypotheses=()):
        if length<1:raise ValueError('positive proof length')
        self.universe=universe;self.target=target;self.length=length;self.hypotheses=tuple(hypotheses)
        self.catalog=dict(rules=universe.rules);self.metrics=collections.Counter();self.cache={}
    initial=R.Model.initial
    def placement(self,key):
        if key in self.cache:return self.cache[key]
        slot,rid,refs=key;r=self.universe.rule(rid)
        if not 0<=slot<self.length or len(refs)!=len(r['inputs']) or any(not -len(self.hypotheses)<=i<slot for i in refs):raise ValueError('candidate reference domain')
        marks=dict(R.formula_marks(slot,r['output']));marks[R.scope(slot)]=0
        for j,a in zip(refs,r['inputs']):
            for p,v in R.formula_marks(j,a)+[(R.scope(j),0)]:
                if p in marks and marks[p]!=v:raise ValueError('single-valued candidate')
                marks[p]=v
        c=Placement(key,((R.cell(slot),CAPACITY),),tuple(sorted(marks.items())),())
        self.cache[key]=c;self.metrics['materialized_placements']+=1;return c
class Graph:
    def __init__(self,model,state):
        self.model=model;self.ports={model.length-1:model.target}|{j:a for j,a in enumerate(model.hypotheses,-len(model.hypotheses))}
        self.order=();self.domains={p:self.calculate(p) for p in state.frontier()}
    def copy(self):
        g=object.__new__(Graph);g.model=self.model;g.ports=self.ports.copy();g.order=self.order;g.domains=self.domains.copy();return g
    def calculate(self,p):
        j=p[0]//2;m=self.model;u=m.universe;h=len(m.hypotheses);a=self.ports.get(j);blocks=[]
        if a is None:blocks.append((0,u.schema_count,None,None))
        else:blocks.extend((rid,rid+1,None,None) for rid in u.bound_schemas(a))
        known=collections.defaultdict(int);bound=0
        for i,value in self.ports.items():
            if -h<=i<j:known[value]|=1<<(i+h);bound|=1<<(i+h)
        free=((1<<(j+h))-1)&~bound
        ids=range(u.schema_count,u.lemma_start) if a is None else u.by_output.get(a,())
        for rid in ids:
            implication=u.implications[rid-u.schema_count];antecedent=implication[1]
            x=free|known[antecedent];y=free|known[implication]
            if popcount(x)*popcount(y)>popcount(x&y):blocks.append((rid,rid+1,x,y))
        if u.family:
            ids=range(u.lemma_start,u.rule_count) if a is None else (u.lemma_start+u.positions[a[1]],) if a[0]=='imp' and a[1]==a[2] and a[1] in u.positions else ()
            blocks.extend((rid,rid+1,None,None) for rid in ids)
        blocks.sort(key=lambda b:b[0]);d=Domain(j,h,blocks)
        m.metrics['domain_constructions']+=1;m.metrics['factor_records_constructed']+=len(blocks);return d
    def update(self,model,state,changed):
        if tuple(state.order[:-1])!=self.order:raise ValueError('one exact placement transaction required')
        key=state.order[-1];j,rid,refs=key;r=model.universe.rule(rid);pairs=[(j,r['output'])]+list(zip(refs,r['inputs']));new=[]
        for i,a in pairs:
            if i in self.ports and self.ports[i]!=a:raise ValueError('formula-port disagreement')
            if not all(state.marks.get(p)==v for p,v in R.formula_marks(i,a)+[(R.scope(i),0)]):raise ValueError('actual point-port binding')
            if i not in self.ports:self.ports[i]=a;new.append(i)
        self.order=tuple(state.order);frontier=state.frontier()
        for p in self.domains.keys()-frontier:del self.domains[p]
        if new:
            first=min(new)
            for p in frontier:
                if p[0]//2>=first:self.domains[p]=self.calculate(p)
    def candidate_points(self,key):
        p=R.cell(key[0]);return {p} if p in self.domains and key in self.domains[p] else set()
    def decision(self,state):
        dead=sorted(p for p,d in self.domains.items() if d.count==0)
        if dead:return 'dead',dead[0],()
        forced=sorted(p for p,d in self.domains.items() if d.count==1)
        if forced:return 'forced',forced[0],self.domains[forced[0]]
        if not self.domains:return 'empty',None,()
        p=min(self.domains,key=lambda p:(state.generations.get(p,state.roots.get(p,0)),self.domains[p].count,p))
        return 'branch',p,self.domains[p]
    def fingerprint(self):return (tuple(sorted(self.ports.items())),self.order,tuple(sorted((p,d.blocks,d.count) for p,d in self.domains.items())))
def search(model,node_limit=10000,seconds=20,policy_weights=None):
    began=time.perf_counter();model.metrics.clear();s=model.initial();g=Graph(model,s);graph_seconds=time.perf_counter()-began
    metrics=collections.Counter();found=None;best=s;proposals=[];preferences={};policy=Policy();samples=[];rng=random.Random(901)
    if policy_weights is not None:policy.weights.update(policy_weights)
    def visit(s,g):
        nonlocal found,best
        metrics['nodes']+=1
        if metrics['nodes']>node_limit or time.perf_counter()-began>seconds:raise R.Limit()
        kind,p,keys=g.decision(s);total=sum(d.count for d in g.domains.values())
        metrics['peak_candidate_nodes']=max(metrics['peak_candidate_nodes'],total);metrics['peak_incidences']=metrics['peak_candidate_nodes']
        metrics['peak_factor_records']=max(metrics['peak_factor_records'],sum(len(d.blocks) for d in g.domains.values()))
        if len(samples)<12:samples.append(dict(kind=kind,point=p,degree=len(keys),placed=list(s.order)))
        if kind=='dead':metrics['dead']+=1;return False,dict(kind=kind,point=p)
        if len(s.order)>len(best.order):best=s
        if kind=='empty':found=s;return True,dict(kind=kind,point=p)
        metrics['forced' if kind=='forced' else 'branches']+=1
        preferred=None
        if kind=='branch' and policy_weights is not None:
            prefix=tuple(s.order)
            if prefix not in preferences:
                seq,_,_,_=R.propose(model,s,g,policy,rng);proposals.append(dict(incoming=list(s.order),expansion=seq))
                for key in seq:preferences[prefix]=key;prefix=prefix+(key,)
            preferred=preferences.get(tuple(s.order))
        tree=dict(kind=kind,point=p,children=[])
        def ordered():
            if preferred is not None and preferred in keys:yield preferred
            for k in keys:
                if k!=preferred:yield k
        for key in ordered():
            metrics['attempts']+=1;ss=s.copy();gg=g.copy();gg.update(model,ss,ss.place(model.placement(key)))
            ok,t=visit(ss,gg);tree['children'].append(dict(key=key,tree=t))
            if ok:return True,tree
            metrics['backtracks']+=1
        return False,tree
    tree=None
    try:ok,tree=visit(s,g);status='finite_exact_proof_tiling' if ok else 'exhausted_finite_envelope'
    except R.Limit:status='unknown_search_budget'
    selected=found or best
    return dict(status=status,placements=selected.order,tile_generations=selected.tile_generations,proof=R.decode(model,selected.order) if found else None,
        metrics=dict(metrics),graph_metrics=dict(model.metrics),seconds=time.perf_counter()-began,graph_seconds=graph_seconds,
        candidate_universe=model.universe.cardinality(model.length,model.hypotheses),samples=samples,proposals=proposals,
        limits=dict(nodes=node_limit,seconds=seconds),policy=policy_weights,search_tree=tree,
        scope='Exact factorization of a declared one-slot full-formula-port point model; reverse incidence is singleton; no heuristic removal.')
