"""Independent finite tile, rule inventory, search-tree and proof replay.

No model, graph, catalog generator, proposer or producer imports. Rule validity
uses the frozen logic kernel. Serialized proofs are expanded by a separately
written expander; audit-only tautology/MP suffixes force full-prefix validation
even when the original last command aliases an earlier assumption.
"""
import copy,hashlib,itertools,json,time
from pathlib import Path
import logic as L
from audit_serialized_kernel import replay,freeze
from audit_proof_compaction import native_binding

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def packed(a):return json.dumps(a,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def need(test,message):
    if not test:raise ValueError(message)
def pin(d):return hashlib.sha256(packed({k:d[k] for k in ('protocol','theory','target')})).hexdigest()
def whole_replay(d,expected_pin=None):
    value=copy.deepcopy(d)
    def close(lines,a):
        need(lines and lines[-1]['formula']==a,'declared last formula')
        n=len(lines);lines.extend([dict(rule='tautology',formula=['imp',a,a]),dict(rule='mp',formula=a,antecedent=n-1,implication=n)])
    for b in value['blocks']:close(b['proof'],b['conclusion'])
    close(value['proof'],value['target'])
    return replay(packed(value),expected_pin)
def term_size(t):return 1+sum(map(term_size,t[2])) if t[0]=='fun' else 1
def bounded_terms(functions,variables,bound):
    values={( 'var',x) for x in variables}|{('fun',f,()) for f,n in functions.items() if n==0}
    # Alternative enumeration: size layers from all smaller available terms,
    # filtering full argument products, rather than integer partitions.
    for n in range(2,bound+1):
        smaller=tuple(values);new=set()
        for f,arity in functions.items():
            if arity:
                for args in itertools.product(smaller,repeat=arity):
                    if 1+sum(map(term_size,args))==n:new.add(('fun',f,args))
        values.update(new)
    return values
def locations(t,path=()):
    yield path,t
    if t[0]=='fun':
        for i,u in enumerate(t[2]):yield from locations(u,path+(i,))
def put(t,path,r):
    if not path:return r
    args=list(t[2]);args[path[0]]=put(args[path[0]],path[1:],r);return ('fun',t[1],tuple(args))
def substitute_term(t,env):
    return env.get(t[1],t) if t[0]=='var' else ('fun',t[1],tuple(substitute_term(a,env) for a in t[2]))
def equation_inventory(c):
    conf=c['configuration'];original=c['formulas'][0][1];ts=bounded_terms(c['theory']['functions'],c['close_variables'],conf['term_bound']);need({a[2] for a in c['formulas']}==ts and all(a[0]=='eq' and a[1]==original for a in c['formulas']),'complete bounded equational language')
    grounded={}
    for name,a in c['theory']['axioms'].items():
        variables=[]
        while a[0]=='all':variables.append(a[1]);a=a[2]
        if a[0]!='eq':continue
        for terms in itertools.product(ts,repeat=len(variables)):
            env=dict(zip(variables,terms));left,right=[substitute_term(t,env) for t in a[1:]]
            for sign,l,r in ((1,left,right),(-1,right,left)):
                if l in ts:grounded.setdefault(l,[]).append((r,name,tuple(sorted(env.items())),sign))
    expected=set()
    for before in ts:
        for path,sub in locations(before):
            for other,name,bindings,sign in grounded.get(sub,()):
                after=put(before,path,other)
                if after!=before and after in ts:expected.add((before,after,name,bindings,path,sign))
    actual=[];defs=[]
    for rule in c['rules']:
        recipe=rule['recipe']
        if recipe['kind']=='block':
            move=recipe['move'];a,b=move['before'],move['after'];need(rule['inputs']==(c['formulas'].index(L.Eq(original,a)),) and c['formulas'][rule['output']]==L.Eq(original,b),'rewrite formula interface')
            actual.append((a,b,recipe['axiom'],tuple(sorted(move['bindings'].items())),move['path'],move['direction']));defs.append(recipe['definition'])
            need(recipe['definition']['premises']==(L.Eq(original,a),) and recipe['definition']['conclusion']==L.Eq(original,b),'block interface')
        elif recipe['kind']=='primitive':
            need(not rule['inputs'] and recipe['witness']==dict(rule='refl',formula=L.Eq(original,original)),'equational reflection seed')
    need(set(actual)==expected and len(actual)==len(expected),'complete contextual rule inventory, including variable-erasing reversals')
    need(len(defs)==conf['derived_rules'],'derived rule count')
    # Check every declared type, even those never used by a search solution.
    d=json.loads(packed(dict(protocol='gcts-fol-1',theory=c['theory'],target=L.Imp(c['target'],c['target']),blocks=defs,proof=[dict(rule='tautology',formula=L.Imp(c['target'],c['target']))])))
    checked=whole_replay(d,pin(d));need(checked['status']=='accepted','every compiled rewrite independently expanded: '+checked.get('reason',''))
    return dict(terms=len(ts),contextual_edges=len(expected),validated_definitions=len(defs))
def primitive_inventory(c):
    fs=c['formulas'];index={a:i for i,a in enumerate(fs)};conf=c['configuration'];k=L.Kernel(c['theory']['functions'],c['theory']['predicates'],c['theory']['axioms']);expected=set()
    def add(kind,inputs,a):
        if a in index and all(p in index for p in inputs):expected.add((kind,tuple(index[p] for p in inputs),index[a]))
    for a in c['theory']['axioms'].values():add('axiom',(),a)
    for a in fs:
        if L.tautology(a):add('tautology',(),a)
        if a[0]=='eq' and a[1]==a[2]:add('refl',(),a)
        if a[0]=='imp':add('mp',(a[1],a),a[2])
        for x in conf['variables']:add('generalize',(a,),L.All(x,a))
        if a[0]=='all':
            for t in conf['terms']:add('instantiate',(),L.Imp(a,L.substitute(a[2],a[1],t)))
            x,b=a[1:]
            if b[0]=='imp' and x not in L.free(b[1]):add('distribute',(),L.Imp(a,L.Imp(b[1],L.All(x,b[2]))))
        if a[0]=='eq':
            for x in conf['variables']:
                for t in conf['templates']:add('eq_subst',(),L.Imp(a,L.Imp(L.substitute(t,x,a[1]),L.substitute(t,x,a[2]))))
    actual=[]
    for r in c['rules']:
        if r['recipe']['kind']=='copy':continue
        need(r['recipe']['kind']=='primitive','only primitive FOL rules');w=r['recipe']['witness'];a=fs[r['output']];inputs=tuple(fs[i] for i in r['inputs']);kind=w['rule']
        need(w['formula']==a,'primitive output')
        if kind=='mp':need(len(inputs)==2 and inputs[1]==L.Imp(inputs[0],a),'MP port validity')
        elif kind=='generalize':need(len(inputs)==1 and a==L.All(w['variable'],inputs[0]),'generalization port validity')
        else:need(not inputs and k.check([w],a),'primitive schema validity')
        actual.append((kind,r['inputs'],r['output']))
    need(set(actual)==expected,'complete primitive inventory inside the declared syntax envelope')
    return dict(formulas=len(fs),primitive_instances=len(actual),distinct_relations=len(expected))
def candidates(c,n):
    universe={}
    for slot in range(n):
        for r,rule in enumerate(c['rules']):
            for refs in itertools.product(range(slot),repeat=len(rule['inputs'])):
                marks={slot:rule['output']};okay=True
                for ref,value in zip(refs,rule['inputs']):
                    if ref in marks and marks[ref]!=value:okay=False;break
                    marks[ref]=value
                if okay:universe[(slot,r,refs)]=marks
    return universe
def domains(universe,n,target,order):
    marks={n-1:target};filled=set()
    for key in order:
        need(key in universe and key[0] not in filled,'candidate identity / exact occupancy')
        filled.add(key[0])
        for p,v in universe[key].items():need(p not in marks or marks[p]==v,'exact scalar marking agreement');marks[p]=v
    result={i:set() for i in range(n) if i not in filled}
    for key,m in universe.items():
        if key[0] in result and all(p not in marks or marks[p]==v for p,v in m.items()):result[key[0]].add(key)
    return result
def decision(ds):
    dead=sorted(i for i,v in ds.items() if not v)
    if dead:return 'dead',dead[0],[]
    forced=sorted(i for i,v in ds.items() if len(v)==1)
    if forced:return 'forced',forced[0],sorted(ds[forced[0]])
    if not ds:return 'empty',None,[]
    i=min(ds,key=lambda j:(len(ds[j]),j));return 'branch',i,sorted(ds[i])
def audit_point_run(c,n,r):
    universe=candidates(c,n);target=c['target_id'];need(len(universe)==r['candidate_universe'],'complete finite candidate count')
    for sample in r['samples']:
        ds=domains(universe,n,target,sample['order']);kind,slot,keys=decision(ds)
        expected_point=(2*slot,0) if slot is not None else None
        need(sample['kind']==kind and sample['point']==expected_point,'global decision sample')
        need(sample['degrees']=={str((2*i,0)):len(v) for i,v in ds.items()},'all frontier domains independently enumerated')
    ds=domains(universe,n,target,r['placements']);solved=r['status']=='finite_exact_proof_tiling';need(not solved or not ds,'all proof cells exactly covered')
    need(r['tile_generations']==(1,)*len(r['placements']),'declared generation-zero roots and tile generations')
    stats=dict(nodes=0,branches=0,forced=0,backtracks=0,attempts=0);leaf=None
    def visit(tree,order):
        nonlocal leaf
        stats['nodes']+=1;ds=domains(universe,n,target,order);kind,slot,keys=decision(ds)
        need(tree['kind']==kind,'full tree decision')
        if slot is not None:need(tree['point']==(2*slot,0),'full tree chosen point')
        if kind=='dead':return False
        if kind=='empty':leaf=order;return True
        stats['forced' if kind=='forced' else 'branches']+=1;children=tree['children']
        need(tuple(child['key'] for child in children)==tuple(keys[:len(children)]),'actual branch-order prefix')
        for j,child in enumerate(children):
            stats['attempts']+=1
            if visit(child['tree'],order+[child['key']]):need(j==len(children)-1,'search stops on first solution');return True
            stats['backtracks']+=1
        need(len(children)==len(keys),'every exhausted branch child covered');return False
    if r['search_tree'] is not None:
        okay=visit(r['search_tree'],[]);need(okay==solved,'tree outcome');need(all(r[k]==v for k,v in stats.items()),'search tree work counters')
        if solved:need(tuple(leaf)==r['placements'],'actual geometric solution path')
    else:need(r['status']=='unknown_search_budget','only budget cutoff omits tree')
    return dict(candidate_types=len(universe),full_tree_nodes=stats['nodes'],domain_samples=len(r['samples']),exact_solution=solved)
def check_decoded(c,n,r):
    keys=r['placements'];by_slot={key[0]:key for key in keys};need(len(keys)==n and set(by_slot)==set(range(n)),'complete logical certificate')
    commands=r['decoded']['commands'];request=r['decoded']['request'];lines=request['proof'];last=[];used={};cursor=0
    for slot in range(n):
        _,rule_id,refs=by_slot[slot];rule=c['rules'][rule_id];need(len(refs)==len(rule['inputs']) and all(0<=i<slot for i in refs),'earlier premise references');need(tuple(c['rules'][by_slot[i][1]]['output'] for i in refs)==rule['inputs'],'all distant logical ports')
        a=c['formulas'][rule['output']];mapped=[last[i] for i in refs];recipe=rule['recipe']
        if recipe['kind']=='primitive':
            expected=dict(recipe['witness'])
            if expected['rule']=='mp':expected.update(antecedent=mapped[0],implication=mapped[1])
            if expected['rule']=='generalize':expected['source']=mapped[0]
            chunk=[expected]
        elif recipe['kind']=='copy':chunk=[dict(rule='tautology',formula=L.Imp(a,a)),dict(rule='mp',formula=a,antecedent=mapped[0],implication=cursor)]
        else:
            b=recipe['definition'];used[b['name']]=b;chunk=[dict(rule='block',formula=a,name=b['name'],inputs=tuple(mapped))]
        need(freeze(lines[cursor:cursor+len(chunk)])==freeze(chunk),'independent exact decoded command sequence');cursor+=len(chunk);last.append(cursor-1)
        need(commands[slot]==dict(slot=slot,rule=rule_id,refs=refs,final_line=cursor-1),'slot to primitive/block line map')
    need(c['rules'][by_slot[n-1][1]]['output']==c['target_id'],'fixed final formula')
    a=lines[last[-1]]['formula']
    for x in reversed(c['close_variables']):
        a=L.All(x,a);need(lines[cursor]==dict(rule='generalize',formula=a,variable=x,source=cursor-1),'universal target closure');cursor+=1
    need(cursor==len(lines) and tuple(used[k] for k in sorted(used))==request['blocks'],'all and only decoded used blocks')
    need(request['theory']==c['theory'] and request['target']==c['target'],'external theory/target preserved')
    raw=json.loads(packed(request));checked=whole_replay(raw,pin(raw));need(checked['status']=='accepted','full-prefix independent proof acceptance: '+checked.get('reason',''))
    ordinary=replay(packed(request),pin(raw));need(ordinary['status']=='accepted','primitive expansion')
    return dict(proof_cells=n,root_lines=len(lines),expanded_lines=ordinary['expanded_lines'],blocks=len(used),nonchronological=tuple(k[0] for k in keys)!=tuple(range(n)))
def external_problems():
    # Independent authored statement reconstruction. No stored proof or
    # producer's problem generator is read.
    def th(f={},p={},a={}):return dict(functions=f,predicates=p,axioms=a,schemas=[])
    p,q,r,t=[('pred',name,()) for name in 'PQRT'];preds=dict(P=0,Q=0,R=0,T=0);chain=th(p=preds,a=dict(given=p,pq=L.Imp(p,q),qr=L.Imp(q,r)));out={}
    def add(id,theory,target,n,kind='fol',**config):out[id]=dict(theory=theory,target=target,length=n,kind=kind,configuration=config)
    add('chain-2',chain,r,5);add('chain-too-short',chain,r,4);add('join',th(p=preds,a=dict(p=p,q=q,join=L.Imp(p,L.Imp(q,r)))),r,5);add('absent-fact',th(p=preds,a=dict(p=p)),t,3);add('generalization',th(dict(c=0)),L.All('x',L.Eq(L.V('x'),L.V('x'))),2)
    c,d=L.F('c'),L.F('d');f=lambda a:L.F('f',a);x,y=L.V('x'),L.V('y')
    add('instantiation',th(dict(c=0,f=1),dict(P=1),dict(universal=L.All('x',('pred','P',(x,))))),('pred','P',(f(c),)),3,rounds=1)
    add('congruence',th(dict(c=0,d=0,f=1),a=dict(equal=L.Eq(c,d))),L.Eq(f(c),f(d)),5,rounds=1)
    z=L.F('zero');s=lambda a:L.F('succ',a);plus=lambda a,b:L.F('add',a,b)
    addition=th(dict(zero=0,succ=1,add=2),a=dict(AZ=L.All('x',L.Eq(plus(x,z),x)),AS=L.All('x',L.All('y',L.Eq(plus(x,s(y)),s(plus(x,y)))))))
    def num(n):return z if n==0 else s(num(n-1))
    for a,b in ((1,1),(2,1),(1,2),(2,2)):add(f'add-{a}-{b}',addition,L.Eq(plus(num(a),num(b)),num(a+b)),b+2,'equational',term_bound=a+b+3)
    a=L.V('a');add('add-one-universal',addition,L.All('a',L.Eq(plus(a,s(z)),s(a))),3,'equational',term_bound=5)
    arithmetic=copy.deepcopy(addition);arithmetic['functions']['mul']=2;m=lambda a,b:L.F('mul',a,b);arithmetic['axioms'].update(MZ=L.All('x',L.Eq(m(x,z),z)),MS=L.All('x',L.All('y',L.Eq(m(x,s(y)),plus(m(x,y),x)))))
    add('mul-one',arithmetic,L.Eq(m(s(z),s(z)),s(z)),5,'equational',term_bound=7);return out
def audit(path=DOCS/'semantic-proofs-001.json'):
    began=time.perf_counter();path=Path(path);data=json.loads(path.read_text());external=external_problems();need(set(external)=={r['problem']['id'] for r in data['cases']},'external case set');results=[];code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program']
    for name,h in data['sources'].items():need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h,'source pin '+name)
    for i,row in enumerate(data['cases']):
        p=freeze(row['problem']);e=external[p['id']];need(all(p[k]==freeze(v) for k,v in e.items()),'independent problem declaration');c=freeze(row['catalog']);need(c['theory']==p['theory'] and c['target']==p['target'],'catalog external theory/target');need(hashlib.sha256(packed(row['catalog'])).hexdigest()==row['catalog_sha256'],'catalog declaration hash')
        need(row['order']==(['gcts','symbolic'] if i%2==0 else ['symbolic','gcts']) and [r['lane'] for r in row['runs']]==row['order'],'counterbalanced lane order')
        target=c['target'];variables=[]
        if p['kind']=='equational':
            while target[0]=='all':variables.append(target[1]);target=target[2]
        need(tuple(variables)==c['close_variables'] and c['formulas'][c['target_id']]==target,'fixed target port and closure')
        copies=[r for r in c['rules'] if r['recipe']['kind']=='copy'];need(len(copies)==len(c['formulas']) and {(r['inputs'],r['output']) for r in copies}=={((i,),i) for i in range(len(c['formulas']))},'all formula copy rules')
        if p['kind']=='equational':need(c['configuration']['term_bound']==p['configuration']['term_bound'],'external term bound')
        else:need(c['configuration']['rounds']==p['configuration'].get('rounds',2) and c['configuration']['max_formula_nodes']==80,'external specialized FOL closure bounds')
        inventory=equation_inventory(c) if p['kind']=='equational' else primitive_inventory(c);runs=[]
        for rawrun in row['runs']:
            run=freeze(rawrun);r=run['result'];need(run['catalog_sha256']==row['catalog_sha256'],'same cold rebuilt catalog');a=dict(lane=run['lane'])
            if run['lane']=='gcts':a['points']=audit_point_run(c,p['length'],r)
            if 'decoded' in r:
                a['derivation']=check_decoded(c,p['length'],r);native_binding(code,rawrun['result']['decoded']['request'],rawrun['native']);a['native_status']=run['native']['status']
            else:need(r['status'] in ('exhausted_finite_proof_envelope','unknown_search_budget'),'bounded outcome vocabulary')
            runs.append(a)
        results.append(dict(id=p['id'],inventory=inventory,runs=runs))
    result=dict(status='passed',cases=results,seconds=time.perf_counter()-began,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),dependencies={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('logic.py','audit_serialized_kernel.py','audit_proof_compaction.py','audit_tree_kernel.py')},scope='Independently enumerated tile types and all sampled domains; every complete GCTS search tree replayed, including full finite failures; whole compiled arithmetic inventories and all decoded proofs expanded with full-prefix checks; native program/input bindings checked, not independent replay of every native instruction. Symbolic controls share the declared grammar; their abandoned search prefixes are not exported.')
    data['independent_audit']=result;path.write_text(json.dumps(data,separators=(',',':'))+'\n');return result
if __name__=='__main__':
    print(json.dumps(audit(),indent=2))
