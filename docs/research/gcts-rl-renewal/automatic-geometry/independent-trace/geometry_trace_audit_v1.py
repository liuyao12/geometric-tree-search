"""Root-dispatched independent audit of completed primitive geometry tapes.

This is an event/certificate verifier, not a search. It imports only our pinned
prior independent logical/point/source-family libraries. Every actual child
exclusion needs a recursively reconstructed exhausted child; unknowns roll back.
The frozen two observations have no point certificate, and this version fails
closed on any positive certificate rather than borrowing the producer decoder.
"""
import copy
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def libraries(plan):
    paths = {e['role']: ROOT/e['path'] for e in plan['libraries']}
    sys.path.insert(0, str(paths['independent_point'].parent))
    sys.path.insert(0, str(paths['symbolic_checker'].parent))
    loaded = {}
    for role, name in (('symbolic_checker', 'independent_aggregate_audit_v1'),
                       ('expansion_checker', 'trace_independent_expansion_library')):
        spec = importlib.util.spec_from_file_location(name, paths[role])
        m = importlib.util.module_from_spec(spec); sys.modules[name] = m
        spec.loader.exec_module(m); loaded[role] = m
    return loaded['symbolic_checker'], loaded['expansion_checker']


def verify_pins(plan, pin, need):
    checked = {}
    for group in ('sources', 'libraries', 'inputs', 'preserved_files'):
        for e in plan.get(group, []):
            if e['path'] not in checked:
                checked[e['path']] = pin(ROOT/e['path'])
            need(checked[e['path']] == {k:e[k] for k in ('sha256','bytes')},
                 'exact independent prerequisite: '+e['path'])
    return len(checked)


