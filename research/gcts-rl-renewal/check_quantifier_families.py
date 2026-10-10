"""Independent explicit replay for scoped formula-context families.

Does not import the producer, its logic routines, patterns, matcher, index,
domain factors or controller. Frozen point/primitive verifiers supply syntax
and complete original candidate enumeration. Bound-variable normalization and
typed context matching below are a separate implementation.
"""
import collections,itertools,math,random
import check_resumable_clusters as W
V,A,F,N=W.V,W.A,W.F,W.N
FIXED=W.FIXED
reviewed=W.reviewed
FIELDS=('kind','inputs','output','parameters','guards')

def alpha(a):
    def tm(t,names):
        if t[0]=='var':return ('bound',names.index(t[1])) if t[1] in names else t
        return ('fun',t[1],tuple(tm(v,names) for v in t[2]))
    def fm(b,names):
        k=b[0]
        if k=='all':return ('all',fm(b[2],[b[1]]+names))
        if k=='pred':return ('pred',b[1],tuple(tm(v,names) for v in b[2]))
        if k=='eq':return ('eq',tm(b[1],names),tm(b[2],names))
        return (k,)+tuple(fm(v,names) for v in b[1:])
    return fm(a,[])

def term_nodes(a):
    def visit(t):
        yield t
        if t[0]=='fun':
            for v in t[2]:yield from visit(v)
    if a[0]=='pred':
        for t in a[2]:yield from visit(t)
    elif a[0]=='eq':yield from visit(a[1]);yield from visit(a[2])
    else:
        for b in a[1:]:yield from term_nodes(b)

def has_bound(t):return t[0]=='bound' or (t[0]=='fun' and any(has_bound(v) for v in t[2]))

def alter(a,needle,replacement):
    def t(v):
        if v==needle:return replacement
        if v[0]=='fun':return ('fun',v[1],tuple(t(w) for w in v[2]))
        return v
    if a[0]=='pred':return ('pred',a[1],tuple(t(v) for v in a[2]))
    if a[0]=='eq':return ('eq',t(a[1]),t(a[2]))
    return (a[0],)+tuple(alter(v,needle,replacement) for v in a[1:])

def add(binding,name,value):
    if name in binding and binding[name]!=value:return None
    return {**binding,name:value}

def typed(p,t,e):
    if p[0]=='tmeta':return add(e,p[1],t)
    if t[0]!='fun' or len(p[2])!=len(t[2]):return None
    e=add(e,p[1],('symbol',t[1],len(t[2])))
    for left,right in zip(p[2],t[2]):
        if e is None:return None
        e=typed(left,right,e)
    return e

def value(p,e):
    if p[0]=='tmeta':return e.get(p[1])
    args=[value(v,e) for v in p[2]]
    return ('fun',e[p[1]][1],tuple(args)) if p[1] in e and all(v is not None for v in args) else None

def match_formula(p,a,e):
    if p[0]=='fmeta':
        out=add(e,p[1],alpha(a));return [] if out is None else [out]
    if p[0]=='papply':
        n=alpha(a);actual=value(p[2],e)
        choices=[actual] if actual is not None else sorted({t for t in term_nodes(n) if not has_bound(t)},key=V.digest)
        answers=[]
        for t in choices:
            q=typed(p[2],t,e)
            if q is None:continue
            if p[1] in q:
                if alter(q[p[1]],('hole',),t)==n:answers.append(q)
            else:
                ctx=alter(n,t,('hole',))
                if ('hole',) in set(term_nodes(ctx)):answers.append({**q,p[1]:ctx})
        return answers
    if p[0]!=a[0]:return []
    if p[0]=='all':
        q=typed(p[1],('var',a[1]),e)
        return [] if q is None else match_formula(p[2],a[2],q)
    if p[0]=='eq':
        q=typed(p[1],a[1],e);q=typed(p[2],a[2],q) if q is not None else None
        return [] if q is None else [q]
    if len(p)!=len(a):return []
    out=[e]
    for left,right in zip(p[1:],a[1:]):out=[q for prior in out for q in match_formula(left,right,prior)]
    return out

