"""Independent full enumeration of request gates and original proof search.

Uses the frozen independent context matcher, not the producer gate, graph
factors, index or controller. The complete scheduler/fallback replay is copied
from the frozen quantified checker and extended before its join decision.
"""
import collections,itertools,math,random
import check_quantifier_families as Q
V,A,F,N,W=Q.V,Q.A,Q.F,Q.N,Q.W
Replay,proposal_pool,policy_event,check_item=Q.Replay,Q.proposal_pool,Q.policy_event,Q.check_item
reviewed,FIXED=Q.reviewed,Q.FIXED
FEATURES=('bias','log_region','log_frontier','log_degree','progress','selected_position','known_ports','forbidden_fraction')

def gate_event(event,rules,spec,chosen,domains,point,weights,stochastic,rng):
    N(F(event['chosen'])==chosen and F(event['point'])==point,'request attached to actual complete graph')
    filled,ports,marks=A.state(rules,spec,chosen);n=spec['bound']+1;h=len(spec['hypotheses'])
    blocked=sum(marks[(-1000,j)]!=0 for j in range(len(spec['variables'])))
    fs=(1.,math.log1p(spec['bound'])/4,math.log1p(len(domains))/4,math.log1p(len(domains[point]))/8,
        len(chosen)/n,point[0]/(2*n),len(ports)/(n+h),blocked/max(1,len(spec['variables'])))
    V.close(fs,event['features']);score=sum(w*x for w,x in zip(weights,fs));V.close([score],[event['score']])
    shift=max(0.,score);masses=(math.exp(-shift),math.exp(score-shift));probs=tuple(x/sum(masses) for x in masses)
    V.close(probs,event['probabilities'])
    if stochastic:
        draw=rng.random();N(draw==event['draw'],'seeded pre-join draw');selected=int(draw<probs[1])
    else:N(event['draw'] is None,'deterministic request action');selected=int(score>0)
    N(selected==event['selected'],'actual request or defer action')
    V.close(tuple((selected-probs[1])*x for x in fs),event['gradient'])
    return bool(selected)

def update(weights,baseline,result,record):
    N(record['observed_total_seconds']==result['total_seconds'],'inclusive observed solve-time binding')
    reward=int(result['status']=='finite_exact_proof_region')-math.log1p(result['total_seconds']/.001)/math.log1p(result['limits']['seconds']/.001)
    events=result['gate_events'];g=[sum(e['gradient'][j] for e in events)/max(1,len(events)) for j in range(8)]
    N(record['rate']==.35 and record['baseline_before']==baseline,'declared learning schedule')
    after=[min(6.,max(-6.,w+.35*(reward-baseline)*x)) for w,x in zip(weights,g)]
    V.close([reward],[record['reward']]);V.close(g,record['gradient']);V.close(after,record['weights_after'])
    return after,.9*baseline+.1*reward

