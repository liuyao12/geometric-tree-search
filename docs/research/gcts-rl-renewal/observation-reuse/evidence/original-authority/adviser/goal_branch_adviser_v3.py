"""SOURCE ONLY: bounded hand-written goal ordering, never learned authority.

Run only after an externally checked BRANCH(row). No engine mutation/import,
donor, proof word, finite recipe library, clock, degree or exhaustion authority.
Future members are preferences; the scheduler must choose them separately.
"""
import hashlib
import json

VERSION = 'unit-row-generic-goal-branch-adviser-v3-compatible-source-fibres'
SEMANTICS_VERSION = 'independent-unit-row-missing-mark-degree-check-v2'
FALLBACK_VERSION = 'unit-row-complete-lazy-six-rule-fallback-v1'
STRONG_FLAGS = ('logical_proof_accepted', 'exact_point_board_accepted',
                'degree_or_EOF_accepted', 'scheduler_accepted',
                'complete_GCTS_model_accepted', 'trajectory_accepted',
                'learned_marking_accepted', 'RL_accepted', 'ROOT_resource_accepted')


def require(ok, reason):
    if not ok:
        raise ValueError('goal adviser: ' + reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def iter_fair_indices(*, lengths, tick):
    """Lazy finite index-box diagonal order; no mathematical EOF authority.

    Increasing coordinate sum, earlier-axis increments first within each shell.
    Every finite vector is reached if consumption/budget continue. Actual bounded
    rounds can stop sooner and do not certify a primitive/candidate universe.
    """
    tick()
    require(type(lengths) in (tuple, list) and 1 <= len(lengths) <= 8
            and all(type(n) is int and 0 <= n <= 64 for n in lengths),
            'bounded literal index-axis lengths')
    bounds = tuple(lengths)
    if any(n == 0 for n in bounds):
        return
    def shell(axis, remaining, prefix):
        tick()
        if axis == len(bounds):
            if remaining == 0:
                yield tuple(prefix)
            return
        low = max(0, remaining - sum(n-1 for n in bounds[axis+1:]))
        high = min(bounds[axis]-1, remaining)
        for value in range(high, low-1, -1):
            tick()
            yield from shell(axis+1, remaining-value, prefix+[value])
    for total in range(sum(n-1 for n in bounds)+1):
        tick()
        yield from shell(0, total, [])


class _Quota(TimeoutError):
    pass


class _Work:
    def __init__(self, tick, maximum):
        self.tick, self.maximum, self.steps = tick, maximum, 0

    def step(self):
        self.tick()
        if self.steps >= self.maximum:
            raise _Quota('finite adviser work quota; no exhaustion claim')
        self.steps += 1


def propose_branch(*, language, semantics, fallback, iter_syntax, state, decision,
                   tick, maximum_work=50000, maximum_proposals=8,
                   maximum_demands=16, maximum_terms=16, maximum_rounds=8):
    """Return finite advice only; complete original fallback remains external.

    Root must authenticate the actual original language/c354/fallback69 APIs,
    state and scheduler decision. No caller-supplied demand/proof/library input.
    A partial batch after TimeoutError is diagnostic only, not executable advice.
    Only exact OutsideLanguage filters definite profile exclusions; other errors
    propagate. Unknown/resource interruption never proves a candidate impossible.
    """
    require(type(decision) is dict and set(decision) == {'kind', 'row'}
            and decision['kind'] == 'BRANCH' and type(decision['row']) is int
            and 0 <= decision['row'] < 24, 'externally selected BRANCH(row) only')
    limits = {'maximum_work': maximum_work, 'maximum_proposals': maximum_proposals,
              'maximum_demands': maximum_demands, 'maximum_terms': maximum_terms,
              'maximum_rounds': maximum_rounds}
    ceilings = {'maximum_work': 500000, 'maximum_proposals': 32,
                'maximum_demands': 48, 'maximum_terms': 32, 'maximum_rounds': 32}
    require(all(type(v) is int and 1 <= v <= ceilings[k] for k, v in limits.items()),
            'literal bounded advisory quotas, never original-language caps')
    work = _Work(tick, maximum_work)
    stats = dict(descriptor_steps=0, candidate_members_checked=0,
                 definite_profile_rejections=0, incompatible_unions=0,
                 duplicate_anchors=0, term_count=0, universal_count=0,
                 demand_count=0, rounds=0, fallback_prefix_candidates=0)
    chosen, binding, state_sha, batch, reason, status = decision['row'], None, None, {}, None, 'READY'
    outside = language.OutsideLanguage

    try:
        work.step()
        require(semantics.VERSION == SEMANTICS_VERSION, 'current original c354 API')
        s, totals, marks, selected, excluded, names = semantics.private_state(language, state, work.step)
        require(totals[(0, chosen)] == 0, 'selected frontier row unfilled')
        binding = semantics.tree(language.binding, work.step)
        state_sha = sha(s)

        def clone(value):
            return semantics.tree(value, work.step)

        def tile(witness, premises, reads, row):
            work.step()
            pre = {'input_epoch': s['input_epoch'], 'primitive_witness': witness,
                   'ordered_premise_formulas': premises,
                   'ordered_offsets': [r-row for r in reads]}
            try:
                candidate = semantics.rebuild_tile(language, pre, [0, row], work.step)
            except outside:
                stats['definite_profile_rejections'] += 1
                return None
            stats['candidate_members_checked'] += 1
            semantics.check_collision(candidate, dict(names))
            if semantics.legality(candidate, totals, marks, selected, excluded) is not None:
                return None
            return semantics.with_obligations(candidate, totals, work.step)

        def compatible(members):
            work.step()
            if any(c is None for c in members):
                return None
            unique = {}
            for candidate in members:
                work.step()
                key = canonical(candidate['placement_key'])
                if key in unique:
                    require(canonical(unique[key]) == canonical(candidate), 'shared full key packet')
                else:
                    unique[key] = candidate
            ordered = sorted(unique.values(), key=lambda c: c['placement_key']['translation'][1])
            tt, mm, ss, nn = dict(totals), dict(marks), set(selected), dict(names)
            for candidate in ordered:
                work.step()
                semantics.check_collision(candidate, nn)
                if semantics.legality(candidate, tt, mm, ss, excluded) is not None:
                    stats['incompatible_unions'] += 1
                    return None
                ss.add(canonical(candidate['placement_key']))
                for point, value in candidate['global_t_values']:
                    tt[tuple(point)] += value
                for point, value in candidate['global_m_values']:
                    p = tuple(point)
                    if p in mm and canonical(mm[p]) != canonical(value):
                        stats['incompatible_unions'] += 1
                        return None
                    mm[p] = value
            return ordered

        def nodes(value):
            work.step()
            if type(value) is list:
                yield value
                for child in value:
                    if type(child) is list:
                        yield from nodes(child)

        # Literal salience only: neither selected outputs nor pending marks are
        # accepted mathematical facts by this adviser.
        roots = []
        for row in range(chosen, 24):
            work.step()
            if totals[(0, row)] == 0 and (1, row) in marks:
                roots.append({'row': row, 'formula': semantics.formula_at(language, marks, row, work.step)})
        roots.sort(key=lambda r: (r['row'], canonical(r['formula'])))
        root_nodes = {canonical(n) for r in roots for n in nodes(r['formula'])}
        selected_outputs = {canonical(r['type_preimage']['primitive_witness']['formula']) for r in s['selected']}

        # Finite salient pool, then bounded canonical term prefix. The universe
        # outside this heuristic pool is retained by the ORIGINAL base fallback.
        terms, seen_terms, universals, seen_universals = [], set(), [], set()
        inputs = [language.target] + [language.theory['axioms'][k] for k in sorted(language.theory['axioms'])] + list(language.gamma)
        inputs += [r['type_preimage']['primitive_witness']['formula'] for r in s['selected']]
        possible_terms = [['var', name] for name in sorted(language.parameters)]
        for formula in inputs:
            for node in nodes(formula):
                if node and node[0] in ('var', 'fun'):
                    possible_terms.append(node)
                if node and node[0] == 'all' and canonical(node) not in seen_universals:
                    try:
                        language.formula(node)
                    except outside:
                        continue
                    if len(universals) < maximum_demands:
                        seen_universals.add(canonical(node))
                        universals.append(clone(node))
        for value in possible_terms:
            work.step()
            if len(terms) >= maximum_terms:
                break
            try:
                language.term(value)
            except outside:
                continue
            key = canonical(value)
            if key not in seen_terms:
                seen_terms.add(key)
                terms.append(clone(value))
        if len(terms) < maximum_terms:
            for value in iter_syntax(language=language, kind='term', maximum_nodes=12, tick=work.step):
                work.step()
                if canonical(value) not in seen_terms:
                    seen_terms.add(canonical(value))
                    terms.append(clone(value))
                if len(terms) >= maximum_terms:
                    break
        stats['term_count'], stats['universal_count'] = len(terms), len(universals)

        def indices(lengths):
            yield from iter_fair_indices(lengths=lengths, tick=work.step)

        def read_compatible(row, formula):
            work.step()
            point = (1, row)
            return point not in marks or canonical(marks[point]) == canonical(['formula', canonical(formula)])

        def expand_frame(frame):
            # One yielded descriptor per parent per round; no eager first-root
            # expansion. Open rows that can host UI+MP are considered first:
            # there must be a strict-prior source distinct from the anchor.
            formula, row = frame['formula'], frame['row']
            if formula[0] != 'all' or formula[1] not in language.parameters or formula[1] in language.forbidden:
                return
            priors = []
            for prior in range(chosen, row):
                work.step()
                if totals[(0, prior)] == 0 and read_compatible(prior, formula[2]):
                    priors.append(prior)
            priors.sort(key=lambda r: (r < chosen+2, r))
            for prior in priors:
                work.step()
                member = tile({'rule': 'generalize', 'variable': formula[1], 'formula': formula},
                              [formula[2]], [prior], row)
                suffix = compatible([member] + frame['suffix'])
                yield (None if suffix is None else
                    {'row': prior, 'formula': clone(formula[2]),
                     'suffix': suffix, 'root': frame['root']})

        frames = [dict(r, suffix=[], root=clone(r)) for r in roots[:maximum_demands]]
        expansions = [expand_frame(frame) for frame in frames]
        stats['demand_count'] = len(frames)

        def emit(anchor, members, scheme, root=None):
            work.step()
            if anchor is None:
                return
            require(anchor['placement_key']['translation'] == [0, chosen], 'incident anchor now')
            ordered = compatible(members)
            if ordered is None:
                return
            anchor_key = canonical(anchor['placement_key'])
            require(any(canonical(c['placement_key']) == anchor_key for c in ordered), 'anchor is a member')
            by_row = {c['placement_key']['translation'][1]: i for i, c in enumerate(ordered)}
            obligations, port_records = [], []
            for index, member in enumerate(ordered):
                ports = []
                for port, read in enumerate(member['read_obligations']):
                    work.step()
                    internal = by_row.get(read['row'])
                    if internal is not None:
                        ports.append({'kind': 'member', 'index': internal, 'row': read['row'], 'port': port})
                    else:
                        ports.append({'kind': 'pending', 'index': len(obligations), 'row': read['row'], 'port': port})
                        obligations.append({'member_index': index, 'port': port, 'row': read['row'],
                            'formula': clone(read['formula']), 'occupied': read['occupied'],
                            'status': 'PENDING', 'fact_accepted': False})
                port_records.append(ports)
            formula = anchor['placement_key']['type_preimage']['primitive_witness']['formula']
            connected = root is not None and any(c['placement_key']['translation'][1] == root['row']
                and c['placement_key']['type_preimage']['primitive_witness']['formula'] == root['formula'] for c in ordered)
            novel = canonical(formula) not in selected_outputs
            overlap = sum(canonical(n) in root_nodes for n in nodes(formula))
            unresolved = set()
            for obligation in obligations:
                work.step()
                if obligation['occupied'] is False:
                    unresolved.add((obligation['row'], canonical(obligation['formula'])))
            reopens = root is not None and any(value == canonical(root['formula']) for row, value in unresolved)
            quality = 0 if reopens else 2 if connected else 1
            score = [quality, -len(unresolved), int(novel), overlap, -len(ordered)]
            if anchor_key in batch:
                stats['duplicate_anchors'] += 1
                if batch[anchor_key]['score'] >= score:
                    return
            records = [{'candidate': clone(member), 'ordered_ports': ports}
                       for member, ports in zip(ordered, port_records)]
            proposal = {'schema': 'unit-row-goal-incident-proposal-v1', 'scheme': scheme,
                'binding': clone(binding), 'state_sha256': state_sha, 'branch_row': chosen,
                'anchor_full_key': clone(anchor['placement_key']), 'members': records,
                'ordered_PENDING_obligations': obligations, 'goal_root': clone(root),
                'score': score, 'future_members_are_preferences_only': True,
                'ranking_features': {'goal_connected': connected, 'anchor_novel': novel,
                    'literal_list_subtree_overlap': overlap, 'primitive_members': len(ordered),
                    'quality_class': quality, 'reopens_root': reopens,
                    'unresolved_interface_pairs': len(unresolved)},
                'installed': False, 'logical_proof_accepted': False}
            batch[anchor_key] = proposal

        def fallback_stream():
            cursor = fallback(language=language, state=clone(s), row=chosen, tick=work.step)
            context = cursor.context()
            require(type(context) is dict and set(context) == {'schema', 'version', 'input_epoch',
                    'language_binding', 'row', 'state', 'state_sha256', 'context_sha256'}
                    and context['schema'] == 'unit-row-all-six-fallback-context-v1'
                    and context['version'] == FALLBACK_VERSION and context['language_binding'] == binding
                    and canonical(context['state']) == canonical(s)
                    and type(context['row']) is int and context['row'] == chosen
                    and context['state_sha256'] == state_sha
                    and context['input_epoch'] == s['input_epoch']
                    and context['context_sha256'] == sha({k: v for k, v in context.items() if k != 'context_sha256'}),
                    'original state-bound fallback prefix')
            ordinal = 0
            while True:
                work.step()
                event = cursor.advance()
                require(type(event) is dict and event['schema'] == 'unit-row-all-six-fallback-event-v1'
                        and event['context_sha256'] == context['context_sha256'], 'fallback prefix context')
                if event['kind'] == 'EOF':
                    return  # No degree/exhaustion interpretation.
                require(event['kind'] == 'CANDIDATE' and type(event['ordinal']) is int
                        and event['ordinal'] == ordinal and event['independently_checked'] is False,
                        'literal ordered prefix')
                ordinal += 1
                raw = event['candidate']
                key = raw['placement_key']
                fresh = tile(key['type_preimage']['primitive_witness'],
                    key['type_preimage']['ordered_premise_formulas'],
                    [chosen+d for d in key['type_preimage']['ordered_offsets']], chosen)
                require(fresh is not None and canonical(raw) == canonical(fresh), 'whole current prefix candidate')
                stats['fallback_prefix_candidates'] += 1
                yield fresh, [fresh], 'CANONICAL_PREFIX_NOVELTY', None

        def licence_stream():
            for ui, ti in indices((len(universals), len(terms))):
                work.step()
                universal, term = universals[ui], terms[ti]
                try:
                    instance = language.substitute(universal[2], universal[1], term)
                except outside:
                    yield None
                    continue
                witness = {'rule': 'instantiate', 'universal': universal, 'term': term,
                           'formula': ['imp', universal, instance]}
                anchor = tile(witness, [], [], chosen)
                yield anchor, [anchor], 'GENERIC_UI_LICENCE', None

        def ui_mp_stream(frame):
            goal, row = frame['formula'], frame['row']
            if row <= chosen:
                return
            pairs = indices((len(universals), len(terms)))
            pairs_done, fibres = False, []
            while True:
                # Admit at most one matching nonempty fibre per yielded turn.
                # Failed pair/read tests charge work, not an empty proposal turn.
                if not pairs_done:
                    for ui, ti in pairs:
                        work.step()
                        universal, term = universals[ui], terms[ti]
                        try:
                            instance = language.substitute(universal[2], universal[1], term)
                        except outside:
                            continue
                        if instance != goal:
                            continue
                        sources = []
                        for source in range(row):
                            work.step()
                            if source != chosen and read_compatible(source, universal):
                                sources.append(source)
                        if sources:
                            fibres.append((universal, term, sources, 0))
                            break
                    else:
                        pairs_done = True
                if not fibres:
                    return
                # FIFO between admitted pairs; canonical row order within each.
                universal, term, sources, position = fibres.pop(0)
                source = sources[position]
                if position+1 < len(sources):
                    fibres.append((universal, term, sources, position+1))
                work.step()
                licence = ['imp', universal, goal]
                anchor = tile({'rule': 'instantiate', 'universal': universal,
                               'term': term, 'formula': licence}, [], [], chosen)
                if anchor is None:
                    yield None
                    continue
                end = tile({'rule': 'mp', 'formula': goal}, [universal, licence], [source, chosen], row)
                yield anchor, [anchor, end] + frame['suffix'], 'GENERIC_UI_MP', frame['root']

        def term_occurrences(value, path=()):
            work.step()
            if type(value) is list:
                if value and value[0] in ('var', 'fun'):
                    yield path, value
                for index, child in enumerate(value):
                    if type(child) is list:
                        yield from term_occurrences(child, path+(index,))

        def transport_stream(frame):
            goal, row = frame['formula'], frame['row']
            if goal[0] not in ('eq', 'pred') or row < chosen+3:
                return
            occurrences = list(term_occurrences(goal))  # One bounded AST, not a product.
            middles = [r for r in range(chosen+1, row) if totals[(0, r)] == 0]
            inputs = [r for r in range(row) if r != chosen]
            for oi, ti, mi, ei, ai in indices((len(occurrences), len(terms),
                                               len(middles), len(inputs), len(inputs))):
                work.step()
                path, right = occurrences[oi]
                left, middle = terms[ti], middles[mi]
                equality_row, antecedent_row = inputs[ei], inputs[ai]
                if equality_row >= middle or antecedent_row == middle:
                    yield None
                    continue
                template = clone(goal)
                parent = template
                for index in path[:-1]:
                    parent = parent[index]
                parent[path[-1]] = ['var', language.hole]
                try:
                    antecedent = language.substitute(template, language.hole, left)
                except outside:
                    yield None
                    continue
                equality = ['eq', left, right]
                if not read_compatible(equality_row, equality) or not read_compatible(antecedent_row, antecedent):
                    yield None
                    continue
                implication = ['imp', antecedent, goal]
                licence = ['imp', equality, implication]
                anchor = tile({'rule': 'eq_subst', 'variable': language.hole,
                    'template': template, 'left': left, 'right': right, 'formula': licence}, [], [], chosen)
                if anchor is None:
                    yield None
                    continue
                mid = tile({'rule': 'mp', 'formula': implication},
                    [equality, licence], [equality_row, chosen], middle)
                end = tile({'rule': 'mp', 'formula': goal},
                    [antecedent, implication], [antecedent_row, middle], row)
                yield anchor, [anchor, mid, end] + frame['suffix'], 'GENERIC_ATOMIC_TRANSPORT', frame['root']

        streams = [fallback_stream(), licence_stream()]
        for frame in frames:
            streams += [ui_mp_stream(frame), transport_stream(frame)]
        for round_index in range(maximum_rounds):
            # Rotate over the parents present at this round's entry. Newly
            # admitted frames are serviced as proposals now, expanded next round.
            continued, admitted = [], []
            for expansion in expansions:
                if len(frames) >= maximum_demands:
                    break
                work.step()
                try:
                    child = next(expansion)
                except StopIteration:
                    continue
                continued.append(expansion)
                if child is not None:
                    frames.append(child)
                    admitted.append(expand_frame(child))
                    streams += [ui_mp_stream(child), transport_stream(child)]
            expansions = continued + admitted
            stats['demand_count'] = len(frames)
            live = []
            for stream in streams:
                work.step()
                try:
                    item = next(stream)
                except StopIteration:
                    continue
                live.append(stream)
                stats['descriptor_steps'] += 1
                if item is not None:
                    emit(*item)
            streams = live
            stats['rounds'] = round_index+1
            if not streams:
                break
        work.step()
    except TimeoutError as error:
        status, reason = 'UNKNOWN', type(error).__name__ + ': ' + str(error)
    # Failure-only builtin output. No scientific callback after a failed tick.
    ordered = sorted(batch.values(), key=lambda p: (tuple(-x for x in p['score']), canonical(p['anchor_full_key'])))
    result = {'schema': 'unit-row-goal-branch-advice-batch-v1', 'version': VERSION,
              'status': status, 'reason': reason, 'binding': binding,
              'state_sha256': state_sha, 'decision': dict(decision),
              'proposals': ordered[:maximum_proposals], 'limits': limits,
              'work': dict(stats, guarded_steps=work.steps, unique_anchors=len(batch)),
              'incomplete': True, 'original_fallback_required': True,
              'partial_UNKNOWN_batch_is_diagnostic_only': True,
              'origin': 'HAND_WRITTEN_GENERIC_GOAL_ORDERING', 'learned': False}
    result.update({name: False for name in STRONG_FLAGS})
    return result
