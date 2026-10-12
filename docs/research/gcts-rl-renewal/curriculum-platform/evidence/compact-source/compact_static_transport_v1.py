"""SOURCE ONLY exact metadata transport. No science or dispatch on load.

The source author never imports/invokes this module. Every actual plan and
platform adapter must be separately supplied, frozen and reviewed by ROOT.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import struct
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
VERSION='compact-static-transport-v1'
FROZEN_SEMANTIC_LIBRARIES=[{'role': 'independent_point', 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-cluster-full-independent-20261011/full_point_oracle_v1.py', 'sha256': '6a94f6c7c2d7713061c7238ca6abb5d58936670d348736f758c57ba8cf5a8546', 'bytes': 14401}, {'role': 'independent_families', 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-cluster-full-independent-20261011/full_family_registry_v1.py', 'sha256': '71fb7add4338cfb1ace339993d991e96c5c2fa59dc450a48816096575e5c297c', 'bytes': 12212}, {'role': 'independent_symbolic', 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-aggregate-independent-audit-20261011/independent_aggregate_audit_v1.py', 'sha256': 'bc7a080659fb0715ef098717a79a4bb5d6583ab05d8dec6739a8de90df488840', 'bytes': 44198}, {'role': 'independent_expansion', 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-aggregate-independent-audit-20261011/independent_aggregate_full_v2.py', 'sha256': 'ea21d696a86f907b333dbe18f712aa7f00e9d3960c6cba69a19d2b879194fc0a', 'bytes': 51577}, {'role': 'independent_static_pool', 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/family-pool-independent-audit-20261012/family_pool_independent_v1.py', 'sha256': '7cf5b5840b7374eb405948baee722747c0122cbeae44d8b9a6057ed76b8106b3', 'bytes': 31396}, {'role': 'independent_context', 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/family-curriculum-independent-source-v3-20261012/curriculum_context_oracle_v1.py', 'sha256': '2f474f5b43793c6d712079130bcb315540e388bc7f6a32f9e6f120654f96bf41', 'bytes': 22429}, {'role': 'independent_curriculum_selection', 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/family-curriculum-independent-source-v3-20261012/independent_curriculum_selection_v1.py', 'sha256': '5f368989c715e90ca018a5d3cca82c4ee1569abb52567aabe06f0c411524e28f', 'bytes': 8816}]
ALLOWED_SELECTORS=('donor-two-equalities','donor-repeated-guard',
                   'donor-repeated-equality','heldout-mixed-guard-equality')
PROJECTION=('status','static_context_pool_accepted','trace_accepted','certificate_accepted',
    'selector','partition','model_epoch','context_id','compiled_context_pin','preparation_evidence_pin',
    'RL_full_pool_capacity','RL_full_pool_capacity_satisfied','primitive_license_count',
    'non_assumption_witness_count','source_body_count','single_types','pair_types',
    'whole_target_logical_checks','native_queries','native_accepted','searches','training')
POSTLUDE=struct.Struct('!8sBBHQQddd')


def path_for(declared):
    path=Path(declared)
    return path if path.is_absolute() else ROOT/path


def stream_pin(path,declared=None):
    path=Path(path);h=hashlib.sha256();count=0
    def identity(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    with path.open('rb') as stream:
        before=os.fstat(stream.fileno())
        for block in iter(lambda:stream.read(65536),b''):h.update(block);count+=len(block)
        after=os.fstat(stream.fileno())
    if identity(before)!=identity(after) or identity(after)!=identity(path.stat()) or count!=after.st_size:
        raise ValueError('immutable stream identity/length changed')
    if declared is None:
        try:declared=str(path.relative_to(ROOT))
        except ValueError:declared=str(path)
    return dict(path=declared,sha256=h.hexdigest(),bytes=count)


def verify_pin(record):
    exact={k:record[k] for k in ('path','sha256','bytes')}
    if stream_pin(path_for(record['path']),record['path'])!=exact:
        raise ValueError('exact declared metadata/source/evidence pin changed')
    return path_for(record['path'])


def no_duplicate_fields(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('duplicate compact metadata field')
        value[key]=item
    return value


def read_small(path,maximum_bytes):
    if type(maximum_bytes) is not int or not 0<maximum_bytes<=536870912:
        raise ValueError('separately ROOT-frozen metadata transport limit within unchanged cap')
    with Path(path).open('rb') as stream:raw=stream.read(maximum_bytes+1)
    if len(raw)>maximum_bytes:raise ValueError('bounded compact metadata exceeded')
    return json.loads(raw,object_pairs_hook=no_duplicate_fields,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite compact metadata')))


def write_new(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')


def require_contract(plan,planpath,workerpath):
    if (plan.get('schema')!='frozen-curriculum-independent-compact-static-plan-v1'
            or plan.get('status')!='frozen_actual_inputs_pending_ROOT_activation'
            or plan.get('stage')!='static' or plan.get('selector') not in ALLOWED_SELECTORS
            or plan.get('actual_execution_authorized') is not False
            or plan.get('ROOT_sole_actual_owner') is not True):
        raise ValueError('only still-unexecuted frozen selector; donor-two-guards permanently excluded')
    if plan['libraries']!=FROZEN_SEMANTIC_LIBRARIES:
        raise ValueError('all seven unchanged exact V3 semantic libraries; no alternate worker child scope')
    if plan['limits']!=dict(whole_seconds=180,supervisor_seconds=175,child_seconds=170,peak_bytes=536870912):
        raise ValueError('unchanged180/175/170second512MiB static bounds')
    contract=plan['compact_transport_contract']
    if contract['version']!=VERSION:raise ValueError('separately frozen exact compact contract')
    for key in ('compact_maximum_bytes','observer_stream_maximum_bytes','maximum_observers'):
        if type(contract[key]) is not int or not 0<contract[key]<=536870912:
            raise ValueError('separately ROOT-frozen bounded metadata envelope under unchanged memory cap')
    for role in ('worker_pin','owner_pin','transport_pin','wrapper_source_manifest_pin',
                 'platform_evidence_pin','accounting_adapter_pin','unexecuted_phase_attestation_pin'):
        verify_pin(contract[role])
    if (stream_pin(Path(workerpath))!=contract['worker_pin']
            or stream_pin(Path(__file__))!=contract['transport_pin']):
        raise ValueError('same actual worker and transport source')
    attestation=read_small(verify_pin(contract['unexecuted_phase_attestation_pin']),contract['compact_maximum_bytes'])
    if (attestation.get('status')!='ROOT_attested_still_unexecuted_compact_static_phase'
            or attestation.get('selector')!=plan['selector']
            or attestation.get('prior_donor_two_guards_resource_UNKNOWN_preserved') is not True):
        raise ValueError('actual ROOT still-unexecuted attestation required, never a rerun')
    platform=read_small(verify_pin(contract['platform_evidence_pin']),contract['compact_maximum_bytes'])
    if (platform.get('status')!='ROOT_verified_platform_accounting_evidence'
            or platform.get('units_verified') is not True
            or platform.get('wait4_descendant_scope_verified') is not True
            or platform.get('leaf_worker_and_observer_scope_verified') is not True
            or platform.get('closed_SELF_postlude_scope_reviewed') is not True
            or platform.get('adapter_pin')!=contract['accounting_adapter_pin']):
        raise ValueError('platform counting rule is absent/unverified; SOURCE ONLY cannot dispatch')
    directory=HERE/'outputs'/plan['selector']
    required=('result','compact','lifetime','observers','samples','stdout','stderr')
    if set(plan['outputs'])!=set(required):raise ValueError('complete distinct immutable metadata outputs')
    paths=[Path(plan['outputs'][name]) for name in required]
    if len(set(paths))!=len(paths) or any(p.parent!=directory for p in paths):
        raise ValueError('new exact per-selector successor output namespace, no aliases')
    return contract


def emit_compact(result,plan,planpath,workerpath,activationpath,started):
    contract=plan['compact_transport_contract']
    scalar={name:result[name] for name in PROJECTION}
    compact=dict(schema='exact-bound-independent-static-worker-compact-v1',
        plan=stream_pin(Path(planpath)),worker=stream_pin(Path(workerpath)),
        transport=stream_pin(Path(__file__)),activation=stream_pin(Path(activationpath)),
        source_manifest=contract['wrapper_source_manifest_pin'],
        full_audit=stream_pin(Path(plan['outputs']['result'])),projection=scalar,
        complete_group_count=len(result['groups_checked']),
        worker_seconds_before_compact_status_serialization=time.perf_counter()-started,
        semantic_scope='Projection of same unchanged full static audit; no trace/proof/RL qualification',
        full_resource_accepted=False,all_five_qualification=False)
    write_new(plan['outputs']['compact'],compact)
    if Path(plan['outputs']['compact']).stat().st_size>contract['compact_maximum_bytes']:
        raise ValueError('compact status transport bound exceeded; no retry')


def validate_compact(plan,planpath,workerpath,activationpath):
    contract=plan['compact_transport_contract']
    compact=read_small(plan['outputs']['compact'],contract['compact_maximum_bytes'])
    expected=dict(schema='exact-bound-independent-static-worker-compact-v1',
        plan=stream_pin(Path(planpath)),worker=stream_pin(Path(workerpath)),
        transport=stream_pin(Path(__file__)),activation=stream_pin(Path(activationpath)),
        source_manifest=contract['wrapper_source_manifest_pin'],
        full_audit=stream_pin(Path(plan['outputs']['result'])),
        full_resource_accepted=False,all_five_qualification=False)
    if any(compact.get(k)!=v for k,v in expected.items()):
        raise ValueError('whole closed audit/plan/worker/activation/source compact binding')
    p=compact['projection']
    if set(p)!=set(PROJECTION) or p['selector']!=plan['selector']:
        raise ValueError('exact complete scalar projection')
    expected_scope=dict(status='passed_independent_frozen_curriculum_context_family_pool_audit',
        static_context_pool_accepted=True,trace_accepted=False,certificate_accepted=False,
        RL_full_pool_capacity=64,primitive_license_count=229,non_assumption_witness_count=226,
        source_body_count=171,single_types=171,pair_types=29241,whole_target_logical_checks=0,
        native_queries=0,native_accepted=False,searches=0,training=0)
    if any(type(p[k]) is not type(v) or p[k]!=v for k,v in expected_scope.items()):
        raise ValueError('same full audit static scope/control census, no scope escalation')
    identity=contract['expected_scalar_identity']
    if set(identity)!={'selector','partition','model_epoch','context_id','compiled_context_pin','preparation_evidence_pin'}:
        raise ValueError('actual plan binds complete expected small context identity')
    if any(p[k]!=v for k,v in identity.items()):
        raise ValueError('compact scalar identity differs from actual frozen context plan')
    count=compact['complete_group_count']
    if (type(count) is not int or count<0 or count!=contract['expected_complete_group_count']
            or type(p['RL_full_pool_capacity_satisfied']) is not bool
            or p['RL_full_pool_capacity_satisfied']!=(count<=64)):
        raise ValueError('complete pool census/capacity; no trimming')
    return compact


def raw_usage(usage):
    return {name:getattr(usage,name) for name in dir(usage) if name.startswith('ru_')}


def emit_closed_SELF_and_exit(role,started,exit_code):
    """After every artifact is closed: fixed52-byte postlude then os._exit.

    SELF ru_maxrss remains RAW, with no platform conversion or rolled-child
    subtraction. The separately reviewed outer reserve must cover struct pack,
    bounded writes/close-on-_exit and hard exit after this last SELF reading.
    """
    closed=time.perf_counter();usage=resource.getrusage(resource.RUSAGE_SELF)
    frame=POSTLUDE.pack(b'GCTSCMP1',role,exit_code,0,os.getpid(),int(usage.ru_maxrss),
        closed-started,started,closed)
    try:
        offset=0
        while offset<len(frame):
            written=os.write(1,frame[offset:])
            if written<=0:raise OSError('closed SELF postlude failed')
            offset+=written
    except BaseException:os._exit(2)
    os._exit(exit_code)


def read_closed_SELF(path,role,pid):
    with Path(path).open('rb') as stream:raw=stream.read(POSTLUDE.size+1)
    if len(raw)!=POSTLUDE.size:raise ValueError('exact fixed SELF postlude and no stray stdout')
    magic,actual_role,code,reserved,actual_pid,rss,elapsed,start,closed=POSTLUDE.unpack(raw)
    if (magic!=b'GCTSCMP1' or actual_role!=role or actual_pid!=pid or reserved!=0
            or code not in (0,1,2) or elapsed<0 or closed<start):
        raise ValueError('terminal SELF raw identity/clock/frame')
    return dict(role=role,pid=pid,exit_code=code,SELF_ru_maxrss_raw=rss,
        seconds_after_all_artifact_close_before_fixed_postlude=elapsed,
        entry_monotone_clock=start,last_closed_monotone_clock=closed,
        remaining_postlude='Fixed52-byte pack/write then os._exit; separately ROOT-reviewed reserve required',
        terminal_frame=stream_pin(Path(path)))
