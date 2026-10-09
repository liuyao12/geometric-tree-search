"""Witness-free syntax envelopes and authored sound semantic rule compilation.

Theory/target syntax and finite bounds are inputs; no searched derivation,
stored policy, earlier theorem witness or theorem-specific proof skeleton is
read. The FOL closure is an explicit specialized envelope, not a fair grammar.
The equational term grammar is exhaustive within its declared node bound.
"""
import hashlib,itertools,time
import logic as L
from kernel_machine import Catalog,size
from proof_block_search import Proof,equations,proof_for_path,fresh,locations,bind,replace_variables
from serialized_kernel import canonical,check,problem_hash,PROTOCOL
from semantic_proof_tiles import body_target,frozen

def signature(theory):return L.Kernel(theory['functions'],theory['predicates'],theory['axioms'])
def catalog(theory,target,formulas,rules,close=(),configuration=None):
    fs=tuple(sorted(set(formulas),key=repr));index={a:i for i,a in enumerate(fs)};out=[]
    for inputs,a,recipe in rules:out.append(dict(inputs=[index[p] for p in inputs],output=index[a],recipe=recipe))
    for a in fs:out.append(dict(inputs=[index[a]],output=index[a],recipe=dict(kind='copy')))
    return dict(theory=theory,target=target,target_id=index[body_target(target)[1] if close else frozen(target)],formulas=fs,rules=out,close_variables=list(close),configuration=configuration or {})
def components(formulas):
    fs=set();ts=set();names=set()
    def term(t):
        ts.add(t)
        if t[0]=='var':names.add(t[1])
        else:
            for a in t[2]:term(a)
    def formula(a):
        if a in fs:return
        fs.add(a)
        if a[0]=='all':names.add(a[1]);formula(a[2])
        elif a[0] in ('imp','and','or'):formula(a[1]);formula(a[2])
        elif a[0]=='not':formula(a[1])
        elif a[0]=='eq':term(a[1]);term(a[2])
        elif a[0]=='pred':
            for t in a[2]:term(t)
    for a in formulas:formula(frozen(a))
    return fs,ts,names
def replace_term(a,path,replacement):
    if not path:return replacement
    xs=list(a);xs[path[0]]=replace_term(xs[path[0]],path[1:],replacement);return tuple(xs)
def term_locations(a,path=()):
    if isinstance(a,tuple):
        if a and a[0] in ('var','fun'):yield path,a
        for i,x in enumerate(a):
            if isinstance(x,tuple):yield from term_locations(x,path+(i,))
def fol(theory,target,rounds=2,max_formula_nodes=80):
    began=time.perf_counter();k=signature(theory);fs,ts,names=components(list(theory['axioms'].values())+[target]);hole='semanticHole'
    while hole in names:hole+='X'
    templates={replace_term(a,p,L.V(hole)) for a in fs for p,t in term_locations(a)};variables=sorted(names|{hole});terms=sorted(ts,key=repr)
    for _ in range(rounds):
        new=set()
        for a in fs:
            if a[0]=='all':
                for t in terms:new.add(L.Imp(a,L.substitute(a[2],a[1],t)))
                if a[2][0]=='imp' and a[1] not in L.free(a[2][1]):new.add(L.Imp(a,L.Imp(a[2][1],L.All(a[1],a[2][2]))))
            if a[0]=='eq':
                for template in templates:new.add(L.Imp(a,L.Imp(L.substitute(template,hole,a[1]),L.substitute(template,hole,a[2]))))
        new.update(L.Eq(t,t) for t in terms)
        fs.update(a for a in new if size(a)<=max_formula_nodes);fs=components(fs)[0]
    c=Catalog(k,sorted(fs,key=repr),terms,variables,sorted(templates,key=repr));rules=[([c.formulas[j] for j in r.premises],c.formulas[r.conclusion],dict(kind='primitive',witness=r.witness)) for r in c.inferences]
    result=catalog(theory,frozen(target),c.formulas,rules,configuration=dict(kind='subformula-and-schema-FOL-closure',rounds=rounds,max_formula_nodes=max_formula_nodes,terms=terms,variables=variables,templates=sorted(templates,key=repr)))
    result['build_seconds']=time.perf_counter()-began;return result
