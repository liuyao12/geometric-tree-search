"""SOURCE ONLY compact streamed DFS/chronological RNG adapter, no dispatch.

Caller must supply independently qualified complete context/body/pool, the pinned
compact dynamic graph/lifecycle, unchanged core and 31 features/math, and this
package's streamed overlayV3. Advice never creates a hypothesis or changes a
domain. No producer proof is accepted; ROOT must separately admit a fresh owned
wrapper and complete independent compact trace checker before invocation.
"""
import copy
import hashlib
import math
import random
import time

VERSION = 'compact24-whole-family-scientific-DFS-RNG-trajectory-v3'


class TraceCeiling(Exception):
    pass


INVENTORY_SCHEMA = 'ROOT-whole-compact-search-inventory-binding-v1'


def complete_inventory_binding(graph, authority, control, qualified_dimensions, core):
    """Reconstruct the exact whole inventory, never select or reduce it.

    ROOT supplies a separately authenticated, predeclared expected binding
    shared by every lane in this context. The helper result alone is not an
    admission or proof that the supplied pool is the full qualified grammar.
    """
    source = authority.original if hasattr(authority, 'original') else authority
    return dict(schema=INVENTORY_SCHEMA, model_epoch=graph.model_epoch,
        catalog_identity_sha256=graph.catalog_identity_sha,
        runtime_authority_sha256=graph.runtime_authority_sha,
        original_body_authority_epoch=source.epoch, whole_group_authority_epoch=authority.epoch,
        original_source_body_inventory_sha256=core.digest([[name, core.digest(core.json.loads(text))]
                                                           for name, text in source.bodies]),
        complete_descriptor_registry_sha256=core.digest([[d.identifier, d.priority, d.text]
                                                         for d in control.descriptors]),
        registered_whole_descriptor_count=len(control.descriptors),
        qualified_dimensions=copy.deepcopy(qualified_dimensions))


