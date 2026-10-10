"""Searched arithmetic proof clusters over the unchanged complete base graph.

Finite contextual equational grammar, identity point transforms. Parametric
proof fragments are learned only from fresh GCTS solutions. Instantiation and
context embedding compile proposals into existing base placements; proposals
never change graph degrees or prune base choices. Every constituent observes
the reference scheduler. This is a specialized arithmetic cluster proposer,
not a fair general FOL grammar or new learned failure marking.
"""
import collections,copy,hashlib,itertools,time
import logic as L
import semantic_proof_tiles as S
from turtle import Graph
from proof_block_search import Proof,equation,locations,bind,replace_variables,proof_for_path,fresh
from serialized_kernel import canonical,check,problem_hash,PROTOCOL

def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def axioms(c):return {n:equation(n,a,'axiom') for n,a in c['theory']['axioms'].items()}
def action(c,rule):
    recipe=c['rules'][rule]['recipe'];move=recipe['move']
    return dict(move,rule=axioms(c)[recipe['axiom']])
def chain(c,keys,length):
    by_slot={k[0]:k for k in keys};out=[];i=length-1;seen=set()
    while True:
        if i in seen:raise ValueError('cyclic logical dependency')
        seen.add(i);k=by_slot[i];out.append(k);rule=c['rules'][k[1]]
        if not k[2]:break
        if len(k[2])!=1:raise ValueError('one-premise equational fragment required')
        i=k[2][0]
    return out[::-1]
def definitions(library):
    return [t['definition'] for t in library]
def closure(blocks,lines):
    by_name={b['name']:b for b in blocks};used=set();active=set();out=[]
    def visit(n):
        if n in used:return
        if n in active or n not in by_name:raise ValueError('missing/cyclic proof block')
        active.add(n);b=by_name[n]
        for l in b['proof']:
            if l['rule']=='block':visit(l['name'])
        active.remove(n);used.add(n);out.append(b)
    for l in lines:
        if l['rule']=='block':visit(l['name'])
    return out
def request(theory,target,proof,blocks):return dict(protocol=PROTOCOL,theory=theory,target=target,proof=proof,blocks=closure(blocks,proof))
def validate_library(theory,library):
    target=L.Imp(('bot',),('bot',));probe=dict(protocol=PROTOCOL,theory=theory,target=target,proof=[dict(rule='tautology',formula=target)],blocks=definitions(library))
    r=check(canonical(probe),expected_problem_sha256=problem_hash(probe),max_work=None,max_bytes=100000000)
    if r['status']!='accepted':raise ValueError(('proof library rejected',r))
    return r
def summary_action(template,instance):
    r=equation(template['name'],template['definition']['conclusion'],'block')
    return dict(before=instance['before'],after=instance['after'],rule=r,bindings=instance['bindings'],path=tuple(instance['context']),direction=instance['direction'])
def closed_formula(a,variables):
    for x in reversed(variables):a=L.All(x,a)
    return a
