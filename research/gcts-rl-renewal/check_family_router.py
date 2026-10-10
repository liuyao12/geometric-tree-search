"""Independent initial-domain contexts, Gaussian policy and feedback algebra.

No producer graph, policy, search, formula routines or kernel is imported.
Frozen independent full-search and source-proof verifiers are reused.
"""
import math,statistics
import check_proposal_gate as V
N,F=V.N,V.F
FEATURES=('log_region','log_hypotheses','log_rules','log_candidates','log_selected_degree',
          'log_target_nodes','log_hypothesis_nodes','forbidden_fraction')
WIDTHS=(.03,.06,.12,.24)
def count_arrays(value):
    stack=[value];count=0
    while stack:
        v=stack.pop()
        if isinstance(v,(tuple,list)):count+=1;stack.extend(v)
    return count
def context(rules,spec):
    ds=V.A.domains(rules,spec,());kind,point,keys=V.A.decide(ds)
    _,_,marks=V.A.state(rules,spec,());blocked=sum(marks[(-1000,j)]!=0 for j in range(len(spec['variables'])))
    fs=(math.log1p(spec['bound'])/4,math.log1p(len(spec['hypotheses']))/3,
        math.log1p(len(rules))/6,math.log1p(sum(map(len,ds.values())))/10,
        math.log1p(len(keys) if keys is not None else 0)/6,
        math.log1p(count_arrays(spec['target']))/4,
        math.log1p(sum(count_arrays(a) for a in spec['hypotheses']))/5,
        blocked/max(1,len(spec['variables'])))
    return dict(features=fs,kind=kind,point=point)
def decision(vector,centers,weights,width,event):
    N(len(vector)==8 and len(centers)==len(weights)>0 and all(len(c)==8 for c in centers) and width in WIDTHS,'declared routing dimensions and kernel')
    masses=[math.exp(-sum((x-y)**2 for x,y in zip(vector,c))/(2*width**2)) for c in centers];total=sum(masses)
    phi=[m/total for m in masses] if total else [1/len(masses)]*len(masses)
    score=sum(w*x for w,x in zip(weights,phi));shift=max(0.,score);prob=math.exp(score-shift)/(math.exp(-shift)+math.exp(score-shift))
    V.V.close(vector,event['features']);V.V.close(phi,event['basis']);V.V.close([score],[event['score']]);V.V.close([1-prob,prob],event['probabilities'])
    N(event['selected']==int(score>0),'frozen routing action and tie-to-base')
    return prob
def returns(c):
    result=[]
    for lane in ('base','fixed'):
        samples=c['timings'][lane]['samples'];budget=c['runs'][lane]['limits']['seconds']
        result.append(statistics.median(int(a['status']=='finite_exact_proof_region')-math.log1p(a['seconds']/.001)/math.log1p(budget/.001) for a in samples))
    V.V.close(result,c['returns']);return result
def step(weights,center,centers,values,width,record):
    V.V.close(weights,record['weights_before']);V.V.close(values,record['returns'])
    p=decision(center,centers,weights,width,record['event'])
    g=[p*(1-p)*(values[1]-values[0])*x for x in record['event']['basis']]
    after=[max(-6.,min(6.,w+4*g)) for w,g in zip(weights,g)]
    V.V.close(g,record['gradient']);V.V.close(after,record['weights_after']);V.V.close([(1-p)*values[0]+p*values[1]],[record['expected_reward']])
    return after
def policy(feedback,p):
    centers=[c['context']['features'] for c in feedback];values=[returns(c) for c in feedback];fits=p['selection']['candidates']
    N(len(fits)==4 and [x['bandwidth'] for x in fits]==list(WIDTHS),'complete declared training-only resolution search')
    expected=[]
    for fit in fits:
        N(tuple(fit['features'])==FEATURES and F(fit['centers'])==F(centers) and fit['initial_weights']==[0.]*len(centers) and fit['rate']==4. and fit['passes']==256,'fresh declared fit')
        weights=[0.]*len(centers);updates=fit['updates'];N(len(updates)==256*len(centers),'all repeated-feedback steps')
        pos=0
        for epoch in range(256):
            order=list(range(len(centers)));offset=epoch%len(order);order=order[offset:]+order[:offset]
            for j in order:
                u=updates[pos];N(u['epoch']==epoch and u['context']==j,'declared rotating feedback schedule')
                weights=step(weights,centers[j],centers,values[j],fit['bandwidth'],u);pos+=1
        V.V.close(weights,fit['weights']);events=[]
        for x in centers:
            phi=[math.exp(-sum((a-b)**2 for a,b in zip(x,c))/(2*fit['bandwidth']**2)) for c in centers];phi=[v/sum(phi) for v in phi]
            z=sum(w*v for w,v in zip(weights,phi));p1=1/(1+math.exp(-z));events.append((p1,int(z>0)))
        mean=sum((1-e[0])*v[0]+e[0]*v[1] for e,v in zip(events,values))/len(values)
        V.V.close([mean],[fit['training_expected_reward']]);V.V.close([sum(v[e[1]] for e,v in zip(events,values))/len(values)],[fit['training_selected_reward']])
        N(fit['training_decisions']==[e[1] for e in events],'all training action choices');expected.append(mean)
    selected=max(range(4),key=lambda i:(expected[i],-i));N(p['selection']['selected']==selected,'training-only model selection')
    N(F({k:v for k,v in p.items() if k!='selection'})==F(fits[selected]),'entire chosen frozen model')
    return dict(updates=sum(len(x['updates']) for x in fits),selected=selected,bandwidth=p['bandwidth'])
