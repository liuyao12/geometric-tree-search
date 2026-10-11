"""Independent semantic interfaces, complete point graphs, policy and native I/O.

Imports no new semantic producer, compiler, miner, join, policy or search.
Literal native derivations remain the certificate authority. Propositional
logical replay is an additional cross-check, not a search callback.
"""
import ast,collections,copy,gzip,hashlib,itertools,json,math,random,subprocess,time
from pathlib import Path
from audit_tree_kernel import need,packed
from audit_certificate_boundary import grammar,initial_for,artifact,sha,pin
from audit_native_receptor_points import initial,legal,state_pin,point_tree as donor_tree,rebuild as primitive_rebuild
from audit_native_inventory_policy import cluster
from audit_proof_boundary import code_bytes,input_bytes,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from audit_semantic_proofs import whole_replay
from audit_logical_wang_clusters import checked_chain
from micro_cert import run,write_cuts

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-semantic-inventory-audit-001')
FEATURES=['lemma','base_growth','new_fact','justified_inputs','target_output','mark_extension','shape_density','completed_rows','semantic_level','defer']
FIXED=[.7,.3,1.,.8,.2,-.1,.2,.2,.4,0.]

def same(a,b):return packed(a)==packed(b)
def close(a,b):return len(a)==len(b) and all(abs(x-y)<=1e-12 for x,y in zip(a,b))
def load(n):return json.loads(gzip.decompress((DOCS/n).read_bytes()))

