"""Metadata-only independent source/input freeze. No mathematical imports."""
import ast
import hashlib
import json
import time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PRODUCER=ROOT/'.gcts-active/receptor-matching-geometry-source-20261011'
PRIOR=ROOT/'.gcts-active/hilbert-cluster-full-independent-20261011'


def pin(path):
    path=Path(path);h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return dict(path=str(path.relative_to(ROOT)),sha256=h.hexdigest(),bytes=path.stat().st_size)


def read(path):
    return json.loads(Path(path).read_text())


def save(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def main():
    started=time.perf_counter()
    if any((HERE/n).exists() for n in ('audit-plan-v2.json','source-freeze-v2.json','source-manifest-v2.json')):
        raise ValueError('immutable independent freeze exists')
    producer=read(PRODUCER/'search-plan-v1.json');prior=read(ROOT/'.gcts-active/shared-symbolic-geometry-trace-independent-20261011/audit-plan-v1.json')
    terminal_path=ROOT/'.gcts-active/receptor-matching-progress-20261011/root-producer-terminal-v1.json'
    terminal=read(terminal_path);outcome=read(PRODUCER/'search-outcome-v1.json')
    if terminal['same_exec_terminal_exit_code']!=0 or terminal['all_owned_processes_terminal_reaped'] is not True:
        raise ValueError('authoritative actual producer terminal required before freeze')
    sources=[pin(HERE/n) for n in ('literal_receptor_oracle_v2.py','receptor_order_oracle_v1.py',
        'positive_certificate_oracle_v1.py','receptor_trace_audit_v2.py','receptor_trace_owner_v2.py','receptor_trace_freeze_v2.py')]
    libs=list(prior['libraries'])+[dict(role='independent_transactions',**pin(ROOT/'.gcts-active/shared-symbolic-geometry-trace-independent-20261011/geometry_trace_point_v1.py'))]
    roles={e['role']:ROOT/e['path'] for e in producer['inputs']}
    inputs=[dict(role=role,**pin(path)) for role,path in (
        ('producer_plan',PRODUCER/'search-plan-v1.json'),
        ('producer_outcome',PRODUCER/'search-outcome-v1.json'),
        ('producer_lifetime',PRODUCER/'search-lifetime-v1.json'),
        ('producer_supervision',PRODUCER/'search-supervision-v1.json'),
        ('producer_activation',PRODUCER/'root-activation-v1.json'),
        ('root_terminal',terminal_path),
        ('accepted_body_plan',roles['passed_full_lifecycle_producer_plan']),
        ('primitive_model',roles['primitive_model']),
        ('family_projection',roles['complete_family_template_projection']),
        ('prior_point_plan',roles['prior_full_model_plan']),
        ('transport_certificate',roles['source_constant_transport_certificate']),
        ('source_schemas',roles['exact_three_source_schemas']),
        ('master_contract',ROOT/'docs/basic-tiling-algorithm.md'),
        ('independent_producer_source_review',HERE/'producer-source-review-v1.json'),
        ('independent_pair_controls',HERE/'prospective-pair-controls-v2.json'),
        ('independent_cross_domain_corpus',ROOT/'.gcts-active/receptor-matching-cross-domain-source-20261011/synthetic-corpus-v2.json'),
        ('architecture_only',HERE/'audit-architecture-v1.json'),
        ('source_correction',HERE/'checkpoint-variable-correction-v2.json'))]
    for record in outcome['observations']:
        inputs.append(dict(role='actual_trace:'+record['id'],**pin(ROOT/record['result']['path'])))
    inputs.extend([dict(e,role='broader_phase:'+e['role']) for e in producer['inputs']])
    if len({e['role'] for e in inputs})!=len(inputs):raise ValueError('input role collision')
    preserved={}
    candidates=producer['sources']+producer['inputs']+producer['preserved_files']
    candidates+=prior['sources']+prior['libraries']+prior['inputs']+prior['preserved_files']
    for folder in (PRODUCER,ROOT/'.gcts-active/shared-symbolic-geometry-trace-independent-20261011'):
        candidates += [pin(p) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    candidates += [pin(HERE/n) for n in ('receptor_trace_audit_v1.py','receptor_trace_owner_v1.py','receptor_trace_freeze_v1.py','audit-plan-v1.json','source-freeze-v1.json','source-manifest-v1.json','worker-v1-to-v2.diff')]
    for e in candidates:
        actual=pin(ROOT/e['path'])
        if actual!={k:e[k] for k in ('path','sha256','bytes')}:raise ValueError('old pin mismatch '+e['path'])
        if e['path'] in preserved and preserved[e['path']]!=actual:raise ValueError('pin conflict')
        preserved[e['path']]=actual
    unique={}
    for e in sources+libs+inputs+list(preserved.values()):
        actual=pin(ROOT/e['path'])
        if actual!={k:e[k] for k in ('path','sha256','bytes')}:raise ValueError('exact new closure '+e['path'])
        unique[e['path']]=actual
    for e in sources+libs:ast.parse((ROOT/e['path']).read_text(),filename=e['path'])
    plan=dict(version='independent-full-receptor-geometry-returned-trace-audit-v2',
        status='source_ready_pending_root_review_and_sole_owner_dispatch',sources=sources,libraries=libs,
        inputs=inputs,preserved_files=[preserved[k] for k in sorted(preserved)],
        expected_observations=[dict(id=r['id'],status=r['status'],events=r['events'],attempts=r['attempts'],
            point_certificates=int(r['decoded_certificate']),decoded_certificates=int(r['decoded_certificate'])) for r in outcome['observations']],
        method=dict(source='Independently rebuild all171 literal source bodies and every229 logical recipe from own accepted symbolic/expansion modules.',
            domains='At each distinct complete graph state enumerate every ordered binding from literal output/formula/offset t/m constraints, cross-check independent factor serialization and full saved semantic hash. Cache only independently rebuilt immutable identical graph states.',
            ordering='Independently extract all229 receptor patterns; compare literal ordered ASTs and exact successful images with own tree oracle plus independent export scanner. Reconstruct every selected key/code, recipe label/comparison stream, complete readiness-first score stream and full chosen-domain permutation. Never prune on mismatch.',
            transactions='Consume exact returned event tape recursively; own deep-state checkpoints/rollback, complete global dead/forced/generation/degree decisions, ordered primitive steps, exclusions only after independently exhausted child and UNKNOWN propagation without exclusion.',
            identity='Reconstruct each visited primitive full decorated preimage/id/t/m/command and ordered reference rows from independent library.',
            controls='Mutate actual independently reconstructed expected event payloads: counts/row scheduler, zero/absence/type, stream/order/keys, occupancy/authority/hints, exact rollback/refcounts and unknown/child/exclusion claims. Expected templates originate in this independent replay.',
            certificates='Actual results contain no point/decoded certificate. Source supports full successful child propagation without rollback, independent exact t/m24rows and every guarded primitive logical command, followed by independent Gamma-retaining flat request; that branch is unexercised here. Truncated trace fails closed with no complete acceptance or exhaustion claim. No native invocation.'),
        whole_seconds=180,child_seconds=170,peak_bytes=512*1024*1024,
        result_path=str((HERE/'audit-result-v2.json').relative_to(ROOT)),
        lifetime_path=str((HERE/'audit-lifetime-v2.json').relative_to(ROOT)),
        stdout_path=str((HERE/'audit-stdout-v2.txt').relative_to(ROOT)),
        stderr_path=str((HERE/'audit-stderr-v2.txt').relative_to(ROOT)),
        worker_path=str((HERE/'receptor_trace_audit_v2.py').relative_to(ROOT)),
        root_command_after_exact_activation='python3 '+str(HERE/'receptor_trace_owner_v2.py'),
        resource_enforcement='Whole owned wait4 lifecycle, child alarm, deadline kill/reap and retrospective fresh-child plus owner kernel peak. No hard OS memory cap. A time/memory failure is UNKNOWN, never partial acceptance.',
        costs=dict(independent_full_lifetime='All source checks/loading/body/model/domain/ordering/trace/mutation/serialization/reap inside independent owner; own final receipt write excluded.',
            source_authoring='unmeasured',prior_failed_V1_producer_seconds=0.935204458,
            prior_V2_producer_seconds=8.109092125, prior_complete_independent_audit_seconds=41.361476959,
            actual_receptor_producer_seconds=terminal['owned_seconds'],
            separate_pure_AST_controls='0.030158792 seconds, additional source-only controls; not actual model authority',prior_and_producer_costs='Additional to independent audit, never free or summed with nested overlapping timers.'),
        limitations=['Exactly two pinned returned UNKNOWN tapes and their marked subtrees; no claim of whole-boundary impossibility or theorem nonprovability. Positive implementation is source-only/unexercised by these results.',
            'Complete t/m and registered interface validity does not imply a completed proof unless every proof row is occupied and all ordered command references close; there is no certificate in these observations.',
            '20-second deadlines are checked and may overshoot in-flight work; actual attempt ceilings hit128. TraceLimit prefixes unsupported/fail-closed by this complete tape gate.',
            'No production graph/controller/ranker/search/decoder acceptance import. The compact family example is decoded and discarded, never supplies target hints/authority.',
            'Domain refresh implementation timers/counters are preserved producer provenance, not independently reproduced by this distinct reconstruction algorithm.'],
        mathematical_model_epoch=producer['model_epoch'],recipes=229,formulas=217,rows=24,
        active_descriptors=0,scientific_searches_by_auditor=0,native_queries=0,training=0,execution_authorized=False)
    pp=HERE/'audit-plan-v2.json';save(pp,plan)
    receipt=dict(status='frozen_independent_source_only_trace_audit_pending_root_dispatch',plan=pin(pp),
        sources=len(sources),libraries=len(libs),inputs=len(inputs),preserved=len(preserved),
        unique_verified_paths=len(unique),ASTs_parsed=len(sources)+len(libs),mismatches=0,
        metadata_freeze_seconds_before_receipt_write=time.perf_counter()-started,
        source_authoring='unmeasured',scientific_loads=0,fixture_runs=0,searches=0,native_queries=0)
    rp=HERE/'source-freeze-v2.json';save(rp,receipt)
    files=sources+[pin(pp),pin(rp)]
    mp=HERE/'source-manifest-v2.json';save(mp,dict(status='immutable_source_only_independent_geometry_trace_audit',
        files=files,total_files=len(files),total_bytes=sum(e['bytes'] for e in files),plan=pin(pp),
        root_command=plan['root_command_after_exact_activation'],scientific_execution=False))
    print(json.dumps(dict(plan=pin(pp),receipt=pin(rp),manifest=pin(mp)),indent=2))


if __name__=='__main__':main()
