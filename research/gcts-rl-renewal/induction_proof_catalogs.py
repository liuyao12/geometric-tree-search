"""Goal-derived induction in a complete finite contextual-equation catalog.

No derivation path is input. Every bounded term, axiom direction, occurrence,
unconstrained substitution and fixed induction-hypothesis rewrite is retained.
Base, conditional-step and direct equations coexist as ordinary point tiles.
Generalization is a primitive root inference, never an illicit open-premise
lemma. Induction is a checked two-premise inference, not a post-search tactic.
This goal-oriented grammar is deliberately narrower than unrestricted FOL.
"""
import hashlib,itertools,time
import logic as L
import semantic_proof_catalogs as C
from semantic_proof_tiles import frozen,body_target
from proof_block_search import (Proof,equations,equation,locations,bind,
                               replace_variables,proof_for_path,deduce,fresh,
                               induction_schema)
from serialized_kernel import canonical,check,problem_hash,PROTOCOL

def close(a,variables):
    for x in reversed(variables):a=L.All(x,a)
    return a

def moves(terms,rules):
    allowed=set(terms)
    for before in terms:
        for path,sub in locations(before):
            for r in rules:
                for direction in (1,-1):
                    left,right=r['body'][1:] if direction==1 else r['body'][1:][::-1]
                    env={}
                    if not bind(left,sub,set(r['variables']),env):continue
                    missing=[x for x in r['variables'] if x not in env]
                    for values in itertools.product(terms,repeat=len(missing)):
                        bindings=dict(env,**dict(zip(missing,values)))
                        after=L.replace_at(before,path,replace_variables(right,bindings))
                        if after in allowed and after!=before:
                            yield dict(before=before,after=after,rule=r,bindings=bindings,path=path,direction=direction)

def definition(premises,conclusion,lines):
    pin=hashlib.sha256(canonical([premises,conclusion,lines])).hexdigest()[:24]
    return dict(name='induction-tile-'+pin,premises=premises,conclusion=conclusion,proof=lines)

def conditional_rewrite(original,hypothesis,move):
    before,after=move['before'],move['after']
    p,q=L.Eq(original,before),L.Eq(original,after)
    # Discharge only the fixed hypothesis in the one-edge derivation.
    # Local assumption indices in proof_for_path are never global axioms.
    derived=deduce(proof_for_path(before,[move]),hypothesis)
    out=Proof();input_i=out.emit('assumption',L.Imp(hypothesis,p),index=0)
    edge_i=out.append(derived);edge=L.Eq(before,after)
    hole=fresh(original,before,after)
    substitution=L.Imp(edge,L.Imp(p,q))
    subst_i=out.emit('eq_subst',substitution,variable=hole,template=L.Eq(original,L.V(hole)),left=before,right=after)
    lifted=out.emit('tautology',L.Imp(substitution,L.Imp(L.Imp(hypothesis,edge),L.Imp(hypothesis,L.Imp(p,q)))))
    consequence=out.mp(edge_i,out.mp(subst_i,lifted))
    combine=out.emit('tautology',L.Imp(L.Imp(hypothesis,L.Imp(p,q)),L.Imp(L.Imp(hypothesis,p),L.Imp(hypothesis,q))))
    out.mp(input_i,out.mp(consequence,combine))
    return definition([L.Imp(hypothesis,p)],L.Imp(hypothesis,q),out.lines)

def ordinary_rewrite(original,move):
    before,after=move['before'],move['after'];p,q=L.Eq(original,before),L.Eq(original,after)
    out=Proof();i=out.emit('assumption',p,index=0);edge=out.append(proof_for_path(before,[move]))
    hole=fresh(original,before,after)
    ax=out.emit('eq_subst',L.Imp(L.Eq(before,after),L.Imp(p,q)),variable=hole,template=L.Eq(original,L.V(hole)),left=before,right=after)
    out.mp(i,out.mp(edge,ax))
    return definition([p],q,out.lines)

def induction_definition(variables,body,x):
    parameters=[v for v in variables if v!=x]
    base=L.substitute(body,x,L.F('zero'))
    step=L.All(x,L.Imp(body,L.substitute(body,x,L.F('succ',L.V(x)))))
    premises=[close(base,parameters),close(step,parameters)]
    target=close(body,variables);out=Proof()
    sources=[out.emit('assumption',a,index=i) for i,a in enumerate(premises)]
    for i,a in enumerate(premises):
        for v in parameters:
            instance=L.substitute(a[2],a[1],L.V(v))
            ax=out.emit('instantiate',L.Imp(a,instance),universal=a,term=L.V(v))
            sources[i]=out.mp(sources[i],ax);a=instance
    both=('and',base,step)
    ax=out.emit('tautology',L.Imp(base,L.Imp(step,both)))
    both_i=out.mp(sources[1],out.mp(sources[0],ax))
    schema=induction_schema(x,body)
    schema_i=out.emit('induction',schema,variable=x,template=body)
    for v in sorted(L.free(body)-{x}):
        instance=L.substitute(schema[2],schema[1],L.V(v))
        ax=out.emit('instantiate',L.Imp(schema,instance),universal=schema,term=L.V(v))
        schema_i=out.mp(schema_i,ax);schema=instance
    result=out.mp(both_i,schema_i)
    # Restore the external quantifier order even when induction selected an
    # outer variable. Closed local premises permit these generalizations.
    a=L.All(x,body)
    ax=out.emit('instantiate',L.Imp(a,body),universal=a,term=L.V(x));result=out.mp(result,ax)
    for v in reversed(variables):result=out.emit('generalize',L.All(v,out.lines[result]['formula']),variable=v,source=result)
    return definition(premises,target,out.lines)

