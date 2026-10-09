"""Independent stack semantics, literal transitions, TM correspondence and points.

No import from stack_program or uniform_stack_machine. Source TM controls use
unbounded sparse tape. Program parsing, input layout and fetch observations
are reconstructed independently from the serialized declaration.
"""
import copy,hashlib,itertools,json,pathlib,time
import wang,lazy_wang,proof_search

OPS={'a':('L',0),'b':('L',1),'c':('R',0),'d':('R',1),'e':('L',None),'f':('R',None)}

def freeze(v):
    if isinstance(v,list): return tuple(freeze(x) for x in v)
    if isinstance(v,dict): return {k:freeze(x) for k,x in v.items()}
    return v

def program(code):
    if type(code) is not str or not code.endswith(';'): raise ValueError('program syntax')
    result=[]; starts=[]; pos=3
    for record in code.split(';')[:-1]:
        starts.append(pos); pos+=len(record)+1
        if not record or record[0] not in 'abcdefgHR': raise ValueError('opcode')
        count=0 if record[0] in 'HR' else 3 if record[0] in 'ef' else 1
        parts=record[1:].split(',') if count else ()
        if len(parts)!=count or (not count and len(record)!=1) or any(any(c!='p' for c in p) for p in parts): raise ValueError('operand grammar')
        result.append((record[0],)+tuple(len(p) for p in parts))
    if not result: raise ValueError('empty program')
    return tuple(result),dict(zip(starts,range(len(starts))))

def stack_reference(code,left,right,capacities,limit=10000):
    instructions,_=program(code); l=list(left); r=list(right); pc=0; trace=[]
    for n in range(limit):
        trace.append(dict(pc=pc,left=tuple(l),right=tuple(r)))
        if not 0<=pc<len(instructions): return dict(status='reject',trace=trace)
        op,*addresses=instructions[pc]
        if op in 'HR': return dict(status='accept' if op=='H' else 'reject',trace=trace)
        if op=='g': pc=addresses[0]; continue
        side,write=OPS[op]; values=l if side=='L' else r; bound=capacities[0 if side=='L' else 1]
        if write is not None:
            if len(values)==bound: return dict(status='unknown_space_bound',trace=trace)
            values.append(write); pc=addresses[0]
        else: pc=addresses[0] if not values else addresses[1+values.pop()]
    return dict(status='unknown_step_budget',trace=trace)

def compiler_from_declaration(d):
    return wang.Compiler(tuple(d['alphabet']),tuple(d['states']),
                         {(q,s):(out,w,direction) for q,s,out,w,direction in d['transitions']},d['halt'])

def literal(d,initial,limit,observe_code=None,capacities=None):
    initial=freeze(initial); heads=[(i,s) for i,s in enumerate(initial) if isinstance(s,tuple)]
    if len(heads)!=1: raise ValueError('single literal head')
    position,(_,q,s)=heads[0]; tape=list(initial); tape[position]=s; transitions={(q,a):(out,w,v) for q,a,out,w,v in d['transitions']}; observed=[]
    if observe_code is not None:
        instructions,pc_at=program(observe_code); left_start=4+len(observe_code); right_start=left_start+capacities[0]+1
    for step in range(limit+1):
        if observe_code is not None and q==d['fetch']:
            if tape[3:3+len(observe_code)]!=list(observe_code) or position not in pc_at: raise AssertionError('noncanonical fetch')
            def read(start,length):
                seq=tape[start:start+length]; digits=[]
                for value in seq:
                    if value=='P': break
                    if value not in ('0','1'): raise AssertionError('invalid binary checkpoint')
                    digits.append(int(value))
                if seq[len(digits):]!=['P']*(length-len(digits)): raise AssertionError('padding hole')
                return tuple(digits)
            observed.append(dict(pc=pc_at[position],left=read(left_start,capacities[0]),right=read(right_start,capacities[1]),tm_step=step))
        if q in (d['halt'],'reject','space-bound'):
            status='unknown_space_bound' if q=='space-bound' else 'accept' if q==d['halt'] else 'reject'; break
        if step==limit: status='unknown_step_budget'; break
        if (q,tape[position]) not in transitions: status='reject'; break
        out,write,move=transitions[q,tape[position]]; tape[position]=write; q=out; position+=move
        if not 0<=position<len(tape): status='unknown_tape_bound'; break
    final=tape.copy()
    if 0<=position<len(tape): final[position]=wang.head(q,final[position])
    else: final=None
    return dict(status=status,steps=step,boundaries=observed,final=tuple(final) if final else None)

