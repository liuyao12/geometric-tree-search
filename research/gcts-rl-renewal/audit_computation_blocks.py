"""Independent local tape-response composition and Wang row-law checks.

No import from computation_blocks, flat_computation or the artifact generator.
Composition uses cellwise symbolic substitution, rather than interval sweeps.
Frozen literal and Wang helpers are explicit implementation dependencies.
"""
import copy,hashlib,itertools,json,pathlib,time
import wang,proof_search,lazy_wang
import audit_binary_machine as old


def sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def unpack(runs):return {i:v for first,last,v in runs for i in range(first,last)}
def compact(values):
    out=[]
    for i in sorted(values):
        value=values[i]
        if out and out[-1][1]==i and out[-1][2]==value:out[-1][1]=i+1
        else:out.append([i,i+1,value])
    return out


def derive(d,node,earlier):
    symbols=d['alphabet']
    if set(node)=={'transition'}:
        i=node['transition']
        if type(i) is not int or not 0<=i<len(d['transitions']):raise ValueError('transition ID')
        q,s,next_q,write,delta=d['transitions'][i];a=symbols.index(s);w=symbols.index(write)
        return dict(q=q,out=next_q,shift=delta,steps=1,extent=[min(0,delta),max(0,delta)],pre=[[0,1,2**a]],writes=[] if a==w else [[0,1,w]])
    if set(node)=={'sweep'}:
        if len(node['sweep'])!=3:raise ValueError('sweep arity')
        q,delta,n=node['sweep']
        if type(n) is not int or n<1 or type(delta) is not int or delta not in (-1,1):raise ValueError('positive scan length')
        eligible={s for source,s,next_q,w,move in d['transitions'] if source==next_q==q and s==w and move==delta}
        if not eligible:raise ValueError('unproved sweep')
        mask=sum(2**symbols.index(s) for s in eligible)
        return dict(q=q,out=q,shift=n*delta,steps=n,extent=[min(0,n*delta),max(0,n*delta)],pre=[[min(0,(n-1)*delta),max(0,(n-1)*delta)+1,mask]],writes=[])
    if set(node)!={'children'} or len(node['children'])!=2 or any(type(i) is not int or not 0<=i<len(earlier) for i in node['children']):raise ValueError('descending children')
    a,b=[earlier[i] for i in node['children']]
    if a['out']!=b['q']:raise ValueError('state boundary')
    inputs=unpack(a['pre']);outputs=unpack(a['writes']);offset=a['shift']
    for relative,required in unpack(b['pre']).items():
        cell=offset+relative
        if cell in outputs:
            if not required//(2**outputs[cell])%2:raise ValueError('output violates next input')
        else:
            choices=required&inputs.get(cell,required)
            if not choices:raise ValueError('inconsistent input conditions')
            inputs[cell]=choices
    outputs.update({offset+x:v for x,v in unpack(b['writes']).items()})
    outputs={x:v for x,v in outputs.items() if inputs.get(x)!=2**v}
    return dict(q=a['q'],out=b['out'],shift=offset+b['shift'],steps=a['steps']+b['steps'],extent=[min(a['extent'][0],offset+b['extent'][0]),max(a['extent'][1],offset+b['extent'][1])],pre=compact(inputs),writes=compact(outputs))


