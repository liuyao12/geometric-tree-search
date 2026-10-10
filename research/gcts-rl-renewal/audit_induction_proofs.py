"""Independent induction inventory, resource marks, all search prefixes and proofs.

No producer, catalog builder, point model, graph or solver is imported.
The frozen independently written prefix/proof auditor checks decoded commands
and all classical support removals; native execution remains a trusted layer.
"""
import collections,gzip,hashlib,itertools,json,time
from pathlib import Path
import logic as L
import audit_semantic_proofs as A
import audit_coarse_proofs as B
from audit_serialized_kernel import freeze
from audit_proof_compaction import native_binding

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(a):return hashlib.sha256(A.packed(a)).hexdigest()
def external_cases():
    # Independent declaration of the nominated statements, not proof witnesses.
    z=L.F('zero');s=lambda t:L.F('succ',t);plus=lambda p,q:L.F('add',p,q);mul=lambda p,q:L.F('mul',p,q)
    x,y,n,a,b=map(L.V,('x','y','n','a','b'))
    theory=dict(functions=dict(zero=0,succ=1,add=2),predicates={},axioms=dict(AZ=L.All('x',L.Eq(plus(x,z),x)),AS=L.All('x',L.All('y',L.Eq(plus(x,s(y)),s(plus(x,y)))))),schemas=['nat-induction'])
    multiplication=json.loads(A.packed(theory));multiplication['functions']['mul']=2;multiplication['axioms'].update(MZ=L.All('x',L.Eq(mul(x,z),z)),MS=L.All('x',L.All('y',L.Eq(mul(x,s(y)),plus(mul(x,y),x)))))
    no_schema=dict(theory,schemas=[]);zero=L.All('n',L.Eq(plus(z,n),n));out={}
    def add(id,t,target,length,bound):out[id]=freeze(dict(theory=t,target=target,length=length,term_bound=bound,enable_induction=True))
    add('ind-add-left-zero',theory,zero,7,4);add('ind-add-left-one',theory,L.All('n',L.Eq(plus(s(z),n),s(n))),7,5)
    add('ind-mul-left-zero',multiplication,L.All('n',L.Eq(mul(z,n),z)),8,5)
    add('ind-add-left-successor',theory,L.All('a',L.All('b',L.Eq(plus(s(a),b),s(plus(a,b))))),11,5)
    add('ind-no-schema',no_schema,zero,7,4);add('ind-too-short',theory,zero,6,4)
    add('ind-wrong-target',theory,L.All('n',L.Eq(plus(z,n),s(n))),7,4)
    return out
def close(a,names):
    for x in reversed(names):a=L.All(x,a)
    return a

def contexts(c):
    names=[];body=c['target']
    while body[0]=='all':names.append(body[1]);body=body[2]
    out=[dict(original=body[1],hypothesis=None,goal=body,closure=tuple(names),kind='direct',variable=None)]
    induction=[]
    if c['configuration']['enable_induction'] and 'nat-induction' in c['theory']['schemas']:
        for x in names:
            others=tuple(v for v in names if v!=x)
            base=L.substitute(body,x,L.F('zero'));step=L.substitute(body,x,L.F('succ',L.V(x)))
            out.extend([dict(original=base[1],hypothesis=None,goal=base,closure=others,kind='base',variable=x),
                        dict(original=step[1],hypothesis=body,goal=L.Imp(body,step),closure=others+(x,),kind='step',variable=x)])
            induction.append((x,(close(base,others),close(L.All(x,L.Imp(body,step)),others))))
    return names,body,out,induction