def matching(p,r):
    if p['kind']!=r['kind'] or len(p['inputs'])!=len(r['inputs']) or len(p['guards'])!=len(r['guards']):return []
    envs=[{}]
    for key,v in p['parameters'].items():
        a=r['parameters'][key]
        if key=='side':envs=envs if v==a else [];continue
        if key=='variable':a=('var',a)
        envs=[q for e in envs for q in [typed(v,a,e)] if q is not None]
    for v,x in zip(p['guards'],r['guards']):envs=[q for e in envs for q in [typed(v,('var',x),e)] if q is not None]
    for v,a in zip(p['inputs']+(p['output'],),r['inputs']+(r['output'],)):
        envs=[q for e in envs for q in match_formula(v,a,e)]
    unique={V.digest(e):e for e in envs};return [unique[k] for k in sorted(unique)]

def names(v):
    if isinstance(v,dict):return set().union(*(names(x) for x in v.values()))
    if not isinstance(v,(tuple,list)):return set()
    own={v[1]} if v and v[0] in ('tmeta','papply','fmeta','fapply') else set()
    return own|set().union(*(names(x) for x in v))

def pattern_for(rules,members):
    inside={k[0]:i for i,k in enumerate(members)};outside={};free={};quant={};predicates={};functions={};serial=0
    def fresh():
        nonlocal serial
        out=('tmeta','T'+str(serial));serial+=1;return out
    def variable(x):
        if x not in free:free[x]=fresh()
        return free[x]
    for _,rid,_ in members:
        row=rules[rid]
        if row['kind']=='generalize':quant[row['output']]=variable(row['parameters']['variable'])
    def term(t,local):
        if t[0]=='var':return local.get(t[1]) or variable(t[1])
        symbol=(t[1],len(t[2]));functions.setdefault(symbol,'F'+str(len(functions)))
        return ('fapply',functions[symbol],tuple(term(v,local) for v in t[2]))
    def formula(a,local=None):
        local=dict(local or {});k=a[0]
        if k=='all':
            if a not in quant:quant[a]=fresh()
            local[a[1]]=quant[a];return ('all',quant[a],formula(a[2],local))
        if k=='pred':
            N(len(a[2])<=1,'unary/nullary donor signature')
            symbol=(a[1],len(a[2]));predicates.setdefault(symbol,'P'+str(len(predicates)))
            return ('papply',predicates[symbol],term(a[2][0],local)) if a[2] else ('fmeta',predicates[symbol])
        if k=='eq':return ('eq',term(a[1],local),term(a[2],local))
        return (k,)+tuple(formula(v,local) for v in a[1:])
    pattern=[]
    for _,rid,refs in members:
        r=rules[rid];N(r['kind'] in ('mp','forall-elim','generalize','projection'),'mined supported primitive')
        contacts=[]
        for ref in refs:
            if ref in inside:contacts.append(('inside',inside[ref]))
            else:outside.setdefault(ref,len(outside));contacts.append(('outside',outside[ref]))
        params={k:v if k=='side' else variable(v) if k=='variable' else term(v,{}) for k,v in r['parameters'].items() if k!='universal'}
        pattern.append(dict(kind=r['kind'],parameters=params,guards=[variable(x) for x in r['guards']],
            inputs=[formula(a) for a in r['inputs']],output=formula(r['output']),refs=contacts))
    return F(pattern)

