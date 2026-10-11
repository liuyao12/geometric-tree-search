"""Fresh softmax REINFORCE over expanded, validated cluster proposals."""
import math
FEATURES=('family','base_growth','internal_refs','already_justified_inputs','target_output','mark_extension','shape_density','completed_pairs','level','defer')
RATE=0.4;EPISODES=24
FIXED=(0.5,0.4,0.6,0.7,0.1,-0.1,0.1,0.3,0.2,0.)
def vector(item,model,state,graph):
    if item is None:return [0.]*9+[1.]
    slots={k[0] for k in item['members']};guards=[model.metadata[k] for k in item['members'] if k[1]==1];refs=[j for g in guards for j,a in g['requirements']]
    # A source is justified only when both its command and guard are present
    # and every strict-prior source was recursively justified. Future occupied
    # conclusions do not count merely because they carry a formula marking.
    known=set();selected={k[0]:k for k in state.selected if k[1]==1};commands={k[0]:k for k in state.selected if k[1]==0}
    for j,k in sorted(selected.items()):
        if j in commands and commands[j][2]==k[2] and all(i in known for i,a in model.metadata[k]['requirements']):known.add(j)
    return [float(item['kind']=='family'),item['new_occupancy']/(12*6),sum(j in slots for j in refs)/max(1,len(refs)),sum(j in known for j in refs)/max(1,len(refs)),float(any(g['command']['formula']==model.spec['target'] for g in guards)),item['new_marks']/1000,len(slots)/(max(slots)-min(slots)+1),len(guards)/3,item['level']/2,0.]
def choose(items,features,weights,rng,stochastic):
    scores=[sum(w*x for w,x in zip(weights,v)) for v in features];top=max(scores);prob=[math.exp(s-top) for s in scores];total=sum(prob);prob=[p/total for p in prob];u=rng.random() if stochastic else None
    if stochastic:
        cumul=0.;index=len(prob)-1
        for j,p in enumerate(prob):
            cumul+=p
            if u<cumul:index=j;break
    else:index=max(range(len(scores)),key=lambda j:(scores[j],-j))
    return items[index],dict(index=index,features=features,scores=scores,probabilities=prob,uniform=u)
def reward(result,accepted):
    growth=2*len(result['proof']) if accepted else 0
    return growth/max(1,result['metrics'].get('attempts',0))-0.25*min(1.,(result['metrics'].get('validation_checks',0)+result['metrics'].get('sample_pair_tests',0))/100000)
def update(weights,events,value,baseline):
    gradient=[0.]*len(FEATURES)
    for e in events:
        selected=e['features'][e['index']]
        for k in range(len(FEATURES)):gradient[k]+=selected[k]-sum(p*v[k] for p,v in zip(e['probabilities'],e['features']))
    gradient=[x/max(1,len(events)) for x in gradient];advantage=value-baseline
    return [w+RATE*advantage*g for w,g in zip(weights,gradient)],0.9*baseline+0.1*value,dict(reward=value,baseline_before=baseline,advantage=advantage,gradient=gradient)
