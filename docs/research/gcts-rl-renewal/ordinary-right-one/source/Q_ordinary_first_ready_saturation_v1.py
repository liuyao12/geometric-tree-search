"""UNEXECUTED ordinary first-ready finite-Q hypergraph saturation.

This is a separate bounded-word heuristic, not the chronological enumerator.
Only the first justification for each formula is retained. All outputs remain
untrusted until a separate original-context independent word check. No project
imports, point scheduler, supplied word, library, rank or RL.
"""
import copy
import hashlib
import itertools
import json
import resource
import sys
import time

VERSION = 'Q-untrusted-ordinary-first-ready-saturation-Source-v1'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CURRENT = {
    'declaration_sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc',
    'model_epoch': '3a8854e0e0137d125dfa8af8870be04e4242ec2e7036b6bb8977cd33ad1454f9',
    'primitive_authority_epoch': '4ac41a90b9655036e2e7ed6cd7d9a971b9097d6b2c7d0f70e8408b8d93a54039',
    'formula_registry_sha256': '4a12ada631861b1637b7d5e17e76c45b9a942816c412f5a6f0fc48c1698eb7fe'}
DECLARATION_VALUE_SHA256 = 'f6ca72af011a9343f4661b5092d54565f668a978fd020734072267b76f89b7a3'
MARKING_VERSION = 'injective-formula-ordered-primitive-offset-Q-v1'
PROFILE = 'arithmetic-empty-Gamma-unary-generalize-finite-catalog-v1'
RULE_FIELDS = {'axiom': {'name'}, 'assumption': {'index'},
    'instantiate': {'universal', 'term'},
    'eq_subst': {'variable', 'template', 'left', 'right'},
    'mp': set(), 'generalize': {'variable'}}
ARITIES = {'axiom': 0, 'assumption': 0, 'instantiate': 0,
           'eq_subst': 0, 'mp': 2, 'generalize': 1}
LIMITS = {'joint_seconds': 20, 'failure_seconds': 55, 'owned_seconds': 60,
    'worker_bytes': 524288000, 'owned_bytes': 536870912,
    'caller_seconds': 90, 'external_allowance_seconds': 1,
    'maximum_word_commands': 24, 'maximum_submissions': 1}


class Unfinished(TimeoutError):
    """No proof, negative theorem, bounded-exhaustion or resource authority."""


