"""SOURCE ONLY metadata finalizer; ROOT owns future invocation.

No compiled model/evidence decoding and no scientific imports or calls. The
exact artifacts must already exist after a fully reaped producer phase. There
are no placeholder pins or default claims of a successful preparation.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CURRICULUM = ROOT / '.gcts-active/family-curriculum-context-source-v3-20261012'
SELECTORS = ('donor-two-guards', 'donor-two-equalities', 'donor-repeated-guard',
             'donor-repeated-equality', 'heldout-mixed-guard-equality')


def pin(path, relative=False):
    path = Path(path).resolve(); sha = hashlib.sha256(); count = 0
    with path.open('rb') as stream:
        for raw in iter(lambda:stream.read(65536), b''):
            sha.update(raw); count += len(raw)
    return dict(path=str(path.relative_to(ROOT)) if relative else str(path),
                sha256=sha.hexdigest(), bytes=count)


def path_of(record):
    path = Path(record['path'])
    return path if path.is_absolute() else ROOT/path


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition: raise ValueError(message)


def bounded(value, maximum):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum


def terminal_contract(selector):
    """Literal future owned receipt contracts, shared with actual worker."""
    required = {
        'producer_outcome': dict(status='completed_fresh_context_preparation_pending_independent_gate',
            selector=selector, native_queries=0, target_searches=0, model_constructions=1, new_RL_training=False),
        'producer_lifetime': dict(status='passed_full_fresh_context_preparation_lifetime', phase_kind='preparation',
            supervisor_exit=0, supervisor_reaped=True, worker_reaped_confirmed=True, cleanup_reason=None),
        'producer_supervision': dict(status='passed_owned_fresh_context_preparation', phase_kind='preparation',
            child_exit=0, child_reaped=True, resource_reason=None, watchdog_error=None, OS_hard_limit_claim=False),
        'producer_activation': dict(schema='ROOT-frozen-curriculum-preparation-activation-v1', authorized=True,
            selector=selector, status='ROOT_authorized_exact_frozen_curriculum_context_preparation_v1'),
        'root_terminal': dict(schema='ROOT-actual-frozen-curriculum-preparation-terminal-v1', selector=selector,
            owner_exit_code=0, owner_terminal_reaped=True, worker_terminal_reaped=True, full_resource_accepted=True),
        'ROOT_source_review': dict(schema='ROOT-frozen-curriculum-static-source-review-v1',
            full_sources_reviewed=True, source_review_passed=True, scientific_calls=0),
    }
    bindings = []
    def bind(record, field, role):
        bindings.append(dict(record=record, field=field, role=role, path_encoding='relative'))
    for record in ('producer_outcome','producer_lifetime','producer_supervision','producer_activation'):
        bind(record, 'plan', 'producer_plan')
    for record, field, role in (
        ('producer_lifetime','supervision','producer_supervision'),
        ('producer_supervision','outcome','producer_outcome'),
        ('producer_supervision','root_activation','producer_activation'),
        ('producer_outcome','compiled_context','compiled_context'),
        ('producer_outcome','preparation_evidence','preparation_evidence'),
        ('root_terminal','preparation_plan','producer_plan'),
        ('root_terminal','compiled_context','compiled_context'),
        ('root_terminal','preparation_evidence','preparation_evidence'),
        ('root_terminal','outcome','producer_outcome'),
        ('root_terminal','lifetime','producer_lifetime'),
        ('root_terminal','supervision','producer_supervision'),
        ('root_terminal','activation','producer_activation'),
        ('ROOT_source_review','curriculum_source_plan','curriculum_source_plan'),
        ('ROOT_source_review','independent_source_plan','independent_source_plan')):
        bind(record,field,role)
    return dict(required_fields=required, nested_pin_bindings=bindings, ceilings={
        'producer_lifetime': dict(full_supervisor_seconds_including_receipt_write=60,
                                  conservative_host_peak_bytes=536870912),
        'producer_supervision': dict(supervisor_seconds_before_receipt_write=55,
                                     conservative_host_peak_bytes=536870912),
        'root_terminal': dict(full_outer_seconds_including_receipt_write=60,
                              conservative_combined_peak_bytes=536870912)})


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in SELECTORS:
        raise ValueError('pass exact selector, ROOT normalized full producer terminal, and ROOT full source review paths')
    selector = sys.argv[1]; source = read(HERE/'source-plan-v1.json')
    checked = {}
    for record in source['sources'] + source['libraries'] + source['inputs'] + source['preserved']:
        actual = pin(path_of(record))
        expected = {k:record[k] for k in ('path','sha256','bytes')}
        require(actual == expected, 'immutable independent closure changed: '+record['path'])
        require(actual['path'] not in checked or checked[actual['path']] == actual, 'consistent exact byte identity')
        checked[actual['path']] = actual
    prep_path = CURRICULUM/('preparation-'+selector+'-plan-v1.json'); preparation = read(prep_path)
    require(preparation['selector'] == selector and preparation['schema']=='frozen-curriculum-family-preparation-plan-v1',
            'exact frozen selector preparation plan')
    frozen_preparation = next(r for r in source['inputs'] if r['role']=='preparation_plan_'+selector)
    require(pin(prep_path) == {k:frozen_preparation[k] for k in ('path','sha256','bytes')},
            'exact frozen selector plan input')
    cfg = preparation['phase']; base = CURRICULUM
    terminal_path, review_path = [Path(arg).resolve() for arg in sys.argv[2:]]
    roles = dict(producer_plan=prep_path, preparation_plan=prep_path,
        compiled_context=base/preparation['outputs']['compiled_context'],
        preparation_evidence=base/preparation['outputs']['preparation_evidence'],
        producer_outcome=base/cfg['outcome'], producer_lifetime=base/cfg['lifetime'],
        producer_supervision=base/cfg['supervision'], producer_activation=base/preparation['activation_basename'],
        root_terminal=terminal_path, ROOT_source_review=review_path,
        curriculum_source_plan=CURRICULUM/'source-plan-v1.json', independent_source_plan=HERE/'source-plan-v1.json')
    for role in ('donor_primitive_model','family_projection','original_body_plan','source_certificate','source_schemas',
                 'master_contract','repository_contract','curriculum_reference','frozen_donor_split',
                 'frozen_RL_protocol','frozen_selection_binding'):
        record = next(r for r in source['inputs'] if r['role']==role)
        roles[role] = path_of(record)
    actual_pins = {role:pin(path) for role,path in roles.items()}
    contract = terminal_contract(selector)
    records = {role:read(roles[role]) for role in contract['required_fields']}
    for role, fields in contract['required_fields'].items():
        for field, expected in fields.items():
            require(type(records[role][field]) is type(expected) and records[role][field] == expected,
                    'actual owned terminal field '+role+'/'+field)
    for binding in contract['nested_pin_bindings']:
        require(records[binding['record']][binding['field']] == pin(roles[binding['role']], relative=True),
                'exact actual nested receipt pin '+binding['record']+'/'+binding['field'])
    for role, fields in contract['ceilings'].items():
        for field, maximum in fields.items():
            require(bounded(records[role][field],maximum), 'actual complete resource ceiling '+role+'/'+field)
    directory = HERE/'outputs'/selector
    require(not directory.exists(), 'one immutable static attempt per selector; successor required for retry')
    plan_path = HERE/('actual-static-'+selector+'-plan-v1.json')
    plan = dict(schema='frozen-curriculum-independent-actual-static-plan-v1',
        status='frozen_actual_inputs_pending_ROOT_activation', plan_path=str(plan_path), selector=selector, stage='static',
        sources=source['sources'], libraries=source['libraries'],
        inputs=[dict(role=role, **record) for role,record in actual_pins.items()],
        preserved=sorted(checked.values(),key=lambda r:r['path']), runtime=source['runtime'], limits=source['limits'],
        worker_path=str(HERE/'curriculum_independent_worker_v1.py'),
        owner_path=str(HERE/'curriculum_independent_owner_v1.py'),
        outputs={name:str(directory/('static-'+name+'-v1.'+('txt' if name in ('stdout','stderr') else 'json')))
                 for name in ('result','lifetime','stdout','stderr')},
        activation_path=str(HERE/('root-static-'+selector+'-activation-v1.json')),
        required_activation_schema='ROOT-independent-frozen-curriculum-static-activation-v1',
        required_result_status='passed_independent_frozen_curriculum_context_family_pool_audit',
        required_owner_success_status='passed_owned_independent_frozen_curriculum_context_family_pool_audit',
        producer_terminal_contract=contract, actual_execution_authorized=False, ROOT_sole_actual_owner=True,
        scientific_calls_by_metadata_finalizer=0, no_compiled_model_or_evidence_decoded=True,
        acceptance_scope='Finite per-context licenses/source bodies/full initial domains/whole pool only; no DFS/RNG/training/native or target-proof acceptance',
        ROOT_full_outer_audit_requirement=dict(maximum_seconds=180, maximum_combined_peak_bytes=536870912,
            owner_terminal_reaped=True, worker_terminal_reaped=True,
            charge='Exact owner imports/setup/reconstruction/full domains/mutants/result and lifetime serialization/exit/reap; ROOT outer receipt final write also timed'))
    for role,path in roles.items(): require(pin(path)==actual_pins[role], 'actual input changed during metadata finalization')
    directory.mkdir(parents=True, exist_ok=False)
    with plan_path.open('x') as stream:
        json.dump(plan,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(actual_static_plan=pin(plan_path,relative=True),scientific_calls=0),indent=2))


if __name__ == '__main__': main()
