"""Saved-only preparation closure: raw hashes, small JSON and native arithmetic."""
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
    p=Path(path);h=hashlib.sha256();n=0
    with p.open('rb') as f:
        for raw in iter(lambda:f.read(65536),b''):h.update(raw);n+=len(raw)
    return {'path':str(p.resolve()),'sha256':h.hexdigest(),'bytes':n}
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

plan=load(ROOT/'ROOT-plan-v1.json');external=ROOT/'preparation-external-v1';owned=ROOT/'preparation-owned-v1'
plan_pin=pin(ROOT/'ROOT-plan-v1.json');native=load(external/'native-terminal.json');obs=load(external/'observation.json')
once=load(external/'ONCE.json');bracket=load(ROOT/'ROOT-tool-bracket-v1.json')
need(native['all_reaped'] and not native['interrupted'] and not native['cancellation_forwarded'] and native['error'] is None,'true native terminal/reap without error/interruption')
need(native['caller_returncode']==native['wait4_status']==obs['meter_returncode']==obs['probe_returncode']==bracket['calls'][-1]['exit_code']==0,'all actual terminal exits zero')
for item in (obs,once):
    need(item['invocation_id']==plan['invocation_id'] and item['purpose']==plan['purpose'] and item['plan_sha256']==plan_pin['sha256'] and item['plan_bytes']==plan_pin['bytes'],'same once-only plan/invocation/purpose')
launch,terminal,probe=native['caller_launch_began_ns'],native['caller_terminal_observed_ns'],obs['postterminal_native_probe_ns']
need(launch<terminal<=probe and terminal-launch==native['caller_kernel_elapsed_ns'],'native terminal order and interval')
need(0<probe-launch<20000000000,'strict original launch-through-postprobe20')
need(native['wait4_pid']==native['caller_pid'] and 0<native['caller_kernel_peak_bytes']==native['wait4_usage'][2]<=536870912,'single owned B=T true wait4 peak below512MiB')
need(bracket['calls'][0]['session_id']==62861 and bracket['calls'][-1]['exit_code']==0 and 0<bracket['ended_ms']-bracket['began_ms']<60000 and bracket['ended_ms']-bracket['began_ms']+1000<90000,'complete same-handle actual tool Date bracket and60/90+1 gates')
need((external/'meter-stderr.txt').read_bytes()==(external/'postterminal-probe-stderr.txt').read_bytes()==b'','whole stderr empty')
need(int((external/'postterminal-probe-stdout.txt').read_bytes())==probe,'actual native postterminal probe bytes')
receipt=load(external/'meter-stdout.txt');raw=(owned/'response.jsonl').read_bytes()
need(raw.endswith(b'\n') and raw.count(b'\n')==2,'entire exact twoLF response')
a,b=raw.splitlines();body,completion=json.loads(a),json.loads(b)
need(a==canonical(body) and b==canonical(completion) and completion['body_sha256']==hashlib.sha256(a+b'\n').hexdigest() and completion['body_bytes']==len(a)+1,'full canonical bodyLF completion hash/bytes')
need(completion['schema']=='Q-clean-verifier-response-completion-v1' and completion['exit_zero_and_coordinator_deadline_required'] is True,'unchanged complete response endpoint')
need(body['schema']=='Q-right-two-preparation-response-body-v1' and body['status']=='COMPLETE_PRODUCER_PREPARATION_PENDING_EXTERNAL' and body['invocation_id']==plan['invocation_id'] and body['plan']=={k:plan_pin[k] for k in ('sha256','bytes')},'complete exact current preparation response')
need(body['limits']==plan['limits'] and body['resource_rule']==plan['resource_rule'] and body['sources']==plan['sources'] and body['inputs']==plan['inputs'],'same actual limits/Source6/input2')
need(receipt['schema']=='Q-right-two-preparation-final-observation-v1' and receipt['pending_external'] is True and receipt['response']=={k:pin(owned/'response.jsonl')[k] for k in ('sha256','bytes')},'whole pending final observation binds response')
need(body['outputs']==receipt['outputs'][:-1] and len(receipt['outputs'])==5,'full final five-file inventory')
for ref in receipt['outputs']:
    need(Path(ref['path']).parent==owned and pin(ref['path'])==ref,'whole EOF/hash:'+Path(ref['path']).name)
