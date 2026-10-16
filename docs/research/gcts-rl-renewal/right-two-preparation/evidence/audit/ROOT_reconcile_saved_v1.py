"""Saved-only closure: stream hashes, small JSON, wire/native arithmetic; no Q decode."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
checks=[]
def need(ok,label):
    if not ok:raise ValueError(label)
    checks.append(label)
def load(path):return json.loads(Path(path).read_bytes())
def pin(path):
    p=Path(path).resolve();h=hashlib.sha256();n=0
    with p.open('rb') as f:
        for raw in iter(lambda:f.read(65536),b''):h.update(raw);n+=len(raw)
    return {'path':str(p),'sha256':h.hexdigest(),'bytes':n}
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

plan=load(ROOT/'ROOT-plan-v1.json');plan_pin=pin(ROOT/'ROOT-plan-v1.json')
external=ROOT/'audit-external-v1';owned=ROOT/'audit-owned-v1'
native=load(external/'native-terminal.json');obs=load(external/'observation.json')
once=load(external/'ONCE.json');bracket=load(ROOT/'ROOT-tool-bracket-v1.json')
need(native['all_reaped'] and not native['interrupted'] and not native['cancellation_forwarded'] and native['error'] is None,'true native terminal/reap without error/interruption')
need(native['caller_returncode']==native['wait4_status']==obs['meter_returncode']==obs['probe_returncode']==bracket['calls'][-1]['exit_code']==0,'all actual terminal exits zero')
for item in (obs,once):
    need(item['invocation_id']==plan['invocation_id'] and item['purpose']==plan['purpose'] and item['plan_sha256']==plan_pin['sha256'] and item['plan_bytes']==plan_pin['bytes'],'same once-only current plan/invocation/purpose')
launch,terminal,probe=native['caller_launch_began_ns'],native['caller_terminal_observed_ns'],obs['postterminal_native_probe_ns']
need(launch<terminal<=probe and terminal-launch==native['caller_kernel_elapsed_ns'],'native terminal order and interval')
need(0<probe-launch<20000000000,'strict launch-through-postprobe20')
need(native['wait4_pid']==native['caller_pid'] and 0<native['caller_kernel_peak_bytes']==native['wait4_usage'][2]<=536870912,'single-owned-process B=T true native wait4 peak below512MiB')
need(bracket['calls'][0]['session_id']==bracket['calls'][1]['session_id']==22160 and len(bracket['calls'])==3 and 0<bracket['ended_ms']-bracket['began_ms']<60000 and bracket['ended_ms']-bracket['began_ms']+1000<90000,'one invocation same-handle complete tool bracket and60/90+1 gates')
need((external/'meter-stderr.txt').read_bytes()==(external/'postterminal-probe-stderr.txt').read_bytes()==b'','entire stderr empty')
need(int((external/'postterminal-probe-stdout.txt').read_bytes())==probe,'whole actual postterminal probe bytes')
for name in ('sources','inputs','producer_sources'):
    for ref in plan[name].values():need(pin(ref['path'])==ref,'entire current '+name+':'+Path(ref['path']).name)
for ref in (plan['source_contract'],plan['ROOT_authorization'],plan['runtime'],*plan['reviews'].values()):
    need(pin(ref['path'])==ref,'entire current authority/review/runtime:'+Path(ref['path']).name)
receipt=load(external/'meter-stdout.txt');raw=(owned/'response.jsonl').read_bytes()
need(raw.endswith(b'\n') and raw.count(b'\n')==2,'entire exact twoLF response')
a,b=raw.splitlines();body,completion=json.loads(a),json.loads(b)
need(a==canonical(body) and b==canonical(completion) and completion['body_sha256']==hashlib.sha256(a+b'\n').hexdigest() and completion['body_bytes']==len(a)+1,'full canonical bodyLF completion hash/bytes')
need(completion['schema']=='Q-clean-verifier-response-completion-v1' and completion['exit_zero_and_coordinator_deadline_required'] is True,'unchanged complete response endpoint')
need(body['schema']=='right-two-independent-audit-response-body-v1' and body['status']=='COMPLETE_INDEPENDENT_AUDIT_PENDING_EXTERNAL' and body['invocation_id']==plan['invocation_id'] and body['plan']=={k:plan_pin[k] for k in ('sha256','bytes')},'complete exact current audit response')
need(body['limits']==plan['limits'] and body['resource_rule']==plan['resource_rule'] and body['sources']==plan['sources'] and body['inputs']==plan['inputs'] and body['producer_sources']==plan['producer_sources'],'same actual limits/current Source4/input6/producerSource6')
need(launch<=body['joint_began_ns']<terminal and body['joint_deadline_ns']-body['joint_began_ns']==20000000000,'one inherited original joint G/D inside native interval')
need(receipt['schema']=='right-two-independent-audit-final-observation-v1' and receipt['pending_external'] is True and receipt['response']==pin(owned/'response.jsonl'),'whole pending final observation binds full response')
need(len(receipt['outputs'])==2 and receipt['outputs'][0]==body['result'] and receipt['outputs'][1]==receipt['response'],'complete two-file final output inventory')
for ref in receipt['outputs']:need(Path(ref['path']).parent==owned and pin(ref['path'])==ref,'whole EOF/hash:'+Path(ref['path']).name)
need(sorted(p.name for p in owned.iterdir())==sorted(Path(r['path']).name for r in receipt['outputs']),'no omitted owned file')
result=load(owned/'audit-result.json');producer=load(plan['inputs']['producer_admission']['path']);decl=load(plan['inputs']['declaration']['path'])
need(producer['producer_preparation_accepted'] is True and producer['resource_accepted'] is True and producer['independent_catalogue_admitted'] is False,'fresh prior producer resource admission only')
need(result['schema']=='independent-complete-Q-catalogue-point-audit-v1' and result['completed'] is True and result['all_catalogue_primitive_and_initial_domains_accepted'] is True and result['bounded_grammar_complete'] is True,'whole independent bounded grammar/primitive/domain result completed and accepted')
need(result['declaration_sha256']==hashlib.sha256(canonical(decl)).hexdigest()==producer['declaration_value_sha256'],'same canonical declaration VALUE digest distinct from raw declaration digest')
binding={'declaration_sha256':plan['inputs']['declaration']['sha256'],**{k:result[k] for k in ('formula_registry_sha256','model_epoch','primitive_authority_epoch')}}
need(binding==producer['context_binding'] and result['source_bindings']==plan['producer_sources'],'all independent context epochs and fixed full producerSource6 match')
need(result['census']==producer['census'] and result['actual_primitive_semantic_checks']==result['census']['recipes']==16201 and result['census']['formulas']==11149,'entire fresh independent and producer census/primitive checks agree')
domains=result['initial_point_domains'];counts=producer['initial_legal_domain_counts']
need(domains['all_rows']==24 and domains['domain_counts']==counts and domains['complete_candidate_count']==sum(counts)==producer['initial_legal_candidate_count']==36734910,'all24 independent complete domain counts agree')
need(len(domains['domain_sha256_by_row'])==24 and all(type(x) is str and len(x)==64 for x in domains['domain_sha256_by_row']) and domains['exact_saved_point_union_accepted'] is True,'all24 complete independent domain fingerprints and exact saved union accepted')
need(domains['point_decision']==producer['initial_decision'] and domains['selected_physical_keys']==0 and result['searches']==result['RL_updates']==0,'same empty initial state/decision and no search or RL')
for name in ('FOL_complete','ROOT_admission_issued','ROOT_resource_accepted','full24_accepted','full_PA_accepted','full_trajectory_accepted','induction_accepted','native_accepted','target_proof_discovered','universal_compiler_accepted'):
    need(result[name] is False,'no unearned result flag:'+name)
for name in ('full24_accepted','full_trajectory_accepted','logical_proof_accepted'):need(domains[name] is False,'no unearned domain flag:'+name)
for name in ('RL_accepted','ROOT_catalogue_admitted','ROOT_resource_accepted','recipient_family_accepted','target_proof_accepted'):need(body[name] is False,'pending response retains no unearned flag:'+name)
evidence=[pin(p) for p in sorted(external.iterdir())]+receipt['outputs']
out={'schema':'ROOT-right-two-independent-audit-disposition-v1','invocation_id':plan['invocation_id'],
    'independent_catalogue_admitted':True,'resource_accepted':True,'all24_initial_domains_admitted':True,
    'target_proof_accepted':False,'recipient_family_accepted':False,'full24_solution_accepted':False,'trajectory_accepted':False,
    'native_Wang_palette_accepted':False,'GCTS_advantage_claimed':False,'RL_accepted':False,'goal_complete':False,
    'context_binding':binding,'declaration_value_sha256':result['declaration_sha256'],'census':result['census'],
    'initial_legal_domain_counts':counts,'initial_legal_candidate_count':sum(counts),'initial_decision':domains['point_decision'],
    'native_caller_elapsed_ns':terminal-launch,'native_launch_to_postprobe_ns':probe-launch,'native_single_worker_peak_bytes':native['caller_kernel_peak_bytes'],
    'tool_date_elapsed_ms':bracket['ended_ms']-bracket['began_ms'],'owned_files':2,'owned_file_bytes':sum(r['bytes'] for r in receipt['outputs']),
    'scope':'Fresh independent complete finite grammar, all16201 primitive semantics and all24 initial point domains admitted under unchanged strict20s/512MiB. Saved closure reads small results and streams raw bytes only; no semantic replay.',
    'limits':'Fixed reviewed synchronous Sources/Darwin runtime and single owned process; no hostile OS/VM guarantee. This is catalogue/initial-state admission, not a discovered theorem or search performance result.',
    'next':'Fresh clean equal-information ordinary/point consumers and controls required before recipient proof/benefit claims.',
    'checks':checks,'evidence':evidence,'plan':plan_pin}
with (ROOT/'ROOT-audit-disposition-v1.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','evidence','census','initial_legal_domain_counts')},sort_keys=True))
