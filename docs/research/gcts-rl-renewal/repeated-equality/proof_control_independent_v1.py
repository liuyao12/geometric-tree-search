"""SOURCE ONLY: independent outer adapter for one future complete raw tape.

No producer compiler/graph/controller/order/decoder is imported or used as
acceptance authority. ROOT passes already pinned independent libraries after
the pending exact input, clock, owner and activation freezes. No search is run
by this auditor. Its own complete owned resource qualification is still a
separate post-terminal gate, not a field this function may self-accept.
"""
import copy
import time
from proof_control_bindings_v1 import (
    VERSION, LIMITS, MODES, need, same, phase_authority, library_bindings,
    context_receipt_gate, owned_result_gate,
)


INDEPENDENT_LIBRARY_ROLES = ('curriculum_worker', 'context', 'point', 'body',
    'symbolic', 'expansion', 'static_pool', 'transactions', 'hints', 'tape', 'positive')


def audit_one_lane(bundle, static_resource_closure, producer_result, producer_resource,
                   producer_resource_closure, libraries, *, selector, mode,
                   activation, source_contract):
    """Future separately ROOT-owned full reconstruction of one exact lane.

    Lower-level Tape.run checks every retained event/node/domain/order/point/
    hint/rollback and conditionally checks all24 primitive rows. It never takes
    producer placement/formula commands as independent expected proof authority.
    """
    began = time.perf_counter()
    need(mode in MODES, 'one of the two predeclared deterministic lanes')
    context_pins = {role: artifact.pin() for role, artifact in bundle.items()}
    static_closure_pins = {path: artifact.pin() for path, artifact in sorted(static_resource_closure.items())}
    producer_closure_pins = {path: artifact.pin() for path, artifact in sorted(producer_resource_closure.items())}
    input_pins = {'context': context_pins, 'resource_closure': static_closure_pins,
                 'producer_result': producer_result.pin(), 'producer_resource': producer_resource.pin(),
                 'producer_resource_closure': producer_closure_pins}
    contract = phase_authority(activation, source_contract, 'independent', selector, mode, input_pins)
    need(set(libraries) == set(INDEPENDENT_LIBRARY_ROLES), 'all exact independent libraries')
    library_bindings(libraries, contract['library_bindings'])
    data = context_receipt_gate(bundle, selector, static_resource_closure)
    owned = owned_result_gate(producer_resource, producer_result, producer_resource_closure,
                             phase='producer', selector=selector, mode=mode)
    result = producer_result.json()
    same(result['context_control_schema'], VERSION, 'future narrow proof-control schema')
    same(result['selector'], selector, 'actual returned selector')
    same(result['mode'], mode, 'actual deterministic lane')
    same(result['observation_id'], selector + '/' + mode, 'prospective observation identity')
    same(result['fresh_static_gate'], context_pins, 'complete exact accepted static input bundle')
    same(result['resource_closure_pins'], static_closure_pins, 'complete static raw closure')
    same(result['limits'], {'attempts': LIMITS['attempts'], 'seconds': LIMITS['seconds'],
                           'events': LIMITS['event_ceiling']}, 'same exact finite search limits')
    same(result['RNG_draws'], 0, 'no RNG stream')
    for field, value in [('target_proof_accepted', False), ('trace_accepted', False),
            ('full_resource_accepted', False), ('all_five_qualification', False),
            ('native_authority_activated', False), ('new_RL_training', False),
            ('native_queries', 0), ('atomic_macro_moves', 0), ('authored_words_used_as_hints', 0)]:
        same(result[field], value, 'producer cannot supply acceptance: ' + field)
    same(owned['source_contract'], result['source_contract'], 'actual producer source contract')
    same(owned['activation'], result['activation'], 'actual producer activation')
    # Rebuild using the genuinely accepted static plan and independent worker;
    # no target route, successful history or producer model object is supplied.
    plan = data['fresh_static_plan']; worker = libraries['curriculum_worker']
    p, b, symbolic = libraries['point'], libraries['body'], libraries['symbolic']
    worker.verify(plan)
    accepted, pool, counts, roles, timings, donor, compiled, prep, evidence, documents = worker.rebuild(
        plan, p, b, symbolic, libraries['expansion'], libraries['static_pool'], libraries['context'])
    # File reading inside the existing independent library remains exactly
    # pinned by the complete accepted static plan before and after reconstruction.
    for role, field in [('compiled_context', 'compiled_context'), ('preparation_evidence', 'preparation_evidence')]:
        same(worker.relative(roles[field]), context_pins[role], 'same raw rebuilt artifact')
    same(accepted['curriculum_binding']['selector'], selector, 'independently literal-resolved selector')
    static = data['fresh_static_result']
    for key in ('curriculum_binding', 'hypothesis_codes', 'target_code', 'model_epoch', 'context_id'):
        same(accepted[key], static[key], 'same independently reconstructed static field: ' + key)
    same(pool.epoch, static['group_authority_epoch'], 'complete source-bound group authority')
    same(pool.original_epoch, static['original_body_authority_epoch'], 'all original bodies')
    same(counts['complete_census'], static['complete_census'], 'entire repeated static census')
    same(result['curriculum_binding'], accepted['curriculum_binding'], 'original whole context')
    same(result['hypothesis_codes'], accepted['hypothesis_codes'], 'ordered occurrence code list')
    same(result['target_code'], accepted['target_code'], 'original target code')
    same(result['partition'], accepted['curriculum_binding']['partition'], 'exact original partition')
    same(result['complete_saved_pool_count'], len(pool.groups), 'all feasible groups available')
    same(result['original_body_authority_epoch'], pool.original_epoch, 'unchanged body authority')
    same(result['group_authority_epoch'], pool.epoch, 'unchanged complete pool authority')
    need(len(pool.groups) <= 64, 'same complete capacity, no trim')
    target = accepted['problem']['target']
    fixed = sorted(accepted['model']['boundary']['fixed_exterior_m'] +
                   accepted['model']['boundary']['fixed_target_m'])
    transactions = libraries['transactions']
    state = transactions.PointState(24, accepted['state'].recipes, fixed, [0] * 24,
                                    accepted['model_epoch'])
    for key in accepted['state'].order:
        state.apply(key, generation=0)
    same(state.semantic(), accepted['state'].semantic(), 'all original licensed hypothesis seeds')
    descriptors = pool.groups if mode == 'fixed-whole-family-pool' else []
    epoch = pool.epoch if mode == 'fixed-whole-family-pool' else pool.original_epoch
    tape_library = libraries['tape']
    Measured = tape_library.measured_transactions(libraries['hints'].FixedPoolTransactions, p, b)
    tx = Measured(state, descriptors, epoch, accepted['model']['context'],
                  accepted['data']['authority']['epoch'], p.digest(accepted['data']['formula_codes']),
                  p, b, transactions, mode, None, accepted['data']['formula_codes'])
    tape = tape_library.Tape(result, tx, {'attempts': 128, 'seconds': 20, 'event_ceiling': 2000},
        p, b, transactions, libraries['positive'], symbolic, accepted['model'], accepted['data'],
        accepted['source_bindings'], fixed, target)
    checked = tape.run()
    # Do not call legacy positive_controls: swapping duplicate equal hypothesis
    # formulas may be logically valid. Exact certificate/full-placement identity
    # is independently checked by Tape and the positive point oracle instead.
    worker.verify(plan)
    library_bindings(libraries, contract['library_bindings'])
    for artifact in tuple(bundle.values()) + tuple(static_resource_closure.values()) + (
            producer_result, producer_resource) + tuple(producer_resource_closure.values()):
        artifact.pin()
    return {
        'schema': 'one-context-proof-control-independent-semantic-result-v1',
        'status': 'complete_tape_and_conditional_positive_certificate_checked_pending_own_resources',
        'selector': selector, 'mode': mode, 'observation_id': selector + '/' + mode,
        'producer_result': producer_result.pin(), 'producer_resource': producer_resource.pin(),
        'context_pins': context_pins, 'static_resource_closure': static_closure_pins,
        'source_contract': source_contract.pin(), 'activation': activation.pin(),
        'checked_tape': checked, 'trace_accepted': checked['trace_accepted'],
        'raw_symbolic_certificate_accepted': checked['certificate_accepted'],
        'fully_qualified_proof_accepted': False, 'own_resource_accepted': False,
        'original_Gamma': copy.deepcopy(accepted['problem']['gamma']), 'target': copy.deepcopy(target),
        'model_epoch': accepted['model_epoch'], 'group_authority_epoch': pool.epoch,
        'repeated_complete_static_census': counts, 'independent_rebuild_timings': timings,
        'worker_seconds_before_result_serialization': time.perf_counter() - began,
        'native_queries': 0, 'native_accepted': False, 'new_training': False,
        'all_five_qualification': False, 'searches_run_by_auditor': 0,
        'scope': 'Original retained-hypothesis ground sequent and exact full raw tape; '
                 'own complete process resource gate and ROOT final decision remain pending.',
    }
