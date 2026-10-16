"""Saved-only closure: whole stream hashes, small records and native arithmetic; no Horn replay."""
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
external=ROOT/'closed-set-external-v1';owned=ROOT/'closed-set-owned-v1'
native=load(external/'native-terminal.json');obs=load(external/'observation.json')
once=load(external/'ONCE.json');bracket=load(ROOT/'ROOT-tool-bracket-v1.json')
need(native['all_reaped'] and not native['interrupted'] and not native['cancellation_forwarded'] and native['error'] is None,'true native terminal/reap without error/interruption')
need(native['caller_returncode']==native['wait4_status']==obs['meter_returncode']==obs['probe_returncode']==bracket['calls'][-1]['exit_code']==0,'all actual terminal exits zero')
for item in (obs,once):
    need(item['invocation_id']==plan['invocation_id'] and item['purpose']==plan['purpose'] and item['plan_sha256']==plan_pin['sha256'] and item['plan_bytes']==plan_pin['bytes'],'same once-only exact plan/invocation/purpose')
launch,terminal,probe=native['caller_launch_began_ns'],native['caller_terminal_observed_ns'],obs['postterminal_native_probe_ns']
need(launch<terminal<=probe and terminal-launch==native['caller_kernel_elapsed_ns'],'native terminal order and interval')
need(0<probe-launch<20000000000,'strict whole launch-through-postprobe20')
need(native['wait4_pid']==native['caller_pid'] and 0<native['caller_kernel_peak_bytes']==native['wait4_usage'][2]<=536870912,'single-owned-process B=T native truewait4 peak below512MiB')
need(len(bracket['calls'])==2 and bracket['calls'][0]['session_id']==63325 and 0<bracket['ended_ms']-bracket['began_ms']<60000 and bracket['ended_ms']-bracket['began_ms']+1000<90000,'same-handle once-only complete tool bracket and60/90+1 gates')
need((external/'meter-stderr.txt').read_bytes()==(external/'postterminal-probe-stderr.txt').read_bytes()==b'','entire stderr empty')
need(int((external/'postterminal-probe-stdout.txt').read_bytes())==probe,'whole native postterminal probe bytes')
for name in ('sources','inputs','producer_sources'):
    for ref in plan[name].values():need(pin(ref['path'])==ref,'entire current '+name+':'+Path(ref['path']).name)
