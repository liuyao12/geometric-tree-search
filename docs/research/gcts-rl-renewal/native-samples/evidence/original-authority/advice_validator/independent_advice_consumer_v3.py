"""SOURCE ONLY: independently check advice; never place or infer from it.

The caller injects fresh authenticated original language/c354 semantics and a
native-budget tick. This endpoint imports/calls no adviser or engine. The engine
must establish the actual global BRANCH decision, preserve every base alternative
and trail preference state. A pending key is checked against the NEW whole state.
"""
import hashlib
import json

VERSION = 'unit-row-independent-advice-consumer-validator-v3-compatible-fibres-versions'
SEMANTICS_VERSION = 'independent-unit-row-missing-mark-degree-check-v2'
ADVISER_VERSION = 'unit-row-generic-goal-branch-adviser-v3-compatible-source-fibres'
STRONG_FLAGS = ('logical_proof_accepted', 'exact_point_board_accepted',
                'degree_or_EOF_accepted', 'scheduler_accepted',
                'complete_GCTS_model_accepted', 'trajectory_accepted',
                'learned_marking_accepted', 'RL_accepted', 'ROOT_resource_accepted')
LEGALITY_REASONS = ('already_selected', 'branch_excluded_complete_key',
                    'whole_support_capacity', 'whole_remote_or_metadata_mark_conflict')
SCHEMES = ('CANONICAL_PREFIX_NOVELTY', 'GENERIC_UI_LICENCE',
           'GENERIC_UI_MP', 'GENERIC_ATOMIC_TRANSPORT')
LIMITS = {'maximum_work': 500000, 'maximum_proposals': 32,
          'maximum_demands': 48, 'maximum_terms': 32, 'maximum_rounds': 32}
WORK_FIELDS = ('descriptor_steps', 'candidate_members_checked',
               'definite_profile_rejections', 'incompatible_unions',
               'duplicate_anchors', 'term_count', 'universal_count',
               'demand_count', 'rounds', 'fallback_prefix_candidates',
               'guarded_steps', 'unique_anchors')


def require(ok, reason):
    if not ok:
        raise ValueError('advice consumer: ' + reason)


def text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(text(value).encode('utf8')).hexdigest()


def equal(actual, expected, reason):
    # Literal JSON equality keeps Boolean values distinct from integers.
    require(text(actual) == text(expected), reason)


def shape(value, fields, reason):
    require(type(value) is dict and set(value) == set(fields), reason)


def subtrees(value, tick):
    stack = [value]
    while stack:
        tick()
        node = stack.pop()
        if type(node) is list:
            yield node
            stack.extend(reversed([v for v in node if type(v) is list]))


