"""SOURCE ONLY complete raw-operation replay of the frozen 24-scenario gate.

Only independent modules are imported by a future ROOT owner. Producer assertion
fields and expected traces have no acceptance authority. Every raw before/after
state, complete domain, Controller hint, overlay transaction and policy payload
is compared. Timing fields are validated as observations, never regenerated.
No real theorem, training or donor/held-out DFS acceptance follows from this gate.
"""
import copy
import hashlib
import math

import independent_fixture_points_v1 as point
import independent_fixture_whole_v1 as whole
import independent_features_v1 as features
import independent_policy_v1 as policy


def same(actual, expected, label):
    point.need(point.canonical(actual) == point.canonical(expected), label)


def hash_stream(keys):
    return hashlib.sha256(('\n'.join(point.canonical(point.key_data(k)) for k in keys) + '\n').encode()).hexdigest()


def scope(corpus, identifier):
    model = ('forced' if identifier in ('global-forced-no-draw', 'forced-extra-draw') else
             'dead_and_forced' if identifier == 'global-distant-dead' else
             'early_wide' if identifier == 'earlier-generation' else
             'pending_source' if identifier in ('forced-active-no-draw', 'pending-source-not-fact') else 'ordinary')
    proposals = ([] if identifier == 'pending-source-not-fact' else
        ['pending-then-future'] if identifier == 'forced-active-no-draw' else
        ['repeated-source'] if identifier == 'repeated-ports' else
        ['remote-zero'] if identifier == 'assigned-zero-remote-retirement' else
        ['waiting-conditional'] if identifier in ('waiting-persistence', 'continuation-extra-draw') else ['ready-Q'])
    return model, proposals


def operations(identifier):
    """Frozen fixture action grammar, not a producer-generated expected trace.

    This closes the empty/prefix transcript loophole. The actual semantic
    states, legal keys, feature values and choices are independently computed.
    """
    step = ['primitive_apply', 'controller_resync', 'overlay_after_resync']
    select = ['prepare', 'choose']
    special = {
        'registration-whole-mutations': ['invalid_registration'] * 5,
        'global-distant-dead': ['prepare_rejected_global_dead'],
        'forced-active-no-draw': select + step + select + step,
        'pending-source-not-fact': step + ['available_facts'] + step + step + ['available_facts'],
        'assigned-zero-remote-retirement': select + step + ['controller_resync'],
        'waiting-persistence': select + step + select + step + select + step + select + step,
        'paired-rollback': ['checkpoint'] + select + ['checkpoint'] + step + ['paired_rollback'] * 2,
        'unknown-no-exclusion': ['zero_attempt_unknown'],
        'continuation-extra-draw': select + select,
        'immutable-weight-mutation': ['prepare', 'explicit_negative_weight_mutation', 'choose'],
    }
    return ['initial_snapshot'] + special.get(identifier, select)


