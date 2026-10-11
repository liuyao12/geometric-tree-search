"""Independent fixed-program capacity estimate and moved-boundary audit.

No workspace producer import. The frozen independent stack interpreter is
observed through its initial heap-validation hook solely to retain its own
working heap for exact comparison. It does not change interpreter semantics.
No native execution; enlargement changes only external blank-band geometry.
"""
import gzip,hashlib,json,resource,signal,struct,time
from pathlib import Path
import audit_tree_kernel as T
from audit_certificate_boundary import initial_for,pin
from audit_proof_boundary import expected_constructor,PINNED_MICRO,PINNED_PROGRAM,code_bytes

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/left-successor-20261011';OUT=PARENT/'workspace-study'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def encoded(initial,alphabet):
    values=[0x47544d33,len(initial['words'])]
    for word,head,capacity in zip(initial['words'],initial['heads'],initial['capacities']):
        values.extend([capacity,head,alphabet.index('^')]);values.extend(alphabet.index(s) for s in word);values.extend([alphabet.index('B')]*(capacity-1-len(word)))
    return struct.pack('<'+'I'*len(values),*values)
def physical_bases(capacities):
    starts=[];pos=1
    for n in capacities:starts.append(pos+1);pos+=n+2
    return starts,pos+1
def alarm(*_):raise TimeoutError('unknown_workspace_audit_time_budget')
def main():
    began=time.perf_counter();plan=json.loads((OUT/'audit-plan.json').read_text());producer=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text());signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,plan['ceilings']['seconds']);need(summary['status']=='preflight_complete_pending_independent_audit' and summary['native_queries']==0,'complete no-native preflight');micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and pin(boundary['program'])==PINNED_PROGRAM,'exact frozen parser/checker/palette')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen independent workspace source '+p)
    for p,h in producer['input_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'exact unchanged request/native/model input '+p)
    T.static_program(boundary['program']);records=load(PARENT/'forward-control/native.json.gz');observations=load(OUT/'preflight.json.gz');result=dict(status='checking',native_queries=0,observations=[]);need(len(records)==len(observations),'all frozen unique candidates')
    for j,(rec,obs) in enumerate(zip(records,observations)):
        start=time.perf_counter();initial=initial_for(micro,boundary['cases'][0]['initial'],rec['request']);nodes,root=expected_constructor(micro,initial,rec['request']);need(obs['query']==j and obs['request']==rec['request'] and obs['request_sha256']==rec['request_sha256'] and obs['original_initial']==initial and obs['constructor_nodes']==nodes and obs['constructor_root']==root,'exact original request and true parser-constructor bindings');working=[];validate=T.validate_heap
        def observe(ns):validate(ns);working.append(ns)
        T.validate_heap=observe
        try:replay=T.replay(boundary['program'],dict(nodes=nodes,node=root),producer['ceilings']['tree_steps'],producer['ceilings']['tree_heap_nodes'],keep=0)
        finally:T.validate_heap=validate
        need(len(working)==1,'observe only independent interpreter heap');final=[list(n) for n in working[0]];claimed={k:v for k,v in obs['tree_result'].items() if k!='seconds'};need(replay==claimed and final==obs['final_tree_nodes'] and replay['status']=='accepted','independent full exact instruction event/profile/frame/heap replay');required=sum((257+i).bit_length()+max(1,a.bit_length())+max(1,b.bit_length())+3 for i,(a,b) in enumerate(final))+2;need(obs['required_heap_capacity']==required,'exact serialized canonical record width/capacity with trailing blank')
        binary=gzip.decompress((PARENT/'forward-control'/('query-%03d-output.bin.gz'%j)).read_bytes());values=struct.unpack('<'+'I'*(len(binary)//4),binary);offset=3;old_heap=None
        for tape in range(values[2]):
            head,n=values[offset:offset+2];offset+=2;body=values[offset:offset+n];offset+=n
            if tape==micro['heap']:old_heap=''.join(micro['raw'][s] for s in body[1:]).rstrip('B');need(head==n==initial['capacities'][tape],'exact original limiting heap boundary')
        bit=lambda v:''.join(str((v>>k)&1) for k in range(max(1,v.bit_length())));serialized=''.join(bit(257+i)+':'+bit(a)+','+bit(b)+';' for i,(a,b) in enumerate(final));need(serialized.startswith(old_heap) and len(old_heap)==obs['old_native_prefix_symbols'],'entire old native exhausted heap prefix matches independent completed heap')
        enlarged=obs['enlarged_initial'];need(enlarged['words']==initial['words'] and enlarged['heads']==initial['heads'] and enlarged['capacities']==[summary['declared_common_heap_capacity'] if t==micro['heap'] else n for t,n in enumerate(initial['capacities'])],'only external heap blank capacity changes');raw=encoded(enlarged,micro['raw']);need(gzip.decompress((OUT/('query-%03d-enlarged-input.bin.gz'%j)).read_bytes())==raw and hashlib.sha256(raw).hexdigest()==obs['enlarged_input_sha256'] and len(raw)==obs['enlarged_input_bytes'],'independent complete moved-boundary encoding bytes');before,width0=physical_bases(initial['capacities']);after,width1=physical_bases(enlarged['capacities']);need(all(after[t]-before[t]==(0 if t<=micro['heap'] else summary['additional_blank_cells']) for t in range(len(before))),'exact physical band shifts')
        result['observations'].append(dict(query=j,request_sha256=rec['request_sha256'],proof_commands=len(rec['request']['proof']),tree_status=replay['status'],tree_instruction_steps=replay['steps'],heap_nodes=len(final),required_heap_capacity=required,declared_heap_capacity=enlarged['capacities'][micro['heap']],original_heap_capacity=initial['capacities'][micro['heap']],old_native_heap_prefix_matches=True,physical_width_before=width0,physical_width_after=width1,problem_band=micro['boundary']['problem'],problem_physical_base_before=before[micro['boundary']['problem']],problem_physical_base_after=after[micro['boundary']['problem']],certificate_band=micro['boundary']['certificate'],certificate_physical_base_before=before[micro['boundary']['certificate']],certificate_physical_base_after=after[micro['boundary']['certificate']],all_payload_symbols_and_local_heads_unchanged=True,enlarged_input_sha256=obs['enlarged_input_sha256'],seconds=time.perf_counter()-start));(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('independent workspace preflight',j,required,enlarged['capacities'][micro['heap']],flush=True);need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=plan['ceilings']['rss_bytes'],'unknown_workspace_audit_memory_budget')
    desired=1
    while desired<max(o['required_heap_capacity'] for o in result['observations'])+producer['safety_blank_cells']:desired*=2
    need(desired==summary['declared_common_heap_capacity'] and summary['micro_code_bytes_sha256']==hashlib.sha256(code_bytes(micro)).hexdigest(),'declared common capacity and byte-identical palette table');result.update(status='passed_workspace_only_capacity_and_encoding_preflight',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,native_queries=0,program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,scope='Independent exact tree instruction/heap estimate and every moved initial boundary byte only. The physical band26 has more trailing blank cells; all request payload symbols, local cursors, parser/checker/program/microtable/palette are unchanged. This guarantees sufficient estimated heap-band space for this deterministic run, not other-band capacity or a native acceptance claim. Both original native heap unknowns remain separate; no native execution occurred in this gate.')
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
