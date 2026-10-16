"""Closed discovered theorems become scoped marked proof-cell productions.

Each theorem type retains its source request and nested block dependencies.
All original compiled inferences remain. This extends the finite grammar;
primitive expansion proves soundness, not equality of finite cell envelopes.
Point search retains the existing exact model, scheduler and full fallback.
"""
import collections,copy,hashlib,time
import logic as L
import induction_proof_tiles as T,semantic_proof_tiles as S,semantic_proof_catalogs as C
import induction_clusters as H,coarse_proof_tiles as M
from induction_proof_catalogs import close,moves,definition,conditional_rewrite,ordinary_rewrite,induction_definition
from semantic_proof_tiles import frozen,body_target
from proof_block_search import Proof,equation,equations
from serialized_kernel import canonical,check,problem_hash,PROTOCOL
from audit_serialized_kernel import replay
from proof_clusters import digest
from turtle import Graph

def definitions_for(lines,available):
    by_name={}
    for b in available:
        if b['name'] in by_name and canonical(by_name[b['name']])!=canonical(b):raise ValueError('conflicting block identity')
        by_name[b['name']]=b
    out=[];seen=set();active=set()
    def visit(name):
        if name in active:raise ValueError('cyclic theorem dependency')
        if name in seen:return
        if name not in by_name:raise ValueError('missing theorem dependency '+name)
        active.add(name);b=by_name[name]
        for line in b['proof']:
            if line['rule']=='block':visit(line['name'])
        active.remove(name);seen.add(name);out.append(b)
    for line in lines:
        if line['rule']=='block':visit(line['name'])
    return out

def library_definitions(library):
    available=[]
    for item in library:
        available.extend(item['dependencies'])
        available.append({k:item[k] for k in ('name','premises','conclusion','proof')})
    return definitions_for([dict(rule='block',name=item['name']) for item in library],available)

def promote(problem,c,result):
    if result['status']!='finite_exact_proof_tiling' or result['decoded']['check']['status']!='accepted':raise ValueError('complete searched proof required')
    request=result['decoded']['request'];pin=problem_hash(request)
    if canonical(request['theory'])!=canonical(problem['theory']) or frozen(request['target'])!=frozen(problem['target']):raise ValueError('source theorem binding')
    checked=check(canonical(request),expected_problem_sha256=pin,max_work=None)
    expanded=replay(canonical(request),pin)
    if checked['status']!='accepted' or expanded['status']!='accepted':raise ValueError('closed theorem proof rejected')
    levels=[c['rules'][k[1]]['recipe'].get('learned_theorem',{}).get('level',0) for k in result['placements']]
    return dict(name='discovered-theorem-'+digest(request)[:24],premises=[],conclusion=frozen(request['target']),proof=request['proof'],dependencies=request['blocks'],expanded_rules=expanded['expanded_lines'],level=1+max(levels,default=0),theory=problem['theory'],source_id=problem['id'],source_request_sha256=digest(request),source_problem_sha256=pin)

def validate_library(theory,library):
    defs=library_definitions(library);levels={}
    for item in library:
        if item['premises'] or L.free(frozen(item['conclusion'])):raise ValueError('only closed zero-premise theorem types')
        if canonical(item['theory'])!=canonical(theory):raise ValueError('theorem theory mismatch')
        request=dict(protocol=PROTOCOL,theory=theory,target=item['conclusion'],blocks=item['dependencies'],proof=item['proof'])
        if item['name']!='discovered-theorem-'+digest(request)[:24] or digest(request)!=item['source_request_sha256'] or problem_hash(request)!=item['source_problem_sha256']:raise ValueError('theorem source hash mismatch')
        result=check(canonical(request),expected_problem_sha256=problem_hash(request),max_work=None)
        if result['status']!='accepted':raise ValueError('theorem source proof rejected')
        expanded=replay(canonical(request),problem_hash(request))
        if expanded['status']!='accepted' or expanded['expanded_lines']!=item['expanded_rules']:raise ValueError('theorem expansion count mismatch')
        calls={line['name'] for proof in [item['proof']]+[b['proof'] for b in item['dependencies']] for line in proof if line['rule']=='block' and line['name'].startswith('discovered-theorem-')}
        if calls-levels.keys():raise ValueError('unknown promoted theorem ancestor')
        if item['level']!=1+max((levels[n] for n in calls),default=0):raise ValueError('theorem hierarchy level mismatch')
        levels[item['name']]=item['level']
    return defs

