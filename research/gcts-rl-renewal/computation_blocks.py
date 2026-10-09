"""Symbolic tape-response proofs with descending, reusable composition.

This is a certificate format, not a changed Wang search engine. Primitive
leaves bind a literal transition; sweep leaves prove repeated copy transitions.
Every interface is derived, including unused nodes. Outside read/write support
is an unchanged headless frame. No supplied interface is trusted.
"""
import hashlib,json,time


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def machine_data(declaration):
    alphabet=declaration['alphabet']; states=declaration['states']; transitions=declaration['transitions']
    if not alphabet or len(set(alphabet))!=len(alphabet) or not states or len(set(states))!=len(states): raise ValueError('distinct finite symbols/states required')
    if any(type(s) is not str for s in alphabet+states) or declaration['halt'] not in states: raise ValueError('invalid alphabet/state')
    lookup={}; sweeps={}
    for i,record in enumerate(transitions):
        if len(record)!=5: raise ValueError('transition arity')
        q,a,out,w,d=record
        if q not in states or out not in states or a not in alphabet or w not in alphabet or type(d) is not int or d not in (-1,0,1) or (q,a) in lookup or q==declaration['halt']: raise ValueError('literal table')
        lookup[q,a]=i
        if q==out and a==w and d: sweeps[q,d]=sweeps.get((q,d),0)|(1<<alphabet.index(a))
    return lookup,sweeps


def ranges(values):
    """Lossless canonical half-open runs; missing means no constraint/write."""
    result=[]
    for x,v in sorted(values.items()):
        if result and result[-1][1]==x and result[-1][2]==v: result[-1][1]+=1
        else: result.append([x,x+1,v])
    return result


def expand(runs):
    return {x:v for lo,hi,v in runs for x in range(lo,hi)}


def interface(q,out,shift,steps,pre,writes,extent):
    writes={x:v for x,v in writes.items() if pre.get(x)!=(1<<v)}
    return dict(q=q,out=out,shift=shift,steps=steps,pre=ranges(pre),writes=ranges(writes),extent=list(extent))


def append_run(runs,lo,hi,value):
    if value is None:return
    if runs and runs[-1][1]==lo and runs[-1][2]==value:runs[-1][1]=hi
    else:runs.append([lo,hi,value])


def leaf(d,node,sweeps):
    alphabet=d['alphabet']
    if set(node)=={'transition'}:
        i=node['transition']
        if type(i) is not int or not 0<=i<len(d['transitions']):raise ValueError('transition identifier')
        q,a,out,w,move=d['transitions'][i];ai=alphabet.index(a);wi=alphabet.index(w)
        return dict(q=q,out=out,shift=move,steps=1,pre=[[0,1,1<<ai]],writes=[] if ai==wi else [[0,1,wi]],extent=[min(0,move),max(0,move)])
    if set(node)=={'sweep'}:
        if type(node['sweep']) not in (list,tuple) or len(node['sweep'])!=3:raise ValueError('sweep arity')
        q,move,n=node['sweep']
        if q not in d['states'] or type(move) is not int or move not in (-1,1) or type(n) is not int or n<1 or (q,move) not in sweeps:raise ValueError('sweep instruction')
        return dict(q=q,out=q,shift=move*n,steps=n,pre=[[0,n,sweeps[q,move]]] if move==1 else [[1-n,1,sweeps[q,move]]],writes=[],extent=[min(0,move*n),max(0,move*n)])
    raise ValueError('unknown leaf')


def compose(a,b):
    if a['out']!=b['q']:raise ValueError('state interface mismatch')
    shift=a['shift'];tables=[a['pre'],a['writes'],[[l+shift,h+shift,v] for l,h,v in b['pre']],[[l+shift,h+shift,v] for l,h,v in b['writes']]]
    cuts=sorted({x for table in tables for l,h,v in table for x in (l,h)});pointers=[0]*4;pre=[];writes=[]
    for lo,hi in zip(cuts,cuts[1:]):
        values=[]
        for j,table in enumerate(tables):
            while pointers[j]<len(table) and table[pointers[j]][1]<=lo:pointers[j]+=1
            i=pointers[j];values.append(table[i][2] if i<len(table) and table[i][0]<=lo else None)
        ap,aw,bp,bw=values;mask=ap
        if bp is not None:
            if aw is not None:
                if not bp&(1<<aw):raise ValueError('written symbol violates child input')
            else:
                mask=bp if ap is None else ap&bp
                if not mask:raise ValueError('incompatible child inputs')
        write=bw if bw is not None else aw
        if write is not None and mask==(1<<write):write=None
        append_run(pre,lo,hi,mask);append_run(writes,lo,hi,write)
    return dict(q=a['q'],out=b['out'],shift=shift+b['shift'],steps=a['steps']+b['steps'],pre=pre,writes=writes,extent=[min(a['extent'][0],shift+b['extent'][0]),max(a['extent'][1],shift+b['extent'][1])])


