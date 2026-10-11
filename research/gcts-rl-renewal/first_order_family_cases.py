"""Theory/target/boundary declarations only; no certificate or proof path."""
from first_order_cases import F,V,P,A,I,E,case

def transport(name,title,names,length,predicate='P',compound=False,disconnect=False):
    functions={n:0 for n in names};terms=[F(n) for n in names]
    if compound:
        functions['wrap']=1;terms=[F('wrap',t) for t in terms]
    axioms={'equality'+str(i):E(terms[i],terms[i+1]) for i in range(len(terms)-1)}
    if disconnect:
        functions['isolated']=0;premise=F('isolated')
    else:premise=terms[0]
    axioms['premise']=P(predicate,premise)
    return case(name,title,functions,{predicate:1},axioms,P(predicate,terms[-1]),length,
                'Closed first-order equality transport. Compound terms and predicate names are symbolic; no explicit geometry or authored proof sequence.')

def promotion():return transport('promote-two-equalities','Discover a dependent two-equality family',['a','b','c'],5)

def training():
    a=F('a');x=V('x')
    return [transport('train-equality','Training: one equality',['a','b'],3),
            case('train-universal','Training: quantified implication',dict(a=0),dict(P=1,Q=1),dict(universal=A('x',I(P('P',x),P('Q',x))),premise=P('P',a)),P('Q',a),3,'Training assertion and boundary only.'),
            transport('train-composition','Training: two equalities',['a','b','c'],5)]

def cases():
    a,b=F('u'),F('v');x=V('x')
    return [
        transport('two-equalities-five','Two equalities in five rows',['u','v','w'],5,'Ready'),
        transport('two-equalities-nine','Two equalities in nine rows',['u','v','w'],9,'Ready'),
        transport('compound-terms-five','Transport a unary predicate on compound terms',['c0','c1','c2'],5,'Stable',True),
        transport('symbolic-points-five','Transport symbolic point typing across equality',['A','B','C'],5,'Point'),
        transport('three-equalities-seven','Compose three equality hypotheses',['d0','d1','d2','d3'],7,'Linked'),
        case('quantifier-equality-five','Compose quantified implication with equality',dict(u=0,v=0),dict(Source=1,Target=1),
             dict(universal=A('x',I(P('Source',x),P('Target',x))),equality=E(a,b),premise=P('Source',a)),P('Target',b),5,
             'A heterogeneous composition of first-order rules. Only theory axioms, target and bounds are inputs.'),
        transport('disconnected-premise-five','A disconnected predicate premise',['n0','n1','n2'],5,'Has',disconnect=True)]
