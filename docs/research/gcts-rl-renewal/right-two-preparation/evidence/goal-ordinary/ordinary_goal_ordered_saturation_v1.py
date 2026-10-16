"""Unexecuted ordinary matched-information search, never a point solver.

The authenticated shared goal module supplies the same primitive inverse agenda
and family instance enumerator used by the point advisory arm. These only reorder
complete forward sweeps. Facts always require every ordered primitive premise.
No provisional family, pending port, or search return is mathematical authority.
The caller authenticates whole original preparation/library/Source and supplies
its unchanged inherited native20/500MiB tick. A separate unchanged1717 checker
must accept any returned original-context, closed-target primitive word.
"""
import copy
import json

VERSION = 'ordinary-goal-ordered-full-sweep-saturation-Source-v1'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
ARITY = {'axiom': 0, 'assumption': 0, 'instantiate': 0,
         'eq_subst': 0, 'mp': 2, 'generalize': 1}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def literal(value, bound):
    need(type(value) is int and 0 <= value < bound, 'literal bounded index, never Boolean')
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def catalogue_rows(catalogue, declaration, binding, tick):
    """Full caller-bound inventory; no reconstruction, subset or new epochs."""
    tick()
    need(type(catalogue) is dict and catalogue['declaration'] == declaration
         and declaration['height'] == catalogue['height'] == 24
         and declaration['ordered_Gamma'] == [], 'entire fresh empty-Gamma24 declaration')
    need(type(binding) is dict and set(binding) == {'declaration_sha256', 'model_epoch',
         'primitive_authority_epoch', 'formula_registry_sha256'}, 'fresh caller-bound four epochs')
    formulas, records = catalogue['formula_codes'], catalogue['recipes']
    need(type(formulas) is list and formulas and type(records) is list and records,
         'whole original registry and complete recipe array')
    code = {canonical(f): i for i, f in enumerate(formulas)}
    need(len(code) == len(formulas), 'injective full formula registry')
    rows = []
    for i, record in enumerate(records):
        tick()
        witness, premises = record['primitive_witness'], record['ordered_premise_formulas']
        need(type(witness) is dict and witness.get('rule') in ARITY
             and type(premises) is list and len(premises) == ARITY[witness['rule']]
             and not any(k in witness for k in ('antecedent', 'implication', 'source')),
             'original zero/unary/binary primitive witness and ordered recipe ports')
        need(type(record['id']) is str and type(record['identity_preimage']) is dict,
             'original recipe ID/preimage retained; shared index validates its full epoch')
        output = code[canonical(witness['formula'])]
        inputs = tuple(code[canonical(p)] for p in premises)
        rows.append((i, record['id'], witness, output, inputs))
    tick()
    return tuple(rows), code[canonical(declaration['target'])]


def validate_instance(instance, *, catalogue, binding, rows, goal_code, tick):
    """A licensed prospective body may order recipes; it grants no fact."""
    tick()
    need(type(instance) is dict and instance.get('schema') == 'goal-attached-logical-instance-v1'
         and instance.get('recipient_binding') == binding
         and instance.get('status') == 'PENDING_INPUTS'
         and instance.get('logical_accepted') is False
         and type(instance.get('family_id')) is str
         and type(instance.get('output_code')) is int and instance['output_code'] == goal_code,
         'exact current pending-only logical family instance')
    inputs, members = instance['ordered_input_codes'], instance['members']
    need(type(inputs) is list and len(inputs) == 2 and type(members) is list and len(members) == 3,
         'actual two-receptor three-primitive family interface')
    for code in inputs:
        literal(code, len(catalogue['formula_codes']))
    obligations = instance['input_obligations']
    need(type(obligations) is list and len(obligations) == len(inputs), 'every ordered pending port')
    for p, (code, obligation) in enumerate(zip(inputs, obligations)):
        tick()
        need(obligation['port'] == p and type(obligation['port']) is int
             and obligation['formula_code'] == code and type(obligation['formula_code']) is int
             and obligation['formula'] == catalogue['formula_codes'][code]
             and obligation['status'] == 'PENDING' and obligation['fact_accepted'] is False,
             'unfilled input never masquerades as a known proof')
    outputs, indices = [], []
    for j, member in enumerate(members):
        tick()
        rid = literal(member['recipe_index'], len(rows)); row = rows[rid]
        need(member['recipe_id'] == row[1] and member['primitive_witness'] == row[2],
             'exact original licensed primitive ID/witness')
        ports = member['ordered_ports']
        need(type(ports) is list and len(ports) == len(row[4]), 'complete ordered member arity')
        required = []
        for port in ports:
            need(type(port) is list and len(port) == 2 and port[0] in ('input', 'member'),
                 'literal ordered external or strict-prior member port')
            source = inputs[literal(port[1], len(inputs))] if port[0] == 'input' else outputs[literal(port[1], j)]
            required.append(source)
        need(tuple(required) == row[4], 'no swapped, circular or future member source')
        outputs.append(row[3]); indices.append(rid)
    need(outputs[-1] == goal_code, 'family output is the actual demanded formula')
    tick()
    return tuple(indices), tuple(inputs)


