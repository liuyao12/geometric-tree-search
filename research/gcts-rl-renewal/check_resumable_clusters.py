"""Independent explicit domains, proposal joins, hint lifetimes and policies.

Never imports either producer, its matcher, graph factors or hint controller.
The old atomic lane is replayed through its original transaction semantics.
"""
import collections,itertools,math,random
import check_adaptive_clusters as V
from check_compact_contexts import certificate

A=V.A;F,N,P=V.F,V.N,V.P
FIXED=(1.,4.,0.,2.,-8.)

def unify(pattern,formula,binding):
    env=dict(binding)
    def bind(p,a):
        if p[0]=='meta':
            k=str(p[1])
            if k in env:return env[k]==a
            env[k]=a;return True
        return p[0]==a[0] and len(p)==len(a) and all(bind(x,y) for x,y in zip(p[1:],a[1:]))
    return env if bind(pattern,formula) else None

def proposal_pool(rules,spec,templates,chosen,point,limit):
    filled,ports,marks=A.state(rules,spec,chosen);ds=A.domains(rules,spec,chosen)
    available={j:a for j,a in ports.items() if j<0 or j in filled};slots=sorted(p[0]//2 for p in ds if p[0]//2<spec['bound'])
    pool={};scanned=0
    for t in sorted(templates.values(),key=lambda t:(-len(t['pattern']),t['name'])):
        pattern=F(t['pattern'])
        for embedding in itertools.combinations(slots,len(pattern)):
            if point[0]//2 not in embedding:continue
            states=[((),{},{})]
            for i,node in enumerate(pattern):
                following=[];j=embedding[i]
                for members,binding,outside in states:
                    for rid,r in enumerate(rules):
                        if r['kind']!=node['kind']:continue
                        env=dict(binding)
                        for p,a in zip(node['inputs']+(node['output'],),r['inputs']+(r['output'],)):
                            env=unify(p,a,env)
                            if env is None:break
                        if env is None:continue
                        scanned+=1;choices=[]
                        for (kind,k),a in zip(node['refs'],r['inputs']):
                            if kind=='inside':N(k<i,'acyclic learned pattern');vs=(embedding[k],)
                            elif str(k) in outside:
                                v=outside[str(k)];vs=(v,) if v<j and available.get(v)==a else ()
                            else:vs=tuple(v for v,b in sorted(available.items()) if v<j and b==a)
                            choices.append(vs)
                        for refs in itertools.product(*choices):
                            key=(j,rid,refs)
                            if key not in ds[A.cell(j)]:continue
                            ext=dict(outside);okay=True
                            for (kind,k),ref in zip(node['refs'],refs):
                                if kind=='outside':
                                    if str(k) in ext and ext[str(k)]!=ref:okay=False;break
                                    ext[str(k)]=ref
                            if okay:following.append((members+(key,),env,ext))
                states=following
                if not states:break
            for members,binding,outside in states:
                totals=collections.Counter();union={};okay=True
                for key in members:
                    tile=A.tile(rules,spec,key)
                    for p,v in tile['occupancy']:totals[p]+=v
                    for p,v in tile['marks']:
                        if p in union and union[p]!=v:okay=False
                        union[p]=v
                if not okay or any(v>12 for v in totals.values()) or any(p in marks and marks[p]!=v for p,v in union.items()):continue
                item=dict(template=t['name'],members=members,bindings=binding,outside=outside,level=t['level'],
                    occupancy=tuple(sorted(totals.items())),marks=tuple(sorted(union.items())))
                pool.setdefault(members,item)
    items=sorted(pool.values(),key=lambda t:(-int(rules[t['members'][-1][1]]['output']==F(spec['target'])),-len(t['members']),V.digest(t)))
    return items[:limit],dict(compatible=len(items),scanned=scanned,truncated=max(0,len(items)-limit))

def reviewed(rules,spec,chosen,active,kind,point,keys):
    if active is None:return None,dict(phase='none',pending=())
    item=active['item'];members=F(item['members']);occupied={k[0]:k for k in chosen}
    pending=tuple(k for k in members if occupied.get(k[0])!=k)
    if any(k[0] in occupied and occupied[k[0]]!=k for k in members):return None,dict(phase='dropped',reason='occupied_differently',pending=pending)
    if not pending:return None,dict(phase='completed',pending=())
    ds=A.domains(rules,spec,chosen)
    if any(k not in ds.get(A.cell(k[0]),()) for k in pending):return None,dict(phase='dropped',reason='member_no_longer_legal',pending=pending)
    marks=A.state(rules,spec,chosen)[2]
    if any(p in marks and marks[p]!=v for p,v in F(item['marks'])):return None,dict(phase='dropped',reason='interface_disagreement',pending=pending)
    eligible=tuple(sorted(k for k in pending if k in keys)) if kind in ('branch','forced') else ()
    phase='resumed' if eligible and active['waiting'] else 'continuing' if eligible else 'suspended'
    return dict(active,waiting=not bool(eligible)),dict(phase=phase,pending=pending,eligible=eligible)

def result(rules,spec,templates,r,atomic=False):
    rules,spec=F(rules),F(spec);counts=collections.Counter();rng=random.Random(r['seed']);events=r['policy_events'];ei=0;hi=0;leaf=None;finished=None
    if not atomic:N(F(r['fixed_weights'])==FIXED,'declared fixed preference weights')
    def visit(t,chosen,active=None,completed=()):
        nonlocal ei,hi,leaf,finished
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
        joins=kind=='branch' and (atomic or active is None) and templates and r['mode']!='base'
        item=None
        if joins:
            items,work=proposal_pool(rules,spec,templates,chosen,point,r['limits']['proposal_limit'])
            for k,v in work.items():counts['proposal_'+k]+=v
            if not atomic:N(F(t['proposal_pool'])==F(items),'complete declared finite proposal join')
            if r['mode']=='policy':
                N(t['policy_event']==ei and F(events[ei]['items'])==F(items),'actual complete pool and policy event sequence')
                item=V.policy_event(events[ei],rules,spec,templates,r['weights'],r['stochastic'],rng,chosen,point);ei+=1
            else:
                fs=[V.vector(None,rules,spec,chosen)]+[V.vector(i,rules,spec,chosen) for i in items]
                scores=[sum(w*x for w,x in zip(FIXED,f)) for f in fs];index=max(range(len(scores)),key=lambda i:(scores[i],-i));item=None if index==0 else items[index-1]
            if not atomic:
                N(('hint_start' in t)==(item is not None),'all and only admitted hints')
                if item is not None:
                    N(t['hint_start']==hi,'sequential hint identities');record=F(r['hints'][hi])
                    N(record==dict(id=hi,chosen=chosen,point=point,item=F(item)),'exact source context and selected family')
                    V.item(rules,spec,templates,item,chosen);active=dict(id=hi,item=F(item),waiting=False);hi+=1;counts['hint_started']+=1
                    active,start=reviewed(rules,spec,chosen,active,kind,point,keys)
                    N(active and start['eligible'] and F(t['start_review'])==F(start),'eligible initial constituent');review=start
        else:N('policy_event' not in t and ('hint_start' not in t or atomic),'no policy bypasses propagation or retained context')
        if atomic:
            N(bool(t['proposals'])==(item is not None),'actual atomic policy action')
            for trial in t['proposals']:
                N(F(trial['item'])==F(item),'same fixed candidate preference');V.item(rules,spec,templates,item,chosen)
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
    N(r['status']==status,'terminal or unknown result scope');N(ei==len(events),'all policy events')
    if not atomic:N(hi==len(r['hints']),'all hint admissions');N(not success or F(r['solution_hints'])==F(finished),'all actual completed families on the positive leaf')
    for k,v in counts.items():N(r['metrics'].get(k,0)==v,'audited work '+k)
    h=len(spec['hypotheses']);universe=spec['bound']+1+spec['bound']+int(bool(h))
    universe+=sum(sum(1 for refs in itertools.product(range(-h,j),repeat=len(row['inputs']))
        if all(refs[a]!=refs[b] or row['inputs'][a]==row['inputs'][b] for a in range(len(refs)) for b in range(a)))
        for j in range(spec['bound']) for row in rules)
    N(r['candidate_universe']==universe,'unchanged complete base universe')
    if success:
        N(leaf==F(r['placements']),'actual positive leaf');A.certificate(rules,spec,r,r['tiles']);certificate(spec,r)
    return dict(status='passed',outcome=success,**counts)

def update(weights,baseline,r,u):
    m=r['metrics'];cost=m.get('attempts',0)+.25*m.get('proposal_scanned',0)+.1*m.get('hint_reviews',0)
    reward=int(r['status']=='finite_exact_proof_region')-math.log1p(cost)/math.log1p(r['limits']['attempts'])
    gs=[e['gradient'] for e in r['policy_events']];gradient=[sum(g[j] for g in gs)/max(1,len(gs)) for j in range(5)]
    N(abs(cost-u['cost_units'])<1e-12 and abs(reward-u['reward'])<1e-12 and baseline==u['baseline_before'] and u['rate']==.15,'verified charged return')
    V.close(gradient,u['gradient']);after=[max(-6,min(6,w+.15*(reward-baseline)*g)) for w,g in zip(weights,gradient)];V.close(after,u['weights_after'])
    return after,.9*baseline+.1*reward