need(sorted(p.name for p in owned.iterdir())==sorted(Path(r['path']).name for r in receipt['outputs']),'no omitted owned file')
summary=load(owned/'summary.json');decl=load(plan['inputs']['declaration']['path'])
need(summary['schema']=='Q-right-two-complete-preparation-summary-v1' and summary['invocation_id']==plan['invocation_id'] and summary['sources']==plan['sources'] and summary['inputs']==plan['inputs'],'whole small summary current invocation/provenance')
need(summary['declaration']==decl and summary['declaration_value_sha256']==hashlib.sha256(canonical(decl)).hexdigest(),'same full literal declaration and distinct canonical value SHA')
need(summary['outputs']==body['outputs'][:3] and summary['context_binding']==body['context_binding']==receipt['context_binding'],'all output/cross-response context bindings')
need(summary['context_binding']['declaration_sha256']==plan['inputs']['declaration']['sha256'] and all(type(v) is str and len(v)==64 for v in summary['context_binding'].values()),'raw declaration identity distinct from canonical value identity')
need(launch<=summary['joint_began_ns']<terminal and summary['joint_deadline_ns']-summary['joint_began_ns']==20000000000,'one inherited source G/D within native interval')
counts=summary['initial_legal_domain_counts'];census=summary['census']
need(summary['height']==summary['all_initial_domain_rows_compared']==24 and len(counts)==24 and all(type(n) is int and n>1 for n in counts),'all24 complete positive nonsingleton producer domains')
smallest=min(range(24),key=lambda r:(counts[r],r))
need(summary['initial_decision']=={'kind':'branch','row':smallest,'count':counts[smallest],'generation':0},'saved initial generation-tied minimum decision from full count array')
need(census['formulas']<=decl['limits']['maximum_formulas'] and census['recipes']<=decl['limits']['maximum_recipes'] and sum(census['arity_counts'].values())==census['recipes'],'observed full census fits fixed compiler ceilings')
for name in ('independent_catalogue_admitted','ROOT_resource_accepted','target_proof_accepted','full24_solution_accepted','trajectory_accepted','native_accepted','RL_accepted'):
    need(summary[name] is False,'no unearned summary flag:'+name)
need(summary['graph_constructions']==1 and summary['target_searches']==summary['proof_words_supplied']==0 and not summary['library_used'] and not summary['recipe_trimming'],'preparation only; no supplied proof or reduced model')
for name in ('independent_catalogue_admitted','ROOT_resource_accepted','target_proof_accepted','recipient_family_accepted','full24_solution_accepted','trajectory_accepted','native_accepted','RL_accepted'):
    need(body[name] is False,'no unearned response flag:'+name)
evidence=[pin(p) for p in sorted(external.iterdir())]+receipt['outputs']
result={'schema':'ROOT-right-two-preparation-disposition-v1','invocation_id':plan['invocation_id'],'producer_preparation_accepted':True,'resource_accepted':True,
    'independent_catalogue_admitted':False,'target_proof_accepted':False,'recipient_family_accepted':False,'GCTS_advantage_claimed':False,'RL_accepted':False,'goal_complete':False,
    'context_binding':summary['context_binding'],'declaration_value_sha256':summary['declaration_value_sha256'],'census':census,
    'initial_legal_domain_counts':counts,'initial_legal_candidate_count':sum(counts),'initial_decision':summary['initial_decision'],
    'native_caller_elapsed_ns':terminal-launch,'native_launch_to_postprobe_ns':probe-launch,'native_single_worker_peak_bytes':native['caller_kernel_peak_bytes'],
    'tool_date_elapsed_ms':bracket['ended_ms']-bracket['began_ms'],'owned_files':5,'owned_file_bytes':sum(r['bytes'] for r in receipt['outputs']),
    'scope':'Resource-closed complete producer preparation/all24 producer-domain comparisons only. Large data raw-hashed, not decoded or semantically replayed by this saved closer.',
    'next':'Fresh current independent grammar/recipe/initial-domain audit required before recipient qualification/search; old1717 original-profile admission cannot be reused.',
    'checks':checks,'evidence':evidence}
with (ROOT/'ROOT-preparation-disposition-v1.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','evidence','census','initial_legal_domain_counts')},sort_keys=True))
