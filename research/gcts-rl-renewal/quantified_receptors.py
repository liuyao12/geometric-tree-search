"""Finite first-order ports, exact reference factors and ambient scope marks.

Only complete formula ports and single-slot capacity-12 placements are supported.
The finite grammar is uniformly closed under a declared number of instantiation
rounds, then one layer of generalization; it is not a complete FOL prover.
"""
import collections,itertools,time
import logic as L
from turtle import State,Placement,CAPACITY
from serialized_kernel import canonical,check,PROTOCOL,problem_hash

def word(a):return canonical(a).decode('ascii')+'#'
def cell(j):return (2*j,0)
def port(j,a):return [((2*j,2+k),v) for k,v in enumerate(word(a))]+[((2*j,1),0)]
def scope(j):return (-1000,j)
def bits(n):
    while n:
        b=n&-n;yield b.bit_length()-1;n-=b
def count(n):return bin(n).count('1')
def subformulas(a):
    yield a
    if a[0]=='all':yield from subformulas(a[2])
    elif a[0] in ('not','imp','and','or'):
        for b in a[1:]:yield from subformulas(b)
def specialize(a,bindings):
    if a[0]=='pred' and a[1] in bindings:
        if len(a[2])!=1:raise ValueError('unary predicate family')
        return L.substitute(bindings[a[1]],'x',a[2][0])
    if a[0]=='all':return L.All(a[1],specialize(a[2],bindings))
    if a[0] in ('not','imp','and','or'):return (a[0],)+tuple(specialize(b,bindings) for b in a[1:])
    return a
def row(r,refs):return dict(kind=r['kind'],formula=r['output'],refs=tuple(refs),parameters=r['parameters'])
def inventory(theory,hypotheses,terms,variables,rounds=2,family=None,bindings=(),generalization_rounds=2):
    base=L.Kernel(theory['functions'],theory['predicates'],theory['axioms'])
    fs=set()
    for a in list(theory['axioms'].values())+list(hypotheses):base.formula(a);fs.update(subformulas(a))
    for t in terms:base.term(t)
    for _ in range(rounds):
        added=set()
        for u in sorted(fs,key=word):
            if u[0]=='all':
                for t in terms:added.update(subformulas(L.substitute(u[2],u[1],t)))
        fs.update(added)
    for a in tuple(fs):
        if a[0]=='imp' and a[2][0]=='and':
            for b in a[2][1:]:fs.update(subformulas(L.Imp(a[1],b)))
    for _ in range(generalization_rounds):fs.update(L.All(x,a) for a in tuple(fs) for x in variables)
    rules=[]
    def add(kind,ps,a,guards=(),**params):rules.append(dict(kind=kind,inputs=tuple(ps),output=a,guards=tuple(guards),parameters=params))
    for name,a in sorted(theory['axioms'].items()):add('axiom',(),a,name=name)
    for a in sorted(fs,key=word):
        if a[0]=='all':
            for t in terms:
                instance=L.substitute(a[2],a[1],t)
                if instance in fs:add('forall-elim',(a,),instance,universal=a,term=t)
        if a[0]=='imp':add('mp',(a[1],a),a[2])
        if a[0]=='imp' and a[2][0]=='and':
            for side,b in enumerate(a[2][1:]):add('projection',(a,),L.Imp(a[1],b),side=side)
        for x in variables:
            if L.All(x,a) in fs:add('generalize',(a,),L.All(x,a),(x,),variable=x)
    if family:
        for binding in bindings:
            proof=[dict(r,formula=specialize(r['formula'],binding),parameters={k:specialize(v,binding) if k=='universal' else v for k,v in r['parameters'].items()}) for r in family['proof']]
            ps=tuple(specialize(a,binding) for a in family['premises']);a=specialize(family['conclusion'],binding)
            add('family',ps,a,family['guards'],name=family['name'],binding=binding,expansion=proof)
    unique={canonical(r):r for r in rules};rules=[unique[k] for k in sorted(unique)]
    return dict(rules=rules,formulas=sorted(fs,key=word),variables=tuple(variables),terms=tuple(terms),rounds=rounds,generalization_rounds=generalization_rounds)

