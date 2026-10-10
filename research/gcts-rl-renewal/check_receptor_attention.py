"""Independent relational features, stochastic choices and full-tree replay.

Reuses the frozen independent original-domain/quantified-family oracle. Its
policy hook is replaced only for this sequential call and restored afterward.
No producer graph, attention, formula, search or primitive kernel is imported.
"""
import collections
import math
from fractions import Fraction
import check_quantifier_families as V
N,F=V.N,V.F
FEATURES=('family','cells','concludes_target','goal_gain','last_goal',
          'internal_fraction','hypothesis_fraction','compactness','level',
          'progress_family','guard_fraction','defer')

def distances(rules,target):
    target=F(target);edges={}
    for r in rules:edges.setdefault(F(r['output']),set()).update(F(r['inputs']))
    levels={target:0};front={target};depth=0
    while front:
        depth+=1
        following=set().union(*(edges.get(v,set()) for v in front))-set(levels)
        levels.update((v,depth) for v in following);front=following
    return levels

def vector(item,rules,spec,chosen,levels):
    if item is None:return (0.,)*11+(1.,)
    filled,ports,_=V.A.state(rules,spec,chosen)
    relevance=lambda a:1/(1+levels[a]) if a in levels else 0.
    available=[a for j,a in ports.items() if j<0 or j in filled]
    members=F(item['members']);slots={k[0] for k in members};rows=[rules[k[1]] for k in members]
    refs=[r for key in members for r in key[2]]
    return (1.,len(members)/6,int(rows[-1]['output']==F(spec['target'])),
        max(relevance(r['output']) for r in rows)-max(map(relevance,available),default=0.),
        relevance(rows[-1]['output']),sum(j in slots for j in refs)/max(1,len(refs)),
        sum(j<0 for j in refs)/max(1,len(refs)),len(slots)/(max(slots)-min(slots)+1),
        item['level']/2,len(chosen)/(spec['bound']+1),sum(bool(r['guards']) for r in rows)/len(rows),0.)

def policy_event(event,rules,spec,templates,weights,stochastic,rng,chosen,point,levels):
    N(F(event['chosen'])==chosen and F(event['point'])==point,'attention context')
    for p in event['items']:V.check_item(rules,spec,templates,p,chosen)
    features=[vector(None,rules,spec,chosen,levels)]+[vector(p,rules,spec,chosen,levels) for p in event['items']]
    N(len(features)==len(event['features']),'entire attention feature matrix')
    for expected,actual in zip(features,event['features']):V.V.close(expected,actual)
    N(len(weights)==len(FEATURES),'attention parameter dimension')
    scores=[sum(x*y for x,y in zip(weights,f)) for f in features]
    shift=max(scores);denominator=sum(math.exp(s-shift) for s in scores)
    probabilities=[math.exp(s-shift)/denominator for s in scores]
    V.V.close(scores,event['scores']);V.V.close(probabilities,event['probabilities'])
    if stochastic:
        draw=rng.random();N(draw==event['draw'],'fresh branch attention draw')
        index=len(scores)-1;acc=0.
        for j,p in enumerate(probabilities):
            acc+=p
            if draw<acc:index=j;break
    else:
        N(event['draw'] is None,'frozen deterministic attention')
        index=max(range(len(scores)),key=lambda i:(scores[i],-i))
    N(index==event['selected'],'selected actual family or defer')
    gradient=[features[index][j]-sum(p*f[j] for p,f in zip(probabilities,features)) for j in range(len(FEATURES))]
    V.V.close(gradient,event['gradient'])
    return None if index==0 else event['items'][index-1]

def result(rules,spec,templates,r):
    rules=F(rules);levels=distances(rules,spec['target'])
    support=r['attention_support']
    if r['mode']=='policy':
        N(F(support['distances'])==F(sorted(levels.items())) and tuple(support['features'])==FEATURES,'entire cold relaxed support')
    else:N(support is None,'base/fixed controls have no attention support')
    N(0<=r['attention_prep_seconds']<=r['seconds'],'support construction included in solve')
    original=V.policy_event
    def hook(event,rs,sp,ts,ws,st,rng,chosen,point):
        return policy_event(event,rs,sp,ts,ws,st,rng,chosen,point,levels)
    try:
        V.policy_event=hook
        checked=V.result(rules,spec,templates,r)
    finally:V.policy_event=original
    checked['attention_events']=len(r['policy_events']);return checked

def reward(r):
    return int(r['status']=='finite_exact_proof_region')-math.log1p(r['total_seconds']/.001)/math.log1p(r['limits']['seconds']/.001)

def update(weights,baseline,r,u):
    value=reward(r);advantage=value-baseline
    gradient=[sum(e['gradient'][j] for e in r['policy_events']) for j in range(12)]
    after=[max(-6.,min(6.,w+2.*advantage*g)) for w,g in zip(weights,gradient)]
    next_baseline=.9*baseline+.1*value
    for actual,expected in ((u['reward'],value),(u['baseline_before'],baseline),(u['advantage'],advantage),(u['rate'],2.),(u['baseline_after'],next_baseline)):
        V.V.close([actual],[expected])
    V.V.close(gradient,u['gradient']);V.V.close(after,u['weights_after'])
    return after,next_baseline

def deferral_bound(weights,templates):
    """A conservative binary64 score bound, independent of any tested goal.

    Every family instance has these feature intervals by the declared vector
    definition and exact distinct support. Directed rounding bounds each actual
    multiplication and addition. No point candidate is excluded by this fact.
    """
    N(len(weights)==12 and all(math.isfinite(w) for w in weights),'finite bound parameters')
    maximum=max((len(t['pattern']) for t in templates.values()),default=0)
    level=max((t['level'] for t in templates.values()),default=0)
    intervals=((1.,1.),(0.,maximum/6),(0.,1.),(-1.,1.),(0.,1.),(0.,1.),
        (0.,1.),(0.,1.),(0.,level/2),(0.,1.),(0.,1.),(0.,0.))
    def upward(exact):
        rounded=float(exact)
        return math.nextafter(rounded,math.inf) if Fraction.from_float(rounded)<exact else rounded
    upper=0.;steps=[]
    for weight,(lo,hi) in zip(weights,intervals):
        exact=Fraction.from_float(weight)*Fraction.from_float(hi if weight>=0 else lo)
        term=upward(exact);upper=upward(Fraction.from_float(upper)+Fraction.from_float(term))
        steps.append(dict(product_upper=term,sum_upper=upper))
    defer=weights[-1]
    return dict(status='certified_always_defer' if upper<defer else 'not_certified',family_score_upper=upper,
        defer_score=defer,strict_margin=defer-upper,feature_intervals=intervals,rounding_steps=steps,
        maximum_cells=maximum,maximum_level=level,
        scope='Every valid deterministic family instance from this frozen inventory and feature definition, in any legal finite model state. Conservative correctly rounded binary64 operations; sampled training may still choose a family. This proves a policy preference, not a logical pruning rule or a new mathematical theorem.')