def expand_first_ready(known, rows, target, tick):
    """Same first-justification discipline; no shorter-proof rescue or lemma."""
    needed, pending = set(), [target]
    while pending:
        tick(); code = pending.pop()
        if code in needed:
            continue
        need(code in known, 'complete retained predecessor fact')
        needed.add(code)
        if len(needed) > 24:
            raise TimeoutError('selected first-ready ancestry exceeds24; UNKNOWN')
        rid, premises, ordinal = known[code]
        need(rows[rid][3] == code and rows[rid][4] == premises, 'exact retained original primitive')
        for p in premises:
            need(p in known and known[p][2] < ordinal, 'strict earlier fact, never pending or circular')
        pending.extend(premises)
    order = sorted(needed, key=lambda c: known[c][2]); local = {c:i for i,c in enumerate(order)}
    commands, recipes, ordinals = [], [], []
    for i, code in enumerate(order):
        tick(); rid, premises, ordinal = known[code]
        command = copy.deepcopy(rows[rid][2]); refs = [local[p] for p in premises]
        need(all(type(r) is int and 0 <= r < i for r in refs), 'strict prior ordered/repeated word ports')
        if command['rule'] == 'mp':
            command.update(antecedent=refs[0], implication=refs[1])
        elif command['rule'] == 'generalize':
            command.update(source=refs[0])
        else:
            need(not refs, 'zero-port primitive')
        commands.append(command); recipes.append(rid); ordinals.append(ordinal)
    need(order and order[-1] == target and 1 <= len(commands) <= 24, 'entire original target ancestry')
    tick()
    return commands, dict(recipe_indices=recipes, formula_codes=order, discovery_ordinals=ordinals)


