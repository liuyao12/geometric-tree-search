"""Independent relative operand semantics and literal/point replay.

Does not import the compact encoder, machine, generator or instruction VM.
Reuses frozen sparse-source and Wang helpers, with explicit source hashes.
"""
import copy,hashlib,itertools,json,pathlib,time
import wang,lazy_wang,proof_search
import audit_uniform_machine as previous

OPS={'a':('L',0),'b':('L',1),'c':('R',0),'d':('R',1),'e':('L',None),'f':('R',None)}
NAMES={'pushL0':'a','pushL1':'b','pushR0':'c','pushR1':'d','popL':'e','popR':'f','jump':'g','accept':'H','reject':'R'}
freeze=previous.freeze

def program(code):
    if type(code) is not str or not code or not code.endswith(';'): raise ValueError('terminated program')
    instructions=[]; offsets={}; position=3
    for index,record in enumerate(code.split(';')[:-1]):
        offsets[position]=index; position+=len(record)+1
        if not record or record[0] not in 'abcdefgHR': raise ValueError('opcode')
        op=record[0]; arity=0 if op in 'HR' else 3 if op in 'ef' else 1
        parts=record[1:].split(',') if arity else ()
        if len(parts)!=arity or (not arity and len(record)!=1): raise ValueError('arity')
        targets=[]
        for operand in parts:
            if operand=='n': targets.append(index+1); continue
            if len(operand)<2 or operand[0] not in '<>' or any(x not in '01' for x in operand[1:]): raise ValueError('address')
            if (len(operand)>2 and operand[1]=='0') or operand=='<0': raise ValueError('noncanonical address')
            value=0
            for bit in operand[1:]: value=2*value+(bit=='1')
            targets.append(index+value if operand[0]=='>' else index-value)
        instructions.append((op,)+tuple(targets))
    return tuple(instructions),offsets

def stack_reference(code,left,right,capacities,limit=10000):
    instructions,_=program(code); stacks=[list(left),list(right)]; pc=0; trace=[]
    for _ in range(limit):
        trace.append(dict(pc=pc,left=tuple(stacks[0]),right=tuple(stacks[1])))
        if not 0<=pc<len(instructions): return dict(status='reject',trace=trace)
        op,*targets=instructions[pc]
        if op in 'HR': return dict(status='accept' if op=='H' else 'reject',trace=trace)
        if op=='g': pc=targets[0]; continue
        side,write=OPS[op]; index=0 if side=='L' else 1; stack=stacks[index]
        if write is not None:
            if len(stack)==capacities[index]: return dict(status='unknown_space_bound',trace=trace)
            stack.append(write); pc=targets[0]
        else: pc=targets[0] if not stack else targets[1+stack.pop()]
    return dict(status='unknown_step_budget',trace=trace)

def initial(d,code,left,right,capacities,work):
    return ('B','B',wang.head(d['start'],'L'))+tuple(code)+('A',)+('P',)*work+('#',)+tuple(map(str,left))+('P',)*(capacities[0]-len(left))+('|',)+tuple(map(str,right))+('P',)*(capacities[1]-len(right))+('$','B','B')

def literal(d,row,limit,code=None,capacities=None,work=0):
    row=freeze(row); heads=[(i,s) for i,s in enumerate(row) if isinstance(s,tuple)]
    if len(heads)!=1: raise ValueError('one head')
    position,(_,q,value)=heads[0]; tape=list(row); tape[position]=value
    table={(q,a):(out,w,v) for q,a,out,w,v in d['transitions']}; observed=[]
    if code is not None:
        _,offsets=program(code); work_start=4+len(code); left_start=work_start+work+1; right_start=left_start+capacities[0]+1
    for step in range(limit+1):
        if code is not None and q==d['fetch']:
            if position not in offsets or tuple(tape[3:3+len(code)])!=tuple(code) or tape[3+len(code)]!='A': raise AssertionError('program/cursor not restored')
            if tape[work_start:work_start+work]!=['P']*work: raise AssertionError('scratch not restored')
            def read(start,size):
                values=tape[start:start+size]; digits=[]
                for symbol in values:
                    if symbol=='P': break
                    if symbol not in ('0','1'): raise AssertionError('nonbit stack')
                    digits.append(int(symbol))
                if values[len(digits):]!=['P']*(size-len(digits)): raise AssertionError('padding hole')
                return tuple(digits)
            observed.append(dict(pc=offsets[position],left=read(left_start,capacities[0]),right=read(right_start,capacities[1]),tm_step=step))
        if q in (d['halt'],'reject','space-bound','workspace-bound'):
            status={d['halt']:'accept','reject':'reject','space-bound':'unknown_space_bound','workspace-bound':'unknown_workspace_bound'}[q]; break
        if step==limit: status='unknown_step_budget'; break
        if (q,tape[position]) not in table: status='reject'; break
        q,w,move=table[q,tape[position]]; tape[position]=w; position+=move
        if not 0<=position<len(tape): status='unknown_tape_bound'; break
    final=tape.copy()
    if 0<=position<len(tape): final[position]=wang.head(q,final[position])
    else: final=None
    return dict(status=status,steps=step,boundaries=observed,final=tuple(final) if final else None)

