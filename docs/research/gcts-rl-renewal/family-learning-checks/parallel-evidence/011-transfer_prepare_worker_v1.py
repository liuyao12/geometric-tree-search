"""ROOT-owned prospective fresh compile/body/domain/pool preparation only."""
import copy
import hashlib
import json
import signal
import time
from context_compiler_v1 import compile_context,construct_graph,construct_family_authority
from transfer_runtime_v1 import HERE,ROOT,read,pin,verify,activation,load_life,save_json,save_gzip

def main():
    started=time.perf_counter();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('50-second complete preparation child gate')));signal.alarm(50)
    planpath=HERE/'preparation-plan-v1.json';plan=read(planpath);verify(plan);activation(plan,planpath)
    roles={p['role']:ROOT/p['path'] for p in plan['inputs']}
    old=read(roles['accepted_old_positive_disposition'])
    if old.get('trace_accepted') is not True or old.get('proof_accepted') is not True:raise ValueError('prior actual positive gate prerequisite unresolved')
    audit=read(roles['primitive_logical_audit']);source=read(roles['primitive_model'])
    if audit['status']!='passed_independent_finite_static_symbolic_and_aggregate_audit':raise ValueError('old exact source logical inventory audit required')
    sourcepin=pin(roles['primitive_model'])
    if sourcepin not in [e['current_pin'] for e in audit['independent_serialization_correspondence']]:raise ValueError('old audit does not bind exact source model bytes')
    bindings={p['role']:{k:p[k] for k in ('path','sha256','bytes')} for p in plan['inputs']}
    bindings['fresh_context_compiler_plan']=pin(planpath)
    sourcepins=[pin(planpath)]+[{k:p[k] for k in ('path','sha256','bytes')} for p in plan['sources']+plan['inputs']]
    compile_started=time.perf_counter();compiled=compile_context(source,read(roles['context_spec']),bindings,sourcepins)
    compile_seconds=time.perf_counter()-compile_started
    imported=time.perf_counter();search,life,proposals=load_life(roles);import_seconds=time.perf_counter()-imported;core=life.core
    constructed=time.perf_counter();graph=construct_graph(compiled,core);graph_seconds=time.perf_counter()-constructed
    projection=read(roles['complete_family_projection']);projection.pop('example',None)  # Decoded then discarded; no witness used as guidance.
    oldbodyplan=read(roles['old_complete_body_plan'])
    oldbodypins=[{k:p[k] for k in ('path','sha256','bytes')} for p in oldbodyplan['inputs']]
    authority_started=time.perf_counter();original=construct_family_authority(graph,projection,life,oldbodypins+sourcepins)
    authority_seconds=time.perf_counter()-authority_started
    grammar_started=time.perf_counter();counters={}
    deadline=min(started+45,grammar_started+30)
    authority,groups,anchors,interfaces=proposals.prepare(graph,original,projection,life,sourcepins,deadline,counters)
    preparation_seconds=time.perf_counter()-grammar_started
    domain_started=time.perf_counter();rows=[];total=0
    for row in range(24):
        if time.perf_counter()>=started+45:raise TimeoutError('full initial domain census preparation cutoff; no accepted partial census')
        stream=hashlib.sha256();count=0
        for key in graph.candidates(row):
            t,m=graph.point_data(key);stream.update((core.canonical({'key':key.data(),'t':t,'m':m})+'\n').encode('utf8'));count+=1
        if count!=graph.domains[row].count:raise AssertionError('complete initial iterator/factor census mismatch')
        rows.append({'row':row,'count':count,'key_t_m_stream_sha256':stream.hexdigest()});total+=count
    domain_seconds=time.perf_counter()-domain_started
    # Prospective exact compiled payload and full preparation evidence; new audit pending.
    modelpath=HERE/'compiled-context-v1.json.gz';save_gzip(modelpath,compiled)
    evidence={'schema':'fresh-context-whole-family-pool-preparation-v1','status':'complete_fresh_context_preparation_pending_independent_static_audit',
        'plan':pin(planpath),'sources':plan['sources'],'inputs':plan['inputs'],'compiled_context_pin':pin(modelpath),
        'context':copy.deepcopy(graph.context),'context_id':graph.context_id,'formula_codes':graph.formulas,'formula_registry_sha256':graph.registry_sha,
        'primitive_authority_epoch':graph.authority_epoch,'model_epoch':graph.model_epoch,'graph_binding':life.graph_binding(graph),
        'initial_graph_semantic_state':graph.semantic_state(),'complete_initial_domains':rows,'initial_complete_candidate_count':total,
        'original_body_authority_epoch':original.epoch,'original_body_authority_graph_text':json.loads(original.graph_text),
        'original_body_authority_source_bindings':json.loads(original.source_text),
        'all_source_bodies':[{'name':n,'body':json.loads(t)} for n,t in original.bodies],
        'declared_interfaces':list(interfaces),'declared_interface_projection_sha256':core.digest(interfaces),
        'root_anchors':list(anchors),'group_authority_epoch':authority.epoch,'group_epoch_payload':authority.epoch_payload(),
        'groups':groups,'preparation_counters':counters,
        'costs':{'context_compilation_seconds':compile_seconds,'scientific_import_seconds':import_seconds,
                'graph_construction_seconds':graph_seconds,'all_body_registration_seconds':authority_seconds,
                'complete_pool_preparation_seconds':preparation_seconds,'complete_initial_domain_census_seconds':domain_seconds},
        'licenses':229,'non_assumption_witnesses':226,'source_body_count':171,'recipes':229,'formulas':217,'height':24,
        'model_constructions':1,'recipient_seed_placements':3,'Controller_calls':0,'Executor_calls':0,
        'target_searches':0,'logical_checker_calls':0,'native_queries':0,'new_RL_training':False,
        'authority_scope':'Fresh context-bound finite point/body/pool preparation; old source receipts are provenance. Independent new-model/domain/pool acceptance is mandatory before search.'}
    evidencepath=HERE/'preparation-evidence-v1.json.gz';save_gzip(evidencepath,evidence)
    verify(plan)
    outcome={'status':'completed_fresh_context_preparation_pending_independent_gate','plan':pin(planpath),
        'compiled_context':pin(modelpath),'preparation_evidence':pin(evidencepath),'model_epoch':graph.model_epoch,
        'group_authority_epoch':authority.epoch,'original_body_authority_epoch':original.epoch,
        'complete_pool_group_count':len(groups),'single_types':counters['single_types_visited'],'pair_types':counters['pair_types_visited'],
        'candidate_count':total,'model_constructions':1,'target_searches':0,'native_queries':0,'new_RL_training':False,
        'worker_seconds_before_outcome_write':time.perf_counter()-started,'costs':evidence['costs']}
    save_json(HERE/'preparation-outcome-v1.json',outcome);signal.alarm(0);print(json.dumps(outcome),flush=True)
if __name__=='__main__':main()
