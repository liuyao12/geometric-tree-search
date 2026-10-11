"""Independent full unchanged-palette native resource-study replay."""
import gzip,hashlib,json,resource,subprocess,time
from pathlib import Path
from audit_proof_boundary import code_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_certificate_boundary import pin
from left_successor_workspace_audit import encoded
from left_successor_pilot_audit import overflowing
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/left-successor-20261011';PRE=PARENT/'workspace-study/attempt-02';OUT=PARENT/'workspace-native';TMP=Path('/private/tmp/gcts-left-successor-workspace-native-audit-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'audit-plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text());need(summary['status']=='complete_resource_native_outcomes_pending_independent_replay','all native resource checkpoints');need(json.loads((PRE/'audit.json').read_text())['status']=='passed_workspace_only_capacity_and_encoding_preflight','full independent source request and external geometry gate');micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged parser/checker/universal palette')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'native audit frozen source '+p)
    for p,h in plan['input_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'exact frozen geometry/request inputs '+p)
    observations=load(PRE/'preflight.json.gz');records=load(OUT/'native.json.gz');need(len(records)==len(observations)==plan['ceilings']['native_queries'],'every unique frozen request');TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));result=dict(status='checking',observations=[],micro_steps=0)
    for j,(obs,rec) in enumerate(zip(observations,records)):
        need(rec['request']==obs['request'] and rec['request_sha256']==obs['request_sha256'] and rec['geometry']['capacity']==obs['enlarged_initial']['capacities'][micro['heap']] and rec['limit']==plan['ceilings']['per_query_micro_steps'],'exact unchanged candidate/theory/target and declared new resource boundary');raw=encoded(obs['enlarged_initial'],micro['raw']);need(hashlib.sha256(raw).hexdigest()==rec['input_sha256']==obs['enlarged_input_sha256'] and gzip.decompress((OUT/('query-%03d-input.bin.gz'%j)).read_bytes())==raw,'all actual parser input bytes');(TMP/'input.bin').write_bytes(raw);response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',rec['limit']));output=(TMP/'output.bin').read_bytes()
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(response[k])==str(rec['result'][k]),'independent actual palette replay '+k)
        need(rec['result']['start']==micro['start']==88986 and hashlib.sha256(output).hexdigest()==rec['output_sha256'] and gzip.decompress((OUT/('query-%03d-output.bin.gz'%j)).read_bytes())==output,'true parser start and every final output byte');result['observations'].append(dict(query=j,request_sha256=rec['request_sha256'],proof_commands=len(rec['request']['proof']),status=response['status'],micro_steps=response['micro_steps'],physical_steps=response['physical_steps'],micro_fnv64=response['micro_fnv64'],seconds=response['seconds'],all_input_output_matched=True,heap_capacity=rec['geometry']['capacity'],out_of_frame_bands=overflowing(output)));result.update(micro_steps=result['micro_steps']+response['micro_steps'],seconds=time.perf_counter()-began);(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('independent larger-boundary native replay',j,response['status'],flush=True)
    result.update(status='passed_complete_larger_workspace_native_replay',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,scope='Every complete native computation with the separately disclosed262144cell heap boundary is independently replayed at true parser start88986, matching exact requests, all input/output and micro/physical/FNV. Same fixed parser/checker/palette; geometry changed only. All original native/search unknowns remain preserved. This certifies the ordinary forward control if accepted, not a GCTS-discovered theorem or new RL result.')
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
