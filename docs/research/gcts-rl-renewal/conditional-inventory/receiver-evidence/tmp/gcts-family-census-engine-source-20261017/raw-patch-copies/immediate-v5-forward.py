"""SOURCE ONLY unit-row engine, explicit owned earliest-generation BRANCH tie.

No project imports or clocks. Optional post-BRANCH goal-ordering preferences.
Caller authenticates language, current semantics,
proposer and complete fallback Sources. EOF alone never proves zero/exhaustion.
"""
import hashlib
import json

VERSION = 'lazy-unit-row-global-engine-v13-receptor-family-preferences-v5-full-exposure-census-provider6'
FAMILY_PROVIDER_SCHEMA = 'receptor-family-observed-receptor-transfer-provider-v2'
FAMILY_PROVIDER_VERSION = 'receptor-family-observed-receptor-transfer-provider-v6'
OBSERVED_PRODUCER_IMPLEMENTATION = 'receptor-family-observed-subset-inference-v2'
CURSOR_CENSUS_IMPLEMENTATION = 'unit-row-channel4-point-adapter-public-prefix-census-v5'
VARIANT = 'GLOBAL-DEAD-FORCED-EARLIEST-GENERATION-ROW-TIE-SUPPORT-RETENTION-ROUTED-NONIMP-EVIDENCE'
MARK_VARIANT = 'GLOBAL-DEAD-FORCED-EARLIEST-GENERATION-ASSIGNED-OUTPUT-THEN-ROW-SUPPORT-RETENTION-ROUTED-NONIMP-EVIDENCE'
BRANCH_TIES = ('ROW', 'ASSIGNED-OUTPUT-THEN-ROW')
SEMANTICS_VERSION = 'unit-row-channel4-routed-nonimp-degree-semantics-v2'
FALLBACK_VERSION = 'unit-row-channel4-filtered-six-rule-fallback-v1'
TRANSITION_VERSION = 'unit-row-channel4-routed-support-transition-v2'
ADVISER_VERSION = 'unit-row-generic-goal-branch-adviser-v3-compatible-source-fibres'
ADVICE_VALIDATOR_VERSION = 'unit-row-independent-advice-consumer-validator-v3-compatible-fibres-versions'
ADVICE_FLAGS = ('logical_proof_accepted', 'exact_point_board_accepted',
    'degree_or_EOF_accepted', 'scheduler_accepted', 'complete_GCTS_model_accepted',
    'trajectory_accepted', 'learned_marking_accepted', 'RL_accepted', 'ROOT_resource_accepted')
HINT_REJECTION_REASONS = ('already_selected', 'branch_excluded_complete_key',
    'whole_support_capacity', 'whole_remote_or_metadata_mark_conflict')
ADVICE_FAMILY_REJECTION_POLICY = 'ABANDON_WHOLE_FAMILY_ON_DEFINITE_CURRENT_PENDING_REJECTION'
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


def select_schedule(*, evidence, generations, tick, branch_tie='ROW',
                    assigned_output_rows=None):
    """Only BRANCH ties use marks; varied-generation controls are NONLOGICAL."""
    tick()
    need(type(branch_tie) is str and branch_tie in BRANCH_TIES, 'named branch tie')
    need(type(evidence) is dict and type(generations) is dict
         and set(evidence) == set(generations), 'entire frontier evidence/generations')
    need(all(type(r) is int and type(generations[r]) is int and generations[r] >= 0
             for r in evidence), 'literal row/generation')
    assigned_output_rows = [] if assigned_output_rows is None else assigned_output_rows
    need(type(assigned_output_rows) is list
         and all(type(r) is int and r in evidence for r in assigned_output_rows)
         and len(assigned_output_rows) == len(set(assigned_output_rows)),
         'literal distinct assigned-output frontier rows')
    assigned = set(assigned_output_rows)
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
    if forced:
        return {'kind': 'FORCED',
                'row': min(forced, key=lambda r: (generations[r], r))}
    row = min(evidence, key=lambda r: (generations[r],
        0 if branch_tie == 'ASSIGNED-OUTPUT-THEN-ROW' and r in assigned else 1, r))
    return {'kind': 'BRANCH', 'row': row}


def validate_native_receipt(*, receipt, language, semantics, state, row, tick, require_cover=False):
    """Protocol/context checks only; never call this on engine-owned transfers/prefixes."""
    tick()
    flags = {'complete_candidate_graph_accepted','scheduler_or_rollback_accepted',
             'logical_proof_accepted','ROOT_resource_accepted'}
    common = {'schema','version','status','accepted_local_evidence','input_epoch',
        'marking_id','state_sha256','row','complete_cover_checked','degree_exact',
        'candidate_keys','sole_candidate','scope'} | flags
    legacy = common | {'missing_mark_cover_checked','original_base_receipt','marked_rejections'}
    new = common | {'nonimp_fibre_cover_checked','checked_candidates','checked_root_rejections',
        'checked_fibre_cover','state','original_state','original_state_sha256',
        'output_formula','language_binding','marking_sha256','independent_marked_state_check','proposal_sha256'}
    need(type(receipt) is dict, 'native local receipt dictionary')
    is_new = receipt.get('schema') == 'unit-row-marked-aware-nonimp-fibre-check-v1'
    need((is_new and set(receipt) == new
              and receipt['version'] == 'unit-row-independent-marked-aware-nonimp-fibre-checker-v1')
         or (not is_new and set(receipt) == legacy
              and receipt.get('schema') == 'unit-row-channel4-degree-evidence-check-v1'
              and receipt['version'] == 'unit-row-channel4-filtered-degree-semantics-v1'),
         'exact native receipt union, never a normalized or transferred header')
    need(receipt['marking_id'] == state['marking_id']
         and receipt['state_sha256'] == digest(state)
         and receipt['input_epoch'] == state['input_epoch'] == language.binding['language_epoch']
         and type(receipt['row']) is int and receipt['row'] == row
         and all(receipt[k] is False for k in flags), 'checked local receipt exact current context')
    status, covered, keys = receipt['status'], receipt['complete_cover_checked'], receipt['candidate_keys']
    need(type(status) is str and status in ('ZERO','SINGLETON','MANY','TWO_OR_MORE','UNKNOWN')
         and receipt['accepted_local_evidence'] is (status != 'UNKNOWN')
         and type(covered) is bool and type(keys) is list, 'literal status/completion/key list')
    encoded = []
    for key in keys:
        tick()
        need(type(key) is dict and set(key) == {'tile_type_id','type_preimage','translation'}
             and key['translation'] == [0,row], 'full incident native candidate key')
        pre = key['type_preimage']
        need(type(pre) is dict and set(pre) == {'schema','base_type_preimage','marking_id'}
             and pre['schema'] == 'unit-row-row0-decorated-type-v1'
             and pre['marking_id'] == state['marking_id']
             and pre['base_type_preimage']['input_epoch'] == state['input_epoch'],
             'unchanged decorated/original key provenance')
        encoded.append(canonical(key))
    need(len(encoded) == len(set(encoded)), 'unique full native candidate keys')
    count, sole = receipt['degree_exact'], receipt['sole_candidate']
    if covered:
        need(type(count) is int and count == len(keys)
             and status == ('ZERO' if count == 0 else 'SINGLETON' if count == 1 else 'MANY'),
             'complete native count/classification coherence')
        if count == 1:
            need(type(sole) is dict and canonical(sole['placement_key']) == encoded[0],
                 'complete current sole packet/key')
        else:
            need(sole is None, 'no sole packet outside exact singleton')
    else:
        need(count is None and sole is None
             and ((status == 'TWO_OR_MORE' and len(keys) >= 2)
                  or (status == 'UNKNOWN' and len(keys) <= 1)), 'partial bound is not completion')
    if is_new:
        original = semantics.base_state(language, state, tick)
        model_check = semantics.check_marking(language, tick)
        need(canonical(receipt['state']) == canonical(state)
             and canonical(receipt['original_state']) == canonical(original)
             and receipt['original_state_sha256'] == digest(original)
             and canonical(receipt['language_binding']) == canonical(language.binding)
             and receipt['marking_sha256'] == digest(model_check['marking']),
             'new receipt literal marked/original state, authority and full marking digest')
        need(receipt['nonimp_fibre_cover_checked'] is covered
             and type(receipt['checked_candidates']) is list
             and [canonical(c['placement_key']) for c in receipt['checked_candidates']] == encoded
             and type(receipt['checked_root_rejections']) is list,
             'new native checked candidate packets and nonimp coverage flag')
        if covered:
            need(type(receipt['checked_fibre_cover']) is dict
                 and receipt['checked_fibre_cover']['completed'] is True,
                 'new completed census retained in native receipt')
        else:
            need(receipt['checked_fibre_cover'] is None and len(keys) == (2 if status == 'TWO_OR_MORE' else len(keys)),
                 'new partial transcript is not independently completed census')
        output = receipt['output_formula']
        need(type(output) is list and output and output[0] != 'imp'
             and [v for p,v in state['m'] if p == [1,row]] == [['formula',canonical(output)]],
             'new native evidence belongs to current assigned nonimp route')
        check = receipt['independent_marked_state_check']
        need(check['marked_state_checked'] is True and check['marking_id'] == state['marking_id']
             and check['original_state_sha256'] == digest(original), 'new full independent marked state check')
    else:
        need(type(receipt['missing_mark_cover_checked']) is bool
             and type(receipt['original_base_receipt']) is dict
             and type(receipt['marked_rejections']) is list, 'legacy native origin remains legacy')
    if require_cover:
        need(covered and status in ('ZERO','SINGLETON','MANY'), 'independent completed cover required')
    tick()


