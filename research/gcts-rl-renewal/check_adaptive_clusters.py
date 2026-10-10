"""Separate explicit-domain and family/transaction/policy certificate checker.

Never imports the producer, its graph masks, its matcher or its controller.
Hints need not be complete. Every claimed exhausted base tree must be complete.
"""
import collections
import hashlib
import itertools
import math
import random

import check_movable_regions as A
from audit_serialized_kernel import replay

F,N,P=A.freeze,A.need,A.A.packed


def digest(value):return hashlib.sha256(P(value)).hexdigest()


def pattern_for(rules,members):
    internal={k[0]:i for i,k in enumerate(members)}
    atoms={};external={};result=[]
    def schema(a):
        if a[0]=='pred' and a[2]==():
            if a[1] not in atoms:atoms[a[1]]=len(atoms)
            return ('meta',atoms[a[1]])
        if a[0] in ('imp','and','or','not'):
            return (a[0],)+tuple(schema(v) for v in a[1:])
        N(a==('bot',),'propositional donor syntax')
        return a
    for slot,rid,refs in members:
        r=rules[rid];N(r['kind']=='mp','mined primitive MP')
        contacts=[]
        for i in refs:
            if i in internal:contacts.append(('inside',internal[i]))
            else:
                if i not in external:external[i]=len(external)
                contacts.append(('outside',external[i]))
        inputs=tuple(schema(a) for a in r['inputs'])
        result.append(dict(kind='mp',inputs=inputs,output=schema(r['output']),refs=contacts))
    return F(result)


def instantiate(a,bindings):
    if a[0]=='meta':
        N(str(a[1]) in bindings,'every formula parameter bound')
        return bindings[str(a[1])]
    return (a[0],)+tuple(instantiate(v,bindings) for v in a[1:])


def item(rules,spec,templates,proposal,chosen=()):
    t=templates[proposal['template']]
    members=F(proposal['members']);pattern=F(t['pattern']);bindings=F(proposal['bindings'])
    N(len(members)==len(pattern) and len(set(members))==len(members),'all distinct constituents')
    slots=[k[0] for k in members]
    N(slots==sorted(set(slots)),'increasing adaptable embedding')
    N(proposal['level']==t['level'],'hierarchy identity')
    filled,ports,marks=A.state(rules,spec,chosen)
    totals=collections.Counter();union={}
    outside={str(k):v for k,v in proposal['outside'].items()}
    for j,((slot,rid,refs),node) in enumerate(zip(members,pattern)):
        N(rid>=0,'primitive rule only')
        r=rules[rid]
        N(r['kind']==node['kind'] and r['output']==instantiate(node['output'],bindings)
          and tuple(r['inputs'])==tuple(instantiate(a,bindings) for a in node['inputs']),
          'concrete rules instantiate the entire formula pattern')
        for (kind,index),ref,a in zip(node['refs'],refs,r['inputs']):
            if kind=='inside':N(index<j and ref==slots[index],'internal receptor binding')
            else:
                N(str(index) in outside and ref==outside[str(index)] and ref<slot,
                  'external receptor binding')
                N((ref<0 or ref in filled) and ports.get(ref)==a,'actual available premise')
        for p,v in A.tile(rules,spec,(slot,rid,refs))['occupancy']:
            totals[p]+=v;N(totals[p]<=12,'aggregate capacity')
        for p,v in A.tile(rules,spec,(slot,rid,refs))['marks']:
            N(p not in union or union[p]==v,'aggregate agreement');union[p]=v
    N(F(proposal['occupancy'])==tuple(sorted(totals.items())),'capacity-preserving exact sum')
    N(F(proposal['marks'])==tuple(sorted(union.items())),'exact compatible marking union')
    N(all(p not in marks or marks[p]==v for p,v in union.items()),'proposal interface agreement')
    N(all(k in A.domains(rules,spec,chosen)[A.cell(k[0])] for k in members),'original legal base members')
    return members


