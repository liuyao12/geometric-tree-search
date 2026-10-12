"""Metadata-only prospective freeze. No scientific module imports or calls.

Reads JSON plans/terminal receipts, hashes bytes and parses Python ASTs. It does
not load the model/certificate/evidence gzip, construct a point state, rebuild
source bodies or execute any fixture/auditor/producer/search/native function.
"""
import ast
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def pin(path):
    path=Path(path).resolve();h=hashlib.sha256();size=0
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):
            h.update(block);size+=len(block)
    return dict(path=str(path),sha256=h.hexdigest(),bytes=size)


def read(path):return json.loads(Path(path).read_text())


def frozen(item):
    expected={k:item[k] for k in ('path','sha256','bytes')}
    path=Path(expected['path']);path=path if path.is_absolute() else ROOT/path
    actual=pin(path)
    if {k:actual[k] for k in ('sha256','bytes')}!={k:expected[k] for k in ('sha256','bytes')}:
        raise ValueError('changed exact prior pin: '+expected['path'])
    return actual


def role(path,name):return dict(pin(path),role=name)


def write(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')


def main():
    started=time.monotonic()
    producer_path=ROOT/'.gcts-active/family-proposal-source-20261012/preparation-plan-v2.json'
    producer=read(producer_path);producer_roles={p['role']:ROOT/p['path'] for p in producer['inputs']}
    old_path=ROOT/'.gcts-active/hilbert-cluster-full-independent-20261011/audit-plan-v1.json'
    old=read(old_path);old_roles={p['role']:ROOT/p['path'] for p in old['inputs']}
    new_sources=[pin(HERE/name) for name in ('family_pool_independent_v1.py','family_pool_owner_v1.py','family_pool_freeze_v1.py')]
    libraries=[role(ROOT/'.gcts-active/hilbert-cluster-full-independent-20261011/full_point_oracle_v1.py','independent_point'),
        role(ROOT/'.gcts-active/hilbert-cluster-full-independent-20261011/full_family_registry_v1.py','independent_body'),
        role(ROOT/'.gcts-active/hilbert-aggregate-independent-audit-20261011/independent_aggregate_audit_v1.py','independent_symbolic'),
        role(ROOT/'.gcts-active/hilbert-aggregate-independent-audit-20261011/independent_aggregate_full_v2.py','independent_expansion')]
    old_library_pins={p['path']:p for p in old['sources']+old['libraries']}
    for item in libraries:
        frozen(old_library_pins[str(Path(item['path']).relative_to(ROOT))])
    producer_folder=producer_path.parent
    inputs=[role(producer_path,'preparation_plan'),
        role(producer_folder/'preparation-evidence-v2.json.gz','preparation_evidence'),
        role(producer_folder/'preparation-outcome-v2.json','preparation_outcome'),
        role(producer_folder/'preparation-lifetime-v2.json','preparation_lifetime'),
        role(producer_folder/'preparation-supervision-v2.json','preparation_supervision'),
        role(ROOT/'.gcts-active/family-proposal-progress-20261012/preparation-terminal-v2.json','root_preparation_terminal'),
        role(producer_roles['primitive_model'],'primitive_model'),
        role(producer_roles['checked_compact_family_projection'],'family_projection'),
        role(producer_roles['source_constant_transport_certificate'],'source_certificate'),
        role(producer_roles['exact_three_source_schemas'],'source_schemas'),
        role(producer_roles['original_point_model_plan'],'prior_point_plan'),
        role(producer_roles['original_56_input_body_plan'],'original_body_plan'),
        role(old_path,'prior_accepted_independent_plan'),
        role(ROOT/'.gcts-active/hilbert-cluster-full-independent-20261011/audit-result-v1.json','prior_accepted_independent_result'),
        role(ROOT/'.gcts-active/hilbert-cluster-full-independent-20261011/audit-lifetime-v1.json','prior_accepted_independent_lifetime'),
        role(ROOT/'.gcts-active/hilbert-cluster-full-independent-20261011/scope-clarification-v1.json','prior_source_scope_clarification'),
        role(ROOT/'.gcts-active/full-model-cluster-progress-20261011/root-full-independent-terminal-v1.json','prior_root_independent_terminal'),
        role(ROOT/'.gcts-active/family-proposal-independent-20261012/fixture-plan-v2.json','pure_fixture_plan'),
        role(ROOT/'.gcts-active/family-proposal-independent-20261012/fixture-result-v2.json','pure_fixture_result'),
        role(ROOT/'.gcts-active/family-proposal-independent-20261012/fixture-lifetime-v2.json','pure_fixture_lifetime'),
        role(ROOT/'.gcts-active/family-preparation-source-independent-review-20261012/source-review-v2.json','independent_preparation_source_review'),
        role(ROOT/'docs/basic-tiling-algorithm.md','master_contract')]
    terminal=read(inputs[5]['path']);outcome=read(inputs[2]['path']);lifetime=read(inputs[3]['path'])
    if (terminal['status']!='passed_ROOT_owned_complete_preparation_pending_actual_pool_audit'
        or lifetime['status']!='passed_family_preparation_full_lifetime_resource_phase'
        or outcome['status']!='complete_declared_proposal_grammar_prepared_pending_independent_audit'):
        raise ValueError('actual completed preparation prerequisite absent')
    # Exact prior role pins remain relative in their original declarations;
    # prospective independent owner pins use resolved absolute paths consistently.
    retained={}
    for group in ('sources','inputs','preserved_files'):
        for item in producer[group]:
            actual=frozen(item)
            prior=retained.setdefault(actual['path'],actual)
            if prior!=actual:raise ValueError('different hashes at one retained path')
    for item in old['sources']+old['libraries']:
        actual=frozen(item);retained[actual['path']]=actual
    explicit_paths={p['path'] for p in new_sources+libraries+inputs}
    preserved=[v for k,v in sorted(retained.items()) if k not in explicit_paths]
    ast_receipts=[]
    for item in new_sources+libraries:
        tree=ast.parse(Path(item['path']).read_text());imports=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom):imports.append(node.module)
        ast_receipts.append(dict(pin=item,imports=sorted(imports),ast_parsed=True,executed=False))
    archive=HERE/'audit-sources-v1.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for item in new_sources+libraries:
            z.write(item['path'],str(Path(item['path']).relative_to(ROOT)))
    design=dict(status='source_only_prospective_independent_complete_pool_gate',
        preparation_acceptance='Complete producer preparation remains pending this independent actual gate.',
        model_reconstruction='Future actual audit builds only independent literal point state, seed order, formula/recipe licenses and identity preimages from exact data. Not merely metadata replay; no production engine is imported.',
        symbolic_body_reconstruction='Future actual audit independently validates the three source declarations, all 171 literal role-preserving transports and strict-prior dependencies under frozen guarded I.2, then recursively expands every leaf/assumption alias/call and rederives each complete projection. Narrow six-rule symbolic relation only.',
        binding_census='All 171 single types and all 29,241 ordered pair types; complete formula-filtered ordered root Cartesian products, included first declared conclusion as second receptor with at least one link. Actual original boundary seed insertion order, not sorted full-key anchor ordinals.',
        embedding='One canonical earliest exact recipe/ordered-reference reuse else earliest unused increasing strict-prior row per binding; a finite DAG embedding adaptation, not arbitrary rigid translation completeness.',
        conclusion='Exact declared projection conclusion row/code, including non-last declarations; independent full projection digest and body member evidence. No default last-member convention.',
        sharing='Deduplicate exact primitive keys and full decorated identities only; preserve every source occurrence, ordered repeated read port and donor/dependency provenance. Receptor aliases add zero occupancy and no new premise seeds.',
        priority='Independent complete registration order and decreasing distinct union size/canonical specification, including exact fixed priority tuple in group authority epoch.',
        point_scope='Every group constituent and whole union checked by direct literal t/m against original initial assignments and unit capacity. Absent and assigned-zero markings differ. Complete candidate graph degrees, scheduler and search exhaustion are not part of this static gate.',
        logical_scope='Primitive inventory licenses and conditional source expansion inference checks; no whole-recipient target word, completed point tiling, native query, theorem discovery or training.',
        mutation_scope='Changed per-group payloads with recomputed self-hashes compared to wholly reconstructed descriptors. Not full altered evidence-file or owner replays. Prior independently owned 52 pure fixture controls remain separately charged and scoped.',
        example_read_scope='Compact projection is JSON-decoded, including authored display example, then example is discarded. No authored example word is used for hints or acceptance authority.',
        timing_scope='All fresh owner pin checks, body/model preparation, complete enumeration, result writing and worker post-verification inside owned lifetime; final owner receipt write outside pre-write timer. Source authoring not instrumented, not zero.',
        exact_input_scope='Current exact-pinned standard JSON files only; no general adversarial JSON parser correctness claim.',
        predicted_counts=dict(families=171,recipes=229,formulas=217,rows=24,leaves=1845,aliases=630,recursive_calls=216),
        producer_observed_not_independently_accepted=dict(groups=5,singles=3,pairs=2,component_member_occurrences=72,sum_distinct_members=67,shared_member_occurrences=5),
        proposed_limits=dict(whole_seconds=180,supervisor_seconds=175,child_seconds=170,peak_bytes=512*1024**2),
        execution_authorized=False,actual_audits_executed=0,production_engine_executed=0,searches=0,native_queries=0)
    write(HERE/'design-v1.json',design);inputs.append(role(HERE/'design-v1.json','independent_gate_design'))
    plan=dict(schema='independent-static-family-pool-audit-plan-v1',status='source_frozen_unexecuted_ROOT_review_and_activation_required',
        sources=new_sources,libraries=libraries,inputs=inputs,preserved=preserved,source_archive=pin(archive),
        runtime=dict(executable=sys.executable,platform=sys.platform,version=sys.version,binary=pin(Path(sys.executable).resolve())),
        limits=design['proposed_limits'],worker_path=str(HERE/'family_pool_independent_v1.py'),owner_path=str(HERE/'family_pool_owner_v1.py'),
        outputs=dict(result=str(HERE/'audit-result-v1.json'),lifetime=str(HERE/'audit-lifetime-v1.json'),stdout=str(HERE/'audit-stdout-v1.txt'),stderr=str(HERE/'audit-stderr-v1.txt')),
        activation_path=str(HERE/'root-static-pool-activation-v1.json'),activation_schema='root-independent-static-family-pool-activation-v1',
        activation_fields=dict(authorized=True,plan_sha256='exact audit-plan-v1.json SHA-256 after ROOT review'),
        enforcement='Permitted own-PID /bin/ps samples, child SIGALRM, supervisor deadline, kill/wait4 reaping and final conservative kernel peak; no hard OS memory limit claim.',
        source_authoring_cost='not instrumented; not zero',metadata_freeze_seconds_before_plan_write=time.monotonic()-started,
        actual_audit_execution_authorized=False,actual_audit_runs=0,scope=design['logical_scope'])
    planpath=HERE/'audit-plan-v1.json';write(planpath,plan)
    command=[sys.executable,str(HERE/'family_pool_owner_v1.py'),str(planpath)]
    ready=dict(status='source_ready_for_ROOT_review_only_unexecuted',plan=pin(planpath),design=pin(HERE/'design-v1.json'),
        source_archive=pin(archive),source_count=len(new_sources),independent_library_count=len(libraries),input_roles=len(inputs),
        preserved_count=len(preserved),exact_unique_path_count=len({p['path'] for p in new_sources+libraries+inputs+preserved}),
        AST=ast_receipts,ROOT_command_argv_after_separate_authorization=command,
        activation_path=plan['activation_path'],activation_schema=plan['activation_schema'],
        execution_authorized=False,scientific_function_calls_by_freeze=0,actual_audit_runs=0)
    write(HERE/'source-ready-v1.json',ready)
    names=['family_pool_independent_v1.py','family_pool_owner_v1.py','family_pool_freeze_v1.py','design-v1.json',
        'audit-sources-v1.zip','audit-plan-v1.json','source-ready-v1.json']
    manifest=dict(status='immutable_source_only_prospective_package',files=[pin(HERE/name) for name in names],
        ROOT_dispatch_required=True,actual_audit_runs=0)
    write(HERE/'integration-v1.json',manifest)
    print(json.dumps({k:ready[k] for k in ('status','plan','source_count','independent_library_count','input_roles','preserved_count','exact_unique_path_count','ROOT_command_argv_after_separate_authorization')}))


if __name__=='__main__':main()