def catalog(theory,target,term_bound,enable_induction=True,library=()):
    began=time.perf_counter();inherited=validate_library(theory,library);variables,body=body_target(target)
    if body[0]!='eq' or len(set(variables))!=len(variables) or L.free(body)-set(variables):
        raise ValueError('closed, distinctly quantified equational target required')
    terms=C.term_grammar(theory['functions'],variables,term_bound)
    axiom_rules=equations(theory,library);axiom_moves=tuple(moves(terms,axiom_rules))
    contexts=[dict(original=body[1],hypothesis=None,goal=body,closure=variables,kind='direct',variable=None)]
    induction=[]
    if enable_induction and 'nat-induction' in theory['schemas']:
        for x in variables:
            base=L.substitute(body,x,L.F('zero'));step=L.substitute(body,x,L.F('succ',L.V(x)))
            others=[v for v in variables if v!=x]
            contexts.extend([dict(original=base[1],hypothesis=None,goal=base,closure=others,kind='base',variable=x),
                             dict(original=step[1],hypothesis=body,goal=L.Imp(body,step),closure=others+[x],kind='step',variable=x)])
            induction.append((x,induction_definition(variables,body,x)))
    fs=set();rules=[];defs=[];descriptions=[];seen=set()
    def add(inputs,a,recipe):
        key=canonical([inputs,a,recipe])
        if key in seen:return
        seen.add(key);fs.add(a);fs.update(inputs);rules.append((inputs,a,recipe))
        if recipe['kind']=='block':
            if recipe.get('axiom') in {b['name'] for b in library}:
                item=next(b for b in library if b['name']==recipe['axiom']);recipe['learned_theorem']={k:item[k] for k in ('name','level','source_id','source_request_sha256','expanded_rules')}
            defs.append(recipe['definition'])
    for context in contexts:
        original,hypothesis=context['original'],context['hypothesis']
        if original not in terms:raise ValueError('required starting term outside finite grammar')
        wrap=lambda a:L.Imp(hypothesis,a) if hypothesis is not None else a
        for t in terms:fs.add(wrap(L.Eq(original,t)))
        reflex=L.Eq(original,original);seed=wrap(reflex)
        if hypothesis is None:add([],seed,dict(kind='primitive',witness=dict(rule='refl',formula=seed)))
        else:
            out=Proof();i=out.emit('refl',reflex);ax=out.emit('tautology',L.Imp(reflex,seed));out.mp(i,ax)
            add([],seed,dict(kind='block',definition=definition([],seed,out.lines),operation='conditional-reflexivity'))
        available=axiom_moves
        if hypothesis is not None:
            h=equation('fixed-induction-hypothesis',hypothesis,'assumption',index=0)
            available=axiom_moves+tuple(moves(terms,(h,)))
        descriptions.append(dict(context,move_count=len(available)))
        for move in available:
            p,q=[wrap(L.Eq(original,t)) for t in (move['before'],move['after'])]
            b=conditional_rewrite(original,hypothesis,move) if hypothesis is not None else ordinary_rewrite(original,move)
            add([p],q,dict(kind='block',definition=b,operation='conditional-rewrite' if hypothesis is not None else 'rewrite',context=dict(context),move={k:move[k] for k in ('before','after','bindings','path','direction')},axiom=move['rule']['name']))
        a=context['goal'];fs.add(a)
        for x in reversed(context['closure']):
            q=L.All(x,a);add([a],q,dict(kind='primitive',witness=dict(rule='generalize',formula=q,variable=x,source=0)));a=q
    for x,b in induction:add(b['premises'],b['conclusion'],dict(kind='block',definition=b,operation='induction',variable=x))
    defs=list({b['name']:b for b in defs}.values())
    all_defs=definitions_for([dict(rule='block',name=b['name']) for b in inherited+defs],inherited+defs)
    probe=dict(protocol=PROTOCOL,theory=theory,target=L.Imp(frozen(target),frozen(target)),blocks=all_defs,proof=[dict(rule='tautology',formula=L.Imp(frozen(target),frozen(target)))])
    start=time.perf_counter();checked=check(canonical(probe),expected_problem_sha256=problem_hash(probe),max_work=None,max_bytes=200000000)
    if checked['status']!='accepted':raise ValueError(('entire induction inventory rejected',checked))
    validation=time.perf_counter()-start
    result=C.catalog(theory,frozen(target),fs,rules,configuration=dict(kind='goal-derived-induction-with-discovered-theorems',term_bound=term_bound,terms=len(terms),variables=variables,enable_induction=enable_induction,contexts=descriptions,induction_variables=[x for x,b in induction],derived_rules=len(defs),templates='external target body only; every quantified target variable is an induction alternative; no supplied derivation or selected variable'))
    result.update(lemma_library=list(library),lemma_definitions=inherited,build_seconds=time.perf_counter()-began,validation_seconds=validation,inventory_check=checked)
    return result

