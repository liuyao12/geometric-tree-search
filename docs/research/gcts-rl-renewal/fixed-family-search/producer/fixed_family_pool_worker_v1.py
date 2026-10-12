"""Prospective ROOT-owned single fixed-pool lane. SOURCE ONLY until activation.

No scientific execution occurs on import. Exact raw inputs, accepted static
gate and source/runtime closure must be frozen before this entry is dispatched.
No native check, training, preparation search or authored target word lookup.
"""
import hashlib
import gzip
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time
from fixed_family_pool_adapter_v1 import fixed_pool_search
from fixed_family_pool_registration_v1 import fixed_pool_registration

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def pin(path):
    path=Path(path);digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):digest.update(block)
    return dict(path=str(path.relative_to(ROOT)),sha256=digest.hexdigest(),bytes=path.stat().st_size)


def module(name,path):
    # Exact original sibling imports of the old search helper remain available.
    path=Path(path);sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result)
    return result


def main():
    started=time.perf_counter()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('fixed pool complete worker alarm')))
    signal.alarm(170)
    planpath=HERE/'search-plan-v1.json';plan=json.loads(planpath.read_text())
    for item in plan['sources']+plan['inputs']+plan['preserved_files']:
        if pin(ROOT/item['path'])!={k:item[k] for k in ('path','sha256','bytes')}:
            raise ValueError('exact fixed-pool source/input prerequisite: '+item['path'])
    runtime=plan['runtime'];binary=Path(sys.executable).resolve()
    if (runtime['executable']!=sys.executable or runtime['platform']!=sys.platform
            or runtime['binary']!=dict(path=str(binary),sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),bytes=binary.stat().st_size)):
        raise ValueError('exact resolved Python runtime binary')
    activationpath=HERE/'root-activation-v1.json';activation=json.loads(activationpath.read_text())
    if (activation['status']!='root_authorized_bounded_fixed_whole_family_pool_geometry_search'
            or activation['plan']!=pin(planpath)):
        raise ValueError('separately reviewed exact ROOT dispatch required')
    roles={item['role']:ROOT/item['path'] for item in plan['inputs']}
    static=json.loads(roles['static_pool_result'].read_text());static_lifetime=json.loads(roles['static_pool_lifetime'].read_text())
    if (static['status']!='passed_complete_independent_static_family_pool_audit'
            or static_lifetime['status']!='passed_owned_independent_static_family_pool_audit'):
        raise ValueError('actual accepted static-pool gate required before any engine/model load')
    imported=time.perf_counter()
    search=module('fixed_pool_prior_search_helpers',roles['prior_search_worker'])
    proposals=module('fixed_pool_frozen_proposal_relation',roles['proposal_module'])
    life=search.load_lifecycle(roles['frozen_lifecycle_kernel'])
    import_seconds=time.perf_counter()-imported;core=life.core
    prepared=time.perf_counter()
    graph=core.frozen_model(ROOT,json.loads(roles['prior_full_model_plan'].read_text()))
    if graph.model_epoch!=plan['model_epoch']:raise ValueError('unchanged point model epoch')
    original=life.frozen_family_authority(graph,json.loads(roles['passed_full_lifecycle_producer_plan'].read_text()))
    # Use the existing strict scientific file convention, no authored example
    # read as guidance. The compact example is decoded then discarded.
    with gzip.open(roles['pool_evidence'],'rt') as stream:evidence=json.load(stream)
    projection=json.loads(roles['checked_compact_family_projection'].read_text());projection.pop('example',None)
    preparation_plan=json.loads(roles['preparation_plan'].read_text())
    authority,descriptors,registration=fixed_pool_registration(graph,life,proposals,original,projection,
        preparation_plan,pin(roles['preparation_plan']),evidence,static,static_lifetime,plan['static_gate_pins'])
    preparation_seconds=time.perf_counter()-prepared
    spec=plan['observations'][0]
    if len(plan['observations'])!=1 or spec['mode']!='fixed-whole-family-pool':raise ValueError('one fixed-pool lane only')
    result=fixed_pool_search(graph,authority,descriptors,life,search,
        attempts=spec['attempts'],seconds=spec['seconds'],event_ceiling=spec['event_ceiling'])
    result['decoded_certificate']=(search.decode(graph,result['point_certificate'],core)
                                   if result['point_certificate'] is not None else None)
    result.update(observation_id=spec['id'],body_authority_epoch=authority.epoch,
        original_body_authority_epoch=original.epoch,validated_source_body_count=len(original.bodies),
        preparation_costs=dict(full_point_model_body_pool_decode_and_registration_seconds=preparation_seconds,
            **registration),static_pool_gate=dict(plan=plan['static_gate_pins']['plan'],result=plan['static_gate_pins']['result'],
            lifetime=plan['static_gate_pins']['lifetime']))
    path=HERE/(spec['id']+'-result-v1.json.gz');serialization=time.perf_counter()
    search.save_gzip(path,result);serialization_seconds=time.perf_counter()-serialization
    observation=dict(id=spec['id'],mode=spec['mode'],status=result['status'],result=pin(path),
        attempts=result['attempts'],seconds=result['seconds'],events=len(result['events']),
        serialization_seconds=serialization_seconds,preparation_costs=result['preparation_costs'],
        decoded_certificate=result['decoded_certificate'] is not None)
    for item in plan['sources']+plan['inputs']+plan['preserved_files']:
        if pin(ROOT/item['path'])!={k:item[k] for k in ('path','sha256','bytes')}:raise ValueError('post-run exact pin mismatch')
    outcome=dict(status='completed_bounded_fixed_whole_family_pool_geometry_observation_pending_independent_audit',
        observations=[observation],plan=pin(planpath),root_activation=pin(activationpath),
        worker_seconds_before_final_receipt_write=time.perf_counter()-started,
        scientific_import_seconds=import_seconds,target_search_observations=1,native_queries=0,
        native_authority_activated=False,new_RL_training=False,authored_words_used_as_hints=0,
        claim='Automatic recomposition of checked conditional source bodies and fixed whole-union hints; returned tape and any proof require separate independent acceptance.')
    with (HERE/'search-outcome-v1.json').open('x') as stream:
        json.dump(outcome,stream,indent=2,allow_nan=False);stream.write('\n')
    signal.alarm(0);print(json.dumps(outcome),flush=True)


if __name__=='__main__':main()
