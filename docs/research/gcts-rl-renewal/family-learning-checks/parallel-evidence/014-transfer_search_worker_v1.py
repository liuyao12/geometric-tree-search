"""ROOT-owned three-lane context-transfer observation; source only until gates."""
import copy
import json
import signal
import time
from context_compiler_v1 import construct_graph,construct_family_authority
from transfer_runtime_v1 import HERE,ROOT,read,pin,verify,activation,load_life,save_json,save_gzip
from transfer_register_v1 import accepted_static_gate,register_pool
from transfer_fixed_pool_search_v1 import fixed_pool_search

def main():
    started=time.perf_counter();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('170-second whole search child gate')));signal.alarm(170)
    planpath=HERE/'search-plan-v1.json';plan=read(planpath);verify(plan);activation(plan,planpath)
    roles={p['role']:ROOT/p['path'] for p in plan['inputs']}
    compiled=read(roles['compiled_context']);evidence=read(roles['fresh_preparation_evidence'])
    static=read(roles['fresh_static_result']);static_life=read(roles['fresh_static_lifetime'])
    accepted_static_gate(pin(roles['compiled_context']),pin(roles['fresh_preparation_evidence']),static,static_life,plan['fresh_static_gate_pins'])
    if evidence['status']!='complete_fresh_context_preparation_pending_independent_static_audit' or compiled['schema']!='closed-recipient-context-transfer-v1':raise ValueError('exact complete fresh preparation')
    projection=read(roles['complete_family_projection']);projection.pop('example',None)
    oldbodyplan=read(roles['old_complete_body_plan']);sourcepins=evidence['group_epoch_payload']['source_bindings']
    originalpins=evidence['original_body_authority_source_bindings']
    imported=time.perf_counter();search,life,proposals=load_life(roles);import_seconds=time.perf_counter()-imported;core=life.core
    expected_modes=['base','fixed-forward','fixed-whole-family-pool']
    if [s['mode'] for s in plan['observations']]!=expected_modes:raise ValueError('frozen three-lane order only')
    observations=[];unexecuted=[]
    for position,spec in enumerate(plan['observations']):
        if time.perf_counter()-started+plan['lane_reservation_seconds']>165:
            unexecuted=[s['id'] for s in plan['observations'][position:]];break
        prepared=time.perf_counter();g=construct_graph(compiled,core)
        if g.model_epoch!=plan['model_epoch']:raise ValueError('same exact fresh model every lane')
        original=construct_family_authority(g,projection,life,originalpins)
        group_authority,groups,registration=register_pool(g,original,projection,proposals,life,evidence,static)
        if core.digest(g.semantic_state())!=core.digest(evidence['initial_graph_semantic_state']):raise ValueError('same fresh initial semantic point state')
        cold_seconds=time.perf_counter()-prepared
        active=groups if spec['mode']=='fixed-whole-family-pool' else []
        active_authority=group_authority if spec['mode']=='fixed-whole-family-pool' else original
        result=fixed_pool_search(g,active_authority,active,life,search,mode=spec['mode'],attempts=spec['attempts'],seconds=spec['seconds'],event_ceiling=spec['event_ceiling'])
        result['decoded_certificate']=search.decode(g,result['point_certificate'],core) if result['point_certificate'] is not None else None
        result.update(observation_id=spec['id'],body_authority_epoch=active_authority.epoch,context_transfer_schema='closed-recipient-context-transfer-v1',
            original_body_authority_epoch=original.epoch,group_authority_epoch=group_authority.epoch,
            available_source_family_count=171,complete_saved_pool_count=len(groups),
            fresh_static_gate=copy.deepcopy(plan['fresh_static_gate_pins']),
            preparation_costs={'fresh_graph_all_body_and_whole_pool_registration_seconds':cold_seconds,**registration})
        path=HERE/(spec['id']+'-result-v1.json.gz');serialization=time.perf_counter();save_gzip(path,result)
        observations.append({'id':spec['id'],'mode':spec['mode'],'status':result['status'],'result':pin(path),
            'attempts':result['attempts'],'events':len(result['events']),'search_seconds':result['seconds'],
            'serialization_seconds':time.perf_counter()-serialization,'cold_setup_seconds':cold_seconds,
            'decoded_candidate':result['decoded_certificate'] is not None})
        # Release complete lane trace before constructing the next cold graph.
        del result,g,original,group_authority,groups,active,active_authority
    verify(plan)
    outcome={'status':'completed_three_context_transfer_observations_pending_independent_trace_audit' if not unexecuted else 'unknown_phase_reservation_budget',
        'plan':pin(planpath),'observations':observations,'unexecuted':unexecuted,'scientific_import_seconds':import_seconds,
        'worker_seconds_before_outcome_write':time.perf_counter()-started,'model_epoch':plan['model_epoch'],
        'target_search_observations':len(observations),'native_queries':0,'native_authority_activated':False,'new_RL_training':False,
        'scope':'One within-library changed-premise recipient, three fixed order controls. Returned candidates need separate complete trace and exact new Gamma/ground symbolic proof acceptance; no native query.'}
    save_json(HERE/'search-outcome-v1.json',outcome);signal.alarm(0);print(json.dumps(outcome),flush=True)
if __name__=='__main__':main()
