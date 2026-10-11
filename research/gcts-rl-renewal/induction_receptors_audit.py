"""Independent finite occurrence catalog, point inventories, trees and native I/O.

Does not import the new catalog, point producer, runner or search. The literal
auditor scans all placements at every tree node. Native replay starts at the
actual parser, checks whole input/output bands and FNV, with a separately written
logical replay as an additional audit check only.
"""
import collections,copy,gzip,hashlib,itertools,json,subprocess,time
from pathlib import Path
from audit_semantic_inventory import LiteralDomains,legal,advance
from audit_native_receptor_points import state_pin
from audit_certificate_boundary import initial_for,pin,sha
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_semantic_proofs import whole_replay
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/induction-receptors-20261011';TMP=Path('/private/tmp/gcts-induction-receptors-audit-20261011')
def packed(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def need(t,m):
    if not t:raise ValueError(m)
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def frozen(x):return tuple(frozen(v) for v in x) if isinstance(x,list) else x
def plain(x):
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    return x
def term_size(t):return 1+sum(term_size(a) for a in t[2]) if t[0]=='fun' else 1
def terms(functions,variables,bound):
    pool={('var',v) for v in variables}|{('fun',f,()) for f,a in functions.items() if a==0}
    while True:
        old=pool.copy()
        for f,a in sorted(functions.items()):
            if a:
                for children in itertools.product(sorted(old),repeat=a):
                    t=('fun',f,children)
                    if term_size(t)<=bound:pool.add(t)
        if pool==old:break
    return sorted(pool,key=lambda t:packed(plain(t)))
def positions(t):
    todo=[((),t)];out=[]
    while todo:
        path,sub=todo.pop();out.append((path,sub))
        if sub[0]=='fun':todo.extend((path+(i,),a) for i,a in enumerate(sub[2]))
    return out
def at(t,path,value):
    if not path:return value
    children=list(t[2]);children[path[0]]=at(children[path[0]],path[1:],value)
    return ('fun',t[1],tuple(children))
def substitute_term(t,env):
    if t[0]=='var':return env.get(t[1],t)
    return ('fun',t[1],tuple(substitute_term(a,env) for a in t[2]))
def independent_moves(pool,equations):
    allowed=set(pool);moves={}
    for rule in equations:
        # Independently exhaust all substitutions, including variables absent
        # from the matched side, instead of producer pattern unification.
        for values in itertools.product(pool,repeat=len(rule['variables'])):
            env=dict(zip(rule['variables'],values));lhs,rhs=[substitute_term(t,env) for t in rule['body'][1:]]
            for direction,old,new in ((1,lhs,rhs),(-1,rhs,lhs)):
                for before in pool:
                    for path,sub in positions(before):
                        if sub!=old:continue
                        after=at(before,path,new)
                        if after not in allowed or before==after:continue
                        m=plain(dict(before=before,after=after,path=path,bindings=env,direction=direction,rule=rule));moves[packed(m)]=m
    return [moves[k] for k in sorted(moves)]
def catalog_binding(c,spec):
    target=frozen(spec['target']);names=[];body=target
    while body[0]=='all':names.append(body[1]);body=body[2]
    pool=terms(spec['theory']['functions'],names,spec['term_bound']);need(plain(pool)==c['terms'] and names==c['variables'],'complete finite eigen term grammar')
    eqs=[]
    for name,raw in sorted(spec['theory']['axioms'].items()):
        f=frozen(raw);vs=[];b=f
        while b[0]=='all':vs.append(b[1]);b=b[2]
        if b[0]=='eq':eqs.append(dict(name=name,formula=f,variables=vs,body=b,origin='axiom'))
    base=independent_moves(pool,eqs);seen_contexts=[];counts=[]
    for ctx in c['contexts']:
        H=ctx['hypothesis'];expected=base
        if H is not None:expected=base+independent_moves(pool,[dict(name='induction-hypothesis',formula=frozen(H),variables=[],body=frozen(H),origin='assumption')])
        got=[r['description']['move'] for r in c['rules'] if r['description']['operation'] in ('rewrite','conditional-rewrite') and r['description']['context']['kind']==ctx['kind'] and r['description']['context']['variable']==ctx['variable']]
        need(sorted(map(packed,got))==sorted(map(packed,expected)),'every direction, occurrence, missing substitution and IH move')
        need(ctx['move_count']==len(expected),'declared complete move count');counts.append(dict(kind=ctx['kind'],moves=len(expected)))
        def wrap(t):
            f=['eq',ctx['original'],t]
            return ['imp',H,f] if H is not None else f
        expected_interfaces=sorted(packed([[wrap(m['before'])],wrap(m['after'])]) for m in expected)
        actual_interfaces=sorted(packed([r['premises'],r['conclusion']]) for r in c['rules'] if r['description']['operation'] in ('rewrite','conditional-rewrite') and r['description']['context']['kind']==ctx['kind'] and r['description']['context']['variable']==ctx['variable'])
        need(actual_interfaces==expected_interfaces,'each exact ordinary/conditional contextual edge interface')
        seeds=[r for r in c['rules'] if r['description']['operation'] in ('reflexivity','conditional-reflexivity') and r['description']['context']['kind']==ctx['kind'] and r['description']['context']['variable']==ctx['variable']]
        need(len(seeds)==1 and seeds[0]['premises']==[] and seeds[0]['conclusion']==wrap(ctx['original']),'every context has exactly its generic reflexivity seed')
        seen_contexts.append((ctx['kind'],ctx['variable']))
    wanted=[('direct',None)]
    if 'nat-induction' in spec['theory']['schemas'] and spec.get('enable_induction',True):
        wanted += [(kind,x) for x in names for kind in ('base','step')]
    need(seen_contexts==wanted,'every target-variable induction alternative, no selected variable')
    definitions={d['name']:d for d in c['definitions']};need(len(definitions)==len(c['definitions']),'distinct native definitions')
    primitive=[];expected_conclusions=set();expected_rules=[]
    from audit_first_order import subst,free
    for ctx in c['contexts']:
        orig=ctx['original'];H=ctx['hypothesis'];closure=ctx['closure']
        for t in c['terms']:
            f=['eq',orig,t];f=['imp',H,f] if H is not None else f;expected_conclusions.add(packed(f))
            for x in reversed(closure):
                q=['all',x,f];expected_rules.append(([f],q,dict(rule='generalize',formula=q,variable=x)));expected_conclusions.add(packed(q));f=q
    actual_rules=[(r['premises'],r['conclusion'],r['command']) for r in c['rules'] if r['command']['rule']=='generalize']
    need(sorted(map(packed,actual_rules))==sorted(map(packed,expected_rules)),'all contextual formula generalization guards')
    need(set(map(packed,c['basis']))==expected_conclusions,'entire contextual formula catalog')
    for f in c['basis']:
        if f[0]=='all':
            for t in c['terms']:primitive.append(dict(rule='instantiate',formula=['imp',f,subst(f[2],f[1],t)],universal=f,term=t))
        if f[0]=='imp':
            for x in names:
                if x not in free(f[1]):primitive.append(dict(rule='distribute',formula=['imp',['all',x,f],['imp',f[1],['all',x,f[2]]]],variable=x,antecedent=f[1],consequent=f[2]))
    for x in names:
        if 'nat-induction' not in spec['theory']['schemas']:continue
        p=plain(body);b=subst(p,x,['fun','zero',[]]);step=['all',x,['imp',p,subst(p,x,['fun','succ',[['var',x]]])]]
        schema=['imp',['and',b,step],['all',x,p]]
        for y in reversed(sorted(free(p)-{x})):schema=['all',y,schema]
        primitive.append(dict(rule='induction',formula=schema,variable=x,template=p))
    primitives=sorted({packed(p):p for p in primitive}.values(),key=packed)
    need(primitives==c['primitive_schemes'],'independent complete exposed primitive syntax')
    for r in c['rules']:
        command=r['command'];need(command['formula']==r['conclusion'],'inference output identity')
        if command['rule']=='block':
            d=definitions[command['name']];need(d['premises']==r['premises'] and d['conclusion']==r['conclusion'],'exact native lemma interface')
        elif command['rule']=='refl':need(not r['premises'] and r['conclusion'][1]==r['conclusion'][2],'primitive reflexivity')
        elif command['rule']=='generalize':need(r['conclusion']==['all',command['variable'],r['premises'][0]],'primitive generalization exact input')
        else:raise ValueError('undeclared primitive inference')
    return dict(terms=len(pool),contexts=counts,definitions=len(definitions),rules=len(c['rules']),primitive_schemes=len(primitives))
def model_binding(spec,c,record):
    rules=c['rules'];words={kind:sorted({packed(v) for v in vals}) for kind,vals in [('formula',c['basis']),('command',[r['command'] for r in rules])]};ids={k:{w:i for i,w in enumerate(v)} for k,v in words.items()}
    def assign(j,kind,value):return [((4*j+2,0 if kind=='formula' else 1),ids[kind][packed(value)])]
    expected_catalog={kind:[dict(id=i,value=json.loads(w),word_hex=w.hex(),expanded_points=len(w)+1) for i,w in enumerate(ws)] for kind,ws in words.items()}
    need(record['catalog']==expected_catalog,'entire injective AST/canonical word dictionary')
    placements=[];domains=[];modes={i:i+1 if r['premises'] else 0 for i,r in enumerate(rules)}
    def add(key,entries,command,requirements,kind,**extra):
        mark={}
        for p,v in entries:need(p not in mark or mark[p]==v,'internally consistent placement');mark[p]=v
        placements.append(dict(key=key,occupancy=[((4*key[0],key[1]),12)],marks=sorted(mark.items()),slot=key[0],kind=kind,command=command,requirements=requirements,**extra))
    for j in range(spec['length']):
        rows=[dict(rule=i,command=r['command']) for i,r in enumerate(rules) if j+1<spec['length'] or r['conclusion']==spec['target']];domains.append(rows)
        for k,row in enumerate(rows):
            i=row['rule'];r=rules[i];entries=assign(j,'command',r['command'])+assign(j,'formula',r['conclusion'])+[((4*j+2,90),modes[i])]
            for role,kind in ((0,'command'),(1,'guard')):add((j,role,k,0),entries,r['command'],[],kind,inference=i)
        for role in range(2):
            add((j,2+role,0,0),[((4*j+2,90),0),((4*j+2,100+role),-1)],None,[],'unused_input',input=role,mode=0,source=None)
            for i,r in enumerate(rules):
                mode=modes[i]
                if not mode:continue
                if role>=len(r['premises']):add((j,2+role,mode,0),[((4*j+2,90),mode),((4*j+2,100+role),-1)],None,[],'unused_input',input=role,mode=mode,source=None)
                else:
                    for source in range(j):
                        p=r['premises'][role];add((j,2+role,mode,source+1),[((4*j+2,90),mode),((4*j+2,100+role),source)]+assign(source,'formula',p),None,[(source,p)],'inference_input',input=role,mode=mode,source=source)
    need(packed(record['domains'])==packed(domains) and packed(record['placements'])==packed(sorted(placements,key=lambda p:p['key'])),'every command guard input placement, no missing candidate')
    need(record['roots']==[[4*j,role] for j in range(spec['length']) for role in range(4)],'all root obligations generation zero')
    need(packed(record['initial_marks'])==packed(assign(spec['length']-1,'formula',spec['target'])),'only target boundary is pinned')
    return placements
def tree_binding(raw):
    spec=raw['case'];model=raw['model'];result=raw['search'];inventory={tuple(c['key']):c for c in model['placements']};literal=LiteralDomains(inventory);roots={tuple(p):0 for p in model['roots']};metrics=collections.Counter();found=None
    root=dict(totals={},marks={tuple(p):v for p,v in model['initial_marks']},generations=roots.copy(),roots=roots,selected=set(),order=[],tile_generations=[])
    def walk(s,t):
        nonlocal found
        metrics['nodes']+=1;d=literal(s);census=[dict(point=p,generation=s['generations'][p],keys=ks) for p,ks in sorted(d.items())]
        need(packed(t['census'])==packed(census) and t['state_sha256']==state_pin(s),'full independent frontier at every state')
        dead=sorted(p for p,v in d.items() if not v);forced=sorted(p for p,v in d.items() if len(v)==1)
        if dead:kind,p='dead',dead[0]
        elif forced:kind,p='forced',forced[0]
        elif not d:kind,p='empty',None
        else:kind,p='branch',min(d,key=lambda p:(s['generations'][p],len(d[p]),p))
        need(t['kind']==kind and packed(t['point'])==packed(p),'global dead before forced before earliest generation')
        if kind=='empty':found=s;need(not t['children'],'terminal exact region');return True
        if kind=='dead':metrics['dead']+=1;need(not t['children'],'dead has no alternatives');return False
        metrics[kind]+=1
        for i,child in enumerate(t['children']):
            need(i<len(d[p]) and tuple(child['key'])==d[p][i],'every original alternative/fallback in order');metrics['attempts']+=1
            q=walk(advance(inventory[d[p][i]],s),child['tree'])
            if q is not False:need(i+1==len(t['children']),'no siblings after accept or unknown');return q
            metrics['backtracks']+=1
        if len(t['children'])<len(d[p]):
            need(t.get('cutoff')=='before_placement' and (metrics['attempts']>=result['limits']['attempts'] or result['seconds']>=result['limits']['seconds']),'soft budget means unknown');return None
        need('cutoff' not in t,'fully exhausted alternatives');return False
    answer=walk(root,result['tree']);status='finite_marked_proof_region' if answer else 'unknown_search_budget' if answer is None else 'exhausted_finite_marked_region'
    need(result['status']==status and result['metrics']==dict(metrics) and result['root_restored'] and result['root_state_sha256']==state_pin(root),'all counters, root rollback and terminal semantics')
    need(packed(result['placements'])==packed(found['order'] if found else []),'actual selected expansion')
    if found:
        by={(4*k[0],k[1]):inventory[k] for k in found['selected']};proof=[];skeleton=[]
        for j in range(spec['length']):
            cc=copy.deepcopy(by[4*j,0]['command']);gg=by[4*j,1];need(cc==gg['command'],'selected C/G match');skeleton.append(copy.deepcopy(cc));rule=model['inference_rules'][gg['inference']];refs=[]
            for r,premise in enumerate(rule['premises']):
                tile=by[4*j,2+r];i=tile['source'];need(0<=i<j and by[4*i,0]['command']['formula']==premise,'each exact earlier source receptor');refs.append(i)
            if cc['rule']=='block':cc['inputs']=refs
            elif cc['rule']=='generalize':cc['source']=refs[0]
            proof.append(cc)
        need(result['proof']==proof and result['command_skeleton']==skeleton,'complete source-explicit proof decode')
    else:need(result['proof'] is None and result['command_skeleton'] is None,'unknown has no proof')
    return dict(metrics)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());c=load(OUT/'catalog.json.gz');records=load(OUT/'native-records.json.gz');admission=load(OUT/'admission.json.gz');summary=json.loads((OUT/'summary.json').read_text())
    for p,h in plan['source_sha256'].items():need(sha(ROOT/p)==h,'frozen source '+p)
    result=dict(status='checking',catalog=catalog_binding(c,plan['case']),observations=[],queries=len(records));requests={};taut=['imp',['bot'],['bot']]
    for d,item in zip(c['definitions'],admission['definitions']):
        q=item['query'];r=dict(protocol='gcts-fol-1',theory=plan['case']['theory'],blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut)
        need(item['name']==d['name'] and records[q]['request']==r and records[q]['result']['status']=='accepted','each native-admitted generic local definition');requests[q]=r
    need(len(admission['definitions'])==len(c['definitions']) and admission['status']=='native_accepted','complete equation inventory admission')
    for item,command in zip(admission['primitive'],c['primitive_schemes']):
        q=item['query'];r=dict(protocol='gcts-fol-1',theory=plan['case']['theory'],blocks=[],proof=[command],target=command['formula']);need(records[q]['request']==r and item['command']==command,'exposed primitive prefix exact query');requests[q]=r
    need(len(admission['primitive'])==min(plan['primitive_query_budget'],len(c['primitive_schemes'])) and admission['primitive_status']=='unknown_compile_budget','partial primitive compilation remains unknown')
    for item in summary['probes']:
        q=item['query'];need(records[q]['result']['status']==item['expected'],'native hygienic scope probe');requests[q]=records[q]['request']
    for observed in plan['observations']:
        raw=load(OUT/(observed['id']+'.json.gz'));spec=copy.deepcopy(plan['case']);spec.update(id=observed['id'],length=observed['length']);need(raw['case']==spec,'predeclared target and observation')
        model_binding(spec,c,raw['model']);metrics=tree_binding(raw);q=raw['native_query']
        if raw['search']['proof'] is not None:
            names={r['name'] for r in raw['search']['proof'] if r['rule']=='block'};r=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[d for d in c['definitions'] if d['name'] in names],proof=raw['search']['proof'],target=spec['target'])
            need(q is not None and records[q]['request']==r and records[q]['result']['status']=='accepted','whole target proof with all used definitions');requests[q]=r
        else:need(q is None,'unknown cannot claim native acceptance')
        result['observations'].append(dict(id=spec['id'],status=raw['search']['status'],metrics=metrics))
    need(set(requests)==set(range(len(records))),'every native computation has accounted provenance')
    TMP.mkdir(parents=True,exist_ok=True);micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text())
    need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged pinned native checker')
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));steps=0
    for q,rec in enumerate(records):
        r=requests[q];need(rec['request_sha256']==pin(r) and rec['query_target']=='fixed_assertion','entire native request identity')
        initial=initial_for(micro,boundary['cases'][0]['initial'],r);(TMP/'input.bin').write_bytes(input_bytes(initial));need(sha(TMP/'input.bin')==rec['input_sha256'],'independent full tagged words and parser frame')
        response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',rec['limit']))
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(response[k])==str(rec['result'][k]),'whole native replay '+k)
        need(rec['result']['start']==88986 and sha(TMP/'output.bin')==rec['output_sha256'],'true parser start and all output bands')
        try:logical=whole_replay(r)['status']
        except ValueError:logical='rejected'
        need(logical==response['status'],'independent logical replay audit only');steps+=response['micro_steps']
        if q%8==0:print('audit native',q,response['status'],flush=True)
    result.update(status='passed',native_micro_steps=steps,seconds=time.perf_counter()-began,scope='Complete finite equational occurrence/substitution catalog, injective scalar point inventory, every node and fallback, every native computation from true parser start. Primitive syntax catalog remains partly compiled and is not the searched grammar. No RL comparison or full Peano/Hilbert/unbounded completeness claim.')
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('AUDIT PASSED',result['seconds'],flush=True)

if __name__=='__main__':main()
