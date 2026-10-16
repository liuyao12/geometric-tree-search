"""Generic quantified/context inference blocks for the unchanged FOL kernel.

Generalization of a free theorem is a root primitive tile. A block may only
generalize an eigenvariable absent from its open input formulas. Existential
notation is not-all-not. No logical/geometric axiom is added by these rules.
"""
import hashlib
import logic as L
from proof_block_search import Proof
from serialized_kernel import canonical
from euclidean_proof_tiles import consume

def exists(x,p):return L.Not(L.All(x,L.Not(p)))
def both(p,q):return ('and',p,q)
def block(inputs,q,lines):
    name='quantifier-'+hashlib.sha256(canonical([inputs,q,lines])).hexdigest()[:24]
    return dict(name=name,premises=inputs,conclusion=q,proof=lines)
def propositional(inputs,q):
    ax=q
    for p in reversed(inputs):ax=L.Imp(p,ax)
    if not L.tautology(ax):raise ValueError('not a propositional inference')
    out=Proof();indices=[out.emit('assumption',a,index=i) for i,a in enumerate(inputs)]
    j=out.emit('tautology',ax)
    for i in indices:j=out.mp(i,j)
    return block(inputs,q,out.lines)
def exists_intro(context,x,p,term):
    instance=L.substitute(p,x,term);input=L.Imp(context,instance);q=L.Imp(context,exists(x,p))
    out=Proof();i=out.emit('assumption',input,index=0)
    u=L.All(x,L.Not(p));inst=L.Imp(u,L.substitute(L.Not(p),x,term))
    j=out.emit('instantiate',inst,universal=u,term=term)
    edge=L.Imp(instance,exists(x,p));k=out.emit('tautology',L.Imp(inst,edge));j=out.mp(j,k)
    k=out.emit('tautology',L.Imp(edge,L.Imp(context,edge)));j=out.mp(j,k)
    consume(out,context,j,i)
    return block([input],q,out.lines)
def forall_distribute(context,x,q):
    if x in L.free(context):raise ValueError('eigenvariable occurs in context')
    input=L.All(x,L.Imp(context,q));target=L.Imp(context,L.All(x,q))
    out=Proof();i=out.emit('assumption',input,index=0)
    j=out.emit('distribute',L.Imp(input,target),variable=x,antecedent=context,consequent=q);out.mp(i,j)
    return block([input],target,out.lines)
def forall_scope(context,x,p,q):
    if x in L.free(context):raise ValueError('eigenvariable occurs in context')
    body=L.Imp(both(context,p),q);input=L.All(x,body);target=L.Imp(context,L.All(x,L.Imp(p,q)))
    out=Proof();i=out.emit('assumption',input,index=0)
    inst=out.emit('instantiate',L.Imp(input,body),universal=input,term=L.V(x));j=out.mp(i,inst)
    curried=L.Imp(context,L.Imp(p,q));k=out.emit('tautology',L.Imp(body,curried));j=out.mp(j,k)
    quantified=L.All(x,curried);j=out.emit('generalize',quantified,variable=x,source=j)
    k=out.emit('distribute',L.Imp(quantified,target),variable=x,antecedent=context,consequent=L.Imp(p,q));out.mp(j,k)
    return block([input],target,out.lines)
def exists_eliminate(context,x,p,q):
    if x in L.free(context)|L.free(q):raise ValueError('witness escapes its context or conclusion')
    body=L.Imp(both(context,p),q);input=L.All(x,body);target=L.Imp(context,L.Imp(exists(x,p),q))
    out=Proof();i=out.emit('assumption',input,index=0)
    j=out.emit('instantiate',L.Imp(input,body),universal=input,term=L.V(x));j=out.mp(i,j)
    r=L.Imp(context,q);contraposed=L.Imp(L.Not(r),L.Not(p))
    k=out.emit('tautology',L.Imp(body,contraposed));j=out.mp(j,k)
    universal=L.All(x,contraposed);j=out.emit('generalize',universal,variable=x,source=j)
    implication=L.Imp(L.Not(r),L.All(x,L.Not(p)))
    k=out.emit('distribute',L.Imp(universal,implication),variable=x,antecedent=L.Not(r),consequent=L.Not(p));j=out.mp(j,k)
    k=out.emit('tautology',L.Imp(implication,target));out.mp(j,k)
    return block([input],target,out.lines)
def forall_instantiate(context,x,p,term):
    input=L.Imp(context,L.All(x,p));q=L.Imp(context,L.substitute(p,x,term));out=Proof()
    i=out.emit('assumption',input,index=0);edge=L.Imp(L.All(x,p),L.substitute(p,x,term))
    j=out.emit('instantiate',edge,universal=L.All(x,p),term=term)
    k=out.emit('tautology',L.Imp(edge,L.Imp(context,edge)));j=out.mp(j,k);consume(out,context,j,i)
    return block([input],q,out.lines)
