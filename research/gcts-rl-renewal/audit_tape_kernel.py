"""Independent finite lowering laws and external request/heap bindings.

Does not import the lowering, serialization, native runner or logical checker.
The finite laws relate selected symbol actions to literal TM scans. They do not
formally prove the upstream tree compiler correct on every possible request.
"""
import gzip,hashlib,json,struct,time,resource,subprocess
from pathlib import Path
from audit_tree_kernel import decode_input,strict_json,packed,sha as canonical_sha,need,PINNED_PROGRAM_SHA256
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
RAW=('B','^','0','1',':',',',';')
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def check_table(micro,raw):
    """Derive every finite physical row independently, then read the binary."""
    words=memoryview(raw).cast('I');cursor=0
    def read(n):
        nonlocal cursor
        need(cursor+n<=len(words),'table truncated');out=list(words[cursor:cursor+n]);cursor+=n;return out
    magic,alphabet,count,start,accept,reject,space=read(7)
    need(magic==0x47544d31 and alphabet==17+micro['tapes'] and (accept,reject,space)==(0,1,2),'literal header')
    entries={};next_state=3
    for q,row in enumerate(micro['rows']):
        if row is not None:entries[q]=list(range(next_state,next_state+4));next_state+=4
    marks={q:next_state+q for q in range(len(micro['rows']))}
    need(count==next_state+len(micro['rows']),'all literal states')
    def entry(q):return 0 if q==micro['accept'] else 1 if q==micro['reject'] else 2 if q==micro['space'] else entries[q][0]
    need(start==entry(micro['start']),'literal start')
    expected={0:(0,1,0,0,{}),1:(0,1,0,0,{}),2:(0,1,0,0,{})}
    for q,(select,header,find,observe) in entries.items():
        tape,choices=micro['rows'][q]
        need(type(tape) is int and 0<=tape<micro['tapes'],'selected tape')
        expected[select]=(select+1,0,0,0,{0:[header,0,2,0]})
        expected[header]=(header+1,2,0,0,{17+tape:[find,17+tape,2,0]})
        expected[find]=(find+1,2,0,0,{s:[observe,s,1,0] for s in range(9,17)})
        actions={}
        for s,(target,write,move) in choices.items():
            need(s in RAW and write in RAW and type(target) is int and 0<=target<len(micro['rows']) and type(move) is int and move in (-1,0,1),'micro action')
            a=9+RAW.index(s);w=(9 if move==0 else 1)+RAW.index(write)
            actions[a]=[entry(target) if move==0 else marks[target],w,move+1,target]
        actions[16]=[2,16,1,0]
        expected[observe]=(0,1,q+1,tape,actions)
    for q,m in marks.items():expected[m]=(0,1,0,0,{s:[entry(q),s+8,1,0] for s in range(1,8)}|{8:[2,8,1,0]})
    overrides=0;sweeps=0
    for q in range(count):
        default,direction,mid,tape,n=read(5);actual={}
        for _ in range(n):
            a,out,w,move,mout=read(5);need(a not in actual,'duplicate literal transition');actual[a]=[out,w,move,mout]
        want=expected[q];need((default,direction,mid,tape)==want[:4] and actual==want[4],'finite literal row '+str(q))
        overrides+=n;sweeps+=int(default==q+1 and direction!=1)
    need(cursor==len(words),'table trailing bytes')
    return dict(states=count,alphabet=alphabet,explicit_overrides=overrides,copy_sweep_states=sweeps,
                expanded_defined_transitions=overrides+sweeps*alphabet-sum(len(v[4]) for q,v in expected.items() if v[0]==q+1 and v[1]!=1))

def check_allocation(program,micro):
    """Validate liveness equations and preservation of simultaneous values."""
    equations=0
    for f,(fn,a) in enumerate(zip(program['functions'],micro['allocation'])):
        code=fn['code'];need(len(a['slots'])==fn['registers'],'register map')
        for pc,ins in enumerate(code):
            op,*x=ins
            reads={x[0]} if op in ('branch','return') else set(x[2]) if op=='call' else set() if op in ('const','jump') else set(x[1:])
            defs=set() if op in ('branch','return','jump') else {x[0]}
            successors=[] if op=='return' else [x[0]] if op=='jump' else x[1:] if op=='branch' else [pc+1] if pc+1<len(code) else []
            after=set().union(*(set(a['live_in'][j]) for j in successors)) if successors else set()
            before=reads|(after-defs)
            need(before==set(a['live_in'][pc]) and after==set(a['live_out'][pc]),'liveness equation')
            simultaneous=before|after|defs;colors=[a['slots'][r] for r in simultaneous]
            need(len(set(colors))==len(colors),'live-register collision');equations+=1
    return equations

def word(n):return format(n,'b')[::-1]
def machine_input(initial):
    values=[0x47544d33,len(initial['words'])]
    for text,h,n in zip(initial['words'],initial['heads'],initial['capacities']):
        band=['^']+list(text)+['B']*(n-len(text)-1);values.extend([n,h,*(RAW.index(s) for s in band)])
    return struct.pack('<'+'I'*len(values),*values)
