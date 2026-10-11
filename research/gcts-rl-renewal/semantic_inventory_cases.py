"""Assertion inputs and disclosed finite envelopes, with no supplied proofs."""
import copy
from certificate_boundary_cases import theory
from native_receptor_cases import cases as original
from native_inventory_cases import chain

def donors():
    return [copy.deepcopy(original()[j]) for j in (2,6,1)]

def promotion():
    spec=chain(4,['A','B','C','D','E'],'promotion-four')
    spec['length']=7
    spec['scope']='Higher-family discovery using fresh lower registered lemmas and fixed cluster ordering. No proof or reference path is supplied.'
    return spec

def training(donor_cases,promotion_case):
    rows=copy.deepcopy(donor_cases)
    rows[1].update(id='training-short-two',length=4,
        scope='Training envelope permits a registered two-hop call. Same donor premises, no imported proof.')
    rows.append(copy.deepcopy(promotion_case))
    return rows

def evaluation():
    rows=[
        chain(5,['Zulu','Alpha','Theta','Beta','Lambda','Kappa'],'renamed-five'),
        chain(6,['Copper','Silver','Indigo','Violet','Cyan','Ochre','Gold'],'renamed-six')]
    rows[0]['length']=8
    rows[1]['length']=10
    a=['fun','a',[]];l=['fun','l',[]]
    inc=['pred','Inc',[a,l]];point=['pred','Point',[a]];obj=['pred','Object',[a]]
    rows.append(dict(id='incidence-two-semantic',title='A compound symbolic incidence statement',
        theory=theory(dict(a=0,l=0),dict(Inc=2,Point=1,Object=1),
                      dict(inc=inc,typing=['imp',inc,point],objecthood=['imp',point,obj])),
        target=obj,length=4,
        scope='Three given ground symbolic premises, with a shorter lemma-call envelope. Not the full Hilbert axiom groups; no literal spatial geometry. Excluded from donors, promotion and training.'))
    p=['pred','Red',[]];q=['pred','Blue',[]];r=['pred','Green',[]];s=['pred','Amber',[]]
    rows.append(dict(id='forked-semantic',title='Two alternative two-hop routes',
        theory=theory(predicates=dict(Red=0,Blue=0,Green=0,Amber=0),
                      axioms=dict(start=p,route1=['imp',p,q],route2=['imp',p,r],
                                  end1=['imp',q,s],end2=['imp',r,s])),
        target=s,length=4,
        scope='Either route can prove the assertion through a registered lemma. No route is supplied. Excluded from training.'))
    x=['var','x']
    rows.append(dict(id='double-universal-semantic',title='A doubly quantified equality statement',
        theory=theory(),target=['all','x',['all','y',['eq',x,x]]],length=3,
        scope='Logical equality and generalization, valid in an arithmetic vocabulary without PA induction. Excluded from training.'))
    short=copy.deepcopy(original()[2]);short.update(id='short-semantic',length=2,
        title='Two-premise implication in a too-short envelope',
        scope='Finite-grammar negative control, not a mathematical unprovability claim.')
    rows.append(short)
    zero=copy.deepcopy(rows[0]);zero.update(id='zero-semantic',attempts=0,search_enabled=False,
        title='No search budget',scope='Declared unknown control. Compilation and registration still run; point and SMT search are disabled.')
    rows.append(zero)
    unfinished=copy.deepcopy(rows[2]);unfinished.update(id='unfinished-inventory-semantic',
        inventory_steps=1,title='Unfinished native registration',
        scope='One native registration step cannot authorize a lemma inventory. No model or search is permitted after this unknown result.')
    rows.append(unfinished)
    return rows
