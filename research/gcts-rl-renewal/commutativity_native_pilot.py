"""Exactly eight frozen stratum winners, unchanged native checker and palette.

Inputs are the independently audited stream encodings. Only serialization is
changed; the existing persistent interpreter executes the full local requests.
Every query checkpoints its whole request, input, output and outcome. No target
proof search, outcome-based selection or remaining-93 admission batch occurs.
"""
import copy,gzip,hashlib,json,resource,shutil,subprocess,time
from pathlib import Path
from semantic_inventory_oracle import RequestOracle
from audit_proof_boundary import code_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_certificate_boundary import pin

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011';ENC=PARENT/'capacity-stream';OUT=PARENT/'native-pilot';TMP=Path('/private/tmp/gcts-commutativity-native-pilot-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def need(t,m):
    if not t:raise ValueError(m)
class EncodedRequestOracle(RequestOracle):
    def frozen_request(self,request,frame,source,limit):
        began=time.perf_counter();request=copy.deepcopy(request);need(self.initial(request)==frame['proposed_initial'] and pin(request)==frame['request_sha256'],'frozen exact parser initial');inp=self.directory/'input.bin';out=self.directory/'output.bin'
        with gzip.open(source,'rb') as src,inp.open('wb') as target:shutil.copyfileobj(src,target,65536)
        need(hashlib.sha256(inp.read_bytes()).hexdigest()==frame['input_sha256'],'native exact audited input');self.process.stdin.write(str(inp)+' '+str(out)+' '+str(limit)+'\n');self.process.stdin.flush();reply=self.process.stdout.readline();need(bool(reply),'native oracle stopped');result=json.loads(reply);record=dict(id=len(self.records),request=request,query_target='fixed_local_interface_admission',request_sha256=pin(request),input_sha256=frame['input_sha256'],output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),result=result,seconds=time.perf_counter()-began,purpose='frozen_eight_stratum_local_definition_admission',limit=limit);self.records.append(record);return record
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());summary=dict(status='running_frozen_eight_request_native_pilot',native_queries=0,target_searches=0,observations=[]);oracle=None
    try:
        for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen native pilot binding '+p)
        need(json.loads((ENC/'audit.json').read_text())['status']=='passed_complete_all94_stream_encoding_and_prior_byte_correspondence','entire94encoding gate');micro=load(DOC/'proof-boundary-microcode-001.json.gz');need(pin(micro)==PINNED_MICRO,'same universal palette');selected=json.loads((PARENT/'capacity-pilot/plan.json').read_text())['selected_requests'];requirements={q['name']:q for q in load(PARENT/'attempt-02/admission-requirements.json.gz')};need([q['definition_name'] for q in selected]==[q['definition_name'] for q in plan['selected_requests']] and len(selected)==8,'exact frozen eight winners');need(all(requirements[q['definition_name']]['exact_prior_request'] is None for q in selected),'all eight are fresh full requests; no uncredited prior-query reuse');TMP.mkdir(exist_ok=True,parents=True);start=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));need(hashlib.sha256((TMP/'code.bin').read_bytes()).hexdigest()==plan['micro_code_bytes_sha256'],'unchanged microtable bytes');first=load(ENC/('frame-%03d.json.gz'%plan['selected_requests'][0]['stream_index']));oracle=EncodedRequestOracle(micro,first['proposed_initial'],TMP/'oracle',TMP/'code.bin',TMP);summary['compile_and_oracle_setup_seconds']=time.perf_counter()-start
        for j,(item,claim) in enumerate(zip(selected,plan['selected_requests'])):
            elapsed=time.perf_counter()-began
            if elapsed>=plan['ceilings']['between_query_seconds']:
                summary.update(status='unknown_eight_pilot_production_budget',remaining_queries=8-j);break
            frame=load(ENC/('frame-%03d.json.gz'%claim['stream_index']));need(item['request_sha256']==frame['request_sha256']==claim['request_sha256'] and item['definition_name']==frame['definition_name'],'selected whole request binding');q=oracle.frozen_request(item['request'],frame,ENC/('input-%03d.bin.gz'%claim['stream_index']),plan['ceilings']['per_query_micro_steps']);q.update(stratum=item['stratum'],definition_name=item['definition_name'],stream_index=claim['stream_index'],estimated_required_heap_capacity=frame['required_heap_capacity'],geometry=dict(heap_band=micro['heap'],original_capacity=73178,capacity=262144),production_seconds_before_query=elapsed,one_query_overshoot_seconds=max(0,time.perf_counter()-began-plan['ceilings']['between_query_seconds']));save(OUT/'native.json.gz',oracle.records)
            for name in ('input.bin','output.bin'):(OUT/('query-%03d-'%j+name+'.gz')).write_bytes(gzip.compress((TMP/name).read_bytes(),mtime=0))
            metric=dict(query=j,definition_name=q['definition_name'],stratum=item['stratum'],request_sha256=q['request_sha256'],commands=len(item['request']['blocks'][0]['proof']),native_status=q['result']['status'],native_seconds=q['seconds'],micro_steps=q['result']['micro_steps'],physical_steps=q['result']['physical_steps'],one_query_overshoot_seconds=q['one_query_overshoot_seconds']);summary['observations'].append(metric);summary.update(native_queries=len(oracle.records),seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('NATIVE STRATUM CHECKPOINT',json.dumps(metric),flush=True);need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=plan['ceilings']['rss_bytes'],'unknown_eight_pilot_memory_budget')
        if len(oracle.records)==8:summary['status']='complete_frozen_eight_native_outcomes_pending_independent_replay'
        summary.update(accepted_queries=sum(q['result']['status']=='accepted' for q in oracle.records),unknown_queries=sum(q['result']['status'] not in ('accepted','rejected') for q in oracle.records),rejected_queries=sum(q['result']['status']=='rejected' for q in oracle.records),remaining_queries=8-len(oracle.records),total_micro_steps=sum(q['result']['micro_steps'] for q in oracle.records),scope='Eight exact pre-outcome stratum winners only. Complete local definitions under original theory and premises checked at unchanged parser/checker/palette with separately audited262144cell blank heap. Unknowns retained, no theory/targetproof change, no commutativity proof search or93-request batch. All interfaces remain unadmitted until full independent native replay.')
    except (ValueError,MemoryError) as e:summary.update(status=str(e),failure_type=type(e).__name__);raise
    finally:
        summary.update(native_queries=0 if oracle is None else len(oracle.records),seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        if oracle is not None:save(OUT/'native.json.gz',oracle.records);oracle.close()
if __name__=='__main__':main()