def certify_by_current_cover(*, language, state, row, completion,
                             checked_candidates, degree_proposer, semantics, tick):
    """Fresh restricted cover only. No blanket all-six EOF authority is granted."""
    tick()
    proposal = degree_proposer(language=language, state=state, row=row, tick=tick)
    receipt = semantics.check_degree_evidence(language=language, state=state,
                                             row=row, proposal=proposal, tick=tick)
    validate_native_receipt(receipt=receipt, language=language, semantics=semantics,
        state=state, row=row, tick=tick)
    if not receipt['accepted_local_evidence'] or not receipt['complete_cover_checked']:
        return None
    actual = [canonical(c['placement_key']) for c in checked_candidates]
    expected = [canonical(k) for k in receipt['candidate_keys']]
    need(len(actual) == len(set(actual)) and len(expected) == len(set(expected))
         and set(actual) == set(expected),
         'fresh complete cover agrees with entire checked fallback stream')
    need(completion['state_sha256'] == digest(state)
         and receipt['state_sha256'] == digest(state) and receipt['row'] == row
         and receipt['input_epoch'] == language.binding['language_epoch']
         and completion['marking_id'] == state['marking_id']
         and receipt['marking_id'] == state['marking_id'],
         'fresh completion/cover exact original context')
    tick()
    return receipt


class _Checkpoint:
    __slots__ = ('owner', 'payload')

    def __init__(self, owner, payload):
        self.owner, self.payload = owner, payload