def decode(catalog,keys,length):
    """Logical slot order is separate from the actual geometric placement order."""
    by_slot={k[0]:k for k in keys}
    if set(by_slot)!=set(range(length)) or len(by_slot)!=len(keys):raise ValueError('one proof tile per slot required')
    lines=[];finals=[];definitions={};commands=[]
    def emit(rule,a,**parameters):lines.append(dict(rule=rule,formula=a,**parameters));return len(lines)-1
    for slot in range(length):
        _,r,refs=by_slot[slot];item=catalog['rules'][r];a=catalog['formulas'][item['output']]
        if len(refs)!=len(item['inputs']) or any(type(i) is not int or not 0<=i<slot for i in refs):raise ValueError('invalid earlier reference')
        if any(catalog['rules'][by_slot[i][1]]['output']!=v for i,v in zip(refs,item['inputs'])):raise ValueError('formula port mismatch')
        mapped=[finals[i] for i in refs];recipe=item['recipe'];kind=recipe['kind']
        if kind=='primitive':
            w=copy.deepcopy(recipe['witness']);rule=w.pop('rule');formula=w.pop('formula')
            if frozen(formula)!=frozen(a):raise ValueError('changed primitive output')
            if rule=='mp':w.update(antecedent=mapped[0],implication=mapped[1])
            if rule=='generalize':w['source']=mapped[0]
            j=emit(rule,a,**w)
        elif kind=='copy':
            s=emit('tautology',L.Imp(frozen(a),frozen(a)));j=emit('mp',a,antecedent=mapped[0],implication=s)
        elif kind=='block':
            b=recipe['definition'];definitions[b['name']]=b;j=emit('block',a,name=b['name'],inputs=mapped)
        else:raise ValueError('unknown rule recipe')
        finals.append(j);commands.append(dict(slot=slot,rule=r,refs=refs,final_line=j))
    if catalog['rules'][by_slot[length-1][1]]['output']!=catalog['target_id']:raise ValueError('changed final theorem')
    for x in reversed(catalog.get('close_variables',[])):
        finals[-1]=emit('generalize',L.All(x,frozen(lines[finals[-1]]['formula'])),variable=x,source=finals[-1])
    request=dict(protocol=PROTOCOL,theory=catalog['theory'],target=catalog['target'],blocks=definitions_for(lines,list(catalog.get('lemma_definitions',[]))+[definitions[n] for n in sorted(definitions)]),proof=lines)
    checked=check(canonical(request),expected_problem_sha256=problem_hash(request))
    if checked['status']!='accepted':raise ValueError(('decoded semantic proof rejected',checked))
    return dict(request=request,check=checked,commands=commands)