def transaction(rules,spec,proposal,trace,chosen):
    members=set(F(proposal['members']));pending=set(members);used=F(chosen)
    for step in trace['steps']:
        ds=A.domains(rules,spec,used);kind,p,keys=A.decide(ds);key=F(step['key'])
        N((step['kind'],F(step['point']))==(kind,p),'every constituent uses global scheduler')
        if kind=='forced':N(key==keys[0],'global forced member or other base tile')
        else:
            N(kind=='branch','no placement past dead or complete')
            options=sorted(k for k in pending if k in keys)
            N(options and key==options[0],'earliest selected frontier constituent')
        N(step['role']==('member' if key in pending else 'global_forced'),'actual transaction role')
        used+=(key,);pending.discard(key)
    kind,p,keys=A.decide(A.domains(rules,spec,used))
    status=trace['status']
    if status=='accepted_cluster':N(not pending and kind!='dead','complete viable transaction')
    elif status=='rejected_dead':N(kind=='dead','actual global dead end')
    elif status=='rejected_empty':N(kind=='empty' and pending,'incomplete cluster')
    elif status=='rejected_scheduler':
        N(pending and kind=='branch' and not any(k in keys for k in pending),'actual scheduler interruption')
    elif status=='unknown_transaction_budget':N(bool(pending),'open budget transaction')
    else:raise ValueError('unknown transaction status')
    return used if status=='accepted_cluster' else None


def vector(proposal,rules,spec,chosen):
    if proposal is None:return (0,0,0,0,1)
    slots=[k[0] for k in proposal['members']]
    return (len(slots)/6,int(rules[proposal['members'][-1][1]]['output']==F(spec['target'])),
            len(chosen)/(spec['bound']+1),len(slots)/(max(slots)-min(slots)+1),0)


def close(a,b):
    N(len(a)==len(b) and all(abs(x-y)<1e-11 for x,y in zip(a,b)),'numeric controller replay')


def policy_event(event,rules,spec,templates,weights,stochastic,rng,chosen,point):
    N(F(event['chosen'])==chosen and F(event['point'])==point,'policy context')
    for p in event['items']:item(rules,spec,templates,p,chosen)
    fs=[vector(None,rules,spec,chosen)]+[vector(p,rules,spec,chosen) for p in event['items']]
    N(F(event['features'])==F(fs),'actual proposal features')
    scores=[sum(x*y for x,y in zip(weights,f)) for f in fs]
    scale=max(scores);mass=[math.exp(s-scale) for s in scores];probs=[x/sum(mass) for x in mass]
    close(probs,event['probabilities'])
    if stochastic:
        draw=rng.random();N(draw==event['draw'],'on-policy seeded draw')
        index=len(probs)-1;acc=0
        for j,p in enumerate(probs):
            acc+=p
            if draw<acc:index=j;break
    else:
        N(event['draw'] is None,'deterministic evaluation')
        index=max(range(len(scores)),key=lambda i:(scores[i],-i))
    N(index==event['selected'],'actual selected cluster or defer')
    gradient=[fs[index][j]-sum(p*f[j] for p,f in zip(probs,fs)) for j in range(5)]
    close(gradient,event['gradient'])
    return None if index==0 else event['items'][index-1]