def source_reference(source,limit=10000):
    initial=freeze(source['initial']); transitions={(q,s):(out,w,d) for q,s,out,w,d in source['transitions']}
    blank=source['alphabet'][0]; heads=[(i,s) for i,s in enumerate(initial) if isinstance(s,tuple)]
    if len(heads)!=1: raise ValueError('one source head')
    position,(_,q,a)=heads[0]; tape={i:(s[2] if isinstance(s,tuple) else s) for i,s in enumerate(initial)}; trace=[]
    for step in range(limit+1):
        trace.append(dict(q=q,tape=tuple(sorted((i-position,s) for i,s in tape.items() if s!=blank))))
        if q==source['halt']: return dict(status='accept',trace=trace,steps=step)
        if step==limit: return dict(status='unknown_step_budget',trace=trace,steps=step)
        a=tape.get(position,blank)
        if (q,a) not in transitions: return dict(status='reject',trace=trace,steps=step)
        q,w,d=transitions[q,a]; tape[position]=w; position+=d

def source_checkpoints(translation,trace):
    width=translation['width']; alphabet=translation['alphabet']; entries={pc:q for q,pc in translation['entries'].items()}; result=[]
    def read(stack):
        if len(stack)%width: raise AssertionError('unaligned source-state stack')
        top=list(reversed(stack)); values=[]
        for offset in range(0,len(top),width):
            index=0
            for bit in top[offset:offset+width]: index=2*index+bit
            if index>=len(alphabet): raise AssertionError('invalid source code')
            values.append(index)
        return values
    for b in trace:
        if b['pc'] not in entries: continue
        l=read(b['left']); r=read(b['right']); values=[(-1-i,alphabet[a]) for i,a in enumerate(l) if a]+[(i,alphabet[a]) for i,a in enumerate(r) if a]
        result.append(dict(q=entries[b['pc']],tape=tuple(sorted(values))))
    return result

def local_rule(d,a,b,c):
    heads=[s for s in (a,b,c) if isinstance(s,tuple)]
    if len(heads)>1: return None
    table={(q,s):(out,w,v) for q,s,out,w,v in d['transitions']}
    if isinstance(b,tuple):
        if b[1]==d['halt']: return b
        transition=table.get((b[1],b[2]))
        if transition is None: return None
        out,w,move=transition
        return wang.head(out,w) if move==0 else w
    for neighbor,direction in ((a,1),(c,-1)):
        if isinstance(neighbor,tuple) and neighbor[1]!=d['halt']:
            transition=table.get((neighbor[1],neighbor[2]))
            if transition and transition[2]==direction: return wang.head(transition[0],b)
    return b

def check_case(d,item):
    left=tuple(map(str,item['left'])); right=tuple(map(str,item['right'])); capacities=item['capacities']
    expected=('B','B',wang.head(d['start'],'L'))+tuple(item['code'])+('#',)+left+('P',)*(capacities[0]-len(left))+('|',)+right+('P',)*(capacities[1]-len(right))+('$','B','B')
    if freeze(item['result']['initial'])!=expected: raise AssertionError('literal input binding changed')
    result=item['result']; actual=literal(d,result['initial'],item['tm_limit'],item['code'],tuple(item['capacities']))
    for field in ('status','steps','final','boundaries'):
        if freeze(actual[field])!=freeze(result[field]): raise AssertionError('literal replay changed '+item['name']+' '+field)
    reference=stack_reference(item['code'],item['left'],item['right'],item['capacities'],item['vm_limit'])
    observed=[{k:v for k,v in b.items() if k!='tm_step'} for b in actual['boundaries']]
    if freeze(observed)!=freeze(reference['trace'][:len(observed)]): raise AssertionError('stack semantics mismatch '+item['name'])
    if actual['status'] not in ('unknown_step_budget','unknown_space_bound','unknown_tape_bound') and actual['status']!=reference['status']: raise AssertionError('terminal semantics mismatch')
    if 'source' in item:
        names={'pushL0':'a','pushL1':'b','pushR0':'c','pushR1':'d','popL':'e','popR':'f','jump':'g','accept':'H','reject':'R'}
        expected_code=''.join(names[op]+','.join('p'*address for address in arguments)+';' for op,*arguments in item['translation']['program'])
        if expected_code!=item['code'] or item['translation']['alphabet']!=item['source']['alphabet']:
            raise AssertionError('translation payload changed')
        source=source_reference(item['source']); projected=source_checkpoints(item['translation'],reference['trace'])
        if freeze(projected)!=freeze(source['trace']): raise AssertionError('general TM translation changed '+item['name'])
        if source['status']!=reference['status']: raise AssertionError('source/VM halting mismatch')
    return len(observed)

