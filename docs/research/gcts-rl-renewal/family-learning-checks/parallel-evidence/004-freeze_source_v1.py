"""Metadata-only immutable prospective source freeze; no project imports."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent

def pin(path):
    path=Path(path);h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b)
    try:name=str(path.relative_to(ROOT))
    except ValueError:name=str(path)
    return {'path':name,'sha256':h.hexdigest(),'bytes':path.stat().st_size}

def read(path):return json.loads(Path(path).read_text())
def save(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

def main():
    started=time.perf_counter();nextplan=ROOT/'.gcts-active/fixed-family-transfer-plan-20261012/next-experiment-v1.json'
    proposal=read(nextplan)
    # Literal AST metadata only; this is not compiler/checker execution.
    context_spec={k:proposal[k] for k in ['theory_ast','original_ordered_hypotheses_ast','new_ordered_hypotheses_ast','target_ast','guard_latex','new_sequent_latex']}
    context_spec.update(schema='exact_closed_three_hypothesis_context_spec_v1',source_plan=pin(nextplan),
        premise_occurrence_change=1,expected_new_hypothesis_codes=[11,42,52],expected_target_code=54,
        source_authoring_cost='unmeasured; metadata freeze timer is not source authoring effort')
    save(HERE/'context-spec-v1.json',context_spec)
    old=read(ROOT/'.gcts-active/fixed-family-pool-search-source-20261012/search-plan-v1.json')
    body=read(ROOT/'.gcts-active/hilbert-cluster-lifecycle-20261011/full-language-plan-v3.json')
    roles={p['role']:p for p in old['inputs']};bodyroles={p['role']:p for p in body['inputs']}
    requests={
        'context_spec':HERE/'context-spec-v1.json','declared_next_experiment':nextplan,
        'primitive_model':ROOT/bodyroles['primitive_model']['path'],
        'primitive_logical_audit':ROOT/bodyroles['primitive_logical_audit']['path'],
        'complete_family_projection':ROOT/bodyroles['complete_family_template_projection']['path'],
        'old_complete_body_plan':ROOT/'.gcts-active/hilbert-cluster-lifecycle-20261011/full-language-plan-v3.json',
        'prior_search_helper':ROOT/roles['prior_search_worker']['path'],
        'prior_forward_order':ROOT/roles['prior_unchanged_sibling_import']['path'],
        'prior_decoder':ROOT/roles['prior_unchanged_decoder']['path'],
        'lifecycle_kernel':ROOT/roles['frozen_lifecycle_kernel']['path'],
        'primitive_core':ROOT/bodyroles['frozen_primitive_core']['path'],
        'proposal_module':ROOT/roles['proposal_module']['path'],
        'accepted_old_positive_disposition':ROOT/'.gcts-active/fixed-family-pool-search-progress-20261012/actual-audit-disposition-v1.json',
        'accepted_old_positive_audit_plan':ROOT/'.gcts-active/fixed-family-pool-trace-independent-20261012/audit-plan-v1.json',
        'accepted_old_positive_audit_result':ROOT/'.gcts-active/fixed-family-pool-trace-independent-20261012/audit-result-v1.json',
        'accepted_old_positive_audit_lifetime':ROOT/'.gcts-active/fixed-family-pool-trace-independent-20261012/audit-lifetime-v1.json',
        'accepted_old_positive_root_terminal':ROOT/'.gcts-active/fixed-family-pool-search-progress-20261012/audit-terminal-v1.json',
        'master_contract':ROOT/'docs/basic-tiling-algorithm.md','repository_contract':ROOT/'AGENTS.md'}
    disposition=read(requests['accepted_old_positive_disposition'])
    if disposition['trace_accepted'] is not True or disposition['proof_accepted'] is not True:raise ValueError('prior stale prerequisite remains unresolved')
    # All original56 source/body roles are retained, including aliases, while
    # BodyAuthority's literal pin list later deduplicates identical physical paths.
    inputs=[{'role':role,**pin(path)} for role,path in requests.items()]
    inputs.extend({'role':'old_body_closure_'+p['role'],**{k:p[k] for k in ('path','sha256','bytes')}} for p in body['inputs'])
    sources=[]
    for path in sorted(HERE.glob('*.py')):
        ast.parse(path.read_text(),filename=str(path));sources.append(pin(path))
    direct={p['path']:p for p in sources+inputs}
    preserved={}
    for plan in [old,body]:
        for p in plan['sources']+plan['inputs']+plan['preserved_files']:
            q={k:p[k] for k in ('path','sha256','bytes')}
            if q['path'] in preserved and preserved[q['path']]!=q:raise ValueError('inconsistent prior source history')
            preserved[q['path']]=q
    preserved[str(nextplan.relative_to(ROOT))]=pin(nextplan)
    for path in direct:preserved.pop(path,None)
    for p in list(direct.values())+list(preserved.values()):
        if pin(ROOT/p['path'])!={k:p[k] for k in ('path','sha256','bytes')}:raise ValueError('exact preserved source/input pin changed: '+p['path'])
    runtime={'executable':sys.executable,'platform':sys.platform,'version':sys.version,
        'binary':{'path':str(Path(sys.executable).resolve()),**{k:pin(Path(sys.executable).resolve())[k] for k in ('sha256','bytes')}},
        'process_metadata':{'path':'/bin/ps',**{k:pin(Path('/bin/ps'))[k] for k in ('sha256','bytes')}}}
    observations=[{'id':identifier,'mode':mode,'attempts':128,'seconds':20,'event_ceiling':2000} for identifier,mode in [
        ('complete-primitive-base','base'),('unchanged-fixed-forward','fixed-forward'),('same-inventory-fixed-whole-pool','fixed-whole-family-pool')]]
    phaseprep={'kind':'preparation','worker':'transfer_prepare_worker_v1.py','child_seconds':50,'supervisor_seconds':55,'outer_seconds':60,'bytes':536870912,
        'stdout':'preparation-stdout-v1.txt','stderr':'preparation-stderr-v1.txt','launch':'preparation-launch-v1.json','outcome':'preparation-outcome-v1.json','supervision':'preparation-supervision-v1.json','lifetime':'preparation-lifetime-v1.json'}
    phasesearch={'kind':'search','worker':'transfer_search_worker_v1.py','child_seconds':170,'supervisor_seconds':175,'outer_seconds':180,'bytes':536870912,
        'stdout':'search-stdout-v1.txt','stderr':'search-stderr-v1.txt','launch':'search-launch-v1.json','outcome':'search-outcome-v1.json','supervision':'search-supervision-v1.json','lifetime':'search-lifetime-v1.json'}
    protocol={'status':'source_only_prospective_search_protocol_uninstantiated_actual_gate_pins','schema':'fresh-context-three-lane-handoff-v1',
        'search_plan_template':{'schema':'fresh-context-three-lane-search-plan-v1','status':'uninstantiated_no_actual_gate_pins',
            'observations':observations,'phase':phasesearch,'lane_reservation_seconds':25,
            'activation_basename':'root-search-activation-v1.json','activation_status':'ROOT_authorized_fresh_context_three_lane_search_v1',
            'runtime':runtime,'proposed_outputs':[s['id']+'-result-v1.json.gz' for s in observations]+[phasesearch[k] for k in ['stdout','stderr','launch','outcome','supervision','lifetime']],
            'execution_authorized_by_source_freeze':False,'native_queries':0,'training_runs':0,
            'comparison':'Within-library changed-premise recipient, one repeat per fixed lane; no statistical or balanced speed-ratio claim.',
            'costs':'All new context/preparation/independent static checking, cold per-lane graph/body/pool loading/registration/order/search/serialization/reaping and independent trace checking must be charged; prior bills retained.'},
        'required_actual_static_result':{'status':'passed_independent_fresh_context_family_pool_audit','fields':['plan','compiled_context_pin','preparation_evidence_pin','model_epoch','original_body_authority_epoch','group_authority_epoch','groups_checked'],'counts':{'primitive_license_count':229,'non_assumption_witness_count':226,'source_body_count':171,'single_types':171,'pair_types':29241}},
        'required_actual_static_lifetime':{'status':'passed_owned_independent_fresh_context_family_pool_audit','child_exit':0,'child_reaped':True,'exact_fields':['plan','result']},
        'ROOT_terminal_metadata_contract':{'owner_exit_code':0,'owner_process_terminal_reaped':True,'worker_reaped':True,'lifetime':'exact corresponding pinned lifetime'},
        'handoff':'ROOT invokes metadata-only finalize_search_plan_v1.py after actual preparation and separately accepted fresh static gate; no dummy pins. New search source/plan review and exact root-search activation remain mandatory.',
        'future_trace_gate':'Separate 180/175/170 seconds/512MiB complete literal graph/order/hint/rollback/exhaustion and guarded new-Gamma symbolic certificate audit; raw count/status does not imply acceptance. TraceLimit prefixes may be refused/qualified UNKNOWN.',
        'positive_scope':'All24 primitive rows/strict-prior refs/new3retained hypotheses/Incident(R,n), exact t/m and flattened blocks=[] request. No native activation, theorem-wide or universal claim.',
        'source_authoring_seconds':None}
    save(HERE/'search-protocol-v1.json',protocol)
    inputs.append({'role':'prospective_search_protocol',**pin(HERE/'search-protocol-v1.json')})
    plan={'schema':'fresh-context-family-preparation-plan-v1','status':'source_frozen_preparation_pending_independent_source_review_and_ROOT_activation',
        'sources':sources,'inputs':inputs,'preserved_files':sorted(preserved.values(),key=lambda p:p['path']),
        'runtime':runtime,'phase':phaseprep,'activation_basename':'root-preparation-activation-v1.json','activation_status':'ROOT_authorized_fresh_context_preparation_v1',
        'proposed_outputs':['compiled-context-v1.json.gz','preparation-evidence-v1.json.gz']+[phaseprep[k] for k in ['stdout','stderr','launch','outcome','supervision','lifetime']],
        'prospective_counts':{'recipes':229,'non_assumption_source_records':226,'fresh_assumptions':3,'formula_codes':217,'rows':24,'source_bodies':171,'single_types':171,'pair_types':29241,'actual_new_groups':'unmeasured'},
        'primitive_authority_policy':'Retain exact inactive theory-bound authority; all 226 logical source records remain literal. New contextual licenses/model/source bindings/full-placement/body/pool epochs rebuilt. Prior audit credit does not validate new model bytes.',
        'scheduler':'Unchanged global dead/forced/earliest-generation+degree+row, complete primitive domain, unit occupancy/injective formula markings/ordered remote refs, all root obligations generation0, -1 exterior. No advisory pool degree/exhaustion shortcut.',
        'scope':'Preparation builds exact fresh context/graph and complete fixed single/pair advice only; no Controller/Executor/search/checker/native/training run in this phase. Independent fresh static acceptance required before search.',
        'authoring_seconds':None,'metadata_freeze_seconds_before_plan_write':time.perf_counter()-started,
        'prior_stale_positive_prerequisite':'Resolved only by exact accepted_old_positive_disposition input; historical next-plan wording retained.',
        'execution_authorized_by_source_freeze':False,'actual_models_constructed_by_freeze':0,'actual_preparation_executions_by_freeze':0,'target_searches_by_freeze':0,'native_queries':0}
    save(HERE/'preparation-plan-v1.json',plan)
    oldadapter=ROOT/'.gcts-active/fixed-family-pool-search-source-20261012/fixed_family_pool_adapter_v1.py'
    diff=''.join(difflib.unified_diff(oldadapter.read_text().splitlines(True),(HERE/'transfer_fixed_pool_search_v1.py').read_text().splitlines(True),fromfile=str(oldadapter.relative_to(ROOT)),tofile=str((HERE/'transfer_fixed_pool_search_v1.py').relative_to(ROOT))))
    with (HERE/'fixed-pool-source-diff-v1.txt').open('x') as f:f.write(diff)
    archive=HERE/'sources-v1.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for item in sources:z.write(ROOT/item['path'],arcname=item['path'])
        z.write(HERE/'context-spec-v1.json',arcname=str((HERE/'context-spec-v1.json').relative_to(ROOT)))
        z.write(HERE/'search-protocol-v1.json',arcname=str((HERE/'search-protocol-v1.json').relative_to(ROOT)))
        z.write(HERE/'preparation-plan-v1.json',arcname=str((HERE/'preparation-plan-v1.json').relative_to(ROOT)))
        z.write(HERE/'fixed-pool-source-diff-v1.txt',arcname=str((HERE/'fixed-pool-source-diff-v1.txt').relative_to(ROOT)))
    readiness={'status':'source_only_ready_for_independent_source_review_not_execution','preparation_plan':pin(HERE/'preparation-plan-v1.json'),
        'search_protocol':pin(HERE/'search-protocol-v1.json'),'context_spec':pin(HERE/'context-spec-v1.json'),'source_archive':pin(archive),
        'source_count':len(sources),'input_roles':len(inputs),'preserved_paths':len(preserved),'unique_existing_paths':len(set(p['path'] for p in sources+inputs+list(preserved.values()))),
        'static_checks':'AST and exact source/input/runtime hash reconciliation only; no compiler/helper/scientific imports or functions executed.',
        'preparation_ROOT_command_after_source_review_only':[runtime['executable'],str(HERE/'transfer_outer_v1.py'),'preparation-plan-v1.json'],
        'preparation_activation_basename':'root-preparation-activation-v1.json','preparation_activation_status':plan['activation_status'],
        'future_search_activation_basename':'root-search-activation-v1.json','future_search_activation_status':protocol['search_plan_template']['activation_status'],
        'limitations':['New model/license/body/domain/pool counts and epochs are predictions, not acceptance.','Three-lane actual plan cannot be frozen until actual fresh preparation/static gates and reaped ROOT receipts exist.','Source authority remains inactive and finite/contextual; native/compiler/universal Wang correspondence stays open.','Canonical single/pair embeddings remain incomplete advice over complete primitive fallback; no winning subset or authored proof supplied.','Source authoring unmeasured; owned clocks exclude their own final receipt write unless ROOT separately records full process.','External RSS and final kernel peak estimates are not OS hard or aggregate host limits.'],
        'scientific_execution':False,'models':0,'checkers':0,'fixtures':0,'searches':0,'training':0,'native_queries':0}
    save(HERE/'source-ready-v1.json',readiness)
    files=[pin(p) for p in sorted(HERE.iterdir()) if p.is_file()]
    integration={'status':readiness['status'],'files':files,'source_ready':pin(HERE/'source-ready-v1.json'),'preparation_plan':pin(HERE/'preparation-plan-v1.json'),'scientific_execution':False}
    save(HERE/'integration-v1.json',integration)
    print(json.dumps({'integration':pin(HERE/'integration-v1.json'),'source_ready':pin(HERE/'source-ready-v1.json'),'preparation_plan':pin(HERE/'preparation-plan-v1.json'),'source_count':len(sources),'input_roles':len(inputs),'preserved_paths':len(preserved),'scientific_execution':False}))
if __name__=='__main__':main()