class Tape:
    def __init__(self, result, transaction, formulas, budget, model, authority, equal, need, digest):
        self.result = result; self.tx = transaction; self.formulas = formulas
        self.budget = budget; self.model = model; self.authority = authority; self.equal = equal
        self.need = need; self.digest = digest; self.events = result['events']; self.pos = 0
        self.next_node = 0; self.attempts = 0; self.forced = 0; self.branches = 0
        self.exclusions = []; self.orders = []; self.exhausted = {}; self.expected_hashes = []
        self.step_identities = []

    def apply(self, chosen, node):
        from full_point_oracle_v1 import decorate, points
        state = self.tx.state
        placed = decorate(chosen, *points(state.recipes[chosen[0]],chosen[1],chosen[2],24),
            state.recipes,self.model['context'],self.authority,self.digest(self.formulas))
        self.step_identities.append(dict(node=node,**placed))
        self.tx.apply(chosen)

    def next_kind(self):
        self.need(self.pos < len(self.events), 'complete event tape is not truncated')
        return self.events[self.pos]['kind']

    def consume(self, kind, node, **fields):
        self.need(self.pos < len(self.events), 'missing event: '+kind)
        expected = dict(kind=kind, node=node, **fields, state=self.tx.compact())
        actual = self.events[self.pos]
        self.equal(actual, expected, 'every independently reconstructed event '+str(self.pos))
        self.expected_hashes.append(self.digest(expected)); self.pos += 1
        return expected

    def rollback(self, saved, checkpoint, node, reason):
        self.tx.restore(saved)
        self.equal(self.tx.checkpoint(), checkpoint, 'exact independently restored paired checkpoint')
        self.consume('paired_rollback', node, checkpoint=checkpoint, reason=reason)

    def walk(self, parent=None):
        from geometry_trace_point_v1 import decision, key_data
        from geometry_trace_order_v1 import ordered_keys, stream_sha
        node = self.next_node; self.next_node += 1
        entry = self.tx.saved(); cp = self.tx.checkpoint()
        self.consume('node_enter', node, parent_node=parent, checkpoint=cp)
        while True:
            choice = decision(self.tx.full())
            self.consume('global_decision', node, decision=choice)
            if choice[0] == 'dead':
                # Every domain was reconstructed; count zero is a global dead
                # end. Induction over this recorded child tree establishes only
                # that this finite marked child, not the theorem, is exhausted.
                self.consume('proved_global_dead', node)
                self.rollback(entry, cp, node, 'dead_subtree')
                self.consume('node_return', node, status='exhausted_finite_marked_subtree')
                self.exhausted[node] = dict(reason='independently_zero_complete_domain', row=choice[1])
                return 'exhausted_finite_marked_subtree', node
            self.need(choice[0] != 'complete', 'positive certificate unsupported by this zero-certificate gate')
            if self.next_kind() == 'budget_unknown_no_exclusion':
                # A clock cutoff is safe UNKNOWN; without timestamp evidence it
                # cannot prove exhaustion. These exact completed runs hit the
                # attempt ceiling, which is reconstructed independently.
                self.need(self.attempts >= self.budget['attempts'], 'actual tape must bind its exact attempt cutoff')
                self.consume('budget_unknown_no_exclusion', node)
                self.rollback(entry, cp, node, 'budget_unknown')
                self.consume('node_return', node, status='unknown_search_budget')
                return 'unknown_search_budget', node
            self.need(self.attempts < self.budget['attempts'], 'no placement beyond attempt budget')
            self.tx.sync()
            base, ordered = ordered_keys(self.tx.state, self.formulas, choice, self.result['mode'])
            self.need(ordered, 'chosen nonempty complete domain')
            chosen = ordered[0]
            self.consume('complete_chosen_domain_order', node, decision=choice,
                base_keys_sha256=stream_sha(base), ordered_keys_sha256=stream_sha(ordered),
                complete_count=len(base), selected_key=key_data(chosen), mode=self.result['mode'])
            self.orders.append(dict(node=node, decision=choice, complete_count=len(base),
                base_sha256=stream_sha(base), ordered_sha256=stream_sha(ordered),
                selected_key=key_data(chosen), changed_first=chosen != base[0],
                changed_permutation=ordered != base))
            if self.next_kind() == 'budget_unknown_after_order_no_exclusion':
                self.consume('budget_unknown_after_order_no_exclusion', node)
                self.rollback(entry, cp, node, 'budget_unknown_after_order')
                self.consume('node_return', node, status='unknown_search_budget')
                return 'unknown_search_budget', node
            if choice[0] == 'forced':
                self.need(len(base) == 1 and ordered == base, 'global forced singleton unchanged')
                self.apply(chosen,node); self.attempts += 1; self.forced += 1
                self.consume('primitive_step', node, key=key_data(chosen))
                continue
            self.need(choice[0] == 'branch', 'only declared earliest-generation branching')
            saved = self.tx.saved(); parent_cp = self.tx.checkpoint()
            self.consume('branch_begin', node, key=key_data(chosen), parent_checkpoint=parent_cp)
            self.apply(chosen,node); self.attempts += 1; self.branches += 1
            self.consume('primitive_step', node, key=key_data(chosen))
            status, child = self.walk(node)
            self.rollback(saved, parent_cp, node, 'restored_branch_parent')
            if status.startswith('unknown_'):
                self.rollback(entry, cp, node, 'unknown_child_without_exclusion')
                self.consume('node_return', node, status=status, child_node=child)
                return status, node
            self.need(status == 'exhausted_finite_marked_subtree' and child in self.exhausted,
                      'parent pruning requires independently reconstructed exhaustion')
            self.consume('before_exhausted_child_exclusion', node, key=key_data(chosen),
                child_node=child, child_status=status)
            self.tx.exclude(chosen)
            self.consume('parent_local_exhausted_child_exclusion', node, key=key_data(chosen),
                child_node=child, child_status=status)
            self.exclusions.append(dict(parent=node, child=child, key=key_data(chosen),
                reason=self.exhausted[child]))

    def run(self):
        initial = self.tx.saved()
        self.equal(self.result['initial_state'], self.tx.compact(), 'exact independently seeded initial state')
        self.consume('solve_begin', None, mode=self.result['mode'], max_attempts=self.budget['attempts'],
            seconds=self.budget['seconds'], event_ceiling=self.budget['event_ceiling'])
        status, root = self.walk()
        self.need(self.pos == len(self.events), 'no unexplained event suffix')
        self.equal(self.result['termination'], dict(kind='returned',root_node=root), 'actual complete returned tape')
        self.equal(status, self.result['status'], 'independent terminal status')
        self.need(status == 'unknown_search_budget', 'this exact gate accepts two UNKNOWN observations only')
        self.tx.restore(initial)
        self.equal(self.result['terminal_state'], self.tx.compact(), 'whole UNKNOWN root restored exactly')
        self.equal(self.result['root_restored'], True, 'whole root restoration flag')
        self.equal(self.result['node_count'], self.next_node, 'complete node census')
        self.equal(self.result['attempts'], self.attempts, 'complete attempted placement census')
        self.equal(self.result['point_certificate'], None, 'zero point certificates')
        self.equal(self.result['decoded_certificate'], None, 'zero decoded certificates')
        m = self.result['graph_metrics']
        for k,v in dict(attempts=self.attempts, placements=self.attempts+3,
                        forced=self.forced,branches=self.branches,backtracks=len(self.exclusions),
                        lazy_id_constructions=0,proposal_validations=0,proposal_rejections=0).items():
            self.equal(m[k],v,'cumulative actual graph counter '+k)
        metrics = self.result['ordering_metrics']
        self.equal(metrics['complete_order_calls'],len(self.orders),'complete order calls')
        self.equal(metrics['complete_order_keys'],sum(e['complete_count'] for e in self.orders),'complete order key count')
        # Resynchronizations count the root, every order, placement and justified
        # exclusion; this cumulative work is retained despite semantic rollback.
        self.equal(self.result['lifecycle_metrics']['resynchronizations'],
            1+len(self.orders)+self.attempts+len(self.exclusions),'all empty-controller resynchronizations')
        for k in ('whole_scans','members_checked','mark_checks','status_updates','whole_retirements','ordering_calls','root_rejections'):
            self.equal(self.result['lifecycle_metrics'][k],0,'no active cluster work '+k)
        fixed=self.result['fixed_forward_metrics']
        if self.result['mode']=='base': self.equal(fixed,None,'no base fixed ranker')
        else:
            branches=[e for e in self.orders if e['decision'][0]=='branch']
            self.equal(fixed['calls'],len(branches),'fixed branch order calls')
            self.equal(fixed['complete_keys_ranked'],sum(e['complete_count'] for e in branches),'fixed every key ranked')
        for k in ('active_cluster_descriptors','authored_words_used_as_hints','native_queries'):
            self.equal(self.result[k],0,'zero authority field '+k)
        self.equal(self.result['validated_source_body_count'],171,'complete finite source family census')
        self.equal(self.result['body_authority_epoch'],self.tx.body_epoch,'independently reconstructed 171-body authority')
        self.need(len(self.events)<self.budget['event_ceiling'],'actual tapes are not trace cutoffs')
        return dict(status=status, events=len(self.events),nodes=self.next_node,attempts=self.attempts,
            forced=self.forced,branches=self.branches,proved_child_exclusions=self.exclusions,
            complete_orders=self.orders,distinct_graph_states=len(self.tx.censuses),
            full_decorated_step_identities=self.step_identities,
            graph_censuses=self.tx.censuses,
            complete_base_binding_checks=sum(c['complete_base_candidates'] for c in self.tx.censuses),
            complete_legal_binding_checks=sum(c['complete_legal_candidates'] for c in self.tx.censuses),
            altered_first_choices=sum(e['changed_first'] for e in self.orders),
            altered_permutations=sum(e['changed_permutation'] for e in self.orders),
            every_event_expected_sha256=self.expected_hashes,
            point_certificates=0,decoded_certificates=0,root_restored=True)