def validate_advice(*, language, semantics, state, decision, batch, tick):
    """Return fresh anchor/preferences only; all invalid/callback errors escape.

    Root's guarded wrapper injects language/semantics so the engine sees the
    five-keyword API state/decision/batch/tick. No exception is converted into a
    rejected hint. Only the four explicit c354 legality RETURN values may remove
    a pending key. READY batch members must all be legal in their exact bound
    state, and each proposed family must be a compatible temporary union.
    """
    tick()
    require(semantics.VERSION == SEMANTICS_VERSION, 'current original semantics')
    s, totals, marks, selected, excluded, names = semantics.private_state(language, state, tick)
    clone = lambda value: semantics.tree(value, tick)
    d, b, binding = clone(decision), clone(batch), clone(language.binding)
    shape(d, ('kind', 'row'), 'exact scheduler decision fields')
    require(d['kind'] == 'BRANCH' and type(d['row']) is int
            and 0 <= d['row'] < 24, 'BRANCH integer row only')
    chosen = d['row']
    require(totals[(0, chosen)] == 0, 'unfilled incident branch row')
    state_sha, input_sha = digest(s), digest(b)
    require(type(b) is dict and type(b.get('schema')) is str, 'input schema')
    equal(b.get('binding'), binding, 'whole original binding')
    require(b.get('state_sha256') == state_sha, 'whole current state hash join')
    equal(b.get('decision'), d, 'exact current decision join')
    common_names = dict(names)

    def rebuild_key(key):
        tick()
        shape(key, ('tile_type_id', 'type_preimage', 'translation'), 'full original key fields')
        fresh = semantics.rebuild_tile(language, key['type_preimage'], key['translation'], tick)
        equal(key, fresh['placement_key'], 'full original key/preimage, not digest only')
        semantics.check_collision(fresh, common_names)
        return semantics.with_obligations(fresh, totals, tick)

    rejections, selection = [], None
    if b['schema'] == 'unit-row-pending-preference-request-v1':
        mode = 'PENDING_KEYS'
        shape(b, ('schema', 'binding', 'state_sha256', 'decision', 'family_id', 'keys'),
              'pending request exact fields')
        require(type(b['family_id']) is str and 1 <= len(b['family_id']) <= 256,
                'opaque nonempty bounded family provenance')
        require(type(b['keys']) is list and len(b['keys']) <= 24, 'bounded pending key list')
        seen = set()
        for key in b['keys']:
            tick()
            fresh = rebuild_key(key)
            require(fresh['placement_key']['translation'] == [0, chosen], 'pending key incident now')
            identity = text(fresh['placement_key'])
            require(identity not in seen, 'duplicate pending full key')
            seen.add(identity)
            reason = semantics.legality(fresh, totals, marks, selected, excluded)
            require(reason is None or reason in LEGALITY_REASONS, 'known explicit legality return')
            if reason is not None:
                rejections.append({'key': clone(key), 'reason': reason})
            elif selection is None:
                selection = {'anchor': fresh, 'future_keys': [],
                             'origin': {'family_id': b['family_id']}}
    else:
        mode = 'ADVICE_BATCH'
        shape(b, ('schema', 'version', 'status', 'reason', 'binding', 'state_sha256',
                  'decision', 'proposals', 'limits', 'work', 'incomplete',
                  'original_fallback_required', 'partial_UNKNOWN_batch_is_diagnostic_only',
                  'origin', 'learned') + STRONG_FLAGS, 'advice batch exact fields')
        require(b['schema'] == 'unit-row-goal-branch-advice-batch-v1'
                and b['version'] == ADVISER_VERSION and b['status'] == 'READY'
                and b['reason'] is None, 'whole current READY batch only')
        require(b['incomplete'] is True and b['original_fallback_required'] is True
                and b['partial_UNKNOWN_batch_is_diagnostic_only'] is True
                and b['origin'] == 'HAND_WRITTEN_GENERIC_GOAL_ORDERING'
                and b['learned'] is False
                and all(b[k] is False for k in STRONG_FLAGS), 'non-authority batch metadata')
        shape(b['limits'], LIMITS, 'exact advisory limit fields')
        require(all(type(v) is int and 1 <= v <= LIMITS[k]
                    for k, v in b['limits'].items()), 'literal bounded advisory limits')
        shape(b['work'], WORK_FIELDS, 'exact diagnostic work fields')
        require(all(type(v) is int and v >= 0 for v in b['work'].values()),
                'literal nonnegative work diagnostics')
        require(1 <= b['work']['guarded_steps'] <= b['limits']['maximum_work']
                and b['work']['rounds'] <= b['limits']['maximum_rounds']
                and b['work']['term_count'] <= b['limits']['maximum_terms']
                and b['work']['universal_count'] <= b['limits']['maximum_demands']
                and b['work']['demand_count'] <= b['limits']['maximum_demands'],
                'READY diagnostics within declared advisory bounds')
        require(type(b['proposals']) is list
                and len(b['proposals']) <= b['limits']['maximum_proposals']
                and len(b['proposals']) <= b['work']['unique_anchors'], 'bounded proposal inventory')
        roots = {}
        root_nodes = set()
        for row in range(chosen, 24):
            tick()
            if totals[(0, row)] == 0 and (1, row) in marks:
                formula = semantics.formula_at(language, marks, row, tick)
                roots[row] = formula
                root_nodes.update(text(n) for n in subtrees(formula, tick))
        selected_outputs = {text(r['type_preimage']['primitive_witness']['formula'])
                            for r in s['selected']}
        all_packets, anchors, ordering = {}, set(), []
        for proposal_index, proposal in enumerate(b['proposals']):
            tick()
            shape(proposal, ('schema', 'scheme', 'binding', 'state_sha256', 'branch_row',
                  'anchor_full_key', 'members', 'ordered_PENDING_obligations', 'goal_root',
                  'score', 'future_members_are_preferences_only', 'ranking_features',
                  'installed', 'logical_proof_accepted'), 'exact incident proposal fields')
            require(proposal['schema'] == 'unit-row-goal-incident-proposal-v1'
                    and proposal['scheme'] in SCHEMES
                    and type(proposal['branch_row']) is int and proposal['branch_row'] == chosen
                    and proposal['state_sha256'] == state_sha, 'current incident proposal metadata')
            equal(proposal['binding'], binding, 'whole proposal binding')
            require(proposal['future_members_are_preferences_only'] is True
                    and proposal['installed'] is False and proposal['logical_proof_accepted'] is False,
                    'uninstalled preference flags')
            require(type(proposal['members']) is list and 1 <= len(proposal['members']) <= 24,
                    'bounded full member expansion')
            members, member_ids, rows = [], set(), []
            for record in proposal['members']:
                tick()
                shape(record, ('candidate', 'ordered_ports'), 'member record fields')
                require(type(record['candidate']) is dict and 'placement_key' in record['candidate'],
                        'whole member packet')
                fresh = rebuild_key(record['candidate']['placement_key'])
                equal(record['candidate'], fresh, 'independent whole current candidate packet')
                identity = text(fresh['placement_key'])
                require(identity not in member_ids, 'shared full key counted once in expansion')
                member_ids.add(identity)
                if identity in all_packets:
                    equal(all_packets[identity], fresh, 'shared full key full packet agreement')
                else:
                    all_packets[identity] = fresh
                require(semantics.legality(fresh, totals, marks, selected, excluded) is None,
                        'whole current member legality')
                rows.append(fresh['placement_key']['translation'][1])
                members.append(fresh)
            require(rows == sorted(set(rows)) and rows[0] == chosen,
                    'incident anchor then distinct later preference rows in canonical order')
            anchor = rebuild_key(proposal['anchor_full_key'])
            anchor_id = text(anchor['placement_key'])
            require(anchor['placement_key']['translation'] == [0, chosen]
                    and anchor_id in member_ids and anchor_id not in anchors,
                    'unique incident member anchor')
            anchors.add(anchor_id)
            # Temporary union only. No state or mark is installed or returned as fact.
            tt, mm, ss = dict(totals), dict(marks), set(selected)
            for member in members:
                tick()
                require(semantics.legality(member, tt, mm, ss, excluded) is None,
                        'compatible complete proposed member union')
                ss.add(text(member['placement_key']))
                for point, value in member['global_t_values']:
                    tt[tuple(point)] += value
                for point, value in member['global_m_values']:
                    semantics.agree(mm, tuple(point), value)
            by_row = {row: index for index, row in enumerate(rows)}
            obligations = []
            for index, member in enumerate(members):
                ports = []
                for port, read in enumerate(member['read_obligations']):
                    tick()
                    if read['row'] in by_row:
                        internal = by_row[read['row']]
                        ports.append({'kind': 'member', 'index': internal, 'row': read['row'], 'port': port})
                    else:
                        ports.append({'kind': 'pending', 'index': len(obligations), 'row': read['row'], 'port': port})
                        obligations.append({'member_index': index, 'port': port, 'row': read['row'],
                            'formula': clone(read['formula']), 'occupied': read['occupied'],
                            'status': 'PENDING', 'fact_accepted': False})
                equal(proposal['members'][index]['ordered_ports'], ports,
                      'every ordered repeated member/pending port')
            equal(proposal['ordered_PENDING_obligations'], obligations, 'whole ordered PENDING obligations')
            root = proposal['goal_root']
            connected = False
            if root is not None:
                shape(root, ('row', 'formula'), 'goal root fields')
                require(type(root['row']) is int and root['row'] in roots, 'current marked unfilled goal root')
                equal(root['formula'], roots[root['row']], 'literal current root formula')
                connected = any(r == root['row'] and
                    text(m['placement_key']['type_preimage']['primitive_witness']['formula']) == text(root['formula'])
                    for r, m in zip(rows, members))
            formula = anchor['placement_key']['type_preimage']['primitive_witness']['formula']
            novel = text(formula) not in selected_outputs
            overlap = sum(text(n) in root_nodes for n in subtrees(formula, tick))
            # External interfaces are reconstructed above, not read from diagnostics.
            # Repeated ordered ports stay present, but share one interface pair here.
            unresolved_pairs = set()
            for obligation in obligations:
                tick()
                if obligation['occupied'] is False:
                    unresolved_pairs.add((obligation['row'], text(obligation['formula'])))
            root_formula = None if root is None else text(root['formula'])
            reopens_root = root is not None and any(
                formula_text == root_formula for _, formula_text in unresolved_pairs)
            quality_class = 0 if reopens_root else 2 if connected else 1
            unresolved_interface_pairs = len(unresolved_pairs)
            score = [quality_class, -unresolved_interface_pairs, int(novel), overlap, -len(members)]
            equal(proposal['score'], score, 'independent literal advisory score')
            equal(proposal['ranking_features'], {'goal_connected': connected, 'anchor_novel': novel,
                  'literal_list_subtree_overlap': overlap, 'primitive_members': len(members),
                  'quality_class': quality_class, 'reopens_root': reopens_root,
                  'unresolved_interface_pairs': unresolved_interface_pairs},
                  'independent advisory feature values')
            ordering.append((tuple(-n for n in score), anchor_id))
            if proposal_index == 0:
                selection = {'anchor': anchor,
                    'future_keys': [clone(m['placement_key']) for m in members
                                    if text(m['placement_key']) != anchor_id],
                    'origin': {'batch_sha256': input_sha, 'proposal_index': 0,
                               'scheme': proposal['scheme'], 'goal_root': clone(root)}}
        require(ordering == sorted(ordering), 'whole original ranked batch order')
    tick()
    result = {'schema': 'unit-row-advice-validation-v1', 'version': VERSION,
              'mode': mode, 'binding': binding, 'state_sha256': state_sha,
              'decision': d, 'input_sha256': input_sha,
              'selection': selection, 'rejections': rejections}
    result.update({name: False for name in STRONG_FLAGS})
    return result
