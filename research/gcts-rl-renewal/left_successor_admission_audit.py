"""Independent whole replay of every fresh retained-union admission.

Each reused pilot request is separately tied to the completed pilot audit.
Every fresh exact definition request is reconstructed from the independently
proved full-grammar projection and run from the native parser start.
"""
import gzip,hashlib,json,subprocess,time
from pathlib import Path
from audit_certificate_boundary import initial_for,pin,sha
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_semantic_proofs import whole_replay
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011';TMP=Path('/private/tmp/gcts-left-successor-admission-audit-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def request(theory,d):
    taut=['imp',['bot'],['bot']];return dict(protocol='gcts-fol-1',theory=theory,blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'admission-audit-plan.json').read_text());producer=json.loads((OUT/'admission-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'admission-summary.json').read_text());pilot=load(OUT/'pilot-native.json.gz');records=load(OUT/'admission-native.json.gz');need(json.loads((OUT/'pilot-audit.json').read_text())['status']=='passed_preparation_native_replay_only','entire reused pilot ledger independently replayed');need(summary['status']=='native_complete_pending_independent_replays','complete measured union')
    for p,h in plan['source_sha256'].items():need(sha(ROOT/p)==h,'frozen admission audit source '+p)
    union={}
    for lane in base['variants']:
        c=load(OUT/(lane+'-reachable-core.json.gz'))
        for d in c['definitions']:
            if d['name'] in union:need(union[d['name']]==d,'same exact shared interface')
            union[d['name']]=d
    need(sorted(union)==producer['union_names'] and len(summary['definitions'])==len(union),'whole union complete');fresh=[]
    for name,item in zip(producer['union_names'],summary['definitions']):
        expected=request(base['case']['theory'],union[name]);need(item['name']==name and item['request_sha256']==pin(expected) and item['status']=='accepted','every exact accepted admission')
        if item['source']=='pilot-exact-request':
            rec=pilot[item['query']];need(rec['request']==expected and rec['result']['status']=='accepted' and producer['reuse'][name]['pilot_query']==item['query'],'exact independently audited reused request')
        else:
            need(item['source']=='fresh-native-request' and item['query']==len(fresh),'sequential fresh ledger');rec=records[item['query']];need(rec['request']==expected and rec['result']['status']=='accepted','fresh whole native request');fresh.append(expected)
    need(len(fresh)==len(records)==producer['ceilings']['new_queries'],'every fresh native computation accounted');DOC=ROOT/'docs/research/gcts-rl-renewal';micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'fixed native checker');TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));result=dict(status='checking',reused_exact_queries=len(producer['reuse']),fresh_queries=[],micro_steps=0)
    for j,(expected,rec) in enumerate(zip(fresh,records)):
        need(whole_replay(expected)['status']=='accepted','complete local logical audit under fixed premises');initial=initial_for(micro,boundary['cases'][0]['initial'],expected);raw=input_bytes(initial);need(hashlib.sha256(raw).hexdigest()==rec['input_sha256'] and gzip.decompress((OUT/('admission-query-%03d-input.bin.gz'%j)).read_bytes())==raw,'whole parser input');(TMP/'input.bin').write_bytes(raw);response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',rec['limit']));output=(TMP/'output.bin').read_bytes()
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(response[k])==str(rec['result'][k]),'entire native replay '+k)
        need(rec['result']['start']==88986 and sha(TMP/'output.bin')==rec['output_sha256'] and gzip.decompress((OUT/('admission-query-%03d-output.bin.gz'%j)).read_bytes())==output,'entire output and real parser start');result['fresh_queries'].append(dict(query=j,status=response['status'],seconds=response['seconds'],micro_steps=response['micro_steps'],whole_input_output_matched=True));result.update(micro_steps=result['micro_steps']+response['micro_steps'],seconds=time.perf_counter()-began);(OUT/'admission-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('union native replay',j,response['status'],flush=True)
    result.update(status='passed_complete_reachable_native_admission',seconds=time.perf_counter()-began,complete_union_definitions=len(union),scope='Complete 24-definition retained union reconstructed; four exact accepted pilot requests independently audited, all twenty fresh requests independently replayed with whole input/output/FNV/micro/physical fingerprints from true parser start. Full-grammar pruning separately passed. No target theorem yet searched.')
    (OUT/'admission-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    for lane in base['variants']:
        c=load(OUT/(lane+'-reachable-core.json.gz'));names={d['name'] for d in c['definitions']};registry=dict(status='native_accepted',definitions=[item for item in summary['definitions'] if item['name'] in names],complete_definition_sha256={d['name']:pin(d) for d in c['definitions']},authority='Complete actual retained definitions, exact native checks and independent whole replays. Full finite successful language preserved by separately proved structural pruning.',pruning_witness_sha256=c['structural_pruning']['witness_sha256'],pilot_audit_status='passed_preparation_native_replay_only',admission_audit_status=result['status']);(OUT/(lane+'-admission.json')).write_text(json.dumps(registry,indent=2)+'\n')
if __name__=='__main__':main()