def promote(c,result,length,library,source_id,min_moves=2,max_moves=4):
    """Mine every eligible window in the checked final dependency chain.

    Donor targets and the window bounds are authored; the interfaces and move
    sequences come from the found proof. Child calls come from actual accepted
    solution transactions, not a postulated hierarchy or supplied witness.
    """
    before=time.perf_counter();decoded=result.get('decoded')
    if decoded is None:return dict(status='no_promotion_unknown_search',templates=[],seconds=time.perf_counter()-before)
    payload=decoded['request'];verified=check(canonical(payload),expected_problem_sha256=problem_hash(payload),max_work=None)
    if verified['status']!='accepted':raise ValueError('source proof must check before mining')
    path=chain(c,result['placements'],length);moves=[];move_keys=[]
    for k in path:
        kind=c['rules'][k[1]]['recipe']['kind']
        if kind=='primitive':continue
        if kind=='copy':continue
        moves.append(action(c,k[1]));move_keys.append(k)
    old={t['name']:t for t in library};transactions=result.get('solution_transactions',[]);new=[];known={digest([t['before'],t['after'],t['actions']]) for t in library}
    for start in range(len(moves)):
        for size in range(min_moves,min(max_moves,len(moves)-start)+1):
            window=moves[start:start+size];keys=move_keys[start:start+size];a,b=window[0]['before'],window[-1]['after']
            if any(x['after']!=y['before'] for x,y in zip(window,window[1:])):raise ValueError('noncontiguous mined equality path')
            pure=[dict(m,rule=m['rule']['name']) for m in window];identity=digest([a,b,pure])
            if identity in known:continue
            variables=sorted(set().union(*(L.term_free(m['before'])|L.term_free(m['after'])|set().union(*(L.term_free(t) for t in m['bindings'].values())) for m in window)))
            steps=[];children=[];i=0
            while i<size:
                choices=[tr for tr in transactions if tr['template'] in old and tuple(tr['members'])==tuple(keys[i:i+len(tr['members'])]) and i+len(tr['members'])<=size]
                if choices:
                    tr=max(choices,key=lambda t:len(t['members']));steps.append(summary_action(old[tr['template']],tr['instance']));children.append(tr['template']);i+=len(tr['members'])
                else:steps.append(window[i]);i+=1
            proof=proof_for_path(a,steps);builder=Proof();builder.append(proof)
            for x in reversed(variables):builder.emit('generalize',L.All(x,builder.lines[-1]['formula']),variable=x,source=len(builder.lines)-1)
            conclusion=closed_formula(L.Eq(a,b),variables);name='proof-cluster-'+digest([conclusion,pure,children])[:20]
            definition=dict(name=name,premises=[],conclusion=conclusion,proof=builder.lines);level=1+max((old[n]['level'] for n in children),default=0)
            probe=request(c['theory'],conclusion,builder.lines,definitions(library));checked=check(canonical(probe),expected_problem_sha256=problem_hash(probe),max_work=None)
            if checked['status']!='accepted':raise ValueError(('mined proof cluster rejected',checked))
            template=dict(name=name,level=level,before=a,after=b,variables=variables,actions=pure,definition=definition,children=children,source=dict(problem=source_id,certificate_sha256=digest(payload),window=[start,start+size],members=keys),check=checked)
            new.append(template);known.add(identity)
    return dict(status='checked_fragments_promoted',templates=new,source_check=verified,seconds=time.perf_counter()-before)

