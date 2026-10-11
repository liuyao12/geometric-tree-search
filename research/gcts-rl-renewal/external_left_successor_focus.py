"""Bounded, generic syntactic instantiation; exact refutation replay remains required.

This extends certificate SEARCH, not inference semantics. Clauses are obtained
by the unchanged polarity-correct first-order clausifier. Every proposed ground
clause is an exact universal instance; satisfiable finite samples remain unknown.
No E rule label, target theorem or target proof sequence is used by this code.
"""
import copy,itertools,time
import external_induction_tstp_check as base
from external_prover_check import (
    alpha,atom_terms,clauses_from,closed,free,nnf,refute,replay_refutation,substitute,
)
from external_prover_inputs import canonical,sha

MAX_ROUNDS=5
MAX_INSTANCES=4000
MAX_TERMS=600

def freeze(x):
    return tuple(freeze(a) for a in x) if isinstance(x,list) else x

def variables(c):
    return sorted(set().union(*(free(a) for sign,a in c)))

def ground_clause(c,env):
    vs=variables(c)
    if set(env)!=set(vs):raise ValueError('ground instance omits or adds a universal')
    for term in env.values():
        if not isinstance(term,tuple) or term[0]!='fun' or free(term):
            raise ValueError('ground instance contains a variable or malformed term')
    g=frozenset((s,substitute(a,env)) for s,a in c)
    if any((not s,a) in g for s,a in g):return None
    return tuple(sorted(g,key=repr))

def match(pattern,term,env):
    """One-way matching, with repeated variables checked exactly; no unification."""
    h=pattern[0]
    if h=='var':
        old=env.get(pattern[1])
        if old is not None:return env if old==term else None
        return {**env,pattern[1]:term}
    if h!=term[0]:return None
    if h=='fun':
        if pattern[1]!=term[1] or len(pattern[2])!=len(term[2]):return None
        for a,b in zip(pattern[2],term[2]):
            env=match(a,b,env)
            if env is None:return None
        return env
    raise ValueError('unsupported matching term')

def replay_instances(parents,child,certificate):
    """Reconstruct the original clausal theory and EACH exact finite instance.

    Uses direct syntax reconstruction independent of the proposal generator and
    the old solver's separate equality relation closure for every refutation leaf.
    Original reserved namespace clashes are rejected rather than silently renamed.
    """
    fs=[closed(f) for f in parents]+[('not',closed(child))]
    from external_prover_check import symbol_names
    if any(n.startswith('__checker_') for f in fs for n in symbol_names(f)):
        raise ValueError('reserved internal witness namespace collision')
    clauses,skolem=clauses_from(fs)
    if canonical(clauses)!=canonical(certificate['universal_clauses']) or canonical(skolem)!=canonical(certificate['internal_witnesses']):
        raise ValueError('polarity/scope-correct clausal preprocessing binding')
    if certificate['input_sha256']!=sha(canonical(fs)):
        raise ValueError('exact logical relation binding')
    signature={}
    def signatures(t):
        if t[0]=='fun':
            if t[1] in signature and signature[t[1]]!=len(t[2]):raise ValueError('source signature arity conflict')
            signature[t[1]]=len(t[2])
            for a in t[2]:signatures(a)
        elif t[0]=='pred':
            for a in t[2]:signatures(a)
        elif t[0]not in('var','top','bot'):
            for a in t[1:]:
                if isinstance(a,tuple):signatures(a)
    for f in fs:signatures(f)
    for name,arity in skolem:
        if name in signature:raise ValueError('internal witness freshness')
        signature[name]=arity
    signature['__checker_nonempty']=0
    cs=[];seen=set()
    for e in certificate['instances']:
        index=e['clause']
        if type(index)is not int or not 0<=index<len(clauses):raise ValueError('instance source index')
        c=clauses[index];env={v:freeze(t) for v,t in e['substitution'].items()}
        vs=set().union(*(free(a) for s,a in c))
        if set(env)!=vs:raise ValueError('independent complete substitution domain')
        def term(t):
            if not isinstance(t,tuple) or len(t)!=3 or t[0]!='fun' or not isinstance(t[1],str) or not isinstance(t[2],tuple):
                raise ValueError('independent ground term syntax')
            if signature.get(t[1])!=len(t[2]):raise ValueError('unproven introduced instantiation term or wrong arity')
            for a in t[2]:term(a)
        for t in env.values():term(t)
        def replace(t):
            if t[0]=='var':
                if t[1] not in env:raise ValueError('unassigned universal')
                return env[t[1]]
            if t[0]=='fun':return ('fun',t[1],tuple(replace(a) for a in t[2]))
            if t[0]=='eq':return ('eq',replace(t[1]),replace(t[2]))
            if t[0]=='pred':return ('pred',t[1],tuple(replace(a) for a in t[2]))
            raise ValueError('unsupported independent clause atom')
        g=set((s,replace(a)) for s,a in c)
        if any((not s,a) in g for s,a in g):raise ValueError('tautological instance is not part of saved ground census')
        g=tuple(sorted(g,key=repr))
        if canonical(g)!=canonical(e['ground_clause']):raise ValueError('altered instance substitution or clause')
        if g in seen:raise ValueError('duplicate saved ground clause')
        seen.add(g);cs.append(g)
    if cs!=sorted(cs,key=repr) or len(cs)>MAX_INSTANCES:raise ValueError('saved instance census/order')
    proof=copy.deepcopy(certificate['refutation']);proof['atoms']=[freeze(a) for a in proof['atoms']]
    if proof['status']!='refuted':raise ValueError('finite sample is not an actual refutation')
    replay_refutation(cs,proof)
    return True

