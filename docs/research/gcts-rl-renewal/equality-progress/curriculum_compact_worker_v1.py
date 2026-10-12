"""ROOT-only future frozen-curriculum context/body/domain/pool static auditor.

No scientific imports at module load. Only ROOT may execute this new static gate. Source-only until actual inputs are
separately byte-frozen and ROOT activates one bounded phase. Static acceptance
and future search-trace acceptance are separate processes/receipts. This file has no search-trace adapter. The old
positive proof is provenance, never a replacement for new-model checking.
"""
import copy
import hashlib
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    path = Path(path).resolve(); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''): h.update(block)
    return dict(path=str(path), sha256=h.hexdigest(), bytes=path.stat().st_size)


def relative(path):
    item = pin(path); item['path'] = str(Path(path).resolve().relative_to(ROOT)); return item


def verify(plan):
    checked = {}
    for group in ('sources', 'libraries', 'inputs', 'preserved'):
        for item in plan[group]:
            checked.setdefault(item['path'], pin(item['path']))
            if checked[item['path']] != {k:item[k] for k in ('path','sha256','bytes')}:
                raise ValueError('exact independent closure: ' + item['path'])
    return len(checked)


def load(role, paths, name):
    location = Path(paths[role]); sys.path.insert(0, str(location.parent))
    spec = importlib.util.spec_from_file_location(name, location)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module); return module


def libraries(plan):
    paths = {r['role']:r['path'] for r in plan['libraries']}
    p = load('independent_point', paths, 'full_point_oracle_v1')
    b = load('independent_families', paths, 'full_family_registry_v1')
    symbolic = load('independent_symbolic', paths, 'independent_aggregate_audit_v1')
    expansion = load('independent_expansion', paths, 'fresh_transfer_expansion_v1')
    static = load('independent_static_pool', paths, 'fresh_transfer_static_pool_v1')
    context = load('independent_context', paths, 'frozen_curriculum_acceptance_oracle_v1')
    return p,b,symbolic,expansion,static,context


def validate_terminal(roles, stage, plan, p, b):
    """Freeze future exact status/field contracts before dispatch, no launch flag proof."""
    contract = plan['producer_terminal_contract']
    required = ('producer_plan','producer_outcome','producer_lifetime','producer_supervision','producer_activation','root_terminal','ROOT_source_review')
    p.need(all(role in roles for role in required), 'all actual ROOT-owned terminal artifacts required')
    records = {name:p.read(roles[name]) for name in required}
    p.need(stage == 'static', 'separate static/trace acceptance phase')
    for name, fields in contract['required_fields'].items():
        p.need(name in records, 'declared actual receipt role')
        for field,value in fields.items(): b.equal(records[name][field],value,'owned terminal field '+name+'/'+field)
    for binding in contract['nested_pin_bindings']:
        b.equal(records[binding['record']][binding['field']],
            relative(roles[binding['role']]) if binding['path_encoding']=='relative' else pin(roles[binding['role']]),
            'actual terminal nested raw pin '+binding['record']+'/'+binding['field'])
    for name, fields in contract['ceilings'].items():
        for field, maximum in fields.items():
            value=records[name][field]
            p.need(type(value) in (float,int) and value >= 0 and value <= maximum, 'owned actual resource ceiling')
    return records