def search_episode(graph, authority, groups, life, overlay_module, features, policy_math, *,
                   episode_id, mode, seed, weights, attempts, seconds, event_ceiling,
                   prerequisite_pins, cold_preparation_costs, qualified_dimensions,
                   expected_inventory_binding, consumer_binding):
    """One predeclared episode; caller owns the full resource envelope.

    RNG and unique non-NULL commits are chronological and never rewound. Active
    origin/commit rolls back beside the graph/Controller/overlay. A commit's
    first chronological terminal transition determines its one retirement
    charge. Retired-first stays charged after revival; consumed-first cannot
    later earn a charge. This is frozen wording interpretation, not a new reward.
    """
    setup_started = time.perf_counter(); core = life.core
    if (type(episode_id) is not str or not episode_id
            or mode not in ('base','fixed','untrained','trained','donor')):
        raise ValueError('one exact predeclared episode and lane required')
    for value in (attempts,event_ceiling): core.integer(value)
    if (attempts < 1 or event_ceiling < 1 or type(seconds) not in (int,float)
            or not math.isfinite(seconds) or seconds <= 0):
        raise ValueError('literal positive complete episode bounds')
    required_dimensions = {'logical_rows','formula_count','primitive_license_count','non_assumption_witness_count','source_body_count'}
    if set(qualified_dimensions) != required_dimensions:
        raise ValueError('independently qualified complete declared dimensions required')
    for field, value in qualified_dimensions.items():
        if type(value) is not int or value < (0 if field == 'source_body_count' else 1):
            raise ValueError('literal complete declared dimensions; source inventory may be empty for primitive discovery only')
    if qualified_dimensions['source_body_count'] == 0 and (mode != 'base' or groups):
        raise ValueError('empty inventory permits primitive-only discovery, never learned-policy evidence')
    source_authority = authority.original if hasattr(authority, 'original') else authority
    if (qualified_dimensions['logical_rows'] != 24 or graph.height != 24 or graph.fixture
            or len(graph.recipes) != qualified_dimensions['primitive_license_count']
            or len(graph.formulas) != qualified_dimensions['formula_count']
            or len(source_authority.bodies) != qualified_dimensions['source_body_count']
            or qualified_dimensions['non_assumption_witness_count'] != graph.catalog.header['dimensions']['non_assumption_witness_count']):
        raise ValueError('complete actual24-row model/body/license census differs from independently qualified declaration')
    if len(groups) > 64:
        raise ValueError('UNRESOLVED complete pool exceeds frozen64 capacity; do not trim or tune')
    if graph.semantic_state().get('schema') != 'compact-complete-dynamic-point-state-v2':
        raise ValueError('new separately qualified compact dynamic state required; no eager-wire relabeling')
    consumer_binding_text = overlay_module.check_consumer_binding(
        consumer_binding, graph, core, features, policy_math, dfs_function=search_episode)
    stochastic = mode in ('donor','untrained','trained')
    if (stochastic and (type(seed) is not int or seed < 0)) or (not stochastic and seed is not None):
        raise ValueError('frozen stochastic seed or exact no-RNG control required')
    if not prerequisite_pins or not cold_preparation_costs:
        raise ValueError('explicit complete context/pool qualification and charged cost provenance')
    control = life.Controller(graph, authority, groups)
    if len(control.descriptors) != len(groups) or json_load(core,control.root_rejected_text):
        raise ValueError('all exact whole records registered; no partial pool or salvage')
    actual_inventory_binding = complete_inventory_binding(graph, authority, control, qualified_dimensions, core)
    if (type(expected_inventory_binding) is not dict
            or expected_inventory_binding.get('schema') != INVENTORY_SCHEMA
            or core.canonical(expected_inventory_binding) != core.canonical(actual_inventory_binding)):
        raise ValueError('every lane must reconstruct/register the same entire independently qualified inventory')
    frozen_weights = policy_math.vector(weights,'frozen episode weights')
    if set(frozen_weights) != set(features.FEATURE_NAMES) or len(frozen_weights) != 31:
        raise ValueError('exact31 weights including zeros required')
    if mode in ('base','fixed','untrained') and any(frozen_weights.values()):
        raise ValueError('base/fixed/untrained controls use frozen zero weights')
    overlay = overlay_module.LearnedFamilyOverlay(control,core,features,policy_math,frozen_weights,
        epsilon=0.1,temperature=1.0,maximum_descriptors=64,consumer_binding=consumer_binding)
    primitive = core.Executor(graph)
    rng = random.Random(seed) if stochastic else None
    setup_seconds = time.perf_counter()-setup_started
    registration_metrics = copy.deepcopy(control.metrics)
    graph_metrics_at_entry = copy.deepcopy(graph.metrics)
    validation_at_entry = control.metrics['members_checked']+control.metrics['mark_checks']
    begin = time.perf_counter(); deadline = begin+seconds
    events=[]; graph_states={}; policy_choices=[]; draws=[]; commits=[]
    terminal_transitions=[]; first_terminal={}; retired_commit_ids=set(); consumed_commit_ids=set()
    active_commit_id=None; commit_trail=[]; node_count=0; maximum_facts=0
    fact_observations=[]; budget_observations=[]; proposal_effect_count=0
    metrics=dict(order_calls=0,logical_domain_keys_represented=0,order_seconds=0.0,
        order_descriptor_seconds=0.0,selected_key_observations=0,trace_seconds=0.0,primitive_step_seconds=0.0,
        full_fact_closure_seconds=0.0,rollback_seconds=0.0,exclusion_seconds=0.0,
        policy_prepare_choose_seconds=0.0,commit_bookkeeping_seconds=0.0)

    def state():
        complete=overlay.semantic_state(); full_graph=complete['controller'].pop('graph')
        graph_sha=core.digest(full_graph)
        if graph_sha not in graph_states: graph_states[graph_sha]=full_graph
        complete['controller']['graph_state_sha256']=graph_sha
        value=dict(overlay=complete,active_commit_id=active_commit_id,
            trail_depths=dict(graph=len(graph.trail),controller=len(control.trail),
                              overlay=len(overlay.trail),commit=len(commit_trail)),
            chronological=dict(draws=len(draws),commits=len(commits),
                terminal_transitions=len(terminal_transitions),
                retired_commit_ids=sorted(retired_commit_ids),consumed_commit_ids=sorted(consumed_commit_ids)),
            maximum_fact_potential=maximum_facts)
        return value

    def event(kind,node,**fields):
        started=time.perf_counter()
        if len(events)>=event_ceiling: raise TraceCeiling('full scientific event budget; prefix never accepted')
        events.append(dict(index=len(events),kind=kind,node=node,**fields,state=state()))
        metrics['trace_seconds']+=time.perf_counter()-started

    def facts(node,reason):
        nonlocal maximum_facts
        started=time.perf_counter()
        available=features.available_rows(overlay._feature_graph(),overlay.recipes)
        potential=len(available['distinct_nonroot_codes'])
        maximum_facts=max(maximum_facts,potential)
        observation=dict(index=len(fact_observations),reason=reason,
            complete_rows=[[r,c] for r,c in sorted(available['complete'].items())],
            distinct_nonroot_codes=sorted(available['distinct_nonroot_codes']),
            root_codes=sorted(available['root_codes']),per_state_potential=potential,
            maximum_so_far=maximum_facts)
        fact_observations.append(observation)
        metrics['full_fact_closure_seconds']+=time.perf_counter()-started
        event('dependency_complete_fact_observation',node,observation=observation)

    def checked_budget(node,stage):
        # Raw provenance for the exact checked cutoff, not a mathematical
        # exhaustion reason. Event serialization may overshoot a finite check.
        elapsed=time.perf_counter()-begin
        used=graph.metrics['attempts']-start_attempts
        observation=dict(index=len(budget_observations),stage=stage,
            checked_search_elapsed_seconds=elapsed,primitive_attempts=used,
            attempt_limit=attempts,checked_search_limit_seconds=seconds,
            attempts_exhausted=used>=attempts,time_exhausted=elapsed>=seconds)
        if budget_observations and elapsed<budget_observations[-1]['checked_search_elapsed_seconds']:
            raise ValueError('monotone checked-search clock required')
        budget_observations.append(observation)
        event('checked_search_budget_observation',node,observation=observation)
        return observation

    def set_active_commit(identifier):
        nonlocal active_commit_id
        commit_trail.append(active_commit_id);active_commit_id=identifier

    def checkpoint():
        value=dict(overlay=overlay.checkpoint(),commit_trail_depth=len(commit_trail),
                   active_commit_id=active_commit_id)
        value['paired_semantic_sha256']=core.digest(dict(
            overlay=overlay.semantic_state(),active_commit_id=active_commit_id))
        return value

    def rollback(cp,node,reason,*,record=True):
        nonlocal active_commit_id
        started=time.perf_counter(); overlay.rollback(cp['overlay'])
        depth=core.integer(cp['commit_trail_depth'])
        if not 0<=depth<=len(commit_trail): raise ValueError('exact paired commit checkpoint depth')
        while len(commit_trail)>depth: active_commit_id=commit_trail.pop()
        if (active_commit_id!=cp['active_commit_id'] or core.digest(dict(
                overlay=overlay.semantic_state(),active_commit_id=active_commit_id))!=cp['paired_semantic_sha256']):
            raise ValueError('graph/hints/overlay/active origin did not roll back exactly')
        metrics['rollback_seconds']+=time.perf_counter()-started
        if record:
            event('paired_rollback',node,checkpoint=cp,reason=reason)
            facts(node,'after-paired-rollback')

    def resync(node,reason,decision=None):
        started=time.perf_counter(); prior_descriptor=overlay.active_id; origin=active_commit_id
        control.resync(decision)
        event('whole_controller_resync',node,reason=reason)
        if prior_descriptor is not None:
            if origin is None: raise ValueError('active proposal requires chronological non-NULL origin')
            hint=next(s for d,s in zip(control.descriptors,control.states) if d.identifier==prior_descriptor)
            if hint.status in ('retired','consumed'):
                first=origin not in first_terminal
                if first: first_terminal[origin]=hint.status
                if hint.status=='retired' and first: retired_commit_ids.add(origin)
                if hint.status=='consumed': consumed_commit_ids.add(origin)
                transition=dict(index=len(terminal_transitions),commit_id=origin,
                    descriptor_id=prior_descriptor,status=hint.status,reason=hint.reason,
                    first_terminal_transition=first,first_terminal_status=first_terminal[origin],
                    retirement_charge_added=hint.status=='retired' and first)
                terminal_transitions.append(transition)
                event('chronological_commit_terminal_transition',node,transition=transition)
        overlay.after_resync()
        if overlay.active_id is None and active_commit_id is not None: set_active_commit(None)
        if (overlay.active_id is None)!=(active_commit_id is None):
            raise ValueError('paired active descriptor/commit relation')
        event('overlay_after_whole_resync',node,reason=reason)
        metrics['commit_bookkeeping_seconds']+=time.perf_counter()-started

    def domain_descriptor(order):
        started=time.perf_counter(); value=order.descriptor()
        metrics['order_descriptor_seconds']+=time.perf_counter()-started
        return value

    def order(decision,node):
        nonlocal proposal_effect_count
        started=time.perf_counter()
        if decision!=graph.decision() or decision.kind not in ('branch','forced'):
            raise ValueError('fresh mandatory global scheduler decision')
        base=graph.ordered_domain(decision)
        if len(base)!=decision.count:
            raise ValueError('full point domain is the only degree authority')
        draw_record=None; selection=None
        if stochastic:
            prepare_start=time.perf_counter(); prepared=overlay.prepare(decision)
            event('policy_prepare',node,decision=[decision.kind,decision.row,decision.count,decision.generation],
                prepared=dict(decision=prepared['decision'],menu=prepared['menu'],
                    needs_one_draw=prepared['needs_one_draw'],pool_epoch=prepared['pool_epoch'],
                    weight_sha256=prepared['weight_sha256'],prepared_state_sha256=prepared['prepared_state_sha256'],
                    complete_base_count=prepared['base_domain_descriptor']['complete_count'],
                    base_domain_descriptor=copy.deepcopy(prepared['base_domain_descriptor'])))
            draw=None
            if prepared['needs_one_draw']:
                before=core.digest(rng.getstate()); draw=rng.random(); after=core.digest(rng.getstate())
                draw_record=dict(index=len(draws),id=episode_id+'/draw/'+str(len(draws)),
                    draw=draw,rng_state_before_sha256=before,rng_state_after_sha256=after)
                draws.append(draw_record)
            ordered,selection=overlay.choose_prepared(prepared,draw)
            if selection['policy'] is not None:
                if draw_record is None: raise ValueError('exact one chronological draw per fresh selection')
                policy=copy.deepcopy(selection['policy']);policy.update(draw_record=draw_record,
                    selection_index=len(policy_choices),decision=prepared['decision'],commit_id=None)
                if selection['policy']['choice']['chosen_id']!='NULL':
                    identifier=episode_id+'/commit/'+str(len(commits))
                    commit=dict(id=identifier,index=len(commits),draw_id=draw_record['id'],
                        draw_index=draw_record['index'],descriptor_id=selection['active_descriptor_id'],
                        selection_index=len(policy_choices),decision=prepared['decision'],node=node)
                    commits.append(commit);set_active_commit(identifier);policy['commit_id']=identifier
                else: set_active_commit(None)
                policy_choices.append(policy)
                proposal_effect_count+=int(policy['commit_id'] is not None and selection['changed_first'])
            elif draw_record is not None: raise ValueError('forced/waiting continuation consumes no draw')
            event('policy_choose',node,selection=selection,draw_record=draw_record,
                active_commit_id=active_commit_id,policy_choice_index=len(policy_choices)-1 if selection['policy'] else None)
            metrics['policy_prepare_choose_seconds']+=time.perf_counter()-prepare_start
        else:
            if mode=='fixed':
                # Exactly the unchanged fixed ordering method's single resync.
                # No redundant preliminary scan is added to the fixed lane.
                ordered=control.ordered(decision)
                event('fixed_complete_order_controller_resync',node)
                overlay.after_resync();event('overlay_after_whole_resync',node,reason='fixed-control-order')
            else:
                resync(node,'base-control-order',decision);ordered=base
        base_descriptor=domain_descriptor(base); ordered_descriptor=domain_descriptor(ordered)
        if (len(ordered)!=len(base)
                or base_descriptor['state_sha256']!=ordered_descriptor['state_sha256']
                or base_descriptor['catalog_identity_sha256']!=ordered_descriptor['catalog_identity_sha256']
                or base_descriptor['runtime_authority_sha256']!=ordered_descriptor['runtime_authority_sha256']
                or base_descriptor['decision']!=ordered_descriptor['decision']):
            raise ValueError('same full current primitive relation and exact fallback permutation required')
        if decision.kind=='forced' and ordered_descriptor['preferred_keys']:
            raise ValueError('global forced singleton cannot be policy modified')
        selected_key=ordered.first()
        metrics['order_calls']+=1;metrics['logical_domain_keys_represented']+=len(base)
        metrics['selected_key_observations']+=1
        metrics['order_seconds']+=time.perf_counter()-started
        event('complete_chosen_domain_order',node,
            decision=[decision.kind,decision.row,decision.count,decision.generation],
            complete_count=len(base),base_domain_descriptor=base_descriptor,
            ordered_domain_descriptor=ordered_descriptor,
            literal_full_stream_hashes_measured=False,
            selected_key=selected_key.data(),mode=mode,
            preferred_keys=selection['preferred_keys'] if selection else
                [k.data() for s in control.states if s.status=='ready' for k in s.eligible] if mode=='fixed' else [])
        return selected_key

    def step(key,node):
        start=time.perf_counter(); primitive.step(key)
        metrics['primitive_step_seconds']+=time.perf_counter()-start
        event('primitive_step',node,key=key.data())
        # Observe even a subsequently failed primitive and every forced step.
        facts(node,'after-primitive-step-before-whole-resync')
        resync(node,'after-primitive-step')

    initial=checkpoint();initial_semantic=core.digest(dict(overlay=overlay.semantic_state(),active_commit_id=active_commit_id))
    start_attempts=graph.metrics['attempts']
    def walk(parent_node=None):
        nonlocal node_count
        node=node_count;node_count+=1;cp=checkpoint()
        event('node_enter',node,parent_node=parent_node,checkpoint=cp)
        while True:
            decision=graph.decision()
            event('global_decision',node,decision=[decision.kind,decision.row,decision.count,decision.generation])
            if decision.kind=='dead':
                event('proved_global_dead',node);rollback(cp,node,'dead-subtree')
                event('node_return',node,status='exhausted_finite_marked_subtree')
                return 'exhausted_finite_marked_subtree',node
            if decision.kind=='complete':
                resync(node,'complete',decision)
                event('node_return',node,status='finite_exact_point_tiling')
                return 'finite_exact_point_tiling',node
            observed=checked_budget(node,'before-order')
            if observed['attempts_exhausted'] or observed['time_exhausted']:
                event('budget_unknown_no_exclusion',node,budget_observation_index=observed['index']);rollback(cp,node,'budget-unknown')
                event('node_return',node,status='unknown_search_budget')
                return 'unknown_search_budget',node
            key=order(decision,node)
            observed=checked_budget(node,'after-order')
            if observed['time_exhausted']:
                event('budget_unknown_after_order_no_exclusion',node,budget_observation_index=observed['index']);rollback(cp,node,'budget-after-order')
                event('node_return',node,status='unknown_search_budget')
                return 'unknown_search_budget',node
            if decision.kind=='forced': step(key,node);continue
            parent=checkpoint();event('branch_begin',node,key=key.data(),checkpoint=parent)
            step(key,node);status,child=walk(node)
            if status=='finite_exact_point_tiling':
                event('node_return',node,status=status,child_node=child);return status,node
            rollback(parent,node,'restored-parent')
            if status.startswith('unknown_'):
                rollback(cp,node,'unknown-child-no-exclusion')
                event('node_return',node,status=status,child_node=child);return status,node
            if status!='exhausted_finite_marked_subtree':
                raise ValueError('only exhausted exact child permits parent-local exclusion')
            event('before_exhausted_child_exclusion',node,key=key.data(),child_node=child,child_status=status)
            start=time.perf_counter();graph.exclude_failed_child(key);graph.metrics['backtracks']+=1
            metrics['exclusion_seconds']+=time.perf_counter()-start
            event('parent_local_exhausted_child_exclusion',node,key=key.data(),child_node=child,child_status=status)
            resync(node,'after-proved-child-exclusion')

    trace_complete=True
    try:
        event('solve_begin',None,version=VERSION,episode_id=episode_id,mode=mode,seed=seed,
            limits=dict(attempts=attempts,seconds=seconds,events=event_ceiling))
        facts(None,'initial-state')
        status,root_node=walk()
        if status!='finite_exact_point_tiling': rollback(initial,None,'final-root-restore')
        event('solve_return',None,status=status,root_node=root_node)
    except TraceCeiling as exc:
        status='unknown_trace_budget';trace_complete=False;root_node=0
        rollback(initial,None,'unaccepted-trace-prefix-cleanup',record=False)
        termination=dict(kind='trace-ceiling',message=str(exc),events_retained=len(events))
    except Exception as exc:
        # Retain an unaccepted partial tape, chronological draws/commits and
        # the exact failure. No failed/partial trajectory may train. Cleanup
        # attempts rollback once and preserves its failure rather than retrying.
        status='unknown_infrastructure_failure';trace_complete=False;root_node=0
        cleanup_error=None
        try: rollback(initial,None,'unaccepted-failure-prefix-cleanup',record=False)
        except Exception as cleanup: cleanup_error=type(cleanup).__name__+': '+str(cleanup)
        termination=dict(kind='infrastructure-failure',type=type(exc).__name__,message=str(exc),
            events_retained=len(events),cleanup_error=cleanup_error)
    else: termination=dict(kind='complete-return',root_node=root_node)
    root_restored=core.digest(dict(overlay=overlay.semantic_state(),active_commit_id=active_commit_id))==initial_semantic
    if status!='finite_exact_point_tiling' and not root_restored:
        status='unknown_infrastructure_failure';trace_complete=False
        termination['root_restore_failure']='whole graph/hint/overlay/origin does not equal exact root'
    terminal=state()
    point_certificate=None
    if status=='finite_exact_point_tiling':
        try: point_certificate=graph.point_certificate()
        except Exception as exc:
            status='unknown_infrastructure_failure';trace_complete=False
            termination['point_certificate_failure']=type(exc).__name__+': '+str(exc)
    checks=control.metrics['members_checked']+control.metrics['mark_checks']-validation_at_entry
    counters=dict(maximum_distinct_dependency_complete_nonroot_facts=maximum_facts,logical_rows=24,
        primitive_attempts=graph.metrics['attempts']-start_attempts,attempt_limit=attempts,
        construction_validation_checks=checks,check_ceiling=10000,
        retired_commits=len(retired_commit_ids),commits=len(commits))
    provisional_reward=policy_math.reward(producer_primitive_certificate_passed=False,**counters)
    return dict(schema=VERSION,status=status,episode_id=episode_id,mode=mode,seed=seed,
        trace_complete=trace_complete,root_restored=root_restored,events=events,graph_states=graph_states,terminal_state=terminal,
        termination=termination,node_count=node_count,attempts=counters['primitive_attempts'],
        policy_choices=policy_choices,rng_draws=draws,
        RNG_schema='stdlib.random.Random/MT19937 pinned Python3.9; exactly one random() per fresh proposal selection',
        RNG_initial_seed=seed,RNG_terminal_state_sha256=core.digest(rng.getstate()) if rng else None,
        commits=commits,commit_terminal_transitions=terminal_transitions,
        commit_first_terminal=first_terminal,retired_commit_ids=sorted(retired_commit_ids),
        consumed_commit_ids=sorted(consumed_commit_ids),fact_observations=fact_observations,
        checked_budget_observations=budget_observations,
        reward_counters=counters,provisional_no_terminal_bonus_reward=provisional_reward,
        proposal_effect_count=proposal_effect_count,point_certificate=point_certificate,
        primitive_certificate_accepted=False,independent_full_replay_accepted=False,
        immutable_weights=frozen_weights,weights_sha256=core.digest(frozen_weights),
        fixed_pool_descriptor_ids=[d.identifier for d in control.descriptors],
        registered_whole_descriptor_count=len(groups),all_source_body_count=qualified_dimensions['source_body_count'],
        qualified_dimensions=copy.deepcopy(qualified_dimensions),
        model_epoch=graph.model_epoch,group_authority_epoch=authority.epoch,
        prerequisite_pins=copy.deepcopy(prerequisite_pins),
        complete_inventory_binding=copy.deepcopy(actual_inventory_binding),
        complete_inventory_binding_sha256=core.digest(actual_inventory_binding),
        consumer_source_binding=json_load(core,consumer_binding_text),
        consumer_source_binding_sha256=core.digest(json_load(core,consumer_binding_text)),
        graph_state_schema='compact-complete-dynamic-point-state-v2',
        order_relation_schema='complete-compact-ordered-domain-descriptor-v2',
        literal_full_stream_hashes_measured=False,
        graph_metrics=copy.deepcopy(graph.metrics),graph_metrics_at_search_entry=graph_metrics_at_entry,
        lifecycle_metrics=copy.deepcopy(control.metrics),registration_lifecycle_metrics=registration_metrics,
        ordering_and_policy_metrics=metrics,cold_preparation_costs=copy.deepcopy(cold_preparation_costs),
        controller_overlay_RNG_setup_seconds=setup_seconds,
        search_seconds_including_certificate_and_return_preparation=time.perf_counter()-begin,
        checked_deadline_overshoot_seconds=max(0.0,time.perf_counter()-deadline),
        cost_scope='Full pool construction/qualification provenance, cold registration, complete factored domain/order descriptors, actual selected-key extraction, all features/choice/gradient/trace/facts/primitive steps/rollback/exclusions and full certificate preparation. Represented candidate counts are not literal key observations or measured full-stream hashes. Enclosing owner complete serialization/exit/reap required separately.',
        native_queries=0,atomic_macro_moves=0,training_updates=0,
        claim_scope='Unqualified compact finite search candidate/UNKNOWN until a NEW independent complete compact trace/resource/symbolic audit; old eager replay cannot accept this wire. No universal palette, RL superiority or source-only speed claim')


def json_load(core,text):
    # Uses the same JSON library already bound by the unchanged core, no parser
    # mutation and no acceptance authority inferred from a decoded payload.
    return core.json.loads(text)
