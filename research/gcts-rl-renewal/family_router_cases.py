"""Statement-only cost-feedback corpus and held-out symbol namespaces.

Most evaluation shapes recur in training. Three new compositions are separate
structural probes; this is not a broad mathematical generalization benchmark.
"""
from quantifier_family_cases import case,registry as old

def registry():
    donors,_,evaluation=old()
    training=[case('routing-train-short'),case('routing-train-compound',compound=True),
        case('routing-train-capture',nested=True),case('routing-train-ground',ground=True),
        case('routing-train-two',hops=2),case('routing-train-compound-two',hops=2,compound=True),
        case('routing-train-ground-two',hops=2,ground=True),case('routing-train-three',hops=3),
        case('routing-train-ground-three',hops=3,ground=True),
        case('routing-train-open',open_scope=True),case('routing-train-missing',missing=True),
        case('routing-train-small',bound=2)]
    evaluation += [case('routing-probe-compound-capture',compound=True,nested=True),
        case('routing-probe-two-capture',hops=2,nested=True),
        case('routing-probe-ground-compound',hops=2,ground=True,compound=True)]
    return donors,training,evaluation