def edge_set(terms,axioms,hypothesis=None):
    grounded=collections.defaultdict(list)
    for name,a in list(axioms.items())+([('fixed-induction-hypothesis',hypothesis)] if hypothesis is not None else []):
        names=[]
        while a[0]=='all':names.append(a[1]);a=a[2]
        if a[0]!='eq':continue
        for values in itertools.product(terms,repeat=len(names)):
            env=dict(zip(names,values));left,right=[A.substitute_term(t,env) for t in a[1:]]
            for sign,p,q in ((1,left,right),(-1,right,left)):
                if p in terms:grounded[p].append((q,name,tuple(sorted(env.items())),sign))
    result=set()
    for before in terms:
        for path,sub in A.locations(before):
            for other,name,bindings,direction in grounded[sub]:
                after=A.put(before,path,other)
                if before!=after and after in terms:result.add((before,after,name,bindings,path,direction))
    return result

def inventory(c):
    names,body,declared,induction=contexts(c);conf=c['configuration'];fs=c['formulas'];index={a:i for i,a in enumerate(fs)}
    terms=A.bounded_terms(c['theory']['functions'],names,conf['term_bound'])
    expected_fs=set();expected=set();descriptions=[]
    def key(kind,inputs,out,extra=None):return sha([kind,inputs,out,extra])
    for context in declared:
        original,h=context['original'],context['hypothesis'];wrap=lambda a:L.Imp(h,a) if h is not None else a
        expected_fs.update(wrap(L.Eq(original,t)) for t in terms)
        seed=wrap(L.Eq(original,original));expected.add(key('conditional-reflexivity' if h is not None else 'refl',(),seed))
        edges=edge_set(terms,c['theory']['axioms'],h);descriptions.append(dict(context,move_count=len(edges)))
        for before,after,name,bindings,path,direction in edges:
            p,q=[wrap(L.Eq(original,t)) for t in (before,after)]
            expected.add(key('conditional-rewrite' if h is not None else 'rewrite',(p,),q,[context,before,after,name,bindings,path,direction]))
        a=context['goal'];expected_fs.add(a)
        for x in reversed(context['closure']):
            q=L.All(x,a);expected_fs.add(q);expected.add(key('generalize',(a,),q,x));a=q
    for x,premises in induction:expected.add(key('induction',premises,c['target'],x))
    A.need(set(fs)==expected_fs and len(fs)==len(expected_fs),'complete formula language, no witness-selected restriction')
    expected.update(key('copy',(a,),a) for a in fs)
    A.need(conf['kind']=='goal-derived-conditional-induction-equations' and conf['terms']==len(terms) and conf['variables']==tuple(names) and conf['induction_variables']==tuple(x for x,p in induction) and conf['contexts']==freeze(descriptions),'entire grammar and all induction-variable alternatives')
    actual=[];definitions={}
    for r in c['rules']:
        inputs=tuple(fs[i] for i in r['inputs']);out=fs[r['output']];recipe=r['recipe'];kind=recipe['kind'];extra=None
        if kind=='copy':operation='copy';A.need(inputs==(out,),'copy interface')
        elif kind=='primitive':
            w=recipe['witness'];operation=w['rule'];A.need(w['formula']==out,'primitive formula')
            if operation=='refl':A.need(not inputs and out[0]=='eq' and out[1]==out[2],'reflection interface')
            elif operation=='generalize':
                extra=w['variable'];A.need(len(inputs)==1 and out==L.All(extra,inputs[0]) and w['source']==0,'generalization as root inference')
            else:raise ValueError('unexpected primitive in grammar')
        else:
            A.need(kind=='block','declared compiled inference');operation=recipe['operation'];b=recipe['definition']
            A.need(b['premises']==inputs and b['conclusion']==out,'exact compiled interface')
            if b['name'] in definitions:A.need(definitions[b['name']]==b,'consistent definition identity')
            definitions[b['name']]=b
            if operation in ('rewrite','conditional-rewrite'):
                m=recipe['move'];extra=[recipe['context'],m['before'],m['after'],recipe['axiom'],tuple(sorted(m['bindings'].items())),m['path'],m['direction']]
            elif operation=='induction':extra=recipe['variable']
            else:A.need(operation=='conditional-reflexivity','known compiled rule kind')
        actual.append(key(operation,inputs,out,extra))
    A.need(set(actual)==expected and len(actual)==len(expected),'every bounded contextual rewrite, closure, induction and copy; no missing or duplicate type')
    A.need(len(definitions)==conf['derived_rules'],'whole definition inventory count')
    probe=dict(protocol='gcts-fol-1',theory=c['theory'],target=L.Imp(c['target'],c['target']),blocks=list(definitions.values()),proof=[dict(rule='tautology',formula=L.Imp(c['target'],c['target']))])
    replay=A.whole_replay(json.loads(A.packed(probe)),A.pin(probe));A.need(replay['status']=='accepted','every compiled proof independently expanded: '+replay.get('reason',''))
    return dict(terms=len(terms),formulas=len(fs),rules=len(actual),definitions=len(definitions),induction_variables=[x for x,p in induction])