def check_case(d,item):
    result=item['result']; work=result['workspace_capacity']
    expected=initial(d,item['code'],item['left'],item['right'],item['capacities'],work)
    if freeze(result['initial'])!=expected: raise AssertionError('external input binding')
    parsed,_=program(item['code']); declared=tuple((NAMES[op],)+tuple(args) for op,*args in item['program'])
    if parsed!=declared: raise AssertionError('encoded instruction semantics changed')
    actual=literal(d,expected,item['tm_limit'],item['code'],item['capacities'],work)
    for field in ('status','steps','final','boundaries'):
        if freeze(actual[field])!=freeze(result[field]): raise AssertionError('literal '+field+' changed '+item['name'])
    reference=stack_reference(item['code'],item['left'],item['right'],item['capacities'],item['vm_limit'])
    observed=[{k:v for k,v in b.items() if k!='tm_step'} for b in actual['boundaries']]
    if freeze(observed)!=freeze(reference['trace'][:len(observed)]): raise AssertionError('instruction simulation')
    if not actual['status'].startswith('unknown') and actual['status']!=reference['status']: raise AssertionError('terminal mismatch')
    source_entries=0
    if 'source' in item:
        source=previous.source_reference(item['source']); full=previous.source_checkpoints(item['translation'],reference['trace'])
        if freeze(full)!=freeze(source['trace']) or source['status']!=reference['status']: raise AssertionError('source/VM mismatch')
        prefix=previous.source_checkpoints(item['translation'],observed)
        if freeze(prefix)!=freeze(source['trace'][:len(prefix)]): raise AssertionError('literal source configuration')
        source_entries=len(prefix)
    return len(observed),source_entries

def check_rectangle(d,item):
    bottom=initial(d,item['program'],item['left'],item['right'],item['capacities'],item['workspace_capacity']); pattern=[(s,) for s in bottom]
    if item['unknown_input_bits']:
        if item['unknown_input_bits']!=1: raise AssertionError('unknown input layout')
        pattern[6+len(item['program'])+item['workspace_capacity']+item['capacities'][0]]=('0','1')
    top=('B','B',wang.head(d['halt'],'L'))+('B',)*(len(bottom)-3)
    if freeze(item['pattern'])!=tuple(pattern) or freeze(item['top'])!=top: raise AssertionError('external rectangle binding')
    compiler=previous.compiler_from_declaration(d); rows,placements=proof_search.unpack(item)
    if not lazy_wang.independent_check(compiler,tuple(pattern),top,rows,placements,extended=item['marking']=='redundant-neighbor-values'): raise AssertionError('point certificate')
    if any(previous.local_rule(d,*tile['triple'])!=tile['N'] for x,y,tile in placements): raise AssertionError('local rule')
    if literal(d,rows[0],item['height'])['status']!='accept': raise AssertionError('literal acceptance')
    return len(placements)

