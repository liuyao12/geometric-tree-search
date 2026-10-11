"""Frozen remaining85 requests, ascending-name43+42, shared900s production.

No outcome-based order, targetproof path or search. Chunk42 requires complete
accepted and independently replayed chunk43. Unknowns stop advancement.
"""
import gzip,hashlib,json,resource,subprocess,sys,time
from pathlib import Path
from commutativity_native_pilot import EncodedRequestOracle,load,save,need
from audit_certificate_boundary import pin
from audit_proof_boundary import code_bytes,PINNED_MICRO

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011';ENC=PARENT/'capacity-stream';OUT=PARENT/'native-complete'
def main():
    began=time.perf_counter();label=sys.argv[1];need(label in ('chunk-43','chunk-42'),'declared chunk only');plan=json.loads((OUT/'plan.json').read_text());directory=OUT/label;tmp=Path('/private/tmp/gcts-commutativity-'+label+'-20261011');summary=dict(status='running_frozen_admission_chunk',chunk=label,native_queries=0,target_searches=0,observations=[]);oracle=None;prior=0
    try:
        for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen remaining85 binding '+p)
        need(json.loads((PARENT/'native-pilot/audit.json').read_text())['status']=='passed_complete_frozen_eight_native_pilot_replay' and json.loads((ENC/'audit.json').read_text())['status']=='passed_complete_all94_stream_encoding_and_prior_byte_correspondence','both completed gates');items=plan['chunks'][label]
        if label=='chunk-42':
            earlier=json.loads((OUT/'chunk-43/summary.json').read_text());audit=json.loads((OUT/'chunk-43/audit.json').read_text());need(earlier['native_queries']==43 and earlier['accepted_queries']==43 and audit['status']=='passed_complete_accepted_chunk_native_replay' and audit['native_admissions']==43,'complete accepted independently replayed firstchunk');prior=earlier['seconds']
        micro=load(DOC/'proof-boundary-microcode-001.json.gz');need(pin(micro)==PINNED_MICRO,'same universal palette');requirements={q['name']:q for q in load(PARENT/'attempt-02/admission-requirements.json.gz')};theory=load(PARENT/'attempt-02/two-lemmas-retained-core.json.gz')['spec']['theory'];tmp.mkdir(exist_ok=True,parents=True);start=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(tmp/'oracle')],check=True);(tmp/'code.bin').write_bytes(code_bytes(micro));need(hashlib.sha256((tmp/'code.bin').read_bytes()).hexdigest()==plan['micro_code_bytes_sha256'],'same exact native microtable');first=load(ENC/('frame-%03d.json.gz'%items[0]['stream_index']));oracle=EncodedRequestOracle(micro,first['proposed_initial'],tmp/'oracle',tmp/'code.bin',tmp);summary['compile_and_oracle_setup_seconds']=time.perf_counter()-start
        for j,item in enumerate(items):
            cumulative=prior+time.perf_counter()-began
            if cumulative>=plan['ceilings']['cumulative_production_seconds']:
                summary.update(status='unknown_remaining_admission_production_budget');break
            frame=load(ENC/('frame-%03d.json.gz'%item['stream_index']));d=requirements[item['definition_name']];taut=['imp',['bot'],['bot']];req=dict(protocol='gcts-fol-1',theory=theory,blocks=[d['definition']],proof=[dict(rule='tautology',formula=taut)],target=taut);need(pin(req)==item['request_sha256']==d['request_sha256']==frame['request_sha256'],'exact full local definition request');q=oracle.frozen_request(req,frame,ENC/('input-%03d.bin.gz'%item['stream_index']),plan['ceilings']['per_query_micro_steps']);q.update(chunk=label,definition_name=item['definition_name'],stream_index=item['stream_index'],estimated_required_heap_capacity=frame['required_heap_capacity'],geometry=dict(heap_band=micro['heap'],original_capacity=73178,capacity=262144),cumulative_production_seconds_before_query=cumulative,one_query_overshoot_seconds=max(0,prior+time.perf_counter()-began-plan['ceilings']['cumulative_production_seconds']));save(directory/'native.json.gz',oracle.records)
            for name in ('input.bin','output.bin'):(directory/('query-%03d-'%j+name+'.gz')).write_bytes(gzip.compress((tmp/name).read_bytes(),mtime=0))
            metric=dict(query=j,definition_name=q['definition_name'],request_sha256=q['request_sha256'],native_status=q['result']['status'],native_seconds=q['seconds'],micro_steps=q['result']['micro_steps'],physical_steps=q['result']['physical_steps'],one_query_overshoot_seconds=q['one_query_overshoot_seconds']);summary['observations'].append(metric);summary.update(native_queries=len(oracle.records),seconds=time.perf_counter()-began,cumulative_production_seconds=prior+time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('REMAINING ADMISSION CHECKPOINT',label,json.dumps(metric),flush=True)
            if q['result']['status']!='accepted':summary['status']='unknown_or_rejected_local_interface_stop';break
            need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=plan['ceilings']['rss_bytes'],'unknown_remaining_admission_memory_budget')
        if len(oracle.records)==len(items) and all(q['result']['status']=='accepted' for q in oracle.records):summary['status']='complete_accepted_chunk_pending_independent_replay'
        summary.update(accepted_queries=sum(q['result']['status']=='accepted' for q in oracle.records),unknown_queries=sum(q['result']['status'] not in ('accepted','rejected') for q in oracle.records),rejected_queries=sum(q['result']['status']=='rejected' for q in oracle.records),unexecuted_queries=len(items)-len(oracle.records),total_micro_steps=sum(q['result']['micro_steps'] for q in oracle.records),scope='Only frozen remaining85localadmissions. Shared900s cumulativeproduction across43+42 excludes separately accounted independentreplay. No targetproof/search. Chunk42 requires completeaccepted/replayed43; all unresolved requests remain unadmitted.')
    except (ValueError,MemoryError) as e:summary.update(status=str(e),failure_type=type(e).__name__);raise
    finally:
        summary.update(native_queries=0 if oracle is None else len(oracle.records),seconds=time.perf_counter()-began,cumulative_production_seconds=prior+time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        if oracle is not None:save(directory/'native.json.gz',oracle.records);oracle.close()
if __name__=='__main__':main()