def ranks(c):
    # Synchronous height layers, independent of the producer's in-place
    # relaxation order and its recorded witnesses.
    known={r['output']:0 for r in c['rules'] if not r['inputs']};depth=1
    while True:
        new={r['output'] for r in c['rules'] if r['output'] not in known and r['inputs'] and all(i in known for i in r['inputs'])}
        if not new:break
        known.update({i:depth for i in new});depth+=1
    return tuple(known.get(i) for i in range(len(c['formulas'])))

def depth_certificate(c,certificate):
    expected=ranks(c);A.need(certificate['rank']==expected,'least formula dependency height')
    current=[None]*len(expected)
    for iteration,changes in enumerate(certificate['rounds']):
        actual=[]
        for rid,r in enumerate(c['rules']):
            inputs=[current[i] for i in r['inputs']]
            if any(i is None for i in inputs):continue
            d=0 if not inputs else 1+max(inputs);i=r['output']
            if current[i] is None or d<current[i]:current[i]=d;actual.append((i,d,rid))
        A.need(tuple(actual)==changes,'each dependency-bound certificate witness')
        A.need(bool(changes)==(iteration<len(certificate['rounds'])-1),'fixed point ends at first empty relaxation pass')
    A.need(tuple(current)==expected,'complete least-height certificate')
    return dict(reachable=sum(i is not None for i in expected),unreachable=sum(i is None for i in expected),rounds=len(certificate['rounds']))

def support_bounds(c):
    # A separate backward graph traversal per formula, not bitset relaxation.
    parents=collections.defaultdict(set)
    for r in c['rules']:parents[r['output']].update(r['inputs'])
    cones=[]
    for start in range(len(c['formulas'])):
        seen={start};pending=[start]
        while pending:
            p=pending.pop()
            for q in parents[p]-seen:seen.add(q);pending.append(q)
        cones.append(frozenset(seen))
    disjoint=tuple(all(not (cones[p]&cones[q]) for i,p in enumerate(r['inputs']) for q in r['inputs'][i+1:]) for r in c['rules'])
    known={r['output']:1 for r in c['rules'] if not r['inputs']}
    while True:
        following=dict(known)
        for rid,r in enumerate(c['rules']):
            if not all(i in known for i in r['inputs']):continue
            values=[known[i] for i in r['inputs']];value=1+(sum(values) if disjoint[rid] else max(values,default=0));out=r['output']
            if out not in following or value<following[out]:following[out]=value
        if following==known:break
        known=following
    return tuple(known.get(i) for i in range(len(cones))),cones,disjoint

