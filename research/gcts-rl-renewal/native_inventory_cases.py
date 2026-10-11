"""Separate assertion inputs for inventory donors and frozen evaluation."""
import copy
from certificate_boundary_cases import theory
from native_receptor_cases import cases as original
def donors():return [copy.deepcopy(original()[j]) for j in (2,6,1)]
def chain(n,names,identifier):
    atoms=[['pred',name,[]] for name in names];axioms={'seed':atoms[0]}
    # Names deliberately put the later implication before the starting fact.
    for i in range(n):axioms['edge'+str(n-i)]=['imp',atoms[i],atoms[i+1]]
    return dict(id=identifier,title=str(n)+' implication links with new receptor names',theory=theory(predicates={name:0 for name in names},axioms=axioms),target=atoms[-1],length=2*n+1,scope='Given implication premises, excluded from policy training and donor mining. No command sequence or reference path is supplied.')
def evaluation():
    rows=[chain(3,['Zulu','Alpha','Theta','Beta'],'renamed-three'),chain(4,['Kappa','Eta','Delta','Omega','Gamma'],'four-links')]
    a=['fun','a',[]];l=['fun','l',[]];inc=['pred','Inc',[a,l]];point=['pred','Point',[a]];obj=['pred','Object',[a]]
    rows.append(dict(id='incidence-two',title='Symbolic incidence with two implication links',theory=theory(dict(a=0,l=0),dict(Inc=2,Point=1,Object=1),dict(inc=inc,typing=['imp',inc,point],objecthood=['imp',point,obj])),target=obj,length=5,scope='Given ground symbolic incidence/typing premises with arities unlike the propositional donors. Not the full Hilbert axiom groups.'))
    x=['var','x'];body=['eq',x,x]
    rows.append(dict(id='double-universal',title='A doubly quantified equality theorem',theory=theory(),target=['all','x',['all','y',body]],length=3,scope='Logical equality and two generalizations, valid in arithmetic vocabularies without PA axioms or induction. Excluded from training.'))
    p=['pred','Red',[]];q=['pred','Blue',[]];r=['pred','Green',[]];s=['pred','Gold',[]]
    rows.append(dict(id='forked-goal',title='Two alternative implication paths to one assertion',theory=theory(predicates=dict(Red=0,Blue=0,Green=0,Gold=0),axioms=dict(start=p,route1=['imp',p,q],route2=['imp',p,r],end1=['imp',q,s],end2=['imp',r,s])),target=s,length=5,scope='A reconverging premise graph with two possible proofs; no route is supplied. Excluded from training.'))
    short=copy.deepcopy(rows[2]);short.update(id='short-incidence',title='Incidence in a too-short envelope',length=4,scope='Finite-envelope negative control; not mathematical unprovability.');rows.append(short)
    zero=copy.deepcopy(rows[0]);zero.update(id='zero-placement',title='No placement budget',attempts=0,scope='Unknown control; no missing candidate may be inferred from this cutoff.');rows.append(zero)
    return rows