def audit_dependencies():
    found={};pending=[Path(__file__).stem]
    while pending:
        name=pending.pop();path=HERE/(name+'.py')
        if name in found or not path.exists():continue
        found[name]=sha(path);tree=ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):pending.extend(n.name.split('.')[0] for n in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
    return {name+'.py':digest for name,digest in sorted(found.items())}

def abstract(request,definitions,provenance):
    local=[];inputs=[];ground={d['name']:d for d in definitions};dependencies=set()
    for row in request['proof']:
        c=copy.deepcopy(row)
        if c['rule']=='axiom':
            formula=request['theory']['axioms'][c['name']]
            need(formula==c['formula'],'donor hypothesis identity')
            if formula not in inputs:inputs.append(formula)
            c=dict(rule='assumption',formula=formula,index=inputs.index(formula))
        elif c['rule']=='block':
            definition=ground[c.pop('name')];dependencies.add(definition['family'])
            c['call']=dict(family=definition['family'],arguments=definition['arguments'])
        local.append(c)
    atoms=[]
    def visit(v):
        if isinstance(v,list):
            if len(v)==3 and v[0]=='pred' and not v[2]:
                if v[1] not in atoms:atoms.append(v[1])
                return ['meta',atoms.index(v[1])]
            return [visit(x) for x in v]
        if isinstance(v,dict):return {k:visit(x) for k,x in v.items()}
        return v
    template=visit(dict(premises=inputs,conclusion=request['target'],proof=local))
    return dict(id=pin(dict(parameters=len(atoms),template=template)),parameters=len(atoms),
                template=template,dependencies=sorted(dependencies),provenance=provenance,donor_atoms=atoms)

def substitution(value,args):
    if isinstance(value,list):
        if len(value)==2 and value[0]=='meta':
            need(type(value[1]) is int and 0<=value[1]<len(args),'formula parameter')
            return copy.deepcopy(args[value[1]])
        return [substitution(x,args) for x in value]
    if isinstance(value,dict):return {k:substitution(x,args) for k,x in value.items()}
    return value

def match(pattern,value,binding):
    if isinstance(pattern,list) and len(pattern)==2 and pattern[0]=='meta':
        index=pattern[1]
        if index in binding:return binding if binding[index]==value else None
        return {**binding,index:value}
    if isinstance(pattern,list):
        if not isinstance(value,list) or len(pattern)!=len(value):return None
        for a,b in zip(pattern,value):
            binding=match(a,b,binding)
            if binding is None:return None
        return binding
    return binding if pattern==value else None

def ground_inventory(library,basis):
    families={f['id']:f for f in library};definitions={};order=[];active=set();interfaces=[]
    def instantiate(fid,args):
        name='lemma'+pin(dict(family=fid,arguments=args))
        if name in definitions:
            need(definitions[name]['family']==fid and definitions[name]['arguments']==args,'identifier collision')
            return name
        need(name not in active and fid in families,'acyclic known family')
        active.add(name);family=families[fid];need(len(args)==family['parameters'],'parameter arity')
        ground=substitution(family['template'],args);commands=[];level=1
        for row in ground['proof']:
            c=copy.deepcopy(row)
            if c['rule']=='block':
                call=c.pop('call');dep=instantiate(call['family'],call['arguments'])
                c['name']=dep;level=max(level,definitions[dep]['level']+1)
            commands.append(c)
        native=dict(name=name,premises=ground['premises'],conclusion=ground['conclusion'],proof=commands)
        definitions[name]=dict(name=name,family=fid,arguments=args,level=level,definition=native)
        order.append(name);active.remove(name);return name
    for family in library:
        bindings=[{}]
        for pattern in family['template']['premises']+[family['template']['conclusion']]:
            candidates={}
            for binding in bindings:
                for value in basis:
                    found=match(pattern,value,binding)
                    if found is not None:candidates[packed(sorted(found.items()))]=found
            bindings=list(candidates.values())
        arguments={}
        for binding in bindings:
            missing=[i for i in range(family['parameters']) if i not in binding]
            for values in itertools.product(basis,repeat=len(missing)):
                complete={**binding,**dict(zip(missing,values))}
                args=[complete[i] for i in range(family['parameters'])]
                arguments[packed(args)]=args
        for key in sorted(arguments):interfaces.append(instantiate(family['id'],arguments[key]))
    return dict(definitions=[definitions[n] for n in order],
                interfaces=list(dict.fromkeys(interfaces)),native_blocks=[definitions[n]['definition'] for n in order])

def closure(inventory,proof):
    definitions={d['name']:d['definition'] for d in inventory['definitions']};wanted=set();pending=[c['name'] for c in proof if c['rule']=='block']
    while pending:
        name=pending.pop()
        if name in wanted:continue
        need(name in definitions,'actual call is registered');wanted.add(name)
        pending.extend(c['name'] for c in definitions[name]['proof'] if c['rule']=='block')
    result=[copy.deepcopy(d) for d in inventory['native_blocks'] if d['name'] in wanted];earlier=set()
    for d in result:
        need(all(c['name'] in earlier for c in d['proof'] if c['rule']=='block'),'dependency precedes its call')
        earlier.add(d['name'])
    need(earlier==wanted,'exact call dependency closure');return result

def encode(j,channel,value):return [((4*j+int(channel=='command'),100+i),v) for i,v in enumerate([*packed(value),256])]

def rebuild(spec,compiled,registry):
    basis,variables,ordinary=grammar(spec)
    need((basis,variables)==(compiled['basis'],compiled['variables']),'complete syntax basis')
    definitions={d['name']:d for d in registry['definitions']}
    interfaces=[definitions[n] for n in registry['interfaces']]
    arity=max([len(d['definition']['premises']) for d in interfaces]+[0])
    modes={d['name']:i+1 for i,d in enumerate(interfaces)}
    placements=[];conflicts=[];domains=[];tauts={packed(f) for f in compiled['tautologies']}
    def add(key,entries,command,requirements,kind,**extra):
        marks={}
        for point,value in entries:
            if point in marks and marks[point]!=value:
                conflicts.append(dict(key=key,reason='internally unequal markings'));return
            marks[point]=value
        placements.append(dict(key=key,occupancy=[((4*key[0],key[1]),12)],marks=sorted(marks.items()),
                               slot=key[0],kind=kind,command=command,requirements=requirements,**extra))
    for j,rows in enumerate(ordinary):
        formulas=[spec['target']] if j+1==spec['length'] else basis
        rows=rows+[dict(rule='block',formula=f,name=d['name']) for f in formulas for d in interfaces]
        rows.sort(key=lambda c:(c['rule'],packed(c['formula']),packed(c)));domains.append(rows)
        for k,c in enumerate(rows):
            f=c['formula'];rule=c['rule'];mode=modes[c['name']] if rule=='block' else 0
            entries=encode(j,'command',c)+encode(j,'formula',f)+[((4*j+2,90),mode)]
            add((j,0,k,0),entries,c,[],'command')
            if rule=='mp':
                for v,imp in enumerate(basis):
                    if imp[0]=='imp' and imp[2]==f:
                        requirements=[(c['antecedent'],imp[1]),(c['implication'],imp)]
                        add((j,1,k,v),entries+[e for i,a in requirements for e in encode(i,'formula',a)],c,requirements,'guard')
            else:
                valid=False;requirements=[]
                if rule=='axiom':valid=spec['theory']['axioms'][c['name']]==f
                elif rule=='refl':valid=f[0]=='eq' and f[1]==f[2]
                elif rule=='tautology':valid=packed(f) in tauts
                elif rule=='generalize':
                    valid=f[0]=='all' and f[1]==c['variable']
                    if valid:requirements=[(c['source'],f[2])]
                elif rule=='block':valid=definitions[c['name']]['definition']['conclusion']==f
                if valid:add((j,1,k,0),entries+[e for i,a in requirements for e in encode(i,'formula',a)],c,requirements,'guard')
        for r in range(arity):
            add((j,2+r,0,0),[((4*j+2,90),0),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=0,source=None)
            for definition in interfaces:
                mode=modes[definition['name']];premises=definition['definition']['premises']
                if r>=len(premises):
                    add((j,2+r,mode,0),[((4*j+2,90),mode),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=mode,source=None)
                else:
                    for source in range(j):
                        add((j,2+r,mode,source+1),[((4*j+2,90),mode),((4*j+2,100+r),source)]+encode(source,'formula',premises[r]),
                            None,[(source,premises[r])],'lemma_input',input=r,mode=mode,source=source)
    return dict(domains=domains,command_counts=list(map(len,domains)),arity=arity,mode_ids=modes,
                placements=sorted(placements,key=lambda p:p['key']),conflicts=conflicts,
                roots=[(4*j,r) for j in range(spec['length']) for r in range(2+arity)])

def verify_model(raw,rebuilt):
    for k in ('domains','command_counts','arity','mode_ids','placements','conflicts','roots'):
        need(same(raw[k],rebuilt[k]),'independently rebuilt complete factored inventory '+k)

def advance(c,state):
    out={k:(v.copy() if isinstance(v,(dict,list,set)) else v) for k,v in state.items()}
    generation=1+min(state['generations'][tuple(p)] for p,v in c['occupancy'])
    for p,v in c['occupancy']:
        p=tuple(p);out['totals'][p]=out['totals'].get(p,0)+v
        out['generations'][p]=min(out['generations'][p],generation)
    for p,v in c['marks']:out['marks'][tuple(p)]=v
    out['selected'].add(tuple(c['key']));out['order'].append(tuple(c['key']))
    out['tile_generations'].append(generation);return out

def decode(model,state):
    lookup={tuple(c['key']):c for c in model['placements']};by_point={(4*k[0],k[1]):lookup[k] for k in state['selected']};result=[]
    need(set(by_point)==set(map(tuple,model['roots'])),'entire C/G/input rectangle')
    for j in range(len(model['domains'])):
        command=copy.deepcopy(by_point[4*j,0]['command'])
        need(command==by_point[4*j,1]['command'],'matching command and rule')
        if command['rule']=='block':
            command['inputs']=[by_point[4*j,r]['source'] for r in range(2,2+model['arity']) if by_point[4*j,r]['kind']=='lemma_input']
        result.append(command)
    return result

def logical_row(inventory,keys,slot,arity):
    roles={k[1]:inventory[tuple(k)] for k in keys if k[0]==slot}
    if not all(r in roles for r in range(2+arity)):return None
    c=roles[0];g=roles[1]
    if c['command']!=g['command']:return None
    if g['command']['rule']!='block':return g['requirements']
    mode=dict((tuple(p),v) for p,v in g['marks'])[4*slot+2,90]
    if any(roles[r]['mode']!=mode for r in range(2,2+arity)):return None
    return [pair for r in range(2,2+arity) for pair in roles[r]['requirements']]

def features(item,inventory,spec,state):
    if item is None:return [0.]*9+[1.]
    arity=max(p[1] for p in state['roots'])-1;known=set();facts=set()
    for j in range(spec['length']):
        requirements=logical_row(inventory,state['selected'],j,arity)
        if requirements is not None and all(i in known for i,a in requirements):
            known.add(j);guard=next(inventory[k] for k in state['selected'] if k[0]==j and k[1]==1)
            facts.add(packed(guard['command']['formula']))
    slots={k[0] for k in item['members']};guards=[inventory[tuple(k)] for k in item['members'] if k[1]==1]
    requirements=[pair for j in slots for pair in (logical_row(inventory,list(state['selected'])+item['members'],j,arity) or [])]
    if not requirements:requirements=[pair for k in item['members'] for pair in inventory[tuple(k)]['requirements']]
    refs=[i for i,a in requirements];full=sum(logical_row(inventory,item['members'],j,arity) is not None for j in slots)
    return [float(item['kind']=='lemma'),item['new_occupancy']/(12*(2+arity)),
        float(any(packed(g['command']['formula']) not in facts for g in guards)),
        sum(i in known for i in refs)/max(1,len(refs)),
        float(any(g['command']['formula']==spec['target'] for g in guards)),item['new_marks']/1000,
        len(slots)/(max(slots)-min(slots)+1),full/max(1,len(slots)),item['level']/2,0.]

def proposals(inventory,library,state,domains,point,limit,check_limit):
    arity=max(p[1] for p in state['roots'])-1
    definitions={d['name']:d for d in library['definitions']} if library else {}
    anchors=domains[point];pool=[];seen=set();work=collections.Counter()
    selected={(4*k[0],k[1]):k for k in state['selected']}
    by_point=collections.defaultdict(list);guards=collections.defaultdict(list)
    for key,c in sorted(inventory.items()):
        by_point[tuple(c['occupancy'][0][0])].append(key)
        if key[1]==1:guards[key[0]].append(key)
    def save(kind,members,level):
        if kind=='sampled':work['sample_validation_checks']+=1
        else:
            if work['validation_checks']>=check_limit:return
            work['validation_checks']+=1
        item=cluster(inventory,members,state)
        if item is None:return
        key=tuple(item['members'])
        if key in seen or not any(k in domains[point] for k in item['pending']):return
        seen.add(key);item.update(kind=kind,level=level);pool.append(item)
    for anchor in anchors[:limit]:
        end=min(limit,len(pool)+max(1,limit//max(1,min(limit,len(anchors)))))
        check_end=min(check_limit,work['validation_checks']+max(1,check_limit//max(1,min(limit,len(anchors)))))
        slot=anchor[0]
        for guard in guards[slot]:
            if len(pool)>=end or work['validation_checks']>=check_end:break
            c=inventory[guard]['command'];block=c['rule']=='block'
            if block and not library:continue
            mode=dict((tuple(p),v) for p,v in inventory[guard]['marks'])[4*slot+2,90]
            pair=[(slot,0,guard[2],0),guard]
            if anchor[1]<2 and anchor not in pair:continue
            if any(k not in state['selected'] and not legal(inventory[k],state) for k in pair):continue
            level=definitions[c['name']]['level'] if block else 0;choices=[]
            for role in range(2,2+arity):
                p=(4*slot,role);rows=[selected[p]] if p in selected else by_point[p]
                rows=[k for k in rows if inventory[k]['mode']==mode and (k in state['selected'] or legal(inventory[k],state))]
                if anchor[1]==role:rows=[k for k in rows if k==anchor]
                choices.append(rows)
            def join(index,members):
                if len(pool)>=end or work['validation_checks']>=check_end:return
                if index==len(choices):
                    save('lemma' if block else 'primitive',members,level);return
                for key in choices[index]:
                    if len(pool)>=end or work['validation_checks']>=check_end:return
                    work['validation_checks']+=1
                    if cluster(inventory,members+[key],state,False):join(index+1,members+[key])
            join(0,pair)
        if len(pool)>=end:work['row_quota_stops']+=1
        if work['validation_checks']>=check_end:work['row_check_stops']+=1
    work['row_pool']=len(pool);work['anchors_omitted']=max(0,len(anchors)-limit)
    keys=sorted({k for rows in domains.values() for k in rows})
    for anchor in anchors[:4]:
        ordering=sorted(keys,key=lambda k:(hashlib.sha256(packed([anchor,k])).digest(),k))
        save('sampled',[anchor],0);members=[anchor]
        for key in ordering:
            if key in members:continue
            if work['sample_pair_tests']>=64:break
            work['sample_pair_tests']+=1
            if cluster(inventory,members+[key],state,False):members.append(key)
            if len(members)==3:break
        if len(members)>1:save('sampled',members,0)
    work['items']=len(pool);return [None]+pool,dict(work)

class LiteralDomains:
    """Full literal marking comparisons, represented by independent bit sets.

    Every original candidate and assigned value is indexed. The union of all
    mismatching-value masks gives exactly the illegal candidates at each state.
    This uses no producer incidence, dependency or domain cache.
    """
    def __init__(self,inventory):
        self.keys=sorted(inventory);self.at=collections.defaultdict(int)
        self.assigned=collections.defaultdict(int);self.equal=collections.defaultdict(int)
        for i,key in enumerate(self.keys):
            c=inventory[key];need(len(c['occupancy'])==1 and c['occupancy'][0][1]==12,'declared unit-capacity inventory')
            bit=1<<i;self.at[tuple(c['occupancy'][0][0])]|=bit
            for point,value in c['marks']:
                point=tuple(point);self.assigned[point]|=bit;self.equal[point,value]|=bit
    def __call__(self,state):
        invalid=0
        for point,value in state['marks'].items():
            invalid|=self.assigned.get(point,0)&~self.equal.get((point,value),0)
        domains={}
        for point in state['roots']:
            if state['totals'].get(point,0)>=12:continue
            remaining=self.at.get(point,0)&~invalid;keys=[]
            while remaining:
                bit=remaining&-remaining;keys.append(self.keys[bit.bit_length()-1]);remaining-=bit
            domains[point]=keys
        return domains

def guided_tree(spec,model,result,library,weights):
    inventory={tuple(c['key']):c for c in model['placements']};root=initial(spec,model);metrics=collections.Counter();events=result['events'];hints=result['hints'];ei=hi=0;found=None;rng=random.Random(result['seed'])
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

def catalog(spec,compiled,records,requests):
    basis,variables,_=grammar(spec)
    need(compiled['status']=='complete' and (compiled['basis'],compiled['variables'])==(basis,variables)
         and len(compiled['queries'])==len(basis),'complete native tautology catalog')
    accepted=[]
    for j,q in enumerate(compiled['queries']):
        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],
                     proof=[dict(rule='tautology',formula=basis[j])],target=basis[j])
        rec=records[q]
        need(rec['purpose']=='tautology_instance' and rec['basis_index']==j
             and same(rec['request'],request) and rec['result']['status'] in ('accepted','rejected'),'each compiled guard')
        if q in requests:need(same(requests[q],request),'reused training catalog identity')
        requests[q]=request
        if rec['result']['status']=='accepted':accepted.append(basis[j])
    need(accepted==compiled['tautologies'],'only native accepted tautologies')

def registration(spec,raw,library,basis,records,requests):
    inventory=ground_inventory(library,basis)
    for k in ('definitions','interfaces','native_blocks'):need(same(raw[k],inventory[k]),'complete grounded dependency inventory '+k)
    taut=['imp',['bot'],['bot']]
    request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=inventory['native_blocks'],
                 proof=[dict(rule='tautology',formula=taut)],target=taut)
    q=raw['query'];rec=records[q]
    need(q not in requests and same(rec['request'],request)
         and rec['purpose']=='check_generated_lemma_definitions','whole native registry admission')
    requests[q]=request
    expected='native_accepted' if rec['result']['status']=='accepted' else 'native_rejected' if rec['result']['status']=='rejected' else 'unknown_native_inventory'
    need(raw['status']==expected,'unfinished registry has no authority')
    return inventory

def proof_query(spec,proof,inventory,records,q,requests,purpose):
    request=dict(protocol='gcts-fol-1',theory=spec['theory'],
                 blocks=closure(inventory,proof) if inventory else [],proof=proof,target=spec['target'])
    rec=records[q]
    need(q not in requests and same(rec['request'],request) and rec['purpose']==purpose,'exact searched proof and dependency closure')
    requests[q]=request
    return request,rec['result']['status']=='accepted'

def training_replay(training):
    need(training['features']==FEATURES and training['rate']==.4 and len(training['episodes'])==24,'fresh learning protocol')
    records=training['records'];requests={};library=[];cache={};nodes=events=hints=0
    for donor in training['donors']:
        spec=donor['case'];compiled=donor['compiled'];catalog(spec,compiled,records,requests)
        model=primitive_rebuild(spec,compiled)
        for k in ('domains','command_counts','complete_words','placements','conflicts','roots'):need(same(donor['model'][k],model[k]),'fresh primitive donor '+k)
        nodes+=donor_tree(dict(case=spec,search=donor['search'],proof=donor['search']['proof']),model)
        q=donor['verification_query'];request,accepted=proof_query(spec,donor['search']['proof'],None,records,q,requests,'fresh_semantic_donor')
        need(accepted,'only checked fresh donor proofs')
        family=abstract(records[q]['request'],[],dict(case=spec['id'],query=q,request_sha256=pin(request)))
        need(family['id']==donor['family'],'primitive mined family identity')
        library.append(family);cache[pin(request)]=q
    promotion=training['promotion'];spec=promotion['case'];compiled=promotion['compiled']
    catalog(spec,compiled,records,requests)
    inventory=registration(spec,promotion['inventory'],library,compiled['basis'],records,requests)
    need(promotion['inventory']['status']=='native_accepted','lower inventory checked before promotion')
    model=rebuild(spec,compiled,inventory);verify_model(promotion['model'],model)
    work=guided_tree(spec,model,promotion['search'],inventory,None)
    nodes+=work['nodes'];events+=work['events'];hints+=work['hints']
    q=promotion['verification_query'];request,accepted=proof_query(spec,promotion['search']['proof'],inventory,records,q,requests,'higher_semantic_family_donor')
    need(accepted,'searched dependent proof checked')
    family=abstract(records[q]['request'],inventory['definitions'],dict(case=spec['id'],query=q,request_sha256=pin(request)))
    need(family['dependencies'] and family['id']==promotion['family'],'actual higher family uses earlier lemmas')
    library.append(family);cache[pin(request)]=q
    need(len(training['library'])==len(library),'all mined families')
    for actual,expected in zip(training['library'],library):
        for k,v in expected.items():need(same(actual[k],v),'mined family, formula parameters and provenance '+k)
    models={};registries={}
    for case in training['cases']:
        compiled=training['catalog'][case['id']];catalog(case,compiled,records,requests)
        inventory=registration(case,training['registries'][case['id']],library,compiled['basis'],records,requests)
        need(training['registries'][case['id']]['status']=='native_accepted','checked training inventory')
        models[case['id']]=rebuild(case,compiled,inventory);registries[case['id']]=inventory
    weights=[0.]*10;baseline=0.
    for index,episode in enumerate(training['episodes']):
        spec=training['cases'][index%len(training['cases'])]
        need(episode['id']==index and episode['case']==spec['id'] and episode['weights_before']==weights,'zero start and declared fresh episode schedule')
        result=episode['search'];model=models[spec['id']];inventory=registries[spec['id']]
        need(result['mode']=='learned' and result['stochastic'] and result['seed']==63000+index
             and result['limits']==dict(attempts=3000,seconds=30,proposal_limit=24,proposal_checks=2048),'fresh exploration and budgets')
        work=guided_tree(spec,model,result,inventory,weights)
        nodes+=work['nodes'];events+=work['events'];hints+=work['hints'];accepted=False
        if result['proof']:
            request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=closure(inventory,result['proof']),proof=result['proof'],target=spec['target'])
            key=pin(request);q=episode['verification_query']
            need(episode['request_sha256']==key,'feedback certificate includes definitions and original target')
            if key in cache:
                need(episode['cached_native_acceptance'] and q==cache[key],'prior exact training-only acceptance')
                accepted=True
            else:
                need(not episode['cached_native_acceptance'],'no unknown or future acceptance reuse')
                _,accepted=proof_query(spec,result['proof'],inventory,records,q,requests,'training_semantic_feedback')
                if accepted:cache[key]=q
        else:
            need(episode['verification_query'] is None and episode['request_sha256'] is None
                 and not episode['cached_native_acceptance'],'no proof supplies no acceptance')
        need(episode['accepted']==accepted,'native training feedback')
        growth=(2+model['arity'])*len(result['proof']) if accepted else 0
        effort=result['metrics'].get('validation_checks',0)+result['metrics'].get('sample_pair_tests',0)
        value=growth/max(1,result['metrics'].get('attempts',0))-.25*min(1.,effort/100000)
        gradient=[0.]*10
        for event in result['events']:
            selected=event['features'][event['index']]
            for k in range(10):gradient[k]+=selected[k]-sum(p*v[k] for p,v in zip(event['probabilities'],event['features']))
        gradient=[x/max(1,len(result['events'])) for x in gradient]
        advantage=value-baseline;updated=[w+.4*advantage*g for w,g in zip(weights,gradient)]
        expected=dict(reward=value,baseline_before=baseline,advantage=advantage,gradient=gradient)
        need(close(episode['learning']['gradient'],gradient)
             and all(abs(episode['learning'][k]-expected[k])<=1e-12 for k in ('reward','baseline_before','advantage'))
             and close(episode['weights_after'],updated),'all actual REINFORCE updates')
        baseline=.9*baseline+.1*value;weights=updated
        need(abs(episode['baseline_after']-baseline)<=1e-12,'baseline update')
    need(close(training['weights'],weights) and abs(training['baseline']-baseline)<=1e-12,'frozen final weights')
    need(set(requests)==set(range(len(records))) and training['queries']==len(records),'all training query origins')
    return dict(library=library,weights=weights,requests=requests,nodes=nodes,events=events,hints=hints)

def smt_binding(model,result):
    inventory={tuple(c['key']):c for c in model['placements']}
    groups=collections.defaultdict(list)
    for k,c in sorted(inventory.items()):
        for p,v in c['marks']:groups[tuple(p),v].append(k)
    grouped=[dict(point=p,value=v,keys=ks) for (p,v),ks in sorted(groups.items())]
    if 'group_encoding_sha256' in result:
        need(result['group_encoding_sha256']==pin(grouped) and result['boolean_variables']==len(inventory)
             and result['value_groups']==len(groups) and result['mark_assignment_memberships']==sum(len(x['keys']) for x in grouped),'every original SMT marking assignment')
    if result['proof']:
        state=initial(dict(length=len(model['domains']),target=result['proof'][-1]['formula']),model)
        for key in result['placements']:
            key=tuple(key);need(key in inventory and legal(inventory[key],state),'SMT original point legality')
            state=advance(inventory[key],state)
        need(all(state['totals'].get(p,0)==12 for p in state['roots'])
             and decode(model,state)==result['proof'] and result['status']=='smt_exact_point_region','entire decoded SMT region')
    else:
        need(result['status'] in ('solver_unsat_finite_point_region','unknown_solver_budget','unknown_search_budget','unknown_encoding_budget')
             and not result['placements'],'SMT finite tri-state result')
    return dict(nodes=0,events=0,hints=0)

def evaluation_replay(raw,library,weights,policy_sha):
    spec=raw['case'];records=raw['records'];requests={};compiled=raw['compiled']
    need(raw['policy_sha256']==policy_sha,'one frozen policy')
    catalog(spec,compiled,records,requests)
    inventory=registration(spec,raw['inventory'],library,compiled['basis'],records,requests)
    if raw['inventory']['status']!='native_accepted':
        need(raw['model'] is None and raw['search'] is None and raw['proof'] is None
             and raw['status']==raw['inventory']['status'],'unfinished registry permits no point search')
        return dict(requests=requests,model=None,nodes=0,events=0,hints=0)
    model=rebuild(spec,compiled,inventory);verify_model(raw['model'],model)
    if raw['mode']=='z3':work=smt_binding(model,raw['search'])
    else:
        need(raw['search']['limits']==dict(attempts=spec.get('attempts',5000),seconds=30,proposal_limit=24,proposal_checks=2048)
             and not raw['search']['stochastic'],'matched point evaluation budget')
        work=guided_tree(spec,model,raw['search'],inventory,weights)
    need(raw['proof']==raw['search']['proof'],'decoded root statement')
    if raw['proof']:
        _,accepted=proof_query(spec,raw['proof'],inventory,records,raw['verification_query'],requests,'frozen_semantic_evaluation')
        need(raw['status']==('native_proof_discovered' if accepted else 'unknown_native_verification'),'whole native evaluation result')
    else:need(raw['status']==raw['search']['status'] and 'verification_query' not in raw,'no invented proof')
    need(set(requests)==set(range(len(records))) and raw['queries']==len(records),'all cold native queries')
    return dict(requests=requests,model=model,**work)

def replay_native(records,requests,micro,template,inventory_limit=5*10**9):
    steps=0;accepted={}
    for q,rec in enumerate(records):
        need(rec['id']==q and same(rec['request'],requests[q]) and rec['request_sha256']==pin(requests[q])
             and rec['query_target']=='fixed_assertion','semantically bound native request')
        # Reconstruct actual wire order independently, after semantic binding.
        request=rec['request'];boot=initial_for(micro,template,request)
        words=dict(fixed=boot['words'][micro['boundary']['problem']][:-1],free=boot['words'][micro['boundary']['certificate']][:-1])
        need(rec['boundary_words']==words,'independent tagged word encoder')
        (TMP/'input.bin').write_bytes(input_bytes(boot))
        need(sha(TMP/'input.bin')==rec['input_sha256'],'entire actual parser input')
        limit=10**9 if rec['purpose']=='tautology_instance' else inventory_limit if rec['purpose']=='check_generated_lemma_definitions' else 5*10**9
        response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',limit))
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(response[k])==str(rec['result'][k]),'independent whole native result '+k)
        need(rec['result']['start']==88986 and sha(TMP/'output.bin')==rec['output_sha256'],'actual start and all output bands')
        steps+=response['micro_steps']
        if response['status'] in ('accepted','rejected'):
            try:logical=whole_replay(request)['status']
            except ValueError:logical='rejected'
            need(logical==response['status'],'independent logical cross-check, audit only')
        if response['status']=='accepted':accepted[pin(request),rec['input_sha256']]=request
    return steps,accepted

def smt_encoding(model,result):
    """Reconstruct every assertion independently; never trust a saved SAT label."""
    if not result.get('complete_encoding'):return dict(status='not_submitted')
    import z3
    inventory={tuple(c['key']):c for c in model['placements']};keys=sorted(inventory)
    xs={k:z3.Bool('c_'+str(i)) for i,k in enumerate(keys)}
    state=initial(dict(length=len(model['domains']),target=model['domains'][-1][0]['formula']),model)
    points=sorted(set(state['marks'])|{tuple(p) for c in inventory.values() for p,v in c['marks']})
    values={p:z3.Int('m_'+str(i)) for i,p in enumerate(points)};solver=z3.Solver()
    for point in sorted(map(tuple,model['roots'])):
        rows=[xs[k] for k in keys if tuple(inventory[k]['occupancy'][0][0])==point]
        solver.add(z3.PbEq([(x,1) for x in rows],1))
    for p,v in sorted(state['marks'].items()):solver.add(values[p]==v)
    grouped=collections.defaultdict(list)
    for k in keys:
        for p,v in inventory[k]['marks']:grouped[tuple(p),v].append(xs[k])
    for (p,v),rows in sorted(grouped.items()):solver.add(z3.Implies(z3.Or(rows),values[p]==v))
    need(result['marking_integer_variables']==len(values) and result['constraints']==len(solver.assertions()),
         'independently reconstructed all SMT variable and assertion counts')
    submitted=z3.parse_smt2_string(result['smtlib'])
    expected=solver.assertions();need(len(submitted)==len(expected),'entire submitted SMT assertion count')
    for i,(a,b) in enumerate(zip(submitted,expected)):
        # SMT-LIB writes the signed numeral as (- 1). Its parser retains a
        # unary-minus node whereas IntVal(-1) is a signed numeral AST. Fold
        # this literal only; no logical assertion is dropped or weakened.
        normalized=a if z3.eq(a,b) else z3.substitute(a,(-z3.IntVal(1),z3.IntVal(-1)))
        need(z3.eq(normalized,b),'SMT assertion '+str(i)+' differs: submitted '+a.sexpr()[:160]+'; reconstructed '+b.sexpr()[:160])
    answer=dict(status='all_assertions_equal',assertions=len(solver.assertions()),version=z3.get_version_string())
    if result['status']=='solver_unsat_finite_point_region':
        solver.set(timeout=30000,random_seed=0);status=solver.check()
        need(status==z3.unsat,'independent finite UNSAT control rerun');answer['rechecked']='unsat'
    return answer

def finite_equivalence(training,library):
    """Exhaust the tiny three-line two-premise envelope, including block inputs.

    This is a differential finite check, not a universal compiler theorem.
    The direct reference grammar enumerates strict-prior tuples. The factored
    representation separately selects C, G and B tiles for the same commands.
    """
    donor=next(d for d in training['donors'] if d['case']['length']==3)
    spec=donor['case'];compiled=donor['compiled'];registry=ground_inventory(library,compiled['basis'])
    model=rebuild(spec,compiled,registry);definitions={d['name']:d for d in registry['native_blocks']}
    choices=[]
    for j,commands in enumerate(model['domains']):
        rows=[]
        for c in commands:
            if c['rule']=='block':
                arity=len(definitions[c['name']]['premises'])
                rows.extend(dict(**c,inputs=list(refs)) for refs in itertools.product(range(j),repeat=arity))
            else:rows.append(c)
        choices.append(rows)
    by_key={tuple(p['key']):p for p in model['placements']};guards=collections.defaultdict(list)
    for key,c in by_key.items():
        if key[1]==1:guards[key[0],key[2]].append(c)
    total=accepted=exact=0;accepted_words=[]
    for word in itertools.product(*choices):
        total+=1;state=initial(spec,model);okay=True
        for j,command in enumerate(word):
            skeleton={k:v for k,v in command.items() if k!='inputs'};k=model['domains'][j].index(skeleton)
            candidates=[by_key[j,0,k,0]];compatible=None
            for guard in guards[j,k]:
                if legal(guard,state):compatible=guard;break
            if compatible is None:okay=False;break
            candidates.append(compatible)
            for role in range(model['arity']):
                mode=model['mode_ids'][command['name']] if command['rule']=='block' else 0
                if command['rule']=='block' and role<len(command['inputs']):key=(j,2+role,mode,command['inputs'][role]+1)
                else:key=(j,2+role,mode,0)
                need(key in by_key,'complete strict-prior direct tuple has every factor');candidates.append(by_key[key])
            for c in candidates:
                if not legal(c,state):okay=False;break
                state=advance(c,state)
            if not okay:break
        if okay:
            need(decode(model,state)==list(word),'exact factor decoding');exact+=1
        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=registry['native_blocks'],proof=list(word),target=spec['target'])
        try:valid=whole_replay(request)['status']=='accepted'
        except ValueError:valid=False
        need(okay==valid,'every complete direct command word agrees with exact marking tiling')
        if valid:accepted+=1;accepted_words.append(word)
    need(total>0 and accepted>0,'nonempty finite positive differential census')
    return dict(case=spec['id'],line_counts=list(map(len,choices)),words=total,
                accepted=accepted,exact_regions=exact,accepted_words_sha256=pin(accepted_words),
                scope='Complete three-line two-premise finite reference grammar including every strict-prior lemma tuple. Logical cross-check is audit-only. Not a universal soundness or completeness theorem.')

def mutations(training,raw,unknown,smt,library,weights,policy_sha):
    rejected=[]
    def changed(name,document,edit,check):
        b=copy.deepcopy(document);edit(b)
        try:check(b)
        except (ValueError,KeyError,IndexError,TypeError,StopIteration):rejected.append(name)
        else:raise ValueError('corruption admitted '+name)
    cold=lambda b:evaluation_replay(b,library,weights,policy_sha)
    changed('missing-original-command',raw,lambda b:b['model']['domains'][0].pop(),cold)
    changed('missing-input-factor',raw,lambda b:next(c for c in b['model']['placements'] if c['kind']=='lemma_input')['marks'].pop(),cold)
    changed('changed-inactive-zero-semantics',raw,lambda b:next(c for c in b['model']['placements'] if c['kind']=='unused_input')['marks'].__setitem__(1,[[2,100],0]),cold)
    changed('invented-source-factor',raw,lambda b:next(c for c in b['model']['placements'] if c['kind']=='lemma_input').update(source=99),cold)
    changed('changed-mode-mark',raw,lambda b:b['model']['mode_ids'].update(invented=99),cold)
    changed('false-census',raw,lambda b:b['search']['tree']['census'][0]['keys'].pop(),cold)
    changed('wrong-generation',raw,lambda b:b['search']['tree']['census'][0].update(generation=7),cold)
    changed('lost-full-fallback',raw,lambda b:b['search']['tree']['alternatives'].pop(),cold)
    changed('false-rollback',raw,lambda b:b['search'].update(root_restored=False),cold)
    changed('changed-probability',raw,lambda b:b['search']['events'][0]['probabilities'].__setitem__(0,.9),cold)
    changed('invented-source-justification',raw,lambda b:b['search']['events'][0]['features'][1].__setitem__(3,9.),cold)
    changed('changed-cluster-expansion',raw,lambda b:b['search']['events'][0]['items'][-1]['members'].pop(),cold)
    changed('lost-hint-receptor',raw,lambda b:b['search']['hints'][0]['item']['pending'].pop(),cold)
    changed('changed-final-target',raw,lambda b:b['records'][-1]['request'].update(target=['bot']),cold)
    changed('invented-family-body',training,lambda b:b['library'][0]['template']['proof'][0].update(rule='induction'),training_replay)
    changed('lost-local-hypothesis',training,lambda b:b['library'][0]['template']['premises'].pop(),training_replay)
    changed('seeded-policy-start',training,lambda b:b['episodes'][0]['weights_before'].__setitem__(0,1.),training_replay)
    changed('false-cached-feedback',training,lambda b:b['episodes'][0].update(verification_query=0),training_replay)
    changed('altered-training-gradient',training,lambda b:b['episodes'][0]['learning']['gradient'].__setitem__(0,9.),training_replay)
    changed('altered-native-reward',training,lambda b:b['episodes'][0]['learning'].update(reward=0.),training_replay)
    changed('invented-final-policy',training,lambda b:b['weights'].__setitem__(0,9.),training_replay)
    changed('unknown-inventory-authorized',unknown,lambda b:b['inventory'].update(status='native_accepted'),cold)
    changed('SMT-omitted-membership',smt,lambda b:b['search'].update(mark_assignment_memberships=0),cold)
    changed('SMT-invented-formula',smt,lambda b:b['search'].update(smtlib='(assert false)'),
            lambda b:smt_encoding(evaluation_replay(b,library,weights,policy_sha)['model'],b['search']))
    return rejected

def certificate_mutations(row,micro,events,root):
    rejected=[]
    for kind in ('checkpoint-register','checkpoint-heap','incoming-head','outgoing-state','fragment-node','fragment-cost','fixed-target','open-premise'):
        changed=copy.deepcopy(events);badrow=copy.deepcopy(row);badroot=copy.deepcopy(root)
        e=next(e for e in changed if e['kind']=='checkpoint');f=next(e for e in changed if e['kind']=='fragment')
        if kind=='checkpoint-register':e['register_words'][0]='0'
        elif kind=='checkpoint-heap':e['heap']=e['heap'][:-1]
        elif kind=='incoming-head':f['input_head']+=1
        elif kind=='outgoing-state':f['out']+=1
        elif kind=='fragment-node':f['node']=0xffffffff
        elif kind=='fragment-cost':
            response=next(o['response'] for o in badroot['observations'] if o['node']==f['node'])
            response['physical_constant']=str(int(response['physical_constant'])+1)
        elif kind=='fixed-target':badrow['request']['target']=['bot']
        elif kind=='open-premise':
            if not badrow['request']['blocks']:continue
            badrow['request']['blocks'][0]['premises']=[['bot']]
        try:
            if kind in ('fixed-target','open-premise'):
                need(same(initial_for(micro,row['initial'],badrow['request']),row['initial']),'complete input theorem binding')
            checked_chain(badrow,micro,changed,badroot)
        except (ValueError,KeyError,IndexError):rejected.append(dict(case=row['name'],kind=kind))
        else:raise ValueError('native certificate corruption admitted '+kind)
    return rejected

def main():
    began=time.perf_counter();TMP.mkdir(parents=True,exist_ok=True);data=load('semantic-inventory-001.json.gz')
    need((data['program_sha256'],data['micro_sha256'],data['literal_table_sha256'])==(PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE),'fixed universal native authority')
    for field,root in (('sources',HERE),('reused_sources',HERE),('reused_inputs',DOCS)):
        for n,p in data[field].items():need(sha(root/n)==p,'frozen runtime dependency '+n)
    closure_file=DOCS/'semantic-inventory-source-closure-001.json';source_closure=json.loads(closure_file.read_text())
    for r in source_closure['sources']:need(sha(HERE.parents[1]/r['path'])==r['sha256'],'complete frozen Python runtime '+r['path'])
    micro=load('proof-boundary-microcode-001.json.gz');template=json.loads((DOCS/'proof-boundary-001.json').read_text())['cases'][0]['initial']
    need(pin(micro)==PINNED_MICRO and hashlib.sha256(gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes())).hexdigest()==PINNED_TABLE,
         'independent actual fixed microcode and primitive table pins')
    (TMP/'code.bin').write_bytes(code_bytes(micro))
    for source,name in (('audit_tape_micro.cpp','native'),('micro_line_check.cpp','checker')):
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    training=json.loads(artifact(data['training']));t=training_replay(training)
    print('all fresh inventory, training graphs and gradients replayed',t['nodes'],t['events'],flush=True)
    steps,requests=replay_native(training['records'],t['requests'],micro,template)
    queries=training['queries'];nodes=t['nodes'];events=t['events'];hints=t['hints']
    print('all fresh native training queries rerun',queries,flush=True)
    policy_path=DOCS/data['policy']['name'];need(sha(policy_path)==data['policy']['sha256'],'frozen policy artifact')
    policy=json.loads(policy_path.read_text())
    need(policy['features']==FEATURES and policy['weights']==training['weights'] and same(policy['library'],training['library'])
         and policy['training']==data['training'],'policy has precisely this training provenance')
    methods=['base','zero','fixed','learned','no-family','z3']
    expected={(c['id'],m,r) for c in data['cases'] for m in methods for r in (1,2)}
    need(data['methods']==methods and data['repetitions']==2 and len(data['cases'])==8
         and len(data['observations'])==96 and {(o['case'],o['mode'],o['repetition']) for o in data['observations']}==expected,'all predeclared cold controls')
    summaries=[];first=unknown=smt=None
    for obs in data['observations']:
        raw=json.loads(artifact(obs['artifact']));spec=next(c for c in data['cases'] if c['id']==obs['case'])
        need(same(raw['case'],spec) and (raw['mode'],raw['repetition'])==(obs['mode'],obs['repetition']),'external assertion, region and lane')
        index=data['cases'].index(spec);rotated=methods[index%6:]+methods[:index%6]
        order=rotated if obs['repetition']==1 else list(reversed(rotated))
        need(raw['method_order']==order,'balanced frozen method order')
        if raw['search'] and raw['mode']!='z3':
            need(raw['search']['mode']==raw['mode'] and raw['search']['seed']==64000+100*index+obs['repetition']-1,'cold lane and fresh seed')
        work=evaluation_replay(raw,t['library'],t['weights'],data['policy']['sha256'])
        smt_work=smt_encoding(work['model'],raw['search']) if raw['mode']=='z3' and raw['search'] else None
        n,accepted=replay_native(raw['records'],work['requests'],micro,template,spec.get('inventory_steps',5*10**9))
        steps+=n;requests.update(accepted);queries+=raw['queries'];nodes+=work['nodes'];events+=work['events'];hints+=work['hints']
        for k in ('status','queries','cold_seconds','verification_query'):need(raw.get(k)==obs.get(k),'cold summary '+k)
        need((raw['search'] or {}).get('metrics')==obs['metrics'],'all cold counters')
        summaries.append(dict(case=obs['case'],mode=obs['mode'],repetition=obs['repetition'],status=raw['status'],
                              queries=raw['queries'],nodes=work['nodes'],events=work['events'],hints=work['hints'],smt=smt_work))
        if first is None and raw['mode']=='learned' and raw['status']=='native_proof_discovered' and raw['search']['events'] and raw['search']['hints']:first=raw
        if unknown is None and raw['status']=='unknown_native_inventory':unknown=raw
        if smt is None and raw['mode']=='z3' and raw['search'] and raw['search'].get('complete_encoding'):smt=raw
        print(obs['case'],obs['mode'],obs['repetition'],'all graph/guidance/native queries checked',flush=True)
    for repetition in (1,2):
        short=[o for o in summaries if o['case']=='short-semantic' and o['repetition']==repetition]
        need(len(short)==6 and all(o['status']==('solver_unsat_finite_point_region' if o['mode']=='z3' else 'exhausted_finite_marked_region') for o in short),'SMT finite UNSAT agrees with all complete GCTS exhaustions')
    certificates=[];corruptions=[]
    for row in data['certificates']:
        request=requests[row['request_sha256'],row['input_sha256']];need(same(row['request'],request),'displayed certificate was discovered and checked')
        boot=initial_for(micro,template,request);need(same(boot,row['initial']),'complete actual accepting input')
        (TMP/'input.bin').write_bytes(input_bytes(boot));need(sha(TMP/'input.bin')==row['input_sha256'],'wire input certificate SHA')
        (TMP/'grammar.bin').write_bytes(artifact(row['grammar']));log=[json.loads(v) for v in artifact(row['events']).splitlines()]
        write_cuts([e['node'] for e in log if e['kind']=='fragment'],TMP/'observed.bin')
        checked=run(TMP/'checker',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'output.bin',5*10**9,1500000000,TMP/'root.json',TMP/'observed.bin'))
        need(checked['status']=='checked_response' and checked['result']=='accepted' and sha(TMP/'output.bin')==row['output_sha256'],'full native response DAG derived again')
        root=json.loads((TMP/'root.json').read_text());need(same(root,json.loads(artifact(row['responses']))),'all observed native interfaces')
        chain=checked_chain(row,micro,log,root);need(chain['final']==row['output'],'all bands and native line contexts')
        certificates.append(dict(name=row['name'],case_id=row['case_id'],role=row['role'],request_sha256=row['request_sha256'],
                                 lines=chain['lines'],contexts=chain['contexts'],fragments=chain['fragments'],checked=checked))
        corruptions.extend(certificate_mutations(row,micro,log,root))
        print(row['name'],'native root/lemma contexts derived',len(chain['lines']),flush=True)
    differential=finite_equivalence(training,t['library'])
    corruptions.extend(mutations(training,first,unknown,smt,t['library'],t['weights'],data['policy']['sha256']))
    result=dict(version='semantic-inventory-audit-001',status='passed',producer_sha256=sha(DOCS/'semantic-inventory-001.json.gz'),
        source_sha256=sha(HERE/'audit_semantic_inventory.py'),dependency_sha256=audit_dependencies(),runtime_closure_sha256=sha(closure_file),queries=queries,micro_steps=steps,
        point_nodes=nodes,policy_events=events,hints=hints,training=dict(episodes=24,families=len(t['library']),nodes=t['nodes'],
        events=t['events'],hints=t['hints'],weights=t['weights']),observations=summaries,certificates=certificates,
        finite_equivalence=differential,mutations_rejected=corruptions,seconds=time.perf_counter()-began,
        scope='Independent literal marking domains at every visited node, complete original fallback, each bounded pool/hint/choice and all fresh policy updates; every recorded native query rerun from the true parser start; all full accepting DAGs and local/root contexts derived again. All submitted SMT assertions reconstructed, selected regions verified, tiny UNSAT rerun and checked against GCTS exhaustion. Finite differential evidence, not a universal compiler theorem, full first-order completeness or primitive-square GCTS search.')
    (DOCS/'semantic-inventory-audit-001.json.gz').write_bytes(gzip.compress(packed(result),mtime=0))
    print('audit passed',queries,nodes,events,'seconds',round(result['seconds'],3),flush=True)

if __name__=='__main__':main()