def support_certificate(c,certificate):
    expected,cones,disjoint=support_bounds(c)
    A.need(certificate['bound']==expected and certificate['disjoint']==disjoint,'independent disjoint-cone ancestral-cell bound')
    A.need(tuple(certificate['cones'])==tuple(hex(sum(1<<i for i in cone)) for cone in cones),'entire backward formula cones, including cycles')
    current=[None]*len(expected)
    for iteration,changes in enumerate(certificate['rounds']):
        actual=[]
        for rid,r in enumerate(c['rules']):
            values=[current[i] for i in r['inputs']]
            if any(v is None for v in values):continue
            value=1+(sum(values) if disjoint[rid] else max(values,default=0));out=r['output']
            if current[out] is None or value<current[out]:current[out]=value;actual.append((out,value,rid))
        A.need(tuple(actual)==changes,'each support-bound witness')
        A.need(bool(changes)==(iteration<len(certificate['rounds'])-1),'complete support-bound fixed point')
    A.need(tuple(current)==expected,'support certificate terminal bounds')
    return dict(reachable=sum(v is not None for v in expected),target_bound=expected[c['target_id']],disjoint_joins=sum(ok and len(r['inputs'])>1 for ok,r in zip(disjoint,c['rules'])),rounds=len(certificate['rounds']))

class Points(B.Points):
    def __init__(self,c,n,marking='none'):
        # Enumerate base candidates directly. The historical cluster auditor
        # preprocesses rewrite-only block recipes even for an empty library;
        # conditional seeds and induction joins are deliberately broader here.
        self.n=n;self.target=c['target_id'];self.width=1;self.base=A.candidates(c,n)
        self.groups=tuple((i,) for i in range(n));self.items=();self.tiles=[]
        self.root={(2*i,0) for i in range(n)}
        for key in sorted(self.base):
            cid=len(self.tiles);marks={(2*j,1):v for j,v in self.base[key].items()}
            marks[(2*key[0],2)]=cid
            self.tiles.append(dict(weights={(2*key[0],0):12},marks=marks,members=(key,),item=None))
        self.initial_marks={(2*(n-1),1):c['target_id']}
        if marking=='depth':
            heights=ranks(c);self.initial_marks.update({(2*i,3):0 for i in range(n)})
            for t in self.tiles:
                slot,rid,refs=t['members'][0];d=heights[c['rules'][rid]['output']]
                t['marks'][(2*slot,3)]=int(d is None or d>slot)
        elif marking=='support':
            bounds,_,_=support_bounds(c);self.initial_marks.update({(2*i,4):0 for i in range(n)})
            for t in self.tiles:
                slot,rid,refs=t['members'][0];rule=c['rules'][rid]
                for j,fid in ((slot,rule['output']),)+tuple(zip(refs,rule['inputs'])):
                    b=bounds[fid];t['marks'][(2*j,4)]=int(b is None or b>j+1)
        else:A.need(marking=='none','declared marking type')
    def domains(self,ids):
        totals=collections.Counter();marks=dict(self.initial_marks);seen=set()
        for cid in ids:
            A.need(type(cid) is int and 0<=cid<len(self.tiles) and cid not in seen,'candidate identity');seen.add(cid);t=self.tiles[cid]
            for p,v in t['weights'].items():totals[p]+=v;A.need(totals[p]<=12,'exact single-cell capacity')
            for p,v in t['marks'].items():A.need(p not in marks or marks[p]==v,'all formula, owner and certified resource markings agree');marks[p]=v
        ds={p:set() for p in self.root if totals[p]<12}
        for cid,t in enumerate(self.tiles):
            if cid not in seen and all(totals[p]+v<=12 for p,v in t['weights'].items()) and all(p not in marks or marks[p]==v for p,v in t['marks'].items()):
                for p in t['weights'].keys()&ds.keys():ds[p].add(cid)
        return ds