def verify_case(row,micro):
    payload=bytes.fromhex(row['payload_hex']);request=strict_json(payload);reference=row['reference']
    need(hashlib.sha256(payload).hexdigest()==reference['certificate_sha256'],'certificate bytes')
    problem=canonical_sha({k:request[k] for k in ('protocol','theory','target')})
    need(problem==row['problem_pin']==reference['problem_sha256'],'external theorem pin')
    initial=row['tree_initial'];need(packed(decode_input(initial['nodes'],initial['node']))==packed(request),'syntax/heap binding')
    expected=['']*micro['tapes'];slot=micro['allocation'][0]['slots'][0]
    for i in range(micro['registers']):expected[i]=word(256)
    expected[slot]=word(initial['node'])
    expected[micro['heap']]=''.join(word(257+i)+':'+word(a)+','+word(b)+';' for i,(a,b) in enumerate(initial['nodes']))
    expected[micro['next']]=word(257+len(initial['nodes']))
    expected[micro['stack']]=':'+('0'*micro['address_width'])+';'
    heads=[1]*micro['tapes'];heads[micro['stack']]=len(expected[micro['stack']])+1
    need(row['initial']['words']==expected and row['initial']['heads']==heads,'initial tape protocol')
    need(len(row['initial']['capacities'])==micro['tapes'] and all(type(n) is int and n>len(w)+1 for n,w in zip(row['initial']['capacities'],expected)),'finite bands')
    need(hashlib.sha256(machine_input(row['initial'])).hexdigest()==row['micro_input_sha256'],'micro input bytes')
    native=row['native'];audit=row['independent']
    for k in ('status','physical_steps','micro_steps','micro_fnv64'):need(native[k]==audit[k],'independent micro replay '+k)
    need(native['status']==reference['status'],'logical reference')
    need(0<=native['sweep_steps']<=native['physical_steps'],'sweep count')
    return native['physical_steps'],native['micro_steps']

def main():
    start=time.perf_counter();path=DOCS/'tape-kernel-001.json';data=json.loads(path.read_text())
    for name,binding in data['sources'].items():need(digest(HERE/name)==binding,'source '+name)
    for name,binding in data['artifacts'].items():need(digest(DOCS/name)==binding['sha256'],'artifact '+name)
    micro=json.loads(gzip.decompress((DOCS/'tape-microcode-001.json.gz').read_bytes()))
    binary=gzip.decompress((DOCS/'tape-machine-001.bin.gz').read_bytes())
    need(sha(micro)==data['micro_sha256'],'micro pin')
    need(hashlib.sha256(binary).hexdigest()==data['machine']['literal_binary_sha256'],'literal binary pin')
    source=json.loads((DOCS/'tree-kernel-001.json').read_text())
    need(digest(DOCS/'tree-kernel-001.json')==data['reused_tree_artifact']['sha256'],'historical tree artifact')
    need(data['program_sha256']==micro['program_sha256']==PINNED_PROGRAM_SHA256==sha(source['program']),'complete program pin')
    laws=check_table(micro,binary);laws['liveness_equations']=check_allocation(source['program'],micro)
    tmp=Path('/private/tmp/gcts-tape-independent-audit');tmp.mkdir(exist_ok=True)
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(tmp/'runner')],check=True)
    values=[0x47544d32,len(micro['rows']),micro['start'],micro['accept'],micro['reject'],micro['space']]
    for row in micro['rows']:
        t,choices=(0,{}) if row is None else row;values.extend([t,len(choices)])
        for s,(q,w,d) in sorted(choices.items()):values.extend([RAW.index(s),q,RAW.index(w),d+1])
    (tmp/'code.bin').write_bytes(struct.pack('<'+'I'*len(values),*values))
    need(digest(tmp/'code.bin')==data['machine']['micro_binary_sha256'],'independent micro serialization')
    physical=steps=0
    for row in data['cases']:
        a,b=verify_case(row,micro);physical+=a;steps+=b
        (tmp/'input.bin').write_bytes(machine_input(row['initial']))
        replay=json.loads(subprocess.check_output([str(tmp/'runner'),str(tmp/'code.bin'),str(tmp/'input.bin'),str(tmp/'output.bin'),str(10**11)]))
        for k in ('status','physical_steps','micro_steps','micro_fnv64'):need(replay[k]==row['native'][k],'fresh independent execution '+row['name']+' '+k)
        need(digest(tmp/'output.bin')==row['independent_output_sha256'],'fresh complete tape output '+row['name'])
    for row in data['controls']:need(row['result']['status']=='unknown_step_budget' and row['result']['physical_steps']==row['limit'],'resource semantics')
    addition=next(r for r in data['cases'] if r['name']=='addition-induction');limited=data['space_control']
    need(limited['problem_pin']==addition['problem_pin'] and limited['initial']['words']==addition['initial']['words'] and limited['initial']['heads']==addition['initial']['heads'],'space control same proof')
    (tmp/'input.bin').write_bytes(machine_input(limited['initial']))
    replay=json.loads(subprocess.check_output([str(tmp/'runner'),str(tmp/'code.bin'),str(tmp/'input.bin'),str(tmp/'output.bin'),str(10**11)]))
    for k in ('status','physical_steps','micro_steps','micro_fnv64'):need(replay[k]==limited['native'][k]==limited['independent'][k],'fresh space replay '+k)
    need(replay['status']=='unknown_space_budget' and digest(tmp/'output.bin')==limited['independent_output_sha256'],'space is unknown')
    data['layout']={k:micro[k] for k in ('registers','heap','next','stack')};data['layout']['arg_end']=micro['work']
    data['machine']['function_allocations']=[dict(name=f['name'],logical=f['registers'],physical=max(a['slots'])+1) for f,a in zip(source['program']['functions'],micro['allocation'])]
    result=dict(laws=laws,cases=len(data['cases']),physical_steps=physical,micro_steps=steps,
        seconds=time.perf_counter()-start,peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        auditor_sha256=digest(__file__),scope='all finite tape-selection laws and CFG liveness equations; independent symbol executions; no universal tree compiler equivalence proof or Wang rectangle yet')
    data['independent_audit']=result;path.write_text(json.dumps(data,separators=(',',':'))+'\n');print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