def audit(path):
    started=time.perf_counter();path=pathlib.Path(path);data=json.loads(path.read_text());d=data['machine'];fingerprint=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if fingerprint!=data['machine_sha256']: raise AssertionError('fixed table hash')
    reused=path.with_name(data['reused_artifact']['path'])
    if hashlib.sha256(reused.read_bytes()).hexdigest()!=data['reused_artifact']['sha256']: raise AssertionError('reused artifact hash')
    historical=json.loads(reused.read_text());old={r['name']:r for r in historical['source_controls']}
    if data['unary_machine']!=historical['machine'] or data['unary_machine_sha256']!=historical['machine_sha256']: raise AssertionError('historical table changed')
    for item in data['comparisons']:
        expected=old[item['name']]
        for field in ('source','translation','left','right','capacities'):
            if freeze(item[field])!=freeze(expected[field]): raise AssertionError('paired external source binding')
        if freeze(item['program'])!=freeze(expected['translation']['program']): raise AssertionError('paired program binding')
    checks=boundaries=entries=0
    for item in data['cases']+[r for r in data['comparisons'] if r['lane']!='unary']:
        if item['result']['machine_sha256']!=fingerprint: raise AssertionError('program-specific table')
        n,s=check_case(d,item);checks+=1;boundaries+=n;entries+=s
    unary=0
    for item in data['comparisons']:
        if item['lane']=='unary': boundaries+=previous.check_case(data['unary_machine'],item);unary+=1
    raw=0
    for item in data['raw_syntax_controls']:
        replay=literal(d,item['initial'],item['tm_limit'])
        if replay['status']!=item['status'] or replay['steps']!=item['steps']: raise AssertionError('raw syntax')
        raw+=1
    compiler=previous.compiler_from_declaration(d);u=lazy_wang.Universe(compiler);symbols=('B','0','n',wang.head(d['start'],'L'),wang.head(d['fetch'],'H'),wang.head('workspace-bound','#'));domains=0
    for allowed,north in [(symbols[:n],target) for n in (2,4,6) for target in (None,'B','0',wang.head('accept','L'))]:
        legal=[triple for triple in itertools.product(allowed,repeat=3) if (out:=previous.local_rule(d,*triple)) is not None and (north is None or north==out)]
        domain=u.domain(allowed,allowed,allowed,north=north)
        if domain.count!=len(legal) or set(domain.options())!=set(legal): raise AssertionError('complete symbolic domain')
        domains+=1
    size=len(d['alphabet']);valid=size+sum(q!=d['halt'] for q,a,out,w,v in d['transitions']);count=size**3+size**2*(valid+2*len(d['states'])*size)
    if count!=u.inventory_count or count!=data['inventory_count']: raise AssertionError('inventory count')
    cells=rectangles=0
    for item in data['wang_runs']:
        if item.get('verified'): cells+=check_rectangle(d,item);rectangles+=1
    base=next(r for r in data['wang_runs'] if r.get('verified') and r['unknown_input_bits']);tampered=[]
    bad=copy.deepcopy(base);bad['workspace_capacity']+=1;tampered.append(bad)
    bad=copy.deepcopy(base);bad['program']='g>0;';tampered.append(bad)
    bad=copy.deepcopy(base);bad['pattern'][0]=['1'];tampered.append(bad)
    bad=copy.deepcopy(base);bad['top'][0]='1';tampered.append(bad)
    bad=copy.deepcopy(base);bad['certificate']['grid'][0][0]=(bad['certificate']['grid'][0][0]+1)%len(bad['certificate']['tile_types_used']);tampered.append(bad)
    for bad in tampered:
        try:check_rectangle(d,bad)
        except (AssertionError,ValueError):pass
        else:raise AssertionError('tampered rectangle accepted')
    bad=copy.deepcopy(data['cases'][0]);bad['result']['boundaries'][0]['pc']=999
    try:check_case(d,bad)
    except AssertionError:pass
    else:raise AssertionError('tampered checkpoint accepted')
    helpers={n:hashlib.sha256(pathlib.Path(m.__file__).read_bytes()).hexdigest() for n,m in [('audit_uniform_machine.py',previous),('wang.py',wang),('lazy_wang.py',lazy_wang),('proof_search.py',proof_search)]}
    evidence=dict(status='passed',compact_runs=checks,unary_runs=unary,fetch_boundaries=boundaries,source_entries=entries,raw_controls=raw,symbolic_domain_checks=domains,checked_rectangles=rectangles,point_cells=cells,tampered_certificates_rejected=6,seconds=time.perf_counter()-started,audit_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),reused_helpers=helpers)
    data['independent_audit']=evidence;path.write_text(json.dumps(data,separators=(',',':'))+'\n');return evidence

if __name__=='__main__':
    import sys
    print(json.dumps(audit(sys.argv[1] if len(sys.argv)>1 else 'docs/research/gcts-rl-renewal/binary-machine-001.json'),indent=2))
