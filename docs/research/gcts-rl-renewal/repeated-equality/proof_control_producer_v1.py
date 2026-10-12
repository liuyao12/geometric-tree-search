"""SOURCE ONLY: one cold deterministic lane of a future two-lane comparison.

No scientific import, process owner, CLI, activation record or actual plan is
provided. ROOT must review/freeze all pending interfaces before calling this.
One invocation constructs one full graph/pool and performs automatic primitive
search. It contains no target proof word, theorem tactic, RNG or learner.
"""
import copy
import time
from proof_control_bindings_v1 import (
    VERSION, MODES, LIMITS, need, same, context_receipt_gate,
    phase_authority, library_bindings,
)


PRODUCER_LIBRARY_ROLES = ('compiler', 'selection', 'lifecycle', 'proposals',
                          'registration', 'search_loop', 'prior_search')


def produce_one_lane(bundle, resource_closure, libraries, *, selector, mode,
                     activation, source_contract):
    """Future ROOT-owned entry; one lane per fresh owned process.

    Returned dictionaries are pending independent tape/proof and full owned
    resource acceptance. The outer owner must retain/serialize all fields,
    close/reap/qualify the entire process, and never silently invoke this twice.
    """
    began = time.perf_counter()
    need(mode in MODES, 'literal base or full fixed-pool lane only')
    context_pins = {role: artifact.pin() for role, artifact in bundle.items()}
    closure_pins = {path: artifact.pin() for path, artifact in sorted(resource_closure.items())}
    contract = phase_authority(activation, source_contract, 'producer', selector, mode,
                               {'context': context_pins, 'resource_closure': closure_pins})
    need(set(libraries) == set(PRODUCER_LIBRARY_ROLES), 'complete exact producer libraries')
    library_bindings(libraries, contract['library_bindings'])
    data = context_receipt_gate(bundle, selector, resource_closure)
    compiled, evidence, static = (data['compiled_context'], data['preparation_evidence'],
                                  data['fresh_static_result'])
    selected = libraries['selection'].select_context(data['frozen_reference'],
        data['frozen_split'], data['frozen_RL_protocol'], data['frozen_selection_binding'], selector)
    same(compiled['context'], {'theory': selected['theory'],
         'ordered_local_premises': selected['ordered_hypotheses']}, 'complete frozen theory/Gamma')
    same(compiled['target'], selected['target'], 'exact frozen target; never a supplied proof goal route')
    same(compiled['curriculum_binding'], selected['binding'], 'exact frozen context selection')
    same(evidence['curriculum_binding'], selected['binding'], 'entire prepared context binding')
    same(static['curriculum_binding'], selected['binding'], 'independent selected context binding')
    same(compiled['height'], 24, 'all original required rows')
    need(len(compiled['recipes']) == 229 and len(compiled['formula_codes']) == 217,
         'complete original primitive and formula domains')
    life = libraries['lifecycle']; core = life.core
    setup = time.perf_counter()
    graph = libraries['compiler'].construct_graph(compiled, core)
    same(graph.model_epoch, static['model_epoch'], 'same accepted fresh model')
    same(graph.semantic_state(), evidence['initial_graph_semantic_state'],
         'entire cold graph state, all three occurrence seeds')
    projection = copy.deepcopy(data['family_projection'])
    projection.pop('example', None)  # Existing authored example is never search guidance.
    original = libraries['compiler'].construct_family_authority(graph, projection, life,
                evidence['original_body_authority_source_bindings'])
    need(len(original.bodies) == 171, 'all authored source bodies retained')
    group_authority, groups, registration = libraries['registration'].register_pool(
        graph, original, projection, libraries['proposals'], life, evidence, static)
    need(len(groups) <= 64, 'full capacity condition, never a trimmed winner subset')
    same(groups, evidence['groups'], 'entire measured audited pool unchanged')
    same(graph.semantic_state(), evidence['initial_graph_semantic_state'],
         'registration cannot alter point legality, marks, hypotheses or generations')
    cold_setup_seconds = time.perf_counter() - setup
    active = groups if mode == 'fixed-whole-family-pool' else []
    active_authority = group_authority if active else original
    # A complete empty pool is legitimate: both lanes then use base order and
    # no cluster-effect claim follows. No result-dependent pool modification.
    if mode == 'fixed-whole-family-pool':
        active_authority = group_authority
    result = libraries['search_loop'].fixed_pool_search(graph, active_authority, active,
        life, libraries['prior_search'], mode=mode, attempts=LIMITS['attempts'],
        seconds=LIMITS['seconds'], event_ceiling=LIMITS['event_ceiling'])
    certificate = result['point_certificate']
    result['decoded_certificate'] = (libraries['prior_search'].decode(graph, certificate, core)
                                     if certificate is not None else None)
    result.update(
        context_control_schema=VERSION, observation_id=selector + '/' + mode,
        selector=selector, partition=selected['split'],
        curriculum_binding=copy.deepcopy(selected['binding']),
        hypothesis_codes=copy.deepcopy(compiled['hypothesis_codes']), target_code=compiled['target_code'],
        body_authority_epoch=active_authority.epoch,
        original_body_authority_epoch=original.epoch, group_authority_epoch=group_authority.epoch,
        available_source_family_count=171, complete_saved_pool_count=len(groups),
        fresh_static_gate=copy.deepcopy(context_pins),
        resource_closure_pins=copy.deepcopy(closure_pins),
        source_contract=source_contract.pin(), activation=activation.pin(),
        preparation_costs={'fresh_graph_all_body_and_whole_pool_registration_seconds': cold_setup_seconds,
                           **registration},
        worker_seconds_before_return_and_outer_serialization=time.perf_counter() - began,
        target_proof_accepted=False, trace_accepted=False, full_resource_accepted=False,
        all_five_qualification=False, RNG_draws=0, native_authority_activated=False,
        scope='Automatic primitive target search using complete prior authored inventory; '
              'pending independent complete tape/point/symbolic and owned resource acceptance.')
    # Include a post-search source byte reconciliation in the owned cost.
    library_bindings(libraries, contract['library_bindings'])
    for artifact in tuple(bundle.values()) + tuple(resource_closure.values()):
        artifact.pin()
    return result
