"""Bind the entire discharged request to separately decoded source commands.

No import of the compact compiler or the source graph/matcher/controller.
Primitive soundness is checked by the separate serialized and old kernels.
"""
import copy
import check_quantified_receptors as A
from audit_quantified_receptors import expected_commands
from audit_serialized_kernel import replay
from serialized_kernel import check,problem_hash

F,N,P=A.freeze,A.need,A.packed
def imp(a,b):return ('imp',a,b)
def context(h):
    if not h:return None
    if len(h)==1:return h[0]
    split=len(h)//2;return ('and',context(h[:split]),context(h[split:]))

def certificate(spec,result):
    s=F(spec);r=F(result);c=r['compact'];rows=r['proof'];hyp=s['hypotheses'];h=len(hyp)
    if rows:A.proof(rows,s['target'],hyp,s['theory'])
    else:N(hyp and hyp[-1]==s['target'],'empty source concludes last hypothesis')
    source,bindings=expected_commands(rows,hyp)
    N(F(c['source_commands'])==F(source) and F(c['source_bindings'])==F(bindings),'entire expanded source binding')
    conjunction=context(hyp);commands=[];mapping={};groups=[];parser=A.parser(s['theory'])
    forbidden=set().union(*(parser.free(a) for a in hyp))
    def emit(cmd):commands.append(cmd);return len(commands)-1
    def mp(formula,a,b):return emit(dict(rule='mp',formula=formula,antecedent=a,implication=b))
    if h:
        for i,a in enumerate(hyp):
            k=emit(dict(rule='tautology',formula=imp(conjunction,a)));mapping[i]=k
            groups.append(dict(kind='hypothesis-projection',hypothesis=i,first=k,last=k))
        for i,cmd in enumerate(source[h:],h):
            a=cmd['formula'];goal=imp(conjunction,a);start=len(commands);kind=cmd['rule']
            if kind=='mp':
                left=imp(conjunction,source[cmd['antecedent']]['formula'])
                right=imp(conjunction,source[cmd['implication']]['formula'])
                edge=emit(dict(rule='tautology',formula=imp(left,imp(right,goal))))
                middle=mp(imp(right,goal),mapping[cmd['antecedent']],edge)
                last=mp(goal,mapping[cmd['implication']],middle)
            elif kind=='generalize':
                x=cmd['variable'];N(x not in forbidden,'original ambient eigenvariable')
                body=source[cmd['source']]['formula'];universal=('all',x,imp(conjunction,body))
                first=emit(dict(rule='generalize',formula=universal,variable=x,source=mapping[cmd['source']]))
                edge=emit(dict(rule='distribute',formula=imp(universal,goal),variable=x,antecedent=conjunction,consequent=body))
                last=mp(goal,first,edge)
            else:
                N(kind in ('axiom','tautology','refl','instantiate','distribute','eq_subst','induction'),'closed primitive schema')
                first=emit(copy.deepcopy(cmd));edge=emit(dict(rule='tautology',formula=imp(a,goal)));last=mp(goal,first,edge)
            mapping[i]=last;groups.append(dict(kind='source',source_command=i,first=start,last=last))
    else:
        commands=copy.deepcopy(source);mapping={i:i for i in range(len(source))}
        groups=[dict(kind='source',source_command=i,first=i,last=i) for i in range(len(source))]
    target=s['target']
    for a in reversed(hyp):target=imp(a,target)
    if h>1:
        start=len(commands);edge=emit(dict(rule='tautology',formula=imp(imp(conjunction,s['target']),target)))
        last=mp(target,mapping[len(source)-1],edge);groups.append(dict(kind='currying',first=start,last=last))
    N(F(c['context'])==conjunction and F(c['curried_target'])==target,'context and exact deduction theorem')
    variables=sorted(parser.free(target));N(list(c['closure_variables'])==variables,'entire universal closure')
    for x in reversed(variables):
        start=len(commands);target=('all',x,target)
        last=emit(dict(rule='generalize',formula=target,variable=x,source=start-1))
        groups.append(dict(kind='closure',variable=x,first=start,last=last))
    expected=dict(protocol='gcts-fol-1',theory=s['theory'],target=target,blocks=[],proof=commands)
    request=c['request'];N(request==F(expected),'all source-linked primitive commands, original theory and target')
    N(F(c['groups'])==F(groups) and {int(k):v for k,v in c['conditional_map'].items()}==mapping,'every reader group and output binding')
    N(c['commands']==c['expected_compact_commands']==len(commands) and c['request_bytes']==len(P(request)),'actual command and byte costs')
    old=3**h*(len(source)-1)+1 if h else len(source)
    N(c['old_expanded_commands']==old,'explicit repeated-discharge recurrence')
    pin=problem_hash(request);host=check(P(request),max_work=None,expected_problem_sha256=pin);independent=replay(P(request),pin)
    N(host['status']==independent['status']=='accepted','both complete primitive kernels')
    return dict(status='accepted',commands=len(commands),request_bytes=len(P(request)),
        hypotheses=h,source_commands=len(source),old_expanded_commands=old,
        closure_variables=variables,root_assumptions=0,added_axioms=0)
