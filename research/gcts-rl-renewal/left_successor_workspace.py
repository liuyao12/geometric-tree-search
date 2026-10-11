"""Preflight a larger physical heap band with the fixed universal palette.

No native execution. Exact frozen tree instructions estimate the canonical
serialized heap needed for each unchanged request. The resource study changes
only external blank padding of band26; all initial symbols/heads, parser,
checker, microtable and actual certificate/theory/target remain unchanged.
"""
import copy,gzip,hashlib,json,resource,signal,struct,time
from pathlib import Path
from tree_machine import Heap,run
from audit_certificate_boundary import initial_for
from audit_proof_boundary import expected_constructor,input_bytes,code_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_certificate_boundary import pin
from tape_tree_machine import RAW

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/left-successor-20261011';OUT=PARENT/'workspace-study'
def need(t,m):
    if not t:raise ValueError(m)
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def little(n):return bin(n)[2:][::-1]
def heap_word(nodes):return ''.join(little(257+i)+':'+little(a)+','+little(c)+';' for i,(a,c) in enumerate(nodes))
def output_bands(data):
    vals=struct.unpack('<'+'I'*(len(data)//4),data);need(vals[0]==0x47544d34,'saved native output');bands=[];i=3
    for j in range(vals[2]):
        h,n=vals[i:i+2];i+=2;body=vals[i:i+n];i+=n;bands.append(dict(head=h,capacity=n,body=''.join(RAW[a] for a in body)))
    need(i==len(vals),'whole output bands');return bands
def alarm(*_):raise TimeoutError('unknown_workspace_preflight_time_budget')
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,plan['ceilings']['seconds'])
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'exact preflight source '+p)
    for p,h in plan['input_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'exact frozen resource input '+p)
    boundary=json.loads((DOC/'proof-boundary-001.json').read_text());micro=load(DOC/'proof-boundary-microcode-001.json.gz');need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==pin(boundary['program'])==PINNED_PROGRAM,'unchanged checker/palette');records=load(PARENT/'forward-control/native.json.gz');observations=[];summary=dict(status='preflighting',native_queries=0,observations=[])
    for i,record in enumerate(records):
        start=time.perf_counter();request=record['request'];initial=initial_for(micro,boundary['cases'][0]['initial'],request);need(hashlib.sha256(input_bytes(initial)).hexdigest()==record['input_sha256'],'exact original parser input');nodes,root=expected_constructor(micro,initial,request);heap=Heap(nodes,limit=plan['ceilings']['tree_heap_nodes']);result=run(boundary['program'],heap,root,limit=plan['ceilings']['tree_steps'],keep=0);serialized=heap_word(heap.nodes);old=output_bands(gzip.decompress((PARENT/'forward-control'/('query-%03d-output.bin.gz'%i)).read_bytes()));h=micro['heap'];prefix=old[h]['body'][1:].rstrip('B');need(serialized.startswith(prefix),'old native exhausted heap is an exact prefix of completed canonical heap estimate');required=len(serialized)+2;maximum_id_bits=max(len(little(257+len(heap.nodes))),len(little(root)));observation=dict(query=i,request_sha256=record['request_sha256'],request=request,original_initial=initial,constructor_nodes=nodes,constructor_root=root,final_tree_nodes=heap.nodes,tree_result=result,original_heap_capacity=initial['capacities'][h],boot_heap_symbols=len(initial['words'][h]),required_heap_capacity=required,old_native_prefix_symbols=len(prefix),old_native_heap_prefix_matches=True,maximum_id_bits=maximum_id_bits,preflight_seconds=time.perf_counter()-start);observations.append(observation);metric={k:observation[k] for k in ('query','request_sha256','original_heap_capacity','boot_heap_symbols','required_heap_capacity','old_native_prefix_symbols','maximum_id_bits','preflight_seconds')};metric.update(tree_status=result['status'],tree_steps=result['steps'],heap_nodes=result['heap_nodes']);summary['observations'].append(metric);save(OUT/'preflight.json.gz',observations);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('WORKSPACE ESTIMATE CHECKPOINT',json.dumps(metric),flush=True);need(result['status']=='accepted','cannot declare complete capacity from unfinished/rejected tree estimate');need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=plan['ceilings']['rss_bytes'],'unknown_workspace_preflight_memory_budget')
    capacity=1
    while capacity<max(o['required_heap_capacity'] for o in observations)+plan['safety_blank_cells']:capacity*=2
    need(capacity<=plan['ceilings']['physical_heap_cells'],'unknown_workspace_geometry_budget')
    for o in observations:
        enlarged=copy.deepcopy(o['original_initial']);enlarged['capacities'][micro['heap']]=capacity;o['enlarged_initial']=enlarged;o['enlarged_input_sha256']=hashlib.sha256(input_bytes(enlarged)).hexdigest();o['enlarged_input_bytes']=len(input_bytes(enlarged));(OUT/('query-%03d-enlarged-input.bin.gz'%o['query'])).write_bytes(gzip.compress(input_bytes(enlarged),mtime=0))
    save(OUT/'preflight.json.gz',observations);summary.update(status='preflight_complete_pending_independent_audit',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,declared_common_heap_capacity=capacity,additional_blank_cells=capacity-observations[0]['original_heap_capacity'],native_queries=0,program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,micro_code_bytes_sha256=hashlib.sha256(code_bytes(micro)).hexdigest(),scope='Capacity estimate and external geometry encoding only; exact frozen tree program replay is not native acceptance. The parser/checker/universal tile palette are unchanged. Only physical blank heap-band capacity is enlarged; the fixed/free payload strings and all heads stay byte-identical. Original heap unknowns remain preserved. No GCTS discovery or new target proof.')
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
