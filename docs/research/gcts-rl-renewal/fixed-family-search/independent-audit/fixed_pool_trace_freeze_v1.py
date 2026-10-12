"""Source/JSON/hash/AST-only freeze, no scientific imports or workloads.

Actual artifact paths are fixed by the separately reviewed producer protocol.
Their delivered bytes are pinned without decoding the mathematical tape/model.
No activation is written and no worker/owner is invoked by this helper.
"""
import ast
import hashlib
import json
import resource
import sys
import time
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PRODUCER=ROOT/'.gcts-active/fixed-family-pool-search-source-20261012'
STATIC=ROOT/'.gcts-active/family-pool-independent-audit-20261012'


def pin(path):
    path=Path(path).resolve();h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):h.update(block)
    return dict(path=str(path),sha256=h.hexdigest(),bytes=path.stat().st_size)


def save(name,value):
    with (HERE/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    began=time.perf_counter()
    if any((HERE/name).exists() for name in ('source-plan-v1.json','audit-plan-v1.json','integration-v1.json')):
        raise ValueError('immutable prior source freeze exists')
    source=json.loads((PRODUCER/'search-plan-v1.json').read_text())
    static=json.loads((STATIC/'audit-plan-v1.json').read_text())
    sources=[pin(HERE/name) for name in ('fixed_pool_trace_audit_v1.py','fixed_pool_trace_owner_v1.py','fixed_pool_trace_freeze_v1.py')]
    library_paths={
        'independent_point':'.gcts-active/hilbert-cluster-full-independent-20261011/full_point_oracle_v1.py',
        'independent_families':'.gcts-active/hilbert-cluster-full-independent-20261011/full_family_registry_v1.py',
        'independent_symbolic':'.gcts-active/hilbert-aggregate-independent-audit-20261011/independent_aggregate_audit_v1.py',
        'independent_expansion':'.gcts-active/hilbert-aggregate-independent-audit-20261011/independent_aggregate_full_v2.py',
        'independent_transactions':'.gcts-active/shared-symbolic-geometry-trace-independent-20261011/geometry_trace_point_v1.py',
        'independent_static_pool':'.gcts-active/family-pool-independent-audit-20261012/family_pool_independent_v1.py',
        'independent_pool_transactions':'.gcts-active/fixed-family-pool-search-source-20261012/fixed_family_pool_trace_oracle_v1.py',
        'independent_positive_certificate':'.gcts-active/receptor-matching-geometry-independent-20261011/positive_certificate_oracle_v1.py'}
    libraries=[dict(role=role,**pin(ROOT/path)) for role,path in library_paths.items()]
    static_roles={v['role']:Path(v['path']) for v in static['inputs']}
    common=('preparation_plan','preparation_evidence','primitive_model','family_projection','source_certificate','source_schemas',
            'prior_point_plan','original_body_plan','master_contract')
    inputs=[dict(role=role,**pin(static_roles[role])) for role in common]
    delivered={
        'producer_plan':PRODUCER/'search-plan-v1.json',
        'producer_outcome':PRODUCER/'search-outcome-v1.json',
        'producer_lifetime':PRODUCER/'search-lifetime-v1.json',
        'producer_supervision':PRODUCER/'search-supervision-v1.json',
        'producer_activation':PRODUCER/'root-activation-v1.json',
        'root_terminal':ROOT/'.gcts-active/fixed-family-pool-search-progress-20261012/search-terminal-v1.json',
        'actual_trace':PRODUCER/'fixed-whole-family-pool-result-v1.json.gz',
        'static_pool_plan':STATIC/'audit-plan-v1.json',
        'static_pool_result':STATIC/'audit-result-v1.json',
        'static_pool_lifetime':STATIC/'audit-lifetime-v1.json',
        'producer_prospective_protocol':PRODUCER/'prospective-audit-protocol-v1.json',
        'producer_source_integration':PRODUCER/'integration-v1.json',
        'prior_independent_numeric_source_review':ROOT/'.gcts-active/family-numeric-source-review-20261012/source-review-v1.json',
        'independent_producer_source_review':ROOT/'.gcts-active/fixed-family-pool-search-arithmetic-source-review-20261012/source-review-v1.json'}
    inputs += [dict(role=role,**pin(path)) for role,path in delivered.items()]
    expected_actual={
        'actual_trace':('32efc494dfc68b037598673b9549009d365ec9198b0acb403fa2076e8e858b1d',112624),
        'producer_outcome':('58f4dd6cbba2f9277b73f0faa8c44781c21271a448c46ef97a1d65554887b2e6',3136),
        'producer_lifetime':('be45e220d4afd83313c6b042be15e3083fb391ec1f76c6cddbe50fd2e7024926',1385)}
    for role,(sha,size) in expected_actual.items():
        actual=pin(delivered[role])
        if actual['sha256']!=sha or actual['bytes']!=size:raise ValueError('ROOT-delivered actual byte mismatch '+role)
    kept={}
    for old,groups in ((source,('sources','inputs','preserved_files')),(static,('sources','libraries','inputs','preserved'))):
        for group in groups:
            for item in old[group]:
                path=Path(item['path']);path=path if path.is_absolute() else ROOT/path
                actual=pin(path)
                if actual['sha256']!=item['sha256'] or actual['bytes']!=item['bytes']:
                    raise ValueError('preserved prerequisite mismatch '+str(path))
                previous=kept.setdefault(str(path.resolve()),actual)
                if previous!=actual:raise ValueError('conflicting prior byte version')
    preserved=sorted(kept.values(),key=lambda p:p['path'])
    parsed=[]
    for row in sources+libraries:
        tree=ast.parse(Path(row['path']).read_text(),filename=row['path'])
        parsed.append(dict(path=row['path'],AST_nodes=sum(1 for _ in ast.walk(tree))))
    observer=pin('/bin/ps');runtime=dict(executable=source['runtime']['executable'],platform=source['runtime']['platform'],
        binary=source['runtime']['binary'],observer=observer)
    if pin(runtime['binary']['path'])!=runtime['binary']:raise ValueError('runtime byte binding')
    outputs={key:str(HERE/name) for key,name in dict(result='audit-result-v1.json',lifetime='audit-lifetime-v1.json',
        stdout='audit-stdout-v1.txt',stderr='audit-stderr-v1.txt').items()}
    if any(Path(path).exists() for path in outputs.values()) or (HERE/'root-activation-v1.json').exists():
        raise ValueError('prospective activation/scientific outputs already exist')
    plan=dict(status='frozen_actual_inputs_pending_ROOT_activation',schema='independent_fixed_family_complete_trace_plan_v1',
        plan_path=str(HERE/'audit-plan-v1.json'),sources=sources,libraries=libraries,inputs=inputs,preserved=preserved,
        runtime=runtime,limits=dict(whole_seconds=180,supervisor_seconds=175,child_seconds=170,peak_bytes=536870912),
        activation_path=str(HERE/'root-activation-v1.json'),worker_path=str(HERE/'fixed_pool_trace_audit_v1.py'),outputs=outputs,
        required_activation_schema='ROOT-independent-fixed-family-trace-activation-v1',
        expected_saved_observation=dict(id='fixed-whole-family-pool',status='finite_exact_point_tiling',events=121,nodes=19,
            attempts=21,branches=18,forced=3,backtracks=0,primitive_rows=24,original_hypotheses=3),
        expected_scope='Saved producer predictions only until complete independent execution. Every121event, complete graph/scheduler/fallback, whole hints and each24 primitive logical command must independently pass.',
        source_authoring_seconds=None,actual_independent_audit_runs=0,scientific_source_imports_by_freezer=0,execution_authorized=False,
        positive_scope='Exact ground guarded incidence consequence with original Gamma retained; blocks empty. No native/compiler/shared-universal palette acceptance.',
        independence='No producer graph/controller/search/order/decoder imported as acceptance. Rebuild whole171/29241 pool from independent libraries, not saved descriptors alone. The old prospective transaction oracle is source-only infrastructure.',
        mutation_scope='Changed event payloads vs independent templates, plus actual rerun of mutated positive certificates and primitive logical commands; not a full mutated-tape/owned-process campaign.',
        costs='All prior preparation/static acceptance/source/readiness/search costs are additional. New independent body/point/pool/domain/trace/proof/control/import/serialization/reap lifetime charged separately; saved implementation timings not independently reproduced.',
        resource_scope='Owned direct-child wait4, child alarm, owner signal/deadline, RSS watchdog and kernel peak rejection; no OS soft-cap theorem. ROOT full process/receipt startup accounting additional.',
        producer_resource_caveat='Original producer host peak estimate excludes simultaneous ps RSS; do not upgrade to strict aggregate host cap.',
        failure_scope='Any incomplete prefix, unexpected return, pin failure, resource failure or exception retains UNKNOWN/failure artifacts; no partial trace/proof acceptance and no restart.',
        ROOT_sole_actual_owner_and_publisher=True)
    source_plan=dict(status='immutable_source_only_auditor_ready_not_activated',sources=sources,libraries=libraries,
        actual_input_pins=inputs,preserved_path_count=len(preserved),limits=plan['limits'],outputs=outputs,
        source_authoring_seconds=None,scientific_imports_models_fixtures_replays_checkers_searches_native_training=0,
        source_and_AST_verification_only=True)
    save('source-plan-v1.json',source_plan);save('audit-plan-v1.json',plan)
    archive=HERE/'audit-source-v1.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sources:z.write(p['path'],Path(p['path']).name)
        for name in ('source-plan-v1.json','audit-plan-v1.json'):z.write(HERE/name,name)
    allpins=sources+libraries+inputs+preserved
    readiness=dict(status='source_ready_requires_ROOT_and_independent_full_review_before_activation',plan=pin(HERE/'audit-plan-v1.json'),
        source_plan=pin(HERE/'source-plan-v1.json'),archive=pin(archive),sources=len(sources),libraries=len(libraries),inputs=len(inputs),
        preserved_paths=len(preserved),unique_bound_paths=len({x['path'] for x in allpins}),AST_parsed=parsed,
        metadata_freeze_seconds_before_readiness_write=time.perf_counter()-began,
        metadata_kernel_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        scientific_imports_models_fixtures_replays_checkers_searches_native_training=0,
        prospective_command=[runtime['executable'],'-B',str(HERE/'fixed_pool_trace_owner_v1.py'),str(HERE/'audit-plan-v1.json')],
        activation_written=False)
    save('source-ready-v1.json',readiness)
    files=sources+[pin(HERE/name) for name in ('source-plan-v1.json','audit-plan-v1.json','source-ready-v1.json','audit-source-v1.zip')]
    save('integration-v1.json',dict(status='immutable_source_only_complete_positive_tape_auditor_ready',files=files,
        actual_audits=0,execution_authorized=False,ROOT_sole_actual_owner_and_publisher=True))
    print(json.dumps(readiness,indent=2))


if __name__=='__main__':main()