class Replay:
    def __init__(self, record, corpus, exact_bindings):
        self.record, self.corpus = record, corpus
        model_name, names = scope(corpus, record['id'])
        model = corpus['models'][model_name]
        authority = copy.deepcopy(corpus['authority_body'])
        authority['epoch'] = point.digest(authority)
        definition = dict(height=corpus['height'], formulas=corpus['formulas'], recipe_data=corpus['recipes'],
            context=corpus['context'], authority=authority, fixed_marks=model['fixed_marks'], roots=model['roots'],
            seed_keys=model['seed_keys'], fixture=True, source_bindings={p['path']:
                dict(sha256=p['sha256'], bytes=p['bytes']) for p in exact_bindings})
        same(record['model'], definition, 'exact declared fixture model, no producer-selected simplification')
        same(record['source_bindings'], exact_bindings, 'complete source/runtime/corpus binding order')
        self.graph = point.LiteralFixtureGraph(definition)
        bodies, specs, original, epoch, records = whole.registry(self.graph, corpus, names, exact_bindings, point)
        for field, expected in (('bodies', bodies), ('descriptor_specs', specs), ('original_authority', original),
                                ('wrapper_epoch', epoch), ('descriptors', records)):
            same(record[field], expected, 'complete independently rebuilt ' + field)
        # The frozen source wrapper calls original.expected twice in initial
        # creation and twice in root registration. Reconstruct its work counter,
        # rather than using our differently organized identity-construction cost.
        self.graph.metrics['lazy_id_constructions'] = 4 * sum(len(d['members']) for d in records)
        self.control = whole.WholeController(self.graph, records, epoch, point)
        self.weights = dict.fromkeys(features.FEATURE_NAMES, 0.0)
        self.weight_sha = point.digest(self.weights)
        self.pool_epoch = point.digest(dict(authority_epoch=epoch, registry=[
            [d['descriptor_id'], d['fixed_priority'], point.canonical(d)] for d in self.control.records]))
        self.active, self.revision, self.trail, self.history = None, 0, [], []
        self.counters = dict(ordered_choices=0, primitive_steps=0, exact_graph_states=0,
                             literal_candidate_keys=0, rejected_preparations=0, rejected_registrations=0)
        self.preparations = []
        self.checkpoints = []

    def semantic(self):
        return dict(controller=self.control.full(), active_descriptor_id=self.active,
                    overlay_revision=self.revision, pool_epoch=self.pool_epoch, weight_sha256=self.weight_sha)

    def active_hint(self):
        if self.active is None:
            return None
        return next(h for d, h in zip(self.control.records, self.control.hints) if d['descriptor_id'] == self.active)

    def set_active(self, identifier):
        point.need(identifier is None or identifier in {d['descriptor_id'] for d in self.control.records},
                   'only whole registered source-authorized selection')
        self.trail.append((self.active, self.revision))
        self.active, self.revision = identifier, self.revision + 1

    def after_resync(self):
        hint = self.active_hint()
        if hint is not None and hint['status'] in ('retired', 'consumed'):
            self.set_active(None)

    def snapshot(self, raw, label):
        expected = dict(overlay=self.semantic(), complete_domains=[
            [point.key_data(k) for k in self.graph.candidates(r)] for r in range(self.graph.height)],
            decision=self.graph.decision(), trail_lengths=dict(graph=len(self.graph.trail),
                controller=len(self.control.trail), overlay=len(self.trail)),
            actual_overlay_weights=self.weights, overlay_history=self.history)
        point.need(set(raw) == set(expected).union({'cumulative_metrics'}), 'complete raw snapshot fields')
        for field in expected:
            if field == 'overlay_history':
                features.numeric(raw[field], expected[field], label + ':' + field)
            else:
                same(raw[field], expected[field], label + ':' + field)
        metrics = raw['cumulative_metrics']
        same(metrics['graph'], self.graph.metrics, label + ': every graph work counter')
        exact = dict(whole_scans=self.control.whole_scans, members_checked=self.control.members_checked,
            mark_checks=self.control.mark_checks, status_updates=self.control.status_updates,
            whole_retirements=self.control.retirements, resynchronizations=self.control.resyncs,
            ordering_calls=0, root_rejections=0)
        observed = metrics['controller']
        point.need(set(observed) == set(exact).union({'validation_seconds', 'ordering_seconds', 'rollback_seconds'}),
                   'complete controller cost fields')
        for name, value in exact.items():
            same(observed[name], value, label + ': controller counter ' + name)
        for name in ('validation_seconds', 'ordering_seconds', 'rollback_seconds'):
            point.need(type(observed[name]) in (float, int) and math.isfinite(observed[name]) and observed[name] >= 0,
                       'finite measured overlapping ' + name)
        self.counters['exact_graph_states'] += 1
        self.counters['literal_candidate_keys'] += sum(len(values) for values in expected['complete_domains'])

    def prepare(self):
        choice = self.graph.decision()
        point.need(choice[0] in ('branch', 'forced'), 'dead/complete bypass all policy advice')
        self.control.sync(); self.after_resync()
        base = [point.key_data(k) for k in self.graph.candidates(choice[1])]
        menu = (features.reconstruct_menu(self.graph.semantic(), self.graph.recipes, self.graph.formulas,
                self.graph.initial_selected, self.control.records, self.control.hints, choice)
                if choice[0] == 'branch' and self.active is None else None)
        return dict(decision=choice, base=base, menu=menu, needs_one_draw=menu is not None,
            prepared_state_sha256=point.digest(self.semantic()), pool_epoch=self.pool_epoch,
            weight_sha256=self.weight_sha)

    def choose(self, prepared, draw):
        point.need(point.digest(self.weights) == self.weight_sha, 'frozen episode weights before any advice')
        choice = self.graph.decision()
        raw_base = self.graph.candidates(choice[1])
        menu = features.audit_preparation(prepared, self.graph.semantic(), self.graph.recipes,
            self.graph.formulas, self.graph.initial_selected, self.control.records, self.control.hints, choice,
            self.active, point.digest(self.semantic()), self.pool_epoch, self.weight_sha,
            [point.key_data(k) for k in raw_base])
        policy_record = None
        if menu is not None:
            point.need(draw is not None, 'one saved new-selection draw')
            distribution = policy.distribution(menu, self.weights)
            selected, gradient = policy.choice_and_gradient(distribution, draw)
            self.set_active(None if selected['chosen_id'] == 'NULL' else selected['chosen_id'])
            policy_record = dict(distribution=distribution, choice=selected, score_gradient=gradient, menu=menu)
        else:
            point.need(draw is None, 'no forced/continuation draw')
        hint = self.active_hint()
        preferred = ([point.key(k) for k in hint['eligible']] if choice[0] == 'branch' and
                     hint is not None and hint['status'] == 'ready' else [])
        point.need(all(k in raw_base for k in preferred), 'whole eligible keys remain in complete domain')
        ordered = list(dict.fromkeys(preferred + raw_base))
        point.need(len(ordered) == len(raw_base) and set(ordered) == set(raw_base), 'every base fallback survives')
        record = dict(version='paired-learned-whole-family-overlay-v2', decision=choice, pool_epoch=self.pool_epoch,
            weight_sha256=self.weight_sha, policy=policy_record, active_descriptor_id=self.active,
            complete_base_count=len(raw_base), base_keys_sha256=hash_stream(raw_base),
            preferred_keys=[point.key_data(k) for k in preferred], ordered_keys_sha256=hash_stream(ordered),
            actual_first_key=point.key_data(ordered[0]), changed_first=ordered[0] != raw_base[0],
            continuation='new-selection' if policy_record is not None else 'existing-whole-hint-or-forced-base',
            pending_scope='Structural obligations only; pending/empty marks never become hypotheses')
        self.history.append(copy.deepcopy(record))
        self.counters['ordered_choices'] += 1
        return [[point.key_data(k) for k in ordered], record]

    def checkpoint(self):
        return dict(controller=self.control.checkpoint(), overlay_trail=len(self.trail),
            active_descriptor_id=self.active, overlay_revision=self.revision, pool_epoch=self.pool_epoch,
            semantic_sha256=point.digest(self.semantic()))

    def rollback(self, checkpoint):
        point.need(checkpoint['pool_epoch'] == self.pool_epoch, 'paired exact pool authority')
        self.control.rollback(checkpoint['controller'])
        depth = checkpoint['overlay_trail']
        point.need(type(depth) is int and 0 <= depth <= len(self.trail), 'overlay checkpoint depth')
        while len(self.trail) > depth:
            self.active, self.revision = self.trail.pop()
        same(self.active, checkpoint['active_descriptor_id'], 'active selection restored')
        same(self.revision, checkpoint['overlay_revision'], 'selection revision restored')
        same(point.digest(self.semantic()), checkpoint['semantic_sha256'], 'complete paired rollback')

    def unknown(self):
        state = self.control.full(); checkpoint = self.control.checkpoint()
        decision = self.graph.decision()
        point.need(decision[0] in ('branch', 'forced'), 'zero-budget context has a live nonterminal frontier')
        events = [dict(kind='solve_begin', max_attempts=0, seconds=1.0, state=copy.deepcopy(state)),
            dict(kind='global_decision', decision=decision, state=copy.deepcopy(state)),
            dict(kind='budget_unknown_no_exclusion', state=copy.deepcopy(state)),
            dict(kind='paired_rollback', checkpoint=checkpoint, state=copy.deepcopy(state)),
            dict(kind='paired_rollback', checkpoint=checkpoint, state=copy.deepcopy(state))]
        return dict(result=dict(status='unknown_budget', attempts=0, certificate=None,
            new_RL_training=False, native_queries=0, atomic_macro_moves=0), unchanged_executor_events=events)

    def invalid_registration(self, payload):
        bad = payload['descriptor']; index = bad['fixture_pool_index']
        expected = next(d for d in self.control.records if d['fixture_pool_index'] == index)
        mutated = copy.deepcopy(expected)
        field = payload['field']
        if field == 'members': mutated[field][0][0] = 1
        elif field == 'full_member_ids': mutated[field][0] = 'invalid-full-identity'
        elif field == 'aggregate_m': mutated[field].append([1, 5, 0])
        elif field == 'components': mutated[field][0]['conclusion_code'] = 0
        elif field == 'body_authority_epoch': mutated[field] = '0' * 64
        else: raise ValueError('unregistered whole-mutation control')
        same(bad, mutated, 'exact actual whole-record mutation, no substituted negative')
        point.need(point.canonical(bad) != point.canonical(expected), 'actual complete malformed record, no synthetic rejection label')
        self.graph.metrics['lazy_id_constructions'] += 2 * len(expected['members'])
        rejected = [dict(registration=0, reason='ValueError: fixture whole descriptor differs from exact original body/identity/metadata',
                         payload_sha256=point.digest(bad))]
        semantic = dict(graph=self.graph.semantic(), hint_states=[], hint_revision=1, descriptor_ids=[],
                        root_rejected=rejected, authority_epoch=self.control.epoch)
        self.counters['rejected_registrations'] += 1
        return dict(descriptor_ids=[], rejected=rejected, semantic_state=semantic)

    def prepared_transport(self, raw):
        expected = copy.deepcopy(self.preparations[-1])
        identifier = self.record['id']
        if identifier == 'stale-prepared-state': expected['prepared_state_sha256'] = '0' * 64
        elif identifier == 'stale-prepared-pool': expected['pool_epoch'] = '0' * 64
        elif identifier == 'stale-prepared-weight': expected['weight_sha256'] = '0' * 64
        elif identifier == 'mutated-prepared-vector': expected['menu']['feature_vectors'][0]['bias'] = 0.25
        elif identifier == 'mutated-prepared-action': expected['menu']['action_ids'][0] = 'altered-action'
        elif identifier == 'mutated-draw-requirement': expected['needs_one_draw'] = False
        elif identifier == 'mutated-draw-bool-type': expected['needs_one_draw'] = 1
        same(raw, expected, 'exact current or predeclared mutated prepared transport')

    def choice_payload(self, payload, index):
        point.need(set(payload) == {'prepared', 'supplied_draw', 'explicit_fixture_action'}, 'complete choice operation payload')
        self.prepared_transport(payload['prepared'])
        identifier = self.record['id']
        position = sum(e['op'] == 'choose' for e in self.record['events'][:index])
        names = {'null-full-fallback': 'NULL', 'nonnull-whole-preference': 'ready-Q',
                 'earlier-generation': 'NULL', 'repeated-ports': 'repeated-source',
                 'assigned-zero-remote-retirement': 'remote-zero', 'paired-rollback': 'ready-Q'}
        name = names.get(identifier)
        if identifier == 'forced-active-no-draw' and position == 0: name = 'pending-then-future'
        if identifier in ('waiting-persistence', 'continuation-extra-draw') and position == 0: name = 'waiting-conditional'
        same(payload['explicit_fixture_action'], name, 'exact declared fixture action, not favorable seed search')
        if name is not None:
            action = 'NULL' if name == 'NULL' else next(d['descriptor_id'] for d in self.control.records if d['body_name'] == name)
            ids = payload['prepared']['menu']['action_ids']
            draw = (ids.index(action) + 0.5) / len(ids)
        else:
            draws_half = (identifier.startswith('stale-prepared-') or identifier.startswith('mutated-') or
                          identifier in ('forced-extra-draw', 'immutable-weight-mutation') or
                          (identifier == 'continuation-extra-draw' and position == 1))
            draw = 0.5 if draws_half else None
        same(payload['supplied_draw'], draw, 'exact fixture draw or absence, not RNG acceptance')
        return (identifier.startswith('stale-prepared-') or identifier.startswith('mutated-') or
                identifier in ('forced-extra-draw', 'missing-new-selection-draw', 'immutable-weight-mutation') or
                (identifier == 'continuation-extra-draw' and position == 1))

    def event(self, raw, index):
        same(raw['index'], index, 'chronological complete event index')
        op, payload = raw['op'], raw['payload']
        if op == 'initial_snapshot':
            point.need(index == 0 and raw['before'] is None and raw['result'] is None and payload == {}, 'one complete initial state')
            self.snapshot(raw['after'], 'initial')
            return
        self.snapshot(raw['before'], 'before-' + str(index))
        point.need(op in set(operations(self.record['id'])), 'only source-declared operation kinds')
        rejected = op == 'prepare_rejected_global_dead'
        if op == 'choose': rejected = self.choice_payload(payload, index)
        same('error' in raw, rejected, 'exact predeclared rejection control, no substituted error')
        before = copy.deepcopy(self.semantic())
        try:
            if op == 'prepare':
                same(payload['decision'], self.graph.decision(), 'prepare current global decision')
                result = self.prepare(); self.preparations.append(copy.deepcopy(result))
            elif op == 'choose':
                result = self.choose(payload['prepared'], payload['supplied_draw'])
                if payload.get('explicit_fixture_action') is not None:
                    name = payload['explicit_fixture_action']
                    identifier = 'NULL' if name == 'NULL' else next(d['descriptor_id'] for d in self.control.records if d['body_name'] == name)
                    menu = payload['prepared']['menu']['action_ids']
                    same(payload['supplied_draw'], (menu.index(identifier) + 0.5) / len(menu), 'declared deterministic fixture draw')
            elif op == 'primitive_apply':
                choice = self.graph.decision(); k = point.key(payload['key'])
                point.need(choice[0] in ('branch', 'forced') and k[1] == choice[1] and k in self.graph.candidates(k[1]),
                           'mandatory complete scheduler before primitive step')
                if choice[0] == 'forced':
                    same(self.graph.candidates(k[1]), [k], 'global forced singleton')
                self.graph.apply(k)
                self.graph.metrics['attempts'] += 1
                self.graph.metrics['forced' if choice[0] == 'forced' else 'branches'] += 1
                self.counters['primitive_steps'] += 1
                result = None
            elif op == 'controller_resync':
                result = self.control.sync()
            elif op == 'overlay_after_resync':
                self.after_resync(); result = None
            elif op == 'checkpoint':
                result = self.checkpoint()
                self.checkpoints.append(copy.deepcopy(result))
            elif op == 'paired_rollback':
                same(payload['checkpoint'], self.checkpoints.pop(), 'paired rollback to exact saved inner then outer checkpoint')
                self.rollback(payload['checkpoint']); result = None
            elif op == 'available_facts':
                _, completed, potential = features.facts(self.graph.semantic(), self.graph.recipes, self.graph.initial_selected)
                result = dict(complete={str(row): code for row, code in completed.items()}, fact_potential=potential)
            elif op == 'invalid_registration':
                result = self.invalid_registration(payload)
            elif op == 'zero_attempt_unknown':
                same(payload, dict(max_attempts=0, seconds=1.0), 'exact zero-attempt UNKNOWN control')
                result = self.unknown()
            elif op == 'prepare_rejected_global_dead':
                result = self.prepare()
            elif op == 'explicit_negative_weight_mutation':
                same(payload, dict(feature='bias', value=0.25), 'exact declared negative mutation')
                self.weights[payload['feature']] = payload['value']; result = None
            else:
                raise ValueError('unrecognized raw operation: ' + str(op))
        except ValueError:
            point.need('error' in raw and raw['error']['type'] == 'ValueError' and raw['result'] is None,
                       'producer must reject the same actually malformed operation')
            same(self.semantic(), before, 'rejected operation has no transactional effect')
            self.counters['rejected_preparations'] += 1
        else:
            point.need('error' not in raw, 'producer error without independent malformed operation')
            features.numeric(raw['result'], result, 'complete raw operation result')
        self.snapshot(raw['after'], 'after-' + str(index))

    def run(self):
        events = self.record['events']
        point.need(events and events[0]['op'] == 'initial_snapshot', 'initial event retained')
        same([e['op'] for e in events], operations(self.record['id']), 'entire frozen scenario operation grammar')
        for index, event in enumerate(events):
            self.event(event, index)
        self.snapshot(self.record['terminal'], 'terminal')
        self.conclusions()
        return dict(id=self.record['id'], complete_events=len(events), **self.counters,
                    synthetic_point_and_overlay_accepted=True, primitive_certificate_accepted=False)

    def conclusions(self):
        identifier = self.record['id']
        if identifier == 'null-full-fallback':
            same(self.history[0]['policy']['choice']['chosen_id'], 'NULL', 'NULL actually selected')
            same(self.history[0]['preferred_keys'], [], 'NULL suppresses every fixed preference')
            point.need(not self.history[0]['changed_first'] and self.active is None, 'NULL complete base order')
        elif identifier == 'nonnull-whole-preference':
            point.need(self.history[0]['changed_first'] and self.history[0]['preferred_keys'], 'executed whole preference effect')
        elif identifier == 'global-distant-dead':
            same(self.graph.decision(), ['dead', 4, 0, 0], 'distant dead outranks all hints')
            same(len(self.graph.candidates(5)), 1, 'distant forced competitor exists')
        elif identifier == 'global-forced-no-draw':
            same(self.graph.decision(), ['forced', 5, 1, 0], 'global forced point selected')
            same(self.history[0]['policy'], None, 'forced bypasses mixture and draw')
        elif identifier == 'forced-active-no-draw':
            point.need(self.active is not None and len(self.history) == 2 and self.history[1]['policy'] is None,
                       'active whole hint survives a genuine forced interruption')
            same(self.history[1]['decision'][:3], ['forced', 2, 1], 'actual forced source, not merely branch continuation')
        elif identifier == 'earlier-generation':
            same(self.history[0]['decision'], ['branch', 1, 7, 0], 'earlier wider frontier selected')
            same(len(self.graph.candidates(2)), 3, 'later smaller non-singleton competitor')
            same(self.graph.generation(2), 2, 'later generation retained')
        elif identifier == 'pending-source-not-fact':
            samples = [e['result'] for e in self.record['events'] if e['op'] == 'available_facts']
            point.need('3' not in samples[0]['complete'] and samples[0]['fact_potential'] == 0,
                       'pending marks/physically selected incomplete output give no fact reward')
            point.need(samples[1]['complete']['3'] == 1 and samples[1]['fact_potential'] == 2,
                       'true strict-prior source closure later activates output')
        elif identifier == 'repeated-ports':
            descriptor = self.control.records[0]
            same(descriptor['members'], [[6, 3, [0, 0]]], 'both repeated source occurrences retained')
            point.need(len(descriptor['ordered_receptor_ports'][0]['readers']) == 2 and
                       [2, 3, -3] in descriptor['aggregate_m'] and [3, 3, -3] in descriptor['aggregate_m'],
                       'repeated reader ports retain both distant offset channels')
        elif identifier == 'assigned-zero-remote-retirement':
            point.need(self.control.hints[0]['status'] == 'retired' and self.active is None and
                       self.graph.marks[1, 1] == 1 and [1, 1, 0] in self.control.records[0]['aggregate_m'],
                       'assigned zero conflicts remotely, whole hint retires and stays retired')
        elif identifier == 'waiting-persistence':
            point.need(self.control.hints[0]['status'] == 'consumed' and self.active is None and
                       sum(record['policy'] is not None for record in self.history) == 1,
                       'one selection persists waiting to ready to consumed without resampling')
        elif identifier == 'paired-rollback':
            same(self.semantic(), self.record['events'][0]['after']['overlay'], 'exact paired rollback to initial complete state')
            point.need(len(self.history) == 1 and not self.checkpoints, 'cumulative choice log retained while both checkpoints restored')
        elif identifier == 'unknown-no-exclusion':
            point.need(all(not values for values in self.graph.excluded) and self.counters['primitive_steps'] == 0,
                       'actual returned budget-UNKNOWN creates no exclusion')


