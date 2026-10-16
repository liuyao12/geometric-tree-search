"""SOURCE ONLY independent local evidence checking, not a search engine.

Private language/state are caller authority. No proposer import or call. Pending
formula marks are obligations, never logical facts. Resource errors propagate.
"""
import hashlib
import json

VERSION = 'independent-unit-row-missing-mark-degree-check-v2'
PROPOSERS = ('unit-row-implicit-degree-evidence-v3-missing-marks',)
FALSE_FLAGS = ('degree_zero_or_singleton_accepted', 'degree_ge_two_accepted',
               'complete_candidate_graph_accepted', 'scheduler_or_rollback_accepted',
               'logical_proof_accepted', 'ROOT_resource_accepted')
ARITY = {'axiom': 0, 'assumption': 0, 'instantiate': 0, 'eq_subst': 0,
         'mp': 2, 'generalize': 1}


def require(ok, reason):
    if not ok:
        raise ValueError('degree evidence: ' + reason)


def tree(value, tick):
    tick()
    if type(value) in (str, int, bool) or value is None:
        return value
    if type(value) is list:
        return [tree(v, tick) for v in value]
    require(type(value) is dict and all(type(k) is str for k in value),
            'exact builtin JSON tree, no floats/custom objects')
    return {k: tree(v, tick) for k, v in value.items()}


def text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def sha(value):
    return hashlib.sha256(text(value).encode('utf8')).hexdigest()


def point_map(entries, tick):
    require(type(entries) is list, 'whole point array')
    result = {}
    for item in entries:
        tick()
        require(type(item) is list and len(item) == 2 and type(item[0]) is list
                and len(item[0]) == 2 and all(type(x) is int for x in item[0]),
                'exact integer coordinate pair')
        p = tuple(item[0])
        require(p not in result, 'duplicate point')
        result[p] = item[1]
    return result


def agree(values, p, v):
    require(p not in values or text(values[p]) == text(v), 'internal marking conflict')
    values[p] = v


def rebuild_tile(language, preimage, translation, tick):
    """Derive point data from private rule membership, not supplied point arrays."""
    tick()
    require(type(preimage) is dict and set(preimage) == {'input_epoch',
            'primitive_witness', 'ordered_premise_formulas', 'ordered_offsets'},
            'exact prototype preimage')
    require(preimage['input_epoch'] == language.binding['language_epoch'], 'prototype epoch')
    require(type(translation) is list and len(translation) == 2
            and all(type(x) is int for x in translation) and translation[0] == 0
            and 0 <= translation[1] < 24, 'unit-row translation')
    row = translation[1]
    witness = preimage['primitive_witness']
    inputs, offsets = preimage['ordered_premise_formulas'], preimage['ordered_offsets']
    require(type(witness) is dict and type(witness.get('rule')) is str and witness['rule'] in ARITY
            and type(inputs) is list and type(offsets) is list
            and len(inputs) == len(offsets) == ARITY[witness['rule']], 'ordered arity')
    require(all(type(d) is int and -23 <= d < 0 and 0 <= row+d < row for d in offsets),
            'strict negative offset with earlier absolute read')
    member = language.primitive(witness, inputs)
    pre = tree(preimage, tick)
    key = {'tile_type_id': 'bounded-point-tile-' + sha(pre),
           'type_preimage': pre, 'translation': list(translation)}
    local = [[[1, 0], ['formula', text(witness['formula'])]]]
    marks = [[[1, row], ['formula', text(witness['formula'])]]]
    for port in range(len(inputs)):
        tick()
        delta, value = offsets[port], ['formula', text(inputs[port])]
        local += [[[1, delta], tree(value, tick)], [[2+port, 0], ['offset', delta]]]
        marks += [[[1, row+delta], tree(value, tick)], [[2+port, row], ['offset', delta]]]
    checked_union = {}
    for p, v in marks:
        agree(checked_union, tuple(p), v)
    return {'placement_key': key, 'selection_record': dict(key, generation=1),
            'local_t_values': [[[0, 0], 1]], 'local_m_values': local,
            'global_t_values': [[[0, row], 1]], 'global_m_values': marks,
            'membership': member}


