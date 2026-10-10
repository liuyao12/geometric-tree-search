"""Statements, signatures and finite envelopes; no proof sequences."""
import logic as L

def registry():
    x,y,u=L.V('x'),L.V('y'),L.V('u');pred=lambda n,*ts:('pred',n,ts)
    p,q=pred('P',x),pred('Q',x);h=(L.All('x',L.Imp(p,q)),L.All('x',p));target=L.All('x',q)
    empty=lambda ps:dict(functions={},predicates=ps,axioms={},schemas=[])
    def case(name,title,theory,hyp,target,length,terms=(x,y),variables=('x','y'),generalization_rounds=1):
        return dict(id=name,title=title,theory=theory,hypotheses=hyp,target=target,length=length,terms=terms,variables=variables,rounds=2,generalization_rounds=generalization_rounds)
    out=[case('universal-mp','Universal modus ponens',empty(dict(P=1,Q=1)),h,target,4),
         case('ambient-y','Generalize x with an open y hypothesis',empty(dict(P=1,Q=1,S=1)),h+(pred('S',y),),target,4),
         case('scope-reject','An open P(x) cannot be generalized',empty(dict(P=1)),(p,),L.All('x',p),1)]
    relation=pred('R',x,y);universal=L.All('x',L.Not(L.All('y',L.Not(relation))))
    hygienic=L.Not(L.All('fresh0',L.Not(pred('R',y,L.V('fresh0')))));naive=L.Not(L.All('y',L.Not(pred('R',y,y))))
    out+=[case('capture-safe','Instantiate while renaming a bound variable',empty(dict(R=2)),(universal,),hygienic,1),
          case('capture-reject','The captured diagonal is not a valid instance',empty(dict(R=2)),(universal,),naive,1)]
    z=L.F('zero');a=L.F('add',x,z);pa=L.Eq(a,x);qa=L.Eq(L.F('succ',a),L.F('succ',x))
    arithmetic=dict(functions=dict(zero=0,add=2,succ=1),predicates={},axioms={'add-zero':L.All('x',pa),'succ-congruence':L.All('x',L.All('y',L.Imp(L.Eq(x,y),L.Eq(L.F('succ',x),L.F('succ',y)))))},schemas=[])
    out.append(case('arithmetic','Successor preserves addition by zero',arithmetic,(),L.All('x',qa),7,terms=(x,y,a)))
    incidence=pred('Inc',x,u);point=pred('Point',x);line=pred('Line',u)
    geometry=dict(functions={},predicates=dict(Inc=2,Point=1,Line=1),axioms={'incidence-typed':L.All('x',L.All('u',L.Imp(incidence,('and',point,line))))},schemas=[])
    out.append(case('hilbert-typing','Reverse the quantifiers in incidence point typing',geometry,(),L.All('u',L.All('x',L.Imp(incidence,point))),6,terms=(x,u),variables=('x','u'),generalization_rounds=2))
    gh=(L.All('x',L.Imp(incidence,point)),L.All('x',incidence))
    out.append(case('geometry-family','Reuse universal inference with symbolic incidence',empty(dict(Inc=2,Point=1)),gh,L.All('x',point),4,terms=(x,u),variables=('x','u')))
    return out,dict(arithmetic=dict(P=pa,Q=qa),geometry=dict(P=incidence,Q=point))