def audit(result, corpus, exact_bindings):
    same(result['schema'], 'real-Controller-learned-overlay-fixture-v1', 'exact raw producer language')
    same([r['id'] for r in result['scenarios']], corpus['scenario_order'], 'all 24 frozen scenarios in order')
    same(result['scope'], corpus['scope'], 'synthetic fixture scope preserved')
    same(result['uncovered'], corpus['uncovered'], 'all implementation gaps retained')
    for name in ('actual_RNG_draws', 'training_updates', 'native_queries', 'actual_Hilbert_models', 'mathematical_proofs_accepted'):
        same(result[name], 0, 'no broad scientific claim from fixture: ' + name)
    same(result['independent_acceptance'], False, 'producer cannot self-admit independent acceptance')
    receipts = [Replay(record, corpus, exact_bindings).run() for record in result['scenarios']]
    return dict(schema='independent-real-Controller-overlay-fixture-replay-v1',
        status='complete_synthetic_fixture_point_and_overlay_replay_passed', scenarios=receipts,
        complete_trace_accepted=True, feature_policy_replay_accepted=True,
        primitive_certificate_accepted=False, actual_RNG_replay_accepted=False,
        training_update_accepted=False, actual_donor_heldout_DFS_accepted=False,
        covered='Every observed synthetic fixture operation, full domain, state, hint, feature, policy and paired rollback',
        uncovered=copy.deepcopy(corpus['uncovered']),
        scope='An activated actual invocation is still required; source author has run none of these functions.')
