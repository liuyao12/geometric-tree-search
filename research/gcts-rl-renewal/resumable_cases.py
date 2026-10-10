"""Fresh branch/tail goals and real symbolic-theory controls; no proof paths."""
import copy
from compact_context_cases import registry as context_cases

def branch(name,tail=0,decoys=0,compound=False,bound=None):
    atom=lambda v:('pred',name+'-'+v,())
    implication=lambda a,b:('imp',a,b)
    formulas=[atom(v) for v in ('A','B','C')]+[atom('T'+str(i)) for i in range(tail)]
    symbols={a[1]:0 for a in formulas}
    if compound:
        side=atom('side');symbols[side[1]]=0
        formulas=[('and',a,side) if i%3==0 else ('not',a) if i%3==1 else implication(side,a) for i,a in enumerate(formulas)]
    a,b,c=formulas[:3];hyp=[a,implication(a,b),implication(a,implication(b,c))]
    hyp.extend(implication(x,y) for x,y in zip(formulas[2:],formulas[3:]))
    for i in range(decoys):
        d=atom('decoy'+str(i));symbols[d[1]]=0;hyp.append(implication(a,d))
    return dict(id=name,title='Shared premise, '+str(tail)+' tail steps'+(', compound formulas' if compound else ''),
        bound=3+tail if bound is None else bound,target=formulas[-1],hypotheses=hyp,
        theory=dict(functions={},predicates=symbols,axioms={},schemas=[]),terms=(),variables=(),rounds=0,generalization_rounds=0)

def registry():
    donors=[branch('resume-donor-fork'),branch('resume-donor-tail',tail=2)]
    training=[branch('resume-train-fork'),branch('resume-train-tail',tail=1),
              branch('resume-train-spare',bound=5),branch('resume-train-decoy',decoys=1)]
    evaluation=[branch('resume-held-fork'),branch('resume-held-compound',compound=True),
        branch('resume-held-decoys',tail=1,decoys=2),branch('resume-held-long',tail=3),
        branch('resume-too-small',tail=1,bound=2),branch('resume-missing',bound=4)]
    evaluation[-1]['hypotheses'].pop(1)
    for name in ('arithmetic-context','incidence-context','scope-reject'):
        s=copy.deepcopy(next(s for s in context_cases() if s['id']==name));s['id']='resume-'+name;evaluation.append(s)
    return donors,training,evaluation