def private_state(language, state, tick):
    s = tree(state, tick)
    require(type(s) is dict and set(s) == {'schema', 'input_epoch', 'height', 't',
            'm', 'selected', 'excluded', 'generation'}, 'exact private state fields')
    require(s['schema'] == 'unit-row-implicit-private-state-v1'
            and type(s['input_epoch']) is str
            and s['input_epoch'] == language.binding['language_epoch']
            and type(s['height']) is int and s['height'] == 24, 'private epoch/profile')
    t, m, generation = (point_map(s[k], tick) for k in ('t', 'm', 'generation'))
    target = {(0, r) for r in range(24)}
    require(set(t) == set(generation) == target
            and all(type(v) is int and v in (0, 1) for v in t.values())
            and all(type(v) is int and v == 0 for v in generation.values()),
            'complete unit target and root0 generations')
    require(type(s['selected']) is list and type(s['excluded']) is list, 'key inventories')
    rt = dict.fromkeys(target, 0)
    rm = {(1, k): ['outside', s['input_epoch']] for k in range(-23, 0)}
    rm[(1, 23)] = ['formula', text(language.target)]
    selected, excluded, names = set(), set(), {}
    for category in ('selected', 'excluded'):
        for record in s[category]:
            tick()
            selected_record = category == 'selected'
            fields = {'tile_type_id', 'type_preimage', 'translation'}
            require(type(record) is dict and set(record) ==
                    fields | ({'generation'} if selected_record else set()), 'full key fields')
            if selected_record:
                require(type(record['generation']) is int and record['generation'] == 1,
                        'selected generation1 from fixed roots')
            tile = rebuild_tile(language, record['type_preimage'], record['translation'], tick)
            expected = tile['selection_record'] if selected_record else tile['placement_key']
            require(text(record) == text(expected), 'literal key/preimage, not digest-only')
            key = text(tile['placement_key'])
            name, pre = record['tile_type_id'], text(record['type_preimage'])
            require(name not in names or names[name] == pre, 'prototype digest collision')
            names[name] = pre
            require(key not in selected and key not in excluded, 'duplicate/overlapping key')
            (selected if selected_record else excluded).add(key)
            if selected_record:
                r = record['translation'][1]
                rt[(0, r)] += 1
                require(rt[(0, r)] <= 1, 'selected capacity overfill')
                for p, v in tile['global_m_values']:
                    agree(rm, tuple(p), v)
    require(text(sorted([[list(p), v] for p, v in t.items()])) ==
            text(sorted([[list(p), v] for p, v in rt.items()])), 'whole selected t equality')
    require(text(sorted([[list(p), v] for p, v in m.items()])) ==
            text(sorted([[list(p), v] for p, v in rm.items()])), 'whole fixed+selected m equality')
    return s, t, m, selected, excluded, names


def formula_at(language, marks, row, tick):
    if (1, row) not in marks:
        return None
    value = marks[(1, row)]
    require(type(value) is list and len(value) == 2 and value[0] == 'formula'
            and type(value[1]) is str, 'assigned literal formula mark')
    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, 'duplicate formula key')
            out[k] = v
        return out
    def forbidden(number):
        raise ValueError('degree evidence: formula float/nonfinite')
    tick()
    formula = json.loads(value[1], object_pairs_hook=pairs,
                         parse_float=forbidden, parse_constant=forbidden)
    require(text(formula) == value[1], 'canonical literal formula string')
    language.formula(formula)
    return formula


def legality(tile, totals, marks, selected, excluded):
    key = text(tile['placement_key'])
    if key in selected:
        return 'already_selected'
    if key in excluded:
        return 'branch_excluded_complete_key'
    if any(totals.get(tuple(p), 1)+v > 1 for p, v in tile['global_t_values']):
        return 'whole_support_capacity'
    if any(tuple(p) in marks and text(marks[tuple(p)]) != text(v)
           for p, v in tile['global_m_values']):
        return 'whole_remote_or_metadata_mark_conflict'
    return None


def with_obligations(tile, totals, tick):
    row = tile['placement_key']['translation'][1]
    pre = tile['placement_key']['type_preimage']
    tile['read_obligations'] = [{'row': row+d, 'formula': tree(f, tick),
            'occupied': totals[(0, row+d)] == 1, 'fact_accepted': False}
            for d, f in zip(pre['ordered_offsets'], pre['ordered_premise_formulas'])]
    return tile