def point_run(c,n,r):
    marking=r['marking'];points=Points(c,n,marking);A.need(r['marked']==(marking!='none'),'declared installed marking')
    A.need(r['groups']==points.groups and r['base_universe']==len(points.base) and r['candidate_universe']==len(points.tiles) and r['index_instances']==0,'all original candidate types retained')
    depth=depth_certificate(c,r['depth_certificate']) if marking=='depth' else None
    support=support_certificate(c,r['support_certificate']) if marking=='support' else None
    A.need(marking=='depth' or r['depth_certificate'] is None,'only depth lane has depth certificate')
    A.need(marking=='support' or r['support_certificate'] is None,'only support lane has support certificate')
    initial=points.domains([]);stats=dict(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,tile_attempts=0)
    best=[];leaf=None;cuts=0;peaks=[n,len(set().union(*initial.values())),sum(map(len,initial.values()))]
    def visit(t,ids):
        nonlocal best,leaf,cuts
        stats['nodes']+=1;A.need(t['selected']==tuple(ids),'actual saved point prefix');ds=points.domains(ids)
        if t['kind']=='cutoff':A.need(t.get('cutoff')=='wall_entry' and r['seconds']>=r['limits']['seconds'],'entry wall cutoff');cuts+=1;return None
        kind,p,choices=points.decision(ds);A.need(t['kind']==kind and t['point']==p,'global dead/forced/generation decision')
        candidates=set().union(*ds.values()) if ds else set();peaks[1]=max(peaks[1],len(candidates));peaks[2]=max(peaks[2],sum(map(len,ds.values())))
        edges={cid:tuple(sorted(p for p,values in ds.items() if cid in values)) for cid in candidates}
        fingerprint=(tuple(sorted((p,tuple(sorted(values))) for p,values in ds.items())),tuple(sorted(edges.items())))
        A.need(t['graph_sha256']==sha(fingerprint),'entire graph independently reconstructed including mark-only elimination')
        if kind=='dead':return False
        if len(ids)>len(best):best=list(ids)
        if kind=='empty':leaf=list(ids);return True
        stats['forced' if kind=='forced' else 'branches']+=1;children=t['children']
        A.need(tuple(x['candidate'] for x in children)==tuple(choices[:len(children)]),'complete candidate ordering prefix')
        for j,child in enumerate(children):
            stats['base_attempts']+=1;stats['tile_attempts']+=1;ok=visit(child['tree'],ids+[child['candidate']])
            if ok is not False:A.need(j==len(children)-1 and 'cutoff' not in t,'stop at open or successful child');return ok
            stats['backtracks']+=1
        if 'cutoff' in t:
            A.need(len(children)<len(choices),'remaining open suffix');reason=t['cutoff'];A.need(reason in ('wall_before_candidate','attempts_before_candidate'),'declared cutoff')
            A.need(r['seconds']>=r['limits']['seconds'] if reason.startswith('wall') else stats['base_attempts']>=r['limits']['base_attempts'],'actual budget reached');cuts+=1;return None
        A.need(len(children)==len(choices),'closed exhaustion covers every candidate');return False
    tree=r['search_tree'] if r['search_tree'] is not None else r['partial_tree'];ok=visit(tree,[])
    status='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope'
    A.need(r['status']==status and cuts==int(ok is None),'tri-state status and one open suffix')
    A.need((r['search_tree'] is None)==(ok is None) and (r['partial_tree'] is None)==(ok is not None),'closed/open distinction')
    A.need(all(r[k]==v for k,v in stats.items()) and stats['base_attempts']<=r['limits']['base_attempts'],'every executed trial and backtrack')
    selected=leaf if ok else best;A.need(r['selected']==tuple(selected) and r['placements']==points.expand(selected),'actual saved expansion')
    A.need(r['tile_generations']==(1,)*len(selected),'generation-zero finite roots')
    A.need((r['peak_frontier_points'],r['peak_candidate_nodes'],r['peak_incidences'])==tuple(peaks),'graph peak accounting')
    A.domains(points.base,n,c['target_id'],r['placements'])
    if ok:A.need(r['solution_transactions']==(),'no hidden cluster supplied');A.check_decoded(c,n,r)
    else:A.need('decoded' not in r,'no proof at a cutoff')
    initial_original=Points(c,n).domains([])
    return dict(**stats,cutoffs=cuts,depth=depth,support=support,initial_candidates_eliminated=len(set().union(*initial_original.values()))-len(set().union(*initial.values())),exact_solution=ok is True)