def rebuild(plan, p,b,symbolic,expansion,static,context):
    """New context/licenses/171 bodies/canonical full pool rechecked each phase."""
    roles={r['role']:Path(r['path']) for r in plan['inputs']}
    preparation=p.read(roles['preparation_plan']); compiled=p.read(roles['compiled_context'])
    b.equal(preparation['selector'],plan['selector'],'same independently activated selector')
    donor=p.read(roles['donor_primitive_model']); evidence=p.read(roles['preparation_evidence'])
    prep_pin=relative(roles['preparation_plan'])
    b.equal(evidence['plan'],prep_pin,'bound preparation plan')
    b.equal(evidence['sources'],preparation['sources'],'entire original preparation source byte relation')
    b.equal(evidence['inputs'],preparation['inputs'],'entire original preparation role relation')
    b.equal(evidence['compiled_context_pin'],relative(roles['compiled_context']),'exact saved fresh context bytes')
    declared={r['role']:r for r in preparation['inputs']}
    for role,audit_role in [('primitive_model','donor_primitive_model'),('complete_family_projection','family_projection'),
            ('old_complete_body_plan','original_body_plan'),('curriculum_reference','curriculum_reference'),
            ('frozen_donor_split','frozen_donor_split'),('frozen_RL_protocol','frozen_RL_protocol'),
            ('frozen_selection_binding','frozen_selection_binding')]:
        b.equal({k:declared[role][k] for k in ('path','sha256','bytes')},relative(roles[audit_role]),'same frozen fresh producer prerequisite '+role)
    documents = {r:p.read(roles[r]) for r in ('curriculum_reference','frozen_donor_split','frozen_RL_protocol','frozen_selection_binding')}
    setup=time.perf_counter(); accepted=context.fresh_data(donor,compiled,preparation,prep_pin,p,b,symbolic,documents)
    timing={'fresh_independent_context_and_229_licenses_seconds':time.perf_counter()-setup}
    projected=p.read(roles['family_projection']);projected.pop('example',None)
    source_certificate=p.read(roles['source_certificate']);schemas=p.read(roles['source_schemas'])
    original_plan=p.read(roles['original_body_plan'])
    body_start=time.perf_counter();Pool=context.fresh_pool_class(static)
    pool=Pool(p,b,accepted,original_plan,source_certificate,schemas,projected,expansion)
    timing['all171_fresh_conditional_body_checks_seconds']=time.perf_counter()-body_start
    enumeration=time.perf_counter();pool.enumerate()
    timing['full171_29241_binding_embedding_union_enumeration_seconds']=time.perf_counter()-enumeration
    compare=time.perf_counter();counts=context.audit_preparation(accepted,pool,evidence,p,b)
    timing['all24_raw_domains_and_entire_preparation_comparison_seconds']=time.perf_counter()-compare
    return accepted,pool,counts,roles,timing,donor,compiled,preparation,evidence,documents


