"""Independent boundary bindings, constructor snapshots and literal laws.

No producer, lowering, encoder, serializer, proof logic or native-runner import.
The selected-symbol checker is rebuilt independently and also stopped at the
constructor/semantic boundary to inspect the exact heap actually assembled.
"""
import gzip,hashlib,json,resource,struct,subprocess,time
from pathlib import Path
from audit_tree_kernel import decode_input,validate_heap,need,packed,sha,static_program
from audit_tape_kernel import check_table,check_allocation

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-proof-boundary-audit')
KEYS=('protocol','theory','target','blocks','proof');RAW='B^01:,;'
PINNED_PROGRAM='877c47879b027b08f02d3923d1e6dd9ccaf9a12e354567109f1aaa640a8fb673'
PINNED_MICRO='2f9e430b0b7034ed615d81c3e9b3978dc47ba4136686227a9b86df5779b203ac'
PINNED_TABLE='fd1621b29a7d497859c850a116b295956db99b3d7c4c076e3b78bed680d682dd'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def wire_parse(word,nodes):
    """Independent postfix language and canonical DAG construction."""
    index={tuple(v):257+i for i,v in enumerate(nodes)};stack=[];i=0
    def cons(a,c):
        if (a,c) not in index:index[a,c]=257+len(nodes);nodes.append([a,c])
        return index[a,c]
    while i<len(word):
        op=word[i];i+=1
        if op=='0':
            bits=word[i:i+9];need(len(bits)==9 and set(bits)<=set('01'),'nine atom bits');i+=9
            value=sum((int(b)<<j) for j,b in enumerate(bits));need(value<=256,'finite atom');stack.append(value)
        elif op=='1':
            need(len(stack)>=2,'postfix underflow');c=stack.pop();a=stack.pop();stack.append(cons(a,c))
        elif op==';':need(set(word[i:])<=set('B'),'terminator padding');return stack
        else:raise ValueError('postfix token')
    raise ValueError('missing terminator')

def expected_constructor(micro,initial,request):
    b=micro['boundary'];nodes=[list(v) for v in b['boot_nodes']];validate_heap(nodes)
    fixed=initial['words'][b['problem']];free=initial['words'][b['certificate']]
    need(fixed.endswith(':') and free.endswith(':'),'fixed band end')
    values=wire_parse(fixed[:-1],nodes)+wire_parse(free[:-1],nodes);need(len(values)==5,'exact five fields')
    index={tuple(v):257+i for i,v in enumerate(nodes)}
    def cons(a,c):
        if (a,c) not in index:index[a,c]=257+len(nodes);nodes.append([a,c])
        return index[a,c]
    body=256
    for key,value in reversed(list(zip(b['key_nodes'],values))):body=cons(cons(key,value),body)
    root=cons(0,body);need(packed(decode_input(nodes,root))==packed(request),'fixed theorem and free certificate decode')
    need(values[:3]==wire_parse(fixed[:-1],[list(v) for v in b['boot_nodes']]),'fixed data cannot depend on free proof')
    return nodes,root

