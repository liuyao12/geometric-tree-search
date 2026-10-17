"""SOURCE ONLY: explicit composition router, never a new point model.

Original Source17/input2 language and821fe point instance are caller-authenticated.
Assigned non-implication uses4316/8f7a; implication/absent retains the legacy safe
path. Native receipt protocols remain literal. No project imports or clocks.
"""
import hashlib
import json

VERSION = 'unit-row-channel4-marked-degree-router-v1'
SEMANTICS_VERSION = 'unit-row-channel4-routed-nonimp-degree-semantics-v2'
TRANSITION_VERSION = 'unit-row-channel4-routed-support-transition-v2'
POINT_SEMANTICS_VERSION = 'unit-row-channel4-filtered-degree-semantics-v1'
LEGACY_PROPOSER_VERSION = 'unit-row-implicit-degree-evidence-v3-missing-marks'
NEW_PROPOSER_VERSION = 'unit-row-marked-aware-nonimp-fibre-proposer-v1'
NEW_CHECKER_VERSION = 'unit-row-independent-marked-aware-nonimp-fibre-checker-v1'
FALLBACK_VERSION = 'unit-row-channel4-filtered-six-rule-fallback-v1'
VERIFIER_VERSION = 'unit-row-independent-channel4-state-verifier-v1'
LEGACY_PROPOSAL_SCHEMA = 'unit-row-channel4-degree-evidence-proposal-v1'
LEGACY_PROPOSAL_VERSION = 'unit-row-channel4-point-adapter-v1'
NEW_PROPOSAL_SCHEMA = 'unit-row-marked-aware-nonimp-fibre-proposal-v1'
ROUTE_POLICY = 'CHECKED_ASSIGNED_NONIMP_ELSE_LEGACY_NO_EXCEPTION_FALLTHROUGH'