def focused(parents,child):
    fs=[closed(f) for f in parents]+[('not',closed(child))]
    # The unchanged internal witness constructor owns this reserved namespace.
    from external_prover_check import symbol_names
    if any(n.startswith('__checker_') for f in fs for n in symbol_names(f)):
        raise ValueError('reserved internal witness namespace collision')
    clauses,skolem=clauses_from(fs)
    initial=set()
    for c in clauses:
        for s,a in c:initial.update(t for t in atom_terms(a) if not free(t))
    constants={t for t in initial if not t[2]}
    if not constants:constants={('fun','__checker_nonempty',())}
    # Counterexample constants and original constants seed every universal,
    # without selecting an induction parameter or a proof path.
    seeds=sorted(constants,key=repr);items={};terms=set(initial)|constants
    def add(i,env):
        c=ground_clause(clauses[i],env)
        if c is None or c in items:return False
        if len(items)>=MAX_INSTANCES:raise ValueError('focused finite instance budget')
        items[c]=dict(clause=i,substitution=env,ground_clause=c)
        for s,a in c:terms.update(atom_terms(a))
        if len(terms)>MAX_TERMS:raise ValueError('focused finite term budget')
        return True
    for i,c in enumerate(clauses):
        vs=variables(c)
        if not vs:add(i,{})
        elif len(c)!=1:
            if len(seeds)**len(vs)>MAX_INSTANCES:raise ValueError('focused seed product budget')
            for values in itertools.product(seeds,repeat=len(vs)):add(i,dict(zip(vs,values)))
    history=[]
    for round_index in range(MAX_ROUNDS):
        changed=False
        # Exact syntactic matches on NONVARIABLE sides of clause equalities.
        # Unmatched universals use the fixed seed constants. This is an incomplete
        # certificate search heuristic; it never declares a finite model complete.
        targets=sorted(terms,key=repr)
        for i,c in enumerate(clauses):
            vs=variables(c)
            if not vs:continue
            for sign,a in c:
                if a[0]!='eq':continue
                for pattern in a[1:]:
                    if pattern[0]=='var':continue
                    for t in targets:
                        env=match(pattern,t,{})
                        if env is None:continue
                        missing=sorted(set(vs)-set(env))
                        for values in itertools.product(seeds,repeat=len(missing)):
                            changed=add(i,{**env,**dict(zip(missing,values))}) or changed
        cs=sorted(items,key=repr)
        proof=refute(cs)
        history.append(dict(round=round_index,instances=len(cs),terms=len(terms),status=proof['status'],nodes=proof['nodes']))
        if proof['status']=='refuted':
            certificate=dict(method='focused_exact_universal_instances',input_sha256=sha(canonical(fs)),universal_clauses=clauses,internal_witnesses=skolem,instances=[items[c] for c in cs],refutation=proof,history=history,bounds=dict(rounds=MAX_ROUNDS,instances=MAX_INSTANCES,terms=MAX_TERMS))
            replay_instances(parents,child,certificate)
            return certificate
        if not changed:break
    raise ValueError('focused finite universal instances remain unrefuted')

@base.bounded_step
def consequence(parents,child):
    began=time.perf_counter();parents=[closed(f) for f in parents];child=closed(child)
    p=base.proposition(parents,child)
    if p['check']['status']=='checked':certificate=p
    else:
        same=next((i for i,f in enumerate(parents) if alpha(nnf(f))==alpha(nnf(child))),None)
        if same is not None:certificate=dict(method='exact_alpha_NNF_equivalence',parent=same,normal_form=alpha(nnf(child)))
        else:certificate=focused(parents,child)
    return dict(status='checked',seconds=time.perf_counter()-began,certificate=certificate)

ORIGINAL_REPLAY=base.replay_consequence
@base.bounded_step
def replay_consequence(parents,child,result):
    if result.get('status')!='checked':raise ValueError('unaccepted focused consequence')
    if result['certificate']['method']=='focused_exact_universal_instances':
        return replay_instances(parents,child,result['certificate'])
    return ORIGINAL_REPLAY(parents,child,result)

def check_output(output,mapping,input_path,saved=None):
    """Reuse the unchanged exact-input/context/Skolem envelope.

    The bounded worker is single-threaded for logic. The temporary module binding
    chooses the new certificate search/replay functions without editing old files.
    """
    original=(base.consequence,base.replay_consequence)
    base.consequence,base.replay_consequence=consequence,replay_consequence
    try:return base.check_output(output,mapping,input_path,saved=saved)
    finally:base.consequence,base.replay_consequence=original
