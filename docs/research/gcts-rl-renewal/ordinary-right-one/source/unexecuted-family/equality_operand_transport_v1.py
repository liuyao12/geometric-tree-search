"""UNEXECUTED Source proposal: mined equality-operand transport, no dispatcher.

Pure data guidance only. ROOT must authenticate donors, inputs, injected checker
adapters and live snapshots before use. Nothing here changes a graph, its
scheduler, its candidate universe, its exclusions or its rollback trail.
"""
import copy
import hashlib
import json

VERSION = 'mined-equality-operand-transport-Source-v1'
PROFILES = ('Q-six-rule-open-parameter', 'Hilbert-five-rule-ground')
ROLES = ('s', 't', 'u')


class NoInstance(ValueError):
    """No licensed/compatible instance; all original base alternatives remain."""


def need(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def integer(value, lower=0, upper=None):
    need(type(value) is int and value >= lower and (upper is None or value < upper),
         'literal bounded integer; Boolean is not an index')
    return value


def term(value, theory, parameters, tick):
    """Nominal term typing, with parameters distinct from substitution holes."""
    tick()
    need(type(value) is list and value, 'literal term AST')
    if value[0] == 'var':
        need(len(value) == 2 and type(value[1]) is str and value[1] in parameters,
             'term variable is an original declared parameter')
    else:
        need(len(value) == 3 and value[0] == 'fun' and type(value[1]) is str
             and type(value[2]) is list and value[1] in theory['functions']
             and type(theory['functions'][value[1]]) is int
             and len(value[2]) == theory['functions'][value[1]], 'original term signature')
        for child in value[2]:
            term(child, theory, parameters, tick)
    return copy.deepcopy(value)


def references(command):
    rule = command['rule']
    return ([command['antecedent'], command['implication']] if rule == 'mp' else
            [command['source']] if rule == 'generalize' else [])


def witness(command):
    return {k: copy.deepcopy(v) for k, v in command.items()
            if k not in ('antecedent', 'implication', 'source')}


def abstract(value, terms, hole):
    """Simultaneous whole-term matching; meta nodes are outside the FOL AST."""
    if value == ['var', hole]:
        return ['family-hole']
    for name in ROLES:
        if value == terms[name]:
            return ['family-term', name]
    if type(value) is list:
        return [abstract(v, terms, hole) for v in value]
    if type(value) is dict:
        return {k: (['family-hole-name'] if k == 'variable' and v == hole else
                    abstract(v, terms, hole)) for k, v in value.items()}
    return copy.deepcopy(value)


def ground(value, terms, hole):
    if value == ['family-hole']:
        return ['var', hole]
    if value == ['family-hole-name']:
        return hole
    if type(value) is list and len(value) == 2 and value[0] == 'family-term':
        need(value[1] in ROLES, 'declared family role')
        return copy.deepcopy(terms[value[1]])
    if type(value) is list:
        return [ground(v, terms, hole) for v in value]
    if type(value) is dict:
        return {k: ground(v, terms, hole) for k, v in value.items()}
    return copy.deepcopy(value)


def recognize(commands, root, context, tick):
    """Recognize an actual checked DAG; never manufacture a donor command."""
    tick()
    final = commands[root]
    if final['rule'] != 'mp':
        return None, 'root_not_MP'
    first_i = integer(final['implication'], 0, root)
    first = commands[first_i]
    if first['rule'] != 'mp':
        return None, 'not_two_ordered_MP_applications'
    subst_i = integer(first['implication'], 0, first_i)
    subst = commands[subst_i]
    if subst['rule'] != 'eq_subst':
        return None, 'not_equality_substitution'
    template, hole = subst['template'], subst['variable']
    if not (type(template) is list and len(template) == 3 and template[0] == 'eq'):
        return None, 'outside_equality_operand_slice'
    slots = [i for i in (0, 1) if template[1+i] == ['var', hole]]
    if len(slots) != 1:
        return None, 'not_exactly_one_whole_operand_hole'
    slot = slots[0]
    parameters = context['parameters']
    if type(hole) is not str or hole in parameters:
        return None, 'hole_aliases_original_parameter'
    try:
        terms = {name: term(value, context['theory'], parameters, tick)
                 for name, value in zip(ROLES, (subst['left'], subst['right'],
                                               template[2-slot]))}
    except ValueError:
        return None, 'ill_typed_or_capture_unsafe_term_roles'
    if len({canonical(v) for v in terms.values()}) != 3:
        return None, 'ambiguous_training_role_alias'
    eq_i = integer(first['antecedent'], 0, first_i)
    phi_i = integer(final['antecedent'], 0, root)
    s, t, u = (terms[n] for n in ROLES)
    phi_s = ['eq', s, u] if slot == 0 else ['eq', u, s]
    phi_t = ['eq', t, u] if slot == 0 else ['eq', u, t]
    expected = ['imp', ['eq', s, t], ['imp', phi_s, phi_t]]
    if (commands[eq_i]['formula'] != ['eq', s, t]
            or commands[phi_i]['formula'] != phi_s
            or subst['formula'] != expected
            or first['formula'] != ['imp', phi_s, phi_t]
            or final['formula'] != phi_t):
        return None, 'actual_formula_or_ordered_port_mismatch'
    indices = [subst_i, first_i, root]
    ports = [[], ['input:equality', 'member:0'], ['input:formula', 'member:1']]
    shape = {
        'slice': 'one-whole-equality-operand', 'slot': slot,
        'roles': list(ROLES),
        'input_receptors': abstract([['eq', s, t], phi_s], terms, hole),
        'members': [{'witness': abstract(witness(commands[i]), terms, hole),
                     'ordered_ports': p} for i, p in zip(indices, ports)],
        'output': abstract(phi_t, terms, hole)}
    return {'shape': shape, 'body_command_indices': indices,
            'ordered_external_command_indices': [eq_i, phi_i],
            'donor_role_terms': terms, 'donor_hole': hole}, 'eligible'


def mine_transport(donors, *, authenticate_donor, check_word, tick):
    """First eligible shape in frozen donor/root order, after FULL donor checks.

    authenticate_donor is a future trusted-coordinator intake, not a supplied
    producer checked=true flag. It must authenticate whole saved search history
    and its exact returned primitive word. No donor is bundled in this Source.
    """
    need(type(donors) is list, 'complete frozen ordered donor list')
    before = digest(donors)
    families, census, receipts = [], [], []
    for donor in donors:
        tick()
        need(type(donor) is dict and set(donor) == {
            'id', 'profile', 'context', 'commands', 'origin'}, 'exact donor intake')
        need(donor['profile'] in PROFILES and type(donor['commands']) is list
             and donor['commands'], 'profile and complete nonempty donor word')
        context, commands = donor['context'], donor['commands']
        receipt = authenticate_donor(donor)
        need(type(receipt) is dict
             and receipt.get('schema') == 'ROOT-authenticated-searched-donor-v1'
             and receipt.get('donor_id') == donor['id']
             and receipt.get('automatically_searched') is True
             and receipt.get('complete_original_target_return') is True
             and receipt.get('commands_sha256') == digest(commands)
             and receipt.get('context_sha256') == digest(context)
             and receipt.get('origin_sha256') == digest(donor['origin']),
             'trusted actual searched-origin binding, no producer authority')
        checked = check_word(profile=donor['profile'], context=context,
                             commands=commands, conclusion=context['target'],
                             primary=True)
        need(checked.get('completed') is True and checked.get('logical_accepted') is True
             and checked.get('profile') == donor['profile']
             and checked.get('scope') == 'original-closed-target-word'
             and checked.get('original_target_primary_accepted') is True,
             'whole donor independently rechecked against original target')
        receipts.append({'donor_id': donor['id'], 'origin': copy.deepcopy(receipt),
                         'independent_word_check': copy.deepcopy(checked)})
        for root in range(len(commands)):
            tick()
            candidate, reason = recognize(commands, root, context, tick)
            entry = {'donor_id': donor['id'], 'root': root, 'reason': reason}
            if candidate is not None:
                entry['shape_sha256'] = digest(candidate['shape'])
                if not families:
                    families.append(dict(candidate, family_id='equality-family-' +
                                         digest(candidate['shape']),
                                         donor_id=donor['id'],
                                         donor_commands_sha256=digest(commands)))
            census.append(entry)
    need(digest(donors) == before, 'immutable full donor intake')
    tick()
    return {'schema': 'mined-equality-operand-library-v1', 'families': families,
            'donor_census': census, 'donor_checks': receipts,
            'selection': 'first eligible body in complete frozen donor/root order',
            'donor_intake_sha256': before, 'ROOT_library_admitted': False,
            'new_theorem_claimed': False, 'scientific_target_accepted': False}


def key_data(raw, catalogue):
    need(type(raw) is list and len(raw) == 3 and type(raw[2]) is list,
         'original [recipe_index, physical_row, ordered_refs] key')
    index = integer(raw[0], 0, len(catalogue['recipes']))
    row = integer(raw[1], 0, catalogue['height'])
    refs = tuple(integer(r, 0, row) for r in raw[2])
    need(len(refs) == len(catalogue['recipes'][index]['inputs']), 'exact ordered port arity')
    return index, row, refs


def raw_key(key):
    return [key[0], key[1], list(key[2])]


def literal_union(keys, catalogue, tick):
    """Exact ORIGINAL shared unit t and ordered-offset m ABI, no new encoding."""
    height = catalogue['height']
    totals, marks, counts, seen = [0] * height, {}, {}, set()
    for x, y, value in catalogue['fixed_marks']:
        p = (integer(x), integer(y, -height + 1, height))
        integer(value, -1)
        need(p not in marks, 'fixed markings were normalized once, without duplicates')
        marks[p], counts[p] = value, 1
    for raw in keys:
        tick()
        key = key_data(raw, catalogue)
        need(key not in seen, 'shared primitive identity counted exactly once')
        seen.add(key)
        index, row, refs = key
        recipe = catalogue['recipes'][index]
        totals[row] += 1
        if totals[row] > 1:
            raise NoInstance('positive unit support overlaps a different selected key')
        local = {(1, row): recipe['output']}
        for port, (ref, code) in enumerate(zip(refs, recipe['inputs'])):
            point = (1, ref)
            if point in local and local[point] != code:
                raise NoInstance('one candidate assigns conflicting local marks')
            local[point] = code
            local[(2 + port, row)] = ref - row
        for point, value in local.items():
            if point in marks and marks[point] != value:
                raise NoInstance('whole current/fixed marking disagreement')
            marks[point] = value
            counts[point] = counts.get(point, 0) + 1
    return {'totals': totals, 'marks': [[*p, marks[p], counts[p]] for p in sorted(marks)]}


def complete_rows(selected, catalogue, tick):
    complete = set()
    for row, key in sorted(selected.items()):
        tick()
        if all(r in complete for r in key[2]):
            complete.add(row)
    return complete


def expand(root, selected, catalogue, tick):
    pending, essential = [root], set()
    while pending:
        tick()
        row = pending.pop()
        need(row in selected, 'no pending/unfilled dependency as a receptor fact')
        if row not in essential:
            essential.add(row)
            pending.extend(selected[row][2])
    # Retain EVERY occurrence-specific Gamma seed, even unused occurrences.
    for raw in catalogue['seed_keys']:
        key = key_data(raw, catalogue)
        need(selected.get(key[1]) == key, 'every original Gamma seed occurrence')
        essential.add(key[1])
    rows = sorted(essential)
    need(rows[-1] == root, 'original Gamma seeds precede the expanded conclusion')
    positions = {row: i for i, row in enumerate(rows)}
    ancestry = essential_ancestors(root, selected, tick)
    commands, keys, consumed = [], [], set()
    for row in rows:
        tick()
        key = selected[row]
        command = copy.deepcopy(catalogue['recipes'][key[0]]['witness'])
        refs = [positions[r] for r in key[2]]
        if command['rule'] == 'mp':
            command.update(antecedent=refs[0], implication=refs[1])
        elif command['rule'] == 'generalize':
            command['source'] = refs[0]
        commands.append(command)
        keys.append(raw_key(key))
        if row in ancestry and command['rule'] == 'assumption':
            consumed.add(command['index'])
    return {'commands': commands, 'primitive_keys': keys,
            'physical_rows': rows, 'conclusion': commands[-1]['formula'],
            'original_ordered_Gamma': copy.deepcopy(catalogue['context']['ordered_Gamma']),
            'consumed_original_occurrence_indices': sorted(consumed)}


def essential_ancestors(root, selected, tick):
    pending, result = [root], set()
    while pending:
        tick()
        row = pending.pop()
        need(row in selected, 'complete ancestry')
        if row not in result:
            result.add(row)
            pending.extend(selected[row][2])
    return result


def instantiate_transport(*, catalogue, snapshot, family, equality_key, formula_key,
                          check_word, tick):
    """Checked provisional base-key expansion; never applies it or alters state.

    snapshot must be a trusted current-model reader in a future ROOT wrapper.
    It supplies the original full semantic_state, not an advice-owned graph.
    """
    tick()
    catalogue_sha, family_sha = digest(catalogue), digest(family)
    state = snapshot()
    before = digest(state)
    need(state['model_epoch'] == catalogue['binding']['model_epoch']
         and canonical(state['roots']) == canonical(catalogue['roots']),
         'original model/root epoch')
    selected = {}
    for raw in state['order']:
        key = key_data(raw, catalogue)
        need(key[1] not in selected, 'one selected key per original positive row')
        selected[key[1]] = key
    for raw in catalogue['seed_keys']:
        seed = key_data(raw, catalogue)
        need(selected.get(seed[1]) == seed, 'every original occurrence-specific Gamma seed')
    current = literal_union(state['order'], catalogue, tick)
    need(canonical(current['totals']) == canonical(state['totals'])
         and canonical(current['marks']) == canonical(state['marks']),
         'whole original t/m union and mark reference counts')
    need(len(state['excluded']) == catalogue['height'], 'all original row exclusions')
    excluded = [{key_data(k, catalogue) for k in row} for row in state['excluded']]
    need(all(k[1] == row for row, keys in enumerate(excluded) for k in keys),
         'each branch-local exclusion belongs to its original row')
    need(all(k not in excluded[r] for r, k in selected.items()), 'selected keys not excluded')
    complete = complete_rows(selected, catalogue, tick)
    eqkey, phikey = key_data(equality_key, catalogue), key_data(formula_key, catalogue)
    for key in (eqkey, phikey):
        if selected.get(key[1]) != key or key[1] not in complete:
            raise NoInstance('only dependency-complete actual selected receptor facts')
    shape = family['shape']
    need(family['family_id'] == 'equality-family-' + digest(shape)
         and set(shape) == {'slice', 'slot', 'roles', 'input_receptors', 'members', 'output'}
         and shape['slice'] == 'one-whole-equality-operand'
         and type(shape['slot']) is int and shape['slot'] in (0, 1)
         and shape['roles'] == list(ROLES)
         and len(shape['members']) == 3
         and [m['witness']['rule'] for m in shape['members']] == ['eq_subst', 'mp', 'mp']
         and [m['ordered_ports'] for m in shape['members']] ==
             [[], ['input:equality', 'member:0'], ['input:formula', 'member:1']],
         'one mined equality-operand slice')
    equality = catalogue['recipes'][eqkey[0]]['witness']['formula']
    phi = catalogue['recipes'][phikey[0]]['witness']['formula']
    slot = shape['slot']
    if not (len(equality) == 3 and equality[0] == 'eq' and len(phi) == 3
            and phi[0] == 'eq' and phi[1+slot] == equality[1]):
        raise NoInstance('ordered equality/formula receptor join has no binding')
    context = catalogue['context']
    terms = {n: term(v, context['theory'], context['parameters'], tick)
             for n, v in zip(ROLES, (equality[1], equality[2], phi[2-slot]))}
    lookup = {canonical([r['witness'], r['premises']]): r['index']
              for r in catalogue['recipes']}
    holes = []
    # A hole is borrowed from a CURRENT licensed recipe, never invented here.
    for record in catalogue['recipes']:
        tick()
        w = record['witness']
        if w['rule'] != 'eq_subst':
            continue
        hole = w['variable']
        if hole in context['parameters'] or hole in holes:
            continue
        first = ground(shape['members'][0]['witness'], terms, hole)
        if first == w:
            holes.append(hole)
    if not holes:
        raise NoInstance('no current licensed substitution-hole/operand preimage')
    # Frozen catalogue order decides equivalent hole choice, not target benefit.
    hole = holes[0]
    need(ground(shape['input_receptors'], terms, hole) == [equality, phi],
         'one simultaneous typed binding at every receptor occurrence')
    sources = {'input:equality': eqkey[1], 'input:formula': phikey[1]}
    new_keys = []
    for member_i, member in enumerate(shape['members']):
        tick()
        w = ground(member['witness'], terms, hole)
        refs = tuple(sources[p] for p in member['ordered_ports'])
        premises = [catalogue['recipes'][selected[r][0]]['witness']['formula'] for r in refs]
        index = lookup.get(canonical([w, premises]))
        if index is None:
            raise NoInstance('ground member absent from COMPLETE original recipe catalogue')
        reused = next((k for r, k in sorted(selected.items())
                       if k[0] == index and k[2] == refs and r in complete), None)
        if reused is None:
            for row in range(len(catalogue['seed_keys']), catalogue['height']):
                tick()
                if row in selected or any(ref >= row for ref in refs):
                    continue
                key = (index, row, refs)
                if key in excluded[row]:
                    continue
                trial = [raw_key(k) for _, k in sorted(selected.items())] + [raw_key(key)]
                try:
                    literal_union(trial, catalogue, tick)
                except NoInstance:
                    continue
                reused = key
                break
            if reused is None:
                raise NoInstance('deterministic greedy current-union embedding unavailable')
            selected[reused[1]] = reused
            complete.add(reused[1])
            new_keys.append(raw_key(reused))
        sources['member:' + str(member_i)] = reused[1]
    expanded = expand(sources['member:2'], selected, catalogue, tick)
    need(expanded['conclusion'] == ground(shape['output'], terms, hole),
         'ground output matches same family binding')
    checked = check_word(profile=catalogue['profile'], context=context,
                         commands=expanded['commands'],
                         conclusion=expanded['conclusion'], primary=False)
    need(checked.get('completed') is True and checked.get('logical_accepted') is True
         and checked.get('profile') == catalogue['profile']
         and checked.get('original_target_primary_accepted') is False
         and checked.get('scope') in ('parameter-scoped-intermediate-consequence',
                                     'closed-intermediate-consequence'),
         'independent entire primitive expansion check')
    whole = literal_union([raw_key(k) for _, k in sorted(selected.items())], catalogue, tick)
    patch = literal_union(expanded['primitive_keys'], catalogue, tick)
    tick()
    need(digest(snapshot()) == before and digest(catalogue) == catalogue_sha
         and digest(family) == family_sha, 'unchanged current state/catalogue/family')
    return dict(expanded, schema='provisional-equality-operand-expansion-v1',
                family_id=family['family_id'], binding=copy.deepcopy(catalogue['binding']),
                source_state_sha256=before, role_terms=terms, licensed_hole=hole,
                new_primitive_keys=new_keys, independent_consequence_check=checked,
                whole_current_point_union=whole, expansion_point_union=patch,
                macro_executed=False, new_primitive_rule=False, graph_changed=False,
                original_target_accepted=False, actual_selected_proof_accepted=False,
                full_board_accepted=False, trajectory_accepted=False,
                ROOT_library_admitted=False, ROOT_resource_accepted=False)


def prefer_at_reference_branch(*, proposal, branch_row, canonical_domain, contains, tick):
    """Reorder only an ALREADY chosen reference branch; complete base fallback.

    Caller must first perform global dead/forced and earliest-generation choice.
    This function does not accept a sampled/top-k domain for degree decisions.
    """
    integer(branch_row)
    yielded = set()
    for key in proposal['new_primitive_keys']:
        tick()
        text = canonical(key)
        if key[1] == branch_row and text not in yielded and contains(key):
            yielded.add(text)
            yield copy.deepcopy(key)
    for key in canonical_domain:
        tick()
        need(key[1] == branch_row, 'one current complete reference branch domain')
        if canonical(key) not in yielded:
            yield copy.deepcopy(key)
    tick()
