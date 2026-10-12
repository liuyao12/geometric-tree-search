"""Metadata-only source freeze and future actual-input plan finalizer.

No scientific imports, model decoding, fixtures, checker calls or activation.
`source` freezes implementation/prerequisites before execution. Separately
ROOT may use `bind-static` or `bind-trace` only after owned actual producer bytes
exist; this writes a new immutable plan, never invokes an owner or worker.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PRODUCER=ROOT/'.gcts-active/fixed-family-transfer-source-v1-20261012'


def pin(path):
    path=Path(path).resolve();h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(65536),b''):h.update(chunk)
    return dict(path=str(path),sha256=h.hexdigest(),bytes=path.stat().st_size)


def wire(path):
    result=pin(path);result['path']=str(Path(path).resolve().relative_to(ROOT));return result


def read(path):return json.loads(Path(path).read_text())


def save(name,value):
    with (HERE/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def checked_closure(plans):
    result={}
    for old,names in plans:
        for name in names:
            for item in old[name]:
                path=Path(item['path']);path=path if path.is_absolute() else ROOT/path
                actual=pin(path)
                if actual['sha256']!=item['sha256'] or actual['bytes']!=item['bytes']:raise ValueError('old pin mismatch '+str(path))
                previous=result.setdefault(actual['path'],actual)
                if previous!=actual:raise ValueError('conflicting preserved versions')
    return sorted(result.values(),key=lambda r:r['path'])


def terminal_contract(stage):
    kind='preparation' if stage=='static' else 'search';seconds=60 if stage=='static' else 180
    outcome='completed_fresh_context_preparation_pending_independent_gate' if stage=='static' else 'completed_three_context_transfer_observations_pending_independent_trace_audit'
    return dict(required_fields={
        'producer_outcome':dict(status=outcome,native_queries=0,new_RL_training=False),
        'producer_lifetime':dict(status='passed_full_fresh_context_'+kind+'_lifetime',phase_kind=kind,
            supervisor_exit=0,supervisor_reaped=True,worker_reaped_confirmed=True),
        'producer_supervision':dict(status='passed_owned_fresh_context_'+kind,phase_kind=kind,child_exit=0,child_reaped=True),
        'producer_activation':dict(status='ROOT_authorized_fresh_context_'+('preparation_v1' if stage=='static' else 'three_lane_search_v1')),
        'root_terminal':dict(owner_exit_code=0,owner_process_terminal_reaped=True,worker_reaped=True)},
        nested_pin_bindings=[dict(record=name,field='plan',role='producer_plan',path_encoding='relative')
            for name in ('producer_outcome','producer_lifetime','producer_supervision','producer_activation')]+[
            dict(record='producer_lifetime',field='supervision',role='producer_supervision',path_encoding='relative'),
            dict(record='producer_supervision',field='outcome',role='producer_outcome',path_encoding='relative'),
            dict(record='producer_supervision',field='root_activation',role='producer_activation',path_encoding='relative'),
            dict(record='root_terminal',field='lifetime',role='producer_lifetime',path_encoding='relative')],
        ceilings={'producer_lifetime':dict(full_supervisor_seconds_including_receipt_write=seconds,conservative_host_peak_bytes=536870912)})


def source():
    started=time.perf_counter()
    if (HERE/'source-plan-v1.json').exists():raise ValueError('immutable source freeze exists')
    producer=read(PRODUCER/'preparation-plan-v1.json')
    old_trace=read(ROOT/'.gcts-active/fixed-family-pool-trace-independent-20261012/audit-plan-v1.json')
    preserved=checked_closure([(producer,('sources','inputs','preserved_files')),
        (old_trace,('sources','libraries','inputs','preserved'))])
    sources=[pin(p) for p in sorted(HERE.glob('*.py'))]
    library_paths={
        'independent_point':'.gcts-active/hilbert-cluster-full-independent-20261011/full_point_oracle_v1.py',
        'independent_families':'.gcts-active/hilbert-cluster-full-independent-20261011/full_family_registry_v1.py',
        'independent_symbolic':'.gcts-active/hilbert-aggregate-independent-audit-20261011/independent_aggregate_audit_v1.py',
        'independent_expansion':'.gcts-active/hilbert-aggregate-independent-audit-20261011/independent_aggregate_full_v2.py',
        'independent_transactions':'.gcts-active/shared-symbolic-geometry-trace-independent-20261011/geometry_trace_point_v1.py',
        'independent_static_pool':'.gcts-active/family-pool-independent-audit-20261012/family_pool_independent_v1.py',
        'independent_fixed_forward':'.gcts-active/shared-symbolic-geometry-trace-independent-20261011/geometry_trace_order_v1.py',
        'independent_positive_certificate':'.gcts-active/receptor-matching-geometry-independent-20261011/positive_certificate_oracle_v1.py',
        'independent_context':str((HERE/'transfer_context_oracle_v1.py').relative_to(ROOT)),
        'independent_trace':str((HERE/'transfer_trace_oracle_v1.py').relative_to(ROOT)),
        'independent_pool_transactions':str((HERE/'transfer_transactions_oracle_v1.py').relative_to(ROOT)),
        'independent_worker':str((HERE/'transfer_independent_worker_v1.py').relative_to(ROOT))}
    libraries=[dict(role=role,**pin(ROOT/path)) for role,path in library_paths.items()]
    prior_roles={r['role']:ROOT/r['path'] for r in producer['inputs']}
    requested={
        'preparation_plan':PRODUCER/'preparation-plan-v1.json','preparation_source_integration':PRODUCER/'integration-v1.json',
        'preparation_protocol':PRODUCER/'search-protocol-v1.json','context_spec':prior_roles['context_spec'],
        'donor_primitive_model':prior_roles['primitive_model'],'family_projection':prior_roles['complete_family_projection'],
        'original_body_plan':prior_roles['old_complete_body_plan'],
        'source_certificate':prior_roles['old_body_closure_source_constant_transport_certificate'],
        'source_schemas':prior_roles['old_body_closure_exact_three_source_schemas'],
        'master_contract':prior_roles['master_contract'],'repository_contract':prior_roles['repository_contract'],
        'accepted_old_positive_disposition':prior_roles['accepted_old_positive_disposition'],
        'own_preparation_source_review':HERE/'preparation-source-review-v1.json'}
    inputs=[dict(role=role,**pin(path)) for role,path in requested.items()]
    parsed=[]
    for item in {r['path']:r for r in sources+libraries}.values():
        tree=ast.parse(Path(item['path']).read_text(),filename=item['path'])
        parsed.append(dict(path=item['path'],AST_nodes=sum(1 for _ in ast.walk(tree))))
    runtime=dict(executable=producer['runtime']['executable'],platform=producer['runtime']['platform'],
        binary=producer['runtime']['binary'],observer=producer['runtime']['process_metadata'])
    for name in ('binary','observer'):
        if pin(runtime[name]['path'])!=runtime[name]:raise ValueError('exact runtime '+name)
    limits=dict(whole_seconds=180,supervisor_seconds=175,child_seconds=170,peak_bytes=536870912)
    protocol=dict(schema='fresh_transfer_independent_two_stage_protocol_v1',
        status='source_only_prospective_gate_no_actual_inputs_or_activation',
        stages={stage:dict(limits=limits,terminal_contract=terminal_contract(stage),
            expected_result_status='passed_independent_fresh_context_family_pool_audit' if stage=='static' else 'passed_independent_fresh_context_complete_trace_audit',
            expected_owner_status='passed_owned_independent_fresh_context_family_pool_audit' if stage=='static' else 'passed_owned_independent_fresh_context_complete_trace_audit',
            activation_schema='ROOT-independent-fresh-context-'+stage+'-activation-v1') for stage in ('static','trace')},
        grammar=dict(rows=24,formulas=217,licenses=229,non_assumption_witnesses=226,fresh_context_assumptions=3,
            source_bodies=171,single_types=171,ordered_pair_types=29241),
        static_scope='Independent exact new Gamma/context/license identity reconstruction and logical229-rule licensing; recursive all171 conditional source proofs; complete canonical pool; every initial raw primitive candidate/point/mark in all24 rows.',
        trace_scope='Three recorded complete DFS tapes; all reached raw candidate graphs/order permutations/scheduler/whole hints/paired rollback/exhaustion. Any positive: all24 primitive lines/full IDs/new original Gamma/target/flat blocks=[] exact symbolic check.',
        expected_observations=read(PRODUCER/'search-protocol-v1.json')['search_plan_template']['observations'],
        actual_inputs='Root-owned complete preparation plus separate fresh static PASS; later separate three-lane actual producer. No missing-file or old receipt stand-in; immutable actual-input plans frozen after real bytes supplied.',
        authority_scope='Retained inactive theory-only primitive authority. All new context/model/body/pool/full-placement bindings checked; structurally certified source bodies, no fresh native acceptance.',
        test_scope='14 prospective changed context payloads; per-group controls from independent pool oracle; later actual per-event templates and positive certificate/logical mutants. Counts are source predictions until actual gates run.',
        costs='Source authoring unmeasured; metadata freeze clock separate. Fresh production/preparation/static audit, cold lane setup/search, and full trace audit/import/domain/body/serialization/reap clocks all additional. Prior failures/unknowns retained.',
        limitations=['Within-library recipient/premise-pattern transfer only, not unseen theorem-family generalization.',
            'Canonical single/pair proposal grammar is bounded incomplete advice; complete primitive universe supplies graph degrees/exhaustion/fallback.',
            'No target proof word or authored example acceptance; compact example decoded then discarded.',
            'Known pinned standard JSON only; no adversarial strict-parser theorem.',
            'Owner sampled RSS plus child/kernel peaks is retrospective enforcement, not an OS hard cap; ROOT outer final process/receipt lifetime additional.',
            'UNKNOWN/unexecuted/truncated evidence never becomes exhaustion or a mathematical rejection; native/shared universal palette remains open.'],
        execution_authorized=False,actual_static_runs=0,actual_trace_runs=0,models=0,fixtures=0,checkers=0,searches=0,native_queries=0,training=0,
        ROOT_sole_actual_owner_and_publisher=True)
    save('prospective-protocol-v1.json',protocol)
    inputs.append(dict(role='prospective_independent_protocol',**pin(HERE/'prospective-protocol-v1.json')))
    plan=dict(schema='fresh_transfer_independent_source_closure_v1',status='immutable_source_only_requires_actual_input_freeze_and_ROOT_review',
        sources=sources,libraries=libraries,inputs=inputs,preserved=preserved,runtime=runtime,limits=limits,
        protocol=pin(HERE/'prospective-protocol-v1.json'),source_authoring_seconds=None,
        actual_activation_written=False,scientific_imports_or_functions=0,models=0,fixtures=0,checkers=0,searches=0,native_queries=0,training=0)
    save('source-plan-v1.json',plan)
    archive=HERE/'sources-v1.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for item in sources:z.write(item['path'],Path(item['path']).name)
        for name in ('source-plan-v1.json','prospective-protocol-v1.json','preparation-source-review-v1.json'):z.write(HERE/name,name)
    allpins=sources+libraries+inputs+preserved
    ready=dict(status='source_only_ready_for_ROOT_and_independent_review_not_execution',source_plan=pin(HERE/'source-plan-v1.json'),
        protocol=pin(HERE/'prospective-protocol-v1.json'),archive=pin(archive),source_count=len(sources),library_roles=len(libraries),
        input_roles=len(inputs),preserved_paths=len(preserved),unique_bound_paths=len({r['path'] for r in allpins}),AST_checks=parsed,
        metadata_seconds_before_readiness_write=time.perf_counter()-started,
        metadata_kernel_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        actual_inputs_pinned=False,activation_written=False,scientific_imports_or_functions=0,ROOT_sole_actual_owner=True)
    save('source-ready-v1.json',ready)
    files=sources+[pin(HERE/name) for name in ('source-plan-v1.json','prospective-protocol-v1.json','preparation-source-review-v1.json','source-ready-v1.json','sources-v1.zip')]
    save('integration-v1.json',dict(status=ready['status'],files=files,source_plan=ready['source_plan'],
        scientific_execution=False,actual_input_plans_uninstantiated=True))
    print(json.dumps(dict(integration=pin(HERE/'integration-v1.json'),source_plan=ready['source_plan'],sources=len(sources),
        libraries=len(libraries),inputs=len(inputs),preserved=len(preserved),unique_bound_paths=ready['unique_bound_paths'],scientific_execution=False)))


def bind(stage,args):
    """Metadata-only actual raw-byte handoff, never worker/model/tape decode."""
    frozen=read(HERE/'source-plan-v1.json');protocol=read(HERE/'prospective-protocol-v1.json')
    checked_closure([(frozen,('sources','libraries','inputs','preserved'))])
    input_map={r['role']:copy.deepcopy(r) for r in frozen['inputs']}
    def add(role,path):input_map[role]=dict(role=role,**pin(path))
    add('compiled_context',PRODUCER/'compiled-context-v1.json.gz')
    add('preparation_evidence',PRODUCER/'preparation-evidence-v1.json.gz')
    kind='preparation' if stage=='static' else 'search'
    for role,name in [('producer_plan',kind+'-plan-v1.json'),('producer_outcome',kind+'-outcome-v1.json'),
            ('producer_lifetime',kind+'-lifetime-v1.json'),('producer_supervision',kind+'-supervision-v1.json'),
            ('producer_activation','root-'+kind+'-activation-v1.json')]:add(role,PRODUCER/name)
    if not args.producer_root_terminal:raise ValueError('actual ROOT producer terminal required')
    add('root_terminal',args.producer_root_terminal)
    terminal=read(args.producer_root_terminal)
    for name,value in dict(owner_exit_code=0,owner_process_terminal_reaped=True,worker_reaped=True).items():
        if terminal.get(name)!=value:raise ValueError('actual ROOT terminal field '+name)
    if terminal['lifetime']!=wire(PRODUCER/(kind+'-lifetime-v1.json')):raise ValueError('exact ROOT terminal lifetime')
    if stage=='trace':
        for name in ('plan','result','lifetime','root_terminal'):
            path=getattr(args,'static_'+name)
            if not path:raise ValueError('actual fresh static '+name+' required')
            add('fresh_static_'+name,path)
        result=read(args.static_result);life=read(args.static_lifetime)
        if (result['status']!='passed_independent_fresh_context_family_pool_audit'
                or life['status']!='passed_owned_independent_fresh_context_family_pool_audit'
                or life['child_exit']!=0 or life['child_reaped'] is not True):raise ValueError('actual fresh static gates required')
        if result['compiled_context_pin']!=wire(PRODUCER/'compiled-context-v1.json.gz') or result['preparation_evidence_pin']!=wire(PRODUCER/'preparation-evidence-v1.json.gz'):
            raise ValueError('same raw new-model/pool inputs')
        if result['plan']!=wire(args.static_plan) or life['plan']!=result['plan'] or life['result']!=wire(args.static_result):raise ValueError('same static plan/result/lifetime')
        for number,spec in enumerate(protocol['expected_observations']):add('actual_trace_'+str(number),PRODUCER/(spec['id']+'-result-v1.json.gz'))
    for role,path in [('source_frozen_independent_plan',HERE/'source-plan-v1.json'),('source_frozen_independent_archive',HERE/'sources-v1.zip')]:add(role,path)
    output_names=dict(result=stage+'-audit-result-v1.json',lifetime=stage+'-audit-lifetime-v1.json',
        stdout=stage+'-audit-stdout-v1.txt',stderr=stage+'-audit-stderr-v1.txt')
    outputs={name:str(HERE/path) for name,path in output_names.items()}
    activation=HERE/('root-'+stage+'-audit-activation-v1.json')
    if activation.exists() or any(Path(path).exists() for path in outputs.values()):raise ValueError('no existing activation/output or rerun')
    name=stage+'-audit-plan-v1.json';contract=protocol['stages'][stage]
    plan=dict(schema='fresh_transfer_independent_actual_'+stage+'_plan_v1',status='frozen_actual_inputs_pending_ROOT_activation',
        plan_path=str(HERE/name),stage=stage,sources=frozen['sources'],libraries=frozen['libraries'],
        inputs=list(input_map.values()),preserved=frozen['preserved'],runtime=frozen['runtime'],limits=contract['limits'],
        worker_path=str(HERE/'transfer_independent_worker_v1.py'),outputs=outputs,activation_path=str(activation),
        required_activation_schema=contract['activation_schema'],required_result_status=contract['expected_result_status'],
        required_owner_success_status=contract['expected_owner_status'],producer_terminal_contract=contract['terminal_contract'],
        actual_execution_authorized=False,metadata_finalizer_scientific_imports_models_checkers_fixtures_search_native_training=0,
        ROOT_sole_actual_owner=True,source_authoring_seconds=None,
        positive_scope='Within-library exact changed Gamma ground consequence only; no native/universal closure.',
        future_ROOT_command=[frozen['runtime']['executable'],'-B',str(HERE/'transfer_independent_owner_v1.py'),str(HERE/name)])
    save(name,plan)
    print(json.dumps(dict(status='actual_raw_input_plan_frozen_requires_ROOT_and_independent_review',plan=pin(HERE/name),
        activation_written=False,scientific_execution=False)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['source','bind-static','bind-trace'])
    parser.add_argument('--producer-root-terminal')
    for name in ('plan','result','lifetime','root_terminal'):parser.add_argument('--static-'+name.replace('_','-'))
    args=parser.parse_args()
    if args.mode=='source':source()
    else:bind(args.mode.split('-')[1],args)


if __name__=='__main__':main()