class Index:
    """Bounded proposal inventory only; never a base candidate domain."""
    def __init__(self,c,length,library,max_instances=50000):
        began=time.perf_counter();self.instances=[];self.by_point=collections.defaultdict(list);self.library={t['name']:t for t in library};self.complete=True
        if not library:self.seconds=time.perf_counter()-began;return
        terms=[a[2] for a in c['formulas']];term_set=set(terms);lookup={}
        def identity(move,name):return digest([move['before'],move['after'],name,move['bindings'],move['path'],move['direction']])
        for i,r in enumerate(c['rules']):
            if r['recipe']['kind']=='block':lookup[identity(r['recipe']['move'],r['recipe']['axiom'])]=i
        for template in library:
            count=len(template['actions'])
            for before in terms:
                for context,sub in locations(before):
                    for direction in (1,-1):
                        lhs=template['before'] if direction==1 else template['after'];bindings={}
                        if not bind(lhs,sub,set(template['variables']),bindings):continue
                        missing=[v for v in template['variables'] if v not in bindings]
                        for extra in itertools.product(terms,repeat=len(missing)):
                            env=dict(bindings,**dict(zip(missing,extra)));steps=template['actions'] if direction==1 else list(reversed(template['actions']));compiled=[];current=before
                            for a in steps:
                                old=a['before'] if direction==1 else a['after'];new=a['after'] if direction==1 else a['before'];next_term=L.replace_at(current,context,replace_variables(new,env))
                                # The learned fragment's recorded internal action
                                # is embedded at the same outer context.
                                move=dict(before=current,after=next_term,bindings={k:replace_variables(v,env) for k,v in a['bindings'].items()},path=tuple(context)+tuple(a['path']),direction=a['direction']*direction)
                                if next_term not in term_set or L.replace_at(current,context,replace_variables(old,env))!=current:compiled=[];break
                                rid=lookup.get(identity(move,a['rule']))
                                if rid is None:compiled=[];break
                                compiled.append(rid);current=next_term
                            if len(compiled)!=count:continue
                            for start in range(1,length-count+1):
                                for ref in range(start):
                                    members=tuple((start+i,rid,(ref if i==0 else start+i-1,)) for i,rid in enumerate(compiled))
                                    item=dict(template=template['name'],members=members,instance=dict(before=before,after=current,bindings=env,context=context,direction=direction),level=template['level'])
                                    if len(self.instances)>=max_instances:self.complete=False;self.seconds=time.perf_counter()-began;return
                                    self.instances.append(item)
                                    for key in members:self.by_point[S.cell(key[0])].append(item)
        self.seconds=time.perf_counter()-began
    def offered(self,model,state,graph,point,limit=8):
        result=[]
        for item in self.by_point.get(point,()):
            if any(k not in model.cache or not state.legal(model.placement(k)) for k in item['members']):continue
            # Individual legality is not enough: the aggregate marks must agree.
            marks=dict(state.marks);valid=True
            for k in item['members']:
                for p,v in model.placement(k).marks:
                    if p in marks and marks[p]!=v:valid=False;break
                    marks[p]=v
                if not valid:break
            if valid:result.append(item)
        # A declared proposal prior; complete singleton incidence stays intact.
        result.sort(key=lambda item:(-int(any(k[0]==model.length-1 for k in item['members'])),-len(item['members']),-item['level'],digest(item)))
        return result[:limit],len(result)

class Budget(Exception):pass
def execute(model,state,graph,item,tick=None):
    if len(set(item['members']))!=len(item['members']):return dict(status='rejected_duplicate_constituent',steps=[]),None,None
    child=state.copy();cg=graph.copy();pending=set(item['members']);steps=[]
    while pending:
        kind,p,keys=cg.decision(child)
        if kind=='dead':return dict(status='rejected_dead',steps=steps),None,None
        if kind=='empty':return dict(status='rejected_incomplete_cluster',steps=steps),None,None
        if kind=='forced':key=keys[0];role='member' if key in pending else 'global_forced'
        else:
            choices=sorted(pending.intersection(keys))
            if not choices:return dict(status='rejected_scheduler',steps=steps),None,None
            key=choices[0];role='member'
        if tick:
            try:tick()
            except Budget:return dict(status='unknown_transaction_budget',steps=steps),None,None
        changed=child.place(model.placement(key));cg.update(model,child,changed);pending.discard(key);steps.append(dict(kind=kind,point=p,key=key,role=role))
    if cg.decision(child)[0]=='dead':return dict(status='rejected_dead',steps=steps),None,None
    return dict(status='accepted_cluster',steps=steps),child,cg

