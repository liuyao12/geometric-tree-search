"""Saved byte/JSON joins only; never replays scientific modules or checks."""
from pathlib import Path
import json,hashlib
S=Path('/private/tmp/gcts-head-gated-ROOT-source-20261017')
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def digest(v,ascii=False):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=ascii,allow_nan=False).encode()).hexdigest()
base=Path('/private/tmp/gcts-head-gated-inference-visible-ROOT-20261017');lit=Path('/private/tmp/gcts-head-gated-inference-literal-ROOT-20261017')
vd=json.loads((base/'ROOT-disposition-v1.json').read_bytes());ld=json.loads((lit/'ROOT-disposition-v1.json').read_bytes())
vp=json.loads((base/'ROOT-plan-v1.json').read_bytes());lp=json.loads((lit/'ROOT-plan-v1.json').read_bytes())
assert vd['actual_closed']and vd['all_reaped']and vd['status']=='UNKNOWN'and not vd['receiver_probe_record_complete']and not vd['complete_wire_verified']and not vd['native_resources_qualified']
assert vd['failure_diagnostic']['complete_pair']and all(v is None for v in vd['failure_diagnostic']['last_observations'].values())
assert not(base/'ROOT-expanded-result-v1.json').exists()
assert ld['actual_closed']and ld['all_reaped']and ld['receiver_probe_record_complete']and ld['complete_wire_verified']and ld['native_resources_qualified']
x=json.loads((lit/'ROOT-expanded-result-v1.json').read_bytes());r=x['receiver_probe']['receiver'];e=r['engine_result']
env=next(q for v in e['events']for q in v.get('receipts',[])if q.get('provider_report')is not None);pr=env['provider_report'];cr=env['consumer_receipt']
assert r['observations']['provider_calls'][0]['report_sha256']==digest(pr)and r['observations']['consumer_calls'][0]['receipt_sha256']==digest(cr)
assert cr['status']=='UNKNOWN'and cr['selection']is None and cr['checks']==[]
assert pr['offers']==[]and pr['batch']['instances']==[]and pr['batch']['status']=='UNKNOWN'
assert e['status']=='UNKNOWN'and e['reason']=='node ceiling; no exhausted conclusion'and e['root_restored']and e['stack_restored']
assert e['counts']['family_choices']==0 and e['counts']['family_canonical_choices']==1
checks=pr['physical_assignment_plan']['head_gate']['checks'];conflicts=[];unknownpasses=0
for g in checks:
 q=g['receipt'];assert g['request']==q['request']and q['request_sha256']==digest(g['request'],True)
 assert q['status']in ('HEAD_CONFLICT','NO_KNOWN_HEAD_CONFLICT')and q['gate_completed']is True
 if q['status']=='HEAD_CONFLICT':
  assert g['outcome']=='SKIP_THIS_PHYSICAL_PLAN'and q['advisory_plan_rejected']is True
  conflicts.append(g)
 else:
  assert g['outcome']=='PASS_TO_OBSERVED_MATCHING'and q['advisory_plan_rejected']is False
  unknownpasses+=bool(q['unknown_requirement_indices'])
assert len(checks)==30 and len(conflicts)==2 and unknownpasses==14
assert [z['plan_index']for z in conflicts]==[0,15]
join={k:vp[k]==lp[k]for k in ('sources','inputs','source_contract','runtime','limits','resource_rule')};assert all(join.values())
metrics=[]
for mode,R,d in [('visible',base,vd),('literal',lit,ld)]:
 metrics.append({'mode':mode,'plan':ref(R/'ROOT-plan-v1.json'),'disposition':ref(R/'ROOT-disposition-v1.json'),'native_ns':d['native_launch_to_postprobe_ns'],'peak_bytes':d['aggregate_B_bytes'],'full_receiver_record':d['receiver_probe_record_complete'],'phases':d['phase_observations'],'observed_head_conflicts':None if mode=='visible' else 2,'observed_offers':None if mode=='visible' else 0,'observed_family_placements':None if mode=='visible' else 0,'observed_engine_status':None if mode=='visible'else e['status'],'root_restored':None if mode=='visible'else True,'unavailable_is_not_zero':True})
result={'schema':'ROOT-head-gated-receiver-saved-summary-v1','arms':metrics,'matched_declared_metadata':join,'matched_actual_receiver_or_planlist_proved':False,'original_model_sources':17,'original_model_inputs':2,'current_executable_sources':22,'current_executable_inputs':10,'required_rows':24,'maximum_nodes':2,'inventory_reused':True,'prior_inventory_native_ns':5642960000,'literal':{'expanded':ref(lit/'ROOT-expanded-result-v1.json'),'accounting':pr['accounting'],'provider_work':pr['work'],'physical_plan':pr['physical_assignment_plan'],'provider_reason':pr['reason'],'engine_counts':e['counts'],'decisions':[v['decision']for v in e['events']if v['kind']=='DECISION'],'provider_report_sha256':digest(pr),'consumer_receipt_sha256':digest(cr),'root_restored':True,'conflicts':conflicts,'absent_head_passes':unknownpasses},'inference':{'complete_failure_pair':True,'all_scalar_slots_null':True,'provider_value_and_one_full_copy_completed':True,'callback_return_to_engine_proved':False,'last_phase':'AFTER_PROVIDER','offer_count':None,'native_member_checks':None,'engine_decisions':None,'whole_provider_record':None,'failure_active_frame_identified':False,'no_reexecution':True},'interpretation':'The control exercises30coarse planning receipts, rejects2same-row head conflicts, passes28plans including14with absent formula-meta heads, and makes0offers before ordinary fallback/nodecapUNKNOWN. Inference produced a provider value and helpercopy but timed out before the complete receiver record; no offer, selected family, exact branch/state/census/counter or restored root can be inferred from the phase marker. Same declared problem/current code/limits are verified; a matched completed inference comparison is unavailable. No new theorem/usefultransfer/GCTSadvantage/trainedRL is accepted.','scientific_actuals':2,'scientific_replay':False,'new_theorem_accepted':False,'useful_transfer_accepted':False,'GCTS_advantage_claimed':False,'trained_RL_accepted':False,'whole_GCTS_accepted':False}
p=S/'ROOT-head-filter-summary-v1.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'summary':ref(p),'counts_literal':pr['accounting'],'native_ns':[x['native_ns']for x in metrics]}))