def load_case(descriptor,docs=DOCS):
    file=docs/descriptor['file'];blob=file.read_bytes();A.need(hashlib.sha256(blob).hexdigest()==descriptor['sha256'] and len(blob)==descriptor['bytes'],'exact compressed case binding')
    payload=gzip.decompress(blob);A.need(hashlib.sha256(payload).hexdigest()==descriptor['raw_sha256'] and len(payload)==descriptor['raw_bytes'],'exact full case/tree binding')
    case=json.loads(payload);A.need(case['problem']==descriptor['problem'],'index/case external statement binding');return case

def audit(path=DOCS/'induction-proofs-001.json'):
    path=Path(path);raw=json.loads(path.read_text());d=freeze(raw);began=time.perf_counter()
    for name,pin in raw['sources'].items():A.need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==pin,'frozen measured source '+name)
    code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program'];A.need(d['program_sha256']==sha(code) and not d['initial_library'] and d['policy'] is None,'fixed checker, empty library and no policy')
    expected=external_cases();A.need(set(expected)=={r['problem']['id'] for r in d['cases']} and len(d['cases'])==len(expected),'entire independently declared external case set')
    A.need(d['configuration']==dict(seconds=15,base_attempts=50000,native_steps=100000000,lanes=('gcts','depth-marked','support-marked','csp')),'fixed matched experiment configuration')
    reports=[]
    for i,descriptor in enumerate(raw['cases']):
        A.need(descriptor['file']=='induction-proof-cases-001/'+descriptor['problem']['id']+'.json.gz','named immutable case shard')
        row=freeze(load_case(descriptor))
        p=row['problem'];c=row['catalog'];A.need({k:p[k] for k in expected[p['id']]}==expected[p['id']],'external statement/bounds reconstructed independently')
        A.need(c['theory']==p['theory'] and c['target']==p['target'] and c['configuration']['term_bound']==p['term_bound'] and c['configuration']['enable_induction']==p['enable_induction'] and sha(c)==row['catalog_sha256'],'original theory, target and grammar binding')
        language=inventory(c);lanes=('gcts','depth-marked','support-marked','csp');shift=i%4
        A.need(tuple(r['lane'] for r in row['runs'])==lanes[shift:]+lanes[:shift],'rotating lane order');runs=[]
        for run in row['runs']:
            r=run['result'];A.need(run['catalog_sha256']==row['catalog_sha256'] and r['limits']==dict(seconds=d['configuration']['seconds'],base_attempts=d['configuration']['base_attempts']),'matched finite catalog and declared budgets')
            if run['lane']=='csp':report=B.csp_run(c,p['length'],r)
            else:A.need(r['marking']=={'gcts':'none','depth-marked':'depth','support-marked':'support'}[run['lane']],'declared marking lane');report=point_run(c,p['length'],r)
            if 'decoded' in r:
                request=r['decoded']['request'];native_binding(code,json.loads(A.packed(request)),json.loads(A.packed(run['native'])));A.need(run['native']['status']=='accepted','complete native gate')
                report['proof']=A.check_decoded(c,p['length'],r);report['native_status']='accepted'
            else:A.need('native' not in run,'no acceptance claim on unknown/exhaustion')
            runs.append(dict(lane=run['lane'],report=report))
        reports.append(dict(id=p['id'],inventory=language,runs=runs));print('audited',p['id'],flush=True)
    result=dict(status='passed',seconds=time.perf_counter()-began,cases=reports,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Independent complete finite induction and rewrite inventory; every compiled proof fully expanded; least dependency heights and disjoint-cone ancestral-cell bounds; actual mark-only graph elimination; all point/classical closed or open prefixes and decoded proofs/native bindings. No imported solver, catalog generator or producer; native instructions and universal compiler soundness remain trusted.')
    raw['independent_audit']=result;path.write_text(json.dumps(raw,separators=(',',':'))+'\n');return result

if __name__=='__main__':print('passed',audit()['seconds'])