class Domain:
    def __init__(self,j,h,blocks):
        self.j=j;self.h=h;self.blocks=tuple(blocks);self.index={r:(m,d) for r,m,d in blocks}
        self.count=sum(1 if not m else count(m[0]) if len(m)==1 else count(m[0])*count(m[1])-(count(m[0]&m[1]) if d else 0) for _,m,d in blocks)
    def __len__(self):return self.count
    def __iter__(self):
        for rid,masks,distinct in self.blocks:
            for refs in itertools.product(*(bits(m) for m in masks)):
                if not distinct or refs[0]!=refs[1]:yield (self.j,rid,tuple(i-self.h for i in refs))
    def __contains__(self,k):
        j,rid,refs=k
        if j!=self.j or rid not in self.index:return False
        masks,d=self.index[rid]
        return len(refs)==len(masks) and all(-self.h<=i<j and bool(m&(1<<(i+self.h))) for i,m in zip(refs,masks)) and (not d or refs[0]!=refs[1])
    def __getitem__(self,j):
        if j!=0:raise IndexError('singleton extraction only')
        return next(iter(self))

class Model:
    def __init__(self,catalog,target,length,hypotheses=()):
        if length<1:raise ValueError('positive slot count')
        self.catalog=catalog;self.target=target;self.length=length;self.hypotheses=tuple(hypotheses);self.cache={};self.metrics=collections.Counter()
        self.forbidden=set().union(*(L.free(a) for a in hypotheses));self.variables=catalog['variables'];self.vi={x:j for j,x in enumerate(self.variables)}
        if any(x not in self.vi for r in catalog['rules'] for x in r['guards']):raise ValueError('complete guard point domain')
        self.by_output=collections.defaultdict(list)
        for rid,r in enumerate(catalog['rules']):self.by_output[r['output']].append(rid)
    def initial(self):
        s=State();s.roots={cell(j):0 for j in range(self.length)};s.generations=s.roots.copy();s.allowed_points=frozenset(s.roots);s.marks=dict(port(self.length-1,self.target))
        for j,a in enumerate(self.hypotheses,-len(self.hypotheses)):s.marks.update(port(j,a))
        s.marks.update((scope(j),int(x in self.forbidden)) for j,x in enumerate(self.variables));return s
    def placement(self,key):
        if key in self.cache:return self.cache[key]
        j,rid,refs=key;r=self.catalog['rules'][rid]
        if not 0<=j<self.length or len(refs)!=len(r['inputs']) or any(not -len(self.hypotheses)<=i<j for i in refs):raise ValueError('reference domain')
        marks={}
        for i,a in [(j,r['output'])]+list(zip(refs,r['inputs'])):
            for p,v in port(i,a):
                if p in marks and marks[p]!=v:raise ValueError('single-valued placement')
                marks[p]=v
        for x in r['guards']:marks[scope(self.vi[x])]=0
        c=Placement(key,((cell(j),CAPACITY),),tuple(sorted(marks.items())),());self.cache[key]=c;self.metrics['materialized_placements']+=1;return c
    def cardinality(self):
        h=len(self.hypotheses)
        return sum((j+h)**len(r['inputs'])-((j+h) if len(r['inputs'])==2 and r['inputs'][0]!=r['inputs'][1] else 0) for j in range(self.length) for r in self.catalog['rules'])