def run_goal_ordered_saturation(*, goal_module, catalogue, declaration, binding,
        families, use_families, coordinator_invocation_id, authority_sha256,
        joint_began_ns, joint_deadline_ns, tick):
    """Reorder full forward sweeps only; all native/Source/output gates outside.

    Both arms use the same complete primitive_goal_order and goal_codes API.
    Family matching is enabled in one arm; each legal expansion adds preference,
    never a synthetic primitive or known formula. No target-positive word input.
    Timeout/invalid proposal remains UNKNOWN. No negative theorem is returned.
    """
    tick()
    need(type(use_families) is bool and type(families) is list
         and type(joint_began_ns) is int and type(joint_deadline_ns) is int
         and 0 <= joint_began_ns < joint_deadline_ns < (1 << 63)
         and joint_deadline_ns-joint_began_ns == 20000000000,
         'explicit arm and original inherited native20; no clock reset')
    need(type(coordinator_invocation_id) is str and 1 <= len(coordinator_invocation_id) <= 128
         and type(authority_sha256) is str and len(authority_sha256) == 64,
         'opaque actual coordinator invocation and authority hash')
    counters = dict(sweeps_started=0, sweeps_completed=0, recipe_tests=0, fallback_recipe_tests=0,
        new_formulas=0, goal_formula_visits=0, family_proposals=0, proposals_with_pending_inputs=0,
        ordered_pending_ports=0, ordered_ports_discharged=0, proposals_all_inputs_discharged=0,
        family_member_recipe_preferences=0)
    known, candidate, error = {}, None, None
    status, fixed_point = 'UNKNOWN', False
    try:
        # The shared index independently retains and binds the entire raw
        # original inventory/epochs. Its original definitions are not copied.
        index = goal_module.GoalFamilyIndex(catalogue=catalogue, binding=binding, tick=tick)
        rows, target = catalogue_rows(catalogue, declaration, binding, tick)
        baseline = goal_module.primitive_goal_order(index=index, goal_code=target, tick=tick)
        need(type(baseline) is list and len(baseline) == len(rows)
             and all(type(i) is int for i in baseline) and sorted(baseline) == list(range(len(rows))),
             'complete permutation retains every canonical primitive fallback')
        goals = index.goal_codes(goal_code=target, tick=tick)
        need(type(goals) is list and goals and goals[0] == target
             and all(type(c) is int and 0 <= c < len(catalogue['formula_codes']) for c in goals)
             and len(set(goals)) == len(goals), 'same complete generic inverse goal encounter order')
        preferred, seen = [], set()
        obligations = []
        def prefer(rid):
            if rid not in seen:
                seen.add(rid); preferred.append(rid)
        counters['goal_formula_visits'] = len(goals)
        if use_families:
            for goal in goals:
                tick()
                for family in families:
                    tick()
                    for proposal in index.iter_instances(goal_formula=catalogue['formula_codes'][goal], family=family, tick=tick):
                        tick()
                        members, inputs = validate_instance(proposal, catalogue=catalogue,
                            binding=binding, rows=rows, goal_code=goal, tick=tick)
                        counters['family_proposals'] += 1
                        counters['proposals_with_pending_inputs'] += 1
                        counters['ordered_pending_ports'] += len(inputs)
                        # At this pre-search stage every original fact is
                        # unknown. Keep both ports even if formula codes alias.
                        obligations.append([inputs, [False]*len(inputs), False])
                        for rid in members:
                            prefer(rid)
                            counters['family_member_recipe_preferences'] += 1
                        # First lawful instance in the shared canonical stream
                        # is advice only, never a completeness/degree claim.
                        break
        seen_family_members = frozenset(seen)
        for rid in baseline:
            prefer(rid)
        need(len(preferred) == len(rows) and sorted(preferred) == list(range(len(rows))),
             'advice orders but never removes an original recipe')
        while True:
            tick(); counters['sweeps_started'] += 1; changed = False
            for rid in preferred:
                tick(); counters['recipe_tests'] += 1
                if rid not in seen_family_members:
                    counters['fallback_recipe_tests'] += 1
                _, identifier, witness, output, premises = rows[rid]
                if output in known or not all(p in known for p in premises):
                    continue
                known[output] = (rid, premises, len(known))
                counters['new_formulas'] += 1; changed = True
            tick(); counters['sweeps_completed'] += 1
            for record in obligations:
                tick(); inputs, discharged, complete = record
                for port, code in enumerate(inputs):
                    if not discharged[port] and code in known:
                        discharged[port] = True; counters['ordered_ports_discharged'] += 1
                if not complete and all(discharged):
                    record[2] = True; counters['proposals_all_inputs_discharged'] += 1
            if target in known:
                commands, origin = expand_first_ready(known, rows, target, tick)
                origin.update(kind='ordinary_goal_ordered_full_sweep_saturation',
                    completed_sweeps=counters['sweeps_completed'], use_families=use_families)
                candidate = dict(schema='Q-untrusted-ordinary-goal-word-v1',
                    coordinator_invocation_id=coordinator_invocation_id,
                    authority_sha256=authority_sha256, binding=copy.deepcopy(binding),
                    submission_index=0, commands=commands, origin=origin,
                    termination=dict(producer_status='CANDIDATE_NOT_VERIFIED',
                        proof_accepted=False, full24_accepted=False, trajectory_accepted=False))
                need(len(canonical(candidate).encode('utf8')) <= 2*1048576,
                     'whole at-most2MiB ordinary candidate; no prefix')
                tick(); status = 'CANDIDATE_NOT_VERIFIED'; break
            if not changed:
                fixed_point = True; status = 'UNREACHED_FINITE_FIXED_POINT_UNTRUSTED'; break
        tick()
    except Exception as failure:
        status, candidate = 'UNKNOWN', None
        error = dict(type=type(failure).__name__, message=str(failure)[:1024])
    result = dict(schema='ordinary-goal-ordered-full-sweep-return-v1',version=VERSION,
        producer_status=status,candidate=candidate,error=error,counters=counters,
        known_formula_count_claimed=len(known),fixed_point_claimed=fixed_point,
        first_justification_only=True,bounded_word_complete=False,full_search_trace_recorded=False,
        binding=copy.deepcopy(binding),CLOCK_DOMAIN=CLOCK_DOMAIN,
        joint_began_ns=joint_began_ns,joint_deadline_ns=joint_deadline_ns,
        proof_accepted=False,point_state_accepted=False,full24_accepted=False,
        trajectory_accepted=False,native_accepted=False,ROOT_resource_accepted=False,
        library_admitted=False,RL_used=False)
    tick()
    return result