def mutations(tape, digest, need):
    """Alter actual event payloads against independently reconstructed events.

    The expected hashes were produced by the independent transaction/ordering
    verifier, not copied as an acceptance oracle from the producer trace.
    """
    receipts=[]
    def reject(label,index,change):
        altered=copy.deepcopy(tape.events[index]);change(altered)
        need(digest(altered)!=tape.expected_hashes[index], 'mutation changed independently expected event')
        receipts.append(dict(label=label,event=index,rejected=True,
            independent_expected_sha256=tape.expected_hashes[index],mutant_sha256=digest(altered)))
    index=lambda kind:next(i for i,e in enumerate(tape.events) if e['kind']==kind)
    i=index('global_decision');reject('false_global_domain_count',i,lambda e:e['decision'].__setitem__(2,e['decision'][2]+1))
    reject('bypass_earliest_generation',i,lambda e:e['decision'].__setitem__(1,22))
    reject('assigned_exterior_replaced_by_absence',i,lambda e:e['state']['projection']['graph']['marks'].pop(0))
    reject('altered_full_factor_semantic_hash',i,lambda e:e['state'].__setitem__('full_semantic_sha256','0'*64))
    reject('false_complete_point_degree',i,lambda e:e['state']['projection']['graph']['domains'][3].__setitem__('count',1))
    reject('boolean_generation',i,lambda e:e['state']['projection']['graph']['roots'].__setitem__(3,False))
    j=index('complete_chosen_domain_order')
    reject('incomplete_candidate_stream',j,lambda e:e.__setitem__('base_keys_sha256','0'*64))
    reject('altered_fixed_permutation',j,lambda e:e.__setitem__('ordered_keys_sha256','0'*64))
    reject('wrong_first_valid_recipe',j,lambda e:e['selected_key'].__setitem__(0,195))
    reject('boolean_recipe_key',j,lambda e:e['selected_key'].__setitem__(0,True))
    k=index('primitive_step');reject('unrecorded_extra_occupancy',k,lambda e:e['state']['projection']['graph']['totals'].__setitem__(4,1))
    def remove_zero(e):
        marks=e['state']['projection']['graph']['marks']
        marks.pop(next(j for j,v in enumerate(marks) if v[2]==0))
    reject('assigned_formula_zero_replaced_by_absence',k,remove_zero)
    reject('wrong_member_identity',k,lambda e:e['key'].__setitem__(0,195))
    reject('hidden_mark_conflict',k,lambda e:e['state']['projection']['graph']['marks'][-1].__setitem__(2,0))
    reject('stale_body_authority',k,lambda e:e['state']['projection'].__setitem__('authority_epoch','0'*64))
    reject('nonempty_target_word_hint',k,lambda e:e['state']['projection'].__setitem__('descriptor_ids',['authored-target']))
    r=index('paired_rollback');reject('incorrect_checkpoint_revision',r,lambda e:e['checkpoint'].__setitem__(2,e['checkpoint'][2]+1))
    reject('inexact_mark_reference_rollback',r,lambda e:e['state']['projection']['graph']['marks'][0].__setitem__(3,2))
    n=index('node_enter');reject('wrong_parent_node',n,lambda e:e.__setitem__('parent_node',999))
    x=index('before_exhausted_child_exclusion');reject('unknown_child_claimed_exhausted',x,lambda e:e.__setitem__('child_status','unknown_search_budget'))
    reject('unrelated_child_as_exhaustion_authority',x,lambda e:e.__setitem__('child_node',999))
    y=index('parent_local_exhausted_child_exclusion');reject('altered_ordered_exclusion_key',y,lambda e:e['key'].__setitem__(1,22))
    z=index('budget_unknown_no_exclusion');reject('unknown_changed_to_exhaustion_event',z,lambda e:e.__setitem__('kind','proved_global_dead'))
    reject('UNKNOWN_prunes_parent',z,lambda e:e['state']['projection']['graph']['excluded'][3].append([144,3,[]]))
    return receipts