def check_item(rules,spec,templates,proposal,chosen=()):
    t=templates[proposal['template']];members=F(proposal['members']);bindings=F(proposal['bindings']);pattern=F(t['pattern'])
    slots=[k[0] for k in members];N(len(members)==len(pattern) and slots==sorted(set(slots)),'distinct increasing original members')
    N(proposal['level']==t['level'],'same inventory family')
    filled,ports,marks=A.state(rules,spec,chosen);ds=A.domains(rules,spec,chosen);totals=collections.Counter();union={}
    external={str(k):v for k,v in proposal['outside'].items()}
    for i,(key,node) in enumerate(zip(members,pattern)):
        j,rid,refs=key;N(rid>=0 and key in ds[A.cell(j)],'original legal primitive candidate');r=rules[rid]
        N(any(all(bindings.get(k)==v for k,v in e.items()) for e in matching(node,r)),'exact typed term/context instance')
        for (kind,index),ref,a in zip(node['refs'],refs,r['inputs']):
            if kind=='inside':N(index<i and ref==slots[index],'acyclic internal receptor')
            else:N(external.get(str(index))==ref and ref<j and (ref<0 or ref in filled) and ports.get(ref)==a,'actually available external receptor')
        tile=A.tile(rules,spec,key)
        for p,v in tile['occupancy']:totals[p]+=v;N(totals[p]<=12,'original aggregate capacity')
        for p,v in tile['marks']:N(p not in union or union[p]==v,'original aggregate agreement');union[p]=v
    N(F(proposal['occupancy'])==tuple(sorted(totals.items())) and F(proposal['marks'])==tuple(sorted(union.items())),'all and only original aggregate values')
    N(all(p not in marks or marks[p]==v for p,v in union.items()),'exact current interface')
    return members

class Replay:
    def __init__(self,rules,templates):
        self.rules=rules;self.declared={};self.nodes={};self.queries=[];self.q=set();self.a=set();self.d=set();self.counts=collections.Counter()
        for t in sorted(templates.values(),key=lambda t:(-len(t['pattern']),t['name'])):
            for p in F(t['pattern']):self.declared.setdefault(V.digest({k:p[k] for k in FIELDS}),p)
    def query(self,p,env):
        pin=V.digest({k:p[k] for k in FIELDS});p=self.declared[pin]
        variables=tuple(sorted(names({k:p[k] for k in FIELDS})))
        if pin not in self.nodes:
            rows=[]
            for rid,r in enumerate(self.rules):
                if r['kind']==p['kind']:
                    self.counts['syntax_rule_tests']+=1
                    rows.extend((rid,e) for e in matching(p,r))
            self.nodes[pin]=dict(node=p,variables=variables,rows=tuple(rows));self.counts['ground_matches']+=len(rows)
        bound=tuple((k,env[k]) for k in variables if k in env);key=(pin,bound)
        self.queries.append(dict(node=pin,bound=bound));self.counts['queries']+=1
        self.counts['query_cache_hits' if key in self.q else 'query_cache_misses']+=1;self.q.add(key)
        return [(rid,e) for rid,e in self.nodes[pin]['rows'] if all(e.get(k)==v for k,v in bound)]
    def aggregate(self,members):
        self.counts['aggregate_cache_hits' if members in self.a else 'aggregate_cache_misses']+=1;self.a.add(members)
    def ordered(self,item):
        key=(item['template'],item['members']);self.counts['item_digest_hits' if key in self.d else 'item_digest_misses']+=1;self.d.add(key)