def search(c,length,library=(),seconds=5,attempt_limit=50000,proposal_limit=8,index_limit=50000,diagnostics=12,mode='clusters'):
    if mode not in ('clusters','rank'):raise ValueError('declared proposal mode required')
    began=time.perf_counter();library=copy.deepcopy(library);library_sha=digest(library);model=S.Model(c,length);build_seconds=time.perf_counter()-began;state=model.initial();graph=Graph(model,state);graph_seconds=time.perf_counter()-began-build_seconds
    index=Index(c,length,library,index_limit);stats=collections.Counter();samples=[];transaction_samples=[];found=None;found_transactions=[];best=state.copy();peak_nodes=len(graph.edges);peak_incidences=sum(map(len,graph.domains.values()))
    def tick():
        if stats['base_attempts']>=attempt_limit or time.perf_counter()-began>seconds:raise Budget()
        stats['base_attempts']+=1
    def visit(s,g,transactions):
        nonlocal found,best,found_transactions,peak_nodes,peak_incidences
        stats['nodes']+=1
        if time.perf_counter()-began>seconds:raise Budget()
        kind,p,keys=g.decision(s);peak_nodes=max(peak_nodes,len(g.edges));peak_incidences=max(peak_incidences,sum(map(len,g.domains.values())))
        if len(samples)<diagnostics:samples.append(dict(order=list(s.order),kind=kind,point=p,degrees={str(q):len(v) for q,v in g.domains.items()}))
        if kind=='dead':return False,dict(kind=kind,point=p)
        if len(s.order)>len(best.order):best=s.copy()
        if kind=='empty':found=s;found_transactions=transactions;return True,dict(kind=kind)
        tree=dict(kind=kind,point=p,proposals=[],children=[]);stats['forced' if kind=='forced' else 'branches']+=1
        if kind=='branch' and library:
            t=time.perf_counter();offered,count=index.offered(model,s,g,p,proposal_limit);stats['proposal_enumeration_seconds']+=time.perf_counter()-t;stats['compatible_proposals']+=count
            if mode=='rank':
                priority=[]
                for item in offered:
                    for key in item['members']:
                        if key in keys and key not in priority:priority.append(key)
                keys=priority+[key for key in keys if key not in priority];tree['ranking_items']=offered;stats['ranked_frontiers']+=1
            for item in offered if mode=='clusters' else ():
                stats['proposal_trials']+=1;t=time.perf_counter();trace,child,cg=execute(model,s,g,item,tick);stats['proposal_validation_seconds']+=time.perf_counter()-t
                stats['constituent_branch_steps']+=sum(step['kind']=='branch' for step in trace['steps']);stats['constituent_forced_steps']+=sum(step['kind']=='forced' for step in trace['steps']);stats['validation_placements']+=len(trace['steps'])
                trial=dict(item=item,trace=trace)
                if len(transaction_samples)<20:transaction_samples.append(dict(order=list(s.order),**trial))
                tree['proposals'].append(trial)
                if trace['status']=='unknown_transaction_budget':raise Budget()
                if child is None:stats['proposal_rejections']+=1;continue
                stats['accepted_proposal_trials']+=1;trial['tree']=None;okay,sub=visit(child,cg,transactions+[dict(item,steps=trace['steps'])]);trial['tree']=sub
                if okay:return True,tree
                stats['backtracks']+=1
        # Every original legal base choice remains available, even if a
        # proposal beginning with that choice failed in a narrower context.
        for key in keys:
            tick();child=s.copy();cg=g.copy();cg.update(model,child,child.place(model.placement(key)));stats['singleton_attempts']+=1
            okay,sub=visit(child,cg,transactions);tree['children'].append(dict(key=key,tree=sub))
            if okay:return True,tree
            stats['backtracks']+=1
        return False,tree
    tree=None
    try:okay,tree=visit(state,graph,[]);status='finite_exact_proof_tiling' if okay else 'exhausted_finite_proof_envelope'
    except Budget:status='unknown_search_budget'
    selected=found or best
    if not S.point_check(model,selected.order,found is not None):raise ValueError('saved cluster state failed point check')
    result=dict(status=status,placements=selected.order,tile_generations=selected.tile_generations,nodes=stats['nodes'],base_attempts=stats['base_attempts'],stats=dict(stats),seconds=time.perf_counter()-began,build_seconds=build_seconds,graph_seconds=graph_seconds,index_seconds=index.seconds,index_instances=len(index.instances),index_complete=index.complete,library_sha256=library_sha,mode=mode,candidate_universe=len(model.cache),peak_candidate_nodes=peak_nodes,peak_incidences=peak_incidences,metrics=dict(model.metrics),samples=samples,transaction_samples=transaction_samples,solution_transactions=found_transactions,search_tree=tree,limits=dict(seconds=seconds,base_attempts=attempt_limit,proposal_limit=proposal_limit,index_instances=index_limit),scope='same complete base proof-tile grammar and scheduler; learned fragments propose scheduler-validated sequences or rank the next singleton, with all singleton alternatives retained; bounded contextual arithmetic proposer, not learned pruning')
    if found:
        before=time.perf_counter();result['decoded']=S.decode(c,selected.order,length);result['decode_seconds']=time.perf_counter()-before
    return result