def check_collision(tile, names):
    key = tile['placement_key']
    name, pre = key['tile_type_id'], text(key['type_preimage'])
    require(name not in names or names[name] == pre, 'prototype digest collision')
    names[name] = pre


def independent_carrier(language, bound, tick):
    """Independent lazy grammar: odometer partitions and iterative child product."""
    require(type(bound) is int and 1 <= bound <= 44, 'carrier bound1..44')
    outside = language.OutsideLanguage
    fun = sorted(language.theory['functions'].items())
    pred = sorted(language.theory['predicates'].items())
    binders = sorted(language.binder_names)

    def allocations(total, width):
        tick()
        if width == 0:
            if total == 0:
                yield ()
            return
        if total < width:
            return
        if width == 1:
            yield (total,)
            return
        upper = total-width+1
        head = [1] * (width-1)
        while True:
            tick()
            last = total-sum(head)
            if last >= 1:
                yield tuple(head+[last])
            position = len(head)-1
            while position >= 0 and head[position] == upper:
                head[position] = 1
                position -= 1
            if position < 0:
                return
            head[position] += 1

    def product(sizes, names, term_mode):
        tick()
        if not sizes:
            yield []
            return
        child = term if term_mode else formula
        stack, prefix = [iter(child(sizes[0], names))], []
        while stack:
            tick()
            try:
                item = next(stack[-1])
            except StopIteration:
                stack.pop()
                if prefix:
                    prefix.pop()
                continue
            if len(stack) == len(sizes):
                yield prefix+[item]
            else:
                prefix.append(item)
                stack.append(iter(child(sizes[len(prefix)], names)))

    def term(size, names):
        tick()
        if not 1 <= size <= 12:
            return
        if size == 1:
            for name in sorted(names):
                tick()
                yield ['var', name]
        for name, arity in fun:
            for sizes in allocations(size-1, arity):
                for values in product(sizes, names, True):
                    tick()
                    yield ['fun', name, values]

    def formula(size, names):
        tick()
        if size == 1:
            yield ['bot']
        for name, arity in pred:
            for sizes in allocations(size-1, arity):
                for values in product(sizes, names, True):
                    tick()
                    yield ['pred', name, values]
        for sizes in allocations(size-1, 2):
            for values in product(sizes, names, True):
                tick()
                yield ['eq', values[0], values[1]]
        if size > 1:
            for body in formula(size-1, names):
                tick()
                yield ['not', body]
            for binder in binders:
                for body in formula(size-1, names | {binder}):
                    tick()
                    yield ['all', binder, body]
        for tag in ('imp', 'and', 'or'):
            for sizes in allocations(size-1, 2):
                for values in product(sizes, names, False):
                    tick()
                    yield [tag, values[0], values[1]]

    for nodes in range(1, bound+1):
        for value in formula(nodes, frozenset(language.parameter_set)):
            tick()
            try:
                measured = language.formula(value)
            except outside:
                continue
            require(measured == nodes, 'independent exact constructor count')
            yield value


def fibre_header(language, prefix, output, tick):
    tick()
    nodes = language.formula(output)
    return {'schema': 'unit-row-missing-mark-fibres-v1', 'completed': False,
            'output_nodes': nodes, 'MP_antecedent_max_nodes': 43-nodes,
            'assigned_prior_rows': [i for i, f in enumerate(prefix) if f is not None],
            'absent_prior_rows': [i for i, f in enumerate(prefix) if f is None],
            'axiom_labels_seen': [], 'Gamma_occurrences_seen': [],
            'UG_fibres': [], 'ordered_MP_fibres': [],
            'carrier_order': 'size; bot,pred,eq,not,all,imp,and,or; literal names; positive size compositions',
            'carrier_materialized': False, 'independently_accepted': False}