def logical_mutations(state,checker,symbolic,formulas,context,digest,need):
    """Consistent point mutants cannot bypass independent inference checking."""
    from full_point_oracle_v1 import points
    receipts=[]
    for rule in ('instantiate','eq_subst'):
        recipe=next(r for r in state.recipes if r['witness']['rule']==rule and r['output']!=54)
        altered=copy.deepcopy(recipe['witness']);altered['formula']=copy.deepcopy(formulas[54])
        altered_recipe=copy.deepcopy(recipe);altered_recipe['witness']=altered;altered_recipe['output']=54
        t,m=points(altered_recipe,23,(),24)
        need(state.totals[23]==0 and state.compatible(m),'mark-consistent invalid-inference control')
        rejected=False
        try:checker.command(altered,[],context['ordered_local_premises'])
        except symbolic.Rejected:rejected=True
        need(rejected,'point-consistent invalid symbolic inference must fail')
        receipts.append(dict(label='consistent_points_invalid_'+rule,rejected=True,t=t,m=m,
            changed_command_sha256=digest(altered),point_consistency=True))
    recipe=next(r for r in state.recipes if r['witness']['rule']=='mp')
    altered=copy.deepcopy(recipe['witness']);altered.update(antecedent=1,implication=0)
    rejected=False
    try:checker.command(altered,recipe['premises'],context['ordered_local_premises'])
    except symbolic.Rejected:rejected=True
    need(rejected,'ordered logical MP ports cannot be reversed')
    receipts.append(dict(label='reversed_ordered_MP_ports',rejected=True,changed_command_sha256=digest(altered)))
    return receipts


