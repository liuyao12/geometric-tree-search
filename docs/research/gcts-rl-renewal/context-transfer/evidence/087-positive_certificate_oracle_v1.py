"""Source-only independent complete-certificate gate; no producer imports.

The root-owned trace auditor must reconstruct the terminal State first. Pinned
independent point/logical modules are passed explicitly, never a producer graph
or decoder. Caller supplies the target and source bindings independently from
the frozen original problem/plan, not from the returned certificate.
"""
import copy
import hashlib
import json


def ascii_canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def check_complete_point_and_proof(certificate, state, *, formulas, context,
                                   authority_epoch, original_target,
                                   original_source_bindings, original_fixed_marks,
                                   point, symbolic):
    need = point.need
    need(type(certificate) is dict, 'complete point certificate dictionary')
    need(set(certificate) == {'status', 'model_epoch', 'source_bindings', 'placements',
                             'native_accepted', 'native_authority_activated', 'compiler_correspondence'},
         'exact point certificate schema')
    need(state.totals == [1] * state.height, 'independently complete required point totals')
    need(type(original_source_bindings) is dict, 'independent original source bindings')
    need(certificate.get('model_epoch') == state.epoch, 'unchanged original model epoch')
    need(ascii_canonical(certificate.get('source_bindings')) == ascii_canonical(original_source_bindings),
         'complete independent source binding closure with exact scalar types')
    need(certificate.get('native_accepted') is False and certificate.get('native_authority_activated') is False,
         'no native authority in a symbolic point certificate')
    need(certificate.get('compiler_correspondence') == 'open', 'native compiler correspondence remains open')
    need(certificate.get('status') == 'finite_exact_point_tiling_pending_independent_logical_certificate',
         'producer point certificate has pending symbolic authority only')
    # Rebuild from the independently reconstructed selected keys, never from
    # supplied formula rows, commands or t/m values.
    by_row = sorted(state.selected, key=lambda key: key[1])
    need(len(by_row) == state.height and [k[1] for k in by_row] == list(range(state.height)),
         'exact distinct row occupancy, including all original seeds')
    registry = point.digest(formulas)
    placements = []
    for key in by_row:
        recipe_index, row, refs = key
        point.integer(recipe_index)
        point.integer(row)
        need(type(refs) is tuple, 'independent strict ordered reference tuple')
        need(0 <= recipe_index < len(state.recipes), 'original primitive inventory identity')
        t, m = point.points(state.recipes[recipe_index], row, refs, state.height)
        placements.append(point.decorate(key, t, m, state.recipes, context, authority_epoch, registry))
    need(len({p['id'] for p in placements}) == len(placements), 'full decorated identities remain distinct')
    need(type(certificate.get('placements')) is list
         and ascii_canonical(certificate['placements']) == ascii_canonical(placements),
         'every returned full identity, command, ordered port and t/m value reconstructed')
    # Markings include the negative-row exterior and explicit assigned zero.
    # Derive the fixed assignments from original bindings supplied by the trace
    # transaction rather than treating absent points as assigned zero.
    fixed = original_fixed_marks
    union = symbolic.point_union(placements, [[0, row] for row in range(state.height)], fixed, exact=True)
    need(union['t'] == [[0, row, 1] for row in range(state.height)], 'no hidden exterior occupancy')
    need(union['m'] == [[x, y, v] for (x, y), v in sorted(state.marks.items())],
         'whole independently solved assigned marking union exact')
    counts = {(x, y): 1 for x, y, value in fixed}
    need(len(counts) == len(fixed), 'distinct original fixed mark assignments')
    for placement in placements:
        for x, y, value in placement['m']:
            counts[(x, y)] = counts.get((x, y), 0) + 1
    need(counts == state.refs, 'complete terminal marking reference counts exact')
    logical = derive_ground_proof_and_flat_request(placements, formulas=formulas, context=context,
        original_target=original_target, symbolic=symbolic, need=need)
    return {'status': 'independently_checked_complete_point_and_guarded_ground_proof',
            'model_epoch': state.epoch, 'rows': state.height, 'placements': placements,
            'aggregate': union, 'point_certificate_sha256': hashlib.sha256(ascii_canonical(certificate)).hexdigest(),
            **logical}


