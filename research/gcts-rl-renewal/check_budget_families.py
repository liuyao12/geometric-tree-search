"""Independent literal domains, family joins, justified features and full trees.

Imports only frozen independent point, syntax and sampled-policy verifiers.
No producer graph, marking synthesis, matcher, support or search is imported.
"""
import collections,itertools,math,random,hashlib
import check_dependency_budget as D
import check_quantifier_families as Q
import check_receptor_attention as Old

A,F,N=D.A,D.F,D.N

class Replay(Q.Replay):
    def ordered(self,item):
        key=(item['template'],item['members'])
        self.counts['item_order_hits' if key in self.d else 'item_order_misses']+=1
        self.d.add(key)
FEATURES=('family','cells','concludes_target','justified_goal_gain','last_goal',
          'internal_fraction','hypothesis_fraction','compactness','level',
          'progress_family','guard_fraction','defer')

def established(rules,spec,chosen):
    occupied={k[0]:k for k in F(chosen)}
    known={i:a for i,a in enumerate(F(spec['hypotheses']),-len(spec['hypotheses']))}
    for i in range(spec['bound']):
        if i not in occupied:continue
        _,rid,refs=occupied[i]
        if rid>=0:
            row=rules[rid]
            if all(ref in known and known[ref]==a for ref,a in zip(refs,row['inputs'])):
                known[i]=row['output']
    return known

def vector(item,rules,spec,chosen,levels,feature_mode):
    if feature_mode=='occupied':return Old.vector(item,rules,spec,chosen,levels)
    if item is None:return (0.,)*11+(1.,)
    relevance=lambda a:1/(1+levels[a]) if a in levels else 0.
    members=F(item['members']);slots={k[0] for k in members};rows=[rules[k[1]] for k in members]
    before=max(map(relevance,established(rules,spec,chosen).values()),default=0.)
    prospective={k[0]:k for k in chosen}
    for key in members:prospective.setdefault(key[0],key)
    after=max(map(relevance,established(rules,spec,tuple(prospective.values())).values()),default=0.)
    refs=[j for key in members for j in key[2]]
    return (1.,len(members)/6,int(rows[-1]['output']==F(spec['target'])),after-before,
        relevance(rows[-1]['output']),sum(j in slots for j in refs)/max(1,len(refs)),
        sum(j<0 for j in refs)/max(1,len(refs)),len(slots)/(max(slots)-min(slots)+1),
        item['level']/2,len(chosen)/(spec['bound']+1),sum(bool(r['guards']) for r in rows)/len(rows),0.)

def aggregate(rules,spec,members,required):
    totals=collections.Counter();marks={}
    for key in members:
        tile=D.tile(rules,spec,key,required)
        for p,v in tile['occupancy']:totals[p]+=v;N(totals[p]<=12,'exact cluster capacities')
        for p,v in tile['marks']:N(p not in marks or marks[p]==v,'exact cluster marking union');marks[p]=v
    return dict(occupancy=tuple(sorted(totals.items())),marks=tuple(sorted(marks.items())))

def check_item(rules,spec,templates,item,chosen,required):
    original=dict(item,marks=[(p,v) for p,v in item['marks'] if p[0]!=-3000])
    members=Q.check_item(rules,spec,templates,original,chosen)
    N(F({k:item[k] for k in ('occupancy','marks')})==F(aggregate(rules,spec,members,required)),'all decorated aggregate values')
    ds=D.domains(rules,spec,chosen,required);_,marks=D.state(rules,spec,chosen,required)
    N(all(k in ds[A.cell(k[0])] for k in members),'all decorated constituent candidates')
    N(all(p not in marks or marks[p]==v for p,v in F(item['marks'])),'distant current interface')
    return members