def verify_missing_cover(language, s, row, output, prefix, t, m,
                         selected, excluded, names, tick):
    """Re-enumerate every fibre; return exact data, not a trusted hash shortcut."""
    outside = language.OutsideLanguage
    evidence = fibre_header(language, prefix, output, tick)
    checked, used, root_rejections = [], set(), []

    def evaluate(witness, premises, reads):
        tick()
        pre = {'input_epoch': s['input_epoch'], 'primitive_witness': witness,
               'ordered_premise_formulas': premises, 'ordered_offsets': [k-row for k in reads]}
        try:
            tile = rebuild_tile(language, pre, [0, row], tick)
        except outside as error:
            return {'rule': witness['rule'], 'reads': reads, 'reason': error.reason,
                    'kind': 'definite_membership_exclusion'}
        key = tile['placement_key']
        name, pretext = key['tile_type_id'], text(key['type_preimage'])
        require(name not in names or names[name] == pretext, 'prototype digest collision')
        reason = legality(tile, t, m, selected, excluded)
        if reason is not None:
            return {'rule': witness['rule'], 'reads': reads, 'kind': reason, 'placement_key': key}
        encoded = text(key)
        if encoded in used:
            return {'kind': 'duplicate_full_key'}
        used.add(encoded)
        names[name] = pretext
        checked.append(with_obligations(tile, t, tick))
        require(len(checked) < 2, 'complete missing cover cannot conceal early two witnesses')
        return {'kind': 'new_survivor'}

    for label in sorted(language.theory['axioms']):
        tick()
        evidence['axiom_labels_seen'].append(label)
        if language.theory['axioms'][label] == output:
            decision = evaluate({'rule': 'axiom', 'name': label, 'formula': output}, [], [])
            if decision['kind'] not in ('new_survivor', 'duplicate_full_key'):
                root_rejections.append(decision)
    for index, value in enumerate(language.gamma):
        tick()
        evidence['Gamma_occurrences_seen'].append(index)
        if value == output:
            decision = evaluate({'rule': 'assumption', 'index': index, 'formula': output}, [], [])
            if decision['kind'] not in ('new_survivor', 'duplicate_full_key'):
                root_rejections.append(decision)

    def finish_fibre(descriptor, stream):
        preimages, decisions = hashlib.sha256(), hashlib.sha256()
        examined, rejected, start = 0, 0, len(checked)
        for witness, premises, reads in stream:
            tick()
            preimages.update((text([witness, premises, reads])+'\n').encode('utf8'))
            examined += 1
            decision = evaluate(witness, premises, reads)
            decisions.update((text(decision)+'\n').encode('utf8'))
            if decision['kind'] not in ('new_survivor', 'duplicate_full_key'):
                rejected += 1
        descriptor.update(completed=True, examined=examined,
            new_survivors=len(checked)-start, rejections=rejected,
            examined_preimages_sha256=preimages.hexdigest(), decisions_sha256=decisions.hexdigest())

    for k, value in enumerate(prefix):
        tick()
        descriptor = {'row': k, 'inverse': 'UG', 'completed': False}
        evidence['UG_fibres'].append(descriptor)
        if output[0] == 'all' and (value is None or value == output[2]):
            descriptor['case'] = 'missing_or_matching_body'
            stream = (({'rule': 'generalize', 'variable': output[1], 'formula': output}, [output[2]], [k]),)
        else:
            descriptor['case'] = 'not_universal_or_assigned_body_mismatch'
            stream = ()
        finish_fibre(descriptor, stream)
    for i in range(row):
        for j in range(row):
            tick()
            a, implication = prefix[i], prefix[j]
            descriptor = {'rows': [i, j], 'inverse': 'MP', 'completed': False}
            evidence['ordered_MP_fibres'].append(descriptor)
            if i == j:
                descriptor.update(case='FINITE_AST_OCCURS_CHECK_EMPTY',
                    equation=['A', ['imp', 'A', 'C']], positive_output_nodes=evidence['output_nodes'])
                stream = ()
            elif a is not None:
                descriptor['case'] = 'antecedent_assigned'
                required = ['imp', a, output]
                stream = (({'rule': 'mp', 'formula': output}, [a, required], [i, j]),) if implication is None or implication == required else ()
            elif implication is not None:
                descriptor['case'] = 'only_implication_assigned'
                stream = (({'rule': 'mp', 'formula': output}, [implication[1], implication], [i, j]),) if implication[0] == 'imp' and implication[2] == output else ()
            else:
                descriptor['case'] = 'both_absent_full_scoped_carrier'
                maximum = evidence['MP_antecedent_max_nodes']
                stream = (({'rule': 'mp', 'formula': output}, [f, ['imp', f, output]], [i, j])
                          for f in independent_carrier(language, maximum, tick)) if maximum >= 1 else ()
            finish_fibre(descriptor, stream)
    tick()
    evidence['completed'] = True
    return checked, root_rejections, evidence