class Graph:
    def __init__(self,m,s):
        self.m=m;self.scope_values={x:s.marks.get(scope(j)) for j,x in enumerate(m.variables)}
        if any(self.scope_values[x]!=int(x in m.forbidden) for x in m.variables):raise ValueError('complete ambient context marking binding')
        self.ports={m.length-1:m.target}|{j:a for j,a in enumerate(m.hypotheses,-len(m.hypotheses))};self.order=();self.domains={p:self.calculate(p) for p in s.frontier()}
    def copy(self):
        g=object.__new__(Graph);g.m=self.m;g.scope_values=self.scope_values.copy();g.ports=self.ports.copy();g.order=self.order;g.domains=self.domains.copy();return g
    def calculate(self,p):
        j=p[0]//2;m=self.m;h=len(m.hypotheses);a=self.ports.get(j);known=collections.defaultdict(int);bound=0;blocks=[]
        for i,v in self.ports.items():
            if -h<=i<j:known[v]|=1<<(i+h);bound|=1<<(i+h)
        free=((1<<(j+h))-1)&~bound
        for rid in m.by_output.get(a,()) if a is not None else range(len(m.catalog['rules'])):
            r=m.catalog['rules'][rid]
            if any(self.scope_values[x]!=0 for x in r['guards']):continue
            masks=tuple(free|known[v] for v in r['inputs']);distinct=len(masks)==2 and r['inputs'][0]!=r['inputs'][1]
            if all(masks) and (not distinct or count(masks[0])*count(masks[1])>count(masks[0]&masks[1])):blocks.append((rid,masks,distinct))
        d=Domain(j,h,blocks);m.metrics['domain_constructions']+=1;m.metrics['factor_records_constructed']+=len(blocks);return d
    def update(self,m,s,changed):
        if tuple(s.order[:-1])!=self.order:raise ValueError('one-placement transaction')
        if any(s.marks.get(scope(m.vi[x]))!=v for x,v in self.scope_values.items()):raise ValueError('fixed context scope values changed')
        j,rid,refs=s.order[-1];r=m.catalog['rules'][rid];new=[]
        for i,a in [(j,r['output'])]+list(zip(refs,r['inputs'])):
            if i in self.ports and self.ports[i]!=a:raise ValueError('port mismatch')
            if not all(s.marks.get(p)==v for p,v in port(i,a)):raise ValueError('actual complete word binding')
            if i not in self.ports:self.ports[i]=a;new.append(i)
        for x in r['guards']:
            if s.marks.get(scope(m.vi[x]))!=0:raise ValueError('actual eigenvariable marking')
        self.order=tuple(s.order);frontier=s.frontier()
        for p in self.domains.keys()-frontier:del self.domains[p]
        if new:
            for p in frontier:
                if p[0]//2>=min(new):self.domains[p]=self.calculate(p)
    def candidate_points(self,key):
        p=cell(key[0]);return {p} if p in self.domains and key in self.domains[p] else set()
    def decision(self,s):
        dead=sorted(p for p,d in self.domains.items() if not len(d));forced=sorted(p for p,d in self.domains.items() if len(d)==1)
        if dead:return 'dead',dead[0],()
        if forced:return 'forced',forced[0],self.domains[forced[0]]
        if not self.domains:return 'empty',None,()
        p=min(self.domains,key=lambda p:(s.generations.get(p,s.roots.get(p,0)),len(self.domains[p]),p));return 'branch',p,self.domains[p]
    def fingerprint(self):return (tuple(sorted(self.ports.items())),tuple(sorted(self.scope_values.items())),self.order,tuple(sorted((p,d.blocks,d.count) for p,d in self.domains.items())))

class Limit(Exception):pass
def decode(m,keys):
    proof=[None]*m.length
    for j,rid,refs in keys:proof[j]=row(m.catalog['rules'][rid],refs)
    return proof
def search(m,node_limit=20000,seconds=15):
    began=time.perf_counter();s=m.initial();g=Graph(m,s);metrics=collections.Counter();found=None;best=s
    def visit(s,g):
        nonlocal found,best
        metrics['nodes']+=1
        if metrics['nodes']>node_limit or time.perf_counter()-began>seconds:raise Limit()
        kind,p,keys=g.decision(s);metrics['peak_candidates']=max(metrics['peak_candidates'],sum(len(d) for d in g.domains.values()))
        if kind=='dead':metrics['dead']+=1;return False,dict(kind=kind,point=p)
        if len(s.order)>len(best.order):best=s
        if kind=='empty':found=s;return True,dict(kind=kind,point=p)
        metrics[kind]+=1;t=dict(kind=kind,point=p,children=[])
        for key in keys:
            metrics['attempts']+=1;ss=s.copy();gg=g.copy();gg.update(m,ss,ss.place(m.placement(key)));ok,child=visit(ss,gg);t['children'].append(dict(key=key,tree=child))
            if ok:return True,t
            metrics['backtracks']+=1
        return False,t
    tree=None
    try:ok,tree=visit(s,g);status='finite_exact_proof_tiling' if ok else 'exhausted_finite_envelope'
    except Limit:status='unknown_search_budget'
    selected=found or best
    return dict(status=status,placements=selected.order,proof=decode(m,selected.order) if found else None,metrics=dict(metrics),graph_metrics=dict(m.metrics),seconds=time.perf_counter()-began,candidate_universe=m.cardinality(),search_tree=tree,limits=dict(nodes=node_limit,seconds=seconds),tile_generations=selected.tile_generations)