for ref in (plan['source_contract'],plan['ROOT_authorization'],plan['runtime'],*plan['reviews'].values()):need(pin(ref['path'])==ref,'entire authority/review/runtime:'+Path(ref['path']).name)
receipt=load(external/'meter-stdout.txt');raw=(owned/'response.jsonl').read_bytes()
need(raw.endswith(b'\n') and raw.count(b'\n')==2,'entire exact twoLF response')
a,b=raw.splitlines();body,completion=json.loads(a),json.loads(b)
need(a==canonical(body) and b==canonical(completion) and completion['body_sha256']==hashlib.sha256(a+b'\n').hexdigest() and completion['body_bytes']==len(a)+1,'canonical complete bodyLF/completion digest and bytes')
need(completion['schema']=='Q-clean-verifier-response-completion-v1' and completion['exit_zero_and_coordinator_deadline_required'] is True,'complete unchanged response endpoint')
need(body['schema']=='right-two-finite-Horn-closed-set-response-body-v1' and body['status']=='COMPLETE_CLOSED_SET_PENDING_EXTERNAL' and body['invocation_id']==plan['invocation_id'] and body['plan']=={k:plan_pin[k] for k in ('sha256','bytes')},'complete current closed-set response')
need(body['limits']==plan['limits'] and body['resource_rule']==plan['resource_rule'] and body['sources']==plan['sources'] and body['inputs']==plan['inputs'] and body['producer_sources']==plan['producer_sources'],'same actual original limits/current Source5/input6/producerSource6')
need(launch<=body['joint_began_ns']<terminal and body['joint_deadline_ns']-body['joint_began_ns']==20000000000,'one inherited original G/D inside native interval')
need(receipt['schema']=='right-two-finite-Horn-closed-set-final-observation-v1' and receipt['pending_external'] is True and receipt['response']==pin(owned/'response.jsonl'),'whole final observation binds complete response')
need(len(receipt['outputs'])==3 and receipt['outputs'][:-1]==body['outputs'] and receipt['outputs'][-1]==receipt['response'],'complete three-file final inventory')
for ref in receipt['outputs']:need(Path(ref['path']).parent==owned and pin(ref['path'])==ref,'whole EOF/hash:'+Path(ref['path']).name)
need(sorted(p.name for p in owned.iterdir())==sorted(Path(r['path']).name for r in receipt['outputs']),'no omitted owned file')
result=load(owned/'closed-set-result.json');candidate=load(owned/'closed-set-certificate.json');checked=result['checker_result']
admission=load(plan['inputs']['catalogue_admission']['path']);audit=load(plan['inputs']['audit_result']['path']);audit_plan=load(plan['inputs']['audit_plan']['path'])
need(admission['independent_catalogue_admitted'] is True and admission['resource_accepted'] is True and admission['plan']==plan['inputs']['audit_plan'] and audit_plan['inputs']['preparation']==plan['inputs']['preparation'],'exact prior independent complete catalogue/raw admission chain')
need(result['schema']=='right-two-finite-Horn-closed-set-result-v1' and result['invocation_id']==plan['invocation_id'] and result['immutable_view_only_exposed_to_producer'] is True,'whole current result and original private immutable-view scope')
need(checked['schema']=='finite-horn-closed-set-check-result-v1' and all(checked[x] is True for x in ('closed_set_verified','target_excluded','finite_horn_unreachable','whole_supplied_recipe_array_checked')),'complete actual checked finite-Horn closure and target exclusion')
need(body['context_binding']==result['context_binding']==checked['binding']==candidate['binding']==admission['context_binding'],'same whole raw-declaration/registry/model/primitive-authority binding throughout')
need(checked['formula_count']==candidate['formula_count']==admission['census']['formulas'] and checked['recipe_count']==candidate['recipe_count']==checked['closure_relations_checked']==admission['census']['recipes'],'all original formula/recipe rows retained and checked')
need(checked['zero_port_records_checked']==audit['census']['arity_counts']['0'] and checked['target_code']==candidate['target_code'] and 0<checked['set_member_count']<checked['formula_count'],'same zero-input census/target and proper certificate membership count')
certificate_raw=(owned/'closed-set-certificate.json').read_bytes()
need(certificate_raw==canonical(candidate)+b'\n' and checked['candidate_sha256']==hashlib.sha256(certificate_raw[:-1]).hexdigest() and checked['relation_sha256']==candidate['relation_sha256'],'whole canonical certificate rawLF versus value SHA and same complete relation digest')
controls=result['controls'];required={'truncated-bits','stale-binding','boolean-formula-count','target-included','missing-zero-input-output','nonzero-padding','nonzero-input-closure-violation'}
need(len(controls)==7 and {r['control'] for r in controls}==required and all(r.get('rejected') is True and type(r['rejection']) is str and r['rejection'] for r in controls) and result['all_applicable_controls_rejected'] is True,'all seven actual invalid-certificate controls rejected, none substituted or inapplicable')
for name in ('original_target_proved','arithmetic_nonprovability_accepted','point_state_accepted','trajectory_accepted','full24_accepted','native_accepted','ROOT_resource_accepted','RL_accepted'):need(checked[name] is False,'no enlarged checker claim:'+name)
for name in ('ROOT_resource_accepted','ROOT_finite_Horn_unreachability_admitted','target_proof_accepted','recipient_family_accepted','GCTS_marking_activated','GCTS_advantage_claimed','RL_accepted','full24_accepted','trajectory_accepted','native_Wang_palette_accepted'):need(result[name] is False,'no unearned result flag:'+name)
for name in ('ROOT_resource_accepted','ROOT_finite_Horn_unreachability_admitted','target_proof_accepted','arithmetic_nonprovability_accepted','GCTS_marking_activated','GCTS_advantage_claimed','RL_accepted'):need(body[name] is False,'pending response no unearned flag:'+name)
observed=result['producer_observations_untrusted']
need(observed['known_count_claimed']==checked['set_member_count'] and observed['recipe_visits_claimed']==observed['complete_sweeps_claimed']*checked['recipe_count'] and observed['declaration_value_sha256']==admission['declaration_value_sha256'],'literal producer diagnostic consistency only; leastness remains unverified')
out={'schema':'ROOT-right-two-finite-Horn-closed-set-disposition-v1','invocation_id':plan['invocation_id'],
    'finite_Horn_unreachability_admitted':True,'resource_accepted':True,'certificate_verified':True,
    'scope':'No finite word over this exact independently audited Horn recipe graph can reach its declared target. Any closed set containing all zero-input outputs and closed under all original rules excludes every possible derivation of an excluded target. This is a finite encoding limitation, not arithmetic/FOL nonprovability or a point-search trajectory.',
    'context_binding':checked['binding'],'formula_count':checked['formula_count'],'recipe_count':checked['recipe_count'],
    'certificate_set_members':checked['set_member_count'],'zero_input_records_checked':checked['zero_port_records_checked'],'target_code':checked['target_code'],
    'relation_sha256':checked['relation_sha256'],'candidate_value_sha256':checked['candidate_sha256'],'controls':controls,
    'leastness_verified':False,'producer_observations_untrusted':observed,
    'native_caller_elapsed_ns':terminal-launch,'native_launch_to_postprobe_ns':probe-launch,'native_single_worker_peak_bytes':native['caller_kernel_peak_bytes'],
    'tool_date_elapsed_ms':bracket['ended_ms']-bracket['began_ms'],'owned_files':3,'owned_file_bytes':sum(r['bytes'] for r in receipt['outputs']),
    'target_proof_accepted':False,'arithmetic_nonprovability_accepted':False,'recipient_family_accepted':False,'GCTS_marking_activated':False,
    'GCTS_advantage_claimed':False,'RL_accepted':False,'full24_solution_accepted':False,'trajectory_accepted':False,'native_Wang_palette_accepted':False,'goal_complete':False,
    'limits':'Fixed reviewed synchronous Sources/Darwin, one owned process/B=T; no hostile VM guarantee. Prior preparation/audit costs are separately disclosed, not included as one cold20 lifecycle. Saved closure streams hashes and reads small literal records only, with no Q decode or Horn/semantic replay.',
    'next':'Treat right-two as a certified negative/eligibility control for this finite encoding. Choose a separately declared complete broader grammar or credible positive-transfer target before comparing proof-search performance; preserve every previous UNKNOWN.',
    'plan':plan_pin,'checks':checks,'evidence':[pin(p) for p in sorted(external.iterdir())]+receipt['outputs']}
with (ROOT/'ROOT-closed-set-disposition-v1.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','evidence','controls','producer_observations_untrusted')},sort_keys=True))
