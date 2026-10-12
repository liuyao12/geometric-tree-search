"""Metadata-only source freeze: JSON plan/receipt reads, byte hashes, AST, ZIP.

No scientific import, worker/owner/model/checker/fixture/search/native execution.
The future source/activation gate is ROOT-owned and remains unexecuted here.
"""
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
    path=Path(path);digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):digest.update(block)
    return dict(path=str(path.relative_to(ROOT)),sha256=digest.hexdigest(),bytes=path.stat().st_size)


def absolute_pin(path):
    path=Path(path).resolve();item=pin(path) if path.is_relative_to(ROOT) else None
    if item:return dict(item,path=str(path))
    data=path.read_bytes();return dict(path=str(path),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))


def read(path):return json.loads(Path(path).read_text())


def preserve(items):
    seen={}
    for item in items:
        path=Path(item['path']);path=path if path.is_absolute() else ROOT/path
        actual=pin(path)
        if (actual['sha256'],actual['bytes'])!=(item['sha256'],item['bytes']):raise ValueError('changed prior frozen pin: '+str(path))
        before=seen.setdefault(actual['path'],actual)
        if before!=actual:raise ValueError('conflicting retained source versions')
    return seen


def role(path,name):return dict(pin(path),role=name)


def write(path,data):
    with path.open('x') as stream:json.dump(data,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    start=time.perf_counter()
    previous=ROOT/'.gcts-active/shared-symbolic-geometry-search-source-v2-20261011'
    preparation=ROOT/'.gcts-active/family-proposal-source-20261012'
    static=ROOT/'.gcts-active/family-pool-independent-audit-20261012'
    prior_plan=read(previous/'search-plan-v1.json');prep_plan=read(preparation/'preparation-plan-v2.json')
    static_plan=read(static/'audit-plan-v1.json')
    prep_roles={r['role']:ROOT/r['path'] for r in prep_plan['inputs']}
    static_lifetime=read(static/'audit-lifetime-v1.json')
    if (static_lifetime['status']!='passed_owned_independent_static_family_pool_audit'
            or static_lifetime['child_reaped'] is not True or static_lifetime['child_exit']!=0):
        raise ValueError('actual complete static gate resource PASS prerequisite')
    exact_static={name:absolute_pin(static/filename) for name,filename in
        [('plan','audit-plan-v1.json'),('result','audit-result-v1.json'),('lifetime','audit-lifetime-v1.json')]}
    if static_lifetime['result']!=exact_static['result'] or static_lifetime['plan']!=exact_static['plan']:
        raise ValueError('exact actual independently accepted static result/plan')
    names=['fixed_family_pool_adapter_v1.py','fixed_family_pool_registration_v1.py','fixed_family_pool_worker_v1.py',
        'fixed_family_pool_supervisor_v1.py','fixed_family_pool_outer_v1.py','fixed_family_pool_trace_oracle_v1.py','fixed_family_pool_freeze_v1.py']
    sources=[pin(HERE/name) for name in names]
    inputs=[role(previous/'shared_symbolic_geometry_search_v1.py','prior_search_worker'),
        role(previous/'shared_symbolic_forward_order_v1.py','prior_unchanged_sibling_import'),
        role(previous/'shared_symbolic_bridge_decode_v1.py','prior_unchanged_decoder'),
        role(prep_roles['lifecycle_kernel'],'frozen_lifecycle_kernel'),
        role(prep_roles['original_point_model_plan'],'prior_full_model_plan'),
        role(prep_roles['original_56_input_body_plan'],'passed_full_lifecycle_producer_plan'),
        role(prep_roles['checked_compact_family_projection'],'checked_compact_family_projection'),
        role(preparation/'family_proposal_v2.py','proposal_module'),
        role(preparation/'preparation-plan-v2.json','preparation_plan'),
        role(preparation/'preparation-evidence-v2.json.gz','pool_evidence'),
        role(preparation/'preparation-outcome-v2.json','pool_outcome'),
        role(preparation/'preparation-lifetime-v2.json','pool_preparation_lifetime'),
        role(static/'audit-plan-v1.json','static_pool_plan'),role(static/'audit-result-v1.json','static_pool_result'),
        role(static/'audit-lifetime-v1.json','static_pool_lifetime'),
        role(ROOT/'.gcts-active/family-pool-audit-progress-20261012/audit-terminal-v1.json','root_static_pool_terminal'),
        role(static/'source-ready-v1.json','independent_static_pool_source_ready'),
        role(previous/'base-complete-primitives-result-v1.json.gz','historical_same_boundary_base_result'),
        role(previous/'fixed-forward-novelty-result-v1.json.gz','historical_same_boundary_fixed_forward_result'),
        role(ROOT/'.gcts-active/receptor-matching-geometry-source-20261011/fixed-forward-receptor-result-v1.json.gz','historical_same_boundary_receptor_result'),
        role(ROOT/'docs/basic-tiling-algorithm.md','master_contract')]
    inherited=[]
    for old in (prior_plan,prep_plan):
        inherited.extend(old['sources']+old['inputs']+old['preserved_files'])
    inherited.extend(static_plan['sources']+static_plan['libraries']+static_plan['inputs']+static_plan['preserved'])
    retained=preserve(inherited);explicit={p['path'] for p in sources+inputs}
    preserved=[p for path,p in sorted(retained.items()) if path not in explicit]
    code=(previous/'shared_symbolic_geometry_search_v1.py').read_text()
    old_function=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='automatic_search')
    prior=ast.get_source_segment(code,old_function)+'\n'
    new_code=(HERE/'fixed_family_pool_adapter_v1.py').read_text()
    new_function=next(n for n in ast.parse(new_code).body if isinstance(n,ast.FunctionDef) and n.name=='fixed_pool_search')
    successor=ast.get_source_segment(new_code,new_function)+'\n'
    diff=''.join(difflib.unified_diff(prior.splitlines(True),successor.splitlines(True),fromfile='prior automatic_search unchanged',tofile='fixed_pool_search source-only sibling'))
    with (HERE/'search-function-source-diff-v1.txt').open('x') as stream:stream.write(diff)
    protocol=dict(status='prospective_independent_trace_audit_protocol_not_an_actual_audit',
        accepted_static_gate=exact_static,
        model='Exact original 229 primitive recipes / 217 injective formulas / 24 required proof rows and point epoch; three original generation-zero local hypotheses only.',
        pool='All five independently reconstructed proposals, unchanged registered priorities and source/interface/port/full-identity/union epoch; no selected target-proof chain or authored word. Runtime proposals are fixed and source conditional.',
        independently_rebuilt_pool='Future trace owner must reconstruct the pool again using independently accepted body/point/transport libraries, or bind their full exact complete static acceptance plus verify immutable group payloads; never import producer GroupAuthority/Controller/search/order/decoder as acceptance.',
        point_graph='Reuse geometry_trace_point_v1.PointState and TransactionState complete direct ordered reference domains, exact all-state census and cached immutable full graph serialization. No shortlist/cluster-size degree.',
        lifecycle='Use source-only FixedPoolTransactions: immutable priority-sorted descriptors, exact full IDs for selected sharing, pending whole aggregate capacity/assigned-m agreement; ready/waiting/consumed/branch-absorbing retired states and exact saved parent revival only by paired rollback.',
        ordering='A fixed priority ordered stream of ready eligible complete keys, deduplicated by full key, followed by EVERY remaining base candidate in unchanged order. Forced singleton interrupts hints. Reconstruct both hashes/counts/first key and whole_pool_order_trace at every recorded order.',
        tape_reuse='Reuse the independently accepted receptor_trace_audit_v3.Tape recursion, replacing receptor feature extraction with FixedPoolTransactions.order and exact whole_pool_order_trace. Do not reuse its empty-controller metric assertions or primitive-only hardcoded lazy-ID/proposal counts; charge/retain all pool preparation and validation work.',
        transactions='Check each node, scheduler decision, one primitive placement, generation, mark reference count, before/after snapshot, whole retirement, paired checkpoint and rollback. Exclude a parent candidate only after recursively established finite child exhaustion. UNKNOWN never excludes.',
        positive='Reconstruct solved global-complete/node-return propagation WITHOUT rollback and complete terminal t/m. Use independent positive_certificate_oracle_v1 for all 24 rows, exact ordered references and primitive licenses, exact guarded I.2/three original hypotheses/ground target. Independently derive Gamma-retaining flat request with blocks empty; do not use producer decode or the authored 24-row example as acceptance.',
        positive_scope='Ground guarded incidence fragment relative to the exact retained original hypotheses; no unrestricted Hilbert geometry, native Wang acceptance or newly discovered lemma claim.',
        unknown='Accept a complete UNKNOWN tape only with exact recorded safe rollback and no certificate. Preserve checked-deadline overshoot as clock/resource metadata. A trace-limit prefix must fail closed for complete-trace acceptance while preserving its UNKNOWN and requiring separate terminal root-restoration review.',
        metrics='Independently verify attempt/forced/branch/backtrack deltas and immutable registry/whole-hint counters where reconstructed. Graph lazy-ID/proposal validation counters include registration and selected shared identity checks: no zero-counter assumption. Retain unvalidated implementation timers as scoped saved costs.',
        controls='Prospective actual event payload/hash controls for false sharing, one component illegally surviving whole retirement, revision/parent restoration, stale authority, missing ordered ports, forced bypass, incomplete fallback and UNKNOWN falsely called exhaustion. Explicitly distinguish expected-payload checks from full mutated tape/owner replay.',
        reporting='Mapping observation id to independently concluded trace_accepted/certificate_accepted/scope. If positive, bind primitive-row/local-certificate/flat-request hashes. Projection flags only after acceptance; no proof flag for UNKNOWN.',
        audit_runtime='Separate future ROOT-reviewed 180/175/170 second, 512 MiB gate; no actual trace exists and no audit owner is currently executed. All import/model/registry/logical checks are part of that future owned cost.',
        current_actual_trace_audits=0,current_target_searches=0,current_native_queries=0,current_training_runs=0,
        future_auditor_owner_and_full_tape_adapter='Not yet authored/frozen for actual data; must be ROOT reviewed after producer terminal, with this independent oracle/protocol as source-only preparation.')
    write(HERE/'prospective-audit-protocol-v1.json',protocol)
    inputs.append(role(HERE/'prospective-audit-protocol-v1.json','prospective_trace_audit_protocol'))
    limits=dict(attempts=128,seconds=20,event_ceiling=2000)
    proposed=['fixed-whole-family-pool-result-v1.json.gz','search-outcome-v1.json','search-launch-v1.json',
        'search-supervision-v1.json','search-lifetime-v1.json','search-stdout-v1.txt','search-stderr-v1.txt']
    plan=dict(schema='source_only_fixed_whole_family_pool_search_plan_v1',status='source_ready_unexecuted_ROOT_reviews_and_activation_required',
        sources=sources,inputs=inputs,preserved_files=preserved,model_epoch=prep_plan['unchanged_model_epoch'],
        static_gate_pins=exact_static,observations=[dict(id='fixed-whole-family-pool',mode='fixed-whole-family-pool',**limits)],
        prospective_resources=dict(whole_seconds=180,supervisor_seconds=175,child_seconds=170,peak_bytes=536870912),
        runtime=dict(executable=sys.executable,platform=sys.platform,version=sys.version,binary=absolute_pin(Path(sys.executable).resolve())),
        proposed_outputs=proposed,activation_basename='root-activation-v1.json',
        activation_status='root_authorized_bounded_fixed_whole_family_pool_geometry_search',
        activation_plan='exact relative path / SHA-256 / bytes pin of search-plan-v1.json',
        execution_authorized_by_freeze=False,source_authoring_cost='not instrumented; not zero',
        source_metadata_freeze_seconds_before_plan_write=time.perf_counter()-start,
        scope='One automatic fixed whole-source-union hint lane, same old bounded finite point model and primitive fallback. Automatic recomposition of checked source bodies; no new lemma discovery, RL or native claim.',
        comparison='Historical 128-attempt/20-second/2000-event controls have the same point model; new preparation/lifecycle costs are separately retained and fully owned. One fresh fixed-pool observation is not a balanced speed-ratio experiment.',
        budgets='No widening of first search cap. Any larger budget is a later separately frozen experiment. Seconds are checked finite-operation boundaries with possible overshoot; 170/175/180 whole owner guards are separate.',
        costs='Cold model/body setup, raw pool/result decoding, all interface/whole-union reconstruction, Controller registration, ordering, full trace, decoder if positive, serialization and whole owner work charged. Static gate and historical preparation receipts separately retained, not erased or presented as free.',
        native_queries=0,new_RL_training=False,authored_words_used_as_hints=0,
        actual_target_searches_executed_by_freeze=0,actual_trace_audits_executed_by_freeze=0)
    planpath=HERE/'search-plan-v1.json';write(planpath,plan)
    archive=HERE/'source-only-v1.zip'
    files=names+['search-function-source-diff-v1.txt','prospective-audit-protocol-v1.json','search-plan-v1.json']
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name in files:z.write(HERE/name,name)
    asts=[]
    for source in sources:
        tree=ast.parse((ROOT/source['path']).read_text());asts.append(dict(source=source,ast_parsed=True,executed=False,
            imports=[dict(module=getattr(n,'module',None),names=[a.name for a in n.names]) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]))
    readiness=dict(status='source_ready_unexecuted_no_activation',plan=pin(planpath),source_archive=pin(archive),
        source_count=len(sources),input_roles=len(inputs),preserved_count=len(preserved),
        unique_exact_paths=len({p['path'] for p in sources+inputs+preserved}),AST=asts,
        prospective_ROOT_command_argv=[sys.executable,str(HERE/'fixed_family_pool_outer_v1.py')],
        activation_basename='root-activation-v1.json',activation_status=plan['activation_status'],
        search_limits=limits,actual_static_gate=exact_static,actual_target_searches=0,actual_trace_audits=0,native_queries=0,
        ROOT_separate_source_review_and_dispatch_required=True)
    write(HERE/'source-ready-v1.json',readiness)
    files+=['source-only-v1.zip','source-ready-v1.json']
    write(HERE/'integration-v1.json',dict(status='immutable_source_only_adapter_and_prospective_audit_package',
        files=[pin(HERE/name) for name in files],execution_authorized=False,searches=0,native_queries=0))
    print(json.dumps({k:readiness[k] for k in ('status','plan','source_count','input_roles','preserved_count','unique_exact_paths','prospective_ROOT_command_argv')}))


if __name__=='__main__':main()
