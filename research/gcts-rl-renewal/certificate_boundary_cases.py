"""External assertions and bounds, never an authored proof sequence."""
def theory(functions=None,predicates=None,axioms=None):return dict(functions=functions or {},predicates=predicates or {},axioms=axioms or {},schemas=[])
def cases():
    z=['fun','zero',[]];one=['fun','succ',[z]];x=['var','x'];p=['pred','P',[]];q=['pred','Q',[]]
    eq=['eq',one,one];body=['eq',x,x];chain=theory(predicates=dict(P=0,Q=0),axioms=dict(p=p,pq=['imp',p,q]));a=['fun','a',[]];l=['fun','l',[]];inc=['pred','Inc',[a,l]];point=['pred','Point',[a]];geometry=theory(dict(a=0,l=0),dict(Inc=2,Point=1),dict(inc=inc,typing=['imp',inc,point]))
    def row(id,title,t,target,length,scope,**extra):return dict(id=id,title=title,theory=t,target=target,length=length,scope=scope,**extra)
    return [row('pa-ground-equality','Arithmetic vocabulary: successor reflexivity',theory(dict(zero=0,succ=1)),eq,1,'Logical equality theorem, valid in PA and in every interpretation of these function symbols; no induction or arithmetic axiom is used.'),
      row('pa-universal-equality','Arithmetic vocabulary: universally quantified reflexivity',theory(dict(zero=0,succ=1)),['all','x',body],2,'A two-line quantified equality theorem. No proof, intermediate formula ordering or reference path is supplied.'),
      row('two-premise','Propositional implication from two given premises',chain,q,3,'The two closed premise formulas are assertion inputs. All certificate commands and backward references are searched.'),
      row('incidence-premises','Symbolic incidence: apply a given typing premise',geometry,point,3,'A ground incidence fragment with explicitly given premises. This is not a deduction from the full Hilbert axiom groups or from a drawn configuration.'),
      row('short-envelope','The implication task with a two-line envelope',chain,q,2,'Finite grammar failure or unknown only; never a claim of mathematical unprovability.'),
      row('absent-fact','Absent proposition in a two-line envelope',theory(predicates=dict(P=0,Q=0),axioms=dict(p=p)),q,2,'A negative finite-envelope control, with no implication premise supplied.'),
      row('zero-query','No native query budget',chain,q,3,'The assertion remains unresolved when no native computation can be requested.',queries=0)]