def search(c,n,library=(),seconds=15,attempt_limit=50000,marked=True):
    began=time.perf_counter();model=H.Model(c,n,library,marked);build=time.perf_counter()-began
    state=model.initial();graph=Graph(model,state);graph_seconds=time.perf_counter()-began-build
    stats=collections.Counter(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,tile_attempts=0,macro_attempts=0);found=None;best=[]
    peaks=[len(graph.domains),len(graph.edges),sum(map(len,graph.domains.values()))]
    def visit(s,g):
        nonlocal found,best
        stats['nodes']+=1;t=dict(kind='cutoff',selected=list(s.order))
        if time.perf_counter()-began>seconds:t['cutoff']='wall_entry';return None,t
        kind,p,choices=g.decision(s);t.update(kind=kind,point=p,graph_sha256=digest(g.fingerprint()))
        peaks[1]=max(peaks[1],len(g.edges));peaks[2]=max(peaks[2],sum(map(len,g.domains.values())))
        if kind=='dead':return False,t
        if len(model.expansion(s.order))>len(model.expansion(best)):best=list(s.order)
        if kind=='empty':found=list(s.order);return True,t
        stats['forced' if kind=='forced' else 'branches']+=1;t['children']=[]
        for cid in sorted(choices,key=model.ordering):
            cost=len(model.descriptions[cid]['members'])
            if stats['base_attempts']+cost>attempt_limit:t['cutoff']='attempts_before_candidate';return None,t
            if time.perf_counter()-began>seconds:t['cutoff']='wall_before_candidate';return None,t
            stats['base_attempts']+=cost;stats['tile_attempts']+=1;stats['macro_attempts']+=int(cost>1)
            child=s.copy();cg=g.copy();cg.update(model,child,child.place(model.placement(cid)))
            ok,sub=visit(child,cg);t['children'].append(dict(candidate=cid,tree=sub))
            if ok is not False:return ok,t
            stats['backtracks']+=1
        return False,t
    ok,tree=visit(state,graph);selected=found if found is not None else best;placements=model.expansion(selected)
    if not S.point_check(model.base,placements,ok is True):raise ValueError('motifs expand to the original exact point model')
    r=dict(status='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope',marked=marked,
      selected=selected,placements=placements,tile_generations=[1]*len(selected),search_tree=tree if ok is not None else None,partial_tree=tree if ok is None else None,
      build_seconds=build,graph_seconds=graph_seconds,seconds=time.perf_counter()-began,base_universe=len(model.base.cache),candidate_universe=len(model.cache),motif_instances=len(model.instances),
      support_certificate=model.support_certificate,library_sha256=digest(library),peak_frontier_points=peaks[0],peak_candidate_nodes=peaks[1],peak_incidences=peaks[2],metrics=dict(model.metrics),limits=dict(seconds=seconds,base_attempts=attempt_limit),**stats)
    if ok:
        start=time.perf_counter();r['decoded']=decode(c,placements,n);r['decode_seconds']=time.perf_counter()-start
        r['solution_motifs']=[dict(candidate=cid,**model.descriptions[cid]) for cid in selected if model.descriptions[cid]['item'] is not None]
    return r