def reviewed(active,chosen,kind,point,keys,domains,marks):
    if active is None:return None,dict(phase='none',pending=())
    members=F(active['item']['members']);filled={k[0]:k for k in chosen}
    pending=tuple(k for k in members if filled.get(k[0])!=k)
    if any(k[0] in filled and filled[k[0]]!=k for k in members):return None,dict(phase='dropped',reason='occupied_differently',pending=pending)
    if not pending:return None,dict(phase='completed',pending=())
    if any(k not in domains.get(A.cell(k[0]),()) for k in pending):return None,dict(phase='dropped',reason='member_no_longer_legal',pending=pending)
    if any(p in marks and marks[p]!=v for p,v in F(active['item']['marks'])):return None,dict(phase='dropped',reason='interface_disagreement',pending=pending)
    eligible=tuple(sorted(k for k in pending if k in keys)) if kind in ('branch','forced') else ()
    phase='resumed' if eligible and active['waiting'] else 'continuing' if eligible else 'suspended'
    return dict(active,waiting=not bool(eligible)),dict(phase=phase,pending=pending,eligible=eligible)

def pool(rules,spec,templates,chosen,point,limit,recorder,required,ds,marks):
    filled,ports,_=A.state(rules,spec,chosen)
    available={j:a for j,a in ports.items() if j<0 or j in filled}
    slots=sorted(p[0]//2 for p in ds if p[0]//2<spec['bound']);found={};scanned=0
    for template in sorted(templates.values(),key=lambda t:(-len(t['pattern']),t['name'])):
        for embedding in itertools.combinations(slots,len(template['pattern'])):
            if point[0]//2 not in embedding:continue
            states=[((),{},{})]
            for i,node in enumerate(F(template['pattern'])):
                following=[];j=embedding[i]
                for members,env,outside in states:
                    matches=recorder.query(node,env);scanned+=len(matches)
                    for rid,local in matches:
                        binding={**env,**local};row=rules[rid];choices=[]
                        for (kind,index),a in zip(node['refs'],row['inputs']):
                            if kind=='inside':N(index<i,'acyclic cluster');choices.append((embedding[index],))
                            elif str(index) in outside:
                                ref=outside[str(index)];choices.append((ref,) if available.get(ref)==a and ref<j else ())
                            else:choices.append(tuple(ref for ref,b in sorted(available.items()) if b==a and ref<j))
                        for refs in itertools.product(*choices):
                            key=(j,rid,refs)
                            if key not in ds[A.cell(j)]:continue
                            ext=dict(outside);okay=True
                            for (kind,index),ref in zip(node['refs'],refs):
                                if kind=='outside':
                                    if str(index) in ext and ext[str(index)]!=ref:okay=False;break
                                    ext[str(index)]=ref
                            if okay:following.append((members+(key,),binding,ext))
                states=following
                if not states:break
            for members,env,outside in states:
                if members in found:recorder.counts['duplicate_expansions']+=1;continue
                recorder.aggregate(members)
                try:union=aggregate(rules,spec,members,required)
                except ValueError:continue
                if any(p in marks and marks[p]!=v for p,v in union['marks']):continue
                found[members]=dict(template=template['name'],members=members,bindings=env,outside=outside,level=template['level'],**union)
    for item in found.values():recorder.ordered(item)
    ordered=sorted(found.values(),key=lambda t:(-int(rules[t['members'][-1][1]]['output']==F(spec['target'])),-len(t['members']),max(k[0] for k in t['members'])-min(k[0] for k in t['members']),t['members'],t['template']))
    grouped=collections.defaultdict(list)
    for item in ordered:grouped[len(item['members'])].append(item)
    balanced=[]
    for index in range(max(map(len,grouped.values()),default=0)):
        for size in sorted(grouped,reverse=True):
            if index<len(grouped[size]):balanced.append(grouped[size][index])
    return balanced[:limit],dict(compatible=len(ordered),scanned=scanned,truncated=max(0,len(ordered)-limit))

def policy(event,items,rules,spec,chosen,point,levels,r,rng):
    N(F(event['chosen'])==chosen and F(event['point'])==point and F(event['items'])==F(items),'exact policy context and entire pool')
    vectors=[vector(None,rules,spec,chosen,levels,r['feature_mode'])]+[vector(item,rules,spec,chosen,levels,r['feature_mode']) for item in items]
    N(len(vectors)==len(event['features']),'whole feature matrix')
    for a,b in zip(vectors,event['features']):Q.V.close(a,b)
    scores=[sum(w*x for w,x in zip(r['weights'],v)) for v in vectors]
    maximum=max(scores);masses=[math.exp(s-maximum) for s in scores];prob=[m/sum(masses) for m in masses]
    Q.V.close(scores,event['scores']);Q.V.close(prob,event['probabilities'])
    selected=max(range(len(scores)),key=lambda i:(scores[i],-i))
    if r['stochastic']:
        draw=rng.random();N(draw==event['draw'],'seeded fresh sample');selected=len(scores)-1;acc=0.
        for i,v in enumerate(prob):
            acc+=v
            if draw<acc:selected=i;break
    else:N(event['draw'] is None,'frozen deterministic choice')
    N(selected==event['selected'],'actual selected family or defer')
    gradient=[vectors[selected][j]-sum(p*v[j] for p,v in zip(prob,vectors)) for j in range(12)]
    Q.V.close(gradient,event['gradient'])
    return None if selected==0 else items[selected-1]

def result(rules,spec,templates,r,required):
    rules,spec=F(rules),F(spec);counts=collections.Counter();recorder=Replay(rules,templates)
    levels=Old.distances(rules,spec['target']);rng=random.Random(r['seed']);ei=hi=0;leaf=finished=None
    if r['mode']=='policy':
        support=r['attention_support'];features=FEATURES if r['feature_mode']=='justified' else Old.FEATURES
        N(F(support['distances'])==F(sorted(levels.items())) and tuple(support['features'])==features,'complete cold support and declared feature meaning')
    else:N(r['attention_support'] is None,'no policy support in marked base')
    N(F(r['root_marks'])==F(sorted(D.initial(spec,required).items())),'every actual fixed root marking')
    def visit(node,chosen,active=None,completed=()):
        nonlocal ei,hi,leaf,finished
        ds=D.domains(rules,spec,chosen,required);kind,point,keys=A.decide(ds);_,marks=D.state(rules,spec,chosen,required)
        counts['nodes']+=1;counts['peak_candidates']=max(counts['peak_candidates'],sum(map(len,ds.values())))
        N((node['kind'],F(node['point']))==(kind,point),'global marked dead/forced/generation scheduler')
        N(F(node['census'])==tuple((p,len(v),0) for p,v in sorted(ds.items())),'entire complete incidence census')
        if node.get('cutoff')=='entry_wall':N(not node['children'],'no children after entry cutoff');return None
        N(node['hint_in']==(active['id'] if active else None),'exact branch-local inherited hint')
        prior=active;active,review=reviewed(active,chosen,kind,point,keys,ds,marks)
        N(F(node['review'])==F(review),'every hint expiry, suspension, resumption and completion')
        if prior:
            counts['hint_reviews']+=1;counts['hint_'+review['phase']]+=1
            if review['phase']=='completed':
                record=r['hints'][prior['id']];completed+=(dict(id=prior['id'],start=len(record['chosen']),end=len(chosen),item=prior['item']),)
        if kind=='dead':counts['dead']+=1;return False
        if kind=='empty':leaf=chosen;finished=completed;return True
        counts[kind]+=1
        joins=kind=='branch' and active is None and templates and r['mode']!='base'
        if joins:
            items,work=pool(rules,spec,templates,chosen,point,r['limits']['proposal_limit'],recorder,required,ds,marks)
            N(F(node['proposal_pool'])==F(items),'all declared proposal instances and exact point unions')
            for k,v in work.items():counts['proposal_'+k]+=v
            N(node['policy_event']==ei,'every sampled or frozen policy action in tree order')
            item=policy(r['policy_events'][ei],items,rules,spec,chosen,point,levels,r,rng);ei+=1
            N(('hint_start' in node)==(item is not None),'all and only admitted hints')
            if item is not None:
                N(node['hint_start']==hi and F(r['hints'][hi])==dict(id=hi,chosen=chosen,point=point,item=F(item)),'exact admitted original family expansion')
                active=dict(id=hi,item=F(item),waiting=False);hi+=1;counts['hint_started']+=1
                active,start=reviewed(active,chosen,kind,point,keys,ds,marks)
                N(active and start['eligible'] and F(node['start_review'])==F(start),'new hint reaches the chosen earliest point');review=start
        else:N('policy_event' not in node and 'hint_start' not in node,'no policy bypasses propagation')
        pending=review.get('pending',()) if active else ()
        base=sorted(keys,key=lambda k:(0 if k[1]==-2 else 1 if k[1]==-1 else 2,k[1],k[2]))
        preferred=sorted(k for k in pending if k in keys) if kind=='branch' else []
        expected=preferred+[k for k in base if k not in preferred];answer=False
        for i,child in enumerate(node['children']):
            N(answer is False and i<len(expected) and F(child['key'])==expected[i],'complete nonduplicated original fallback order')
            key=F(child['key']);role='member' if active and key in pending else 'unrelated' if active else 'base'
            N(child['role']==role,'actual member or unrelated constituent');counts['role_'+role]+=1;counts['attempts']+=1
            answer=visit(child['tree'],chosen+(key,),active,completed)
            if answer is False:counts['backtracks']+=1
        if node.get('cutoff')=='before_placement':N(answer is False and len(node['children'])<len(expected),'unknown retains a pending original alternative');return None
        N(answer is not False or len(node['children'])==len(expected),'all original alternatives before exhaustion')
        return answer
    outcome=visit(r['search_tree'],())
    N(r['status']==('finite_exact_proof_region' if outcome else 'unknown_search_budget' if outcome is None else 'exhausted_finite_region'),'tri-state result')
    N(ei==len(r['policy_events']) and hi==len(r['hints']),'all actual actions and admitted families audited')
    N(all(r['metrics'].get(k,0)==v for k,v in counts.items()),'all deterministic work counters')
    N(all(g==1 for g in r['tile_generations']),'one beyond root generation')
    if outcome:
        N(leaf==F(r['placements']) and F(r['solution_hints'])==F(finished),'exact successful leaf and every completed family')
        N(F(r['tiles'])==tuple(D.tile(rules,spec,k,required) for k in leaf),'all actual decorated tile values')
        stripped=[dict(t,marks=[(p,v) for p,v in t['marks'] if p[0]!=-3000]) for t in r['tiles']]
        A.certificate(rules,spec,r,stripped);D.state(rules,spec,leaf,required)
    index=F(r['index'])
    if index is not None:
        N(index['nodes']==recorder.nodes and index['queries']==F(recorder.queries),'every complete typed syntax index and query')
        N(all(index['metrics'].get(k,0)==v for k,v in recorder.counts.items()),'all index and cache work')
        catalog=dict(rules=rules,formulas=spec['_formulas'],variables=spec['variables'],terms=spec['terms'],rounds=spec['rounds'],generalization_rounds=spec['generalization_rounds'])
        context=dict(catalog=catalog,target=spec['target'],bound=spec['bound'],hypotheses=spec['hypotheses'],initial=sorted(D.initial(spec,required).items()),transformations='identity',capacity=12)
        N(index['context']==hashlib.sha256(D.packed(context)).hexdigest(),'complete decorated immutable root context')
        ordered=sorted(templates.values(),key=lambda t:(-len(t['pattern']),t['name']))
        N(index['library_pin']==Q.V.digest([(t['name'],t['pattern'],t['level']) for t in ordered]),'immutable mined inventory')
        N(0<=index['build_seconds']<=r['seconds'],'cold index charged')
    else:N(not recorder.queries,'no unrecorded matching index')
    return dict(status='passed',outcome=outcome,index_queries=len(recorder.queries),**counts)

update=Old.update