def chronological(m,node_limit=20000,seconds=15):
    start=time.perf_counter();metrics=collections.Counter();found=None
    def visit(keys,known):
        nonlocal found
        metrics['nodes']+=1
        if metrics['nodes']>node_limit or time.perf_counter()-start>seconds:raise Limit()
        j=len(keys)
        if j==m.length:found=keys;return True
        for rid,r in enumerate(m.catalog['rules']):
            if (j==m.length-1 and r['output']!=m.target) or any(x in m.forbidden for x in r['guards']):continue
            for refs in itertools.product(*([i for i,a in known.items() if a==v] for v in r['inputs'])):
                metrics['attempts']+=1
                if visit(keys+[(j,rid,refs)],known|{j:r['output']}):return True
                metrics['backtracks']+=1
        return False
    try:ok=visit([],{j:a for j,a in enumerate(m.hypotheses,-len(m.hypotheses))});status='found' if ok else 'exhausted_finite_envelope'
    except Limit:status='unknown_search_budget'
    return dict(status=status,proof=decode(m,found) if found else None,placements=found,metrics=dict(metrics),seconds=time.perf_counter()-start)
def saturation(m):
    start=time.perf_counter();known={a:None for a in m.hypotheses};steps=0
    while True:
        changed=False
        for rid,r in enumerate(m.catalog['rules']):
            steps+=1
            if r['output'] in known or any(x in m.forbidden for x in r['guards']) or not all(a in known for a in r['inputs']):continue
            known[r['output']]=rid;changed=True
        if m.target in known or not changed:break
    proof=[];ids={a:j for j,a in enumerate(m.hypotheses,-len(m.hypotheses))}
    def emit(a):
        if a in ids:return ids[a]
        rid=known[a];r=m.catalog['rules'][rid];refs=tuple(emit(v) for v in r['inputs']);j=len(proof);proof.append(row(r,refs));ids[a]=j;return j
    if m.target in known:emit(m.target)
    return dict(status='found' if m.target in known else 'exhausted_finite_formula_closure',proof=proof if m.target in known else None,seconds=time.perf_counter()-start,rule_tests=steps,known=len(known),fits_slot_bound=len(proof)<=m.length if proof else None)

def commands(proof,hypotheses=()):
    out=[dict(rule='assumption',formula=a,index=j) for j,a in enumerate(hypotheses)];refs={j:i for i,j in enumerate(range(-len(hypotheses),0))};bindings=[]
    def emit(r):out.append(r);return len(out)-1
    def expand(rows,external):
        mapping=dict(external)
        for j,r in enumerate(rows):
            a=r['formula'];p=r['parameters'];indices=[mapping[i] for i in r['refs']]
            if r['kind']=='axiom':k=emit(dict(rule='axiom',formula=a,name=p['name']))
            elif r['kind']=='forall-elim':
                u=p['universal'];k=emit(dict(rule='instantiate',formula=L.Imp(u,a),universal=u,term=p['term']));k=emit(dict(rule='mp',formula=a,antecedent=indices[0],implication=k))
            elif r['kind']=='generalize':k=emit(dict(rule='generalize',formula=a,variable=p['variable'],source=indices[0]))
            elif r['kind']=='projection':
                before=out[indices[0]]['formula'];k=emit(dict(rule='tautology',formula=L.Imp(before,a)));k=emit(dict(rule='mp',formula=a,antecedent=indices[0],implication=k))
            elif r['kind']=='mp':k=emit(dict(rule='mp',formula=a,antecedent=indices[0],implication=indices[1]))
            elif r['kind']=='family':k=expand(p['expansion'],{i:k for i,k in enumerate(indices,-len(indices))})
            else:raise ValueError('source rule')
            mapping[j]=k
        return mapping[len(rows)-1]
    for j,r in enumerate(proof):
        start=len(out);k=expand([r],{i:refs[i] for i in r['refs']});refs[j]=k;bindings.append(dict(source_slot=j,first=start,last=k))
    return out,bindings