def static_run(plan):
    began=time.perf_counter();checked=verify(plan)
    p,b,symbolic,expansion,static,context=libraries(plan)
    roles={r['role']:Path(r['path']) for r in plan['inputs']}
    terminal=validate_terminal(roles,'static',plan,p,b)
    outcome=terminal['producer_outcome']
    b.equal(outcome['compiled_context'],relative(roles['compiled_context']),'actual preparation context output')
    b.equal(outcome['preparation_evidence'],relative(roles['preparation_evidence']),'actual complete preparation output')
    accepted,pool,counts,roles,timings,donor,compiled,prep,evidence,documents=rebuild(plan,p,b,symbolic,expansion,static,context)
    b.equal(outcome['model_epoch'],accepted['model_epoch'],'actual fresh model epoch')
    b.equal(outcome['group_authority_epoch'],pool.epoch,'actual complete pool epoch')
    b.equal(outcome['original_body_authority_epoch'],pool.original_epoch,'actual conditional source-body epoch')
    b.equal(outcome['candidate_count'],counts['initial_complete_candidates'],'actual whole initial universe')
    b.equal(outcome['complete_pool_group_count'],len(pool.groups),'actual complete grammar result')
    for name in ('curriculum_binding','hypothesis_codes','target_code'):
        b.equal(outcome[name],accepted[name],'actual frozen curriculum outcome '+name)
    b.equal(outcome['selector'],plan['selector'],'exact actual selector')
    b.equal(outcome['partition'],accepted['curriculum_binding']['partition'],'exact actual split partition')
    b.equal(outcome['RL_full_pool_capacity_satisfied'],len(pool.groups)<=64,'preserved complete pool capacity disposition')
    tests=time.perf_counter()
    controls=context.context_controls(donor,compiled,prep,relative(roles['preparation_plan']),p,b,symbolic,documents)
    pool_controls=pool.mutations()
    timings['actual_context_and_pool_payload_controls_seconds']=time.perf_counter()-tests
    verify(plan)
    return dict(status='passed_independent_frozen_curriculum_context_family_pool_audit',plan=relative(plan['plan_path']),
        static_context_pool_accepted=True,trace_accepted=False,certificate_accepted=False,
        selector=plan['selector'], partition=accepted['curriculum_binding']['partition'],
        curriculum_binding=accepted['curriculum_binding'], hypothesis_codes=accepted['hypothesis_codes'], target_code=accepted['target_code'],
        RL_full_pool_capacity=64, RL_full_pool_capacity_satisfied=len(pool.groups)<=64,
        RL_episode_or_training_accepted=False, full_DFS_or_RNG_replay_accepted=False,
        compiled_context_pin=relative(roles['compiled_context']),preparation_evidence_pin=relative(roles['preparation_evidence']),
        model_epoch=accepted['model_epoch'],context_id=accepted['context_id'],
        original_Gamma=accepted['problem']['gamma'],target=accepted['problem']['target'],
        primitive_license_count=229,non_assumption_witness_count=226,source_body_count=171,
        single_types=171,pair_types=29241,source_expansion_counts=pool.source_counts,
        independent_source_logical_receipts=pool.source_receipts,independent_primitive_rules=accepted['primitive_rules'],
        fresh_context_assumptions=accepted['assumptions'],group_authority_epoch=pool.epoch,
        original_body_authority_epoch=pool.original_epoch,declared_interface_projection_sha256=p.digest(pool.interfaces),
        groups_checked=[dict(pool_index=g['pool_index'],descriptor_id=g['descriptor_id'],descriptor_sha256=p.digest(g),
            fixed_priority=g['fixed_priority'],occurrence_members=g['component_member_occurrences'],
            distinct_members=g['distinct_member_count'],shared_members=g['shared_member_count']) for g in pool.groups],
        complete_census=counts['complete_census'],complete_initial_domain_census=counts,
        independently_reconstructed_initial_state_sha256=p.digest(accepted['state'].semantic()),
        context_controls=controls,pool_controls=pool_controls,phase_timings=timings,
        worker_seconds_before_result_serialization=time.perf_counter()-began,unique_raw_byte_pins=checked,
        whole_target_logical_checks=0,native_queries=0,native_accepted=False,searches=0,training=0,
        prior_acceptance_scope='Source/theory/body provenance only. Every new recipient license, body transport, model point and pool field checked independently in this phase.',
        read_scope='Known pinned standard JSON; compact authored example decoded then discarded. No authored proof words supply proposal or acceptance.',
        limitations=['Static acceptance of finite context/bodies/all initial primitive candidates/complete canonical proposal grammar only; no target search or returned proof acceptance.',
            'All171 bodies are existing authored/certified conditional interfaces; this is within-library transfer, not unseen theorem-family generalization.',
            'Native/shared request-independent Wang compiler correspondence remains open.',
            'Payload mutations are actual context-gate calls and per-group comparisons, not full altered-file/process replays; duplicate-key adversarial parser theorem is not claimed.'])


def main():
    # Only metadata preflight/post-audit transport changes below this point.
    # All preceding audit/guard functions are byte-identical to V3.
    started=time.perf_counter()
    from compact_static_transport_v1 import (require_contract,read_small,emit_compact,
        emit_closed_SELF_and_exit)
    planpath=Path(sys.argv[1]).resolve();plan=json.loads(planpath.read_text())
    contract=require_contract(plan,planpath,Path(__file__))
    if any(Path(plan['outputs'][name]).exists() for name in ('result','compact')):
        raise ValueError('closed immutable audit/compact output already exists; no rerun')
    activationpath=Path(plan['activation_path'])
    activation=read_small(activationpath,contract['compact_maximum_bytes'])
    if (activation.get('schema')!='ROOT-independent-frozen-curriculum-compact-static-activation-v1'
            or activation.get('authorized') is not True or activation.get('plan')!=relative(planpath)
            or activation.get('selector')!=plan['selector']):
        raise ValueError('exact separate ROOT compact static activation required before scientific imports')
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('independent compact static child lifetime')))
    signal.setitimer(signal.ITIMER_REAL,max(.001,170-(time.perf_counter()-started)))
    result=static_run(plan)
    result['plan']=relative(planpath)
    result['kernel_peak_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    with Path(plan['outputs']['result']).open('x') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')
    verify(plan)
    emit_compact(result,plan,planpath,Path(__file__),activationpath,started)
    signal.setitimer(signal.ITIMER_REAL,0)
    # Full audit and compact receipt are closed. SELF is read after these
    # metadata costs; only a fixed52byte frame and os._exit remain.
    emit_closed_SELF_and_exit(1,started,0)


if __name__=='__main__':main()
