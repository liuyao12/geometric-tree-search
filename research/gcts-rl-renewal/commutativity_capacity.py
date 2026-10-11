"""Eight deterministic exact-request capacity estimates; no native execution.

Each full definition request is selected by declared operation/origin strata
and maximal canonical request bytes before outcomes. The exact fixed checker
program computes the complete canonical heap, with bounded time/space.
"""
import copy,gzip,hashlib,json,resource,signal,time
from pathlib import Path
from tree_machine import Heap,run
from audit_certificate_boundary import initial_for,pin
from audit_proof_boundary import expected_constructor,input_bytes,code_bytes,PINNED_MICRO,PINNED_PROGRAM

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011';OUT=PARENT/'capacity-pilot'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def need(t,m):
    if not t:raise ValueError(m)
def alarm(*a):raise TimeoutError('unknown_commutativity_capacity_time_budget')
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,plan['ceilings']['seconds']);summary=dict(status='running_capacity_estimates',native_queries=0,target_searches=0,observations=[]);observations=[]
    try:
        for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen capacity pilot '+p)
        need(json.loads((PARENT/'attempt-02/audit.json').read_text())['status']=='passed_complete_bounded_feasibility_audit','complete independent feasibility gate');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());micro=load(DOC/'proof-boundary-microcode-001.json.gz');need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==pin(boundary['program'])==PINNED_PROGRAM,'unchanged checker and palette')
        for j,item in enumerate(plan['selected_requests']):
            start=time.perf_counter();req=item['request'];need(pin(req)==item['request_sha256'],'exact complete request');initial=initial_for(micro,boundary['cases'][0]['initial'],req);nodes,root=expected_constructor(micro,initial,req);heap=Heap(nodes,limit=plan['ceilings']['tree_heap_nodes']);result=run(boundary['program'],heap,root,limit=plan['ceilings']['tree_steps'],keep=0);required=2+sum((257+i).bit_length()+max(1,a.bit_length())+max(1,b.bit_length())+3 for i,(a,b) in enumerate(heap.nodes));obs=dict(query=j,stratum=item['stratum'],definition_name=item['definition_name'],request=req,request_sha256=item['request_sha256'],original_initial=initial,original_input_sha256=hashlib.sha256(input_bytes(initial)).hexdigest(),constructor_nodes=nodes,constructor_root=root,tree_result=result,final_tree_nodes=heap.nodes,required_heap_capacity=required,requirement_is_complete=result['status']=='accepted',original_heap_capacity=initial['capacities'][micro['heap']],seconds=time.perf_counter()-start);observations.append(obs);save(OUT/'estimates.json.gz',observations);metric={k:obs[k] for k in ('query','stratum','definition_name','request_sha256','required_heap_capacity','requirement_is_complete','original_heap_capacity','seconds')};metric.update(tree_status=result['status'],tree_steps=result['steps'],heap_nodes=result['heap_nodes']);summary['observations'].append(metric);summary.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('COMMUTATIVITY CAPACITY CHECKPOINT',json.dumps(metric),flush=True)
            need(result['status']=='accepted','unknown_or_rejected_capacity_estimate');need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=plan['ceilings']['rss_bytes'],'unknown_commutativity_capacity_memory_budget')
        capacity=1
        while capacity<max(o['required_heap_capacity'] for o in observations)+plan['safety_blank_cells']:capacity*=2
        need(capacity<=plan['ceilings']['physical_heap_cells'],'unknown_commutativity_physical_boundary_budget')
        for o in observations:
            extended=copy.deepcopy(o['original_initial']);extended['capacities'][micro['heap']]=capacity;o['proposed_initial']=extended;raw=input_bytes(extended);o['proposed_input_sha256']=hashlib.sha256(raw).hexdigest();o['proposed_input_bytes']=len(raw);(OUT/('query-%03d-proposed-input.bin.gz'%o['query'])).write_bytes(gzip.compress(raw,mtime=0))
        save(OUT/'estimates.json.gz',observations);summary.update(status='complete_capacity_pilot_pending_independent_replay',declared_common_heap_capacity=capacity,program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,micro_code_bytes_sha256=hashlib.sha256(code_bytes(micro)).hexdigest(),scope='Eight generic size-stratified exact local-definition requests only, not all93freshrequests. No target proof or native execution; same fixed program/palette and only a proposed external blank heap boundary. Complete canonical heap estimates are not native acceptance and do not estimate unselected requests or all other tape bands.')
    except (ValueError,MemoryError,TimeoutError) as e:summary.update(status=str(e),failure_type=type(e).__name__);raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);summary.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,native_queries=0,target_searches=0);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
