"""Independent checks of prefix teachers and their bounded causal restriction.

Imports none of the new learner or overlay. Reuses the independently authored
Notebook 63 literal-domain and complete-tree checker, not its producer engine.
"""
import collections,itertools,json,math,random
from audit_semantic_inventory import (rebuild,guided_tree,need,same,pin,packed,encode,
    LiteralDomains,initial,state_pin,legal,advance,decode,proposals,features,close,FIXED)

def decorations(c):return json.dumps(dict(occupancy=c['occupancy'],marks=c['marks']),sort_keys=True,separators=(',',':'))

def semantic(model):
    return {k:v for k,v in model.items() if k not in ('compile_seconds','encoding','scope','initial_marks','failure_overlay')}

def fixed_vocabulary_prefix(spec,compiled,registry):
    # The parent vocabulary stays fixed even if the new prefix target has
    # fewer subformulas. Recomputing it from that target would unsoundly omit
    # original prefix candidates, particularly in quantified examples.
    basis=compiled['basis'];variables=compiled['variables']
    definitions={d['name']:d for d in registry['definitions']}
    interfaces=[definitions[n] for n in registry['interfaces']]
    arity=max([len(d['definition']['premises']) for d in interfaces]+[0])
    modes={d['name']:i+1 for i,d in enumerate(interfaces)}
    placements=[];conflicts=[];domains=[];tauts={packed(f) for f in compiled['tautologies']}
    def add(key,entries,command,requirements,kind,**extra):
        marks={}
        for p,v in entries:
            if p in marks and marks[p]!=v:
                conflicts.append(dict(key=key,reason='internally unequal markings'));return
            marks[p]=v
        placements.append(dict(key=key,occupancy=[((4*key[0],key[1]),12)],marks=sorted(marks.items()),
            slot=key[0],kind=kind,command=command,requirements=requirements,**extra))
    for j in range(spec['length']):
        formulas=[spec['target']] if j+1==spec['length'] else basis;rows=[]
        for f in formulas:
            rows.extend(dict(rule='axiom',formula=f,name=name) for name in sorted(spec['theory']['axioms']))
            rows.extend(dict(rule='generalize',formula=f,variable=v,source=s) for v in variables for s in range(j))
            rows.extend(dict(rule='mp',formula=f,antecedent=a,implication=b) for a,b in itertools.product(range(j),repeat=2))
            rows.extend(dict(rule=r,formula=f) for r in ('refl','tautology'))
            rows.extend(dict(rule='block',formula=f,name=d['name']) for d in interfaces)
        rows.sort(key=lambda c:(c['rule'],packed(c['formula']),packed(c)));domains.append(rows)
        for k,c in enumerate(rows):
            f=c['formula'];r=c['rule'];mode=modes[c['name']] if r=='block' else 0
            entries=encode(j,'command',c)+encode(j,'formula',f)+[((4*j+2,90),mode)]
            add((j,0,k,0),entries,c,[],'command')
            if r=='mp':
                for v,imp in enumerate(basis):
                    if imp[0]=='imp' and imp[2]==f:
                        required=[(c['antecedent'],imp[1]),(c['implication'],imp)]
                        add((j,1,k,v),entries+[e for i,a in required for e in encode(i,'formula',a)],c,required,'guard')
            else:
                valid=False;required=[]
                if r=='axiom':valid=spec['theory']['axioms'][c['name']]==f
                elif r=='refl':valid=f[0]=='eq' and f[1]==f[2]
                elif r=='tautology':valid=packed(f) in tauts
                elif r=='generalize':
                    valid=f[0]=='all' and f[1]==c['variable']
                    if valid:required=[(c['source'],f[2])]
                elif r=='block':valid=definitions[c['name']]['definition']['conclusion']==f
                if valid:add((j,1,k,0),entries+[e for i,a in required for e in encode(i,'formula',a)],c,required,'guard')
        for r in range(arity):
            add((j,2+r,0,0),[((4*j+2,90),0),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=0,source=None)
            for d in interfaces:
                mode=modes[d['name']];premises=d['definition']['premises']
                if r>=len(premises):
                    add((j,2+r,mode,0),[((4*j+2,90),mode),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=mode,source=None)
                else:
                    for source in range(j):
                        required=[(source,premises[r])]
                        add((j,2+r,mode,source+1),[((4*j+2,90),mode),((4*j+2,100+r),source)]+encode(source,'formula',premises[r]),
                            None,required,'lemma_input',input=r,mode=mode,source=source)
    return dict(domains=domains,command_counts=list(map(len,domains)),arity=arity,mode_ids=modes,
        placements=sorted(placements,key=lambda c:c['key']),conflicts=conflicts,
        roots=[(4*j,r) for j in range(spec['length']) for r in range(2+arity)])

def bound_context(parent):
    return dict(theory=parent.spec['theory'],basis=parent.compiled['basis'],variables=parent.compiled['variables'],
        tautologies=parent.compiled['tautologies'],definitions=parent.inventory['definitions'],
        interfaces=parent.inventory['interfaces'],native_blocks=parent.inventory['native_blocks'],
        arity=parent.arity,mode_ids=parent.mode,
        encoding='Exact canonical command/formula words and strict earlier source ports; semantic-receptor model 001')

def teacher(parent,probe):
    spec=probe['spec'];original=parent.spec
    need(spec['theory']==original['theory'] and spec['length']==probe['slot']+1
         and spec['target']==probe['formula'],'declared prefix statement and theory')
    record=fixed_vocabulary_prefix(spec,parent.compiled,parent.inventory)
    need(same(semantic(record),semantic(probe['model'])),'independently rebuilt complete prefix inventory')
    full=rebuild(original,parent.compiled,parent.inventory)
    required={decorations(c):tuple(c['key']) for c in full['placements']
        if c['key'][0]<spec['length'] and not (c['key'][0]==probe['slot'] and c['key'][1]<2
                                               and c['command']['formula']!=probe['formula'])}
    pairs=[]
    for c in record['placements']:
        word=decorations(c);need(word in required,'necessary-prefix decorated placement')
        pairs.append((tuple(c['key']),required.pop(word)))
        need(all(p[0]<=4*c['key'][0]+2 for p,v in c['marks']),'all requirements stay at this row or earlier')
    need(not required and same(pairs,probe['lift']['pairs']) and pin(pairs)==probe['lift']['sha256'],
         'all original prefix placements and exact identity lift')
    need(record['roots']==[p for p in full['roots'] if p[0]<4*spec['length']],
         'complete prefix root restriction')
    checked=guided_tree(spec,record,probe['search'],parent.inventory,None)
    labels={'finite_marked_proof_region':'positive','exhausted_finite_marked_region':'negative',
            'unknown_search_budget':'unknown'}
    need(probe['label']==labels[probe['search']['status']],'unknown is never an exclusion')
    return dict(status='passed',label=probe['label'],lift_sha256=pin(pairs),**checked)

def check_learning(parent,learning):
    # Reconstruct the complete per-row formula catalog from initial native
    # target agreement. Do not trust a sampled teacher list or learner labels.
    full=rebuild(parent.spec,parent.compiled,parent.inventory);target=parent.spec['target']
    need(same(semantic(full),semantic(parent.record())),'actual parent inventory independently reconstructed')
    need(same(bound_context(parent),learning['context']) and pin(bound_context(parent))==learning['context_sha256'],
         'complete grammar context of every transferred prefix certificate')
    groups=collections.defaultdict(list);formulas={json.dumps(f,sort_keys=True,separators=(',',':'),ensure_ascii=False):f for f in parent.compiled['basis']}
    for c in full['placements']:
        if c['key'][1]!=0:continue
        if c['key'][0]+1==parent.spec['length'] and c['command']['formula']!=target:continue
        word=json.dumps(c['command']['formula'],sort_keys=True,separators=(',',':'),ensure_ascii=False)
        groups[c['key'][0],word].append(c['key'])
    catalog=[dict(id=i,slot=j,length=j+1,formula=formulas[word],command_keys=keys)
             for i,((j,word),keys) in enumerate(sorted(groups.items()))]
    need(same(catalog,learning['catalog']) and len(learning['probes'])==len(catalog),'complete prefix query catalog')
    counts=collections.Counter();nodes=0
    for expected,probe in zip(catalog,learning['probes']):
        for k,v in expected.items():need(same(probe[k],v),'unsampled prefix '+k)
        need(all(probe['search']['limits'][k]==v for k,v in learning['limits'].items()),'predeclared teacher budgets')
        checked=teacher(parent,probe);counts[checked['label']]+=1;nodes+=checked['nodes']
        if 'independent_check' in probe:need(probe['independent_check']==checked,'actual pre-activation check')
    need(dict(counts)==learning['counts'],'all resolved and unresolved prefix results')
    return dict(version='prefix-failure-certificate-001',status='passed',learning_sha256=pin(learning),
        context_sha256=learning['context_sha256'],prefixes=len(catalog),counts=dict(counts),nodes=nodes,
        scope='Independent reconstruction of every candidate and every visited domain, exact prefix restriction, complete fallback and rollback. Negatives authorize only grammar-scoped redundant marking values; unknowns authorize none.')

def check_overlay(parent,learning,certificate,record):
    need(certificate['status']=='passed' and certificate['learning_sha256']==pin(learning)
         and certificate['context_sha256']==pin(bound_context(parent)),'pre-activation certificate context')
    full=rebuild(parent.spec,parent.compiled,parent.inventory)
    values={tuple(c['key']):dict((tuple(p),v) for p,v in c['marks']) for c in full['placements']}
    expected_marks={k:dict(v) for k,v in values.items()};exterior={};failures=[]
    for probe in learning['probes']:
        if probe['label']!='negative':continue
        need(probe['search']['status']=='exhausted_finite_marked_region','no unknown negative')
        p=(4*probe['slot']+3,100000+parent.compiled['basis'].index(probe['formula']))
        word=encode(probe['slot'],'formula',probe['formula']);exterior[p]=0;affected=[];kinds=collections.Counter()
        for c in full['placements']:
            k=tuple(c['key'])
            if all(values[k].get(tuple(q))==v for q,v in word):
                need(p not in values[k] and all(tuple(q)!=p for q,v in c['occupancy']),'additional marking-only point')
                expected_marks[k][p]=1;affected.append(k);kinds[c['kind']]+=1
        failures.append(dict(probe=probe['id'],slot=probe['slot'],formula=probe['formula'],point=p,
            exterior_value=0,tile_value=1,affected_keys=sorted(affected),by_kind=dict(kinds)))
    original={tuple(c['key']):c for c in full['placements']}
    expected=dict(full,placements=[dict(c,marks=sorted(expected_marks[tuple(c['key'])].items())) for c in full['placements']])
    need(same(semantic(expected),semantic(record)),'all original t-data, roots and identities; exact extra marking values')
    overlay=record['failure_overlay']
    need(overlay['certificate']==certificate and overlay['learning_sha256']==pin(learning)
         and overlay['context_sha256']==pin(bound_context(parent)) and same(overlay['exterior'],sorted(exterior.items()))
         and same(overlay['failures'],failures),'complete source/guard/consumer failure support')
    state=initial(parent.spec,full);state['marks'].update(exterior)
    need(same(record['initial_marks'],sorted(state['marks'].items())),'exact fixed boundary plus every redundant zero')
    lookup={tuple(c['key']):c for c in record['placements']};checked=0
    for probe in learning['probes']:
        if probe['label']!='positive':continue
        lift={tuple(a):tuple(b) for a,b in probe['lift']['pairs']}
        s=initial(probe['spec'],probe['model']);s['marks'].update(exterior)
        for key in probe['search']['placements']:
            c=lookup[lift[tuple(key)]];need(legal(c,s),'each witnessed positive prefix survives all learned markings')
            s=advance(c,s)
        need(set(s['totals'])==set(s['roots']) and all(v==12 for v in s['totals'].values()),'entire witnessed positive prefix')
        checked+=1
    return dict(status='passed',negative_ports=len(exterior),positive_prefixes_rechecked=checked,
        affected_candidates=len({k for f in failures for k in f['affected_keys']}),
        placements=len(full['placements']),scope='Every extra assigned value reconstructed. All positive teacher regions retain exact marking agreement; unknowns supply no support. This supplements the exhaustive negative-prefix and causal-restriction certificates.')


# Reused independent Notebook 63 tree auditor, extended only with the
# independently reconstructed marking-only boundary. Its literal-domain
# enumeration, scheduler, policy, complete fallback and rollback checks remain.
def extended_tree(spec,model,result,library,weights,initial_marks):
    inventory={tuple(c['key']):c for c in model['placements']};root=initial(spec,model)
    supplied={tuple(p):v for p,v in initial_marks}
    need(all(supplied.get(p)==v for p,v in root['marks'].items()),'original fixed assertion retained')
    root['marks'].update(supplied);metrics=collections.Counter();events=result['events'];hints=result['hints'];ei=hi=0;found=None;rng=random.Random(result['seed'])
    scoring=[0.]*10 if result['mode']=='zero' else FIXED if result['mode']=='fixed' else weights
    need(result['weights']==scoring and result['mode'] in ('base','zero','fixed','learned','no-family'),'frozen ordering lane');used_library=[] if result['mode']=='no-family' else library;enumerate_domains=LiteralDomains(inventory)
    def review(s,domains,hint,point):
        if hint is None:return None,dict(phase='absent',pending=[],eligible=[])
        pending=[tuple(k) for k in hint['item']['members'] if tuple(k) not in s['selected']]
        if not pending:return None,dict(phase='completed',pending=[],eligible=[])
        bad=[k for k in pending if not legal(inventory[k],s)]
        if bad:return None,dict(phase='invalid',pending=pending,illegal=bad,eligible=[])
        allowed=[k for k in pending if k in domains.get(point,[])];return hint,dict(phase='eligible' if allowed else 'waiting',pending=pending,eligible=allowed)
    def walk(s,t,hint):
        nonlocal ei,hi,found
        metrics['nodes']+=1;domains=enumerate_domains(s);census=[dict(point=p,generation=s['generations'][p],keys=d) for p,d in sorted(domains.items())]
        need(same(t['census'],census) and t['state_sha256']==state_pin(s),'every complete point graph and full state')
        dead=sorted(p for p,d in domains.items() if not d);forced=sorted(p for p,d in domains.items() if len(d)==1)
        if dead:kind,p='dead',dead[0]
        elif forced:kind,p='forced',forced[0]
        elif not domains:kind,p='empty',None
        else:kind,p='branch',min(domains,key=lambda p:(s['generations'][p],len(domains[p]),p))
        need(t['kind']==kind and same(t['point'],p),'global reference scheduler');need(t['hint_in']==(hint['id'] if hint else None),'branch-local hint inheritance');active,trace=review(s,domains,hint,p);need(same(t['review'],trace),'exact hint completion, waiting and retirement')
        if hint:metrics['hint_'+trace['phase']]+=1
        if kind=='dead':metrics['dead']+=1;need(not t['children'] and 'policy_event' not in t,'dead precedes policy');return False
        if kind=='empty':found=s;need(not t['children'] and 'policy_event' not in t,'whole target before success');return True
        metrics[kind]+=1;keys=domains[p]
        if kind=='branch' and active is None and result['mode']!='base':
            need(t['policy_event']==ei and ei<len(events),'every guidance event');event=events[ei];items,work=proposals(inventory,used_library,s,domains,p,result['limits']['proposal_limit'],result['limits']['proposal_checks'])
            for k,v in work.items():metrics[k]+=v
            vectors=[features(item,inventory,spec,s) for item in items];need(same(event['items'],items) and all(close(a,b) for a,b in zip(event['features'],vectors)) and len(event['features'])==len(vectors),'entire bounded proposal pool and exact state features');need(event['id']==ei and same(event['chosen'],s['order']) and same(event['point'],p) and event['weights']==scoring,'state-bound policy event')
            scores=[sum(w*x for w,x in zip(scoring,v)) for v in vectors];top=max(scores);raw=[math.exp(x-top) for x in scores];prob=[x/sum(raw) for x in raw];need(close(scores,event['scores']) and close(prob,event['probabilities']),'actual softmax distribution')
            if result['stochastic']:
                u=rng.random();need(event['uniform']==u,'fresh seeded stochastic draw');cumulative=0.;selected=len(prob)-1
                for j,x in enumerate(prob):
                    cumulative+=x
                    if u<cumulative:selected=j;break
            else:selected=max(range(len(scores)),key=lambda j:(scores[j],-j));need(event['uniform'] is None,'greedy held-out policy')
            need(event['index']==selected,'actual chosen cluster/defer');ei+=1;item=items[selected]
            if item is not None:
                need(t['hint_start']==hi and hi<len(hints),'new hint identity');expected=dict(id=hi,chosen=s['order'],point=p,item=item);need(same(hints[hi],expected),'validated original expansion and current interface');active=dict(id=hi,item=item);hi+=1;metrics['hints_started']+=1;active,start=review(s,domains,active,p);need(active is not None and start['eligible'] and same(t['start_review'],start),'new cluster reaches selected point');trace=start
            else:need('hint_start' not in t,'defer leaves all candidates available')
        else:need('policy_event' not in t and 'hint_start' not in t,'forced/waiting precedes new proposals')
        preferred=set(trace['eligible']) if active else set();order=keys if kind=='forced' else [k for k in keys if k in preferred]+[k for k in keys if k not in preferred];need(same(t['alternatives'],order),'complete original fallback, reordered only')
        for index,child in enumerate(t['children']):
            need(index<len(order) and same(child['key'],order[index]) and child['role']==('member' if order[index] in preferred else 'base'),'exact scheduled constituent and fallback role');metrics['attempts']+=1;okay=walk(advance(inventory[order[index]],s),child['tree'],active)
            if okay is not False:need(index+1==len(t['children']),'no siblings after accept/unknown');return okay
            metrics['backtracks']+=1
        if len(t['children'])<len(order):
            need(t.get('cutoff')=='before_placement' and (metrics['attempts']>=result['limits']['attempts'] or result['seconds']>=result['limits']['seconds']),'unfinished remains unknown');return None
        need('cutoff' not in t,'fully exhausted branch');return False
    okay=walk(root,result['tree'],None);status='finite_marked_proof_region' if okay else 'unknown_search_budget' if okay is None else 'exhausted_finite_marked_region';need(result['status']==status and result['root_restored'] and result['root_state_sha256']==state_pin(root),'exact terminal result and rollback');expected_metrics={k:v for k,v in result['metrics'].items() if k!='proposal_seconds'};need(expected_metrics==dict(metrics) and ei==len(events) and hi==len(hints),'all placements, proposals, branches and hints');need(result['metrics'].get('proposal_seconds',0)>=0,'reported proposal clock')
    proof=decode(model,found) if found else None;need(result['proof']==proof and same(result['placements'],found['order'] if found else []) and result['tile_generations']==(found['tile_generations'] if found else []),'actual decoded proof and generations');return dict(nodes=metrics['nodes'],events=ei,hints=hi)

