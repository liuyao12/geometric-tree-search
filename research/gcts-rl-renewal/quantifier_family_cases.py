"""Statements and finite grammars only; no supplied derivation or family."""
import copy
import logic as L
from compact_context_cases import registry as old

def case(name,hops=1,compound=False,nested=False,ground=False,open_scope=False,missing=False,bound=None):
    donor=name.startswith('quantifier-donor');free='u' if donor else 'v';first='x' if donor else 'a'
    x,u=L.V(first),L.V(free);predicates={};functions={'c':0,'f':1}
    def p(k,t):
        s=name+'-'+str(k);predicates[s]=1;return ('pred',s,(t,))
    def body(k,t):
        a=p(k,t)
        if nested and k==hops:
            s=name+'-relation';predicates[s]=2
            return L.All(free,('pred',s,(t,L.V(free))))
        if compound:
            return ('and',a,('not',p(k+20,L.F('f',t)))) if k%2==0 else ('imp',p(k+20,t),a)
        return a
    # Independent bound names in the supplied hypotheses deliberately differ.
    hypotheses=[L.All(first,body(0,x))]
    for k in range(hops):
        binder=('b' if donor else 'q')+str(k);v=L.V(binder)
        hypotheses.append(L.All(binder,L.Imp(body(k,v),body(k+1,v))))
    term=L.F('c') if ground else u
    target=L.substitute(body(hops,x),first,term)
    if not ground:target=L.All(free,target)
    if open_scope:hypotheses[0]=body(0,u)
    if missing:
        last=hypotheses[-1];hypotheses[-1]=L.All(last[1],L.Imp(p(99,L.V(last[1])),last[2][2]))
    count=2*hops+1+int(not ground)-int(open_scope)
    return dict(id=name,title=name.replace('-',' '),theory=dict(functions=functions,predicates=predicates,axioms={},schemas=[]),
        hypotheses=hypotheses,target=target,bound=count if bound is None else bound,
        terms=(term,),variables=() if ground else (free,),rounds=1,generalization_rounds=0 if ground else 1)

def registry():
    donors=[case('quantifier-donor-one'),case('quantifier-donor-two',hops=2),
            case('quantifier-donor-compound',hops=2,compound=True)]
    training=[case('quantifier-train-renamed'),case('quantifier-train-compound',compound=True),
              case('quantifier-train-ground',ground=True),case('quantifier-train-spare',bound=5)]
    evaluation=[case('quantifier-renamed'),case('quantifier-compound',compound=True),
        case('quantifier-capture',nested=True),case('quantifier-ground',ground=True),
        case('quantifier-chain',hops=3),case('quantifier-compound-chain',hops=2,compound=True),
        case('quantifier-open-scope',open_scope=True),case('quantifier-missing',missing=True),
        case('quantifier-small',bound=2)]
    for name in ('arithmetic-context','incidence-context'):
        s=copy.deepcopy(next(s for s in old() if s['id']==name));s['id']='quantifier-'+name;evaluation.append(s)
    return donors,training,evaluation
