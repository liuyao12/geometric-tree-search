"""A Bernoulli request policy using existing graph counts, before any join.

The request action enables the frozen fixed family selector. Neither action
changes the complete original candidate graph, its scheduler or fallback.
"""
import math

FEATURES=('bias','log_region','log_frontier','log_degree','progress',
          'selected_position','known_ports','forbidden_fraction')

def features(model,state,graph,point,keys):
    h=len(model.hypotheses);n=model.length
    return (1.,math.log1p(model.bound)/4,math.log1p(len(graph.domains))/4,
        math.log1p(len(keys))/8,len(state.order)/n,point[0]/(2*n),
        len(graph.ports)/(n+h),len(set(model.variables)&model.forbidden)/max(1,len(model.variables)))

def choose(vector,weights,stochastic,rng):
    if len(vector)!=len(FEATURES) or len(weights)!=len(FEATURES):raise ValueError('request policy dimension')
    score=sum(x*w for x,w in zip(vector,weights))
    probability=1/(1+math.exp(-score)) if score>=0 else math.exp(score)/(1+math.exp(score))
    draw=rng.random() if stochastic else None
    selected=int(draw<probability) if stochastic else int(score>0)
    event=dict(features=vector,score=score,probabilities=(1-probability,probability),
        draw=draw,selected=selected,gradient=tuple((selected-probability)*x for x in vector))
    return bool(selected),event

def update(weights,baseline,result,rate=.35):
    # Inclusive observed solve time: grammar, model, gate, join, search and
    # positive point/source/discharged-kernel checks. Clocks are observations.
    cost=result['total_seconds'];budget=result['limits']['seconds']
    reward=int(result['status']=='finite_exact_proof_region')-math.log1p(cost/.001)/math.log1p(budget/.001)
    events=result['gate_events']
    gradient=[sum(e['gradient'][j] for e in events)/max(1,len(events)) for j in range(len(FEATURES))]
    after=[max(-6.,min(6.,w+rate*(reward-baseline)*g)) for w,g in zip(weights,gradient)]
    return after,.9*baseline+.1*reward,dict(observed_total_seconds=cost,reward=reward,
        baseline_before=baseline,gradient=gradient,rate=rate,weights_after=after,
        scope='Observed inclusive cold-solve wall-time reward, not a deterministic work proxy. Independent audit checks recorded clock binding and update algebra; it cannot reproduce wall time.')
