"""Compactly discharge searched sequents using the unchanged primitive kernel.

Lift each source command under one balanced conjunction of all hypotheses.
All helpers are explicit primitive tautology/MP/distribution commands; no new
trusted inference, premise axiom, block, or source proof path is introduced.
The generated command count is linear, although formula words and the existing
truth-table checker can still be expensive. Source point capacities are not
replaced by these compiler groups.
"""
import copy
import time

import logic as L
import quantified_receptors as Q
import check_quantified_receptors as A
from serialized_kernel import canonical, check, PROTOCOL, problem_hash
from audit_serialized_kernel import replay


def packed(hypotheses):
    if not hypotheses:
        return None
    if len(hypotheses)==1:
        return hypotheses[0]
    middle=len(hypotheses)//2
    return ('and',packed(hypotheses[:middle]),packed(hypotheses[middle:]))


def curried(hypotheses,target):
    for h in reversed(hypotheses):
        target=L.Imp(h,target)
    return target


def compile_request(proof,target,hypotheses,theory,close_free=True):
    started=time.perf_counter()
    proof,target,hypotheses=A.freeze(proof),A.freeze(target),A.freeze(hypotheses)
    if proof:
        source_check=A.proof(proof,target,hypotheses,theory)
    elif hypotheses and hypotheses[-1]==target:
        source_check=dict(status='accepted',primitive_lines=0,commands=0)
    else:
        raise ValueError('empty derivation must end at a supplied hypothesis')
    source,source_bindings=Q.commands(proof,hypotheses)
    h=len(hypotheses);context=packed(hypotheses);out=[];mapping={};groups=[]
    forbidden=set().union(*(L.free(a) for a in hypotheses))
    def emit(line):out.append(line);return len(out)-1
    def mp(a,i,j):return emit(dict(rule='mp',formula=a,antecedent=i,implication=j))
    if not h:
        out=copy.deepcopy(source)
        mapping={i:i for i in range(len(source))}
        groups=[dict(kind='source',source_command=i,first=i,last=i) for i in range(len(source))]
    else:
        for i,a in enumerate(hypotheses):
            k=emit(dict(rule='tautology',formula=L.Imp(context,a)))
            mapping[i]=k;groups.append(dict(kind='hypothesis-projection',hypothesis=i,first=k,last=k))
        for i,r in enumerate(source[h:],h):
            first=len(out);a=r['formula'];goal=L.Imp(context,a);kind=r['rule']
            if kind=='mp':
                p=source[r['antecedent']]['formula']
                left=L.Imp(context,p);right=L.Imp(context,L.Imp(p,a))
                edge=emit(dict(rule='tautology',formula=L.Imp(left,L.Imp(right,goal))))
                bridge=mp(L.Imp(right,goal),mapping[r['antecedent']],edge)
                k=mp(goal,mapping[r['implication']],bridge)
            elif kind=='generalize':
                x=r['variable'];body=source[r['source']]['formula']
                if x in forbidden:
                    raise ValueError('source eigenvariable is free in the packed context')
                universal=L.All(x,L.Imp(context,body))
                first_gen=emit(dict(rule='generalize',formula=universal,variable=x,source=mapping[r['source']]))
                edge=emit(dict(rule='distribute',formula=L.Imp(universal,goal),variable=x,
                               antecedent=context,consequent=body))
                k=mp(goal,first_gen,edge)
            elif kind in ('axiom','tautology','refl','instantiate','distribute','eq_subst','induction'):
                fact=emit(dict(r))
                edge=emit(dict(rule='tautology',formula=L.Imp(a,goal)))
                k=mp(goal,fact,edge)
            else:
                raise ValueError('unexpanded source reference rule')
            mapping[i]=k;groups.append(dict(kind='source',source_command=i,first=first,last=k))
    conditional=curried(hypotheses,target)
    if h>1:
        first=len(out);last=mapping[len(source)-1]
        edge=emit(dict(rule='tautology',formula=L.Imp(L.Imp(context,target),conditional)))
        k=mp(conditional,last,edge);groups.append(dict(kind='currying',first=first,last=k))
    closures=sorted(L.free(conditional)) if close_free else []
    actual=conditional
    for x in reversed(closures):
        first=len(out);actual=L.All(x,actual)
        k=emit(dict(rule='generalize',formula=actual,variable=x,source=len(out)-1))
        groups.append(dict(kind='closure',variable=x,first=first,last=k))
    request=dict(protocol=PROTOCOL,theory=copy.deepcopy(theory),target=actual,blocks=[],proof=out)
    compiled=time.perf_counter()-started
    payload=canonical(request);checked=time.perf_counter()
    host=check(payload,max_work=None,expected_problem_sha256=problem_hash(request))
    independent=replay(payload,problem_hash(request))
    if host['status']!='accepted' or independent['status']!='accepted':
        raise ValueError(('compact discharge rejected',host,independent))
    return dict(request=request,context=context,curried_target=conditional,closure_variables=closures,
                source_commands=source,source_bindings=source_bindings,conditional_map=mapping,
                groups=groups,source_check=source_check,host=host,independent=independent,
                compile_seconds=compiled,checking_seconds=time.perf_counter()-checked,
                request_bytes=len(payload),commands=len(out),
                old_expanded_commands=(3**h*(len(source)-1)+1) if h else len(source),
                expected_compact_commands=(h+3*(len(source)-h)+int(h>1)*2 if h else len(source))+len(closures))
