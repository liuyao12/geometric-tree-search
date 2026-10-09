"""Independent tree-instruction replay; no producer/compiler/logic imports.

The published program hash is an external pin, not proof-supplied authority.
This audits an operational tree machine. Its infinite heap/frame implementation
has not yet been lowered to the project's literal finite tape interpreter.
"""
import hashlib,json,resource,time
from pathlib import Path

PINNED_PROGRAM_SHA256='5f3aaf81e325654d30cc116a8f412c3152e75ccb4e0d781882180e8d0ec1fa31'
HERE=Path(__file__).resolve().parent
DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'

def packed(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def sha(x):return hashlib.sha256(packed(x)).hexdigest()
def need(condition,reason):
    if not condition:raise ValueError(reason)
def integer(x,lo,hi):return type(x) is int and lo<=x<hi

def strict_json(payload):
    def obj(items):
        result={}
        for k,v in items:
            need(k not in result,'duplicate key');result[k]=v
        return result
    def forbidden(_):raise ValueError('noninteger number')
    return json.loads(payload.decode('utf-8'),object_pairs_hook=obj,parse_float=forbidden,parse_constant=forbidden)

def validate_heap(nodes):
    seen=set()
    for i,pair in enumerate(nodes):
        need(type(pair) in (list,tuple) and len(pair)==2,'cons pair shape')
        need(all(integer(c,0,257+i) for c in pair),'acyclic exact child IDs')
        need(tuple(pair) not in seen,'unique initial cons cells');seen.add(tuple(pair))

def decode_input(nodes,root):
    """Decode only the syntax adapter, independently of producer allocation."""
    validate_heap(nodes)
    def pair(x):
        need(integer(x,257,257+len(nodes)),'cons required');return nodes[x-257]
    def items(x):
        result=[]
        while x!=256:
            a,x=pair(x);result.append(a)
        return result
    def word(x):
        values=items(x);need(all(integer(v,0,256) for v in values),'byte list required')
        return bytes(values).decode('utf-8','surrogatepass')
    cache={}
    def value(x):
        if x in cache:return cache[x]
        tag,body=pair(x)
        if tag==0:
            result={}
            for field in items(body):
                k,v=pair(field);k=word(k);need(k not in result,'duplicate object key');result[k]=value(v)
        elif tag==1:result=[value(v) for v in items(body)]
        elif tag==2:result=word(body)
        elif tag in (3,4):
            vs=items(body);need(all(type(v) is int and v==1 for v in vs),'unary integer')
            need(tag!=4 or vs,'negative zero forbidden');result=len(vs)*(1 if tag==3 else -1)
        elif tag==5:need(integer(body,0,2),'boolean atom');result=bool(body)
        elif tag==6:need(type(body) is int and body==256,'null atom');result=None
        else:raise ValueError('unknown JSON tag')
        cache[x]=result;return result
    return value(root)

def static_program(p):
    need(set(p)=={'atom_max','nil','nodes','constants','functions'},'program fields')
    need(type(p['atom_max']) is int and p['atom_max']==256 and type(p['nil']) is int and p['nil']==256,'atom header')
    validate_heap(p['nodes']);bound=257+len(p['nodes'])
    need(all(integer(c,0,bound) for c in p['constants']),'constant binding')
    fs=p['functions'];need(fs and fs[0]['name']=='main' and fs[0]['arity']==1,'entry point')
    need(len({f['name'] for f in fs})==len(fs),'unique function names')
    shapes={'const':3,'move':3,'cons':4,'head':3,'tail':3,'pair':3,'atom':4,'succ':3,'not':3,'branch':4,'jump':2,'call':4,'return':2}
    for f in fs:
        need(set(f)=={'name','arity','registers','code'},'function fields')
        need(type(f['name']) is str and integer(f['registers'],1,10000000) and integer(f['arity'],0,f['registers']+1),'function size')
        need(f['code'],'nonempty function')
        for ins in f['code']:
            need(type(ins) is list and ins and ins[0] in shapes and len(ins)==shapes[ins[0]],'instruction shape')
            op=ins[0];args=ins[1:];reg=lambda x:integer(x,0,f['registers'])
            if op=='jump':need(integer(args[0],0,len(f['code'])),'jump destination')
            elif op=='const':need(reg(args[0]) and integer(args[1],0,len(p['constants'])),'constant operand')
            elif op=='branch':need(reg(args[0]) and all(integer(x,0,len(f['code'])) for x in args[1:]),'branch destinations')
            elif op=='call':need(reg(args[0]) and integer(args[1],0,len(fs)) and type(args[2]) is list and len(args[2])==fs[args[1]]['arity'] and all(reg(x) for x in args[2]),'call interface')
            else:need(all(reg(x) for x in args),'register operand')

def replay(p,initial,step_limit,heap_limit,keep=60):
    nodes=[tuple(n) for n in initial['nodes']];validate_heap(nodes)
    table={n:257+i for i,n in enumerate(nodes)};fs=p['functions']
    # Frame: function, next instruction, registers, destination in caller.
    stack=[[0,0,[initial['node']]+[256]*(fs[0]['registers']-1),None]]
    calls={};digest=hashlib.sha256();trace=[];peak=0
    def result(status,steps,**kw):
        return dict(status=status,steps=steps,event_sha256=digest.hexdigest(),profile=calls,
                    peak_frames=peak,heap_nodes=len(nodes),trace=trace,**kw)
    for tick in range(step_limit):
        frame=stack[-1];f,pc,reg,_=frame;ins=fs[f]['code'][pc];op=ins[0];a=ins[1:]
        frame[1]+=1;event=[f,pc,op];terminal=None
        try:
            if op=='jump':frame[1]=a[0]
            elif op=='call':
                vals=[reg[r] for r in a[2]];target=fs[a[1]]
                stack.append([a[1],0,vals+[256]*(target['registers']-len(vals)),a[0]])
                name=target['name'];calls[name]=calls.get(name,0)+1;event.append(vals)
            elif op=='return':
                v=reg[a[0]];event.append(v);done=stack.pop()
                if stack:stack[-1][2][done[3]]=v
                else:terminal=('accepted' if v==1 else 'rejected',v)
            elif op=='branch':
                v=reg[a[0]];need(v in (0,1),'Boolean branch value required');frame[1]=a[v+1];event.append(v)
            else:
                if op=='const':v=p['constants'][a[1]]
                elif op=='move':v=reg[a[1]]
                elif op=='cons':
                    k=(reg[a[1]],reg[a[2]])
                    if k not in table:
                        if heap_limit is not None and len(nodes)>=heap_limit:return result('unknown_heap_budget',tick,reason='tree heap bound')
                        table[k]=257+len(nodes);nodes.append(k)
                    v=table[k]
                elif op in ('head','tail'):
                    x=reg[a[1]];need(integer(x,257,257+len(nodes)),op+' requires a cons node');v=nodes[x-257][int(op=='tail')]
                elif op=='pair':v=int(reg[a[1]]>256)
                elif op=='atom':v=int(reg[a[1]]<=256 and reg[a[2]]<=256 and reg[a[1]]==reg[a[2]])
                elif op=='succ':
                    x=reg[a[1]];need(0<=x<255,'byte successor requires a byte below 255');v=x+1
                elif op=='not':
                    x=reg[a[1]];need(x in (0,1),'Boolean branch value required');v=1-x
                else:raise ValueError('unknown opcode')
                reg[a[0]]=v;event.append(v)
        except ValueError as exc:
            return result('rejected',tick+1,reason='invalid data operation: '+str(exc),function=fs[f]['name'],pc=pc)
        if len(trace)<keep:trace.append(event)
        digest.update(json.dumps(event,separators=(',',':')).encode()+b'\n')
        peak=max(peak,len(stack)-1)
        if terminal:return result(terminal[0],tick+1,value=terminal[1])
    return result('unknown_step_budget',step_limit)

def audit_row(p,row):
    payload=bytes.fromhex(row['payload_hex']);record=row['check'];initial=record['initial']
    need(hashlib.sha256(payload).hexdigest()==record['certificate_sha256'],'request byte binding')
    raw=strict_json(payload);need(packed(decode_input(initial['nodes'],initial['node']))==packed(raw),'encoded input binding')
    bound=sha({k:raw[k] for k in ('protocol','theory','target')})
    need(bound==row['problem_pin']==record['problem_sha256'],'external problem binding')
    need(record['program_sha256']==PINNED_PROGRAM_SHA256==sha(p),'fixed program binding')
    need(initial['nodes'][:len(p['nodes'])]==p['nodes'],'initial constant heap binding')
    actual=replay(p,initial,row['step_limit'],row['heap_limit'])
    claimed={k:v for k,v in record['result'].items() if k!='seconds'}
    need(packed(actual)==packed(claimed),'literal tree trace/result mismatch')
    need(record['status']==actual['status'],'adapter/VM status mismatch')
    if 'reference' in row:need(actual['status']==row['reference']['status'],'semantic reference mismatch')
    return actual

def audit(data):
    p=data['program'];need(sha(p)==PINNED_PROGRAM_SHA256==data['program_sha256'],'program pin');static_program(p)
    for name,binding in data['sources'].items():need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==binding,'source binding '+name)
    totals={'cases':0,'steps':0,'accepted':0,'rejected':0,'unknown':0}
    for row in data['cases']+data['machine_controls']:
        r=audit_row(p,row);totals['cases']+=1;totals['steps']+=r['steps']
        totals['accepted' if r['status']=='accepted' else 'rejected' if r['status']=='rejected' else 'unknown']+=1
    for row in data['adapter_controls']:
        payload=bytes.fromhex(row['payload_hex']);r=row['check']
        need(hashlib.sha256(payload).hexdigest()==r['certificate_sha256'] and r['program_sha256']==PINNED_PROGRAM_SHA256,'adapter input pin')
        if row['max_bytes'] is not None and len(payload)>row['max_bytes']:expected='unknown_resource_budget'
        else:
            try:
                raw=strict_json(payload);bound=sha({k:raw[k] for k in ('protocol','theory','target')})
                need(row['problem_pin'] is None or row['problem_pin']==bound,'external problem change')
                if row['heap_limit'] is not None and row['heap_limit']<len(p['nodes']):expected='unknown_resource_budget'
                else:raise ValueError('unrecognized pre-VM adapter control')
            except (ValueError,KeyError,UnicodeError):expected='rejected'
        need(r['status']==expected and 'result' not in r,'adapter resource/parse result')
    totals['adapter_controls']=len(data['adapter_controls'])
    return totals