def csp_search(c,n,library=(),seconds=15,attempt_limit=50000,marked=True):
    """Same resource constraints and learned motifs offered to classical AC/MRV.

    Complete original variable domains are retained. A motif simultaneously
    assigns its original constituent values; every ordinary value is still tried
    after failed proposals. Motifs do not change classical support semantics.
    """
    began=time.perf_counter();binary=M.Binary(c,n);certificate=T.supports(c) if marked else None
    if certificate is not None:
        bounds=certificate['bound']
        for i,row in enumerate(binary.keys):
            for j,key in enumerate(row):
                slot,rid,refs=key;r=c['rules'][rid]
                contacts=((slot,r['output']),)+tuple(zip(refs,r['inputs']))
                if any(bounds[f] is None or bounds[f]>p+1 for p,f in contacts):binary.initial[i]&=~(1<<j)
    motifs=H.instances(c,n,library);index={key:(i,j) for i,row in enumerate(binary.keys) for j,key in enumerate(row)}
    values=[tuple(index[key] for key in item['members']) for item in motifs];by_slot=collections.defaultdict(list)
    for mid,assignment in enumerate(values):
        for i,j in assignment:by_slot[i].append(mid)
    build=time.perf_counter()-began
    stats=collections.Counter(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,macro_attempts=0,support_tests=0,removed_values=0,revisions=0);found=None;used=[]
    def order(mid):
        item=motifs[mid];return (-int(any(k[0]==n-1 for k in item['members'])),-len(item['members']),mid)
    def visit(incoming,path):
        nonlocal found,used
        stats['nodes']+=1;ds=list(incoming);tree=dict(kind='ac',incoming=[hex(x) for x in incoming],revisions=[],children=[])
        if not all(ds):tree.update(kind='dead',domains=[hex(x) for x in ds]);return False,tree
        queue=collections.deque((i,j) for i in range(n) for j in range(n) if i!=j)
        while queue:
            if time.perf_counter()-began>seconds:tree.update(cutoff='wall_ac',domains=[hex(x) for x in ds]);return None,tree
            i,j=queue.popleft();removed=0
            for k in M.indices(ds[i]):
                stats['support_tests']+=1
                if not binary.support(i,k,j)&ds[j]:removed|=1<<k
            stats['revisions']+=1;stats['removed_values']+=M.count(removed);tree['revisions'].append((i,j,hex(removed)));ds[i]&=~removed
            if not ds[i]:tree.update(kind='dead',domains=[hex(x) for x in ds]);return False,tree
            if removed:queue.extend((k,i) for k in range(n) if k!=i and k!=j)
        tree['domains']=[hex(x) for x in ds]
        if all(M.count(x)==1 for x in ds):
            found=[binary.keys[i][next(M.indices(mask))] for i,mask in enumerate(ds)];used=list(path);tree['kind']='empty';return True,tree
        i=min((i for i in range(n) if M.count(ds[i])>1),key=lambda i:(M.count(ds[i]),i));tree.update(kind='branch',slot=i);stats['branches']+=1
        offered=sorted((mid for mid in by_slot[i] if all(ds[j]&(1<<k) for j,k in values[mid])),key=order)
        choices=[('motif',mid,values[mid]) for mid in offered]+[('base',k,((i,k),)) for k in M.indices(ds[i])]
        for kind,choice,assignment in choices:
            cost=len(assignment)
            if stats['base_attempts']+cost>attempt_limit:tree['cutoff']='attempts_before_candidate';return None,tree
            if time.perf_counter()-began>seconds:tree['cutoff']='wall_before_candidate';return None,tree
            stats['base_attempts']+=cost;stats['macro_attempts']+=int(kind=='motif');child=list(ds)
            for j,k in assignment:child[j]=1<<k
            okay,sub=visit(child,path+([choice] if kind=='motif' else []));tree['children'].append(dict(mode=kind,choice=choice,tree=sub))
            if okay is not False:return okay,tree
            stats['backtracks']+=1
        return False,tree
    ok,tree=visit(binary.initial,[])
    r=dict(status='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope',marked=marked,support_certificate=certificate,
      placements=found or [],search_tree=tree if ok is not None else None,partial_tree=tree if ok is None else None,build_seconds=build,seconds=time.perf_counter()-began,
      base_universe=len(binary.model.cache),candidate_universe=len(binary.model.cache),motif_instances=len(motifs),library_sha256=digest(library),limits=dict(seconds=seconds,base_attempts=attempt_limit),**stats)
    if ok:
        if not S.point_check(binary.model,found,True):raise ValueError('classical witness expands to exact original points')
        start=time.perf_counter();r['decoded']=decode(c,found,n);r['decode_seconds']=time.perf_counter()-start;r['used_motif_proposals']=used
    return r
