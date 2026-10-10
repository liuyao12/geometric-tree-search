"""Shared sampled softmax over native family instances and defer."""
import math
FEATURES=('family','cells','level','known_receptors','head_fraction','accept_fraction','progress','defer')
FIXED=(1.,2.,.5,1.,.5,1.,0.,-2.)
RATE=2.
def vector(item,g):
    if item is None:return (0.,)*7+(1.,)
    i=g.universe.inventory;heads=accepts=0
    for _,key in item['pending']:
        b=key[1];heads+=b>=i.A;accepts+=b>=i.A and (b-i.A)//i.A==i.accept
    n=len(item['pending'])
    return (1.,n/8,item['level']/4,item['known_fraction'],heads/n,accepts/n,len(g.order)/len(g.required),0.)
def choose(items,g,weights,stochastic,rng):
    if len(weights)!=len(FEATURES):raise ValueError('native policy dimension')
    vectors=[vector(None,g)]+[vector(v,g) for v in items];scores=[sum(a*b for a,b in zip(v,weights)) for v in vectors];maximum=max(scores);mass=[math.exp(s-maximum) for s in scores];total=sum(mass);probabilities=[m/total for m in mass]
    selected=max(range(len(scores)),key=lambda j:(scores[j],-j));draw=rng.random() if stochastic else None
    if stochastic:
        cumulative=0.;selected=len(scores)-1
        for j,p in enumerate(probabilities):
            cumulative+=p
            if draw<cumulative:selected=j;break
    gradient=[vectors[selected][j]-sum(p*v[j] for p,v in zip(probabilities,vectors)) for j in range(len(FEATURES))]
    return (None if selected==0 else items[selected-1]),dict(features=vectors,scores=scores,probabilities=probabilities,selected=selected,draw=draw,gradient=gradient)
def update(weights,baseline,result):
    value=int(result['status']=='finite_exact_native_rectangle')-math.log1p(result['total_seconds']/.001)/math.log1p(result['limits']['seconds']/.001);events=result['policy_events'];gradient=[sum(e['gradient'][j] for e in events) for j in range(len(FEATURES))]
    after=[max(-6.,min(6.,w+RATE*(value-baseline)*v)) for w,v in zip(weights,gradient)]
    return after,.9*baseline+.1*value,dict(reward=value,baseline_before=baseline,advantage=value-baseline,gradient=gradient,rate=RATE,weights_after=after)
