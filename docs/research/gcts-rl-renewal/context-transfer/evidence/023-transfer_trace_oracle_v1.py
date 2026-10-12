"""Prospective independent full fixed-family tape and positive proof audit.

There are no scientific imports at module load. ROOT alone dispatches after an
exact actual-input freeze. Independent source/point libraries reconstruct the
pool and every graph/transaction demanded by the returned tape; no search or
producer graph/controller/order/decoder is imported as acceptance authority.
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
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return dict(path=str(path), sha256=h.hexdigest(), bytes=path.stat().st_size)


def verify(plan):
    checked = {}
    for group in ('sources', 'libraries', 'inputs', 'preserved'):
        for item in plan[group]:
            expected = {k: item[k] for k in ('path', 'sha256', 'bytes')}
            if item['path'] not in checked: checked[item['path']] = pin(item['path'])
            if checked[item['path']] != expected:
                raise ValueError('exact independent input/source bytes: ' + item['path'])
    return len(checked)


def load(role, paths, name):
    location = Path(paths[role]); sys.path.insert(0, str(location.parent))
    spec = importlib.util.spec_from_file_location(name, location)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def independent_libraries(plan):
    paths = {item['role']: item['path'] for item in plan['libraries']}
    point = load('independent_point', paths, 'full_point_oracle_v1')
    body = load('independent_families', paths, 'full_family_registry_v1')
    symbolic = load('independent_symbolic', paths, 'independent_aggregate_audit_v1')
    expansion = load('independent_expansion', paths, 'fixed_pool_trace_expansion_v1')
    transactions = load('independent_transactions', paths, 'geometry_trace_point_v1')
    static = load('independent_static_pool', paths, 'fixed_pool_static_reconstruction_v1')
    hints = load('independent_pool_transactions', paths, 'fresh_transfer_whole_hint_oracle_v1')
    positive = load('independent_positive_certificate', paths, 'fixed_pool_positive_certificate_v1')
    forward = load('independent_fixed_forward',paths,'geometry_trace_order_v1')
    context = load('independent_context',paths,'fresh_context_acceptance_oracle_v1')
    return point, body, symbolic, expansion, transactions, static, hints, positive, forward, context


def measured_transactions(base_class, point, body):
    """Cumulative integer work counts; semantic snapshots never roll these back."""
    class MeasuredPool(base_class):
        def __init__(self, *args):
            self.counts = dict(whole_scans=0, members_checked=0, mark_checks=0,
                status_updates=0, whole_retirements=0, resynchronizations=0,
                ordering_calls=0, root_rejections=0, selected_identity_reads=0)
            super().__init__(*args)
            self.root_selected_identity_reads = self.counts['selected_identity_reads']

        def _view(self, descriptor, choice, old):
            if old['status'] != 'retired':
                self.counts['whole_scans'] += 1
                if (point.digest([self.state.epoch, self.state.recipes, self.state.roots]) == self.invariant
                        and descriptor['body_authority_epoch'] == self.group_epoch
                        and descriptor['graph_binding']['model_epoch'] == self.state.epoch):
                    additional = {}; reason = None
                    for value, identifier in zip(descriptor['members'], descriptor['full_member_ids']):
                        self.counts['members_checked'] += 1
                        key = body.key(value)
                        if key in self.state.selected:
                            self.counts['selected_identity_reads'] += 1
                            t, m = point.points(self.state.recipes[key[0]], key[1], key[2], self.state.height)
                            if point.decorate(key, t, m, self.state.recipes, self.context,
                                    self.authority, self.registry)['id'] != identifier:
                                reason = 'selected_identity_mismatch'; break
                            continue
                        if not self.state.legal(key): reason = 'pending_member_illegal'; break
                        for x, y, value in point.points(self.state.recipes[key[0]], key[1], key[2], self.state.height)[0]:
                            additional[x, y] = additional.get((x, y), 0) + value
                            if self.state.totals[y] + additional[x, y] > 1:
                                reason = 'pending_aggregate_overcapacity'; break
                        if reason: break
                    if reason is None:
                        for x, y, value in descriptor['aggregate_m']:
                            self.counts['mark_checks'] += 1
                            if (x, y) in self.state.marks and self.state.marks[x, y] != value: break
            return super()._view(descriptor, choice, old)

        def sync(self):
            before = copy.deepcopy(self.hints)
            choice = super().sync()
            self.counts['resynchronizations'] += 1
            for old, new in zip(before, self.hints):
                if point.canonical(old) != point.canonical(new):
                    self.counts['status_updates'] += 1
                    if old['status'] != 'retired' and new['status'] == 'retired':
                        self.counts['whole_retirements'] += 1
            return choice

        def order(self, choice):
            self.counts['ordering_calls'] += 1
            return super().order(choice)
    return MeasuredPool


class Tape:
    def __init__(self, result, tx, spec, point, body, transactions, positive, symbolic,
                 model, data, sources, fixed, target):
        self.result, self.tx, self.spec = result, tx, spec
        self.p, self.b, self.transactions, self.positive, self.symbolic = point, body, transactions, positive, symbolic
        self.model, self.data, self.sources, self.fixed, self.target = model, data, sources, fixed, target
        self.events = result['events']; self.pos = self.nodes = self.attempts = self.forced = self.branches = 0
        self.exhausted = {}; self.exclusions = []; self.orders = []; self.expected_hashes = []; self.identities = []
        self.logical = None

    def next_kind(self):
        self.p.need(self.pos < len(self.events), 'complete returned tape is not a truncated prefix')
        return self.events[self.pos]['kind']

    def consume(self, kind, node, **fields):
        self.p.need(self.pos < len(self.events), 'missing independent event ' + kind)
        expected = dict(kind=kind, node=node, **fields, state=self.tx.compact())
        self.b.equal(self.events[self.pos], expected, 'complete independently reconstructed event ' + str(self.pos))
        self.expected_hashes.append(self.p.digest(expected)); self.pos += 1

    def rollback(self, saved, checkpoint, node, reason):
        self.tx.restore(saved)
        self.b.equal(self.tx.checkpoint(), checkpoint, 'exact independent paired checkpoint')
        self.consume('paired_rollback', node, checkpoint=checkpoint, reason=reason)

    def apply(self, chosen, node):
        s = self.tx.state
        full = self.p.decorate(chosen, *self.p.points(s.recipes[chosen[0]], chosen[1], chosen[2], s.height),
            s.recipes, self.model['context'], self.data['authority']['epoch'], self.p.digest(self.data['formula_codes']))
        self.identities.append(dict(node=node, **full))
        self.tx.apply(chosen)

    def stream_sha(self, keys):
        return hashlib.sha256(('\n'.join(self.p.canonical(self.b.key_data(k)) for k in keys) + '\n').encode()).hexdigest()

    def walk(self, parent=None):
        node = self.nodes; self.nodes += 1
        entry, checkpoint = self.tx.saved(), self.tx.checkpoint()
        self.consume('node_enter', node, parent_node=parent, checkpoint=checkpoint)
        while True:
            choice = self.transactions.decision(self.tx.full())
            self.consume('global_decision', node, decision=choice)
            if choice[0] == 'dead':
                self.consume('proved_global_dead', node)
                self.rollback(entry, checkpoint, node, 'dead_subtree')
                status = 'exhausted_finite_marked_subtree'
                self.consume('node_return', node, status=status)
                self.exhausted[node] = dict(row=choice[1], reason='independently_zero_complete_domain')
                return status, node
            if choice[0] == 'complete':
                self.tx.sync()
                self.consume('node_return', node, status='finite_exact_point_tiling')
                return 'finite_exact_point_tiling', node
            if self.next_kind() == 'budget_unknown_no_exclusion':
                self.p.need(self.attempts >= self.spec['attempts'] or self.result['seconds'] >= self.spec['seconds'],
                    'UNKNOWN uses exact attempt ceiling or preserved checked-clock provenance, never exhaustion')
                self.consume('budget_unknown_no_exclusion', node)
                self.rollback(entry, checkpoint, node, 'budget_unknown')
                self.consume('node_return', node, status='unknown_search_budget')
                return 'unknown_search_budget', node
            self.p.need(self.attempts < self.spec['attempts'], 'no primitive step past attempt ceiling')
            base, ordered, hint_trace = self.tx.order(choice)
            self.p.need(ordered, 'complete nonempty selected-point domain')
            selected = ordered[0]
            self.consume('complete_chosen_domain_order', node, decision=choice,
                base_keys_sha256=self.stream_sha(base), ordered_keys_sha256=self.stream_sha(ordered),
                complete_count=len(base), selected_key=self.b.key_data(selected), mode=self.result['mode'],
                whole_pool_order_trace=hint_trace)
            self.orders.append(dict(node=node, decision=choice, complete_count=len(base),
                base_keys_sha256=self.stream_sha(base), ordered_keys_sha256=self.stream_sha(ordered),
                selected_key=self.b.key_data(selected), whole_pool_order_trace=hint_trace,
                changed_first=selected != base[0], changed_permutation=ordered != base))
            if self.next_kind() == 'budget_unknown_after_order_no_exclusion':
                self.p.need(self.result['seconds'] >= self.spec['seconds'], 'post-order saved checked-clock cutoff')
                self.consume('budget_unknown_after_order_no_exclusion', node)
                self.rollback(entry, checkpoint, node, 'budget_unknown_after_order')
                self.consume('node_return', node, status='unknown_search_budget')
                return 'unknown_search_budget', node
            if choice[0] == 'forced':
                self.p.need(base == ordered and len(base) == 1, 'forced-first singleton bypass of advice')
                self.apply(selected, node); self.attempts += 1; self.forced += 1
                self.consume('primitive_step', node, key=self.b.key_data(selected)); continue
            self.p.need(choice[0] == 'branch', 'only earliest-generation complete branching')
            saved, parent_cp = self.tx.saved(), self.tx.checkpoint()
            self.consume('branch_begin', node, key=self.b.key_data(selected), parent_checkpoint=parent_cp)
            self.apply(selected, node); self.attempts += 1; self.branches += 1
            self.consume('primitive_step', node, key=self.b.key_data(selected))
            status, child = self.walk(node)
            if status == 'finite_exact_point_tiling':
                self.consume('node_return', node, status=status, child_node=child)
                return status, node
            self.rollback(saved, parent_cp, node, 'restored_branch_parent')
            if status.startswith('unknown_'):
                self.rollback(entry, checkpoint, node, 'unknown_child_without_exclusion')
                self.consume('node_return', node, status=status, child_node=child)
                return status, node
            self.p.need(status == 'exhausted_finite_marked_subtree' and child in self.exhausted,
                'parent-local exclusion requires independently exhausted recorded child')
            self.consume('before_exhausted_child_exclusion', node, key=self.b.key_data(selected), child_node=child, child_status=status)
            self.tx.exclude(selected)
            self.consume('parent_local_exhausted_child_exclusion', node, key=self.b.key_data(selected), child_node=child, child_status=status)
            self.exclusions.append(dict(parent=node, child=child, key=self.b.key_data(selected), reason=self.exhausted[child]))

    def run(self):
        initial = self.tx.saved()
        self.b.equal(self.result['initial_state'], self.tx.compact(), 'whole independently seeded registry/graph/hints')
        self.consume('solve_begin', None, mode=self.result['mode'], max_attempts=self.spec['attempts'],
            seconds=self.spec['seconds'], event_ceiling=self.spec['event_ceiling'])
        status, root = self.walk()
        self.p.need(self.pos == len(self.events), 'no unexplained returned suffix')
        self.b.equal(self.result['termination'], dict(kind='returned', root_node=root), 'complete returned tape, no TraceLimit prefix acceptance')
        self.b.equal(self.result['status'], status, 'independent terminal status')
        self.p.need(status in ('unknown_search_budget', 'finite_exact_point_tiling', 'exhausted_finite_marked_subtree'), 'finite returned status')
        solved = status == 'finite_exact_point_tiling'
        if solved:
            self.logical = self.positive.check_complete_point_and_proof(self.result['point_certificate'], self.tx.state,
                formulas=self.data['formula_codes'], context=self.model['context'], authority_epoch=self.data['authority']['epoch'],
                original_target=self.target, original_source_bindings=self.sources, original_fixed_marks=self.fixed,
                point=self.p, symbolic=self.symbolic)
            decoded = self.result['decoded_certificate']; self.p.need(type(decoded) is dict, 'returned positive translation')
            for field in ('local_certificate','flat_request','request_ascii','request_bytes','request_sha256','problem_sha256','retained_hypotheses'):
                self.b.equal(decoded[field], self.logical[field], 'independent complete logical translation ' + field)
            for field, expected in dict(model_epoch=self.tx.state.epoch, point_certificate=self.result['point_certificate'], rows=24,
                    status='decoded_exact_primitive_ground_certificate_pending_independent_symbolic_check', native_queries=0, native_accepted=False).items():
                self.b.equal(decoded[field], expected, 'positive producer translation scope ' + field)
        else:
            self.tx.restore(initial)
            self.b.equal(self.result['point_certificate'], None, 'UNKNOWN/exhausted has no certificate')
            self.b.equal(self.result['decoded_certificate'], None, 'UNKNOWN/exhausted has no logical translation')
        self.b.equal(self.result['terminal_state'], self.tx.compact(), 'complete terminal graph/hint state')
        self.b.equal(self.result['root_restored'], not solved, 'terminal paired root restoration')
        self.b.equal(self.result['node_count'], self.nodes, 'complete node count')
        self.b.equal(self.result['attempts'], self.attempts, 'complete primitive attempt count')
        self.b.equal(self.result['fixed_pool_descriptor_ids'], [d['descriptor_id'] for d in self.tx.descriptors], 'complete immutable sorted descriptor IDs')
        self.b.equal(self.result['fixed_pool_priorities'], [d['fixed_priority'] for d in self.tx.descriptors], 'source-epoch fixed priorities')
        entry = self.result['graph_metrics_at_search_entry']; metrics = self.result['graph_metrics']
        for name, value in dict(placements=3, attempts=0, forced=0, branches=0, backtracks=0).items():
            self.b.equal(entry[name], value, 'original root activity at search entry ' + name)
        for name, value in dict(placements=3+self.attempts, attempts=self.attempts, forced=self.forced,
                branches=self.branches, backtracks=len(self.exclusions)).items():
            self.b.equal(metrics[name], value, 'independent cumulative primitive counter ' + name)
        for name in ('proposal_validations', 'proposal_rejections'):
            self.p.integer(entry[name]); self.p.need(entry[name] >= 0, 'nonnegative preparation work counter')
            self.b.equal(metrics[name], entry[name], 'no new root registration during target search ' + name)
        self.p.integer(entry['lazy_id_constructions'])
        self.b.equal(metrics['lazy_id_constructions'], entry['lazy_id_constructions']
            + self.tx.counts['selected_identity_reads'] - self.tx.root_selected_identity_reads + (24 if solved else 0),
            'post-entry complete selected-identity checks and positive certificate decoration')
        for name in ('whole_scans','members_checked','mark_checks','status_updates','whole_retirements','resynchronizations','ordering_calls','root_rejections'):
            self.b.equal(self.result['lifecycle_metrics'][name], self.tx.counts[name], 'independent full hint integer counter ' + name)
        self.b.equal(self.result['ordering_metrics']['complete_order_calls'], len(self.orders), 'complete ordering census')
        self.b.equal(self.result['ordering_metrics']['complete_order_keys'], sum(o['complete_count'] for o in self.orders), 'every fallback key counted')
        self.b.equal(self.tx.counts['resynchronizations'], 1+len(self.orders)+self.attempts+len(self.exclusions)+int(solved), 'root/order/step/exclusion/complete resynchronizations')
        if self.result['mode']=='fixed-forward':
            forward_metrics=self.result['fixed_forward_metrics']
            branch_orders=[o for o in self.orders if o['decision'][0]=='branch']
            self.b.equal(forward_metrics['calls'],len(branch_orders),'all unchanged fixed-forward branch ranker calls')
            self.b.equal(forward_metrics['complete_keys_ranked'],sum(o['complete_count'] for o in branch_orders),'every fixed-forward full-domain key')
        else:self.b.equal(self.result['fixed_forward_metrics'],None,'no fixed-forward recipe ranker in base/pool')
        for name, value in dict(active_cluster_descriptors=len(self.tx.descriptors), authored_words_used_as_hints=0, native_queries=0,
                new_RL_training=False, atomic_macro_moves=0, available_source_family_count=171).items():
            self.b.equal(self.result[name], value, 'fixed scope field ' + name)
        self.b.equal(self.result['body_authority_epoch'], self.tx.group_epoch, 'independent complete group authority')
        self.p.need(len(self.events) <= self.spec['event_ceiling'], 'retained tape event ceiling')
        return dict(status=status, trace_accepted=True, certificate_accepted=solved, root_restored=not solved,
            events=len(self.events), nodes=self.nodes, attempts=self.attempts, forced=self.forced, branches=self.branches,
            proved_child_exclusions=self.exclusions, complete_orders=self.orders,
            full_step_identities=self.identities, every_event_expected_sha256=self.expected_hashes,
            graph_censuses=self.tx.censuses, distinct_graph_states=len(self.tx.censuses),
            complete_base_binding_checks=sum(c['complete_base_candidates'] for c in self.tx.censuses),
            complete_legal_binding_checks=sum(c['complete_legal_candidates'] for c in self.tx.censuses),
            reconstructed_integer_hint_counts=self.tx.counts,
            changed_first_choices=sum(o['changed_first'] for o in self.orders),
            changed_permutations=sum(o['changed_permutation'] for o in self.orders),
            independently_checked_positive_certificate=self.logical,
            point_certificates=int(solved), decoded_certificates=int(solved), native_queries=0,
            unverified_implementation_costs='Saved preparation/domain-refresh/timers are provenance; root registration lazy-ID baseline is not independently duplicated as a counter. Post-entry lazy-ID delta and every hint integer counter are reconstructed.')


def event_controls(tape):
    """Changed actual payloads vs independently reconstructed exact templates."""
    receipts = []
    def find(kind): return next((i for i, e in enumerate(tape.events) if e['kind'] == kind), None)
    def reject(label, index, mutate):
        if index is None: return
        changed = copy.deepcopy(tape.events[index]); mutate(changed)
        tape.p.need(tape.p.digest(changed) != tape.expected_hashes[index], 'control changes independently checked event')
        receipts.append(dict(name=label, event=index, rejected=True, mutant_sha256=tape.p.digest(changed),
            independent_expected_sha256=tape.expected_hashes[index], scope='Changed actual per-event payload against independent template; not full mutated tape or owned-process replay'))
    d=find('global_decision'); o=find('complete_chosen_domain_order'); s=find('primitive_step')
    reject('false_complete_point_degree',d,lambda e:e['decision'].__setitem__(2,e['decision'][2]+1))
    reject('wrong_generation_scheduler',d,lambda e:e['decision'].__setitem__(1,(e['decision'][1]+1)%24))
    reject('exterior_mark_erased',d,lambda e:e['state']['projection']['graph']['marks'].pop(0))
    reject('full_factor_hash_altered',d,lambda e:e['state'].__setitem__('full_semantic_sha256','0'*64))
    reject('incomplete_fallback_stream',o,lambda e:e.__setitem__('base_keys_sha256','0'*64))
    reject('preferred_stream_altered',o,lambda e:e.__setitem__('ordered_keys_sha256','0'*64))
    descriptor_order_event=next((i for i,e in enumerate(tape.events) if e['kind']=='complete_chosen_domain_order'
        and e['whole_pool_order_trace']['descriptor_order']),None)
    reject('immutable_priority_changed',descriptor_order_event,lambda e:e['whole_pool_order_trace']['descriptor_order'][0].__setitem__('fixed_priority',99))
    preferred_event=next((i for i,e in enumerate(tape.events) if e['kind']=='complete_chosen_domain_order'
        and e['whole_pool_order_trace']['preferred_keys']),None)
    reject('missing_ordered_eligible_member',preferred_event,lambda e:e['whole_pool_order_trace']['preferred_keys'].pop())
    reject('pending_output_claimed_proved',o,lambda e:e['whole_pool_order_trace'].__setitem__('advice_scope','proved new premise'))
    reject('wrong_complete_recipe_key',s,lambda e:e['key'].__setitem__(0,(e['key'][0]+1)%229))
    descriptor_step=next((i for i,e in enumerate(tape.events) if e['kind']=='primitive_step'
        and e['state']['projection']['descriptor_ids']),None)
    reject('false_formula_identity_sharing',descriptor_step,lambda e:e['state']['projection']['descriptor_ids'].__setitem__(0,'formula-only-share'))
    reject('whole_registry_dropped',descriptor_step,lambda e:e['state']['projection']['descriptor_ids'].pop())
    reject('stale_group_epoch',s,lambda e:e['state']['projection'].__setitem__('authority_epoch','0'*64))
    reject('boolean_hint_revision',s,lambda e:e['state']['projection'].__setitem__('hint_revision',False))
    retired=next((i for i,e in enumerate(tape.events) if any(h['status']=='retired' for h in e['state']['projection']['hint_states'])),None)
    def revive(e):
        h=next(h for h in e['state']['projection']['hint_states'] if h['status']=='retired');h['status']='waiting';h['reason']=None
    reject('illegal_sibling_survives_whole_retirement',retired,revive)
    r=find('paired_rollback')
    reject('inexact_paired_revision',r,lambda e:e['checkpoint'].__setitem__(2,e['checkpoint'][2]+1))
    reject('inexact_mark_refcount_rollback',r,lambda e:e['state']['projection']['graph']['marks'][0].__setitem__(3,2))
    x=find('before_exhausted_child_exclusion')
    reject('unknown_child_falsely_exhausted',x,lambda e:e.__setitem__('child_status','unknown_search_budget'))
    reject('unrelated_child_pruning_authority',x,lambda e:e.__setitem__('child_node',999999))
    u=find('budget_unknown_no_exclusion')
    reject('unknown_event_claims_exhaustion',u,lambda e:e.__setitem__('kind','proved_global_dead'))
    reject('UNKNOWN_excludes_parent_key',u,lambda e:e['state']['projection']['graph']['excluded'][3].append([0,3,[]]))
    return receipts


def run(plan):
    """Later ROOT-owned complete three-lane trace and conditional positive audit."""
    phase=time.perf_counter();checked=verify(plan)
    p,b,symbolic,expansion,transactions,static,hints,positive,forward,context=independent_libraries(plan)
    paths={item['role']:item['path'] for item in plan['libraries']}
    worker=load('independent_worker',paths,'fresh_transfer_common_gate_v1')
    roles={r['role']:Path(r['path']) for r in plan['inputs']}
    terminals=worker.validate_terminal(roles,'trace',plan,p,b)
    source=terminals['producer_plan'];outcome=terminals['producer_outcome']
    accepted,pool,pool_counts,roles,timings,donor,compiled,prep,evidence=worker.rebuild(plan,p,b,symbolic,expansion,static,context)
    fresh_result=p.read(roles['fresh_static_result']);fresh_life=p.read(roles['fresh_static_lifetime'])
    static_terminal=p.read(roles['fresh_static_root_terminal'])
    p.need(fresh_result['status']=='passed_independent_fresh_context_family_pool_audit'
        and fresh_life['status']=='passed_owned_independent_fresh_context_family_pool_audit'
        and fresh_life['child_reaped'] is True and fresh_life['child_exit']==0,
        'actual complete new-model static and resource prerequisites')
    relative=worker.relative
    b.equal(fresh_result['plan'],relative(roles['fresh_static_plan']),'same exact new static plan')
    b.equal(fresh_life['plan'],fresh_result['plan'],'same owned new static plan')
    b.equal(fresh_life['result'],relative(roles['fresh_static_result']),'owned exact fresh static result')
    for name, value in [('owner_exit_code',0),('owner_process_terminal_reaped',True),('worker_reaped',True)]:
        b.equal(static_terminal[name],value,'ROOT static terminal '+name)
    b.equal(static_terminal['lifetime'],relative(roles['fresh_static_lifetime']),'ROOT actual fresh static lifetime')
    for name,value in [('compiled_context_pin',relative(roles['compiled_context'])),
            ('preparation_evidence_pin',relative(roles['preparation_evidence'])),('model_epoch',accepted['model_epoch']),
            ('group_authority_epoch',pool.epoch),('original_body_authority_epoch',pool.original_epoch)]:
        b.equal(fresh_result[name],value,'new static gate independently repeated '+name)
    for name,value in dict(primitive_license_count=229,non_assumption_witness_count=226,source_body_count=171,
            single_types=171,pair_types=29241).items():b.equal(fresh_result[name],value,'complete fresh inventory '+name)
    b.equal(fresh_result['complete_census'],pool_counts['complete_census'],'fresh full static census repeated')
    expected_gate={name:relative(roles['fresh_static_'+name]) for name in ('plan','result','lifetime','root_terminal')}
    b.equal(source['fresh_static_gate_pins'],expected_gate,'exact search prerequisite new static gate')
    b.equal(source['model_epoch'],accepted['model_epoch'],'same fresh context/model in every lane')
    b.equal(source['complete_saved_pool_count'],len(pool.groups),'complete available pool, no winner subset')
    modes=['base','fixed-forward','fixed-whole-family-pool']
    p.need([r['mode'] for r in source['observations']]==modes,'all three frozen equal-inventory controls')
    p.need(not outcome['unexecuted'] and len(outcome['observations'])==3,'complete three returned tapes required; unexecuted stays UNKNOWN')
    results=[];all_controls=[];proof_controls=[]
    target=accepted['problem']['target'];fixed=sorted(accepted['model']['boundary']['fixed_exterior_m']+accepted['model']['boundary']['fixed_target_m'])
    for number,(spec,record) in enumerate(zip(source['observations'],outcome['observations'])):
        p.need(spec['attempts']==128 and spec['seconds']==20 and spec['event_ceiling']==2000,'unchanged matched finite search budgets')
        b.equal(record['id'],spec['id'],'frozen observation identity');b.equal(record['mode'],spec['mode'],'frozen mode')
        path=roles['actual_trace_'+str(number)];b.equal(record['result'],relative(path),'actual exact returned lane bytes')
        result=p.read(path)
        b.equal(result['limits'],dict(attempts=128,seconds=20,events=2000),'complete lane limits')
        b.equal(result['observation_id'],spec['id'],'same exact lane');b.equal(result['mode'],spec['mode'],'same exact mode')
        b.equal(result['context_transfer_schema'],'closed-recipient-context-transfer-v1','fresh context schema')
        b.equal(result['fresh_static_gate'],expected_gate,'same actual accepted new static inputs')
        b.equal(result['original_body_authority_epoch'],pool.original_epoch,'same fresh171 conditional bodies')
        b.equal(result['group_authority_epoch'],pool.epoch,'same entire pool available in all lanes')
        b.equal(result['complete_saved_pool_count'],len(pool.groups),'same available inventory, descriptors alone differ')
        state=transactions.PointState(24,accepted['state'].recipes,fixed,[0]*24,accepted['model_epoch'])
        for key in accepted['state'].order:state.apply(key,generation=0)
        b.equal(state.semantic(),accepted['state'].semantic(),'independent original Gamma-only initial point state')
        descriptors=pool.groups if spec['mode']=='fixed-whole-family-pool' else []
        epoch=pool.epoch if spec['mode']=='fixed-whole-family-pool' else pool.original_epoch
        Measured=measured_transactions(hints.FixedPoolTransactions,p,b)
        tx=Measured(state,descriptors,epoch,accepted['model']['context'],accepted['data']['authority']['epoch'],
            p.digest(accepted['data']['formula_codes']),p,b,transactions,spec['mode'],forward,accepted['data']['formula_codes'])
        tape=Tape(result,tx,spec,p,b,transactions,positive,symbolic,accepted['model'],accepted['data'],
            accepted['source_bindings'],fixed,target)
        started=time.perf_counter();checked_trace=tape.run();checked_trace['id']=spec['id']
        checked_trace['mode']=spec['mode'];checked_trace['audit_seconds_before_controls']=time.perf_counter()-started
        b.equal(record['status'],checked_trace['status'],'actual terminal result')
        b.equal(record['attempts'],checked_trace['attempts'],'actual primitive attempts')
        b.equal(record['events'],checked_trace['events'],'every complete returned event')
        b.equal(record['decoded_candidate'],checked_trace['certificate_accepted'],'certificate presence independently accepted')
        all_controls.append(dict(id=spec['id'],controls=event_controls(tape)))
        proof_controls.append(dict(id=spec['id'],controls=positive_controls(tape)))
        results.append(checked_trace)
    verify(plan)
    return dict(status='passed_independent_fresh_context_complete_trace_audit',plan=relative(plan['plan_path']),
        trace_accepted=True,certificate_accepted=any(r['certificate_accepted'] for r in results),
        static_context_pool_accepted=True,model_epoch=accepted['model_epoch'],context_id=accepted['context_id'],
        original_Gamma=accepted['problem']['gamma'],target=target,primitive_license_count=229,
        non_assumption_witness_count=226,source_body_count=171,single_types=171,pair_types=29241,
        original_body_authority_epoch=pool.original_epoch,group_authority_epoch=pool.epoch,
        repeated_independent_static_census=pool_counts,independent_source_logical_receipts=pool.source_receipts,
        independent_source_expansion_counts=pool.source_counts,observations=results,
        actual_event_controls=all_controls,actual_positive_certificate_or_symbolic_controls=proof_controls,
        whole_target_logical_checks=sum(r['decoded_certificates'] for r in results),
        point_certificates=sum(r['point_certificates'] for r in results),native_queries=0,native_accepted=False,
        searches_run_by_auditor=0,training_runs=0,phase_timings=timings,unique_raw_byte_pins=checked,
        worker_seconds_before_result_serialization=time.perf_counter()-phase,
        scope='Exact returned full-language traces and any complete24-row new-Gamma ground proof; within-library changed-premise transfer only.',
        limitations=['UNKNOWN remains UNKNOWN; no theorem nonprovability or infinite tiling claim.',
            'Truncated TraceLimit prefixes fail closed for complete trace acceptance; no invented continuation/exhaustion.',
            'All171 conditional source bodies are prior authored/certified inventory, not newly mined lemmas. No authored target-word guidance or new RL.',
            'Exact ground Gamma is retained in flat blocks=[] request; no native/shared machine/compiler or universal closure acceptance.',
            'Per-event payload mutations use rebuilt expected templates; positive certificate/primitive logical mutants actually rerun the independent checker. Not full mutated-tape/owner replays.',
            'Saved implementation timers/registration baseline and checked deadline overshoot are provenance. New full audit lifetime charged separately.'])


def positive_controls(tape):
    """Rerun independent positive checks on mutated actual certificates only."""
    if tape.logical is None:return []
    p,checker=tape.p,tape.symbolic.SymbolicChecker(tape.model['context']['theory'])
    receipts=[]
    def certificate_case(name,change):
        changed=copy.deepcopy(tape.result['point_certificate']);change(changed)
        try:
            tape.positive.check_complete_point_and_proof(changed,tape.tx.state,
                formulas=tape.data['formula_codes'],context=tape.model['context'],authority_epoch=tape.data['authority']['epoch'],
                original_target=tape.target,original_source_bindings=tape.sources,original_fixed_marks=tape.fixed,
                point=p,symbolic=tape.symbolic)
        except (ValueError,tape.symbolic.Rejected) as exc:
            receipts.append(dict(name=name,rejected=True,mutant_sha256=p.digest(changed),reason=str(exc),
                scope='Actually rejected mutated complete certificate by independent checker; no native or owned-process replay'))
        else:raise ValueError('positive certificate mutant accepted: '+name)
    certificate_case('false_full_primitive_identity',lambda c:c['placements'][3].__setitem__('id','formula-only-share'))
    certificate_case('duplicate_physical_placement',lambda c:c['placements'].append(copy.deepcopy(c['placements'][0])))
    certificate_case('stale_point_model_epoch',lambda c:c.__setitem__('model_epoch','0'*64))
    certificate_case('boolean_row_identity',lambda c:c['placements'][1]['key'].__setitem__(1,True))
    certificate_case('hidden_extra_assigned_zero_mark',lambda c:c['placements'][3]['m'].append([8,3,0]))
    certificate_case('incomplete_original_source_closure',lambda c:c['source_bindings'].pop(next(iter(c['source_bindings']))))
    commands=tape.logical['local_certificate']['proof'];premises=tape.model['context']['ordered_local_premises']
    def logical_case(name,proof,local,target):
        try:checker.proof(proof,local,target)
        except tape.symbolic.Rejected as exc:
            receipts.append(dict(name=name,rejected=True,mutant_sha256=p.digest([proof,local,target]),reason=str(exc),
                scope='Actually rejected altered primitive logical proof or original premise/target by independent symbolic checker'))
        else:raise ValueError('logical mutant accepted: '+name)
    for rule in ('instantiate','eq_subst'):
        row=next((i for i,c in enumerate(commands) if c['rule']==rule),None)
        if row is not None:
            changed=copy.deepcopy(commands);changed[row]['formula']=['bot']
            logical_case('invalid_primitive_'+rule,changed,premises,tape.target)
    row=next((i for i,c in enumerate(commands) if c['rule']=='mp'),None)
    if row is not None:
        changed=copy.deepcopy(commands);c=changed[row];c['antecedent'],c['implication']=c['implication'],c['antecedent']
        logical_case('reversed_ordered_MP_sources',changed,premises,tape.target)
    changed=copy.deepcopy(commands);changed[0]['index']=1
    logical_case('changed_hypothesis_occurrence',changed,premises,tape.target)
    logical_case('Gamma_erased_from_ground_sequent',commands,[],tape.target)
    logical_case('conclusion_replaced_by_falsehood',commands,premises,['bot'])
    request=copy.deepcopy(tape.logical['flat_request']);request['theory']['axioms'].pop('hypothesis-0')
    try:tape.symbolic.SymbolicChecker(request['theory']).proof(request['proof'],[],request['target'])
    except tape.symbolic.Rejected as exc:
        receipts.append(dict(name='retained_flat_Gamma_axiom_erased',rejected=True,mutant_sha256=p.digest(request),reason=str(exc),
            scope='Actually rejected altered Gamma-retaining flat proof with one required hypothesis axiom removed'))
    else:raise ValueError('flat request lost Gamma but accepted')
    p.need(tape.logical['flat_request']['blocks']==[],'positive flat translation has no macro authority')
    return receipts