def check_degree_evidence(*, language, state, row, proposal, tick):
    """Accept a local bound/cover only. UNKNOWN is not zero or singleton."""
    outside = language.OutsideLanguage
    s, t, m, selected, excluded, names = private_state(language, state, tick)
    require(type(row) is int and 0 <= row < 24 and t[(0, row)] == 0, 'unfilled queried row')
    p = tree(proposal, tick)
    fields = {'schema', 'version', 'kind', 'state', 'state_sha256', 'input_epoch',
              'language_binding', 'row', 'candidates', 'coverage', 'rejections',
              'complete_cover_proposed', 'fibre_cover', 'untrusted', 'scope'} | set(FALSE_FLAGS)
    require(type(p) is dict and set(p) == fields, 'exact proposal fields')
    require(p['schema'] == 'unit-row-degree-evidence-proposal-v2'
            and p['version'] in PROPOSERS and type(p['version']) is str, 'proposal protocol/version')
    require(text(p['state']) == text(s) and p['state_sha256'] == sha(s)
            and p['input_epoch'] == s['input_epoch']
            and text(p['language_binding']) == text(language.binding)
            and type(p['row']) is int and p['row'] == row, 'private state/binding/query custody')
    require(p['untrusted'] is True and all(p[f] is False for f in FALSE_FLAGS)
            and p['scope'] == 'Local evidence only; independent checker/global graph/fallback still required.',
            'untrusted flags/scope must not assert authority')
    require(type(p['candidates']) is list and type(p['rejections']) is list, 'candidate/rejection arrays')
    kind = p['kind']
    require(type(kind) is str and kind in ('NON_IMP_ASSIGNED_PREFIX_COVER', 'NON_IMP_MISSING_MARK_COVER',
            'TWO_LEGAL_WITNESSES', 'UNKNOWN'), 'declared proposal kind')
    covered = kind in ('NON_IMP_ASSIGNED_PREFIX_COVER', 'NON_IMP_MISSING_MARK_COVER')
    missing_checked = kind == 'NON_IMP_MISSING_MARK_COVER'
    require(p['complete_cover_proposed'] is covered, 'cover flag exact boolean')
    checked, used = [], set()

    output = formula_at(language, m, row, tick)
    prefix = [formula_at(language, m, k, tick) for k in range(row)]
    missing_eligible = output is not None and output[0] != 'imp' and any(f is None for f in prefix)
    if missing_checked:
        require(missing_eligible and p['coverage'] is None, 'missing-cover hypotheses')
        checked, root_rejections, expected_fibres = verify_missing_cover(
            language, s, row, output, prefix, t, m, selected, excluded, names, tick)
        require(text(p['candidates']) == text(checked), 'whole missing-cover survivor list')
        require(text(p['rejections']) == text(root_rejections), 'missing-cover root observations')
        require(text(p['fibre_cover']) == text(expected_fibres), 'complete independent fibre census/counts/hashes')
    elif covered:
        require(p['fibre_cover'] is None, 'legacy cover has no missing fibre evidence')
        require(output is not None and output[0] != 'imp'
                and all(f is not None for f in prefix), 'restricted cover hypotheses')
        coverage = {'axiom_labels_seen': sorted(language.theory['axioms']),
                    'Gamma_occurrences_seen': list(range(len(language.gamma))),
                    'UG_prior_rows_seen': list(range(row)) if output[0] == 'all' else [],
                    'ordered_MP_pairs_seen': [[i, j] for i in range(row) for j in range(row)]}
        descriptors = []
        for name in coverage['axiom_labels_seen']:
            if language.theory['axioms'][name] == output:
                descriptors.append(({'rule': 'axiom', 'name': name, 'formula': output}, [], []))
        for index in coverage['Gamma_occurrences_seen']:
            if language.gamma[index] == output:
                descriptors.append(({'rule': 'assumption', 'index': index, 'formula': output}, [], []))
        if output[0] == 'all':
            for k, f in enumerate(prefix):
                for variable in language.parameters:
                    if ['all', variable, f] == output:
                        descriptors.append(({'rule': 'generalize', 'variable': variable,
                                             'formula': output}, [f], [k]))
        for i, j in coverage['ordered_MP_pairs_seen']:
            if prefix[j] == ['imp', prefix[i], output]:
                descriptors.append(({'rule': 'mp', 'formula': output}, [prefix[i], prefix[j]], [i, j]))
        rejected = []
        for witness, premises, reads in descriptors:
            tick()
            pre = {'input_epoch': s['input_epoch'], 'primitive_witness': witness,
                   'ordered_premise_formulas': premises, 'ordered_offsets': [k-row for k in reads]}
            try:
                tile = rebuild_tile(language, pre, [0, row], tick)
            except outside as error:
                rejected.append({'rule': witness['rule'], 'reads': reads,
                                 'reason': error.reason, 'kind': 'definite_membership_exclusion'})
                continue
            check_collision(tile, names)
            reason = legality(tile, t, m, selected, excluded)
            if reason is not None:
                rejected.append({'rule': witness['rule'], 'reads': reads, 'kind': reason,
                                 'placement_key': tile['placement_key']})
            elif text(tile['placement_key']) not in used:
                used.add(text(tile['placement_key']))
                checked.append(with_obligations(tile, t, tick))
        require(text(p['coverage']) == text(coverage), 'complete occurrence/pair census')
        require(text(p['rejections']) == text(rejected), 'complete filtered-cover observations')
        require(text(p['candidates']) == text(checked), 'whole exact ordered survivor list')
    else:
        if missing_eligible:
            header = fibre_header(language, prefix, output, tick)
            actual = p['fibre_cover']
            require(type(actual) is dict and set(actual) == set(header), 'partial fibre header fields')
            for name, value in header.items():
                if name in ('axiom_labels_seen', 'Gamma_occurrences_seen', 'UG_fibres', 'ordered_MP_fibres'):
                    require(type(actual[name]) is list, 'partial fibre observation array')
                else:
                    require(text(actual[name]) == text(value), 'partial fibre header/completion flag')
            # Partial arrays/digests do not contribute to witness acceptance.
        else:
            require(p['fibre_cover'] is None, 'no missing-fibre context')
        require(p['coverage'] is None and (len(p['candidates']) == 2
                if kind == 'TWO_LEGAL_WITNESSES' else len(p['candidates']) <= 1),
                'witness/UNKNOWN shape')
        for raw in p['candidates']:
            tick()
            require(type(raw) is dict and type(raw.get('placement_key')) is dict, 'candidate full key')
            key = raw['placement_key']
            require(set(key) == {'tile_type_id', 'type_preimage', 'translation'}
                    and key['translation'] == [0, row], 'incident placement')
            tile = rebuild_tile(language, key['type_preimage'], key['translation'], tick)
            check_collision(tile, names)
            require(legality(tile, t, m, selected, excluded) is None, 'whole candidate legality')
            encoded = text(tile['placement_key'])
            require(encoded not in used, 'two witnesses cannot repeat one full key')
            used.add(encoded)
            tile = with_obligations(tile, t, tick)
            require(text(raw) == text(tile), 'entire candidate/prototype/marks/member/read receipt')
            checked.append(tile)
        # Hint rejections are untrusted diagnostics, not a completed domain census.
    exact_degree = len(checked) if covered else None
    status = ('ZERO' if exact_degree == 0 else 'SINGLETON' if exact_degree == 1 else 'MANY') if covered else (
             'TWO_OR_MORE' if kind == 'TWO_LEGAL_WITNESSES' else 'UNKNOWN')
    tick()
    return {'schema': 'unit-row-degree-evidence-check-v2', 'version': VERSION,
            'status': status, 'accepted_local_evidence': status != 'UNKNOWN',
            'input_epoch': s['input_epoch'], 'state_sha256': sha(s), 'row': row,
            'complete_cover_checked': covered, 'degree_exact': exact_degree,
            'missing_mark_cover_checked': missing_checked,
            'candidate_keys': [v['placement_key'] for v in checked],
            'sole_candidate': checked[0] if exact_degree == 1 else None,
            'complete_candidate_graph_accepted': False, 'scheduler_or_rollback_accepted': False,
            'logical_proof_accepted': False, 'ROOT_resource_accepted': False}