def proposal_pool(rules,spec,templates,chosen,point,limit,recorder):
    filled,ports,marks=A.state(rules,spec,chosen);ds=A.domains(rules,spec,chosen)
    available={j:a for j,a in ports.items() if j<0 or j in filled};slots=sorted(p[0]//2 for p in ds if p[0]//2<spec['bound']);pool={};scanned=0
    for t in sorted(templates.values(),key=lambda t:(-len(t['pattern']),t['name'])):
        for embedding in itertools.combinations(slots,len(t['pattern'])):
            if point[0]//2 not in embedding:continue
            partial=[((),{},{})]
            for i,node in enumerate(F(t['pattern'])):
                following=[];j=embedding[i]
                for members,env,outside in partial:
                    rows=recorder.query(node,env);scanned+=len(rows)
                    for rid,local in rows:
                        binding={**env,**local};r=rules[rid];choices=[]
                        for (kind,ref),a in zip(node['refs'],r['inputs']):
                            if kind=='inside':N(ref<i,'acyclic family');choices.append((embedding[ref],))
                            elif str(ref) in outside:
                                v=outside[str(ref)];choices.append((v,) if available.get(v)==a and v<j else ())
                            else:choices.append(tuple(v for v,b in sorted(available.items()) if v<j and b==a))
                        for refs in itertools.product(*choices):
                            key=(j,rid,refs)
                            if key not in ds[A.cell(j)]:continue
                            ext=dict(outside);okay=True
                            for (kind,ref),v in zip(node['refs'],refs):
                                if kind=='outside':
                                    if str(ref) in ext and ext[str(ref)]!=v:okay=False;break
                                    ext[str(ref)]=v
                            if okay:following.append((members+(key,),binding,ext))
                partial=following
                if not partial:break
            for members,binding,outside in partial:
                if members in pool:recorder.counts['duplicate_expansions']+=1;continue
                recorder.aggregate(members);totals=collections.Counter();union={};okay=True
                for key in members:
                    tile=A.tile(rules,spec,key)
                    for p,v in tile['occupancy']:totals[p]+=v
                    for p,v in tile['marks']:
                        if p in union and union[p]!=v:okay=False
                        union[p]=v
                if not okay or any(v>12 for v in totals.values()) or any(p in marks and marks[p]!=v for p,v in union.items()):continue
                pool[members]=dict(template=t['name'],members=members,bindings=binding,outside=outside,level=t['level'],
                    occupancy=tuple(sorted(totals.items())),marks=tuple(sorted(union.items())))
    for p in pool.values():recorder.ordered(p)
    ordered=sorted(pool.values(),key=lambda t:(-int(rules[t['members'][-1][1]]['output']==F(spec['target'])),-len(t['members']),V.digest(t)))
    return ordered[:limit],dict(compatible=len(ordered),scanned=scanned,truncated=max(0,len(ordered)-limit))

def policy_event(event,rules,spec,templates,weights,stochastic,rng,chosen,point):
    N(F(event['chosen'])==chosen and F(event['point'])==point,'policy context')
    for p in event['items']:check_item(rules,spec,templates,p,chosen)
    fs=[V.vector(None,rules,spec,chosen)]+[V.vector(p,rules,spec,chosen) for p in event['items']]
    N(F(event['features'])==F(fs),'all actual proposal features')
    scores=[sum(x*y for x,y in zip(weights,f)) for f in fs];scale=max(scores);mass=[math.exp(s-scale) for s in scores];prob=[x/sum(mass) for x in mass];V.close(prob,event['probabilities'])
    if stochastic:
        draw=rng.random();N(draw==event['draw'],'fresh seeded on-policy draw');index=len(prob)-1;acc=0
        for j,p in enumerate(prob):
            acc+=p
            if draw<acc:index=j;break
    else:N(event['draw'] is None,'deterministic evaluation');index=max(range(len(scores)),key=lambda i:(scores[i],-i))
    N(index==event['selected'],'actual cluster or defer action')
    gradient=[fs[index][j]-sum(p*f[j] for p,f in zip(prob,fs)) for j in range(5)];V.close(gradient,event['gradient'])
    return None if index==0 else event['items'][index-1]


def result(rules,spec,templates,r,atomic=False):
    rules,spec=F(rules),F(spec);counts=collections.Counter();rng=random.Random(r['seed']);events=r['policy_events'];ei=0;hi=0;leaf=None;finished=None
    N(not atomic,'this audit supports original-placement resumable search only')
    recorder=Replay(rules,templates)
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
    N(r['status']==status,'terminal or unknown result scope');N(ei==len(events),'all policy events')
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