def partitions(n,k):
    if k==0:
        if n==0:yield ()
        return
    for i in range(1,n-k+2):
        for rest in partitions(n-i,k-1):yield (i,)+rest
def term_grammar(functions,variables,bound):
    layers={};leafs=[L.V(x) for x in variables]+[L.F(f) for f,n in sorted(functions.items()) if n==0]
    layers[1]=set(leafs)
    for n in range(2,bound+1):
        layer=set()
        for f,arity in sorted(functions.items()):
            if not arity:continue
            for pieces in partitions(n-1,arity):
                for args in itertools.product(*(layers[p] for p in pieces)):layer.add(L.F(f,*args))
        layers[n]=layer
    return tuple(sorted(set().union(*layers.values()),key=repr))
def equational(theory,target,term_bound):
    began=time.perf_counter();close,body=body_target(target)
    if body[0]!='eq':raise ValueError('equational target required')
    ts=term_grammar(theory['functions'],close,term_bound);original,desired=body[1:]
    if original not in ts or desired not in ts:raise ValueError('target outside term bound')
    fs=[L.Eq(original,t) for t in ts];rs=equations(theory);rules=[([],L.Eq(original,original),dict(kind='primitive',witness=dict(rule='refl',formula=L.Eq(original,original))))];definitions=[]
    moves=[];term_set=set(ts)
    for before in ts:
        for path,sub in locations(before):
            for r in rs:
                for direction in (1,-1):
                    left,right=r['body'][1:] if direction==1 else r['body'][1:][::-1];env={}
                    if not bind(left,sub,set(r['variables']),env):continue
                    missing=[x for x in r['variables'] if x not in env]
                    for values in itertools.product(ts,repeat=len(missing)):
                        bindings=dict(env,**dict(zip(missing,values)))
                        after=L.replace_at(before,path,replace_variables(right,bindings))
                        if after in term_set and after!=before:moves.append(dict(before=before,after=after,rule=r,bindings=bindings,path=path,direction=direction))
    for move in moves:
            before=move['before']
            after=move['after'];p=L.Eq(original,before);q=L.Eq(original,after);builder=Proof();input_i=builder.emit('assumption',p,index=0);edge_i=builder.append(proof_for_path(before,[move]));edge=L.Eq(before,after);hole=fresh(original,before,after);template=L.Eq(original,L.V(hole))
            s=builder.emit('eq_subst',L.Imp(edge,L.Imp(p,q)),variable=hole,template=template,left=before,right=after);builder.mp(input_i,builder.mp(edge_i,s))
            name='semantic-rewrite-'+hashlib.sha256(canonical([p,q,move['rule']['name'],move['bindings'],move['path'],move['direction']])).hexdigest()[:20]
            b=dict(name=name,premises=[p],conclusion=q,proof=builder.lines);definitions.append(b);rules.append(([p],q,dict(kind='block',definition=b,move={key:move[key] for key in ('before','after','bindings','path','direction')},axiom=move['rule']['name'])))
    # Every compiled type is validated before point search. No proof path is
    # used to select, trim or seed this complete bounded rule inventory.
    probe=dict(protocol=PROTOCOL,theory=theory,target=L.Imp(frozen(target),frozen(target)),blocks=definitions,proof=[dict(rule='tautology',formula=L.Imp(frozen(target),frozen(target)))])
    before=time.perf_counter();checked=check(canonical(probe),expected_problem_sha256=problem_hash(probe),max_work=None,max_bytes=100000000)
    if checked['status']!='accepted':raise ValueError(('compiled semantic inventory rejected',checked))
    result=catalog(theory,frozen(target),fs,rules,close,dict(kind='complete-bounded-contextual-equations',term_bound=term_bound,terms=len(ts),axiom_names=[r['name'] for r in rs],derived_rules=len(definitions),substitutions='all quantified-variable substitutions from the bounded term grammar; both directions, every term position, nonidentity endpoints inside the grammar'))
    result['inventory_check']=checked;result['validation_seconds']=time.perf_counter()-before;result['build_seconds']=time.perf_counter()-began;return result
