"""Statement-only inputs, transfer controls and larger unresolved goals."""
import copy
from receptor_attention_cases import registry as previous
from quantifier_family_cases import case


def registry():
    _, _, old = previous()
    cases = copy.deepcopy(old)
    for spec in cases:
        spec['id'] = spec['id'].replace('attention-', 'dependency-')
    cases.extend([case('dependency-four-hop', hops=4),
                  case('dependency-five-hop', hops=5),
                  case('dependency-four-hop-small', hops=4, bound=9)])
    return cases
