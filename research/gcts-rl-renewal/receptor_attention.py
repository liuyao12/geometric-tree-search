"""Shared softmax attention over checked, variable-shaped proof families.

The scores are search preferences. They assign no point values, add no axiom,
and remove no original candidate. Backward rule distance is a relaxed feature,
not a proof: all premises of a rule still need an exact original derivation.
"""
import collections
import math
import quantified_receptors as Q

FEATURES=('family','cells','concludes_target','goal_gain','last_goal',
          'internal_fraction','hypothesis_fraction','compactness','level',
          'progress_family','guard_fraction','defer')
RATE=2.
EPOCHS=8

class Support:
    def __init__(self,model):
        self.model=model
        reverse=collections.defaultdict(set)
        for rule in model.catalog['rules']:
            reverse[rule['output']].update(rule['inputs'])
        self.distance={model.target:0};queue=collections.deque([model.target])
        while queue:
            out=queue.popleft()
            for value in sorted(reverse[out]):
                if value not in self.distance:
                    self.distance[value]=1+self.distance[out];queue.append(value)

    def relevance(self,value):
        return 1/(1+self.distance[value]) if value in self.distance else 0.

    def vector(self,item,state,graph):
        if item is None:return (0.,)*11+(1.,)
        model=self.model;members=item['members'];slots={k[0] for k in members}
        rules=[model.catalog['rules'][k[1]] for k in members]
        available=[a for j,a in graph.ports.items() if j<0 or Q.cell(j) in state.totals]
        before=max(map(self.relevance,available),default=0.)
        after=max(self.relevance(r['output']) for r in rules)
        refs=[j for k in members for j in k[2]]
        return (1.,len(members)/6,int(rules[-1]['output']==model.target),after-before,
            self.relevance(rules[-1]['output']),
            sum(j in slots for j in refs)/max(1,len(refs)),
            sum(j<0 for j in refs)/max(1,len(refs)),
            len(slots)/(max(slots)-min(slots)+1),item['level']/2,
            len(state.order)/model.length,
            sum(bool(r['guards']) for r in rules)/len(rules),0.)

    def record(self):
        return dict(distances=sorted(self.distance.items()),features=FEATURES,
            scope='Relaxed backward input edges of the complete original ground-rule catalog. Exact symbol/term equality, no supplied proof, names or formula identities as learned parameters. Constructed cold once per policy solve; not a pruning or derivability certificate.')

def choose(items,support,state,graph,weights,stochastic,rng):
    if len(weights)!=len(FEATURES):raise ValueError('attention parameter dimension')
    vectors=[support.vector(None,state,graph)]+[support.vector(item,state,graph) for item in items]
    scores=[sum(x*w for x,w in zip(v,weights)) for v in vectors]
    maximum=max(scores);mass=[math.exp(x-maximum) for x in scores];total=sum(mass)
    probabilities=[x/total for x in mass]
    selected=max(range(len(scores)),key=lambda i:(scores[i],-i))
    draw=rng.random() if stochastic else None
    if stochastic:
        cumulative=0.;selected=len(scores)-1
        for i,p in enumerate(probabilities):
            cumulative+=p
            if draw<cumulative:selected=i;break
    gradient=[vectors[selected][j]-sum(p*v[j] for p,v in zip(probabilities,vectors)) for j in range(len(FEATURES))]
    return (None if not selected else items[selected-1]),dict(features=vectors,scores=scores,
        probabilities=probabilities,selected=selected,draw=draw,gradient=gradient)

def reward(result):
    return int(result['status']=='finite_exact_proof_region')-math.log1p(result['total_seconds']/.001)/math.log1p(result['limits']['seconds']/.001)

def update(weights,baseline,result):
    value=reward(result);advantage=value-baseline
    # The episode likelihood includes every sampled branch action, including
    # actions on later failed branches. No division by the event count.
    gradient=[sum(e['gradient'][j] for e in result['policy_events']) for j in range(len(FEATURES))]
    after=[max(-6.,min(6.,w+RATE*advantage*g)) for w,g in zip(weights,gradient)]
    next_baseline=.9*baseline+.1*value
    return after,next_baseline,dict(reward=value,baseline_before=baseline,advantage=advantage,
        gradient=gradient,rate=RATE,weights_after=after,baseline_after=next_baseline,
        scope='Sampled episode likelihood-ratio update, inclusive observed cold wall-time return, per-statement baseline based only on previous training solves. Parameters clipped to the declared box; clocks cannot be independently reproduced.')