def certify(d,initial,limit=20000000):
    if type(limit) is not int or limit<0: raise ValueError('natural limit')
    started=time.perf_counter(); lookup,sweeps=machine_data(d);alphabet=d['alphabet'];symbol_index={s:i for i,s in enumerate(alphabet)}
    heads=[(i,s) for i,s in enumerate(initial) if isinstance(s,(tuple,list))]
    if len(heads)!=1: raise ValueError('one head')
    h,head=heads[0]
    if len(head)!=3 or head[0]!='head':raise ValueError('head tag')
    _,q,a=head;tape=list(initial);tape[h]=a
    if any(s not in alphabet for s in tape) or q not in d['states'] or tape[0]!='B' or tape[-1]!='B' or not 0<h<len(tape)-1: raise ValueError('bounded blank frame')
    nodes=[];interfaces=[];intern={};stack=[];tokens=[];step=0
    def add(node):
        key=json.dumps(node,sort_keys=True,separators=(',',':'))
        if key in intern:return intern[key]
        if 'children' in node:
            x,y=node['children'];value=compose(interfaces[x],interfaces[y])
        else:value=leaf(d,node,sweeps)
        index=len(nodes);intern[key]=index;nodes.append(dict(node,interface=value));interfaces.append(value);return index
    def emit(node):
        index=add(node);tokens.append(index);level=0
        while stack and stack[-1][0]==level:
            _,other=stack.pop();index=add({'children':[other,index]});level+=1
        stack.append((level,index))
    while step<limit and q not in (d['halt'],'reject','space-bound','workspace-bound'):
        if (q,tape[h]) not in lookup:break
        i=lookup[q,tape[h]];_,_,out,w,move=d['transitions'][i]
        if q==out and w==tape[h] and move:
            mask=sweeps[q,move];n=0
            while step+n<limit and 0<h+move*(n+1)<len(tape)-1 and mask&(1<<symbol_index[tape[h+move*n]]):n+=1
            if n:
                emit({'sweep':[q,move,n]});step+=n;h+=move*n;continue
        if not 0<h+move<len(tape)-1:break
        emit({'transition':i});tape[h]=w;h+=move;q=out;step+=1
    root=None
    for _,index in stack:
        root=index if root is None else add({'children':[root,index]})
    final=tape.copy();final[h]=('head',q,tape[h])
    status={'space-bound':'unknown_space_bound','workspace-bound':'unknown_workspace_bound'}.get(q,'accept' if q==d['halt'] else 'reject' if q=='reject' else 'unknown_step_budget' if step==limit else 'reject' if (q,tape[h]) not in lookup else 'unknown_frame_bound')
    uses=[0]*len(nodes)
    if root is not None:uses[root]=1
    for i in range(len(nodes)-1,-1,-1):
        for j in nodes[i].get('children',[]):uses[j]+=uses[i]
    selected=([root] if root is not None else [])+sorted((i for i,n in enumerate(nodes) if 'children' in n),key=lambda i:uses[i],reverse=True)[:8]
    observations=[dict(node=i,uses=uses[i],interface=interfaces[i]) for i in dict.fromkeys(selected)]
    for node in nodes:del node['interface']
    proof=dict(version=1,machine_sha256=digest(d),initial=list(initial),final=final,status=status,steps=step,limit=limit,nodes=nodes,root=root,tokens=tokens,observations=observations)
    proof['problem_sha256']=digest(dict(machine_sha256=proof['machine_sha256'],initial=proof['initial'],steps=step,limit=limit,final=proof['final'],status=status))
    proof['build_seconds']=time.perf_counter()-started
    return proof


