"""Metadata-only source/input/output freeze; grants no execution authorization."""
import ast
import hashlib
import json
import time
import zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def pin(p,role=None):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b)
    r=dict(path=str(p.relative_to(ROOT)),sha256=h.hexdigest(),bytes=p.stat().st_size)
    if role is not None:r['role']=role
    return r


def load(p):return json.loads(p.read_bytes())


def main():
    began=time.perf_counter();planpath=HERE/'audit-plan-v1.json'
    if planpath.exists():raise ValueError('immutable audit freeze exists')
    producer=ROOT/'.gcts-active/hilbert-cluster-lifecycle-20261011'
    ppath=producer/'full-language-plan-v3.json';pp=load(ppath)
    expected='016b6f14ca64cba4af58d742738ad5a785efec46c2d6b2cd103e1aaeb06e6d0a'
    if pin(ppath)['sha256']!=expected:raise ValueError('reviewed producer plan changed')
    old={e['role']:ROOT/e['path'] for e in pp['inputs']}
    paths={'producer_plan':ppath,'producer_freeze':producer/'full-language-freeze-v3.json',
        'producer_outcome':producer/'full-language-outcome-v3.json',
        'producer_supervision':producer/'full-language-supervision-v3.json',
        'producer_lifetime':producer/'full-language-lifetime-v3.json',
        'producer_source_review':HERE/'producer-source-review-v3.json',
        'primitive_model':old['primitive_model'],'family_projection':old['complete_family_template_projection'],
        'transport_certificate':old['source_constant_transport_certificate'],
        'source_schemas':old['exact_three_source_schemas'],'prior_point_plan':old['prior_full_model_plan'],
        'prior_point_outcome':old['prior_full_model_outcome'],
        'prior_point_independent_result':old['prior_full_model_independent_result'],
        'tiny_independent_result':old['new_tiny_lifecycle_independent_result'],
        'tiny_independent_lifetime':old['new_tiny_lifecycle_independent_lifetime'],
        'master_contract':ROOT/'docs/basic-tiling-algorithm.md','independent_design':HERE/'design-v1.json'}
    lifetime=load(paths['producer_lifetime']);supervision=load(paths['producer_supervision'])
    if lifetime['status']!='passed_authored_full_language_lifecycle_full_lifetime' or supervision['status']!='passed_bounded_authored_full_language_lifecycle':
        raise ValueError('producer complete terminal/resource gate has not passed')
    if supervision['owned_child_terminal_wait_reaped'] is not True or lifetime['supervisor_wait_reaped'] is not True:
        raise ValueError('producer owners not terminal/reaped')
    inputs=[pin(p,role) for role,p in paths.items()]
    names=['full_point_oracle_v1.py','full_family_registry_v1.py','full_lifecycle_state_v1.py',
           'full_lifecycle_audit_v1.py','full_lifecycle_owner_v1.py',Path(__file__).name]
    sources=[]
    for name in names:
        p=HERE/name;ast.parse(p.read_text());sources.append(pin(p))
    libs=ROOT/'.gcts-active/hilbert-aggregate-independent-audit-20261011'
    libraries=[pin(libs/'independent_aggregate_audit_v1.py','symbolic_checker'),
               pin(libs/'independent_aggregate_full_v2.py','expansion_checker')]
    preserved={}
    for e in pp['sources']+pp['inputs']+pp['preserved_files']:
        if pin(ROOT/e['path'])!={k:e[k] for k in ('path','sha256','bytes')}:
            raise ValueError('preserved producer closure changed: '+e['path'])
        preserved[e['path']]={k:e[k] for k in ('path','sha256','bytes')}
    for p in HERE.iterdir():
        if p.is_file() and p.suffix in ('.py','.json'):
            preserved[str(p.relative_to(ROOT))]=pin(p)
    occupied={e['path'] for e in sources+inputs+libraries}
    preserved=[e for path,e in sorted(preserved.items()) if path not in occupied]
    with zipfile.ZipFile(HERE/'audit-sources-v1.zip','x',zipfile.ZIP_DEFLATED) as z:
        for e in sources+libraries:z.write(ROOT/e['path'],e['path'])
    output=dict(result_path=str((HERE/'audit-result-v1.json').relative_to(ROOT)),
        lifetime_path=str((HERE/'audit-lifetime-v1.json').relative_to(ROOT)),
        stdout_path=str((HERE/'audit-stdout-v1.txt').relative_to(ROOT)),
        stderr_path=str((HERE/'audit-stderr-v1.txt').relative_to(ROOT)))
    plan=dict(status='frozen_independent_full_language_lifecycle_gate_pending_root_review_and_dispatch',
        version='full-language-lifecycle-independent-v1',sources=sources,libraries=libraries,inputs=inputs,
        preserved_files=preserved,source_archive=pin(HERE/'audit-sources-v1.zip'),
        whole_seconds=180,child_seconds=170,peak_bytes=536870912,
        worker_path=str((HERE/'full_lifecycle_audit_v1.py').relative_to(ROOT)),
        owner_path=str((HERE/'full_lifecycle_owner_v1.py').relative_to(ROOT)),**output,
        activation_path=str((HERE/'root-activation-v1.json').relative_to(ROOT)),
        scope='All 171 source-body transports, 175 registered literal bodies/five descriptors and 11 recorded full-model point/hint states with nine controlled transactions. No target DFS.',
        predicted_counts=dict(recipes=229,formulas=217,rows=24,source_families=171,literal_leaves=1845,
            aliases=630,recursive_calls=216,recorded_states=11,transactions=9,independent_corruptions=24),
        source_preparation_seconds_before_plan_write=time.perf_counter()-began,
        source_authoring_cost='not instrumented; not zero',
        enforcement='Single wait4 direct-child owner: wall kill/reap plus child SIGALRM; retrospective fresh-child+owner kernel peak. No OS soft-limit or live RSS claim.',
        limits_disposition='Any failed, unsupported, over-limit or incomplete check remains unknown; no accepted producer result can replace this independent artifact reconstruction.',
        root_command_after_review='python3 '+str((HERE/'full_lifecycle_owner_v1.py').relative_to(ROOT)),
        no_activation=dict(execution_authorized_by_this_freeze=False,target_searches=0,native_queries=0,solver_calls=0,compiler_activations=0))
    planpath.write_text(json.dumps(plan,indent=2)+'\n')
    ready=dict(status='source_and_terminal_input_freeze_pending_root_readiness_review',plan=pin(planpath),
        source_archive=pin(HERE/'audit-sources-v1.zip'),counts=dict(sources=len(sources),libraries=len(libraries),
            inputs=len(inputs),preserved=len(preserved)),owner_command=plan['root_command_after_review'],
        actual_audit_executions=0)
    path=HERE/'source-ready-v1.json';path.write_text(json.dumps(ready,indent=2)+'\n');print(json.dumps(ready))


if __name__=='__main__':main()
