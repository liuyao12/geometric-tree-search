"""Fresh training symbols and frozen evaluation statements; no proof paths."""
from quantifier_family_cases import case,registry as previous

def registry():
    donors,_,evaluation=previous()
    training=[case('request-train-short'),case('request-train-compound',compound=True),
        case('request-train-two',hops=2),case('request-train-compound-two',hops=2,compound=True),
        case('request-train-ground-two',hops=2,ground=True),case('request-train-spare',bound=5),
        case('request-train-open',open_scope=True),case('request-train-missing',missing=True)]
    return donors,training,evaluation