def run(plan):
    symbolic, expansion = libraries(plan)
    from full_point_oracle_v1 import canonical,digest,pin,read,need,validate_model
    from full_family_registry_v1 import VERSION,equal,graph_binding,family_bodies,receptor_ports,key_data
    from geometry_trace_point_v1 import PointState,TransactionState
    checked=verify_pins(plan,pin,need);roles={e['role']:ROOT/e['path'] for e in plan['inputs']}
    source_plan=read(roles['producer_plan']);body_plan=read(roles['accepted_body_plan'])
    outcome=read(roles['producer_outcome']);root_terminal=read(roles['root_terminal'])
    lifetime=read(roles['producer_lifetime']);supervision=read(roles['producer_supervision'])
    need(root_terminal['exec_terminal_return_code']==0 and root_terminal['worker_and_supervisor_reaped'] is True,
         'root authoritative actual terminal')
    need(lifetime['status']=='passed_automatic_primitive_geometry_full_lifetime' and
         lifetime['process_return_code']==0 and lifetime['supervisor_wait_reaped'] is True and
         lifetime['worker_terminal_reaped_confirmed'] is True,'actual producer full lifetime gate')
    need(supervision['exit_code']==0 and supervision['owned_child_terminal_wait_reaped'] is True,
         'actual producer child terminal')
    full_pin=lambda role:dict(path=str(roles[role].relative_to(ROOT)),**pin(roles[role]))
    for record in (lifetime,supervision,outcome):
        equal(record['plan'],full_pin('producer_plan'),'producer exact plan')
    equal(lifetime['supervision'],full_pin('producer_supervision'),'producer full nested supervision binding')
    equal(supervision['outcome'],full_pin('producer_outcome'),'supervision exact completed outcome')
    for name,role in (('lifetime','producer_lifetime'),('supervision','producer_supervision'),('outcome','producer_outcome')):
        equal(root_terminal[name],full_pin(role),'root authoritative actual '+name)
    equal(supervision['root_activation'],full_pin('producer_activation'),'supervision exact root activation')
    equal(outcome['root_activation'],full_pin('producer_activation'),'outcome exact root activation')
    need(len(body_plan['inputs'])==len({e['path'] for e in body_plan['inputs']})==56 and
         source_plan['inputs'][:56]==body_plan['inputs'],'exact full body relation with unique source pins')
    data=read(roles['primitive_model']);projected=read(roles['family_projection'])
    projected.pop('example',None)  # decoded, discarded, never hint/acceptance input
    model,inventory,checker,seeds,rule_census=validate_model(data,symbolic)
    fixed=sorted(model['boundary']['fixed_exterior_m']+model['boundary']['fixed_target_m'])
    prior=read(roles['prior_point_plan'])
    source_bindings={e['role']:{k:e[k] for k in ('path','sha256','bytes')} for e in prior['inputs']}
    roots=[v[2] for v in model['boundary']['root_generations']]
    epoch=digest(dict(height=24,context=model['context'],registry=digest(data['formula_codes']),
        authority=data['authority']['epoch'],recipes=[r['id'] for r in inventory],fixed_marks=fixed,
        roots=roots,seed_keys=[key_data(k) for k in seeds],marking_version='injective-formula-ordered-mp-offset-v1',
        fixture=False,source_bindings=source_bindings))
    equal(epoch,source_plan['model_epoch'],'unchanged exact original point model')
    state=PointState(24,inventory,fixed,roots,epoch)
    for k in seeds:state.apply(k,generation=0)
    logical_mutants=logical_mutations(state,checker,symbolic,data['formula_codes'],model['context'],digest,need)
    binding=graph_binding(state,model['context'],data['authority'],data['formula_codes'],source_bindings,seeds,fixed)
    bodies,census,logical_receipts=family_bodies(read(roles['transport_certificate']),read(roles['source_schemas']),
        projected,data,expansion)
    for b in bodies:b['ordered_receptor_ports']=receptor_ports(b,inventory)
    sources=[{k:e[k] for k in ('path','sha256','bytes')} for e in body_plan['inputs']]
    body_epoch=digest(dict(graph=binding,sources=sources,bodies=[[b['name'],digest(b)] for b in bodies],version=VERSION))
    results=[];mutants=[]
    need(len(source_plan['observations'])==len(outcome['observations'])==2,
         'exact two-lane complete observation inventory')
    for spec,record in zip(source_plan['observations'],outcome['observations']):
        need(spec['id']==record['id'],'predeclared exact observation order')
        result_path=ROOT/record['result']['path']
        equal(pin(result_path),{k:record['result'][k] for k in ('sha256','bytes')},'exact returned tape')
        result=read(result_path)
        equal(result['limits'],dict(attempts=spec['attempts'],seconds=spec['seconds'],events=spec['event_ceiling']),
              'original observation bounds')
        equal(result['mode'],spec['mode'],'original mode')
        equal(result['observation_id'],spec['id'],'original observation identity')
        equal(record['status'],result['status'],'outcome actual status')
        equal(record['attempts'],result['attempts'],'outcome actual attempt count')
        equal(record['events'],len(result['events']),'outcome actual event count')
        equal(record['decoded_certificate'],False,'outcome zero decoded certificate flag')
        tx=TransactionState(copy.deepcopy(state),body_epoch)
        tape=Tape(result,tx,data['formula_codes'],spec,model,data['authority']['epoch'],equal,need,digest)
        checked_result=tape.run();checked_result['id']=spec['id'];results.append(checked_result)
        mutants.extend([dict(observation=spec['id'],**r) for r in mutations(tape,digest,need)])
        del result,tape,tx
    need(len(results)==2,'both actual returned observations audited')
    verify_pins(plan,pin,need)
    return dict(status='passed_independent_complete_geometry_trace_audit_zero_certificates',
        exact_model_epoch=epoch,complete_sources=171,source_expansion_census=census,
        independent_logical_source_receipts=logical_receipts,independent_recipe_rule_census=rule_census,
        recipes=229,formulas=217,rows=24,body_authority_epoch=body_epoch,
        observations=results,actual_event_mutations=mutants,total_events=sum(r['events'] for r in results),
        point_consistent_logical_mutations=logical_mutants,
        total_nodes=sum(r['nodes'] for r in results),actual_attempts=sum(r['attempts'] for r in results),
        point_certificates=0,decoded_certificates=0,whole_target_logical_checks=0,native_queries=0,
        searches_run_by_auditor=0,training=0,unique_exact_input_paths=checked,
        read_scope='Compact projection example is decoded then discarded; no authored target witness is a hint or acceptance authority.',
        limitations=['Exact two complete returned UNKNOWN tapes only; this gate fails closed on positive certificates or truncated tapes.',
            'Each excluded child has independently reconstructed finite exhaustion. The whole UNKNOWN observation does not establish theorem nonprovability or full-boundary impossibility.',
            'Complete candidate bindings are enumerated from independent literal output/ordered-port point constraints; immutable graph censuses may be cached across identical graph states, never from producer counts.',
            'Saved cumulative timers are provenance only; checked 20-second deadlines allow operation overshoot and differ from whole-owner gates.',
            'Symbolic source/recipe validity is checked in the guarded incidence fragment; no shared native/Wang checker/compiler activation or proof-search superiority claim.'])


def main():
    began=time.perf_counter();plan=json.loads((HERE/'audit-plan-v1.json').read_text())
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('independent trace child gate')))
    signal.alarm(plan['child_seconds'])
    result=run(plan)
    from full_point_oracle_v1 import pin
    result['plan_sha256']=pin(HERE/'audit-plan-v1.json')['sha256']
    result['child_seconds_before_result_serialization']=time.perf_counter()-began
    result['result_serialization_clock_scope']='Final result serialization/reap charged by outer owner; source authoring unmeasured.'
    out=ROOT/plan['result_path']
    with out.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=result['status'],plan_sha256=result['plan_sha256'],events=result['total_events'])),flush=True)


if __name__=='__main__':main()