def discharge(lines,premises):
    """Ordinary Hilbert deduction, including the universal distribution step.

    This compiler transforms the discovered derivation; it supplies no search
    path. Each generated command is independently checked by the fixed kernel.
    """
    lines=list(lines);premises=list(premises)
    while premises:
        h=premises[-1];out=[];mapping={}
        def emit(r):out.append(r);return len(out)-1
        def mp(a,i,j):return emit(dict(rule='mp',formula=a,antecedent=i,implication=j))
        for j,r in enumerate(lines):
            a=r['formula'];rule=r['rule'];goal=L.Imp(h,a)
            if rule=='assumption' and r['index']==len(premises)-1:
                k=emit(dict(rule='tautology',formula=goal))
            elif rule=='mp':
                p=lines[r['antecedent']]['formula'];left=L.Imp(h,p);right=L.Imp(h,L.Imp(p,a))
                k=emit(dict(rule='tautology',formula=L.Imp(left,L.Imp(right,goal))));k=mp(L.Imp(right,goal),mapping[r['antecedent']],k);k=mp(goal,mapping[r['implication']],k)
            elif rule=='generalize':
                x=r['variable'];body=lines[r['source']]['formula']
                if x in L.free(h):raise ValueError('deduction eigenvariable')
                u=L.All(x,L.Imp(h,body));k=emit(dict(rule='generalize',formula=u,variable=x,source=mapping[r['source']]))
                e=emit(dict(rule='distribute',formula=L.Imp(u,goal),variable=x,antecedent=h,consequent=body));k=mp(goal,k,e)
            else:
                k=emit(dict(r));e=emit(dict(rule='tautology',formula=L.Imp(a,goal)));k=mp(goal,k,e)
            mapping[j]=k
        lines=out;premises.pop()
    return lines

def compile_request(proof,target,hypotheses,theory,deduce=False):
    lines,bindings=commands(proof,hypotheses);actual=target;theory=dict(theory,axioms=dict(theory['axioms']))
    if deduce:
        lines=discharge(lines,hypotheses)
        for h in reversed(hypotheses):actual=L.Imp(h,actual)
    elif any(L.free(a) for a in hypotheses):
        # An explicitly checked sequent declaration; the root is only a probe.
        probe=L.Imp(('bot',),('bot',));request=dict(protocol=PROTOCOL,theory=theory,target=probe,blocks=[dict(name='discovered-sequent',premises=hypotheses,conclusion=target,proof=lines)],proof=[dict(rule='tautology',formula=probe)])
        result=check(canonical(request),max_work=None)
        if result['status']!='accepted':raise ValueError(result)
        return dict(request=request,host=result,bindings=bindings,scope='all commands in the discovered open-premise sequent declaration; root is only a probe')
    else:
        for j,a in enumerate(hypotheses):
            name='premise-'+str(j)
            if name in theory['axioms']:raise ValueError('reserved premise name')
            theory['axioms'][name]=a;lines[j]=dict(rule='axiom',formula=a,name=name)
    request=dict(protocol=PROTOCOL,theory=theory,target=actual,blocks=[],proof=lines);result=check(canonical(request),max_work=None,expected_problem_sha256=problem_hash(request))
    if result['status']!='accepted':raise ValueError(result)
    return dict(request=request,host=result,bindings=bindings,scope='fully discharged implication theorem' if deduce else 'closed-premise/theory proof',primitive_lines=len(lines))