def require(ok, reason):
    if not ok:
        raise ValueError('marked degree router: ' + reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


class RoutedMarkedSemantics:
    VERSION = SEMANTICS_VERSION

    def __init__(self, *, point_semantics, legacy_proposer,
                 marked_aware_proposer, marked_aware_checker, tick):
        self._point = point_semantics
        self._legacy = legacy_proposer
        self._new_proposer, self._new_checker = marked_aware_proposer, marked_aware_checker
        self.base = point_semantics.base
        self._marking = None
        self._frozen_marking = None
        # No language is constructed or authority rebased here. The first public
        # check_marking binds the full already-authenticated point model.
        self._check_components(tick)

    @property
    def point(self):
        """Exact legacy point object for4316 and the unchanged filtered cursor."""
        return self._point

    @property
    def marking_id(self):
        return self._point.marking_id

    def _check_components(self, tick):
        tick()
        require(self._point.VERSION == POINT_SEMANTICS_VERSION
                and self._legacy.VERSION == LEGACY_PROPOSER_VERSION
                and self._new_proposer.VERSION == NEW_PROPOSER_VERSION
                and self._new_checker.VERSION == NEW_CHECKER_VERSION
                and self.base is self._point.base, 'exact immutable injected version coupling')

    def routing_policy(self, tick):
        self._check_components(tick)
        return {'schema': 'unit-row-channel4-degree-route-policy-v1',
            'router_version': VERSION, 'semantics_version': SEMANTICS_VERSION,
            'point_semantics_version': POINT_SEMANTICS_VERSION,
            'legacy_proposer_version': LEGACY_PROPOSER_VERSION,
            'new_proposer_version': NEW_PROPOSER_VERSION,
            'new_checker_version': NEW_CHECKER_VERSION, 'route_policy': ROUTE_POLICY,
            'legacy_receipt': ['unit-row-channel4-degree-evidence-check-v1',POINT_SEMANTICS_VERSION],
            'new_receipt': ['unit-row-marked-aware-nonimp-fibre-check-v1',NEW_CHECKER_VERSION]}

    def tree(self, value, tick):
        return self._point.tree(value, tick)

    def point_map(self, entries, tick):
        return self._point.point_map(entries, tick)

    def agree(self, values, point, value):
        return self._point.agree(values, point, value)

    def check_marking(self, language, tick):
        self._check_components(tick)
        check = self._point.check_marking(language, tick)
        current = canonical(check['marking'])
        if self._frozen_marking is None:
            self._marking = self.tree(check['marking'], tick)
            self._frozen_marking = current
        require(current == self._frozen_marking and canonical(self._marking) == current,
                'same full frozen point marking, no constructor-table substitution')
        return check

    def base_state(self, language, state, tick):
        return self._point.base_state(language, state, tick)

    def initial_state(self, language, tick):
        self.check_marking(language, tick)
        return self._point.initial_state(language, tick)

    def rebuild_tile(self, language, preimage, translation, tick):
        return self._point.rebuild_tile(language, preimage, translation, tick)

    def private_state(self, language, state, tick):
        return self._point.private_state(language, state, tick)

    def check_collision(self, tile, names):
        return self._point.check_collision(tile, names)

    def legality(self, tile, totals, marks, selected, excluded):
        return self._point.legality(tile, totals, marks, selected, excluded)

    def with_obligations(self, tile, totals, tick):
        return self._point.with_obligations(tile, totals, tick)

    def _current_route(self, language, state, row, tick):
        self.check_marking(language, tick)
        s, totals, marks, _, _, _ = self._point.private_state(language, state, tick)
        require(type(row) is int and 0 <= row < 24 and totals[(0,row)] == 0,
                'current unfilled query row')
        output = self.base.formula_at(language, marks, row, tick)
        return s, output is not None and output[0] != 'imp'

    def propose_degree(self, *, language, state, row, tick):
        s, nonimp = self._current_route(language, state, row, tick)
        if nonimp:
            return self._new_proposer.propose_degree(language=language,
                semantics=self._point, state=s, row=row, tick=tick)
        return self._point.propose_degree(language=language, state=s, row=row,
            tick=tick, degree_proposer=self._legacy.propose_degree)

    def check_degree_evidence(self, *, language, state, row, proposal, tick):
        s, nonimp = self._current_route(language, state, row, tick)
        require(type(proposal) is dict, 'literal proposal, never a supplied receipt')
        if nonimp:
            require(proposal.get('schema') == NEW_PROPOSAL_SCHEMA
                    and proposal.get('version') == NEW_PROPOSER_VERSION,
                    'checked nonimp route requires exact new proposal protocol')
            return self._new_checker.check_degree_evidence(language=language,
                base_semantics=self.base, verifier=self._point.verifier,
                marking=self.tree(self._marking, tick), state=s, row=row,
                proposal=proposal, tick=tick)
        require(proposal.get('schema') == LEGACY_PROPOSAL_SCHEMA
                and proposal.get('version') == LEGACY_PROPOSAL_VERSION,
                'checked implication/absent route requires exact legacy proposal protocol')
        return self._point.check_degree_evidence(language=language, state=s,
                                                row=row, proposal=proposal, tick=tick)


class RoutedMarkedTransition:
    VERSION = TRANSITION_VERSION

    def authority_snapshot(self, *, language, semantics, tick):
        require(semantics.VERSION == SEMANTICS_VERSION, 'marked semantics API')
        check = semantics.check_marking(language, tick)
        value = {name: getattr(language, name) for name in ('policy', 'declaration',
            'source_bindings', 'theory', 'parameters', 'gamma', 'target', 'hole', 'binding')}
        for name in ('parameter_set', 'input_names', 'binder_names', 'forbidden'):
            values = getattr(language, name)
            require(type(values) is frozenset and all(type(v) is str for v in values), 'frozen scoped names')
            value[name] = sorted(values)
        value.update(semantics_version=SEMANTICS_VERSION, fallback_version=FALLBACK_VERSION,
            marking=check['marking'], independent_marked_verifier_version=VERIFIER_VERSION,
            degree_route_policy=semantics.routing_policy(tick))
        return semantics.tree(value, tick)

    def _projection(self, state, totals, marks, row, tick):
        # Complete POSSIBLE support, including ungenerated placements. Strict
        # prior offsets and independent prototype reconstruction prove this
        # superset; no inference from the currently exposed candidate list.
        points = [(ch, k) for ch in (1, 4) for k in range(row+1)] + [(2, row), (3, row)]
        assignments = []
        for p in points:
            tick()
            assignments.append([list(p), p in marks, marks[p] if p in marks else None])
        inventories = {name: sorted(canonical(k) for k in state[name]
            if k['translation'][1] == row) for name in ('selected', 'excluded')}
        return {'row': row, 't': [[[0, row], totals[(0, row)]]], 'm': assignments,
            'inventories': inventories, 'root_generation': dict((tuple(p), v)
                for p, v in state['generation'])[(0, row)], 'marking_id': state['marking_id']}

    def check_transition(self, *, language, semantics, before, after, rows, authority, tick):
        require(type(authority) is str and canonical(self.authority_snapshot(
            language=language, semantics=semantics, tick=tick)) == authority, 'unchanged full marked authority')
        require(type(rows) is list and all(type(r) is int and 0 <= r < 24 for r in rows)
                and rows == sorted(set(rows)), 'sorted unique rows')
        old, ot, om, _, _, on = semantics.private_state(language, before, tick)
        new, nt, nm, _, _, nn = semantics.private_state(language, after, tick)
        same_names = canonical(sorted(on.items())) == canonical(sorted(nn.items()))
        result = []
        for row in rows:
            tick()
            op = self._projection(old, ot, om, row, tick)
            np = self._projection(new, nt, nm, row, tick)
            equal = canonical(op) == canonical(np)
            frontier = ot[(0, row)] == nt[(0, row)] == 0
            result.append({'row': row, 'retain': frontier and same_names and equal,
                'reason': ('occupied_or_removed_frontier' if not frontier else
                    'global_collision_ledger_changed' if not same_names else
                    'possible_full_channel4_support_changed' if not equal else
                    'literal_all_possible_full_support_and_collision_ledger_equal'),
                'read_occupancy_changes': [k for k in range(row) if ot[(0, k)] != nt[(0, k)]],
                'before_projection_sha256': sha(op), 'after_projection_sha256': sha(np)})
        return {'schema': 'unit-row-channel4-checked-domain-transition-v2', 'version': TRANSITION_VERSION,
            'marking_id': semantics.marking_id, 'before_state_sha256': sha(old), 'after_state_sha256': sha(new),
            'authority_sha256': hashlib.sha256(authority.encode('utf8')).hexdigest(),
            'input_epoch': old['input_epoch'], 'rows': result, 'collision_ledger_equal': same_names,
            'before_collision_ledger_sha256': sha(sorted(on.items())),
            'after_collision_ledger_sha256': sha(sorted(nn.items())),
            'compared_literal_values_not_only_hashes': True, 'degree_or_EOF_accepted': False,
            'complete_graph_accepted': False, 'scheduler_trajectory_accepted': False,
            'logical_proof_accepted': False, 'ROOT_resource_accepted': False}

    def refresh_candidates(self, *, language, semantics, state, candidates, tick):
        _, t, m, selected, excluded, names = semantics.private_state(language, state, tick)
        require(type(candidates) is list, 'complete known candidate list')
        refreshed, used = [], set()
        for raw in candidates:
            tick()
            key = raw['placement_key']
            tile = semantics.rebuild_tile(language, key['type_preimage'], key['translation'], tick)
            semantics.check_collision(tile, names)
            require(canonical(key) == canonical(tile['placement_key'])
                    and semantics.legality(tile, t, m, selected, excluded) is None, 'retained full current legality')
            require(canonical({k: v for k, v in raw.items() if k != 'read_obligations'}) == canonical(tile),
                    'all retained original and channel4 core values unchanged')
            encoded = canonical(key)
            require(encoded not in used, 'distinct full retained keys')
            used.add(encoded)
            refreshed.append(semantics.with_obligations(tile, t, tick))
        return refreshed