def result(rules,spec,templates,r):
    counts=collections.Counter();events=r['policy_events'];event_index=0;leaf=None;rng=random.Random(r['seed'])
    def visit(t,chosen):
        nonlocal event_index,leaf
        ds=A.domains(rules,spec,chosen);kind,p,keys=A.decide(ds)
        N((t['kind'],F(t['point']))==(kind,p),'full base-domain scheduler')
        counts['nodes']+=1
        counts['peak_candidates']=max(counts['peak_candidates'],sum(map(len,ds.values())))
        if t.get('cutoff')=='entry_wall':return None
        if kind=='dead':counts['dead']+=1;return False
        if kind=='empty':leaf=chosen;return True
        counts[kind]+=1
        selected=None
        if 'policy_event' in t:
            N(kind=='branch' and t['policy_event']==event_index,'sequential policy events')
            selected=policy_event(events[event_index],rules,spec,templates,r['weights'],r['stochastic'],rng,chosen,p)
            event_index+=1
        if 'policy_event' in t:
            N(bool(t['proposals'])==(selected is not None),'executed on-policy action')
            if selected is not None:N(F(t['proposals'][0]['item'])==F(selected),'exact chosen proposal')
        for trial in t['proposals']:
            N(kind=='branch','macros cannot bypass forced propagation')
            item(rules,spec,templates,trial['item'],chosen)
            counts['proposal_trials']+=1
            trace=trial['trace'];counts['attempts']+=len(trace['steps'])
            counts['constituent_steps']+=len(trace['steps'])
            counts['constituent_forced']+=sum(x['kind']=='forced' for x in trace['steps'])
            counts['constituent_branches']+=sum(x['kind']=='branch' for x in trace['steps'])
            continuation=transaction(rules,spec,trial['item'],trace,chosen)
            if trace['status']=='unknown_transaction_budget':return None
            if continuation is None:counts['rejected_transactions']+=1
            else:
                counts['accepted_transactions']+=1
                success=visit(trial['tree'],continuation)
                if success is not False:return success
                counts['backtracks']+=1
        seen=[]
        for child in t['children']:
            key=F(child['key'])
            N(key in keys and key not in seen,'original incident alternative')
            N(key==keys[len(seen)],'unchanged fallback order')
            seen.append(key);counts['attempts']+=1;counts['singleton_attempts']+=1
            success=visit(child['tree'],chosen+(key,))
            if success is not False:return success
            counts['backtracks']+=1
        if t.get('cutoff')=='base_before_placement':return None
        N(len(seen)==len(keys),'all original alternatives before exhaustion')
        return False
    success=visit(r['search_tree'],())
    expected='finite_exact_proof_region' if success else 'unknown_search_budget' if success is None else 'exhausted_finite_region'
    N(r['status']==expected,'reported search outcome')
    N(event_index==len(events),'all and only executed policy events')
    for k,v in counts.items():N(r['metrics'].get(k,0)==v,'search cost '+k)
    h=len(spec['hypotheses']);universe=spec['bound']+1+spec['bound']+int(bool(h))
    universe+=sum(sum(1 for refs in itertools.product(range(-h,j),repeat=len(row['inputs']))
                       if all(refs[a]!=refs[b] or row['inputs'][a]==row['inputs'][b]
                              for a in range(len(refs)) for b in range(a)))
                  for j in range(spec['bound']) for row in rules)
    N(r['candidate_universe']==universe,'identical complete base inventory')
    if success:
        N(leaf==F(r['placements']),'actual successful base witness')
        A.certificate(rules,spec,r,r['tiles'])
        request=F(r['compiled']['request'])
        theory=F(spec['theory']);actual_theory=F(request['theory'])
        N(actual_theory==dict(theory,axioms={**theory['axioms'],**{'premise-'+str(i):F(a) for i,a in enumerate(spec['hypotheses'])}}),
          'every premise and original theory bound')
        commands=[dict(rule='axiom',formula=F(a),name='premise-'+str(i)) for i,a in enumerate(spec['hypotheses'])]
        for row in F(r['proof']):
            N(row['kind']=='mp','direct primitive inference')
            a,b=row['refs']
            commands.append(dict(rule='mp',formula=row['formula'],antecedent=a+h,implication=b+h))
        N(request['target']==F(spec['target']) and not request['blocks'] and F(request['proof'])==F(commands),
          'no added oracle or different conclusion')
        N(replay(P(request))['status']=='accepted','independent host kernel')
    return dict(status='accepted',outcome=success,**counts)


def training_update(weights,baseline,r,u):
    reward=int(r['status']=='finite_exact_proof_region')-math.log1p(r['metrics'].get('attempts',0))/math.log1p(r['limits']['attempts'])
    events=r['policy_events'];gradient=[sum(e['gradient'][j] for e in events)/max(1,len(events)) for j in range(5)]
    N(abs(reward-u['reward'])<1e-12 and baseline==u['baseline_before'] and u['rate']==.15,'verified episode return')
    close(gradient,u['gradient'])
    next_weights=[max(-6,min(6,w+.15*(reward-baseline)*g)) for w,g in zip(weights,gradient)]
    close(next_weights,u['weights_after'])
    return next_weights,.9*baseline+.1*reward
