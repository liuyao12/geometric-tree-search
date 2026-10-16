"""SOURCE ONLY: a sufficient domain-equality relation, not degree evidence.

No engine/proposer/fallback imports. The caller owns an already checked domain
in `before`; this module checks when its exact candidate relation is unchanged.
It never accepts a supplied degree receipt, rewrites an old state hash, or
certifies fallback EOF. Fresh whole c354 state validation remains mandatory.
"""
import hashlib
import json

VERSION = 'unit-row-domain-transition-checker-v1'
SEMANTICS_VERSION = 'independent-unit-row-missing-mark-degree-check-v2'
FALLBACK_VERSION = 'unit-row-complete-lazy-six-rule-fallback-v1'


def require(ok, reason):
    if not ok:
        raise ValueError('domain transition: ' + reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def authority_snapshot(*, language, semantics, tick):
    """Literal semantic inputs; effective code/native custody is external."""
    tick()
    require(semantics.VERSION == SEMANTICS_VERSION, 'original c354 semantics')
    value = {name: getattr(language, name) for name in (
        'policy', 'declaration', 'source_bindings', 'theory', 'parameters',
        'gamma', 'target', 'hole', 'binding')}
    for name in ('parameter_set', 'input_names', 'binder_names', 'forbidden'):
        values = getattr(language, name)
        require(type(values) is frozenset and all(type(x) is str for x in values),
                'literal frozen name set')
        value[name] = sorted(values)
    value['semantics_version'] = SEMANTICS_VERSION
    value['fallback_version'] = FALLBACK_VERSION
    return semantics.tree(value, tick)


def _projection(*, state, totals, marks, row, tick):
    """All possible unit-row t/m support, not only exposed candidates.

    A tile at r writes t(0,r), output m(1,r), zero/two metadata marks
    m(2,r),m(3,r), and only reads m(1,k) for 0<=k<r. Earlier t values
    change read-obligation packets, not this candidate relation. Those
    packets must be rebuilt separately. The outside boundary is recomposed
    by c354 and strict negative offsets forbid every other read position.
    """
    tick()
    points = [(1, k) for k in range(row+1)] + [(2, row), (3, row)]
    assignments = []
    for point in points:
        tick()
        # Explicit presence distinguishes no marking, assigned zero and None.
        assignments.append([list(point), point in marks,
                            marks[point] if point in marks else None])
    inventories = {}
    for name in ('selected', 'excluded'):
        keys = []
        for record in state[name]:
            tick()
            if record['translation'][1] == row:
                keys.append(canonical(record))
        inventories[name] = sorted(keys)
    generations = {(tuple(p)): v for p, v in state['generation']}
    return {'row': row, 't': [[[0, row], totals[(0, row)]]],
            'm': assignments, 'inventories': inventories,
            'root_generation': generations[(0, row)]}


def check_transition(*, language, semantics, before, after, rows, authority, tick):
    """Compare literal support and collision ledgers; return no degree claim.

    `authority` is the caller's immutable canonical authority snapshot captured
    before the original queries. Both full states are checked afresh. A changed
    global type-id/full-preimage ledger invalidates every row conservatively:
    this preserves c354 collision rejection without assuming injective SHA256.
    A true row result is sufficient, deliberately not a necessary/minimal test.
    """
    tick()
    require(type(authority) is str and
            canonical(authority_snapshot(language=language, semantics=semantics,
                                         tick=tick)) == authority,
            'unchanged complete original authority; new engine on any change')
    require(type(rows) is list and all(type(r) is int and 0 <= r < 24 for r in rows)
            and rows == sorted(set(rows)), 'literal sorted distinct queried rows')
    old, ot, om, _, _, on = semantics.private_state(language, before, tick)
    new, nt, nm, _, _, nn = semantics.private_state(language, after, tick)
    # Compare full canonical preimages, never tile hashes alone. Both ledgers
    # have already passed their own c354 per-state collision checks.
    old_names, new_names = sorted(on.items()), sorted(nn.items())
    same_names = canonical(old_names) == canonical(new_names)
    result = []
    for row in rows:
        tick()
        op = _projection(state=old, totals=ot, marks=om, row=row, tick=tick)
        np = _projection(state=new, totals=nt, marks=nm, row=row, tick=tick)
        equal = canonical(op) == canonical(np)
        frontier = ot[(0, row)] == nt[(0, row)] == 0
        retain = frontier and same_names and equal
        reason = ('occupied_or_removed_frontier' if not frontier else
                  'global_collision_ledger_changed' if not same_names else
                  'possible_support_or_local_key_set_changed' if not equal else
                  'literal_all_possible_support_and_collision_ledger_equal')
        result.append({'row': row, 'retain': retain, 'reason': reason,
                       'read_occupancy_changes': [k for k in range(row)
                                                  if ot[(0, k)] != nt[(0, k)]],
                       'before_projection_sha256': sha(op),
                       'after_projection_sha256': sha(np)})
    tick()
    return {'schema': 'unit-row-checked-domain-transition-v1', 'version': VERSION,
            'before_state_sha256': sha(old), 'after_state_sha256': sha(new),
            'authority_sha256': hashlib.sha256(authority.encode('utf8')).hexdigest(),
            'input_epoch': old['input_epoch'], 'rows': result,
            'collision_ledger_equal': same_names,
            'before_collision_ledger_sha256': sha(old_names),
            'after_collision_ledger_sha256': sha(new_names),
            'compared_literal_values_not_only_hashes': True,
            'degree_or_EOF_accepted': False, 'complete_graph_accepted': False,
            'scheduler_trajectory_accepted': False, 'logical_proof_accepted': False,
            'ROOT_resource_accepted': False}


def refresh_candidates(*, language, semantics, state, candidates, tick):
    """Rebuild retained known keys, never an exhaustive degree certificate.

    Candidate membership/core packets are checked again against the original
    c354 authority. Only read-obligation occupancy may differ. Fresh names are
    checked together to reject collisions between exposed candidates as well
    as collisions with the entire selected/excluded state ledger.
    """
    _, totals, marks, selected, excluded, names = semantics.private_state(language, state, tick)
    require(type(candidates) is list, 'complete known candidate array')
    refreshed, seen = [], set()
    for raw in candidates:
        tick()
        source = semantics.tree(raw, tick)
        require(type(source) is dict and type(source.get('placement_key')) is dict,
                'known candidate full key')
        key = source['placement_key']
        require(set(key) == {'tile_type_id', 'type_preimage', 'translation'}, 'exact full key')
        tile = semantics.rebuild_tile(language, key['type_preimage'], key['translation'], tick)
        require(canonical(tile['placement_key']) == canonical(key), 'unchanged literal key/preimage')
        semantics.check_collision(tile, names)
        require(semantics.legality(tile, totals, marks, selected, excluded) is None,
                'retained candidate whole current legality')
        old_core = {k: v for k, v in source.items() if k != 'read_obligations'}
        require(canonical(old_core) == canonical(tile), 'unchanged entire core member/point packet')
        encoded = canonical(key)
        require(encoded not in seen, 'unique known full keys')
        seen.add(encoded)
        refreshed.append(semantics.with_obligations(tile, totals, tick))
    tick()
    return refreshed
