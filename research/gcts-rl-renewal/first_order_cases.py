"""Assertions, theories and finite boundaries only; no proof paths or donors."""
def V(x):return ['var',x]
def F(n,*args):return ['fun',n,list(args)]
def P(n,*args):return ['pred',n,list(args)]
def A(x,p):return ['all',x,p]
def I(p,q):return ['imp',p,q]
def E(s,t):return ['eq',s,t]
def case(name,title,functions,predicates,axioms,target,length,scope):
    return dict(id=name,title=title,theory=dict(functions=functions,predicates=predicates,axioms=axioms,schemas=[]),
        target=target,length=length,instantiation_rounds=2,scope=scope)
def cases():
    a,b,c=map(F,('a','b','c'));x,y=map(V,('x','y'))
    return [
        case('quantified-application','Apply a universally quantified implication',dict(a=0),dict(P=1,Q=1),
             dict(universal=A('x',I(P('P',x),P('Q',x))),premise=P('P',a)),P('Q',a),5,
             'First-order implication application; no derived instance is supplied.'),
        case('equality-predicate','Transport a predicate across equality',dict(a=0,b=0),dict(P=1),
             dict(equality=E(a,b),premise=P('P',a)),P('P',b),5,
             'Ground equality operands and an atomic predicate template; no substitution proof is supplied.'),
        case('double-universal','Instantiate two nested quantifiers',dict(a=0,b=0),dict(R=2),
             dict(universal=A('x',A('y',P('R',x,y)))),P('R',a,b),5,
             'Uniform two-round syntax closure; no intermediate quantified formula is supplied.'),
        case('capture-avoiding','Keep a free variable free during instantiation',{},dict(R=2),
             dict(universal=A('x',A('y',P('R',x,y)))),A('fresh0',P('R',y,V('fresh0'))),3,
             'The target uses the native deterministic fresh name. The input gives no proof commands; the term pool follows free target variables.'),
        case('pa-addition-base','Instantiate the Peano addition base axiom',dict(a=0,zero=0,add=2),{},
             dict(add_base=A('x',E(F('add',x,F('zero')),x))),E(F('add',a,F('zero')),a),3,
             'One defining addition axiom, with a named constant. This is an axiom instance, not induction or a full Peano-arithmetic result.'),
        case('hilbert-incidence-typing','Extract point typing from symbolic incidence',dict(A=0,ell=0),dict(Incident=2,Point=1),
             dict(typing=A('x',A('l',I(P('Incident',x,V('l')),P('Point',x)))),incidence=P('Incident',F('A'),F('ell'))),P('Point',F('A')),7,
             'A one-sorted incidence-typing consequence. It is a preparation for Hilbert geometry, with no coordinates or drawing-based inference; it does not establish the full Hilbert axiom system.'),
        case('equality-two-steps','Transport through two equality hypotheses',dict(a=0,b=0,c=0),dict(P=1),
             dict(first=E(a,b),second=E(b,c),premise=P('P',a)),P('P',c),9,
             'Longer compositional target under the same uniform grammar and budget; unresolved searches remain unknown.')]
