"""Narrow standalone Skolem reconstruction prototype, not a TSTP proof checker.

This module never changes the published external_prover_check validator.
It verifies a conservative witness extension of one closed NNF formula and a
global reserved-symbol set. Integrating this transformation into a complete
proof DAG with exact inputs and certified logical steps is an outstanding gate.
"""
import re
from external_prover_check import alpha,free,nnf,substitute,symbol_names,validate_signature

def witness_sites(parent):
    """Lexical paths distinguish shadowed/sibling quantifiers independently."""
    if free(parent):raise ValueError('parent must be explicitly closed')
    out=[]
    def walk(f,path,universals):
        h=f[0]
        if h=='forall':walk(f[2],path+(2,),universals+[path])
        elif h=='exists':
            out.append(dict(path=list(path),dependencies=[list(p) for p in universals]))
            walk(f[2],path+(2,),universals)
        elif h in ('and','or'):
            walk(f[1],path+(1,),universals);walk(f[2],path+(2,),universals)
        elif h not in ('lit','top','bot'):raise ValueError('unsupported NNF node')
    walk(nnf(parent),(),[]);return out

def check_extension(parent,child,witnesses,signature,reserved_symbols):
    """Exact scope/shape check; success is NOT local first-order entailment.

    Each existential occurrence gets a different fresh function of exactly the
    surrounding universal variables, in lexical order. The result retains all
    connectives, literals and universal scopes. Alpha renaming is allowed.
    Closed formulas and ordinary untyped FOL only; no simultaneous definitions,
    miniscoping, distribution, or dropping of universal quantifiers is accepted.
    Caller must reserve all original input symbols AND all earlier introductions.
    """
    if set(signature)!={'function_arities','predicate_arities'}:raise ValueError('signature fields')
    if any(type(a) is not int or a<0 for k in signature for a in signature[k].values()):raise ValueError('signature arity')
    declared=set(signature['function_arities'])|set(signature['predicate_arities'])
    if not declared<=set(reserved_symbols):raise ValueError('incomplete original-symbol reservation')
    validate_signature(parent,signature)
    sites=witness_sites(parent)
    if not sites or len(witnesses)!=len(sites):raise ValueError('missing/extra witness occurrence')
    names=[];new={}
    for site,w in zip(sites,witnesses):
        if set(w)!={'path','dependencies','symbol'}:raise ValueError('witness certificate fields')
        paths=[w['path'],*w['dependencies']]
        if any(not isinstance(p,list) or any(type(i) is not int or i not in (1,2) for i in p) for p in paths):raise ValueError('lexical path encoding')
        if w['path']!=site['path'] or w['dependencies']!=site['dependencies']:raise ValueError('wrong scope/dependency order')
        name=w['symbol']
        if not isinstance(name,str) or not re.fullmatch('[a-z][A-Za-z0-9_]*',name):raise ValueError('unsupported witness symbol')
        if name in reserved_symbols or name in names:raise ValueError('witness is not globally fresh')
        names.append(name);new[name]=len(site['dependencies'])
    extended={**signature,'function_arities':{**signature['function_arities'],**new}}
    validate_signature(child,extended)
    if free(child):raise ValueError('child must be explicitly closed')
    by_path={tuple(w['path']):w for w in witnesses};counter=[0]
    def walk(f,path,env,universals):
        h=f[0]
        if h=='forall':
            v=('var','V'+str(counter[0]));counter[0]+=1
            return ('forall',v[1],walk(f[2],path+(2,),{**env,f[1]:v},universals+[v]))
        if h=='exists':
            w=by_path[path];term=('fun',w['symbol'],tuple(universals))
            return walk(f[2],path+(2,),{**env,f[1]:term},universals)
        if h in ('and','or'):return (h,walk(f[1],path+(1,),env,universals),walk(f[2],path+(2,),env,universals))
        if h=='lit':return ('lit',f[1],substitute(f[2],env))
        return f
    expected=walk(nnf(parent),(),{},[])
    if alpha(expected)!=alpha(nnf(child)):raise ValueError('Skolem reconstruction/shape mismatch')
    if symbol_names(child)-declared-set(new):raise ValueError('unaccounted symbol')
    return dict(status='checked_scoped_witness_extension',introduced_functions=new,witnesses=witnesses,
                relation='Every model of the closed parent has an expansion satisfying the child; every child model reduces to a parent model. Other current formulas must mention no newly introduced symbol.',
                integration_status='Standalone transformation only. Complete TSTP DAG/context validation remains unimplemented; no theorem acceptance is issued.')

def check_tstp_proof(*args,**kwargs):
    """Prevent mistaking a tested transformation for a complete proof checker."""
    raise ValueError('full TSTP/context integration is not implemented; proof status unknown')