def check(d,proof,expected_problem=None,max_nodes=1000000,max_cells=100000000,max_tokens=1000000):
    started=time.perf_counter();lookup,sweeps=machine_data(d)
    if any(type(proof[x]) is not int or proof[x]<0 for x in ('steps','limit')) or proof['steps']>proof['limit']:raise ValueError('natural steps/limit')
    if type(proof['version']) is not int or proof['version']!=1 or proof['machine_sha256']!=digest(d):raise ValueError('machine/version binding')
    problem=digest({k:proof[k] for k in ('machine_sha256','initial','steps','limit','final','status')})
    if problem!=proof['problem_sha256'] or (expected_problem is not None and problem!=expected_problem):raise ValueError('problem binding')
    if len(proof['nodes'])>max_nodes or len(proof['tokens'])>max_tokens:return dict(status='unknown_certificate_budget')
    derived=[];cells=0;counts=[]
    for i,node in enumerate(proof['nodes']):
        desc=node
        if set(desc)=={'children'}:
            ids=desc['children']
            if len(ids)!=2 or any(type(j) is not int or not 0<=j<i for j in ids):raise ValueError('descending child references')
            value=compose(*(derived[j] for j in ids));count=sum(counts[j] for j in ids)
        else:
            if 'sweep' in desc and (type(desc['sweep'][2]) is not int or desc['sweep'][2]>max_cells):return dict(status='unknown_certificate_budget')
            value=leaf(d,desc,sweeps);count=1
        cells+=sum(hi-lo for lo,hi,v in value['pre'])
        if cells>max_cells:return dict(status='unknown_certificate_budget')
        derived.append(value);counts.append(count)
    heads=[(i,s) for i,s in enumerate(proof['initial']) if isinstance(s,(tuple,list))]
    if len(heads)!=1:raise ValueError('one initial head')
    h,head=heads[0]
    if len(head)!=3 or head[0]!='head' or head[1] not in d['states']:raise ValueError('head tag/state')
    _,q,a=head;tape=list(proof['initial']);tape[h]=a; alphabet=d['alphabet']
    if any(s not in alphabet for s in tape) or tape[0]!='B' or tape[-1]!='B' or not 0<h<len(tape)-1:raise ValueError('input frame')
    root=proof['root']
    if root is None:
        if proof['steps']!=0 or proof['tokens']:raise ValueError('empty proof')
    else:
        if type(root) is not int or not 0<=root<len(derived):raise ValueError('root identifier')
        response=derived[root]
        if response['q']!=q or response['steps']!=proof['steps'] or h+response['extent'][0]<1 or h+response['extent'][1]>=len(tape)-1:raise ValueError('root frame/state/length')
        for x,mask in expand(response['pre']).items():
            if not mask&(1<<alphabet.index(tape[h+x])):raise ValueError('input precondition')
        for x,v in expand(response['writes']).items():tape[h+x]=alphabet[v]
        h+=response['shift'];q=response['out']
    final=tape.copy();final[h]=('head',q,tape[h])
    if json.dumps(final)!=json.dumps(proof['final']):raise ValueError('output boundary')
    terminal={'space-bound':'unknown_space_bound','workspace-bound':'unknown_workspace_bound'}.get(q,'accept' if q==d['halt'] else 'reject' if q=='reject' else None)
    if terminal is not None:
        if proof['status']!=terminal:raise ValueError('terminal status')
    elif proof['status']=='unknown_step_budget':
        if proof['steps']!=proof['limit']:raise ValueError('unreached step limit')
    elif proof['status']=='reject':
        if (q,tape[h]) in lookup or proof['steps']==proof['limit']:raise ValueError('unjustified rejection')
    elif proof['status']=='unknown_frame_bound':
        if (q,tape[h]) not in lookup or proof['steps']==proof['limit']:raise ValueError('unreached tape bound')
        move=d['transitions'][lookup[q,tape[h]]][4]
        if 0<h+move<len(tape)-1:raise ValueError('unreached tape bound')
    else:raise ValueError('nonterminal status')
    # A second sequential representation must describe exactly the same root.
    if root is not None and counts[root]!=len(proof['tokens']):raise ValueError('changed token count')
    ids=[];pending=[root] if root is not None else []
    while pending:
        i=pending.pop();node=proof['nodes'][i]
        if 'children' in node:pending.extend(reversed(node['children']))
        else:ids.append(i)
    if ids!=proof['tokens']:raise ValueError('changed sequential serialization')
    uses=[0]*len(derived)
    if root is not None:uses[root]=1
    for i in range(len(derived)-1,-1,-1):
        for j in proof['nodes'][i].get('children',[]):uses[j]+=uses[i]
    for observation in proof['observations']:
        i=observation['node']
        if type(i) is not int or not 0<=i<len(derived) or observation['uses']!=uses[i] or observation['interface']!=derived[i]:raise ValueError('forged observed interface')
    return dict(status='checked_computation_response',result=proof['status'],nodes=len(derived),interface_cells=cells,steps=proof['steps'],seconds=time.perf_counter()-started)