def mutation_checks(data):
    import copy
    p=data['program'];base=next(r for r in data['cases'] if r['name']=='reflexivity');mutations=[]
    def change(name,fn):
        row=copy.deepcopy(base);fn(row);mutations.append((name,row))
    change('payload',lambda r:r.update(payload_hex=r['payload_hex']+'20'))
    change('problem pin',lambda r:r.update(problem_pin='0'*64))
    change('program pin',lambda r:r['check'].update(program_sha256='0'*64))
    change('decoded input',lambda r:r['check']['initial'].update(node=256))
    change('duplicate heap node',lambda r:r['check']['initial']['nodes'].append(r['check']['initial']['nodes'][-1]))
    change('dangling heap child',lambda r:r['check']['initial']['nodes'][0].__setitem__(0,len(r['check']['initial']['nodes'])+257))
    change('Boolean heap child',lambda r:r['check']['initial']['nodes'][0].__setitem__(0,True))
    change('event prefix',lambda r:r['check']['result']['trace'][0].__setitem__(-1,0))
    change('event digest',lambda r:r['check']['result'].update(event_sha256='0'*64))
    change('status',lambda r:r['check'].update(status='rejected'))
    change('step count',lambda r:r['check']['result'].update(steps=1))
    change('call profile',lambda r:r['check']['result']['profile'].update(main=1))
    change('heap count',lambda r:r['check']['result'].update(heap_nodes=1))
    change('resource boundary',lambda r:r.update(step_limit=0))
    rejected=[]
    for name,row in mutations:
        try:audit_row(p,row)
        except (ValueError,IndexError,KeyError,UnicodeError):rejected.append(name)
        else:raise ValueError('undetected mutation '+name)
    bad=copy.deepcopy(p);bad['functions'][0]['code'][0]=['return',0]
    need(sha(bad)!=PINNED_PROGRAM_SHA256,'changed instructions detected by external program pin');rejected.append('instruction table pin')
    return rejected

def main():
    start=time.perf_counter();path=DOCS/'tree-kernel-001.json';data=json.loads(path.read_text())
    result=audit(data);result['mutations_rejected']=mutation_checks(data)
    result.update(seconds=time.perf_counter()-start,peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope='every saved tree instruction and external input binding; operational tree VM, not literal tape/Wang')
    data['independent_audit']=result;path.write_text(json.dumps(data,separators=(',',':'))+'\n');print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
