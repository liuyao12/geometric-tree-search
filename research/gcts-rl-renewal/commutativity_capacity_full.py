"""All86remaining exact-request estimates, streamed under fixed resource bounds.

No native query, target proof or outcome-based selection. The frozen eight
pilot estimates remain separate. A later encoding pass proposes one common
external heap geometry for every actual94request, including original pilot8.
"""
import copy,gzip,hashlib,json,resource,signal,time
from pathlib import Path
from tree_machine import Heap,run
from audit_certificate_boundary import initial_for,pin
from audit_proof_boundary import expected_constructor,input_bytes,code_bytes,PINNED_MICRO,PINNED_PROGRAM

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011';OUT=PARENT/'capacity-full'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def need(t,m):
    if not t:raise ValueError(m)
def alarm(*a):raise TimeoutError('unknown_full_capacity_time_budget')
def arm(plan,began):
    remaining=plan['ceilings']['batch_seconds']-(time.perf_counter()-began);need(remaining>0,'unknown_full_capacity_batch_time_budget');signal.setitimer(signal.ITIMER_REAL,min(remaining,plan['ceilings']['per_request_seconds']))
def check(plan,began):
    need(time.perf_counter()-began<=plan['ceilings']['batch_seconds'],'unknown_full_capacity_batch_time_budget');need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=plan['ceilings']['rss_bytes'],'unknown_full_capacity_memory_budget')
def estimate(obs):
    return {k:obs[k] for k in ('request_sha256','definition_name','required_heap_capacity','requirement_is_complete','seconds')}|dict(tree_status=obs['tree_result']['status'],tree_steps=obs['tree_result']['steps'],heap_nodes=obs['tree_result']['heap_nodes'])