def catalog(theory,target,term_bound,enable_induction=True):
    began=time.perf_counter();variables,body=body_target(target)
    if body[0]!='eq' or len(set(variables))!=len(variables) or L.free(body)-set(variables):
        raise ValueError('closed, distinctly quantified equational target required')
    terms=C.term_grammar(theory['functions'],variables,term_bound)
    axiom_rules=equations(theory);axiom_moves=tuple(moves(terms,axiom_rules))
    contexts=[dict(original=body[1],hypothesis=None,goal=body,closure=variables,kind='direct',variable=None)]
    induction=[]
    if enable_induction and 'nat-induction' in theory['schemas']:
        for x in variables:
            base=L.substitute(body,x,L.F('zero'));step=L.substitute(body,x,L.F('succ',L.V(x)))
            others=[v for v in variables if v!=x]
            contexts.extend([dict(original=base[1],hypothesis=None,goal=base,closure=others,kind='base',variable=x),
                             dict(original=step[1],hypothesis=body,goal=L.Imp(body,step),closure=others+[x],kind='step',variable=x)])
            induction.append((x,induction_definition(variables,body,x)))
    fs=set();rules=[];defs=[];descriptions=[];seen=set()
    def add(inputs,a,recipe):
        key=canonical([inputs,a,recipe])
        if key in seen:return
        seen.add(key);fs.add(a);fs.update(inputs);rules.append((inputs,a,recipe))
        if recipe['kind']=='block':defs.append(recipe['definition'])
    for context in contexts:
        original,hypothesis=context['original'],context['hypothesis']
        if original not in terms:raise ValueError('required starting term outside finite grammar')
        wrap=lambda a:L.Imp(hypothesis,a) if hypothesis is not None else a
        for t in terms:fs.add(wrap(L.Eq(original,t)))
        reflex=L.Eq(original,original);seed=wrap(reflex)
        if hypothesis is None:add([],seed,dict(kind='primitive',witness=dict(rule='refl',formula=seed)))
        else:
            out=Proof();i=out.emit('refl',reflex);ax=out.emit('tautology',L.Imp(reflex,seed));out.mp(i,ax)
            add([],seed,dict(kind='block',definition=definition([],seed,out.lines),operation='conditional-reflexivity'))
        available=axiom_moves
        if hypothesis is not None:
            h=equation('fixed-induction-hypothesis',hypothesis,'assumption',index=0)
            available=axiom_moves+tuple(moves(terms,(h,)))
        descriptions.append(dict(context,move_count=len(available)))
        for move in available:
            p,q=[wrap(L.Eq(original,t)) for t in (move['before'],move['after'])]
            b=conditional_rewrite(original,hypothesis,move) if hypothesis is not None else ordinary_rewrite(original,move)
            add([p],q,dict(kind='block',definition=b,operation='conditional-rewrite' if hypothesis is not None else 'rewrite',context=dict(context),move={k:move[k] for k in ('before','after','bindings','path','direction')},axiom=move['rule']['name']))
        a=context['goal'];fs.add(a)
        for x in reversed(context['closure']):
            q=L.All(x,a);add([a],q,dict(kind='primitive',witness=dict(rule='generalize',formula=q,variable=x,source=0)));a=q
    for x,b in induction:add(b['premises'],b['conclusion'],dict(kind='block',definition=b,operation='induction',variable=x))
    defs=list({b['name']:b for b in defs}.values())
    probe=dict(protocol=PROTOCOL,theory=theory,target=L.Imp(frozen(target),frozen(target)),blocks=defs,proof=[dict(rule='tautology',formula=L.Imp(frozen(target),frozen(target)))])
    start=time.perf_counter();checked=check(canonical(probe),expected_problem_sha256=problem_hash(probe),max_work=None,max_bytes=200000000)
    if checked['status']!='accepted':raise ValueError(('entire induction inventory rejected',checked))
    validation=time.perf_counter()-start
    result=C.catalog(theory,frozen(target),fs,rules,configuration=dict(kind='goal-derived-conditional-induction-equations',term_bound=term_bound,terms=len(terms),variables=variables,enable_induction=enable_induction,contexts=descriptions,induction_variables=[x for x,b in induction],derived_rules=len(defs),templates='external target body only; every quantified target variable is an induction alternative; no supplied derivation or selected variable'))
    result.update(build_seconds=time.perf_counter()-began,validation_seconds=validation,inventory_check=checked)
    return result