def validate(d,proof,pinned):
    problem={k:proof[k] for k in ('machine_sha256','initial','steps','limit','final','status')}
    if type(proof['version']) is not int or proof['version']!=1 or sha(d)!=proof['machine_sha256'] or sha(problem)!=pinned or pinned!=proof['problem_sha256']:raise ValueError('external binding')
    if any(type(proof[x]) is not int or proof[x]<0 for x in ('steps','limit')) or proof['steps']>proof['limit']:raise ValueError('natural budget')
    earlier=[]
    for node in proof['nodes']:earlier.append(derive(d,node,earlier))
    row=old.freeze(proof['initial']);heads=[(i,s) for i,s in enumerate(row) if isinstance(s,tuple)]
    if len(heads)!=1:raise ValueError('one head')
    cursor,head=heads[0]
    if len(head)!=3 or head[0]!='head' or head[1] not in d['states']:raise ValueError('head tag/state')
    q,s=head[1:];values=list(row);values[cursor]=s
    if any(x not in d['alphabet'] for x in values) or values[0]!='B' or values[-1]!='B' or not 0<cursor<len(values)-1:raise ValueError('frame')
    root=proof['root']
    if root is None:
        if proof['steps'] or proof['tokens']:raise ValueError('empty proof')
    else:
        if type(root) is not int or not 0<=root<len(earlier):raise ValueError('root')
        response=earlier[root]
        if response['q']!=q or response['steps']!=proof['steps'] or cursor+response['extent'][0]<1 or cursor+response['extent'][1]>len(values)-2:raise ValueError('root interface/frame')
        for x,mask in unpack(response['pre']).items():
            if not mask//(2**d['alphabet'].index(values[cursor+x]))%2:raise ValueError('input constraint')
        for x,symbol in unpack(response['writes']).items():values[cursor+x]=d['alphabet'][symbol]
        cursor+=response['shift'];q=response['out']
    values[cursor]=wang.head(q,values[cursor])
    if tuple(values)!=old.freeze(proof['final']):raise ValueError('final interface')
    table={(q,s):(out,w,v) for q,s,out,w,v in d['transitions']};scanned=values[cursor][2]
    expected={'space-bound':'unknown_space_bound','workspace-bound':'unknown_workspace_bound'}.get(q,'accept' if q==d['halt'] else 'reject' if q=='reject' else 'unknown_step_budget' if proof['steps']==proof['limit'] else 'reject' if (q,scanned) not in table else 'unknown_frame_bound' if not 0<cursor+table[q,scanned][2]<len(values)-1 else None)
    if expected!=proof['status']:raise ValueError('status')
    traversal=[];work=[root] if root is not None else [];uses=[0]*len(earlier)
    while work:
        i=work.pop();uses[i]+=1
        if 'children' in proof['nodes'][i]:work+=list(reversed(proof['nodes'][i]['children']))
        else:traversal.append(i)
    if traversal!=proof['tokens']:raise ValueError('sequential proof differs')
    for o in proof['observations']:
        i=o['node']
        if type(i) is not int or not 0<=i<len(earlier) or o['interface']!=earlier[i] or o['uses']!=uses[i]:raise ValueError('observed interface')
    return dict(nodes=len(earlier),steps=proof['steps'],tokens=len(traversal),interface=earlier[root] if root is not None else None)


def wang_laws(d):
    started=time.perf_counter();compiler=old.previous.compiler_from_declaration(d);alphabet=d['alphabet'];triples=0;pairs=0
    for a,b,c in itertools.product(alphabet,repeat=3):
        if compiler.rule(a,b,c)!=b:raise AssertionError('headless frame law')
        triples+=1
    for q,s,out,w,move in d['transitions']:
        H=wang.head(q,s)
        for a,b in itertools.product(alphabet,repeat=2):
            expected=(wang.head(out,a),w,b) if move==-1 else (a,wang.head(out,w),b) if move==0 else (a,w,wang.head(out,b))
            actual=(compiler.rule('B',a,H),compiler.rule(a,H,b),compiler.rule(H,b,'B'))
            if actual!=expected:raise AssertionError('one-head radius-one law')
            pairs+=1
    # Accepting head is absorbing; outer bare symbols cannot affect a one-head neighborhood.
    for s,a,b in itertools.product(alphabet,repeat=3):
        H=wang.head(d['halt'],s)
        if compiler.rule(a,H,b)!=H or compiler.rule('B',a,H)!=a or compiler.rule(H,b,'B')!=b:raise AssertionError('accepting frame law')
    return dict(headless_triples=triples,transition_neighbor_pairs=pairs,accepting_neighbor_triples=len(alphabet)**3,seconds=time.perf_counter()-started)


def dense(d,proof):
    compiler=old.previous.compiler_from_declaration(d);row=old.freeze(proof['initial']);rows=[row];placements=[]
    for y in range(proof['steps']):
        after=wang.direct_step(compiler,row)
        for x,b in enumerate(row):
            a=row[x-1] if x else 'B';c=row[x+1] if x+1<len(row) else 'B';n=compiler.rule(a,b,c)
            if n!=after[x]:raise AssertionError('expanded local tile')
            placements.append((x,y,dict(S=b,N=n,W=(a,b),E=(b,c),triple=(a,b,c))))
        rows.append(after);row=after
    if row!=old.freeze(proof['final']):raise AssertionError('dense output')
    pattern=tuple((s,) for s in rows[0]);top=rows[-1]
    if not lazy_wang.independent_check(compiler,pattern,top,rows,placements,extended=False):raise AssertionError('dense point occupancy/markings')
    return len(placements)