def request(theory,d):
    t=['imp',['bot'],['bot']];return dict(protocol='gcts-fol-1',theory=theory,blocks=[d],proof=[dict(rule='tautology',formula=t)],target=t)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());signal.signal(signal.SIGALRM,alarm);summary=dict(status='running_complete_remaining_capacity',native_queries=0,target_searches=0,observations=[],encodings=[]);metrics={}
    try:
        arm(plan,began)
        for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen full-capacity binding '+p)
        need(json.loads((PARENT/'capacity-pilot/audit.json').read_text())['status']=='passed_complete_selected_capacity_and_encoding_replay','exact eight-request gate');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());micro=load(DOC/'proof-boundary-microcode-001.json.gz');need(pin(micro)==PINNED_MICRO and pin(boundary['program'])==PINNED_PROGRAM,'same checker/palette');codehash=hashlib.sha256(code_bytes(micro)).hexdigest();requirements=load(PARENT/'attempt-02/admission-requirements.json.gz');by={q['name']:q for q in requirements};theory=load(PARENT/'attempt-02/two-lemmas-retained-core.json.gz')['spec']['theory']
        for q in load(PARENT/'capacity-pilot/estimates.json.gz'):metrics[q['definition_name']]=estimate(q)
        for j,name in enumerate(plan['remaining_names']):
            arm(plan,began);stage=time.perf_counter();item=by[name];req=request(theory,item['definition']);need(pin(req)==item['request_sha256'],'unchanged exact request');initial=initial_for(micro,boundary['cases'][0]['initial'],req);nodes,root=expected_constructor(micro,initial,req);heap=Heap(nodes,limit=plan['ceilings']['tree_heap_nodes']);result=run(boundary['program'],heap,root,limit=plan['ceilings']['tree_steps'],keep=0);required=2+sum((257+i).bit_length()+max(1,a.bit_length())+max(1,b.bit_length())+3 for i,(a,b) in enumerate(heap.nodes));obs=dict(query=j,definition_name=name,request=req,request_sha256=item['request_sha256'],original_initial=initial,original_input_sha256=hashlib.sha256(input_bytes(initial)).hexdigest(),constructor_nodes=nodes,constructor_root=root,tree_result=result,final_tree_nodes=heap.nodes,required_heap_capacity=required,requirement_is_complete=result['status']=='accepted',original_heap_capacity=initial['capacities'][micro['heap']],seconds=time.perf_counter()-stage);save(OUT/('estimate-%03d.json.gz'%j),obs);metric=estimate(obs);metrics[name]=metric;summary['observations'].append(metric);summary.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('FULL CAPACITY CHECKPOINT',j,required,result['steps'],result['status'],flush=True);need(result['status']=='accepted','unknown_or_rejected_complete_capacity');del obs,heap,nodes,initial,req;__import__('gc').collect();check(plan,began)
        need(set(metrics)==set(by),'all94 exact request capacities accounted');capacity=1
        while capacity<max(o['required_heap_capacity'] for o in metrics.values())+plan['safety_blank_cells']:capacity*=2
        need(capacity<=plan['ceilings']['physical_heap_cells'],'unknown_full_capacity_physical_boundary_budget')
        for j,name in enumerate(sorted(by)):
            arm(plan,began);req=request(theory,by[name]['definition']);initial=initial_for(micro,boundary['cases'][0]['initial'],req);extended=copy.deepcopy(initial);extended['capacities'][micro['heap']]=capacity;raw=input_bytes(extended);(OUT/('input-%03d.bin.gz'%j)).write_bytes(gzip.compress(raw,mtime=0));summary['encodings'].append(dict(index=j,definition_name=name,request_sha256=by[name]['request_sha256'],required_heap_capacity=metrics[name]['required_heap_capacity'],common_heap_capacity=capacity,original_capacity=initial['capacities'][micro['heap']],input_sha256=hashlib.sha256(raw).hexdigest(),input_bytes=len(raw),physical_width=sum(extended['capacities'])+2*len(extended['capacities'])+2));del raw,initial,extended;__import__('gc').collect();check(plan,began)
        allmetrics=[metrics[name] for name in sorted(metrics)];save(OUT/'complete-metrics.json.gz',allmetrics);fresh=[q for q in requirements if q['exact_prior_request'] is None];fresh_steps=sum(metrics[q['name']]['tree_steps'] for q in fresh);calibration=[]
        oldpre=load(ROOT/'.gcts-active/left-successor-20261011/workspace-study/attempt-02/preflight.json.gz');oldnative=load(ROOT/'.gcts-active/left-successor-20261011/workspace-native/native.json.gz')
        for pre,q in zip(oldpre,oldnative):
            need(pre['request_sha256']==q['request_sha256'] and q['result']['status']=='accepted','historical cost calibration exact native/request pair');calibration.append(dict(request_sha256=q['request_sha256'],tree_steps=pre['tree_result']['steps'],native_micro_steps=q['result']['micro_steps'],native_seconds=q['seconds'],micro_steps_per_tree_instruction=q['result']['micro_steps']/pre['tree_result']['steps'],microsteps_per_second=q['result']['micro_steps']/q['seconds']))
        ratios=[q['micro_steps_per_tree_instruction'] for q in calibration];rates=[q['microsteps_per_second'] for q in calibration];lo=fresh_steps*min(ratios);hi=fresh_steps*max(ratios);summary.update(status='complete_full_capacity_and_encoding_pending_independent_replay',complete_request_estimates=94,new_request_estimates=86,prior_exact_pilot_estimates=8,declared_common_heap_capacity=capacity,complete_fixed_tree_instructions=sum(m['tree_steps'] for m in allmetrics),maximum_required_heap_capacity=max(m['required_heap_capacity'] for m in allmetrics),requests_requiring_more_than_original_heap=sum(m['required_heap_capacity']>73178 for m in allmetrics),fresh_native_requests=93,fresh_native_fixed_tree_instructions=fresh_steps,complete_original_request_json_bytes=sum(q['request_json_bytes'] for q in requirements),fresh_native_request_json_bytes=sum(q['request_json_bytes'] for q in fresh),fresh_native_local_commands=sum(q['commands'] for q in fresh),calibration=calibration,heuristic_native_batch_cost=dict(status='extrapolation_only_not_a_bound',micro_steps_range=[lo,hi],native_seconds_range=[lo/max(rates),hi/min(rates)],native_plus_equal_cost_replay_seconds_range=[2*lo/max(rates),2*hi/min(rates)],assumptions='Linear native-microsteps/tree-instruction and measured microstep throughput from two earlier same-theory/checker full certificates. Local interface requests have different shapes/heaps; this is a nominal extrapolation, not a guarantee, confidence interval or approval to run. Actual93nativewall/microsteps/physicalsteps remain unknown.',formal_budget_example={'per_query_micro_steps':20000000000,'93_query_maximum_micro_steps':1860000000000}),program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,micro_code_bytes_sha256=codehash,scope='Complete94 exact-request heap capacities/encodings, with86fresh tree estimates and8audited exact reuse. Sameparser/checker/palette; no native admission, targetproof/search, GCTS/RL result or all-other-band guarantee.')
    except (ValueError,MemoryError,TimeoutError) as e:summary.update(status=str(e),failure_type=type(e).__name__);raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);summary.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