def hierarchical_certificate(c,result,length,library):
    """Compile actual goal-chain transactions into checked nested block calls."""
    began=time.perf_counter();original=result['decoded']['request'];checked=check(canonical(original),expected_problem_sha256=problem_hash(original),max_work=None)
    if checked['status']!='accepted':raise ValueError('entire original proof must check')
    path=chain(c,result['placements'],length);templates={t['name']:t for t in library};transactions=result['solution_transactions'];blocks=[r['recipe']['definition'] for r in c['rules'] if r['recipe']['kind']=='block']+definitions(library);builder=Proof();mapping={};used=[];i=0
    while i<len(path):
        key=path[i];rule=c['rules'][key[1]];a=c['formulas'][rule['output']];choices=[tr for tr in transactions if tuple(tr['members'])==tuple(path[i:i+len(tr['members'])]) and i+len(tr['members'])<=len(path)]
        if choices:
            tr=max(choices,key=lambda tr:len(tr['members']));template=templates[tr['template']];act=summary_action(template,tr['instance']);anchor=c['formulas'][rule['inputs'][0]][1];p=L.Eq(anchor,act['before']);q=L.Eq(anchor,act['after']);out=Proof();source=out.emit('assumption',p,index=0);edge=out.append(proof_for_path(act['before'],[act]));hole=fresh(anchor,act['before'],act['after']);schema=out.emit('eq_subst',L.Imp(L.Eq(act['before'],act['after']),L.Imp(p,q)),variable=hole,template=L.Eq(anchor,L.V(hole)),left=act['before'],right=act['after']);out.mp(source,out.mp(edge,schema));name='cluster-instance-'+digest([template['name'],tr['instance'],anchor])[:20];b=dict(name=name,premises=[p],conclusion=q,proof=out.lines);blocks.append(b)
            ref=key[2][0];j=builder.emit('block',q,name=name,inputs=[mapping[ref]]);end=path[i+len(tr['members'])-1][0];mapping[end]=j;used.append(dict(template=template['name'],members=tr['members'],instance=tr['instance'],definition=name,root_line=j));i+=len(tr['members']);continue
        recipe=rule['recipe'];mapped=[mapping[ref] for ref in key[2]]
        if recipe['kind']=='primitive':w=dict(recipe['witness']);r=w.pop('rule');w.pop('formula');j=builder.emit(r,a,**w)
        elif recipe['kind']=='copy':taut=builder.emit('tautology',L.Imp(a,a));j=builder.mp(mapped[0],taut)
        else:j=builder.emit('block',a,name=recipe['definition']['name'],inputs=mapped)
        mapping[key[0]]=j;i+=1
    for x in reversed(c['close_variables']):builder.emit('generalize',L.All(x,builder.lines[-1]['formula']),variable=x,source=len(builder.lines)-1)
    value=request(c['theory'],c['target'],builder.lines,blocks);output=check(canonical(value),expected_problem_sha256=problem_hash(original),max_work=None)
    if output['status']!='accepted':raise ValueError(('hierarchical certificate rejected',output))
    return dict(request=value,check=output,input_check=checked,transactions_used=used,seconds=time.perf_counter()-began,original_root_lines=len(original['proof']),root_lines=len(value['proof']),definitions=len(value['blocks']))