def derive_ground_proof_and_flat_request(placements, *, formulas, context,
                                         original_target, symbolic, need):
    """Every row is checked, retaining all ordered hypothesis occurrences."""
    need(type(placements) is list and placements, 'complete nonempty primitive rows')
    premises = copy.deepcopy(context['ordered_local_premises'])
    theory = copy.deepcopy(context['theory'])
    checker = symbolic.SymbolicChecker(theory)
    commands, accepted, provenance = [], [], []
    codes = {ascii_canonical(value): index for index, value in enumerate(formulas)}
    need(len(codes) == len(formulas), 'injective complete original formula registry')
    for row, placement in enumerate(placements):
        command = copy.deepcopy(placement['command'])
        need(type(command) is dict and command.get('rule') in ('assumption', 'axiom', 'instantiate', 'eq_subst', 'mp'),
             'primitive guarded symbolic rule only')
        need(placement['key'][1] == row, 'row-preserving primitive word translation')
        formula = checker.command(command, accepted, premises)
        accepted.append(formula)
        commands.append(command)
        need(ascii_canonical(formula) in codes, 'original registered output formula')
        provenance.append({'row': row, 'placement_id': placement['id'],
                           'key': copy.deepcopy(placement['key']),
                           'formula_code': codes[ascii_canonical(formula)],
                           'command_sha256': hashlib.sha256(ascii_canonical(command)).hexdigest()})
    need(accepted[-1] == original_target, 'exact original target, not merely some complete row tiling')
    checker.proof(commands, premises, original_target)
    local = {'theory': copy.deepcopy(theory), 'ordered_local_premises': copy.deepcopy(premises),
             'proof': copy.deepcopy(commands), 'target': copy.deepcopy(original_target)}
    hypothesis_records = []
    for occurrence, formula in enumerate(premises):
        hypothesis_name = 'hypothesis-' + str(occurrence)
        need(hypothesis_name not in theory['axioms'], 'fresh retained hypothesis axiom name')
        theory['axioms'][hypothesis_name] = copy.deepcopy(formula)
        hypothesis_records.append({'index': occurrence, 'name': hypothesis_name, 'formula': copy.deepcopy(formula)})
    flat_commands = []
    for command in commands:
        if command['rule'] == 'assumption':
            occurrence = command['index']
            need(type(occurrence) is int and 0 <= occurrence < len(premises), 'exact ordered hypothesis occurrence')
            need(command['formula'] == premises[occurrence], 'retained hypothesis formula exact')
            flat_commands.append({'rule': 'axiom', 'name': hypothesis_records[occurrence]['name'],
                                  'formula': copy.deepcopy(premises[occurrence])})
        else:
            flat_commands.append(copy.deepcopy(command))
    # Recheck under the extended theory, now with no local assumptions. This is
    # a ground consequence of retained Gamma, not discharge or universal closure.
    symbolic.SymbolicChecker(theory).proof(flat_commands, [], original_target)
    request = {'protocol': 'gcts-fol-1', 'theory': theory, 'blocks': [],
               'proof': flat_commands, 'target': copy.deepcopy(original_target)}
    payload = ascii_canonical(request)
    problem = {key: request[key] for key in ('protocol', 'theory', 'target')}
    return {'local_certificate': local, 'flat_request': request,
            'request_ascii': payload.decode('ascii'), 'request_bytes': len(payload),
            'request_sha256': hashlib.sha256(payload).hexdigest(),
            'local_certificate_sha256': hashlib.sha256(ascii_canonical(local)).hexdigest(),
            'row_proof_sha256': hashlib.sha256(ascii_canonical(commands)).hexdigest(),
            'problem_sha256': hashlib.sha256(ascii_canonical(problem)).hexdigest(),
            'retained_hypotheses': hypothesis_records, 'provenance': provenance,
            'logical_scope': 'Original ground sequent with all hypotheses retained; no universal closure or native execution.',
            'native_queries': 0, 'native_accepted': False}
