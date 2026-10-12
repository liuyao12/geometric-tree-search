"""Metadata/hash/AST/archive-only source freeze. No scientific import or call."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CURRICULUM = ROOT / '.gcts-active/family-curriculum-context-source-v3-20261012'
TRANSFER = ROOT / '.gcts-active/family-curriculum-independent-source-20261012'
SELECTORS = ('donor-two-guards', 'donor-two-equalities', 'donor-repeated-guard',
             'donor-repeated-equality', 'heldout-mixed-guard-equality')
PARENTS = (
    (CURRICULUM/'source-plan-v1.json', '6631f0bd5c079442f48a0035aeb630373e4a8a460fc0aaec5f82cfd20871cf38'),
    (TRANSFER/'source-plan-v1.json', '9974fc67f340a5bb91a47e0b6a308cf67b06e419c4650f2e32e9ced3225ac5f7'),
)


def absolute(path):
    path = Path(path)
    return path.resolve() if path.is_absolute() else (ROOT/path).resolve()


def pin(path, role=None):
    path = absolute(path); stream_sha = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        for raw in iter(lambda:stream.read(65536),b''):
            stream_sha.update(raw); size += len(raw)
    result = dict(path=str(path), sha256=stream_sha.hexdigest(), bytes=size)
    return dict(role=role, **result) if role else result


def read(path):
    return json.loads(absolute(path).read_text())


def write(name, value):
    with (HERE/name).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    began=time.perf_counter()
    if any((HERE/name).exists() for name in ('source-plan-v1.json','readiness-v1.json','sources-v1.zip')):
        raise ValueError('immutable source outputs already exist; append a successor')
    parent_records=[]; expected={}; archive_checks=[]
    def reconcile(record):
        actual=pin(record['path']); expected_pin=dict(path=str(absolute(record['path'])),
                                                   sha256=record['sha256'],bytes=record['bytes'])
        if actual != expected_pin: raise ValueError('changed inherited exact bytes: '+record['path'])
        previous=expected.setdefault(actual['path'],actual)
        if previous != actual: raise ValueError('conflicting inherited exact pin')
    for path,sha in PARENTS:
        parent_pin=pin(path)
        if parent_pin['sha256'] != sha: raise ValueError('unchanged parent source plan required')
        document=read(path); parent_records.append((path,document));reconcile(parent_pin)
        for group in ('sources','libraries','inputs','preserved','preserved_files'):
            for record in document.get(group,[]): reconcile(record)
        archive=path.parent/'sources-v1.zip';reconcile(pin(archive))
        members=[]
        with zipfile.ZipFile(archive) as bundle:
            for name in bundle.namelist():
                if name.endswith('/') or name.startswith('/') or '..' in Path(name).parts:
                    raise ValueError('exact safe source archive members')
                target=path.parent/name
                if not target.is_file(): target=ROOT/name
                raw=bundle.read(name)
                if not target.is_file() or raw != target.read_bytes():
                    raise ValueError('source archive member changed: '+name)
                members.append(dict(name=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
        archive_checks.append(dict(archive=pin(archive),members=members))
    donor=parent_records[0][1]; prior=parent_records[1][1]
    sources=[pin(path) for path in sorted(HERE.glob('*.py'))]
    asts=[]
    for record in sources:
        tree=ast.parse(Path(record['path']).read_text(),filename=record['path'],feature_version=(3,9))
        asts.append(dict(pin=record,python_grammar='3.9',functions=[n.name for n in tree.body
                        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]))
    wanted=('independent_point','independent_families','independent_symbolic','independent_expansion','independent_static_pool')
    libraries=[dict(role=r['role'],**pin(r['path'])) for r in prior['libraries'] if r['role'] in wanted]
    if tuple(r['role'] for r in libraries) != wanted: raise ValueError('all five independent libraries in original order')
    libraries.append(pin(HERE/'curriculum_context_oracle_v1.py','independent_context'))
    libraries.append(pin(HERE/'independent_curriculum_selection_v1.py','independent_curriculum_selection'))
    inputs=[]
    for role in ('donor_primitive_model','family_projection','original_body_plan','source_certificate','source_schemas',
                 'master_contract','repository_contract'):
        record=next(r for r in prior['inputs'] if r['role']==role);inputs.append(pin(record['path'],role))
    prep=read(CURRICULUM/'preparation-donor-two-guards-plan-v1.json')
    for role in ('curriculum_reference','frozen_donor_split','frozen_RL_protocol','frozen_selection_binding'):
        record=next(r for r in prep['inputs'] if r['role']==role);inputs.append(pin(record['path'],role))
    for selector in SELECTORS:
        path=CURRICULUM/('preparation-'+selector+'-plan-v1.json');document=read(path)
        if document['selector']!=selector or document['schema']!='frozen-curriculum-family-preparation-plan-v1':
            raise ValueError('exact five frozen selector preparation plans')
        for group in ('sources','inputs','preserved_files'):
            for record in document[group]:reconcile(record)
        inputs.append(pin(path,'preparation_plan_'+selector))
    inputs.extend([pin(CURRICULUM/'source-plan-v1.json','curriculum_source_plan'),
        pin(CURRICULUM/'integration-v1.json','curriculum_integration'),
        pin(CURRICULUM/'sources-v1.zip','curriculum_source_archive'),
        pin(TRANSFER/'source-plan-v1.json','previous_independent_source_plan'),
        pin(TRANSFER/'sources-v1.zip','previous_independent_source_archive'),
        pin(HERE/'protocol-v1.json','independent_protocol'),pin(HERE/'source-review-v1.json','independent_source_review')])
    for record in sources+libraries+inputs:reconcile(record)
    if len(inputs) != len({r['role'] for r in inputs}): raise ValueError('unique source-stage input roles')
    # This is a metadata comparison of runtime identities. No subprocess/model
    # or native query is launched, and no source function is imported.
    runtime=prior['runtime']
    if pin(Path(sys.executable).resolve()) != runtime['binary'] or sys.platform != runtime['platform']:
        raise ValueError('exact Python runtime identity')
    if pin('/bin/ps') != runtime['observer']: raise ValueError('exact future observer identity')
    preserved=sorted(expected.values(),key=lambda r:r['path'])
    metadata=[HERE/'protocol-v1.json',HERE/'source-review-v1.json']+sorted(HERE.glob('*-source-diff-v1.txt'))
    with zipfile.ZipFile(HERE/'sources-v1.zip','x',zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted([Path(r['path']) for r in sources]+metadata):
            bundle.write(path,path.name)
    plan=dict(schema='five-context-independent-static-source-plan-v1',
        status='SOURCE_ONLY_FROZEN_NO_ACTUAL_INPUTS_OR_ACTIVATION',
        sources=sources,libraries=libraries,inputs=inputs,preserved=preserved,runtime=runtime,
        limits=dict(whole_seconds=180,supervisor_seconds=175,child_seconds=170,peak_bytes=536870912),
        selectors=list(SELECTORS),actual_input_plans_written=False,actual_activations_written=False,
        metadata_AST_records=asts,parent_source_archive_checks=archive_checks,
        scientific_imports_functions_models_compiles_fixtures_checkers_searches_RNG_updates_native=0,
        source_authoring_seconds=None,metadata_seconds_before_source_plan_write=time.perf_counter()-began,
        execution_authorized=False,ROOT_sole_actual_owner=True,
        protocol=pin(HERE/'protocol-v1.json'),source_review=pin(HERE/'source-review-v1.json'),
        absence_scope='No curriculum selection/compiler/model/source checker/pool enumerator or independent gate has been invoked by this subagent.')
    write('source-plan-v1.json',plan)
    output=dict(status='SOURCE_ONLY_READY_REQUIRES_ROOT_SOURCE_REVIEW_AND_REAL_INPUTS',
        source_plan=pin(HERE/'source-plan-v1.json'),source_archive=pin(HERE/'sources-v1.zip'),
        source_count=len(sources),Python39_ASTs=len(asts),input_roles=len(inputs),
        inherited_unique_exact_paths=len(preserved),parent_archive_member_count=sum(len(r['members']) for r in archive_checks),
        future_static_phases=5,actual_static_phases=0,actual_source_controls=0,
        full_DFS_RNG_adapter_in_this_package=False,training_acceptance_in_this_package=False,
        metadata_elapsed_before_readiness_write=time.perf_counter()-began,source_authoring_seconds=None,
        prior_metadata_author_failure='Preserved V1 metadata authoring history in parent source plan; V3 binding successor no new functional execution.',
        draft_review_repair='Only fresh V3 source/plan/output namespace rebinding. Worker/owner/context/selection sources byte identical to frozen V1.',
        ROOT_review_required=True,execution_authorized=False,scientific_calls=0)
    write('readiness-v1.json',output)
    write('integration-v1.json',dict(source_plan=output['source_plan'],source_archive=output['source_archive'],
        readiness=pin(HERE/'readiness-v1.json'),source_review=pin(HERE/'source-review-v1.json'),
        scientific_calls=0,actual_execution_authorized=False,
        next='ROOT reviews complete sources/diffs/closures. After each real producer preparation passes full ROOT resource and reaping gate, metadata finalizer can bind exact artifacts; then separate ROOT activation owns independent static audit.'))
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