class LazyUnitRowEngine:
    def __init__(self, *, language, degree_proposer, semantics, fallback,
                 certify_fallback, transition_checker, tick, initial_state=None,
                 maximum_nodes=128, maximum_events=2000,
                 branch_adviser=None, validate_advice=None, branch_tie='ROW',
                 family_proposer=None, family_consumer=None,
                 initial_prototype_census=None):
        tick()
        need(type(branch_tie) is str and branch_tie in BRANCH_TIES, 'named branch tie')
        self._branch_tie = branch_tie
        need(semantics.VERSION == SEMANTICS_VERSION, 'selected independent semantics API')
        need(type(maximum_nodes) is int and 0 < maximum_nodes <= 128
             and type(maximum_events) is int and 0 < maximum_events <= 2000,
             'unchanged node/event ceilings')
        self.language, self.semantics, self.tick = language, semantics, tick
        self.degree_proposer, self.fallback = degree_proposer, fallback
        self.certify_fallback = certify_fallback
        need((branch_adviser is None and validate_advice is None)
             or (callable(branch_adviser) and callable(validate_advice)),
             'both optional advice endpoints or neither')
        need(branch_adviser is None and validate_advice is None,
             'initial frozen-channel4 lane has advice disabled in both comparison arms')
        self.branch_adviser, self.validate_advice = branch_adviser, validate_advice
        self._preferences = None
        need((family_proposer is None and family_consumer is None)
             or (callable(family_proposer) and callable(family_consumer)),
             'both optional checked family endpoints or neither')
        self.family_proposer, self.family_consumer = family_proposer, family_consumer
        self._family_callbacks = (family_proposer, family_consumer)
        need(transition_checker.VERSION == TRANSITION_VERSION, 'selected transition checker')
        self.transition_checker = transition_checker
        self._authority = canonical(transition_checker.authority_snapshot(
            language=language, semantics=semantics, tick=tick))
        self._scheduler_policy = canonical({'schema': 'unit-row-owned-branch-tie-policy-v1',
            'branch_tie': branch_tie, 'original_authority': self._authority})
        self._last_transition = None
        self.maximum_nodes, self.maximum_events = maximum_nodes, maximum_events
        self.events = []
        self.counts = dict(nodes=0, placements=0, forced=0, branches=0, backtracks=0, restores=0,
                           global_scans=0, fallback_advances=0, cursor_replays=0,
                           retained_domains=0, invalidated_domains=0, retained_queries=0,
                           retained_prefixes=0, advice_calls=0, advice_unknown=0,
                           advice_selected=0, pending_checks=0, pending_selected=0,
                           pending_rejected=0, pending_retired=0, family_abandonments=0,
                           fallback_branch_choices=0, family_batches=0,
                           family_checks=0, family_invalidated=0, family_unknown=0,
                           family_choices=0, family_canonical_choices=0)
        if initial_state is None:
            initial_state = semantics.initial_state(language, tick)
        initial_checked = semantics.private_state(language, initial_state, tick)
        self._state = initial_checked[0]
        self._family_prototype_census = {} if family_proposer is not None else None
        self._family_cursor_censuses = {}
        if self._family_prototype_census is not None:
            self._join_prototype_census([[name, pre] for name, pre in sorted(initial_checked[5].items())])
        if initial_prototype_census is not None:
            initial_prototype_census = self._copy(initial_prototype_census)
            need(type(initial_prototype_census) is list
                 and (family_proposer is not None or initial_prototype_census == []),
                 'explicit exposure seed requires enabled family endpoints')
            self._join_prototype_census(initial_prototype_census)
        self._revision, self._versions = 0, (0,) * 24
        self._certs, self._slots, self._observed, self._reverse = {}, {}, {}, {}
        self._live = {}
        self._refs = self._reference_counts(self._state)

    @property
    def branch_tie(self):
        """Fixed per engine; checkpoint rollback never selects another policy."""
        return self._branch_tie

    def _policy_snapshot(self):
        return {'schema': 'unit-row-owned-branch-tie-policy-v1',
            'branch_tie': self.branch_tie,
            'authority_sha256': hashlib.sha256(self._authority.encode('utf8')).hexdigest(),
            'policy_sha256': hashlib.sha256(self._scheduler_policy.encode('utf8')).hexdigest()}

    def _copy(self, value):
        return self.semantics.tree(value, self.tick)

    def _reference_counts(self, state):
        refs = {(1, k): 1 for k in range(-23, 0)}
        refs[(1, 23)] = 1
        refs[(4, 0)] = 1
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
        return {'schema': 'unit-row-receptor-family-engine-snapshot-v1', 'version': VERSION,
            'state': self._state, 'revision': self._revision,
            'row_versions': list(self._versions),
            'mark_reference_counts': [[list(p), n] for p, n in sorted(self._refs.items())],
            'certificates': [[r, v] for r, v in sorted(self._certs.items())],
            'cursors': [[r, v] for r, v in sorted(self._slots.items())],
            'exposed_candidates': [[k, v] for k, v in sorted(self._observed.items())],
            'reverse_dependencies': [[list(p), sorted(keys)] for p, keys in sorted(self._reverse.items())],
            'last_transition': self._last_transition,
            'pending_preferences': self._preferences,
            'scheduler_policy': self._policy_snapshot(),
            'family_preference_policy': self._family_policy(),
            'family_prototype_census': (None if self._family_prototype_census is None else
                [[name, pre] for name, pre in sorted(self._family_prototype_census.items())]),
            'family_cursor_censuses': [[r, v] for r, v in sorted(self._family_cursor_censuses.items())],
            'marking_id': self._state['marking_id'],
            'authority_sha256': hashlib.sha256(self._authority.encode('utf8')).hexdigest(),
            'implicit_dependencies': {'scope': 'ALL_POSSIBLE_UNIT_ROW_SUPPORT_PLUS_COLLISION_LEDGER',
                'rows': [{'row': r, 'positive': [0, r], 'output': [1, r],
                          'read_channels': [1, 4], 'output_channels': [1, 4],
                          'possible_absolute_mark_rows': [0, r],
                          'read_interval': [-23, r-1],
                          'read_occupancy': [[0, k] for k in range(r)],
                          'local_full_key_exclusions': r,
                          'global_full_preimage_collision_ledger': True,
                          'offset_channels': [[2, r], [3, r]]} for r in range(24)]}}

    def state_snapshot(self):
        """Logical state includes cursor positions; live iterators are disposable."""
        return self._copy(self._snapshot_value())

    def checkpoint(self):
        # These containers are copy-on-write. No mutable iterator is authority.
        return _Checkpoint(self, (self._state, self._revision, self._versions,
            self._refs, self._certs, self._slots, self._observed, self._reverse,
            self._last_transition, self._preferences,
            self._family_prototype_census, self._family_cursor_censuses))

    def rollback(self, token):
        """No callback/replay needed for restoration after an exhausted budget."""
        need(type(token) is _Checkpoint and token.owner is self, 'owned checkpoint')
        (self._state, self._revision, self._versions, self._refs, self._certs,
         self._slots, self._observed, self._reverse, self._last_transition,
         self._preferences, self._family_prototype_census,
         self._family_cursor_censuses) = token.payload
        self._live = {}  # Lazily reopen and verify the saved full prefix on use.

    def _family_policy(self):
        return {'schema': 'receptor-family-owned-preference-policy-v2-full-census',
            'enabled': self.family_proposer is not None,
            'consumer_version': 'receptor-family-primitive-preference-consumer-v2-batch-collision-ledger',
            'provider_schema': FAMILY_PROVIDER_SCHEMA, 'provider_version': FAMILY_PROVIDER_VERSION,
            'cursor_census_implementation': CURSOR_CENSUS_IMPLEMENTATION,
            'type_census_policy': 'OWNED_COPY_ON_WRITE_FULL_PREIMAGE_EXPOSURES',
            'atomic_family_moves': False, 'family_degree_or_exclusion_authority': False}

    def _check_authority(self):
        need(type(self._family_callbacks) is tuple and len(self._family_callbacks) == 2
             and self.family_proposer is self._family_callbacks[0]
             and self.family_consumer is self._family_callbacks[1],
             'fixed constructor family endpoints')
        need(type(self._branch_tie) is str and self._branch_tie in BRANCH_TIES
             and self._scheduler_policy == canonical({
                 'schema': 'unit-row-owned-branch-tie-policy-v1',
                 'branch_tie': self._branch_tie, 'original_authority': self._authority}),
             'immutable owned branch policy and original authority binding')
        need(canonical(self.transition_checker.authority_snapshot(
            language=self.language, semantics=self.semantics, tick=self.tick)) == self._authority,
            'immutable original authority; no cache reuse across authority changes')

    def _transfer_receipt(self, receipt, row, transition, refreshed):
        # Only engine-owned checked origins enter here; native headers stay literal.
        original = receipt.get('original_receipt', receipt)
        protocol = {'schema': original['schema'], 'version': original.get('version')}
        if protocol == {'schema':'unit-row-marked-aware-nonimp-fibre-check-v1',
                        'version':'unit-row-independent-marked-aware-nonimp-fibre-checker-v1'}:
            coverage = {'kind':'MARKED_AWARE_NONIMP_FIBRES',
                'nonimp_fibre_cover_checked':original['nonimp_fibre_cover_checked']}
        elif protocol == {'schema':'unit-row-channel4-degree-evidence-check-v1',
                          'version':'unit-row-channel4-filtered-degree-semantics-v1'}:
            coverage = {'kind':'LEGACY_ORIGINAL_COVER_AND_MARKED_FILTER',
                'missing_mark_cover_checked':original['missing_mark_cover_checked']}
        else:
            need(protocol == {'schema':'unit-row-channel4-checked-prefix-classification-v1','version':None}
                 and original['status'] == 'TWO_OR_MORE'
                 and original['complete_cover_checked'] is False,
                 'owned fallback prefix is a distinct lower-bound protocol')
            coverage = {'kind':'CHECKED_CANONICAL_FALLBACK_PREFIX'}
        current = transition['after_state_sha256']
        need(receipt['state_sha256'] == transition['before_state_sha256']
             and receipt['row'] == row and receipt['input_epoch'] == self._state['input_epoch'],
             'owned checked cache at exact preceding state')
        proof = next(v for v in transition['rows'] if v['row'] == row)
        need(proof['retain'] is True, 'checked sufficient domain equality')
        return {'schema': 'unit-row-channel4-transferred-domain-classification-v2',
            'marking_id': self._state['marking_id'],
            'version': VERSION, 'state_sha256': current, 'row': row,
            'input_epoch': self._state['input_epoch'],
            'status': receipt['status'],
            'accepted_local_evidence': receipt['accepted_local_evidence'],
            'complete_cover_checked': receipt['complete_cover_checked'],
            'degree_exact': receipt['degree_exact'],
            'origin_protocol': protocol, 'origin_coverage': coverage,
            'candidate_keys': self._copy(receipt['candidate_keys']),
            'sole_candidate': (self._copy(refreshed[canonical(receipt['sole_candidate']['placement_key'])])
                               if receipt['sole_candidate'] is not None else None),
            'original_receipt': self._copy(original),
            'previous_evidence_sha256': digest(receipt),
            'transfer_chain': self._copy(receipt.get('transfer_chain', [])) + [{
                'before_state_sha256': transition['before_state_sha256'],
                'after_state_sha256': current, 'transition_sha256': digest(transition)}],
            'transition': dict(transition, rows=[self._copy(proof)]),
            'complete_candidate_graph_accepted': False,
            'scheduler_or_rollback_accepted': False, 'logical_proof_accepted': False,
            'ROOT_resource_accepted': False}

    def _has_archived_context(self, slot):
        for entry in slot.get('context_archive', []):
            self.tick()
            if (canonical(entry['context']) == canonical(slot['context'])
                    and canonical(entry['keys']) == canonical(slot['keys'])
                    and canonical(entry['completion']) == canonical(slot['completion'])):
                self.tick()
                return True
        self.tick()
        return False

    def _archive_context(self, slot):
        """Archive actual old packets before refreshing them, without nesting."""
        self.tick()
        archive = list(slot.get('context_archive', []))
        context = slot['context']
        packet_state = slot.get('retention_current_state', context['state'])
        if canonical(packet_state) != canonical(context['state']):
            # A second retention can precede replay. Its active packets have
            # already been refreshed, so only the first genuine source entry
            # may represent the old cursor. Do not archive refreshed packets
            # under that cursor's old full context.
            need(self._has_archived_context(slot), 'old full context/prefix/EOF already archived')
            self.tick()
            return archive, 0
        entry = {name: self._copy(slot[name])
                 for name in ('context', 'keys', 'candidates', 'completion')}
        encoded = canonical(entry)
        for previous in archive:
            self.tick()
            if canonical(previous) == encoded:
                return archive, 0
        self.tick()
        # Only these four literal fields: never a slot, archive or history.
        return archive + [entry], 1

    def _install(self, state, change):
        # Prepare everything before installation. Each kept domain has a
        # literal sufficient-dependency proof, including unseen candidates.
        transition = self.transition_checker.check_transition(
            language=self.language, semantics=self.semantics, before=self._state,
            after=state, rows=list(range(24)), authority=self._authority, tick=self.tick)
        checked = self.semantics.private_state(self.language, state, self.tick)[0]
        refs = self._reference_counts(checked)
        kept = {v['row'] for v in transition['rows'] if v['retain']}
        known = {}

        def remember(tile):
            self.tick()
            encoded = canonical(tile['placement_key'])
            need(encoded not in known or canonical(known[encoded]) == canonical(tile),
                 'same full key has one preceding-state packet')
            known[encoded] = tile

        for record in self._observed.values():
            if record['row'] in kept:
                remember(record['candidate'])
        for r, slot in self._slots.items():
            if r in kept:
                for tile in slot['candidates']:
                    remember(tile)
        for r, receipt in self._certs.items():
            if r in kept and receipt.get('sole_candidate') is not None:
                remember(receipt['sole_candidate'])
        refreshed = self.transition_checker.refresh_candidates(
            language=self.language, semantics=self.semantics, state=checked,
            candidates=list(known.values()), tick=self.tick)
        refreshed = {canonical(tile['placement_key']): tile for tile in refreshed}
        need(set(refreshed) == set(known), 'full retained known-key set refreshed')
        certs = {r: self._transfer_receipt(v, r, transition, refreshed)
                 for r, v in self._certs.items() if r in kept and v['status'] != 'UNKNOWN'}
        slots = {}
        archive_total = sum(len(v.get('context_archive', []))
                            for r, v in self._slots.items() if r in kept)
        for r, slot in self._slots.items():
            self.tick()
            if r in kept:
                archive, added = self._archive_context(slot)
                if archive_total + added > self.maximum_events:
                    raise Unresolved('cursor archive entry ceiling; no exhausted conclusion')
                archive_total += added
                # Preserve original context/EOF bytes; no context SHA relabel.
                # Resume opens the genuine new context and checks the ENTIRE
                # retained prefix again before requesting its next element.
                slots[r] = dict(slot, context_archive=archive,
                    retention_current_state_sha256=transition['after_state_sha256'],
                    retention_current_state=checked,
                    original_prefix_candidates=slot.get('original_prefix_candidates', slot['candidates']),
                    candidates=[refreshed[canonical(tile['placement_key'])] for tile in slot['candidates']],
                    candidate_packets_state_sha256=transition['after_state_sha256'],
                    retention_transition=self._copy(transition),
                    retention_chain=self._copy(slot.get('retention_chain', [])) + [{
                        'before_state_sha256': transition['before_state_sha256'],
                        'after_state_sha256': transition['after_state_sha256'],
                        'transition_sha256': digest(transition)}])
        observed = {k: dict(v, candidate=refreshed[k])
                    for k, v in self._observed.items() if v['row'] in kept}
        reverse = {}
        for key, record in observed.items():
            self.tick()
            for raw_point in record['dependencies']:
                point = tuple(raw_point)
                reverse[point] = reverse.get(point, frozenset()) | {key}
        versions = tuple(v if r in kept else v+1 for r, v in enumerate(self._versions))
        self._state, self._refs = checked, refs
        self._revision += 1
        self._versions = versions
        self._certs, self._slots, self._observed, self._reverse = certs, slots, observed, reverse
        self._live = {}  # Native generators are disposable, not domain authority.
        self._last_transition = transition
        self.counts['retained_domains'] += len(kept)
        self.counts['invalidated_domains'] += 24-len(kept)
        self.counts['retained_prefixes'] += len(slots)

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
        self._record_family_tile_census(tile)
        return tile

    def _candidate_from_decision_context(self, raw, row, checked, current):
        """Only the immediate fresh-proposal loop owns this checked tuple/guard."""
        current()
        raw = self._copy(raw)
        current()
        need(type(raw) is dict and type(raw.get('placement_key')) is dict, 'full candidate')
        key = raw['placement_key']
        need(set(key) == {'tile_type_id', 'type_preimage', 'translation'}
             and key['translation'] == [0, row], 'query incident candidate')
        state, t, m, selected, excluded, names = checked
        tile = self.semantics.rebuild_tile(self.language, key['type_preimage'],
                                           key['translation'], self.tick)
        current()
        # Fresh _candidate rebuilt this ledger for each candidate. Do not let one
        # offered candidate change the checked state ledger for the next one.
        self.semantics.check_collision(tile, dict(names))
        current()
        need(self.semantics.legality(tile, t, m, selected, excluded) is None,
             'whole original point legality')
        current()
        tile = self.semantics.with_obligations(tile, t, self.tick)
        current()
        need(canonical(raw) == canonical(tile), 'exact entire candidate/member/point receipt')
        current()
        self._record_family_tile_census(tile)
        current()
        return tile

    def _observe(self, tile):
        encoded = canonical(tile['placement_key'])
        row = tile['placement_key']['translation'][1]
        name = tile['placement_key']['tile_type_id']
        preimage = canonical(tile['placement_key']['type_preimage'])
        base = tile['base_tile']['placement_key']
        base_name = base['tile_type_id']
        base_preimage = canonical(base['type_preimage'])
        for record in self._observed.values():
            self.tick()
            old = record['candidate']['placement_key']
            need(old['tile_type_id'] != name or canonical(old['type_preimage']) == preimage,
                 'exposed prototype digest/full-preimage collision')
            old_base = record['candidate']['base_tile']['placement_key']
            need(old_base['tile_type_id'] != base_name
                 or canonical(old_base['type_preimage']) == base_preimage,
                 'exposed original prototype digest/full-preimage collision')
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
        self._emit('INVALIDATE', reason='placement changes checked dependency slices',
            rows=[v['row'] for v in self._last_transition['rows'] if not v['retain']],
            retained_rows=[v['row'] for v in self._last_transition['rows'] if v['retain']],
            transition=self._last_transition)
        self._emit('PLACE', row=row, key=tile['placement_key'])

    def _exclude_exhausted(self, candidate):
        state = self._copy(self._state)
        state['excluded'].append(self._copy(candidate['placement_key']))
        self._install(state, 'proved exhausted child; fresh parent exclusion context')
        self._emit('INVALIDATE', reason='proved exhausted child; checked exclusion dependencies',
            rows=[v['row'] for v in self._last_transition['rows'] if not v['retain']],
            retained_rows=[v['row'] for v in self._last_transition['rows'] if v['retain']],
            transition=self._last_transition)
        self._emit('EXCLUDE', key=candidate['placement_key'], reason='CHILD_EXHAUSTED')

    def _open(self, row):
        cursor = self.fallback(language=self.language, state=self._copy(self._state),
                               row=row, tick=self.tick)
        context = self._copy(cursor.context())
        fields = {'schema', 'version', 'input_epoch', 'language_binding', 'row',
                  'state', 'state_sha256', 'context_sha256', 'marking_id', 'original_context'}
        need(type(context) is dict and set(context) == fields
             and context['schema'] == 'unit-row-channel4-fallback-context-v1'
             and context['marking_id'] == self._state['marking_id']
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
        need(type(event) is dict and event.get('schema') == 'unit-row-channel4-fallback-event-v1'
             and event.get('context_sha256') == context['context_sha256'], 'fallback event context')
        self._join_family_cursor_census(cursor, context, event, ordinal)
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
                  'logical_proof_accepted', 'ROOT_resource_accepted', 'marking_id', 'original_completion'}
        need(type(completion) is dict and set(completion) == fields
             and completion['schema'] == 'unit-row-channel4-fallback-completion-v1'
             and completion['marking_id'] == self._state['marking_id']
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
        """Keep logical prefixes; replay into a genuine new full context."""
        self._check_authority()
        need(type(row) is int and 0 <= row < 24, 'literal cursor row')
        slot = self._slots.get(row)
        current_sha = digest(self._state)
        same_context = slot is not None and canonical(slot['context']['state']) == canonical(self._state)
        if same_context and slot['completion'] is not None:
            return {'kind': 'EOF', 'completion': self._copy(slot['completion'])}
        live = self._live.get(row)
        if live is None:
            cursor, context = self._open(row)
            if slot is None:
                slot = {'context': context, 'keys': [], 'candidates': [], 'completion': None}
            else:
                if same_context:
                    need(canonical(slot['context']) == canonical(context), 'rollback cursor exact context')
                else:
                    need(slot.get('retention_current_state_sha256') == current_sha
                         and canonical(slot.get('retention_current_state')) == canonical(self._state),
                         'owned checked cursor-domain transition')
                    need(self._has_archived_context(slot),
                         'retained original context/prefix/EOF survives fresh replay')
                    self.tick()
                for ordinal, key in enumerate(slot['keys']):
                    tile, completion = self._advance(cursor, context, ordinal)
                    need(completion is None and canonical(tile['placement_key']) == canonical(key)
                         and canonical(tile) == canonical(slot['candidates'][ordinal]),
                         'replayed entire ordered full candidate prefix in genuine current context')
                    self.counts['cursor_replays'] += 1
                # Old context/completion is provenance only. Even a retained
                # old EOF must now be observed from the new authentic cursor.
                slot = dict(slot, context=context, completion=None,
                    replayed_from_context_sha256=slot['context']['context_sha256'])
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
                return {'schema': 'unit-row-channel4-checked-prefix-classification-v1',
                        'marking_id': self._state['marking_id'],
                        'status': 'TWO_OR_MORE', 'state_sha256': digest(self._state),
                        'input_epoch': self._state['input_epoch'],
                        'row': row, 'candidate_keys': self._copy(slot['keys'][:2]),
                        'accepted_local_evidence': True, 'complete_cover_checked': False,
                        'sole_candidate': None, 'degree_exact': None,
                        'prefix_context_state_sha256': slot['context']['state_sha256'],
                        'domain_transfer': self._copy(slot.get('retention_transition'))}
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

    def _validate_receipt(self, receipt, row, require_cover=False, proposal=None):
        validate_native_receipt(receipt=receipt, language=self.language,
            semantics=self.semantics, state=self._state, row=row, tick=self.tick,
            require_cover=require_cover)
        self._join_family_degree_census(receipt, proposal)

    def decision(self):
        self.tick()
        self._check_authority()
        # Stack-local, engine-owned data only. The full authority literal already
        # contains the independently checked frozen marking and route policy.
        # No producer/checker receives this tuple or its guard, and no checkpoint
        # or engine field retains either after the first pass.
        owner = self
        state_object, state_literal = self._state, canonical(self._state)
        revision = self._revision
        language, semantics = self.language, self.semantics
        transition, native_tick = self.transition_checker, self.tick
        proposer = self.degree_proposer
        binding_literal = canonical(language.binding)
        marking_id = self._state['marking_id']
        authority, policy, branch_tie = self._authority, self._scheduler_policy, self._branch_tie
        checked, active = None, True

        def current():
            # Trusted synchronous pinned Sources: compare owned literals and
            # identities here; rebuild/checker calls still do their full math.
            native_tick()
            need(active and self is owner and self._state is state_object
                 and canonical(self._state) == state_literal and self._revision == revision
                 and self.language is language and self.semantics is semantics
                 and self.transition_checker is transition and self.tick is native_tick
                 and self.degree_proposer is proposer
                 and canonical(language.binding) == binding_literal
                 and self._state['marking_id'] == marking_id and semantics.marking_id == marking_id
                 and self._authority == authority and self._scheduler_policy == policy
                 and self._branch_tie == branch_tie
                 and (checked is None or canonical(checked[0]) == state_literal),
                 'current decision-local checked state/object/revision/authority')

        try:
            current()
            checked = semantics.private_state(language, state_object, native_tick)
            current()
            state, totals, marks, selected, excluded, names = checked
            frontier = [r for r in range(24) if totals[(0, r)] == 0]
            self.counts['global_scans'] += 1
            certificates = {r: v for r, v in self._certs.items() if r in frontier}
            # First inspect every checked local query, so a later certified dead
            # point is not hidden behind an earlier unresolved fallback.
            for row in frontier:
                current()
                receipt = certificates.get(row)
                if receipt is not None and receipt['status'] != 'UNKNOWN':
                    need(receipt['state_sha256'] == digest(self._state)
                         and receipt['row'] == row and receipt['input_epoch'] == self._state['input_epoch'],
                         'engine-owned current checked or transferred domain')
                    self.counts['retained_queries'] += 1
                else:
                    offered_state = self._copy(self._state)
                    current()
                    proposal = proposer(language=language,
                        state=offered_state, row=row, tick=native_tick)
                    current()
                    receipt_state = self._copy(self._state)
                    current()
                    receipt = semantics.check_degree_evidence(language=language,
                        state=receipt_state, row=row, proposal=proposal, tick=native_tick)
                    current()
                    self._validate_receipt(receipt, row, proposal=proposal)
                    current()
                    for raw in proposal['candidates']:
                        tile = self._candidate_from_decision_context(raw, row, checked, current)
                        self._observe(tile)
                        current()
                certificates[row] = self._copy(receipt)
                current()
                if receipt['status'] == 'ZERO':
                    self._certs = certificates
                    result = {'kind': 'DEAD', 'row': row}
                    self._emit('DECISION', decision=result, branch_tie=self.branch_tie,
                               statuses=[[r, v['status']] for r, v in certificates.items()],
                               evidence=[[r, v] for r, v in certificates.items()])
                    current()
                    return result
        finally:
            active = False
        for row in frontier:
            if certificates[row]['status'] == 'UNKNOWN':
                certificates[row] = self._fallback_degree(row)
                if certificates[row]['status'] == 'ZERO':
                    break
        self._certs = certificates
        # Mark presence is an obligation, never an occupied/proved output.
        assigned = [r for r in frontier
                    if (1, r) in marks and marks[(1, r)][0] == 'formula']
        result = select_schedule(evidence=certificates,
            generations={r: 0 for r in frontier}, tick=self.tick,
            branch_tie=self.branch_tie, assigned_output_rows=assigned)
        if result['kind'] == 'FORCED':
            result['candidate'] = self._copy(certificates[result['row']]['sole_candidate'])
        self._emit('DECISION', decision=result, branch_tie=self.branch_tie,
                   assigned_output_rows=assigned, statuses=[[r, v['status']] for r, v in certificates.items()],
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
            pre = record['type_preimage']['base_type_preimage']
            command = self._copy(pre['primitive_witness'])
            refs = [row+d for d in pre['ordered_offsets']]
            if command['rule'] == 'mp':
                command.update(antecedent=refs[0], implication=refs[1])
            elif command['rule'] == 'generalize':
                command['source'] = refs[0]
            word.append(command)
        return word

    def _checked_advice(self, decision, batch, mode):
        """Join a fresh independent receipt; never reinterpret a raised failure."""
        self.tick()
        receipt = self.validate_advice(state=self._copy(self._state),
            decision=self._copy(decision), batch=self._copy(batch), tick=self.tick)
        # An adviser-local UNKNOWN is not permission to outlive the owning clock.
        self.tick()
        receipt = self._copy(receipt)
        fields = {'schema', 'version', 'mode', 'binding', 'state_sha256',
                  'decision', 'input_sha256', 'selection', 'rejections'} | set(ADVICE_FLAGS)
        need(type(receipt) is dict and set(receipt) == fields
             and receipt['schema'] == 'unit-row-advice-validation-v1'
             and receipt['version'] == ADVICE_VALIDATOR_VERSION and receipt['mode'] == mode
             and canonical(receipt['binding']) == canonical(self.language.binding)
             and receipt['state_sha256'] == digest(self._state)
             and canonical(receipt['decision']) == canonical(decision)
             and receipt['input_sha256'] == digest(batch)
             and all(receipt[k] is False for k in ADVICE_FLAGS),
             'independent advice receipt exact current input and false authority flags')
        need(type(receipt['rejections']) is list and len(receipt['rejections']) <= 24,
             'bounded explicit pending rejections')
        rejected = set()
        requested = {canonical(k) for k in batch['keys']} if mode == 'PENDING_KEYS' else set()
        for rejection in receipt['rejections']:
            self.tick()
            need(type(rejection) is dict and set(rejection) == {'key', 'reason'}
                 and rejection['reason'] in HINT_REJECTION_REASONS,
                 'only definite original legality returns remove a hint')
            identity = canonical(rejection['key'])
            need(identity in requested and identity not in rejected,
                 'each rejected full key belongs to this pending request once')
            rejected.add(identity)
        selection = receipt['selection']
        if selection is not None:
            need(type(selection) is dict and set(selection) == {'anchor', 'future_keys', 'origin'},
                 'independent chosen family fields')
            anchor = self._candidate(selection['anchor'], decision['row'])
            identity = canonical(anchor['placement_key'])
            need(identity not in rejected and type(selection['future_keys']) is list
                 and len(selection['future_keys']) <= 23 and type(selection['origin']) is dict,
                 'chosen anchor and bounded future preferences')
            seen = {identity}
            for key in selection['future_keys']:
                self.tick()
                need(type(key) is dict and set(key) == {'tile_type_id', 'type_preimage', 'translation'}
                     and type(key['translation']) is list and len(key['translation']) == 2
                     and type(key['translation'][0]) is int and key['translation'][0] == 0
                     and type(key['translation'][1]) is int
                     and decision['row'] < key['translation'][1] < 24,
                     'full later-row preference keys, never installed members')
                encoded = canonical(key)
                need(encoded not in seen, 'unique full future keys')
                seen.add(encoded)
            if mode == 'PENDING_KEYS':
                need(identity in requested and selection['future_keys'] == []
                     and selection['origin'] == {'family_id': batch['family_id']},
                     'pending selection belongs to existing family only')
            selection = dict(selection, anchor=anchor)
        return selection, rejected

    def _select_branch(self, decision):
        """Pure with respect to preference state; called only after global BRANCH."""
        need(decision['kind'] == 'BRANCH', 'advice cannot bypass global scheduler')
        row, preferences = decision['row'], self._copy(self._preferences)
        dropped, retired, abandoned = [], [], None
        if preferences is not None:
            # The real global decision already validated this owned point state.
            # Occupied rows need no future preference, even if globally forced.
            totals = self.semantics.point_map(self._state['t'], self.tick)
            remaining = []
            for key in preferences['pending_keys']:
                self.tick()
                if totals[(0, key['translation'][1])] == 1:
                    retired.append(self._copy(key))
                else:
                    remaining.append(key)
            self.counts['pending_retired'] += len(retired)
            preferences = dict(preferences, pending_keys=remaining) if remaining else None
        if preferences is not None:
            keys = [k for k in preferences['pending_keys'] if k['translation'][1] == row]
            if keys:
                self.counts['pending_checks'] += 1
                request = {'schema': 'unit-row-pending-preference-request-v1',
                    'binding': self._copy(self.language.binding),
                    'state_sha256': digest(self._state), 'decision': self._copy(decision),
                    'family_id': preferences['family_id'], 'keys': keys}
                selected, rejected = self._checked_advice(decision, request, 'PENDING_KEYS')
                dropped = [self._copy(k) for k in keys if canonical(k) in rejected]
                self.counts['pending_rejected'] += len(dropped)
                if rejected:
                    # This retires advice, never a base candidate or point mark.
                    abandoned = {'schema': 'unit-row-advisory-family-abandonment-v1',
                        'family_id': preferences['family_id'], 'branch_row': row,
                        'reason': 'DEFINITE_CURRENT_PENDING_MEMBER_REJECTION',
                        'pending_keys': self._copy(preferences['pending_keys']),
                        'rejected_keys': self._copy(dropped)}
                    self.counts['family_abandonments'] += 1
                    preferences = None
                elif selected is not None:
                    anchor = selected['anchor']
                    chosen = canonical(anchor['placement_key'])
                    remaining = [k for k in preferences['pending_keys'] if canonical(k) != chosen]
                    lineage = preferences['lineage'] + [{'mode': 'PENDING_KEYS',
                        'key': self._copy(anchor['placement_key']), 'state_sha256': digest(self._state)}]
                    need(len(lineage) <= 24, 'one preference lineage entry per installed row')
                    preferences = dict(preferences, pending_keys=remaining, lineage=lineage)
                    return {'candidate': anchor, 'mode': 'PENDING_KEYS',
                        'preferences': preferences if remaining else None,
                        'family_id': request['family_id'], 'origin': selected['origin'],
                        'rejected_keys': dropped, 'retired_keys': retired,
                        'abandoned_family': abandoned}
                if preferences is not None and not preferences['pending_keys']:
                    preferences = None
        # Preserve one chosen family across intervening canonical branches.
        # A new unrelated batch cannot replace an unconsumed family.
        if preferences is None:
            self.counts['advice_calls'] += 1
            batch = self.branch_adviser(state=self._copy(self._state),
                                        decision=self._copy(decision), tick=self.tick)
            self.tick()
            need(type(batch) is dict and batch.get('schema') == 'unit-row-goal-branch-advice-batch-v1'
                 and batch.get('version') == ADVISER_VERSION
                 and batch.get('status') in ('READY', 'UNKNOWN'), 'current advisory batch status')
            if batch['status'] == 'UNKNOWN':
                # No partial candidate, pending key, completion or pruning is used.
                self.counts['advice_unknown'] += 1
            else:
                selected, rejected = self._checked_advice(decision, batch, 'ADVICE_BATCH')
                need(not rejected, 'READY validation never silently drops bad members')
                if selected is not None:
                    anchor, future = selected['anchor'], selected['future_keys']
                    origin = self._copy(selected['origin'])
                    family_id = digest({'binding': self.language.binding, 'origin': origin,
                        'anchor_key': anchor['placement_key'], 'future_keys': future})
                    family = {'schema': 'unit-row-branch-preference-family-v1',
                        'family_id': family_id, 'binding': self._copy(self.language.binding),
                        'origin': origin, 'anchor_key': self._copy(anchor['placement_key']),
                        'pending_keys': self._copy(future), 'lineage': [{'mode': 'ADVICE_BATCH',
                            'key': self._copy(anchor['placement_key']), 'state_sha256': digest(self._state)}]}
                    return {'candidate': anchor, 'mode': 'ADVICE_BATCH',
                        'preferences': family if future else None, 'family_id': family_id,
                        'origin': origin, 'rejected_keys': dropped, 'retired_keys': retired,
                        'abandoned_family': abandoned}
        self.counts['fallback_branch_choices'] += 1
        slot = self._slots.get(row)
        if slot is not None and slot['candidates']:
            candidate = self._copy(slot['candidates'][0])
        else:
            item = self.next_alternative(row)
            if item['kind'] == 'EOF':
                raise Unresolved('no canonical branch alternative; EOF is not pruning authority')
            candidate = item['candidate']
        return {'candidate': candidate, 'mode': 'CANONICAL_FALLBACK',
            'preferences': preferences, 'family_id': None if preferences is None else preferences['family_id'],
            'origin': None, 'rejected_keys': dropped, 'retired_keys': retired,
            'abandoned_family': abandoned}

    def _adopt_branch(self, plan):
        """Called INSIDE the owned child try/finally; no future mark is imposed."""
        self._preferences = self._copy(plan['preferences'])
        if plan['mode'] == 'ADVICE_BATCH':
            self.counts['advice_selected'] += 1
        elif plan['mode'] == 'PENDING_KEYS':
            self.counts['pending_selected'] += 1
        self._observe(plan['candidate'])
        self._emit('ADVICE', mode=plan['mode'], family_id=plan['family_id'],
            key=plan['candidate']['placement_key'], origin=plan['origin'],
            rejected_keys=plan['rejected_keys'], retired_keys=plan['retired_keys'],
            abandoned_family=plan['abandoned_family'], pending_preferences=self._preferences)

    def _join_prototype_census(self, entries):
        """Collision evidence only: no candidate, point union or domain insertion."""
        if self._family_prototype_census is None:
            return
        need(type(entries) is list, 'full prototype census literal list')
        names = dict(self._family_prototype_census)
        for entry in entries:
            self.tick()
            need(type(entry) is list and len(entry) == 2
                 and type(entry[0]) is str and type(entry[1]) is str,
                 'full prototype census literal name/preimage pair')
            name, encoded = entry
            pre = json.loads(encoded)
            need(type(pre) is dict and canonical(pre) == encoded,
                 'canonical full literal prototype preimage, not digest-only authority')
            base_fields = {'input_epoch','primitive_witness','ordered_premise_formulas','ordered_offsets'}
            if set(pre) == base_fields:
                need(pre['input_epoch'] == self._state['input_epoch']
                     and name == 'bounded-point-tile-' + digest(pre),
                     'reported original identity/current original epoch')
            else:
                need(set(pre) == {'schema','base_type_preimage','marking_id'}
                     and pre['schema'] == 'unit-row-row0-decorated-type-v1'
                     and pre['marking_id'] == self._state['marking_id']
                     and type(pre['base_type_preimage']) is dict
                     and set(pre['base_type_preimage']) == base_fields
                     and pre['base_type_preimage']['input_epoch'] == self._state['input_epoch']
                     and name == 'row0-decorated-tile-' + digest(pre),
                     'reported decorated identity/current separate marking')
            need(name not in names or names[name] == encoded,
                 'family and entire exposed original/decorated prototype full-preimage census')
            names[name] = encoded
            self.tick()
        # No in-place mutation: every owned checkpoint keeps its exact old ledger.
        self._family_prototype_census = names

    def _record_family_tile_census(self, tile):
        if self._family_prototype_census is not None:
            keys = (tile['base_tile']['placement_key'], tile['placement_key'])
            self._join_prototype_census([[key['tile_type_id'], canonical(key['type_preimage'])]
                                        for key in keys])

    def _join_family_degree_census(self, receipt, proposal=None):
        if self._family_prototype_census is None:
            return
        # Only after the unchanged fresh native receipt/context validator. This
        # is identity comparison, not a second degree certificate or shortlist.
        keys = list(receipt['candidate_keys'])
        if receipt['schema'] == 'unit-row-channel4-degree-evidence-check-v1':
            keys += receipt['original_base_receipt']['candidate_keys']
            keys += [item['placement_key'] for item in receipt['marked_rejections']
                     if 'placement_key' in item]
            if proposal is not None:
                for item in proposal['original_proposal']['rejections']:
                    self.tick()
                    if 'placement_key' in item:
                        key = item['placement_key']
                        tile = self.semantics.base.rebuild_tile(self.language, key['type_preimage'],
                                                               key['translation'], self.tick)
                        need(canonical(tile['placement_key']) == canonical(key),
                             'public original rejection exact fresh native reconstruction')
                        keys.append(tile['placement_key'])
        else:
            for tile in receipt['checked_candidates']:
                self.tick()
                self._record_family_tile_census(tile)
            rejected = list(receipt['checked_root_rejections'])
            if proposal is not None:
                rejected += proposal['root_rejections']
            seen_rejected = set()
            for item in rejected:
                self.tick()
                if 'placement_key' in item:
                    key = item['placement_key']
                    encoded = canonical(key)
                    if encoded in seen_rejected:
                        continue
                    seen_rejected.add(encoded)
                    # The public rejected key has no original key packet.
                    # Rebuild it through unchanged native point semantics rather
                    # than manufacture an original type ID from its digest.
                    tile = self.semantics.rebuild_tile(self.language, key['type_preimage'],
                                                      key['translation'], self.tick)
                    need(canonical(tile['placement_key']) == canonical(key),
                         'public rejected degree key exact fresh reconstruction')
                    self._record_family_tile_census(tile)
                    keys.append(key)
        self._join_prototype_census([[key['tile_type_id'], canonical(key['type_preimage'])]
                                    for key in keys])

    def _join_family_cursor_census(self, cursor, context, event, ordinal):
        if self._family_prototype_census is None:
            return
        self.tick()
        need(callable(getattr(cursor, 'prototype_census', None)),
             'family lane requires public full marked cursor prefix census')
        exported = self._copy(cursor.prototype_census())
        fields = {'schema','version','implementation_version','context','context_sha256',
            'input_epoch','marking_id','row','state_sha256','prototype_census',
            'original_yielded_candidates','yielded_candidates','marked_removed',
            'eof_reached','complete_prefix_census','scope','independently_checked',
            'degree_zero_or_singleton_accepted','complete_candidate_graph_accepted',
            'scheduler_or_rollback_accepted','logical_proof_accepted','ROOT_resource_accepted'}
        need(type(exported) is dict and set(exported) == fields
             and exported['schema'] == 'unit-row-channel4-fallback-prototype-census-v1'
             and exported['version'] == FALLBACK_VERSION
             and exported['implementation_version'] == CURSOR_CENSUS_IMPLEMENTATION
             and canonical(exported['context']) == canonical(context)
             and exported['context_sha256'] == context['context_sha256']
             and exported['input_epoch'] == self._state['input_epoch']
             and exported['marking_id'] == self._state['marking_id']
             and type(exported['row']) is int and exported['row'] == context['row']
             and exported['state_sha256'] == context['state_sha256'] == digest(self._state)
             and exported['complete_prefix_census'] is True
             and exported['scope'] == 'CHECKED_STATE_AND_BASE_YIELDED_MARKED_CURSOR_PREFIX'
             and all(exported[k] is False for k in ('independently_checked',
                 'degree_zero_or_singleton_accepted','complete_candidate_graph_accepted',
                 'scheduler_or_rollback_accepted','logical_proof_accepted','ROOT_resource_accepted')),
             'public cursor census exact current context and separate false authority')
        raw, shown, removed = (exported[k] for k in
            ('original_yielded_candidates','yielded_candidates','marked_removed'))
        need(all(type(n) is int and n >= 0 for n in (raw, shown, removed))
             and raw == shown + removed
             and event.get('kind') in ('CANDIDATE','EOF')
             and shown == ordinal + (1 if event['kind'] == 'CANDIDATE' else 0)
             and exported['eof_reached'] is (event['kind'] == 'EOF'),
             'actual cursor prefix counters, never complete candidate authority')
        entries = exported['prototype_census']
        need(type(entries) is list and entries == sorted(entries)
             and len({entry[0] for entry in entries}) == len(entries),
             'sorted unique full public prefix census')
        self._join_prototype_census(entries)
        exports = dict(self._family_cursor_censuses)
        exports[context['row']] = exported
        self._family_cursor_censuses = exports
        self.tick()

    def _consume_family(self, decision, mode, payload):
        self.tick()
        provider_report = None
        if mode == 'BATCH':
            offered = self._copy(payload)
            need(type(offered) is dict and set(offered) == {'batch','report'},
                 'full provider batch/report wrapper required, including UNKNOWN/no offer')
            payload, provider_report = offered['batch'], offered['report']
            fields = {'schema','version','matching_mode','binding_policy','batch','request',
                'binding','marking_id','state_sha256','decision','producer_implementation_version',
                'residual_policy_version','host','original_state','checked_state','branch_output_receptor',
                'records','row_rejections','offers','physical_assignment_plan','accounting',
                'prototype_census','reason','work','scope','flags'}
            need(type(provider_report) is dict and set(provider_report) == fields
                 and provider_report['schema'] == FAMILY_PROVIDER_SCHEMA
                 and provider_report['version'] == FAMILY_PROVIDER_VERSION
                 and provider_report['producer_implementation_version'] == OBSERVED_PRODUCER_IMPLEMENTATION
                 and provider_report['residual_policy_version'] == 'receptor-family-residual-host-binding-prefix-v2-max-index-shells'
                 and type(provider_report['matching_mode']) is str
                 and provider_report['matching_mode'] in ('VISIBLE_RECEPTOR','LITERAL_GROUND')
                 and provider_report['binding_policy'] == ({
                     'VISIBLE_RECEPTOR': 'EMPTY_PROBE_THEN_THEORY_NAMES_MAX_INDEX_SHELLS_V2',
                     'LITERAL_GROUND': 'EXPLICIT_MINED_ORIGIN_ENVIRONMENT_V1'}[provider_report['matching_mode']])
                 and canonical(provider_report['binding']) == canonical(self.language.binding)
                 and provider_report['marking_id'] == self._state['marking_id']
                 and provider_report['state_sha256'] == digest(self._state)
                 and canonical(provider_report['decision']) == canonical(decision)
                 and canonical(provider_report['batch']) == canonical(payload),
                 'full current provider report/header/batch, not transferred authority')
            source = provider_report['request']
            need(type(source) is dict and set(source) ==
                    {'mined','state','decision','matching_mode','binding_policy','limits'}
                 and canonical(source['state']) == canonical(self._state)
                 and canonical(source['decision']) == canonical(decision)
                 and canonical(source['matching_mode']) == canonical(provider_report['matching_mode'])
                 and canonical(source['binding_policy']) == canonical(provider_report['binding_policy'])
                 and (provider_report['checked_state'] is None
                      or canonical(provider_report['checked_state']) == canonical(self._state)),
                 'whole provider request/current state/decision and declared policy')
            flags = {'proposal_only': True, 'matching_complete': False,
                 'fact_accepted': False, 'degree_or_EOF_accepted': False, 'engine_activated': False,
                 'scheduler_accepted': False, 'pruning_accepted': False, 'proof_accepted': False,
                 'trajectory_accepted': False, 'RL_accepted': False, 'runtime_qualified': False}
            need(type(provider_report['flags']) is dict and set(provider_report['flags']) == set(flags)
                 and all(provider_report['flags'][key] is value for key, value in flags.items()),
                 'provider syntax/physical proposal has no scheduler or proof authority')
            entries = provider_report['prototype_census']
            need(type(entries) is list and entries == sorted(entries)
                 and len({entry[0] for entry in entries}) == len(entries),
                 'sorted unique full provider exposure census even without retained offer')
            self._join_prototype_census(entries)
        else:
            need(mode == 'CONTINUATION', 'explicit unchanged family request modes')
            # Every pending key was admitted with the prior full batch report.
            # A continuation may not introduce an unreported prototype identity.
            for key in payload['member_keys']:
                self.tick()
                need(self._family_prototype_census.get(key['tile_type_id']) == canonical(key['type_preimage']),
                     'owned pending member already in complete exposure census')
        request = {'schema': 'receptor-family-primitive-preference-request-v1',
                   'mode': mode, 'payload': self._copy(payload)}
        self.counts['family_checks'] += 1
        receipt = self.family_consumer(state=self._copy(self._state),
            decision=self._copy(decision), request=self._copy(request), tick=self.tick)
        self.tick()
        receipt = self._copy(receipt)
        fields = {'schema','version','mode','binding','marking_id','state_sha256',
            'decision','request_sha256','status','selection','entry','checks','invalidations'} | set(ADVICE_FLAGS)
        need(type(receipt) is dict and set(receipt) == fields
             and receipt['schema'] == 'receptor-family-primitive-preference-check-v1'
             and receipt['version'] == 'receptor-family-primitive-preference-consumer-v2-batch-collision-ledger'
             and receipt['mode'] == mode and receipt['request_sha256'] == digest(request)
             and canonical(receipt['binding']) == canonical(self.language.binding)
             and receipt['marking_id'] == self._state['marking_id']
             and receipt['state_sha256'] == digest(self._state)
             and canonical(receipt['decision']) == canonical(decision)
             and canonical(receipt['entry']['state']) == canonical(self._state)
             and canonical(receipt['entry']['decision']) == canonical(decision)
             and receipt['status'] in ('READY','NO_MATCH','UNKNOWN','INVALIDATED')
             and type(receipt['checks']) is list and type(receipt['invalidations']) is list
             and all(receipt[k] is False for k in ADVICE_FLAGS),
             'fresh family receipt whole current context, separate false authority')
        # A local instance/batch ledger does not cover previously exposed degree
        # or fallback candidates. Compare all full type preimages without adding
        # any candidate/incidence/dependency, point value or domain certificate.
        type_census = []
        for observed in self._observed.values():
            self.tick()
            tile = observed['candidate']
            type_census.extend((tile['base_tile']['placement_key'], tile['placement_key']))
        for checked in receipt['checks']:
            self.tick()
            adaptation = checked['adaptation']
            if adaptation is not None and adaptation['status'] == 'READY_LOCAL_CLUSTER':
                for member in adaptation['members']:
                    self.tick()
                    tile = member['tile']
                    type_census.extend((tile['base_tile']['placement_key'], tile['placement_key']))
        self._join_prototype_census([[key['tile_type_id'], canonical(key['type_preimage'])]
                                    for key in type_census])
        selection = receipt['selection']
        if receipt['status'] == 'READY':
            need(type(selection) is dict and set(selection) == {'candidate','family'}
                 and type(selection['family']) is dict, 'one checked primitive preference')
            candidate = self._candidate(selection['candidate'], decision['row'])
            need(any(canonical(candidate['placement_key']) == canonical(key)
                     for key in selection['family']['member_keys']), 'actual full family member key')
            selection = dict(selection, candidate=candidate)
        elif receipt['status'] == 'NO_MATCH' and selection is not None:
            need(mode == 'CONTINUATION' and type(selection) is dict
                 and set(selection) == {'candidate','family'} and selection['candidate'] is None
                 and type(selection['family']) is dict, 'unconsumed family without row preference')
        else:
            need(selection is None, 'no partial candidate from unknown or invalid family')
        if selection is not None:
            family = selection['family']
            need(family['schema'] == 'receptor-family-pending-primitive-instance-v1'
                 and canonical(family['binding']) == canonical(self.language.binding)
                 and family['marking_id'] == self._state['marking_id']
                 and family['family_instance_id'] == digest({k: family[k] for k in
                    ('binding','marking_id','initial_instance','member_keys')})
                 and type(family['member_keys']) is list and 0 < len(family['member_keys']) <= 24
                 and type(family['lineage']) is list and len(family['lineage']) <= 24,
                 'whole owned family identity without future installation')
            if mode == 'CONTINUATION':
                need(family['family_instance_id'] == payload['family_instance_id']
                     and canonical(family['initial_instance']) == canonical(payload['initial_instance'])
                     and canonical(family['member_keys']) == canonical(payload['member_keys']),
                     'continuation preserves full initial instance/member identity')
        checked_record = {'schema': 'receptor-family-engine-full-census-check-v1',
            'version': VERSION, 'mode': mode, 'status': receipt['status'],
            'binding': self._copy(self.language.binding), 'marking_id': self._state['marking_id'],
            'state_sha256': digest(self._state), 'decision': self._copy(decision),
            'consumer_receipt': receipt, 'provider_report': provider_report,
            'prototype_census': [[name, pre] for name, pre in sorted(self._family_prototype_census.items())],
            'census_is_collision_evidence_only': True,
            **{k: False for k in ADVICE_FLAGS}}
        return selection, checked_record

    def _select_family_branch(self, decision):
        """Preference plan only; decision() already completed global scheduling."""
        need(decision['kind'] == 'BRANCH', 'family cannot bypass global scheduler')
        pending, receipts = self._copy(self._preferences), []
        if pending is not None:
            selection, receipt = self._consume_family(decision, 'CONTINUATION', pending)
            receipts.append(receipt)
            if receipt['status'] == 'READY':
                return {'candidate': selection['candidate'], 'family': selection['family'],
                        'receipts': receipts, 'mode': 'CONTINUATION'}
            if receipt['status'] == 'INVALIDATED':
                self.counts['family_invalidated'] += 1
                pending = None
            elif receipt['status'] == 'NO_MATCH':
                pending = None if selection is None else selection['family']
            else:
                self.counts['family_unknown'] += 1
        if pending is None:
            self.counts['family_batches'] += 1
            batch = self.family_proposer(state=self._copy(self._state),
                decision=self._copy(decision), tick=self.tick)
            self.tick()
            selection, receipt = self._consume_family(decision, 'BATCH', batch)
            receipts.append(receipt)
            if receipt['status'] == 'READY':
                return {'candidate': selection['candidate'], 'family': selection['family'],
                        'receipts': receipts, 'mode': 'BATCH'}
            need(receipt['status'] in ('UNKNOWN','NO_MATCH'), 'fresh batch cannot be a stale continuation')
            self.counts['family_unknown'] += receipt['status'] == 'UNKNOWN'
        # Complete original fallback is preserved, with its original ordering.
        self.counts['family_canonical_choices'] += 1
        row = decision['row']
        slot = self._slots.get(row)
        if slot is not None and slot['candidates']:
            candidate = self._copy(slot['candidates'][0])
        else:
            item = self.next_alternative(row)
            if item['kind'] == 'EOF':
                raise Unresolved('no canonical branch alternative; EOF is not pruning authority')
            candidate = item['candidate']
        return {'candidate': candidate, 'family': pending, 'receipts': receipts,
                'mode': 'CANONICAL_FALLBACK'}

    def _adopt_family_branch(self, plan):
        """Inside existing child checkpoint; only a single base placement follows."""
        self._preferences = self._copy(plan['family'])
        if plan['mode'] != 'CANONICAL_FALLBACK':
            self.counts['family_choices'] += 1
        self._observe(plan['candidate'])
        self._emit('FAMILY_PREFERENCE', mode=plan['mode'], key=plan['candidate']['placement_key'],
            pending_family=self._preferences, receipts=plan['receipts'],
            family_degree_or_exclusion_authority=False)

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
                branch_plan = None
                if kind == 'FORCED':
                    candidate = decision['candidate']
                    self.counts['forced'] += 1
                else:
                    self.counts['branches'] += 1
                    if self.family_proposer is not None:
                        branch_plan = self._select_family_branch(decision)
                        candidate = branch_plan['candidate']
                    elif self.branch_adviser is not None:
                        branch_plan = self._select_branch(decision)
                        candidate = branch_plan['candidate']
                    else:
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
                    if branch_plan is not None:
                        if self.family_proposer is not None:
                            self._adopt_family_branch(branch_plan)
                        else:
                            self._adopt_branch(branch_plan)
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
                # before any sibling. Unaffected domains may be retained only
                # through checked equality; old native iterators are discarded.

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
        return {'schema': 'unit-row-receptor-family-lazy-global-search-result-v1', 'version': VERSION,
            'marking_id': self._state['marking_id'],
            'variant': VARIANT if self.branch_tie == 'ROW' else MARK_VARIANT,
            'scheduler_policy': self._policy_snapshot(),
            'status': status, 'reason': reason,
            'branch_advice_enabled': self.branch_adviser is not None,
            'family_preferences_enabled': self.family_proposer is not None,
            'family_preference_policy': self._family_policy(),
            'input_epoch': self._state['input_epoch'], 'root_restored': True,
            'stack_restored': True, 'last_observed_state': last_state,
            'root_snapshot_sha256': digest(before), 'final_snapshot_sha256': digest(after),
            'found': found, 'events': diagnostic_copy(self.events), 'counts': dict(self.counts),
            'trace_complete': status != 'UNKNOWN',
            'logical_proof_accepted': False, 'exact_point_board_accepted': False,
            'complete_candidate_graph_accepted': False, 'trajectory_accepted': False,
            'GCTS_advantage_accepted': False, 'RL_accepted': False,
            'ROOT_resource_accepted': False}
