"""A one-step, full-feedback policy for requesting the discovered inventory.

It selects between complete base search and the frozen fixed family controller.
This is an episode-level contextual-bandit control, not branch-level sampled RL.
Both action costs are observed in training; no proof path is a policy input.
"""
import math

FEATURES=('log_region','log_hypotheses','log_rules','log_candidates',
          'log_selected_degree','log_target_nodes','log_hypothesis_nodes','forbidden_fraction')
BANDWIDTHS=(.03,.06,.12,.24)
RATE=4.
PASSES=256

def nodes(value):
    # Count syntax nodes, not predicate names or serialized character lengths.
    if not isinstance(value,(tuple,list)):return 0
    return 1+sum(nodes(x) for x in value if isinstance(x,(tuple,list)))

def context(model,state,graph):
    kind,point,keys=graph.decision(state)
    values=(math.log1p(model.bound)/4,math.log1p(len(model.hypotheses))/3,
        math.log1p(len(model.catalog['rules']))/6,
        math.log1p(sum(len(v) for v in graph.domains.values()))/10,
        math.log1p(len(keys) if keys is not None else 0)/6,
        math.log1p(nodes(model.target))/4,
        math.log1p(sum(nodes(h) for h in model.hypotheses))/5,
        len(set(model.variables)&model.forbidden)/max(1,len(model.variables)))
    return dict(features=values,kind=kind,point=point)

def basis(vector,centers,bandwidth):
    if len(vector)!=len(FEATURES) or not centers:raise ValueError('router input dimension')
    if bandwidth not in BANDWIDTHS or any(len(c)!=len(FEATURES) for c in centers):raise ValueError('router kernel declaration')
    values=[math.exp(-sum((a-b)**2 for a,b in zip(vector,c))/(2*bandwidth**2)) for c in centers]
    total=sum(values)
    if total==0:return [1./len(centers)]*len(centers)
    return [v/total for v in values]

def decision(vector,centers,weights,bandwidth):
    if len(weights)!=len(centers):raise ValueError('router parameter dimension')
    phi=basis(vector,centers,bandwidth);score=sum(x*w for x,w in zip(phi,weights))
    probability=1/(1+math.exp(-score)) if score>=0 else math.exp(score)/(1+math.exp(score))
    return dict(features=vector,basis=phi,score=score,probabilities=(1-probability,probability),selected=int(score>0))

def reward(result):
    return int(result['status']=='finite_exact_proof_region')-math.log1p(result['total_seconds']/.001)/math.log1p(result['limits']['seconds']/.001)

def step(weights,vector,centers,returns,bandwidth):
    event=decision(vector,centers,weights,bandwidth);p=event['probabilities'][1]
    gradient=[p*(1-p)*(returns[1]-returns[0])*x for x in event['basis']]
    after=[min(6.,max(-6.,w+RATE*g)) for w,g in zip(weights,gradient)]
    return after,dict(event=event,returns=returns,expected_reward=(1-p)*returns[0]+p*returns[1],gradient=gradient,weights_after=after)

def fit_one(contexts,returns,bandwidth):
    centers=[c['features'] for c in contexts];weights=[0.]*len(centers);updates=[]
    for epoch in range(PASSES):
        # Deterministic rotating order; feedback is reused, not fresh episodes.
        order=list(range(len(centers)));offset=epoch%len(order);order=order[offset:]+order[:offset]
        for j in order:
            after,record=step(weights,centers[j],centers,returns[j],bandwidth)
            record.update(epoch=epoch,context=j,weights_before=weights);updates.append(record);weights=after
    return dict(features=FEATURES,centers=centers,initial_weights=[0.]*len(centers),weights=weights,
        bandwidth=bandwidth,rate=RATE,passes=PASSES,updates=updates,
        scope='Analytic gradient of the paired-feedback expected one-step return. No sampled actions, branch-level credit assignment, evaluation feedback or proof-path input.')

def fit(contexts,returns):
    fits=[]
    for bandwidth in BANDWIDTHS:
        p=fit_one(contexts,returns,bandwidth)
        events=[decision(c['features'],p['centers'],p['weights'],bandwidth) for c in contexts]
        p['training_expected_reward']=sum(sum(prob*value for prob,value in zip(e['probabilities'],r)) for e,r in zip(events,returns))/len(returns)
        p['training_selected_reward']=sum(r[e['selected']] for e,r in zip(events,returns))/len(returns)
        p['training_decisions']=[e['selected'] for e in events];fits.append(p)
    selected=max(range(len(fits)),key=lambda i:(fits[i]['training_expected_reward'],-i))
    result=dict(fits[selected]);result['selection']=dict(candidates=fits,selected=selected,
        criterion='Maximum expected return on the paired training feedback; first candidate breaks exact ties. No evaluation feedback. This fits training contexts and is not a structural-generalization guarantee.')
    return result