def need(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


class Budget:
    """Untrusted local accounting; native enclosing caller remains authority.

    On the pinned Darwin runtime ru_maxrss is bytes. There is no perf-counter
    epoch projection because this module calls no original float-deadline API.
    """
    def __init__(self, began_ns, deadline_ns):
        need(sys.platform == 'darwin', 'pinned Darwin RSS byte semantics only')
        need(type(began_ns) is int and type(deadline_ns) is int
             and 0 <= began_ns < deadline_ns < (1 << 63)
             and deadline_ns - began_ns == 20000000000,
             'inherited exact global native twenty seconds; no reset')
        self.began_ns, self.deadline_ns = began_ns, deadline_ns
        self.clock, self.clock_id = time.clock_gettime_ns, time.CLOCK_MONOTONIC
        self.usage = resource.getrusage
        need(type(self.clock_id) is int, 'literal native clock ID')
        self.check()

    def check(self, *, cleanup=False):
        if time.clock_gettime_ns is not self.clock or time.CLOCK_MONOTONIC is not self.clock_id:
            raise ValueError('original global clock endpoint/ID changed')
        if resource.getrusage is not self.usage:
            raise ValueError('original process memory endpoint changed')
        now = self.clock(self.clock_id)
        if now < self.began_ns or now - self.began_ns >= 55000000000:
            raise Unfinished('foreign native epoch or failure reserve55 exceeded')
        if self.usage(resource.RUSAGE_SELF).ru_maxrss >= 524288000:
            raise Unfinished('producer memory reserve500MiB exceeded')
        if not cleanup and now >= self.deadline_ns:
            raise Unfinished('original shared20 unfinished')


def digest(value, budget, *, cleanup=False):
    """Whole canonical traversal with bounded encoder fragments; no prefix SHA."""
    budget.check(cleanup=cleanup)
    h, since_check = hashlib.sha256(), 0
    encoder = json.JSONEncoder(sort_keys=True, separators=(',', ':'),
                               ensure_ascii=False, allow_nan=False)
    for fragment in encoder.iterencode(value):
        raw = fragment.encode('utf8')
        h.update(raw)
        since_check += len(raw)
        if since_check >= 16384:
            budget.check(cleanup=cleanup)
            since_check = 0
    budget.check(cleanup=cleanup)
    return h.hexdigest()


def inventory(catalogue, declaration, original_source_bindings, binding, budget):
    """Structural/whole-digest binding only; not a semantic admission/checker.

    Retains the complete original ordered registry and every recipe. It repeats
    the original model identity preimage without constructing/executing a graph.
    """
    need(type(binding) is dict and binding == CURRENT, 'original four digest epochs')
    need(type(declaration) is dict and digest(declaration, budget) == DECLARATION_VALUE_SHA256,
         'entire exact original declaration, not a new target')
    need(declaration['ordered_Gamma'] == [] and type(declaration['height']) is int
         and declaration['height'] == 24, 'empty indexed original context and twenty-four command bound')
    need(type(catalogue) is dict and catalogue['schema'] == PROFILE
         and catalogue['declaration'] == declaration and catalogue['height'] == 24,
         'original full prepared finite catalogue')
    context, authority = catalogue['context'], catalogue['authority']
    need(context == {'theory': declaration['theory'], 'ordered_local_premises': []},
         'entire original theory/context; no additional facts')
    need(type(original_source_bindings) is dict and authority['source_bindings'] == original_source_bindings
         and set(original_source_bindings) == {'kernel', 'catalogue', 'point_graph', 'controls', 'payload', 'worker', 'master'},
         'unchanged original seven-source provenance, not executed modules')
    need(authority['activated'] is False and authority['native_accepted'] is False
         and authority['epoch'] == CURRENT['primitive_authority_epoch']
         and digest({k: v for k, v in authority.items() if k != 'epoch'}, budget) == authority['epoch']
         and authority['recipient_theory_sha256'] == digest(declaration['theory'], budget),
         'original inactive primitive authority and whole preimage')
    formulas = catalogue['formula_codes']
    need(type(formulas) is list and formulas and digest(formulas, budget) == CURRENT['formula_registry_sha256']
         and catalogue['formula_registry_sha256'] == CURRENT['formula_registry_sha256'],
         'entire original formula registry, no subset')
    codes = {}
    for code, formula in enumerate(formulas):
        budget.check()
        key = canonical(formula)
        need(key not in codes, 'injective literal formula registry')
        codes[key] = code
    target_code = codes[canonical(declaration['target'])]
    context_id = digest(context, budget)
    rows, identifiers = [], set()
    need(type(catalogue['recipes']) is list and catalogue['recipes'], 'whole nonempty primitive inventory')
    for rid, record in enumerate(catalogue['recipes']):
        budget.check()
        need(type(record) is dict and set(record) ==
             {'primitive_witness', 'ordered_premise_formulas', 'id', 'identity_preimage'},
             'exact original raw recipe fields')
        witness, premises = record['primitive_witness'], record['ordered_premise_formulas']
        need(type(witness) is dict and witness.get('rule') in ARITIES, 'all and only six primitive cases')
        rule = witness['rule']
        need(set(witness) == {'rule', 'formula'} | RULE_FIELDS[rule]
             and type(premises) is list and len(premises) == ARITIES[rule],
             'whole zero/unary/binary ordered interface; no physical references in witness')
        if rule == 'assumption':
            index = witness['index']
            need(type(index) is int and 0 <= index < len(declaration['ordered_Gamma'])
                 and declaration['ordered_Gamma'][index] == witness['formula'],
                 'exact original occurrence only; empty Gamma supplies none')
        elif rule == 'mp':
            need(premises[1] == ['imp', premises[0], witness['formula']], 'ordered MP ports')
        elif rule == 'generalize':
            need(type(witness['variable']) is str and witness['variable'] in declaration['parameters']
                 and witness['formula'] == ['all', witness['variable'], premises[0]],
                 'genuine unary generalization interface; no binary encoding')
        preimage = {'recipe': {'primitive_witness': witness, 'ordered_premise_formulas': premises},
            'primitive_authority_epoch': authority['epoch'],
            'recipient_theory_sha256': authority['recipient_theory_sha256'],
            'marking_version': MARKING_VERSION,
            'formula_registry_sha256': CURRENT['formula_registry_sha256'], 'local_context_id': context_id}
        need(record['identity_preimage'] == preimage
             and record['id'] == 'primitive-recipe-' + digest(preimage, budget)
             and record['id'] not in identifiers, 'complete original unique recipe preimage')
        identifiers.add(record['id'])
        rows.append((rid, record['id'], canonical(witness),
                     codes[canonical(witness['formula'])], tuple(codes[canonical(p)] for p in premises)))
    boundary = catalogue['boundary']
    need(type(boundary) is dict and boundary['required'] == [[0, r] for r in range(24)]
         and boundary['seed_keys'] == [] and len(boundary['roots']) == 24
         and all(type(x) is int and x >= 0 for x in boundary['roots']),
         'original full row/boundary provenance; no point scheduling is executed')
    marks = {}
    for item in boundary['fixed_marks']:
        need(type(item) is list and len(item) == 3 and all(type(x) is int for x in item),
             'literal fixed marking record')
        x, y, value = item
        need((x, y) not in marks or marks[x, y] == value, 'consistent original fixed marks')
        marks[x, y] = value
    model = {'height': 24, 'context': context, 'registry': CURRENT['formula_registry_sha256'],
        'authority': authority['epoch'], 'recipes': [r[1] for r in rows],
        'fixed_marks': [[x, y, value] for (x, y), value in sorted(marks.items())],
        'roots': boundary['roots'], 'seed_keys': [], 'marking_version': MARKING_VERSION,
        'fixture': False, 'source_bindings': original_source_bindings}
    need(digest(model, budget) == CURRENT['model_epoch'], 'whole unchanged model epoch, raw provenance only')
    budget.check()
    return tuple(rows), target_code


def first_ready_word(known, recipes, target, budget):
    """Only the frozen first-justification DAG; no shorter-proof rescue.

    Reachability may use more than24 commands. That does not prove absence of a
    bounded word; it only makes this chosen first-justification heuristic UNKNOWN.
    """
    essential, pending = set(), [target]
    while pending:
        budget.check()
        code = pending.pop()
        if code in essential:
            continue
        need(code in known, 'whole retained predecessor justification')
        essential.add(code)
        if len(essential) > 24:
            raise Unfinished('chosen first-ready ancestry exceeds24; no bounded-completeness claim')
        rid, premises, ordinal = known[code]
        need(recipes[rid][3] == code and recipes[rid][4] == premises,
             'exact original ordered first justification')
        for predecessor in premises:
            need(predecessor in known and known[predecessor][2] < ordinal,
                 'strictly earlier discovery; no cyclic justification')
        pending.extend(premises)
    order = sorted(essential, key=lambda code: known[code][2])
    remap = {code: row for row, code in enumerate(order)}
    commands, indices, ordinals = [], [], []
    for row, code in enumerate(order):
        budget.check()
        rid, premises, ordinal = known[code]
        command = json.loads(recipes[rid][2])
        refs = [remap[p] for p in premises]
        need(all(type(ref) is int and 0 <= ref < row for ref in refs),
             'ordered repeated ports are actual strict-prior command references')
        if command['rule'] == 'mp':
            need(len(refs) == 2, 'all two ordered MP ports')
            command.update(antecedent=refs[0], implication=refs[1])
        elif command['rule'] == 'generalize':
            need(len(refs) == 1, 'genuine unary source')
            command.update(source=refs[0])
        else:
            need(not refs, 'zero-port original primitive')
        commands.append(command); indices.append(rid); ordinals.append(ordinal)
    need(order and order[-1] == target and 1 <= len(commands) <= 24,
         'complete target dependency word')
    return commands, {'kind': 'ordinary_first_ready_forward_saturation',
        'recipe_indices': indices, 'formula_codes': order,
        'discovery_ordinals': ordinals, 'known_formula_count': len(known)}


def run_first_ready_saturation(*, catalogue, declaration, original_source_bindings,
        binding, coordinator_invocation_id, authority_sha256, joint_began_ns, joint_deadline_ns):
    """Scan every original recipe each sweep, insert first ready output once.

    New facts are visible later in the same sweep. Stop at a complete sweep EOF
    once target is known or no fact changed. No target backcone/library/word is
    input. No alternate justification search or bounded-word completeness.
    """
    budget = Budget(joint_began_ns, joint_deadline_ns)
    need(type(coordinator_invocation_id) is str and 1 <= len(coordinator_invocation_id) <= 128
         and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:'
                 for c in coordinator_invocation_id), 'opaque original invocation')
    need(type(authority_sha256) is str and len(authority_sha256) == 64
         and all(c in '0123456789abcdef' for c in authority_sha256), 'fixed authority digest')
    recipes, target = inventory(catalogue, declaration, original_source_bindings, binding, budget)
    known = {}
    counters = dict(sweeps_started=0, sweeps_completed=0, recipe_tests=0, new_formulas=0)
    status, candidate, error, fixed_point = 'UNKNOWN', None, None, False
    try:
        while True:
            budget.check()
            counters['sweeps_started'] += 1
            changed = False
            for record in recipes:
                budget.check()
                counters['recipe_tests'] += 1
                rid, identifier, witness_text, output, premises = record
                if output in known or not all(code in known for code in premises):
                    continue
                # Premises are retained in original order, including repeats.
                # This record never overwrites an earlier justification.
                known[output] = (rid, premises, len(known))
                counters['new_formulas'] += 1
                changed = True
            budget.check()
            counters['sweeps_completed'] += 1
            if target in known:
                commands, origin = first_ready_word(known, recipes, target, budget)
                origin['completed_sweeps'] = counters['sweeps_completed']
                candidate = {'schema': 'Q-untrusted-ordinary-first-ready-word-v1',
                    'coordinator_invocation_id': coordinator_invocation_id,
                    'authority_sha256': authority_sha256, 'binding': copy.deepcopy(binding),
                    'submission_index': 0, 'commands': commands, 'origin': origin,
                    'termination': {'producer_status': 'CANDIDATE_NOT_VERIFIED',
                        'proof_accepted': False, 'full24_accepted': False,
                        'trajectory_accepted': False}}
                status = 'CANDIDATE_NOT_VERIFIED'
                break
            if not changed:
                # A full fixed point is only an untrusted finite reachability
                # observation. No producer negative theorem certificate.
                fixed_point = True
                status = 'UNREACHED_FINITE_FIXED_POINT_UNTRUSTED'
                break
        budget.check()
    except BaseException as failure:
        status, candidate = 'UNKNOWN', None
        error = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
    result = {'schema': 'Q-untrusted-ordinary-first-ready-return-v1', 'version': VERSION,
        'CLOCK_DOMAIN': CLOCK_DOMAIN, 'producer_status': status, 'candidate': candidate,
        'error': error, 'binding': copy.deepcopy(binding), 'limits': dict(LIMITS),
        'joint_began_ns': joint_began_ns, 'joint_deadline_ns': joint_deadline_ns,
        'counters': counters, 'known_formula_count_claimed': len(known),
        'fixed_point_claimed': fixed_point, 'first_justification_only': True,
        'bounded_word_complete': False, 'full_search_trace_recorded': False,
        'proof_accepted': False, 'selected_provenance_accepted': False,
        'point_state_accepted': False, 'full24_accepted': False,
        'trajectory_accepted': False, 'mathematical_authority': False,
        'ROOT_resource_accepted': False, 'native_accepted': False,
        'library_used': False, 'rank_used': False, 'RL_used': False}
    try:
        if candidate is not None:
            need(len(canonical(candidate).encode('utf8')) <= 2 * 1048576,
                 'complete first-ready candidate wire at most2MiB')
        digest(result, budget, cleanup=status == 'UNKNOWN')
        budget.check(cleanup=status == 'UNKNOWN')
    except BaseException as failure:
        result['producer_status'], result['candidate'] = 'UNKNOWN', None
        result['fixed_point_claimed'] = False
        result['error'] = {'type': type(failure).__name__, 'message': str(failure)[:1024]}
    return result