def audit(path):
    started=time.perf_counter();path=pathlib.Path(path);data=json.loads(path.read_text());reuse=path.with_name(data['reused_artifact']['path'])
    if hashlib.sha256(reuse.read_bytes()).hexdigest()!=data['reused_artifact']['sha256']:raise AssertionError('artifact binding')
    old_data=json.loads(reuse.read_text());d=old_data['machine']
    if data['machine_sha256']!=sha(d):raise AssertionError('table binding')
    expected_sources=[i for i,c in enumerate(old_data['comparisons']) if c['lane']=='relative+next' and c['replica']==0]
    if sorted(c['case_index'] for c in data['cases'] if 'case_index' in c)!=list(range(len(old_data['cases']))) or sorted(c['source_index'] for c in data['cases'] if 'source_index' in c)!=expected_sources:raise AssertionError('complete reused control catalogs')
    addition_input=next(c['result']['initial'] for c in old_data['comparisons'] if c['name']=='unary-addition' and c['lane']=='relative+next' and c['replica']==0)
    prefixes=[c for c in data['cases'] if c.get('prefix_control')]
    if sorted(c['proof']['limit'] for c in prefixes)!=[0,100,5000] or any(old.freeze(c['proof']['initial'])!=old.freeze(addition_input) for c in prefixes):raise AssertionError('addition prefix bindings')
    seen=set();point_indices=[]
    for i,c in enumerate(old_data['wang_runs']):
        if c.get('verified') and c['problem'] not in seen:seen.add(c['problem']);point_indices.append(i)
    if sorted(c['point_index'] for c in data['cases'] if 'point_index' in c)!=point_indices:raise AssertionError('point controls')
    for name,h in data['sources'].items():
        if hashlib.sha256((pathlib.Path(__file__).parent/name).read_bytes()).hexdigest()!=h:raise AssertionError('source binding '+name)
    nodes=steps=tokens=literal=0
    for case in data['cases']:
        proof=case['proof'];expected=old_data['comparisons'][case['source_index']]['result'] if 'source_index' in case else old_data['cases'][case['case_index']]['result'] if 'case_index' in case else None
        if expected is not None:
            prior=old_data['comparisons'][case['source_index']] if 'source_index' in case else old_data['cases'][case['case_index']]
            if proof['limit']!=prior['tm_limit'] or case['name']!=prior['name']:raise AssertionError('external source name/limit')
            for k in ('initial','final','steps','status'):
                if old.freeze(proof[k])!=old.freeze(expected[k]):raise AssertionError('paired source '+k)
        if 'point_index' in case:
            prior=old_data['wang_runs'][case['point_index']];rows,_=proof_search.unpack(prior)
            if old.freeze(proof['initial'])!=rows[0] or old.freeze(proof['final'])!=rows[-1] or proof['steps']!=len(rows)-1:raise AssertionError('point source binding')
        result=validate(d,proof,proof['problem_sha256']);nodes+=result['nodes'];steps+=result['steps'];tokens+=result['tokens']
        replay=old.literal(d,proof['initial'],proof['limit'])
        for k in ('steps','status','final'):
            if old.freeze(replay[k])!=old.freeze(proof[k]):raise AssertionError('independent literal '+k)
        literal+=1
    point_cells=sum(dense(d,c['proof']) for c in data['cases'] if 'point_index' in c)
    laws=wang_laws(d)
    base=next(c['proof'] for c in data['cases'] if c.get('name')=='unary-addition');bad=[]
    def mutation(change):
        p=copy.deepcopy(base);change(p);bad.append(p)
    mutation(lambda p:p['nodes'][p['root']]['children'].__setitem__(0,p['root']))
    mutation(lambda p:p['observations'][0]['interface'].__setitem__('shift',1))
    mutation(lambda p:p['initial'].__setitem__(3,'R'))
    mutation(lambda p:p['final'].__setitem__(3,'1'))
    mutation(lambda p:p['tokens'].__setitem__(0,p['tokens'][-1]))
    mutation(lambda p:p.__setitem__('steps',p['steps']-1))
    mutation(lambda p:p.__setitem__('machine_sha256','0'*64))
    primitive=next(i for i,n in enumerate(base['nodes']) if 'transition' in n)
    mutation(lambda p:p['nodes'][primitive].__setitem__('transition',True))
    scan=next(i for i,n in enumerate(base['nodes']) if 'sweep' in n)
    mutation(lambda p:p['nodes'][scan]['sweep'].__setitem__(2,0))
    # An unused declaration is also checked.
    mutation(lambda p:p['nodes'].append({'children':[len(p['nodes']),0]}))
    for p in bad:
        try:validate(d,p,base['problem_sha256'])
        except (ValueError,IndexError,KeyError):pass
        else:raise AssertionError('altered proof accepted')
    result=dict(status='passed',cases=len(data['cases']),nodes=nodes,represented_steps=steps,flat_tokens=tokens,literal_replays=literal,point_cells=point_cells,wang_laws=laws,tampered_certificates_rejected=len(bad),seconds=time.perf_counter()-started,audit_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest())
    data['independent_audit']=result;path.write_text(json.dumps(data,separators=(',',':'))+'\n');return result

if __name__=='__main__':
    import sys
    print(json.dumps(audit(sys.argv[1] if len(sys.argv)>1 else 'docs/research/gcts-rl-renewal/computation-blocks-001.json'),indent=2))
