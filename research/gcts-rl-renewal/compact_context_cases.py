"""Declarative fresh goals, signatures and finite envelopes; no proof paths."""
import copy
import logic as L
from run_adaptive_clusters import case
from quantified_receptor_cases import registry as quantified


def registry():
    p=lambda n,*ts:('pred',n,ts)
    out=[case('context-six',6,6)]
    out[0]['title']='Six implications, seven hypotheses'
    for name,compound in (('branch-donor',False),('branch-compound',True)):
        a,b,c=[p(name+'-'+v) for v in 'ABC']
        if compound:a,b,c=('and',a,p(name+'-D')),('not',b),L.Imp(c,p(name+'-E'))
        h=(a,L.Imp(a,b),L.Imp(a,L.Imp(b,c)))
        symbols={name+'-'+v:0 for v in ('ABCDE' if compound else 'ABC')}
        out.append(dict(id=name,title='Two branches share one hypothesis'+(' with compound formulas' if compound else ''),
            bound=3,target=c,hypotheses=h,theory=dict(functions={},predicates=symbols,axioms={},schemas=[]),
            terms=(),variables=(),rounds=0,generalization_rounds=0))
    qs,_=quantified()
    ar=copy.deepcopy(next(s for s in qs if s['id']=='arithmetic'))
    congruence=ar['theory']['axioms'].pop('succ-congruence')
    ar.update(id='arithmetic-context',title='Successor preserves addition by zero, conditional on congruence',
              hypotheses=(congruence,),bound=6)
    ar.pop('length');out.append(ar)
    x,u,a,b=L.V('x'),L.V('u'),L.V('a'),L.V('b')
    geo=copy.deepcopy(next(s for s in qs if s['id']=='hilbert-typing'))
    geo.update(id='incidence-context',title='A conditional symbolic incidence consequence',
        hypotheses=(p('Inc',a,u),L.Imp(p('Point',a),p('Point',b))),target=p('Point',b),
        bound=6,terms=(a,b,u),variables=('a','b','u'),generalization_rounds=0)
    geo.pop('length');out.append(geo)
    for name in ('ambient-y','scope-reject'):
        s=copy.deepcopy(next(s for s in qs if s['id']==name));s['bound']=s.pop('length');out.append(s)
    a,b=p('copy-A'),p('copy-B')
    out.append(dict(id='zero-derivation',title='The conclusion is already a hypothesis',bound=0,target=b,hypotheses=(a,b),
        theory=dict(functions={},predicates={'copy-A':0,'copy-B':0},axioms={},schemas=[]),terms=(),variables=(),rounds=0,generalization_rounds=0))
    return out
