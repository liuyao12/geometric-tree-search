"""Independent whole native replay of the declared preparation diagnostics.

Every exact representative request is reconstructed and logically replayed.
The fixed transition table executes from the real parser start; full input,
output and execution fingerprints must match. Space exhaustion is diagnosed
from the output tape bands, never translated into a validity rejection.
"""
import gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
from audit_certificate_boundary import initial_for,pin,sha
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_semantic_proofs import whole_replay
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011';TMP=Path('/private/tmp/gcts-left-successor-pilot-audit-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def overflowing(word):
    values=struct.unpack('<%dI'%(len(word)//4),word);need(values[0]==0x47544d34,'native output magic');offset=3;bands=[]
    for band in range(values[2]):
        head,capacity=values[offset:offset+2];offset+=2;bands.append(dict(band=band,head=head,capacity=capacity)) if head>=capacity else None;offset+=capacity
    need(offset==len(values),'complete output frame');return bands
def main():
    began=time.perf_counter();plan=json.loads((OUT/'pilot-audit-plan.json').read_text());producer=json.loads((OUT/'native-pilot-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'pilot-summary.json').read_text());records=load(OUT/'pilot-native.json.gz');need(summary['native_queries']==len(records) and len(records)<=producer['ceilings']['queries'],'complete actual query ledger')
    for path,h in plan['source_sha256'].items():need(sha(ROOT/path)==h,'frozen audit source '+path)
    cores={v:load(OUT/(producer['lane']+('-compact' if v=='compact' else '')+'-core.json.gz')) for v in producer['variants']};definitions={v:{d['name']:d for d in c['definitions']} for v,c in cores.items()};DOC=ROOT/'docs/research/gcts-rl-renewal';micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'fixed native checker');TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));result=dict(status='checking',queries=[],micro_steps=0)
    for j,rec in enumerate(records):
        item=producer['strata'][j//len(producer['variants'])];variant=producer['variants'][j%len(producer['variants'])];d=definitions[variant][item['name']];taut=['imp',['bot'],['bot']];expected=dict(protocol='gcts-fol-1',theory=base['case']['theory'],blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut);need(rec['request']==expected and rec['request_sha256']==pin(expected) and rec['definition_name']==item['name'] and rec['variant']==variant and rec['stratum']==item['stratum'],'independently reconstructed exact representative');need(whole_replay(expected)['status']=='accepted','separate host logical audit');initial=initial_for(micro,boundary['cases'][0]['initial'],expected);raw=input_bytes(initial);need(hashlib.sha256(raw).hexdigest()==rec['input_sha256'] and gzip.decompress((OUT/('pilot-query-%03d-input.bin.gz'%j)).read_bytes())==raw,'entire real parser input');(TMP/'input.bin').write_bytes(raw);response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',rec['limit']));output=(TMP/'output.bin').read_bytes()
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(response[k])==str(rec['result'][k]),'whole native execution '+k)
        need(rec['result']['start']==88986 and sha(TMP/'output.bin')==rec['output_sha256'] and gzip.decompress((OUT/('pilot-query-%03d-output.bin.gz'%j)).read_bytes())==output,'entire native output and true parser start');result['queries'].append(dict(query=j,stratum=item['stratum'],variant=variant,status=response['status'],micro_steps=response['micro_steps'],seconds=response['seconds'],complete_input_output_sha256_matched=True,out_of_frame_bands=overflowing(output)));result.update(micro_steps=result['micro_steps']+response['micro_steps'],seconds=time.perf_counter()-began);(OUT/'pilot-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('whole native pilot replay',j,variant,response['status'],flush=True)
    result.update(status='passed_preparation_native_replay_only',seconds=time.perf_counter()-began,scope='Exact declared representative requests reconstructed. Whole native transitions, full parser input/output, micro/physical steps and execution FNV matched. Native unknowns remain unknowns. No complete inventory admission or searched target proof.')
    (OUT/'pilot-audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