def micro_output(path):
    values=list(struct.unpack('<'+'I'*(path.stat().st_size//4),path.read_bytes()));i=0
    def take(n):
        nonlocal i
        result=values[i:i+n];need(len(result)==n,'micro output length');i+=n;return result
    magic,state,nt=take(3);need(magic==0x47544d34,'micro output');heads=[];words=[]
    for _ in range(nt):
        h,n=take(2);body=take(n);need(body[0]==1 and all(v<7 for v in body),'micro symbols');heads.append(h);words.append(''.join(RAW[v] for v in body[1:]).rstrip('B'))
    need(i==len(values),'micro output trailing data');return dict(state=state,heads=heads,words=words)

def heap_records(word):
    need(word.endswith(';'),'complete heap');nodes=[]
    for i,record in enumerate(word[:-1].split(';')):
        label,children=record.split(':');a,c=children.split(',')
        need(int(label[::-1],2)==257+i,'sequential heap ID');nodes.append([int(a[::-1],2),int(c[::-1],2)])
    validate_heap(nodes);return nodes

def input_bytes(initial):
    values=[0x47544d33,len(initial['words'])]
    for word,h,n in zip(initial['words'],initial['heads'],initial['capacities']):
        body='^'+word+'B'*(n-len(word)-1);need(len(body)==n and 0<=h<n,'band declaration')
        values.extend([n,h,*[RAW.index(s) for s in body]])
    return struct.pack('<'+'I'*len(values),*values)

def code_bytes(micro):
    values=[0x47544d32,len(micro['rows']),micro['start'],micro['accept'],micro['reject'],micro['space']]
    for row in micro['rows']:
        tape,choices=(0,{}) if row is None else row;values.extend([tape,len(choices)])
        for a,(q,w,d) in sorted(choices.items()):values.extend([RAW.index(a),q,RAW.index(w),d+1])
    return struct.pack('<'+'I'*len(values),*values)

def binding_checks(data,micro):
    need(sha(data['program'])==data['program_sha256']==PINNED_PROGRAM and micro['program_sha256']==data['program_sha256'],'program binding');static_program(data['program'])
    need(len(micro['rows'])==data['machine']['micro_states'] and sha(micro)==data['machine']['micro_sha256']==PINNED_MICRO,'microcode binding')
    need(data['machine']['literal_binary_sha256']==PINNED_TABLE,'external literal table pin')
    for name,pin in data['sources'].items():need(digest(HERE/name)==pin,'source '+name)
    for name,pin in data['artifacts'].items():need(digest(DOCS/name)==pin['sha256'] and (DOCS/name).stat().st_size==pin['bytes'],'artifact '+name)
    for name,pin in data['reused_artifacts'].items():need(digest(DOCS/name)==pin,'unchanged artifact '+name)
    return True

def main():
    start=time.perf_counter();TMP.mkdir(exist_ok=True);data=json.loads((DOCS/'proof-boundary-001.json').read_text())
    micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()));binding_checks(data,micro)
    raw=gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes())
    need(hashlib.sha256(raw).hexdigest()==data['machine']['literal_binary_sha256'],'literal binary binding')
    table=check_table(micro,raw);liveness=check_allocation(data['program'],micro);del raw
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_boundary_micro.cpp'),'-o',str(TMP/'runner')],check=True)
    (TMP/'code.bin').write_bytes(code_bytes(micro));summaries=[];total=0;constructor_total=0
    def execute(initial,limit,stop):
        (TMP/'input.bin').write_bytes(input_bytes(initial))
        r=json.loads(subprocess.check_output([str(TMP/'runner'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'output.bin'),str(limit),str(stop)]))
        return r,micro_output(TMP/'output.bin')
    b=micro['boundary']
    for row in data['cases']:
        need(sha({k:row['request'][k] for k in KEYS[:3]})==row['problem_pin'],'external theorem pin')
        expected,root=expected_constructor(micro,row['initial'],row['request'])
        # No proof-dependent initial registers, heap cells or frame state.
        template=data['cases'][0]['initial']
        for t in range(micro['tapes']):
            need(row['initial']['heads'][t]==1 or t==micro['stack'],'initial logical heads')
            if t not in (b['problem'],b['certificate']):
                need(row['initial']['words'][t]==template['words'][t] and row['initial']['capacities'][t]==template['capacities'][t],'fixed bootstrap '+str(t))
        r,end=execute(row['initial'],10**12,b['old_start'])
        need(r['status']=='stopped_state' and end['state']==b['old_start'],'constructor reaches checker')
        need(heap_records(end['words'][micro['heap']])==expected,'exact constructed canonical heap')
        slot=micro['allocation'][0]['slots'][0];need(int(end['words'][slot][::-1],2)==root,'actual semantic request root')
        constructor_total+=r['micro_steps']
        full,out=execute(row['initial'],10**12,len(micro['rows']))
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(full[k]==row['selected'][k],'fresh full symbol replay '+k)
        need(digest(TMP/'output.bin')==row['output_sha256'] and out==row['output'],'complete symbol output')
        if row['native']:
            for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(full[k]==row['native'][k],'literal agreement')
        capacity=row['initial']['capacities'][b['certificate']];word=row['initial']['words'][b['certificate']]
        need(len(word)==capacity-2 and word[-1]==':' and set(word[:-1])<=set('01;B'),'declared free payload and fixed frame')
        base=2+sum(n+2 for n in row['initial']['capacities'][:b['certificate']])
        pattern=dict(band=b['certificate'],logical_payload_cells=[1,capacity-2],ordinary_alphabet=['0','1',';','B'],
            frame_cell=capacity-2,frame_value=':',logical_cursor=1,physical_payload_cells=[base+1,base+capacity-2],
            first_cell_symbols=['@0','@1','@;','@B'],remaining_cell_symbols=['0','1',';','B'],
            fixed_assertion_sha256=hashlib.sha256(row['initial']['words'][b['problem']].encode('ascii')).hexdigest())
        total+=full['micro_steps'];summaries.append(dict(name=row['name'],constructor_micro_steps=r['micro_steps'],constructor_physical_steps=r['physical_steps'],constructed_nodes=len(expected),root=root,free_pattern=pattern))
        print(row['name'],'bound and replayed',r['micro_steps'],flush=True)
    for row in data['controls']:
        r,_=execute(row['initial'],row.get('limit',10**10),len(micro['rows']))
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(r[k]==row['result'][k],'control replay '+row['name'])
        need(digest(TMP/'output.bin')==row['output_sha256'],'control output '+row['name'])
    # Change each trust binding in isolation; malformed source hashes cannot
    # become new authority just by replacing certificate-side declarations.
    import copy
    mutations=[]
    for kind in ('program','microcode','source','fixed-target','free-proof'):
        bad=copy.deepcopy(data)
        try:
            if kind=='program':bad['program']['functions'][0]['code'][0]=['return',0];binding_checks(bad,micro)
            elif kind=='microcode':changed=copy.deepcopy(micro);changed['start']=0;binding_checks(bad,changed)
            elif kind=='source':bad['sources']['proof_boundary.py']='0'*64;binding_checks(bad,micro)
            else:
                row=bad['cases'][2];row['request']['target' if kind=='fixed-target' else 'proof']=['bot'];expected_constructor(micro,row['initial'],row['request'])
        except (ValueError,KeyError,IndexError):mutations.append(kind)
        else:raise ValueError('tampered '+kind+' accepted')
    audit=dict(cases=len(data['cases']),controls=len(data['controls']),constructor_snapshots=summaries,constructor_micro_steps=constructor_total,
        replay_micro_steps=total,liveness_equations=liveness,table=table,mutations_rejected=mutations,source_sha256=digest(__file__),
        replay_source_sha256=digest(HERE/'audit_boundary_micro.cpp'),seconds=time.perf_counter()-start,
        peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scope='finite constructor snapshots and full symbol replays, independent finite lowering laws; no formal universal compiler equivalence or accepting Wang rectangle')
    data['independent_audit']=audit;(DOCS/'proof-boundary-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print(json.dumps(audit,indent=2),flush=True)
if __name__=='__main__':main()
