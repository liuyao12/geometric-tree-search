"""Saved JSON joins and presentation fields only; never replays scientific code."""
import hashlib
import json
from pathlib import Path

S=Path('/private/tmp/gcts-receiver-inference-ROOT-source-20261017')
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def ref(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
arms=[];raws=[]
for mode in ('visible','literal'):
    R=Path('/private/tmp/gcts-receiver-inference-'+mode+'-ROOT-20261017')
    x=json.loads((R/'ROOT-expanded-result-v1.json').read_bytes())
    d=json.loads((R/'ROOT-disposition-v1.json').read_bytes())
    p=json.loads((R/'ROOT-plan-v1.json').read_bytes())
    r=x['receiver_probe']['receiver'];e=r['engine_result']
    assert d['actual_closed'] and d['all_reaped'] and d['native_resources_qualified'] and d['complete_wire_verified']
    assert d['receiver_probe_record_complete'] and not d['logical_proof_accepted']
    assert x['sources']==p['sources'] and x['inputs']==p['inputs']
    assert e['status']=='UNKNOWN' and e['reason']=='node ceiling; no exhausted conclusion'
    assert e['root_restored'] and e['stack_restored'] and r['root_restored']
    assert e['counts']['family_choices']==0 and e['counts']['family_canonical_choices']==1
    decisions=[v['decision'] for v in e['events'] if v['kind']=='DECISION']
    assert decisions==[{'kind':'BRANCH','row':23},{'kind':'DEAD','row':0}]
    envelopes=[q for v in e['events'] for q in v.get('receipts',[]) if q.get('provider_report') is not None]
    assert len(envelopes)==1
    env=envelopes[0];pr=env['provider_report'];cr=env['consumer_receipt']
    assert len(r['observations']['provider_calls'])==len(r['observations']['consumer_calls'])==1
    assert r['observations']['provider_calls'][0]['report_sha256']==digest(pr)
    assert r['observations']['consumer_calls'][0]['receipt_sha256']==digest(cr)
    assert cr['status']=='UNKNOWN' and cr['selection'] is None and cr['checks']==[]
    assert pr['offers']==[] and pr['batch']['instances']==[] and pr['batch']['status']=='UNKNOWN'
    assert pr['checked_state']==r['initial_state'] and pr['decision']==decisions[0]
    ledger=dict(env['prototype_census'])
    assert all(ledger[k]==v for k,v in pr['prototype_census'])
    conflicts=[]
    plans=pr['physical_assignment_plan']['plans']
    for record in pr['records']:
        for match in record['matches']:
            for grounding in match['groundings']:
                pf=grounding['preflight']
                if pf is not None and pf['status']=='INCOMPATIBLE_ASSIGNMENT':
                    conflicts.append({'plan':plans[match['plan_index']],
                        'family_id':record['record']['family_id'],
                        'substitution':grounding['environment']['substitution'],
                        'port_bindings':grounding['port_bindings'],
                        'preflight':pf})
    arm={'mode':mode,'disposition':ref(R/'ROOT-disposition-v1.json'),
        'expanded':ref(R/'ROOT-expanded-result-v1.json'),'plan':ref(R/'ROOT-plan-v1.json'),
        'native_seconds':d['native_launch_to_postprobe_ns']/1e9,
        'native_ns':d['native_launch_to_postprobe_ns'],'peak_bytes':d['aggregate_B_bytes'],
        'engine_status':e['status'],'engine_reason':e['reason'],'engine_counts':e['counts'],
        'decisions':decisions,'provider_reason':pr['reason'],'provider_work':pr['work'],
        'accounting':pr['accounting'],'physical_plan':pr['physical_assignment_plan'],
        'frozen_open_pool_sha256':r['frozen_open_pool_sha256'],
        'provider_report_sha256':digest(pr),'consumer_receipt_sha256':digest(cr),
        'provider_report_types':len(pr['prototype_census']),
        'engine_census_at_consumer':len(ledger),'root_restored':True,
        'new_theorems':0,'family_offers':0,'family_placements':0,
        'native_point_conflicts':conflicts,'scientific_replay':False}
    arms.append(arm);raws.append((x,r,pr,e))
a,b=raws
matches={'same_sources':a[0]['sources']==b[0]['sources'],
 'same_inputs':a[0]['inputs']==b[0]['inputs'],
 'same_initial_state':a[1]['initial_state']==b[1]['initial_state'],
 'same_pool':a[1]['frozen_open_pool_sha256']==b[1]['frozen_open_pool_sha256'],
 'same_whole_physical_plan':a[2]['physical_assignment_plan']==b[2]['physical_assignment_plan'],
 'same_actual_branch':a[2]['decision']==b[2]['decision'],
 'same_fallback_placement':[v['key']for v in a[3]['events']if v['kind']=='PLACE']==[v['key']for v in b[3]['events']if v['kind']=='PLACE']}
assert all(matches.values())
assert len(arms[0]['native_point_conflicts'])==1 and len(arms[1]['native_point_conflicts'])==0
conflict=arms[0]['native_point_conflicts'][0]
assert conflict['preflight']['reason']=='literal_repeated_or_remote_formula_mark_conflict'
assert conflict['preflight']['row']==23 and conflict['preflight']['node_id']=='n1'
assert len(conflict['preflight']['membership'])==2
assert all(x['membership']['status']=='MEMBER' for x in conflict['preflight']['membership'])
assert all('membership'in x for x in conflict['preflight']['membership'])
result={'schema':'ROOT-receiver-pair-saved-interpretation-v1','arms':arms,'matched_data_joins':matches,
 'current_code_native_windows_qualified':True,'original_rows':24,'maximum_engine_nodes':2,
 'inventory_reused':True,'prior_inventory_cost_ns':5642960000,
 'target':a[2]['branch_output_receptor'],
 'interpretation':'Inference exercised joint syntax matching at a real receiver but made no fully checked current family offer. It hit its own1M work cap in the first abstract physical layout. Literal binding completed its planned prefix with no match. Both used the same canonical fallback and reached DEADrow0 before root restoration and the2-node ceiling. No current-family transfer, theorem, proof-search advantage or learned-marking sample from UNKNOWN is accepted.',
 'next_direction':'Known outer template constructors can provide coarse point markings to reject an incompatible row assignment before enumerating environments. Proposed gate remains Source-only and unmeasured.',
 'logical_proof_accepted':False,'useful_transfer_accepted':False,'whole_engine_qualified':False,
 'complete_GCTS_model_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,
 'scientific_replay':False}
p=S/'ROOT-receiver-pair-interpretation-v1.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'summary':ref(p),'matched_data_joins':matches,'offers':[x['family_offers']for x in arms],
                 'native_seconds':[x['native_seconds']for x in arms],'point_conflicts':len(arms[0]['native_point_conflicts'])}))
