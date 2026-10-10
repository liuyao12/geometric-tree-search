"""Statements and finite grammars; no supplied derivation or proof family."""
import copy
from quantifier_family_cases import case,registry as previous

def registry():
    donors,_,old=previous()
    training=[case('attention-train-short'),case('attention-train-ground-two',hops=2,ground=True),
        case('attention-train-compound-two',hops=2,compound=True),
        case('attention-train-three',hops=3),case('attention-train-ground-three',hops=3,ground=True),
        case('attention-train-missing',missing=True)]
    evaluation=[case('attention-renamed-three',hops=3),case('attention-renamed-compound-two',hops=2,compound=True),
        case('attention-probe-two-capture',hops=2,nested=True),
        case('attention-probe-compound-capture',hops=2,nested=True,compound=True),
        case('attention-probe-ground-compound',hops=2,ground=True,compound=True),
        case('attention-probe-three-capture',hops=3,nested=True),
        case('attention-open',open_scope=True),case('attention-missing',missing=True),case('attention-small',bound=2)]
    for name in ('quantifier-arithmetic-context','quantifier-incidence-context'):
        spec=copy.deepcopy(next(s for s in old if s['id']==name))
        spec['id']=spec['id'].replace('quantifier-','attention-');evaluation.append(spec)
    return donors,training,evaluation
