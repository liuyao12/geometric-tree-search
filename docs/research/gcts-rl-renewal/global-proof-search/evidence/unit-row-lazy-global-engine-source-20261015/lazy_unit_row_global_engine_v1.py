"""SOURCE ONLY original unit-row engine, named EARLIEST-GENERATION-ROW-TIE.

No project imports or clocks. Caller authenticates language, current semantics,
proposer and complete fallback Sources. EOF alone never proves zero/exhaustion.
"""
import hashlib
import json

VERSION = 'lazy-unit-row-global-engine-v1'
VARIANT = 'GLOBAL-DEAD-FORCED-EARLIEST-GENERATION-ROW-TIE'
SEMANTICS_VERSION = 'independent-unit-row-missing-mark-degree-check-v2'
FALLBACK_VERSION = 'unit-row-complete-lazy-six-rule-fallback-v1'
RULES = ['axiom', 'assumption', 'instantiate', 'eq_subst', 'mp', 'generalize']


class Unresolved(TimeoutError):
    pass


def need(ok, reason):
    if not ok:
        raise ValueError('lazy engine: ' + reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def diagnostic_copy(value):
    """Builtin output data only; usable during failure-only restoration/output."""
    return json.loads(canonical(value))


def select_schedule(*, evidence, generations, tick):
    """Pure scheduler kernel; varied-generation controls are NONLOGICAL only."""
    tick()
    need(type(evidence) is dict and type(generations) is dict
         and set(evidence) == set(generations), 'entire frontier evidence/generations')
    need(all(type(r) is int and type(generations[r]) is int and generations[r] >= 0
             for r in evidence), 'literal row/generation')
    allowed = ('ZERO', 'SINGLETON', 'MANY', 'TWO_OR_MORE', 'UNKNOWN')
    need(all(type(v) is dict and v.get('status') in allowed for v in evidence.values()),
         'checked or explicitly unresolved local status')
    if not evidence:
        return {'kind': 'SOLVED', 'row': None}
    zero = [r for r in evidence if evidence[r]['status'] == 'ZERO']
    if zero:
        return {'kind': 'DEAD', 'row': min(zero)}
    unknown = sorted(r for r in evidence if evidence[r]['status'] == 'UNKNOWN')
    if unknown:
        return {'kind': 'UNKNOWN', 'row': None, 'unresolved_rows': unknown}
    forced = [r for r in evidence if evidence[r]['status'] == 'SINGLETON']
    row = min(forced if forced else evidence, key=lambda r: (generations[r], r))
    return {'kind': 'FORCED' if forced else 'BRANCH', 'row': row}


def certify_by_current_cover(*, language, state, row, completion,
                             checked_candidates, degree_proposer, semantics, tick):
    """Fresh restricted cover only. No blanket all-six EOF authority is granted."""
    tick()
    proposal = degree_proposer(language=language, state=state, row=row, tick=tick)
    receipt = semantics.check_degree_evidence(language=language, state=state,
                                             row=row, proposal=proposal, tick=tick)
    if not receipt['accepted_local_evidence'] or not receipt['complete_cover_checked']:
        return None
    actual = [canonical(c['placement_key']) for c in checked_candidates]
    expected = [canonical(k) for k in receipt['candidate_keys']]
    need(len(actual) == len(set(actual)) and set(actual) == set(expected),
         'fresh complete cover agrees with entire checked fallback stream')
    need(completion['state_sha256'] == digest(state)
         and receipt['state_sha256'] == digest(state) and receipt['row'] == row
         and receipt['input_epoch'] == language.binding['language_epoch'],
         'fresh completion/cover exact original context')
    tick()
    return receipt


class _Checkpoint:
    __slots__ = ('owner', 'payload')

    def __init__(self, owner, payload):
        self.owner, self.payload = owner, payload


class LazyUnitRowEngine:
    def __init__(self, *, language, degree_proposer, semantics, fallback,
                 certify_fallback, tick, initial_state=None,
                 maximum_nodes=128, maximum_events=2000):
        tick()
        need(semantics.VERSION == SEMANTICS_VERSION, 'selected independent semantics API')
        need(type(maximum_nodes) is int and 0 < maximum_nodes <= 128
             and type(maximum_events) is int and 0 < maximum_events <= 2000,
             'unchanged node/event ceilings')
        self.language, self.semantics, self.tick = language, semantics, tick
        self.degree_proposer, self.fallback = degree_proposer, fallback
        self.certify_fallback = certify_fallback
        self.maximum_nodes, self.maximum_events = maximum_nodes, maximum_events
        self.events = []
        self.counts = dict(nodes=0, placements=0, forced=0, branches=0, backtracks=0, restores=0,
                           global_scans=0, fallback_advances=0, cursor_replays=0)
        epoch = language.binding['language_epoch']
        if initial_state is None:
            marks = [[[1, k], ['outside', epoch]] for k in range(-23, 0)]
            marks.append([[1, 23], ['formula', canonical(language.target)]])
            initial_state = {'schema': 'unit-row-implicit-private-state-v1',
                'input_epoch': epoch, 'height': 24,
                't': [[[0, r], 0] for r in range(24)], 'm': marks,
                'selected': [], 'excluded': [],
                'generation': [[[0, r], 0] for r in range(24)]}
        self._state = semantics.private_state(language, initial_state, tick)[0]
        self._revision, self._versions = 0, (0,) * 24
        self._certs, self._slots, self._observed, self._reverse = {}, {}, {}, {}
        self._live = {}
        self._refs = self._reference_counts(self._state)

    def _copy(self, value):
        return self.semantics.tree(value, self.tick)

    def _reference_counts(self, state):
        refs = {(1, k): 1 for k in range(-23, 0)}
        refs[(1, 23)] = 1
        for record in state['selected']:
            self.tick()
            tile = self.semantics.rebuild_tile(self.language, record['type_preimage'],
                                              record['translation'], self.tick)
            for point, value in tile['global_m_values']:
                p = tuple(point)
                refs[p] = refs.get(p, 0) + 1
        return refs

    def _emit(self, kind, **data):
        self.tick()
        if len(self.events) >= self.maximum_events:
            raise Unresolved('event ceiling; no exhausted conclusion')
        self.events.append(dict(event=len(self.events), kind=kind,
                                state_sha256=digest(self._state), **diagnostic_copy(data)))

    def _snapshot_value(self):
        return {'state': self._state, 'revision': self._revision,
            'row_versions': list(self._versions),
            'mark_reference_counts': [[list(p), n] for p, n in sorted(self._refs.items())],
            'certificates': [[r, v] for r, v in sorted(self._certs.items())],
            'cursors': [[r, v] for r, v in sorted(self._slots.items())],
            'exposed_candidates': [[k, v] for k, v in sorted(self._observed.items())],
            'reverse_dependencies': [[list(p), sorted(keys)] for p, keys in sorted(self._reverse.items())],
            'implicit_dependencies': {'scope': 'ALL24_CONTEXT_REBIND',
                'rows': [{'row': r, 'positive': [0, r], 'output': [1, r],
                          'read_channel': 1, 'read_interval': [-23, r-1],
                          'offset_channels': [[2, r], [3, r]]} for r in range(24)]}}

    def state_snapshot(self):
        """Logical state includes cursor positions; live iterators are disposable."""
        return self._copy(self._snapshot_value())

    def checkpoint(self):
        # These containers are copy-on-write. No mutable iterator is authority.
        return _Checkpoint(self, (self._state, self._revision, self._versions,
            self._refs, self._certs, self._slots, self._observed, self._reverse))

    def rollback(self, token):
        """No callback/replay needed for restoration after an exhausted budget."""
        need(type(token) is _Checkpoint and token.owner is self, 'owned checkpoint')
        (self._state, self._revision, self._versions, self._refs, self._certs,
         self._slots, self._observed, self._reverse) = token.payload
        self._live = {}  # Lazily reopen and verify the saved full prefix on use.

    def _install(self, state, change):
        checked = self.semantics.private_state(self.language, state, self.tick)[0]
        refs = self._reference_counts(checked)
        self._state, self._refs = checked, refs
        self._revision += 1
        self._versions = tuple(v+1 for v in self._versions)
        # Exact whole-state-bound certificates include unseen placements. The
        # conservative dependency guard invalidates ALL24 on every change,
        # including removal/revival and changed exclusion context.
        self._certs, self._slots, self._observed, self._reverse, self._live = {}, {}, {}, {}, {}

    def _candidate(self, raw, row):
        raw = self._copy(raw)
        need(type(raw) is dict and type(raw.get('placement_key')) is dict, 'full candidate')
        key = raw['placement_key']
        need(set(key) == {'tile_type_id', 'type_preimage', 'translation'}
             and key['translation'] == [0, row], 'query incident candidate')
        s, t, m, selected, excluded, names = self.semantics.private_state(
            self.language, self._state, self.tick)
        tile = self.semantics.rebuild_tile(self.language, key['type_preimage'],
                                           key['translation'], self.tick)
        self.semantics.check_collision(tile, names)
        need(self.semantics.legality(tile, t, m, selected, excluded) is None,
             'whole original point legality')
        tile = self.semantics.with_obligations(tile, t, self.tick)
        need(canonical(raw) == canonical(tile), 'exact entire candidate/member/point receipt')
        return tile

    def _observe(self, tile):
        encoded = canonical(tile['placement_key'])
        row = tile['placement_key']['translation'][1]
        dependencies = sorted({tuple(p) for p, v in tile['global_t_values'] + tile['global_m_values']})
        observed = dict(self._observed)
        observed[encoded] = {'row': row, 'candidate': tile,
            'incidence': [[[0, row], 1]], 'dependencies': [list(p) for p in dependencies]}
        reverse = dict(self._reverse)
        for point in dependencies:
            reverse[point] = reverse.get(point, frozenset()) | {encoded}
        self._observed, self._reverse = observed, reverse

    def place(self, candidate):
        """Validated transaction API. search(), not this method, enforces policy."""
        need(type(candidate) is dict and type(candidate.get('placement_key')) is dict
             and type(candidate['placement_key'].get('translation')) is list
             and len(candidate['placement_key']['translation']) == 2,
             'placement transaction candidate shape')
        row = candidate['placement_key']['translation'][1]
        tile = self._candidate(candidate, row)
        state = self._copy(self._state)
        t, m = self.semantics.point_map(state['t'], self.tick), self.semantics.point_map(state['m'], self.tick)
        for point, value in tile['global_t_values']:
            t[tuple(point)] += value
        for point, value in tile['global_m_values']:
            self.semantics.agree(m, tuple(point), value)
        state['t'] = [[list(p), v] for p, v in sorted(t.items())]
        state['m'] = [[list(p), v] for p, v in sorted(m.items())]
        state['selected'].append(self._copy(tile['selection_record']))
        self._install(state, 'placement changes complete implicit context')
        self.counts['placements'] += 1
        self._emit('INVALIDATE', reason='placement changes complete implicit context', rows=list(range(24)))
        self._emit('PLACE', row=row, key=tile['placement_key'])

    def _exclude_exhausted(self, candidate):
        state = self._copy(self._state)
        state['excluded'].append(self._copy(candidate['placement_key']))
        self._install(state, 'proved exhausted child; fresh parent exclusion context')
        self._emit('INVALIDATE', reason='proved exhausted child; fresh parent exclusion context', rows=list(range(24)))
        self._emit('EXCLUDE', key=candidate['placement_key'], reason='CHILD_EXHAUSTED')

    def _open(self, row):
        cursor = self.fallback(language=self.language, state=self._copy(self._state),
                               row=row, tick=self.tick)
        context = self._copy(cursor.context())
        fields = {'schema', 'version', 'input_epoch', 'language_binding', 'row',
                  'state', 'state_sha256', 'context_sha256'}
        need(type(context) is dict and set(context) == fields
             and context['schema'] == 'unit-row-all-six-fallback-context-v1'
             and context['version'] == FALLBACK_VERSION
             and context['input_epoch'] == self._state['input_epoch']
             and context['language_binding'] == self.language.binding
             and type(context['row']) is int and context['row'] == row
             and canonical(context['state']) == canonical(self._state)
             and context['state_sha256'] == digest(self._state), 'fresh full fallback context')
        plain = {k: v for k, v in context.items() if k != 'context_sha256'}
        need(context['context_sha256'] == digest(plain), 'whole context digest')
        return cursor, context

    def _advance(self, cursor, context, ordinal):
        self.tick()
        self.counts['fallback_advances'] += 1
        event = self._copy(cursor.advance())
        base = {'schema', 'kind', 'context_sha256'}
        need(type(event) is dict and event.get('schema') == 'unit-row-all-six-fallback-event-v1'
             and event.get('context_sha256') == context['context_sha256'], 'fallback event context')
        if event.get('kind') == 'CANDIDATE':
            need(set(event) == base | {'ordinal', 'candidate', 'independently_checked'}
                 and type(event['ordinal']) is int and event['ordinal'] == ordinal
                 and event['independently_checked'] is False, 'literal candidate ordinal/untrusted marker')
            return self._candidate(event['candidate'], context['row']), None
        need(event.get('kind') == 'EOF' and set(event) == base | {'completion'}, 'explicit EOF event')
        completion = event['completion']
        fields = {'schema', 'version', 'context_sha256', 'state_sha256', 'input_epoch',
                  'row', 'yielded_candidates', 'rules_completed', 'stats', 'complete_fallback_proposed',
                  'independently_checked', 'degree_zero_or_singleton_accepted',
                  'complete_candidate_graph_accepted', 'scheduler_or_rollback_accepted',
                  'logical_proof_accepted', 'ROOT_resource_accepted'}
        need(type(completion) is dict and set(completion) == fields
             and completion['schema'] == 'unit-row-all-six-fallback-completion-v1'
             and completion['version'] == FALLBACK_VERSION
             and completion['context_sha256'] == context['context_sha256']
             and completion['state_sha256'] == context['state_sha256']
             and completion['input_epoch'] == context['input_epoch']
             and type(completion['row']) is int and completion['row'] == context['row']
             and type(completion['yielded_candidates']) is int and completion['yielded_candidates'] == ordinal
             and completion['rules_completed'] == RULES and type(completion['stats']) is dict
             and completion['complete_fallback_proposed'] is True
             and all(completion[k] is False for k in ('independently_checked',
                 'degree_zero_or_singleton_accepted', 'complete_candidate_graph_accepted',
                 'scheduler_or_rollback_accepted', 'logical_proof_accepted', 'ROOT_resource_accepted')),
             'complete but untrusted six-rule EOF receipt')
        return None, completion

    def next_alternative(self, row):
        """Return checked candidate or untrusted EOF, retaining a logical cursor."""
        need(type(row) is int and 0 <= row < 24, 'literal cursor row')
        slot = self._slots.get(row)
        if slot is not None and slot['completion'] is not None:
            return {'kind': 'EOF', 'completion': self._copy(slot['completion'])}
        live = self._live.get(row)
        if live is None:
            cursor, context = self._open(row)
            if slot is None:
                slot = {'context': context, 'keys': [], 'candidates': [], 'completion': None}
            else:
                need(canonical(slot['context']) == canonical(context), 'rollback cursor exact context')
                for ordinal, key in enumerate(slot['keys']):
                    tile, completion = self._advance(cursor, context, ordinal)
                    need(completion is None and canonical(tile['placement_key']) == canonical(key),
                         'replayed entire canonical cursor prefix')
                    self.counts['cursor_replays'] += 1
            self._live[row] = cursor
        else:
            cursor, context = live, slot['context']
        ordinal = len(slot['keys'])
        tile, completion = self._advance(cursor, context, ordinal)
        new_slot = dict(slot)
        if tile is not None:
            key = tile['placement_key']
            need(all(canonical(k) != canonical(key) for k in slot['keys']), 'unique complete fallback keys')
            new_slot['keys'] = slot['keys'] + [self._copy(key)]
            new_slot['candidates'] = slot['candidates'] + [tile]
            self._observe(tile)
        else:
            new_slot['completion'] = completion
        slots = dict(self._slots)
        slots[row] = new_slot
        self._slots = slots
        self._emit('FALLBACK', row=row, ordinal=ordinal, result='EOF' if completion is not None else 'CANDIDATE')
        return {'kind': 'EOF', 'completion': self._copy(completion)} if completion is not None else {'kind': 'CANDIDATE', 'candidate': self._copy(tile)}

    def _fallback_degree(self, row):
        # Prefix witnesses prove >=2. A short EOF is never its own certificate.
        while True:
            slot = self._slots.get(row)
            if slot is not None and len(slot['keys']) >= 2:
                return {'status': 'TWO_OR_MORE', 'state_sha256': digest(self._state),
                        'row': row, 'candidate_keys': self._copy(slot['keys'][:2]),
                        'accepted_local_evidence': True, 'complete_cover_checked': False,
                        'sole_candidate': None, 'degree_exact': None}
            item = self.next_alternative(row)
            if item['kind'] != 'EOF':
                continue
            if self.certify_fallback is None:
                return {'status': 'UNKNOWN'}
            slot = self._slots[row]
            receipt = self.certify_fallback(language=self.language,
                state=self._copy(self._state), row=row, completion=self._copy(item['completion']),
                checked_candidates=self._copy(slot['candidates']), tick=self.tick)
            if receipt is None:
                return {'status': 'UNKNOWN'}
            self._validate_receipt(receipt, row, require_cover=True)
            need({canonical(k) for k in receipt['candidate_keys']} ==
                 {canonical(k) for k in slot['keys']}, 'certified EOF agrees with complete checked stream')
            return receipt

    def _validate_receipt(self, receipt, row, require_cover=False):
        need(type(receipt) is dict and receipt.get('schema') == 'unit-row-degree-evidence-check-v2'
             and receipt.get('state_sha256') == digest(self._state)
             and receipt.get('input_epoch') == self._state['input_epoch']
             and type(receipt.get('row')) is int and receipt['row'] == row
             and all(receipt.get(k) is False for k in ('complete_candidate_graph_accepted',
                  'scheduler_or_rollback_accepted', 'logical_proof_accepted', 'ROOT_resource_accepted')),
             'checked local receipt exact current context')
        need(receipt['status'] in ('ZERO', 'SINGLETON', 'MANY', 'TWO_OR_MORE', 'UNKNOWN')
             and receipt['accepted_local_evidence'] is (receipt['status'] != 'UNKNOWN'), 'checked local status')
        if require_cover:
            need(receipt['complete_cover_checked'] is True
                 and receipt['status'] in ('ZERO', 'SINGLETON', 'MANY'), 'independent completed cover required')

    def decision(self):
        self.tick()
        state, totals, marks, selected, excluded, names = self.semantics.private_state(
            self.language, self._state, self.tick)
        frontier = [r for r in range(24) if totals[(0, r)] == 0]
        self.counts['global_scans'] += 1
        certificates = {}
        # First inspect every cheap local query, so a later certified dead point
        # is not hidden behind an earlier unresolved fallback.
        for row in frontier:
            self.tick()
            proposal = self.degree_proposer(language=self.language,
                state=self._copy(self._state), row=row, tick=self.tick)
            receipt = self.semantics.check_degree_evidence(language=self.language,
                state=self._copy(self._state), row=row, proposal=proposal, tick=self.tick)
            self._validate_receipt(receipt, row)
            certificates[row] = self._copy(receipt)
            for raw in proposal['candidates']:
                self._observe(self._candidate(raw, row))
            if receipt['status'] == 'ZERO':
                self._certs = certificates
                result = {'kind': 'DEAD', 'row': row}
                self._emit('DECISION', decision=result,
                           statuses=[[r, v['status']] for r, v in certificates.items()],
                           evidence=[[r, v] for r, v in certificates.items()])
                return result
        for row in frontier:
            if certificates[row]['status'] == 'UNKNOWN':
                certificates[row] = self._fallback_degree(row)
                if certificates[row]['status'] == 'ZERO':
                    break
        self._certs = certificates
        result = select_schedule(evidence=certificates,
            generations={r: 0 for r in frontier}, tick=self.tick)
        if result['kind'] == 'FORCED':
            result['candidate'] = self._copy(certificates[result['row']]['sole_candidate'])
        self._emit('DECISION', decision=result,
                   statuses=[[r, v['status']] for r, v in certificates.items()],
                   evidence=[[r, v] for r, v in certificates.items()])
        return result

    def _word(self):
        state = self.semantics.private_state(self.language, self._state, self.tick)[0]
        totals = self.semantics.point_map(state['t'], self.tick)
        need(all(v == 1 for v in totals.values()), 'entire original target, not a partial endpoint')
        records = sorted(state['selected'], key=lambda x: x['translation'][1])
        need([r['translation'][1] for r in records] == list(range(24)), 'exactly one original placement per row')
        word = []
        for row, record in enumerate(records):
            self.tick()
            pre = record['type_preimage']
            command = self._copy(pre['primitive_witness'])
            refs = [row+d for d in pre['ordered_offsets']]
            if command['rule'] == 'mp':
                command.update(antecedent=refs[0], implication=refs[1])
            elif command['rule'] == 'generalize':
                command['source'] = refs[0]
            word.append(command)
        return word

    def search(self):
        """Full rollback on FOUND/UNKNOWN too; only exhausted child permits exclusion."""
        before = self.state_snapshot()
        root = self.checkpoint()
        found, reason, last_state = None, None, None

        def walk(depth):
            nonlocal found, last_state
            while True:
                self.tick()
                if self.counts['nodes'] >= self.maximum_nodes:
                    raise Unresolved('node ceiling; no exhausted conclusion')
                self.counts['nodes'] += 1
                decision = self.decision()
                kind = decision['kind']
                if kind == 'DEAD':
                    return 'EXHAUSTED'
                if kind == 'UNKNOWN':
                    last_state = diagnostic_copy(self._state)
                    return 'UNKNOWN'
                if kind == 'SOLVED':
                    found = {'state': self._copy(self._state), 'word_proposal': self._word()}
                    return 'POINT_BOARD_PROPOSAL'
                row = decision['row']
                if kind == 'FORCED':
                    candidate = decision['candidate']
                    self.counts['forced'] += 1
                else:
                    self.counts['branches'] += 1
                    slot = self._slots.get(row)
                    if slot is not None and slot['candidates']:
                        candidate = self._copy(slot['candidates'][0])
                    else:
                        item = self.next_alternative(row)
                        if item['kind'] == 'EOF':
                            raise Unresolved('no canonical branch alternative; EOF is not pruning authority')
                        candidate = item['candidate']
                checkpoint = self.checkpoint()
                self._emit('TRY', depth=depth, row=row, mode=kind, key=candidate['placement_key'])
                try:
                    self.place(candidate)
                    child = walk(depth+1)
                except TimeoutError:
                    if last_state is None:
                        last_state = diagnostic_copy(self._state)
                    raise
                finally:
                    self.rollback(checkpoint)
                    self.counts['restores'] += 1
                if child == 'EXHAUSTED':
                    self.counts['backtracks'] += 1
                self._emit('RESTORE', depth=depth, row=row, child_status=child,
                           key=candidate['placement_key'])
                if child != 'EXHAUSTED' or kind == 'FORCED':
                    return child
                self._exclude_exhausted(candidate)
                # A new exclusion is a new context. Recheck EVERY frontier
                # before any sibling; do not reuse its old parent iterator.

        try:
            status = walk(0)
        except TimeoutError as error:
            status, reason = 'UNKNOWN', str(error)
            if last_state is None:
                last_state = diagnostic_copy(self._state)
        finally:
            self.rollback(root)
        after = diagnostic_copy(self._snapshot_value())
        need(canonical(before) == canonical(after), 'exact root semantic/cursor/dependency rollback')
        if status == 'UNKNOWN' and reason is None:
            reason = 'unresolved local degree or unaccepted fallback completion'
        if status != 'UNKNOWN':
            self.tick()
        return {'schema': 'unit-row-lazy-global-search-result-v1', 'version': VERSION,
            'variant': VARIANT, 'status': status, 'reason': reason,
            'input_epoch': self._state['input_epoch'], 'root_restored': True,
            'stack_restored': True, 'last_observed_state': last_state,
            'root_snapshot_sha256': digest(before), 'final_snapshot_sha256': digest(after),
            'found': found, 'events': diagnostic_copy(self.events), 'counts': dict(self.counts),
            'trace_complete': status != 'UNKNOWN',
            'logical_proof_accepted': False, 'exact_point_board_accepted': False,
            'complete_candidate_graph_accepted': False, 'trajectory_accepted': False,
            'GCTS_advantage_accepted': False, 'RL_accepted': False,
            'ROOT_resource_accepted': False}
