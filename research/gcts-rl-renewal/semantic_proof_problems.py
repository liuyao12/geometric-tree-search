"""External statements, theories and declared finite search bounds; no proofs."""
import logic as L

def theory(functions=None,predicates=None,axioms=None):
    return dict(functions=functions or {},predicates=predicates or {},axioms=axioms or {},schemas=[])
def addition():
    x,y=L.V('x'),L.V('y');z=L.F('zero');s=lambda a:L.F('succ',a);a=lambda p,q:L.F('add',p,q)
    return theory(dict(zero=0,succ=1,add=2),{},dict(AZ=L.All('x',L.Eq(a(x,z),x)),AS=L.All('x',L.All('y',L.Eq(a(x,s(y)),s(a(x,y)))))))
def statements():
    p,q,r,t=[('pred',x,()) for x in ('P','Q','R','T')];preds=dict(P=0,Q=0,R=0,T=0)
    chain=theory(predicates=preds,axioms=dict(given=p,pq=L.Imp(p,q),qr=L.Imp(q,r)))
    def row(id,label,theory,target,length,kind='fol',**config):return dict(id=id,label=label,theory=theory,target=target,length=length,kind=kind,configuration=config)
    out=[row('chain-2','Two implication steps',chain,r,5),row('chain-too-short','Same theorem; one cell too short',chain,r,4),
         row('join','Two premises joined',theory(predicates=preds,axioms=dict(p=p,q=q,join=L.Imp(p,L.Imp(q,r)))),r,5),
         row('absent-fact','Absent fact control',theory(predicates=preds,axioms=dict(p=p)),t,3),
         row('generalization','Equality generalization',theory(dict(c=0),{}),L.All('x',L.Eq(L.V('x'),L.V('x'))),2)]
    c,d=L.F('c'),L.F('d');f=lambda a:L.F('f',a);x=L.V('x');px=('pred','P',(x,))
    out.extend([row('instantiation','Universal instantiation',theory(dict(c=0,f=1),dict(P=1),dict(universal=L.All('x',px))),('pred','P',(f(c),)),3,rounds=1),
                row('congruence','Equality through a function',theory(dict(c=0,d=0,f=1),{},dict(equal=L.Eq(c,d))),L.Eq(f(c),f(d)),5,rounds=1)])
    z=L.F('zero');s=lambda a:L.F('succ',a);a=lambda p,q:L.F('add',p,q)
    def numeral(n):
        v=z
        for _ in range(n):v=s(v)
        return v
    for left,right in ((1,1),(2,1),(1,2),(2,2)):
        target=L.Eq(a(numeral(left),numeral(right)),numeral(left+right));bound=left+right+3
        out.append(row(f'add-{left}-{right}',f'Addition {left} + {right}',addition(),target,right+2,'equational',term_bound=bound))
    parameter=L.V('a');out.append(row('add-one-universal','Addition by one, universally quantified',addition(),L.All('a',L.Eq(a(parameter,s(z)),s(parameter))),3,'equational',term_bound=5))
    # Reverse variable-erasing equations are included by enumerating the
    # unconstrained substitution, rather than silently excluding that direction.
    y=L.V('y');m=lambda p,q:L.F('mul',p,q);arith=addition();arith['functions']['mul']=2
    arith['axioms'].update(MZ=L.All('x',L.Eq(m(x,z),z)),MS=L.All('x',L.All('y',L.Eq(m(x,s(y)),a(m(x,y),x)))))
    out.append(row('mul-one','Multiplication of one by one',arith,L.Eq(m(s(z),s(z)),s(z)),5,'equational',term_bound=7))
    return out