def check_rectangle(d,run):
    code=run['program']; program(code); capacities=run['capacities']; left=tuple(map(str,run['left'])); right=tuple(map(str,run['right']))
    initial=('B','B',wang.head(d['start'],'L'))+tuple(code)+('#',)+left+('P',)*(capacities[0]-len(left))+('|',)+right+('P',)*(capacities[1]-len(right))+('$','B','B')
    pattern=[(s,) for s in initial]
    if run['unknown_input_bits']:
        if run['unknown_input_bits']!=1: raise AssertionError('unknown input layout')
        pattern[4+len(code)+capacities[0]+1]=('0','1')
    top=('B','B',wang.head('accept','L'))+('B',)*(len(initial)-3)
    if freeze(run['pattern'])!=tuple(pattern) or freeze(run['top'])!=top: raise AssertionError('external program/boundary binding changed')
    compiler=compiler_from_declaration(d); rows,placements=proof_search.unpack(run)
    if not lazy_wang.independent_check(compiler,tuple(pattern),top,rows,placements,extended=run['marking']=='redundant-neighbor-values'):
        raise AssertionError('Wang point certificate invalid')
    if any(local_rule(d,*tile['triple'])!=tile['N'] for x,y,tile in placements): raise AssertionError('literal Wang tile rule invalid')
    if literal(d,rows[0],run['height'])['status']!='accept': raise AssertionError('rectangle does not accept')
    return len(placements)

def audit(path):
    started=time.perf_counter(); path=pathlib.Path(path); data=json.loads(path.read_text()); d=data['machine']
    fingerprint=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if fingerprint!=data['machine_sha256']: raise AssertionError('literal table fingerprint changed')
    checks=boundaries=source_runs=raw=0
    for group in ('equality_cases','operation_cases','serialized_components','source_controls'):
        for item in data[group]:
            if item['result']['machine_sha256']!=fingerprint: raise AssertionError('program-dependent machine')
            boundaries+=check_case(d,item); checks+=1
            source_runs+=int('source' in item)
    for item in data['raw_syntax_controls']:
        actual=literal(d,item['initial'],item['tm_limit'])
        if actual['status']!=item['status']: raise AssertionError('raw grammar changed')
        raw+=1
    compiler=compiler_from_declaration(d); u=lazy_wang.Universe(compiler); domain_checks=0
    # Finite exhaustive restrictions, including undefined/accepting heads.
    symbols=('B','0','1',wang.head(d['start'],'L'),wang.head(d['fetch'],'H'),wang.head('reject','0'))
    for allowed,north in [(symbols[:n],target) for n in (2,4,6) for target in (None,'B','0',wang.head('accept','L'))]:
        legal=[triple for triple in itertools.product(allowed,repeat=3) if (out:=local_rule(d,*triple)) is not None and (north is None or out==north)]
        domain=u.domain(allowed,allowed,allowed,north=north)
        if domain.count!=len(legal) or set(domain.options())!=set(legal): raise AssertionError('incomplete symbolic domain')
        domain_checks+=1
    size=len(d['alphabet']); valid_centers=len(d['alphabet'])+sum(q!=d['halt'] for q,s,out,w,move in d['transitions'])
    expected=size**3+size**2*(valid_centers+2*len(d['states'])*size)
    if expected!=u.inventory_count or expected!=data['inventory_count']: raise AssertionError('full inventory count changed')
    cells=rectangles=0
    for run in data['wang_runs']:
        if not run.get('verified'): continue
        cells+=check_rectangle(d,run); rectangles+=1
    original=next(run for run in data['wang_runs'] if run.get('verified') and run['unknown_input_bits'])
    tampered=[]
    bad=copy.deepcopy(original); bad['program']='g;'; tampered.append(bad)
    bad=copy.deepcopy(original); bad['top'][0]='1'; tampered.append(bad)
    bad=copy.deepcopy(original); bad['pattern'][0]=['1']; tampered.append(bad)
    bad=copy.deepcopy(original); grid=bad['certificate']['grid']; grid[0][0]=(grid[0][0]+1)%len(bad['certificate']['tile_types_used']); tampered.append(bad)
    for bad in tampered:
        try: check_rectangle(d,bad)
        except (AssertionError,ValueError): pass
        else: raise AssertionError('tampered Wang proof accepted')
    bad=copy.deepcopy(data['equality_cases'][0]); bad['result']['boundaries'][0]['pc']=999
    try: check_case(d,bad)
    except AssertionError: pass
    else: raise AssertionError('tampered VM checkpoint accepted')
    evidence=dict(status='passed',literal_runs=checks,fetch_boundaries=boundaries,source_controls=source_runs,raw_grammar_controls=raw,
                  symbolic_domain_checks=domain_checks,checked_rectangles=rectangles,point_cells=cells,tampered_certificates_rejected=5,seconds=time.perf_counter()-started,
                  audit_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                  reused_helpers={name:hashlib.sha256(pathlib.Path(module.__file__).read_bytes()).hexdigest()
                                  for name,module in [('wang.py',wang),('lazy_wang.py',lazy_wang),('proof_search.py',proof_search)]})
    data['independent_audit']=evidence; path.write_text(json.dumps(data,separators=(',',':'))+'\n'); return evidence

if __name__=='__main__':
    import sys
    print(json.dumps(audit(sys.argv[1] if len(sys.argv)>1 else 'docs/research/gcts-rl-renewal/uniform-machine-001.json'),indent=2))