def result(rules,spec,templates,r,atomic=False):
    rules,spec=F(rules),F(spec);counts=collections.Counter();rng=random.Random(r['seed']);events=r['policy_events'];ei=0;hi=0;gi=0;gates=r['gate_events'];leaf=None;finished=None
    N(not atomic,'this audit supports original-placement resumable search only')
    N(tuple(r['gate_features'])==FEATURES,'declared cheap features')
    N(r['mode'] in ('base','fixed','policy','gated'),'declared search mode')
    N(r['mode']=='gated' or not gates,'no gate on frozen controls')
    N(r['mode']!='gated' or len(r['gate_weights'])==8,'request policy dimension')
    recorder=Replay(rules,templates)
    if not atomic:N(F(r['fixed_weights'])==FIXED,'declared fixed preference weights')
    def visit(t,chosen,active=None,completed=()):
        nonlocal ei,hi,gi,leaf,finished
        ds=A.domains(rules,spec,chosen);kind,point,keys=A.decide(ds);counts['nodes']+=1
        counts['peak_candidates']=max(counts['peak_candidates'],sum(map(len,ds.values())))
        N((t['kind'],F(t['point']))==(kind,point),'complete global scheduler')
        if t.get('cutoff')=='entry_wall':return None
        if not atomic:
            N(t['hint_in']==(active['id'] if active else None),'inherited branch-local hint')
            prior=active;active,review=reviewed(rules,spec,chosen,active,kind,point,keys)
            N(F(t['review'])==F(review),'entire pending set, expiry and resumption')
            if prior:
                counts['hint_reviews']+=1;counts['hint_'+review['phase']]+=1
                if review['phase']=='completed':
                    record=r['hints'][prior['id']]
                    completed+=(dict(id=prior['id'],start=len(record['chosen']),end=len(chosen),item=prior['item']),)
        if kind=='dead':counts['dead']+=1;return False
        if kind=='empty':leaf=chosen;finished=completed;return True
        counts[kind]+=1
        eligible=kind=='branch' and active is None and bool(templates)
        if eligible and r['mode']=='gated':
            N(t.get('gate_event')==gi and gates[gi]['id']==gi,'all sequential request decisions')
            requested=gate_event(gates[gi],rules,spec,chosen,ds,point,r['gate_weights'],r['stochastic'],rng)
            gi+=1;counts['gate_decisions']+=1;counts['gate_queries' if requested else 'gate_deferrals']+=1
        else:
            N('gate_event' not in t,'no request bypasses global propagation or retained hints')
            requested=eligible and r['mode']!='base'
        joins=requested
        if not joins:N('proposal_pool' not in t,'deferral constructs no family pool')
        item=None
        if joins:
            items,work=proposal_pool(rules,spec,templates,chosen,point,r['limits']['proposal_limit'],recorder)
            for k,v in work.items():counts['proposal_'+k]+=v
            if not atomic:N(F(t['proposal_pool'])==F(items),'complete declared finite proposal join')
            if r['mode']=='policy':
                N(t['policy_event']==ei and F(events[ei]['items'])==F(items),'actual complete pool and policy event sequence')
                item=policy_event(events[ei],rules,spec,templates,r['weights'],r['stochastic'],rng,chosen,point);ei+=1
            else:
                fs=[V.vector(None,rules,spec,chosen)]+[V.vector(i,rules,spec,chosen) for i in items]
                scores=[sum(w*x for w,x in zip(FIXED,f)) for f in fs];index=max(range(len(scores)),key=lambda i:(scores[i],-i));item=None if index==0 else items[index-1]
            if not atomic:
                N(('hint_start' in t)==(item is not None),'all and only admitted hints')
                if item is not None:
                    N(t['hint_start']==hi,'sequential hint identities');record=F(r['hints'][hi])
                    N(record==dict(id=hi,chosen=chosen,point=point,item=F(item)),'exact source context and selected family')
                    check_item(rules,spec,templates,item,chosen);active=dict(id=hi,item=F(item),waiting=False);hi+=1;counts['hint_started']+=1
                    active,start=reviewed(rules,spec,chosen,active,kind,point,keys)
                    N(active and start['eligible'] and F(t['start_review'])==F(start),'eligible initial constituent');review=start
        else:N('policy_event' not in t and ('hint_start' not in t or atomic),'no policy bypasses propagation or retained context')
        if atomic:
            N(bool(t['proposals'])==(item is not None),'actual atomic policy action')
            for trial in t['proposals']:
                N(F(trial['item'])==F(item),'same fixed candidate preference');check_item(rules,spec,templates,item,chosen)
                tr=trial['trace'];counts['proposal_trials']+=1;counts['attempts']+=len(tr['steps']);counts['constituent_steps']+=len(tr['steps'])
                counts['constituent_forced']+=sum(a['kind']=='forced' for a in tr['steps']);counts['constituent_branches']+=sum(a['kind']=='branch' for a in tr['steps'])
                continuation=V.transaction(rules,spec,item,tr,chosen)
                if tr['status']=='unknown_transaction_budget':return None
                if continuation is None:counts['rejected_transactions']+=1
                else:
                    counts['accepted_transactions']+=1;ok=visit(trial['tree'],continuation)
                    if ok is not False:return ok
                    counts['backtracks']+=1
            expected=keys
        else:
            pending=review.get('pending',()) if active else ()
            preferred=sorted(k for k in pending if k in keys) if kind=='branch' else []
            expected=preferred+[k for k in keys if k not in preferred]
        used=[]
        for child in t['children']:
            key=F(child['key']);N(len(used)<len(expected) and key==expected[len(used)],'complete nonduplicated fallback order')
            used.append(key);counts['attempts']+=1
            if atomic:counts['singleton_attempts']+=1
            else:
                role='member' if active and key in pending else 'unrelated' if active else 'base'
                N(child['role']==role,'actual pending or unrelated placement');counts['role_'+role]+=1
            ok=visit(child['tree'],chosen+(key,),active,completed)
            if ok is not False:return ok
            counts['backtracks']+=1
        if t.get('cutoff') in ('before_placement','base_before_placement'):return None
        N(len(used)==len(expected),'every original alternative before exhaustion');return False
    success=visit(r['search_tree'],())
    status='finite_exact_proof_region' if success else 'unknown_search_budget' if success is None else 'exhausted_finite_region'
    N(r['status']==status,'terminal or unknown result scope');N(ei==len(events),'all policy events');N(gi==len(gates),'all request decisions')
    if not atomic:N(hi==len(r['hints']),'all hint admissions');N(not success or F(r['solution_hints'])==F(finished),'all actual completed families on the positive leaf')
    for k,v in counts.items():N(r['metrics'].get(k,0)==v,'audited work '+k)
    h=len(spec['hypotheses']);universe=spec['bound']+1+spec['bound']+int(bool(h))
    universe+=sum(sum(1 for refs in itertools.product(range(-h,j),repeat=len(row['inputs']))
        if all(refs[a]!=refs[b] or row['inputs'][a]==row['inputs'][b] for a in range(len(refs)) for b in range(a)))
        for j in range(spec['bound']) for row in rules)
    N(r['candidate_universe']==universe,'unchanged complete base universe')
    if success:
        N(leaf==F(r['placements']),'actual positive leaf');A.certificate(rules,spec,r,r['tiles']);W.certificate(spec,r)
    index=F(r['index'])
    if index is not None:
        N(index['nodes']==recorder.nodes,'every complete typed syntax table')
        N(index['queries']==F(recorder.queries),'all scoped matching queries in exact tree order')
        N(all(index['metrics'].get(k,0)==v for k,v in recorder.counts.items()),'every index and cache counter')
        N(set(index['metrics'])<=set(recorder.counts)|{'ground_matches'},'all index work explained')
        N(index['context']==A.context_hash(dict(rules=rules,formulas=spec['_formulas'],variables=spec['variables'],terms=spec['terms'],rounds=spec['rounds'],generalization_rounds=spec['generalization_rounds']),spec),'immutable model binding')
        ordered=sorted(templates.values(),key=lambda t:(-len(t['pattern']),t['name']))
        N(index['library_pin']==V.digest([(t['name'],t['pattern'],t['level']) for t in ordered]),'immutable inventory binding')
        N(0<=index['build_seconds']<=r['seconds'],'cold construction charged')
    else:N(not recorder.queries,'all and only actual lazy indexes')
    return dict(status='passed',outcome=success,index_queries=len(recorder.queries),**counts)
